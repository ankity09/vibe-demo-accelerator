# Lakebase Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-demo` skill (loads `resources/LAKEBASE.md` and `resources/LAKEBASE_MCP_SERVER.md`)
- MCP tools: `databricks_cli` (for instance creation and psql commands)
- A Databricks CLI profile configured for the target workspace
- `lakebase/core_schema.sql` and `lakebase/domain_schema.sql` prepared

## Provisioning (via AI Dev Kit)
Use AI Dev Kit MCP tools — do NOT use raw REST API calls:
1. `databricks_cli` — Create the Lakebase instance:
   ```bash
   databricks database create-database-instance <instance-name> --capacity CU_1 --profile=<profile>
   ```
   Instance name uses HYPHENS, not underscores. `CU_1` is sufficient for demos.
2. Poll until state is `AVAILABLE` (not `RUNNING`):
   ```bash
   databricks database get-database-instance <instance-name> --profile=<profile> -o json | jq '.state'
   ```
3. Create the database:
   ```bash
   databricks psql <instance-name> --profile=<profile> -- -c "CREATE DATABASE <db_name>;"
   ```
4. Apply schemas (do NOT grant SP access yet — SP role doesn't exist until after resource registration):
   ```bash
   databricks psql <instance-name> --profile=<profile> -- -d <db_name> -f lakebase/core_schema.sql
   databricks psql <instance-name> --profile=<profile> -- -d <db_name> -f lakebase/domain_schema.sql
   ```
5. Register as app resource via API, then redeploy (PGHOST is only injected at deploy time):
   ```bash
   databricks apps update <app-name> --json '{
     "resources": [
       ...,
       {"name":"database","database":{"instance_name":"<instance-name>","database_name":"<db_name>","permission":"CAN_CONNECT_AND_CREATE"}}
     ]
   }' --profile=<profile>
   databricks apps deploy <app-name> --source-code-path <path> --profile=<profile>
   ```
6. After redeploy, grant table access to the app SP:
   ```bash
   databricks psql <instance-name> --profile=<profile> -- -d <db_name> -c "
   GRANT ALL ON ALL TABLES IN SCHEMA public TO \"<app-sp-client-id>\";
   GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO \"<app-sp-client-id>\";
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO \"<app-sp-client-id>\";
   ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO \"<app-sp-client-id>\";
   "
   ```
7. Seed data (do NOT use serverless notebooks — ephemeral `spark-*` users have no Lakebase role):
   ```bash
   databricks psql <instance-name> --profile=<profile> -- -d <db_name> -f /tmp/seed.sql
   ```

## VDA App Wiring
1. `core/lakebase.py` is already wired — DO NOT MODIFY. It handles connection pooling, OAuth token refresh, and automatic retry on `InterfaceError`/`OperationalError`.
2. Use the core functions in all routes:
   - `run_pg_query(sql, params)` — read queries, returns `list[dict]`
   - `write_pg(sql, params)` — INSERT/UPDATE/DELETE, use `RETURNING *` to get created row
3. Always use parameterized queries (`%s`) for Lakebase — never f-strings with user input.
4. Always use `asyncio.to_thread()` for all `run_pg_query` / `write_pg` calls (they are blocking I/O).
5. Always use `asyncio.gather(..., return_exceptions=True)` when mixing Delta + Lakebase queries.
6. Update `app/app.yaml` env vars (resource registration injects PGHOST/PGPORT/PGDATABASE/PGUSER automatically — do NOT set these manually):
   ```yaml
   resources:
     - name: database
       database:
         instance_name: "<instance-name>"
         database_name: "<db_name>"
         permission: CAN_CONNECT_AND_CREATE
   ```

## MAS Integration
Wire the Lakebase MCP Server as an `external-mcp-server` sub-agent in MAS to give the AI write access to Lakebase during chat. See `features/mas/skill.md` and `lakebase-mcp-server/CLAUDE.md` for full setup.

The 16 MCP tools available through the MCP server:
- READ: `list_tables`, `describe_table`, `read_query`, `list_schemas`, `get_connection_info`, `list_slow_queries`
- WRITE: `insert_record`, `update_records`, `delete_records`, `batch_insert`
- SQL: `execute_sql`, `execute_transaction`, `explain_query`
- DDL: `create_table`, `drop_table`, `alter_table`

In MAS instructions, reference tool names explicitly (not "use Lakebase" — the model needs exact tool names):
```
To record a work order, use insert_record with table="work_orders" and the appropriate fields.
To update status, use update_records with a WHERE clause on the primary key.
```

## Manual Setup (fallback without AI Dev Kit)
See `CLAUDE.md` Deployment Sequence Phase B for the complete step-by-step. Key CLI commands:
```bash
# Create instance (hyphens, not underscores)
databricks database create-database-instance <name> --capacity CU_1 --profile=<profile>

# Wait for AVAILABLE state (not RUNNING)
watch -n 10 "databricks database get-database-instance <name> --profile=<profile> -o json | jq '.state'"

# Connect and create database
databricks psql <name> --profile=<profile> -- -c "CREATE DATABASE <db>;"

# Apply schemas
databricks psql <name> --profile=<profile> -- -d <db> -f lakebase/core_schema.sql
databricks psql <name> --profile=<profile> -- -d <db> -f lakebase/domain_schema.sql

# Seed (use local CLI, not serverless notebooks)
databricks database generate-database-credential \
  --json '{"instance_names":["<name>"],"request_id":"seed"}' \
  --profile=<profile>
```
