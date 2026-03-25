# Lakeflow Connect Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-demo` skill
- MCP tools: `run_notebook_or_sql`, `create_databricks_job`
- Source system credentials available (Salesforce, ServiceNow, SAP, SharePoint, etc.)
- Databricks workspace with Lakeflow Connect (Ingestion) enabled — available in FEVM workspaces
- Unity Catalog with a target schema for ingested tables

## Provisioning (via AI Dev Kit)
Use AI Dev Kit MCP tools — do NOT use raw REST API calls:
1. `run_notebook_or_sql` — Create a Lakeflow Connect ingestion pipeline via the Databricks Pipelines API, specifying the source connector type, credentials (stored in Databricks Secrets), and target Unity Catalog location.
2. `create_databricks_job` — Schedule the ingestion pipeline to run on a cadence (hourly, daily) using a Databricks Job with a pipeline task.

Ingestion pipeline creation:
```bash
databricks pipelines create --json '{
  "name": "<Demo> <Source> Ingestion",
  "ingestion_definition": {
    "connection_name": "<uc-connection-name>",
    "ingestion_gateway_id": "<gateway-id>",
    "objects": [
      {
        "schema": {
          "source_schema": "<source-schema>",
          "destination_catalog": "<catalog>",
          "destination_schema": "<schema>"
        }
      }
    ]
  },
  "serverless": true,
  "catalog": "<catalog>",
  "target": "<schema>"
}' --profile=<profile>
```

First, create the UC connection for the source system:
```bash
databricks connections create \
  --name "<source>-connection" \
  --connection-type "<Salesforce|ServiceNow|SAP|...>" \
  --options '{"host":"<source-url>","username":"<user>","password":"{{secrets/<scope>/<key>}}"}' \
  --profile=<profile>
```

## VDA App Wiring
1. Lakeflow Connect populates Delta Lake tables in Unity Catalog. The VDA app reads these tables via `run_query()` the same as any other Delta table. No Lakeflow-specific routes are needed.
2. To show ingestion freshness in the dashboard, query the pipeline event log:
   ```python
   @router.get("/ingestion/status")
   async def ingestion_status():
       rows = await asyncio.to_thread(
           run_query,
           f"""SELECT
             MAX(timestamp) as last_sync,
             COUNT(DISTINCT origin.flow_name) as tables_synced,
             SUM(CASE WHEN event_type='flowProgress' THEN details.flow_progress.num_output_rows ELSE 0 END) as rows_ingested
           FROM {CATALOG}.{SCHEMA}.{PIPELINE_EVENT_LOG_TABLE}
           WHERE timestamp >= CURRENT_TIMESTAMP() - INTERVAL '24' HOUR"""
       )
       return rows[0] if rows else {}
   ```
3. Add env var in `app/app.yaml`:
   ```yaml
   - name: LAKEFLOW_PIPELINE_ID
     value: "<pipeline-id>"
   ```
4. Frontend: Add a "Data Sources" section to the dashboard showing which source systems are connected, last sync time, and row counts. Use `.badge-green` / `.badge-amber` for sync health status.

## MAS Integration
Lakeflow Connect tables are Delta Lake tables queryable by Genie Space. Add all ingested tables to the Genie Space `serialized_space` (sorted alphabetically):
```json
{"identifier": "<catalog>.<schema>.<ingested_table_1>"},
{"identifier": "<catalog>.<schema>.<ingested_table_2>"}
```

MAS instructions should tell the Genie sub-agent what each ingested table represents, so the model knows which source system the data came from:
```
The <source_system> table contains data ingested from <source> via Lakeflow Connect.
Fields: <key_fields>. Use this for questions about <domain> from <source_system>.
```

## Manual Setup (fallback without AI Dev Kit)
1. In the Databricks workspace UI, go to **Data Engineering > Ingestion**.
2. Click **+ Add data source** and select the connector type (Salesforce, ServiceNow, SAP HANA, PostgreSQL, MySQL, SharePoint, etc.).
3. Provide connection credentials (store secrets in a Databricks secret scope first):
   ```bash
   databricks secrets create-scope <scope-name> --profile=<profile>
   databricks secrets put-secret <scope-name> <key-name> --string-value "<secret-value>" --profile=<profile>
   ```
4. Select the target catalog, schema, and tables to ingest.
5. Configure sync mode (full refresh or incremental) and schedule.
6. Start the pipeline and verify tables appear in Unity Catalog.

Grant app SP access to ingested tables:
```sql
GRANT SELECT ON SCHEMA <catalog>.<schema> TO `<app-sp-client-id>`;
```
