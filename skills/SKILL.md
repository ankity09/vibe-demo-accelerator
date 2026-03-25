---
name: databricks-demo
description: Create, deploy and run demos relating to or integrating with Databricks.
---

# Databricks Demo Skill — /new-demo Wizard

Create, deploy and run demos on Databricks using the Vibe Demo Accelerator scaffold. This skill runs a 3-phase conversational wizard to gather all project details, then activates features and generates code.

---

## Critical Resource Docs (read before generating any code)

These docs contain battle-tested patterns for common failure modes. Do NOT duplicate their content — reference them at the point of need:

- `skills/resources/DATABRICKS_APPS.md` — Devloop process, port configuration, local validation loop
- `skills/resources/LAKEBASE.md` — Connection pooling, SP permissions, resource registration, ephemeral workspace recovery
- `skills/resources/LAKEBASE_MCP_SERVER.md` — MCP server deployment, MAS integration, UC HTTP connection, multi-database routing
- `skills/resources/DATA_GENERATION_SERVERLESS.md` — dbldatagen, serverless client versions, Python version pinning

---

## Existing Demo Detection

Before running the wizard, check if the current directory already has a `demo-config.yaml`:

- If `demo-config.yaml` exists — read it and skip to Phase 2 or Phase 3 as appropriate, or go straight to Feature Activation if all phases are complete.
- If `DEMO.md` and `TASKS.md` exist but no `demo-config.yaml` — read them for context, then confirm details with the user before generating `demo-config.yaml`.
- If none of the above exist — run the full 3-phase wizard.

---

## Phase 1: Identity & Infrastructure

Ask the user for the following in a single conversational block. Do not ask them one at a time. Present them as a numbered list and wait for all answers before proceeding.

```
I need a few details to set up your demo. Please answer as many as you can — I'll fill in defaults for anything you skip:

1. Demo name (e.g., "Apex Steel Predictive Maintenance")
2. Customer name (real or fictional)
3. Industry / domain (e.g., manufacturing, healthcare, financial services, agriculture, retail)
4. Key use cases — describe 2-4 things the demo should showcase
5. Databricks workspace URL (e.g., https://fe-sandbox-serverless-my-demo.cloud.databricks.com)
6. CLI profile name (e.g., my-demo)
7. Catalog name (FEVM auto-creates this as serverless_<name>_catalog)
8. Schema name (you'll create this, e.g., my_demo_schema)
9. SQL Warehouse ID — I'll try to find this automatically, but have it ready from the SQL Warehouses page
```

**Warehouse auto-discovery:** After receiving the workspace URL and CLI profile, attempt to call the AI Dev Kit tool `get_best_warehouse` to discover the warehouse ID automatically. If the tool is available and returns a result, use that value and inform the user. If the tool is unavailable or errors, ask the user for the warehouse ID directly.

**FEVM workspace conventions:**
- Workspace URL: `https://fe-sandbox-serverless-<name>.cloud.databricks.com`
- Auto-created catalog: `serverless_<name_with_underscores>_catalog` (hyphens become underscores)
- If the user doesn't have a workspace yet, direct them to use the `/databricks-fe-vm-workspace-deployment` skill first

---

## Phase 2: Databricks Features

### Step 1: Detect AI Dev Kit availability

Silently attempt to call the AI Dev Kit tool `get_current_user`. Do NOT tell the user you are doing this — just note the result internally.

- If the call succeeds: AI Dev Kit is available. Use its tools throughout the wizard for auto-provisioning.
- If the call fails or the tool does not exist: AI Dev Kit is not available. All provisioning steps will be manual CLI commands. Note this in `demo-config.yaml` as `ai_dev_kit: false`.

### Step 2: Build the feature menu

Read all `features/*/config.json` files in the project. Each file defines:
- `id` — the feature identifier
- `name` — display name
- `description` — one-line description
- `category` — grouping: `ai`, `data-platform`, `ml`, `operational`
- `ai_dev_kit.required_tools` — AI Dev Kit tools needed to auto-provision this feature
- `requires` — other feature IDs that must also be enabled
- `auto_include_with` — feature IDs that automatically pull this feature in as a dependency

For each feature, check whether all its `ai_dev_kit.required_tools` are available given the detection result from Step 1.

### Step 3: Pre-select features based on use-case keywords

Analyze the use cases provided in Phase 1. Apply the following keyword-to-feature mapping:

| If the use cases mention... | Pre-select features |
|---|---|
| "real-time", "streaming", "sensor", "IoT", "telemetry" | `live-feed` |
| "anomaly", "prediction", "ML", "model", "scoring", "forecast" | `model-serving` |
| "work order", "automation", "agent", "chat", "conversational", "AI assistant" | `mas`, `lakebase` |
| "Q&A", "document", "search", "RAG", "knowledge", "wiki" | `vector-search`, `knowledge-assistant` |
| "query", "SQL", "data exploration", "analytics", "natural language" | `genie` |
| "pipeline", "ETL", "ingestion", "transformation", "DLT" | `declarative-pipelines` |
| "dashboard", "report", "visualization", "embed" | `aibi-dashboard` |
| "external data", "Salesforce", "SAP", "Workday", "connector" | `lakeflow-connect` |
| "feature engineering", "training data", "feature table" | `feature-store` |
| "LLM", "foundation model", "inference", "completions" | `foundation-model-api` |
| "schedule", "job", "orchestrate", "workflow trigger" | `workflows-jobs` |
| "governance", "rate limit", "guardrail", "cost tracking" | `ai-gateway` |

After applying keyword matching, also auto-include dependencies:
- `mas` selected → also include `lakebase` (per `auto_include_with`)
- `genie` selected → also include `mas` (per `auto_include_with`)
- `knowledge-assistant` selected → also include `mas`, `vector-search`
- `vector-search` selected → also include `knowledge-assistant`
- `foundation-model-api` selected → also include `ai-gateway`
- `lakeflow-connect` selected → also include `declarative-pipelines`
- `feature-store` selected → also include `model-serving`

### Step 4: Present the feature checklist

Display the feature menu grouped by category. Mark pre-selected features with `[x]` and recommended ones with `★`. If AI Dev Kit is not available, add `(manual setup)` next to each feature.

```
Based on your use cases, here are the recommended Databricks features:

━━━ AI & Agents ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[x] ★ Multi-Agent Supervisor (MAS)       — Orchestrates Genie, KA, MCP, UC functions
[x] ★ Genie Space                        — Natural language SQL over Delta Lake
[x] ★ Knowledge Assistant               — RAG over documents and domain wikis
[ ]   Foundation Model API              — Pay-per-token access to hosted LLMs
[ ]   AI/BI Dashboard                   — Embedded dashboards with NL editing
[ ]   AI Gateway                        — Rate limits, guardrails, cost tracking

━━━ Data Platform ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[x] ★ Lakebase                          — PostgreSQL OLTP for agent writes
[ ]   Live Feed                         — Real-time streaming simulation
[ ]   Declarative Pipelines (DLT)       — Serverless incremental ETL
[ ]   Lakeflow Connect                  — Managed source connectors

━━━ ML ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ]   Model Serving                     — Deploy custom ML models as endpoints
[ ]   Feature Store                     — Versioned ML feature tables in UC
[ ]   Vector Search                     — Semantic similarity over Delta Lake

━━━ Operational ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[ ]   Workflows & Jobs                  — Schedule and orchestrate jobs

Type the feature IDs to toggle on/off, or say "looks good" to continue.
```

Wait for the user to confirm or adjust selections before proceeding.

---

## Phase 3: UI Preferences

Ask these in a single block:

```
Almost done! A few UI questions:

1. Layout:
   a) Sidebar nav — best for 5+ pages, full-featured apps (default)
   b) Top nav bar — clean, 3-4 pages
   c) Dashboard-first — command center, everything on one page

2. Color theme — I'll suggest one based on your industry, or you can override:
   - Manufacturing / industrial → dark navy + amber (#F59E0B)
   - Healthcare / life sciences → clean white/light + teal (#0D9488)
   - Financial / banking → corporate navy + blue (#3B82F6)
   - Agriculture / supply chain → dark + emerald (#10B981)
   - Technology / SaaS → dark charcoal + violet (#8B5CF6)
   - Retail / e-commerce → dark + rose (#F43F5E)
   - Custom — provide your own hex accent color

3. Mode: dark (default) or light?

4. Dashboard description — what should the main landing page show?
   (e.g., "KPI cards for OEE, active alerts table, morning briefing from AI, asset health chart")

5. Additional pages — beyond AI Chat and Agent Workflows (included free), what domain pages do you need?
   (e.g., "Asset inventory, maintenance history, parts catalog, shift handoff log")
```

---

## Output: Write demo-config.yaml

After all three phases, write `demo-config.yaml` at the project root with the full configuration:

```yaml
# Generated by /new-demo wizard
demo:
  name: "Apex Steel Predictive Maintenance"
  customer: "Apex Steel"
  industry: "manufacturing"
  use_cases:
    - "Anomaly detection on CNC machine vibration data"
    - "Automated work order creation via AI agent"
    - "Spare parts inventory optimization"

databricks:
  workspace_url: "https://fe-sandbox-serverless-apex-steel.cloud.databricks.com"
  cli_profile: "apex-steel"
  catalog: "serverless_apex_steel_catalog"
  schema: "predictive_maintenance"
  sql_warehouse_id: "abc123def456"
  ai_dev_kit: true   # or false if not detected

features:
  selected:
    - mas
    - genie
    - lakebase
    - live-feed
    - model-serving
  # env vars to be filled in during provisioning
  env_vars: {}

ui:
  layout: "sidebar"      # sidebar | topnav | dashboard-first
  theme: "dark"          # dark | light
  accent_color: "#F59E0B"
  brand_name: "Apex Steel"
  dashboard_description: "KPI cards for OEE and MTBF, active alerts table, morning briefing from AI"
  pages:
    - id: "assets"
      title: "Asset Inventory"
      description: "CNC machine list with health scores and last maintenance"
    - id: "maintenance"
      title: "Maintenance History"
      description: "Work orders, completed repairs, parts used"
    - id: "analytics"
      title: "Sensor Analytics"
      description: "Vibration, temperature, and pressure time-series charts"
```

---

## Post-Wizard: Feature Activation Flow

After writing `demo-config.yaml`, iterate through each selected feature and activate it:

### For each feature:

1. **Read the feature's `skill.md`** at `features/<id>/skill.md` if it exists — it contains wiring instructions specific to that feature.
2. **Copy `routes.py`** from `features/<id>/routes.py` to `app/backend/routes/<id>.py` if the file exists.
3. **Mount the router** in `app/backend/main.py` by adding the import and `app.include_router()` call after the `# DOMAIN ROUTES` marker.
4. **Add env vars** from the feature's `config.json` `env_vars` list to `app/app.yaml`.
5. **Use AI Dev Kit to provision** if `ai_dev_kit: true` in `demo-config.yaml` and the feature has `required_tools`. Call those tools to create the resource, then write the returned IDs back into `demo-config.yaml` under `features.env_vars`.
6. **If AI Dev Kit is not available** — print the manual CLI commands the user needs to run, based on the patterns in the resource docs.

### Feature-specific wiring notes:

**`lakebase`:** Follow `skills/resources/LAKEBASE.md` for connection pooling, SP permission grants, resource registration, and the ephemeral workspace recovery checklist. The app must register the database resource via `databricks apps update` AND redeploy before `PGHOST` is injected.

**`mas` + `lakebase`:** Deploy the Lakebase MCP Server from `lakebase-mcp-server/` as a separate Databricks App. Follow `skills/resources/LAKEBASE_MCP_SERVER.md` for deployment, UC HTTP connection creation, and wiring into MAS as an `external-mcp-server` agent. MAS agent types use kebab-case (`genie-space`, `external-mcp-server`, `knowledge-assistant`).

**`genie`:** Create a blank Genie Space first (POST), then PATCH tables via `serialized_space` JSON string with alphabetically sorted dotted identifiers. `table_identifiers` field is silently ignored — only `serialized_space` works. Grant `CAN_RUN` to app SP and users group via `/api/2.0/permissions/genie/<space_id>` (NOT `genie/spaces`).

**`live-feed`:** Import `LiveFeedEngine` and `create_streaming_router` from `app/backend/core/livefeed.py`. Configure streams and entities, then mount the streaming router. The engine runs as a background `asyncio.Task` and auto-stops after the configured duration.

**`model-serving`:** Use `databricks-claude-sonnet-4-5` or `databricks-claude-sonnet-4` for LLM endpoints. Use the Databricks-hosted model serving endpoint pattern from the workspace.

**`aibi-dashboard`:** Use `create_or_update_dashboard` and `publish_dashboard` AI Dev Kit tools if available. Set `AIBI_DASHBOARD_ID` in `app.yaml` after creation.

**`declarative-pipelines`:** Follow `skills/resources/DATA_GENERATION_SERVERLESS.md` for serverless client version compatibility. Use Python 3.12 with `client: "4"` in `databricks.yml`.

### Generate `demo-config.ts`

After activating all features, generate `app/frontend/src/demo-config.ts` (or `client/src/demo-config.ts` depending on scaffold layout) from the finalized `demo-config.yaml`. This file exports typed constants consumed by React components:

```typescript
// AUTO-GENERATED from demo-config.yaml — do not edit manually
export const DEMO_CONFIG = {
  name: "Apex Steel Predictive Maintenance",
  customer: "Apex Steel",
  industry: "manufacturing",
  accentColor: "#F59E0B",
  features: {
    mas: true,
    genie: true,
    lakebase: true,
    liveFeed: true,
    modelServing: true,
  },
  pages: [
    { id: "assets", title: "Asset Inventory" },
    { id: "maintenance", title: "Maintenance History" },
  ],
} as const;
```

### Generate React pages and domain components

For each page listed in `demo-config.yaml` under `ui.pages`:
1. Generate a React page component at `client/src/pages/<PageId>.tsx` (or equivalent path in the scaffold)
2. Add a nav entry in the sidebar/topnav per the chosen layout
3. Add the page to the `PAGES` array and `PAGE_TITLES` map in the JS navigation system
4. Wire a `load<PageId>()` function to `fetchApi()` calls

Follow the design standards from the project's `CLAUDE.md`:
- No Inter font, no purple gradients, no cookie-cutter layouts
- Dark theme: deep navy/charcoal base (`#0A0F1C`, `#111827`)
- Typography: Space Mono for data, Plus Jakarta Sans or Satoshi for UI
- Use the accent color from `demo-config.yaml` for CTA and highlights
- Framer Motion for transitions and staggered reveals
- Skeleton screens for loading states, not spinners

---

## Deployment Sequence (summary)

Follow the full sequence in `CLAUDE.md` under "Deployment Sequence". The critical ordering rule:

**Data notebooks (Phases A-B) MUST run before app deployment (Phase D).** If you deploy the app first, the dashboard will show zeros because the Delta Lake tables don't exist yet.

1. Phase A: Run `notebooks/01_setup_schema.sql` and `notebooks/02_generate_data.py`
2. Phase B: Create Lakebase instance, apply `lakebase/core_schema.sql` + `lakebase/domain_schema.sql`
3. Phase C: Create Genie Space, deploy Lakebase MCP Server, create MAS
4. Phase D: Deploy app, register resources via API, redeploy for `PGHOST` injection, grant SP permissions

For Databricks Apps devloop, follow `skills/resources/DATABRICKS_APPS.md` — local run → Chrome DevTools validation → remote deploy → `/logz` for crash logs.

---

## Guidelines

1. **Always use FEVM workspaces** for customer-facing demos and anything with Databricks Apps.
2. **Always use `uv`** for Python — never `pip` or `python` standalone.
3. **Always use Unity Catalog** — 3-layer namespaces, never Hive Metastore, never DBFS.
4. **Serverless only** — never classic clusters. Serverless client version 4 for Python 3.12.
5. **All blocking I/O via `asyncio.to_thread()`** in FastAPI routes.
6. **Parameterized queries** (`%s`) for Lakebase, `_safe()` for Delta Lake filter values.
7. **Node.js / React frontend** for customer-facing apps. Python frameworks only for internal tools.
8. **Two starter pages are pre-built** (AI Chat + Agent Workflows) — customize them, do not rebuild.
9. **Resource registration is mandatory** — `app.yaml` resources are documentation only. Always register via `databricks apps update --json` and redeploy.
10. If the demo needs Snowflake integration, use the `fe-snowflake` skill.
