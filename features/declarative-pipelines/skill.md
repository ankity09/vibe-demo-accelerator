# Declarative Pipelines (DLT) Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-demo` skill
- MCP tools: `run_notebook_or_sql`, `create_databricks_job`
- Source data available (raw files in Unity Catalog volume, streaming source, or existing Delta tables)
- Delta Live Tables (DLT) enabled in the workspace (available in all FEVM workspaces)
- Serverless compute selected for DLT pipeline (no cluster management)

## Provisioning (via AI Dev Kit)
Use AI Dev Kit MCP tools — do NOT use raw REST API calls:
1. `run_notebook_or_sql` — Create the DLT pipeline notebook with `@dlt.table` and `@dlt.view` decorators defining the data transformation layers (bronze → silver → gold).
2. `create_databricks_job` — Create a Databricks Job that triggers the DLT pipeline on a schedule or as part of a workflow.

Pipeline creation via CLI:
```bash
databricks pipelines create --json '{
  "name": "<Demo> Data Pipeline",
  "serverless": true,
  "catalog": "<catalog>",
  "target": "<schema>",
  "libraries": [{"notebook": {"path": "/Workspace/Users/<you>/<demo>-pipeline"}}],
  "configuration": {
    "catalog": "<catalog>",
    "schema": "<schema>"
  }
}' --profile=<profile>
```

## VDA App Wiring
1. DLT pipelines produce Delta Lake tables that the VDA app reads via `run_query()`. No routes file specifically for DLT is needed — the app queries the output tables.
2. To surface pipeline status in the dashboard, add a pipeline status endpoint:
   ```python
   import asyncio, os
   from fastapi import APIRouter
   from databricks.sdk import WorkspaceClient

   router = APIRouter()
   w = WorkspaceClient()
   PIPELINE_ID = os.getenv("DLT_PIPELINE_ID", "")

   @router.get("/pipeline/status")
   async def pipeline_status():
       if not PIPELINE_ID:
           return {"status": "not_configured"}
       update = await asyncio.to_thread(
           w.pipelines.get_update, pipeline_id=PIPELINE_ID, update_id="latest"
       )
       return {
           "state": update.update.state.value if update.update.state else "unknown",
           "start_time": str(update.update.creation_time or ""),
       }
   ```
3. Mount in `app/backend/main.py`:
   ```python
   from backend.routes.pipeline import router as pipeline_router
   app.include_router(pipeline_router, prefix="/api")
   ```
4. Add env var in `app/app.yaml`:
   ```yaml
   - name: DLT_PIPELINE_ID
     value: "<pipeline-id>"
   ```
5. Frontend: Add a "Data Pipeline" status indicator in the dashboard header or sidebar showing the last pipeline run status (green = succeeded, amber = running, red = failed). Use a pulsing dot for "running" state. This is a strong talking point for data engineering–focused demos.

## MAS Integration
DLT pipelines are not directly invoked by MAS agents. However, pipeline output tables are available to Genie Space for NL querying. Ensure all gold-layer DLT tables are added to the Genie Space `serialized_space`.

To trigger a pipeline update from MAS (e.g., "refresh the data"), register a UC function:
```sql
CREATE FUNCTION <catalog>.<schema>.trigger_pipeline_update(pipeline_id STRING)
RETURNS STRING
LANGUAGE PYTHON AS $$
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
update = w.pipelines.start_update(pipeline_id=pipeline_id, full_refresh=False)
return f"Pipeline update triggered: {update.update_id}"
$$;
```

## Manual Setup (fallback without AI Dev Kit)
Write the DLT pipeline notebook:
```python
import dlt
from pyspark.sql.functions import *

@dlt.table(name="bronze_<entity>", comment="Raw ingested <entity> data")
def bronze_entity():
    return spark.read.format("json").load("/Volumes/<catalog>/<schema>/raw/<entity>/")

@dlt.table(name="silver_<entity>", comment="Cleaned and validated <entity> data")
@dlt.expect_or_drop("valid_id", "<entity_id> IS NOT NULL")
def silver_entity():
    return dlt.read("bronze_<entity>").withColumn(
        "processed_at", current_timestamp()
    ).dropDuplicates(["<entity_id>"])

@dlt.table(name="gold_<entity>_metrics", comment="Aggregated <entity> KPIs")
def gold_entity_metrics():
    return dlt.read("silver_<entity>").groupBy("<group_col>").agg(
        count("*").alias("total"),
        avg("<metric_col>").alias("avg_metric"),
    )
```

Grant app SP access to pipeline output tables:
```sql
GRANT SELECT ON TABLE <catalog>.<schema>.gold_<entity>_metrics TO `<app-sp-client-id>`;
```
