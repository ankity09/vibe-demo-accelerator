# Workflows & Jobs

Databricks Workflows is the native orchestration service for scheduling and running multi-task
data pipelines, notebooks, Python scripts, and Delta Live Tables pipelines.

## What it does
- Defines multi-task DAGs with dependencies, retry logic, and alerting
- Triggers on a schedule (cron), on file arrival, or via REST API
- Integrates with DLT pipelines, SQL tasks, dbt, and arbitrary Python scripts
- Shows run history, task duration, and failure reasons in the workspace UI

## Prerequisites
- Notebooks or scripts uploaded to the workspace or a Git repo connected
- Workflow job created via AI Dev Kit `manage_jobs` or the Workflows UI
- App SP has `CAN_MANAGE_RUN` or `IS_OWNER` on the job

## Setup
1. Create a workflow via AI Dev Kit `manage_jobs` or the Databricks Workflows UI
2. Add tasks: notebook paths, Python scripts, or DLT pipeline references
3. Set schedule and configure alerts (email on failure)
4. Note the job ID and set `WORKFLOW_JOB_ID` in `app.yaml`
5. Trigger runs via `/api/2.0/jobs/run-now` from a FastAPI endpoint for interactive demos

## Connection to the Demo
Workflows makes the operational story tangible. A "Run Data Refresh" button in the frontend
can trigger the data generation job via the REST API and poll for completion, showing a live
progress indicator — demonstrating how the customer's data pipelines would run in production.
