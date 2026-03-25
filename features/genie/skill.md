# Genie Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-genie` skill
- MCP tools: `create_or_update_genie`, `ask_genie`
- SQL warehouse provisioned and its ID available

## Provisioning (via AI Dev Kit)
Use AI Dev Kit MCP tools — do NOT use raw REST API calls:
1. `create_or_update_genie` — Create a Genie Space with title, description, warehouse ID, and tables (dotted 3-part identifiers sorted alphabetically). Tables MUST be passed via `serialized_space` — the `table_identifiers` field is silently ignored.
2. `ask_genie` — Validate the space by asking a test question against the connected tables.

After creation, grant `CAN_RUN` to the `users` group:
```bash
databricks api patch /api/2.0/permissions/genie/<space_id> \
  --json '{"access_control_list":[{"group_name":"users","permission_level":"CAN_RUN"}]}' \
  --profile=<profile>
```
Note: the endpoint is `/permissions/genie/{id}`, NOT `/permissions/genie/spaces/{id}` (returns 404).

## VDA App Wiring
1. No `routes.py` for Genie — queries go through MAS. Skip backend step unless building a direct Genie query endpoint.
2. Set env var in `app/app.yaml`:
   ```yaml
   - name: GENIE_SPACE_ID
     value: "<space_id>"
   ```
3. Genie is always wired via MAS — add it as a `genie-space` sub-agent in `agent_bricks/mas_config.json` (see MAS Integration below).
4. Frontend: the AI Chat page (`POST /api/chat`) already surfaces Genie results through MAS streaming. No additional React component needed. Optionally build a standalone `GeniePanel` that calls `POST /api/genie/ask` if direct querying is desired.

## MAS Integration
Add to `agent_bricks/mas_config.json` `agents` array:
```json
{
  "agent_type": "genie-space",
  "genie_space": { "id": "<GENIE_SPACE_ID>" },
  "name": "<demo>_data",
  "description": "Query <domain> data tables using natural language. Use for any questions about historical metrics, aggregations, or trends."
}
```
Wire MAS first (see `features/mas/skill.md`) — Genie is always a sub-agent, never a top-level endpoint.

## Manual Setup (fallback without AI Dev Kit)
```bash
# 1. Create blank Genie Space
databricks api post /api/2.0/genie/spaces \
  --json '{"serialized_space":"{\"version\":2}","warehouse_id":"<warehouse-id>"}' \
  --profile=<profile>
# Returns: {"space_id": "abc123..."}

# 2. Set title and description
databricks api patch /api/2.0/genie/spaces/<space_id> \
  --json '{"title":"<Demo> Data","description":"<description>"}' \
  --profile=<profile>

# 3. Attach tables via serialized_space (SORTED ALPHABETICALLY)
databricks api patch /api/2.0/genie/spaces/<space_id> \
  --json '{"serialized_space":"{\"version\":2,\"data_sources\":{\"tables\":[{\"identifier\":\"cat.schema.table1\"},{\"identifier\":\"cat.schema.table2\"}]}}"}' \
  --profile=<profile>

# 4. Add instructions
databricks api patch /api/2.0/genie/spaces/<space_id> \
  --json '{"instructions":"You are a data assistant for <domain>. Always provide precise numbers."}' \
  --profile=<profile>

# 5. Verify tables are attached (check serialized_space, not table_identifiers — that field is always empty)
databricks api get "/api/2.0/genie/spaces/<space_id>?include_serialized_space=true" \
  --profile=<profile>

# 6. Grant permissions
databricks api patch /api/2.0/permissions/genie/<space_id> \
  --json '{"access_control_list":[{"group_name":"users","permission_level":"CAN_RUN"}]}' \
  --profile=<profile>
```
