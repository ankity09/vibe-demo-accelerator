# AI Gateway Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-demo` skill
- MCP tools: `create_ai_gateway_config` (if available), or REST API via `databricks api`
- A Model Serving endpoint to route through (foundation model or custom model)
- Databricks workspace with AI Gateway enabled (available in FEVM workspaces)

## Provisioning (via AI Dev Kit)
Use AI Dev Kit MCP tools — do NOT use raw REST API calls:
1. Enable AI Gateway on an existing Model Serving endpoint to add guardrails, rate limits, usage tracking, and PII detection.
2. Configure governance features:
   - **Rate limits** — Tokens per minute, requests per minute (per user or per endpoint)
   - **Usage tracking** — Log all requests/responses to a Delta Lake table in Unity Catalog
   - **Guardrails** — PII detection (output and/or input), toxicity filtering
   - **Inference tables** — Automatic logging of inputs, outputs, and token usage

Enable AI Gateway on an endpoint:
```bash
databricks api put /api/2.0/serving-endpoints/<endpoint-name>/ai-gateway \
  --json '{
    "usage_tracking_config": {"enabled": true},
    "inference_table_config": {
      "enabled": true,
      "catalog_name": "<catalog>",
      "schema_name": "<schema>",
      "table_name_prefix": "<demo>_ai_logs"
    },
    "guardrails": {
      "input": {"pii": {"behavior": "BLOCK"}},
      "output": {"pii": {"behavior": "BLOCK"}}
    },
    "rate_limit_config": {
      "calls": 100,
      "renewal_period": "minute"
    }
  }' --profile=<profile>
```

## VDA App Wiring
1. AI Gateway is transparent to the app — calls go to the same Model Serving endpoint URL. No code changes are required once the gateway is configured.
2. To display AI governance metrics in the demo dashboard, create `app/backend/routes/ai_governance.py`:
   ```python
   import asyncio, os
   from fastapi import APIRouter
   from backend.core import run_query

   router = APIRouter()
   CATALOG = os.getenv("CATALOG", "")
   SCHEMA = os.getenv("SCHEMA", "")

   @router.get("/ai-governance/metrics")
   async def ai_metrics():
       rows = await asyncio.to_thread(
           run_query,
           f"""SELECT
             DATE(timestamp) as date,
             COUNT(*) as total_requests,
             SUM(usage.total_tokens) as total_tokens,
             SUM(CASE WHEN status_code = 200 THEN 1 ELSE 0 END) as successful,
             SUM(CASE WHEN guardrail_blocked THEN 1 ELSE 0 END) as blocked
           FROM {CATALOG}.{SCHEMA}.<demo>_ai_logs_payload
           GROUP BY 1 ORDER BY 1 DESC LIMIT 30"""
       )
       return {"metrics": rows}
   ```
3. Mount in `app/backend/main.py`:
   ```python
   from backend.routes.ai_governance import router as governance_router
   app.include_router(governance_router, prefix="/api")
   ```
4. No additional env vars beyond `CATALOG` and `SCHEMA`.
5. Frontend: Add an "AI Governance" dashboard page showing request volume, token usage, guardrail blocks, and cost estimates. Use Recharts `AreaChart` for trends and VDA `.kpi-row` for totals. This page is a powerful demo talking point for governance-conscious customers.

## MAS Integration
AI Gateway is not a MAS sub-agent. It is applied as a governance layer on top of Model Serving endpoints that MAS may call via Foundation Model API or custom UC functions.

To demonstrate governance in the context of MAS: enable inference table logging on the Foundation Model API endpoints used by MAS (`databricks-claude-sonnet-4-5`). The inference table captures all MAS → FMAPI calls with full input/output logging.

## Manual Setup (fallback without AI Dev Kit)
```bash
# Enable AI Gateway on the FMAPI endpoint
databricks api put /api/2.0/serving-endpoints/databricks-claude-sonnet-4-5/ai-gateway \
  --json '{
    "usage_tracking_config": {"enabled": true},
    "inference_table_config": {
      "enabled": true,
      "catalog_name": "<catalog>",
      "schema_name": "<schema>",
      "table_name_prefix": "<demo>_ai_logs"
    }
  }' --profile=<profile>

# Verify configuration
databricks api get /api/2.0/serving-endpoints/databricks-claude-sonnet-4-5/ai-gateway \
  --profile=<profile>

# Check that inference tables were created (takes a few minutes)
databricks api post /api/2.0/sql/statements \
  --json '{
    "statement": "SHOW TABLES IN <catalog>.<schema> LIKE \"<demo>_ai_logs*\"",
    "warehouse_id": "<warehouse-id>"
  }' --profile=<profile>
```

Key inference table columns: `timestamp`, `databricks_request_id`, `request`, `response`, `usage` (prompt/completion/total tokens), `status_code`, `execution_time_ms`.
