# Workflows & Jobs Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-demo` skill
- MCP tools: `create_databricks_job`, `run_databricks_job`, `get_job_run_status`
- Notebooks or Python scripts to be scheduled (data generation, model retraining, pipeline refresh)
- Databricks workspace with serverless job compute available (all FEVM workspaces)

## Provisioning (via AI Dev Kit)
Use AI Dev Kit MCP tools — do NOT use raw REST API calls:
1. `create_databricks_job` — Create a Databricks Job with one or more tasks. Use serverless compute (`"serverless": true`) to eliminate cluster management. Supported task types: notebook, Python script, DLT pipeline, SQL, Delta Live Tables.
2. `run_databricks_job` — Trigger a one-time run for testing.
3. `get_job_run_status` — Poll the run until completion, capturing any errors.

Job creation example (data refresh job):
```bash
databricks jobs create --json '{
  "name": "<Demo> Data Refresh",
  "tasks": [
    {
      "task_key": "generate_data",
      "notebook_task": {
        "notebook_path": "/Workspace/Users/<you>/notebooks/02_generate_data",
        "base_parameters": {"catalog": "<catalog>", "schema": "<schema>"}
      },
      "new_cluster": {"num_workers": 0, "spark_version": "15.4.x-scala2.12", "node_type_id": "i3.xlarge"}
    }
  ],
  "schedule": {
    "quartz_cron_expression": "0 0 6 * * ?",
    "timezone_id": "America/Los_Angeles",
    "pause_status": "PAUSED"
  }
}' --profile=<profile>
```

For serverless jobs (recommended):
```bash
databricks jobs create --json '{
  "name": "<Demo> Data Refresh",
  "tasks": [{
    "task_key": "refresh",
    "notebook_task": {"notebook_path": "/Workspace/Users/<you>/notebooks/02_generate_data"},
    "environment_key": "default"
  }],
  "environments": [{"environment_key":"default","spec":{"client":"1","dependencies":[]}}]
}' --profile=<profile>
```

## VDA App Wiring
1. The Agent Workflows page (`app/backend/routes/workflows.py`) is already included in the scaffold — it manages the `workflows` and `agent_actions` Lakebase tables, not Databricks Jobs. These are separate concepts:
   - **Workflows page** → human-in-the-loop agent action approvals (stored in Lakebase)
   - **Databricks Jobs** → scheduled data pipelines, model retraining, batch scoring
2. To surface job status in the VDA app, add `app/backend/routes/jobs.py`:
   ```python
   import asyncio, os
   from fastapi import APIRouter
   from databricks.sdk import WorkspaceClient

   router = APIRouter()
   w = WorkspaceClient()
   JOB_IDS = {
       "data_refresh": os.getenv("JOB_ID_DATA_REFRESH", ""),
       "model_retrain": os.getenv("JOB_ID_MODEL_RETRAIN", ""),
   }

   @router.get("/jobs/status")
   async def jobs_status():
       results = {}
       for name, job_id in JOB_IDS.items():
           if not job_id:
               continue
           runs = await asyncio.to_thread(
               w.jobs.list_runs, job_id=int(job_id), limit=1
           )
           run_list = list(runs)
           if run_list:
               results[name] = {
                   "state": run_list[0].state.life_cycle_state.value if run_list[0].state else "UNKNOWN",
                   "result": run_list[0].state.result_state.value if run_list[0].state and run_list[0].state.result_state else None,
                   "start_time": run_list[0].start_time,
               }
       return {"jobs": results}

   @router.post("/jobs/{job_name}/trigger")
   async def trigger_job(job_name: str):
       job_id = JOB_IDS.get(job_name)
       if not job_id:
           from fastapi import HTTPException
           raise HTTPException(404, f"Job '{job_name}' not configured")
       run = await asyncio.to_thread(w.jobs.run_now, job_id=int(job_id))
       return {"run_id": run.run_id}
   ```
3. Mount in `app/backend/main.py`:
   ```python
   from backend.routes.jobs import router as jobs_router
   app.include_router(jobs_router, prefix="/api")
   ```
4. Add env vars in `app/app.yaml`:
   ```yaml
   - name: JOB_ID_DATA_REFRESH
     value: "<job-id>"
   - name: JOB_ID_MODEL_RETRAIN
     value: "<job-id>"
   ```
5. Frontend: Add job status badges to the dashboard sidebar or a "Pipelines" status page showing each job's last run state with a "Run Now" button. Use `.badge-green` (SUCCESS), `.badge-amber` (RUNNING), `.badge-red` (FAILED).

## MAS Integration
Expose job triggering as a Unity Catalog function so MAS can trigger data refreshes or model retraining during chat:
```sql
CREATE FUNCTION <catalog>.<schema>.trigger_data_refresh(job_name STRING)
RETURNS STRING
LANGUAGE PYTHON AS $$
from databricks.sdk import WorkspaceClient
import os
w = WorkspaceClient()
job_ids = {"data_refresh": os.getenv("JOB_ID_DATA_REFRESH", "")}
job_id = job_ids.get(job_name)
if not job_id:
    return f"Unknown job: {job_name}"
run = w.jobs.run_now(job_id=int(job_id))
return f"Triggered {job_name}, run_id={run.run_id}"
$$;
```
Add to MAS agents via REST API PATCH:
```json
{
  "agent_type": "unity-catalog-function",
  "unity_catalog_function": { "uc_path": { "catalog": "<catalog>", "schema": "<schema>", "name": "trigger_data_refresh" } },
  "name": "<demo>_pipeline_trigger",
  "description": "Trigger a Databricks Job for data refresh or model retraining. Use when the user asks to refresh data or retrain the model."
}
```

## Manual Setup (fallback without AI Dev Kit)
```bash
# List existing jobs
databricks jobs list --profile=<profile>

# Create a job
databricks jobs create --json-file jobs/data_refresh.json --profile=<profile>

# Run immediately
databricks jobs run-now --job-id <id> --profile=<profile>

# Get run status
databricks runs get --run-id <run-id> --profile=<profile> | jq '.state'

# Cancel a run
databricks runs cancel --run-id <run-id> --profile=<profile>
```
