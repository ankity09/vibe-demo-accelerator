# MAS (Multi-Agent Supervisor) Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-demo` skill
- MCP tools: `create_or_update_mas`, `get_mas_details`
- Sub-agents provisioned first: Genie Space (see `features/genie/skill.md`), Knowledge Assistant (see `features/knowledge-assistant/skill.md`)
- SQL warehouse and Lakebase instance available
- Lakebase MCP Server deployed (see `features/lakebase/skill.md`) if agent writes are needed

## Provisioning (via AI Dev Kit)
Use AI Dev Kit MCP tools — do NOT use raw REST API calls:
1. `create_or_update_mas` — Create the MAS with name, description, instructions, and sub-agents array. Note: `create_or_update_mas` does NOT support `unity-catalog-function` or `external-mcp-server` agent types — create with `genie-space` and `knowledge-assistant` agents first, then PATCH to add MCP agents via REST API.
2. After creation, discover the full tile UUID:
   ```bash
   databricks api get /api/2.0/serving-endpoints --profile=<profile> | \
     jq '.endpoints[] | select(.name | startswith("mas-")) | .tile_endpoint_metadata.tile_id'
   ```
3. PATCH to add `external-mcp-server` or `unity-catalog-function` agents:
   ```bash
   databricks api patch /api/2.0/multi-agent-supervisors/<full-tile-uuid> \
     --json '{"name":"<name>","agents":[... ALL existing agents + new agents ...]}' \
     --profile=<profile>
   ```
4. Grant `CAN_QUERY` on the MAS serving endpoint to the app SP:
   ```bash
   # Get endpoint UUID (not name)
   databricks api get /api/2.0/serving-endpoints --profile=<profile> | \
     jq '.endpoints[] | select(.name=="mas-<8chars>-endpoint") | .id'
   # Grant
   databricks api patch /api/2.0/permissions/serving-endpoints/<endpoint-uuid> \
     --json '{"access_control_list":[{"service_principal_name":"<app-sp-client-id>","permission_level":"CAN_QUERY"}]}' \
     --profile=<profile>
   ```

## VDA App Wiring
1. No `routes.py` to copy — MAS is wired via `app/backend/routes/chat.py` (already present in scaffold).
2. Fill `app/app.yaml` env vars:
   ```yaml
   - name: MAS_TILE_ID
     value: "<first-8-chars-of-tile-uuid>"  # NOT the full UUID
   ```
3. Register MAS endpoint as app resource (and redeploy):
   ```bash
   databricks apps update <app-name> --json '{
     "resources": [
       ...,
       {"name":"mas-endpoint","serving_endpoint":{"name":"mas-<8chars>-endpoint","permission":"CAN_QUERY"}}
     ]
   }' --profile=<profile>
   databricks apps deploy <app-name> --source-code-path <path> --profile=<profile>
   ```
4. Enable OBO (user token forwarding) so MCP tool calls work:
   ```bash
   databricks api patch /api/2.0/apps/<app-name> \
     --json '{"user_api_scopes":["serving.serving-endpoints","sql"]}' \
     --profile=<profile>
   ```
5. Frontend: The AI Chat page is already wired. Customize the welcome card text and `formatAgentName()` map in the frontend to match sub-agent names. Do NOT rebuild the chat component.

## MAS Agent Type Reference
All agent types use kebab-case:
```json
{ "agent_type": "genie-space", "genie_space": { "id": "<space_id>" } }
{ "agent_type": "knowledge-assistant", "knowledge_assistant": { "knowledge_assistant_id": "<ka_id>" } }
{ "agent_type": "unity-catalog-function", "unity_catalog_function": { "uc_path": { "catalog": "...", "schema": "...", "name": "..." } } }
{ "agent_type": "external-mcp-server", "external_mcp_server": { "connection_name": "<uc-connection-name>" } }
```

## Streaming Protocol
The VDA `core/streaming.py` handles:
- Auto-approval of MCP tool calls (10-round limit)
- Phase tracking: intermediate rounds emit `thinking`, final round emits `delta`
- OBO token forwarding from `x-forwarded-access-token` header
- `max_turns: 15` to prevent early budget exhaustion in multi-tool workflows
- Keepalive SSE comments every 15s to prevent proxy timeouts

## Manual Setup (fallback without AI Dev Kit)
```bash
# Step 1: Create MAS (without MCP agents — add those via PATCH)
databricks api post /api/2.0/multi-agent-supervisors --json '{
  "name": "<Demo>_Supervisor",
  "description": "...",
  "instructions": "...",
  "agents": [
    {"agent_type":"genie-space","genie_space":{"id":"<space_id>"},"name":"<demo>_data","description":"..."},
    {"agent_type":"knowledge-assistant","knowledge_assistant":{"knowledge_assistant_id":"<ka_id>"},"name":"<demo>_kb","description":"..."}
  ]
}' --profile=<profile>

# Step 2: Discover tile ID (no list endpoint — search serving endpoints)
databricks api get /api/2.0/serving-endpoints --profile=<profile> | \
  jq '.endpoints[] | select(.name | startswith("mas-")) | .tile_endpoint_metadata.tile_id'

# Step 3: PATCH to add external-mcp-server (must include ALL agents)
databricks api patch /api/2.0/multi-agent-supervisors/<full-uuid> --json '{
  "name": "<Demo>_Supervisor",
  "agents": [
    ... all existing agents ...,
    {"agent_type":"external-mcp-server","external_mcp_server":{"connection_name":"<uc-connection>"},"name":"mcp-lakebase-connection","description":"Write to Lakebase..."}
  ]
}' --profile=<profile>
```
