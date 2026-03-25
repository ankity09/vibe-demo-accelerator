# Declarative Pipelines (Delta Live Tables)

Databricks Declarative Pipelines (DLT) is a framework for building reliable, auto-scaling
data pipelines with built-in data quality, lineage, and incremental processing.

## What it does
- Defines Bronze/Silver/Gold table transformations as simple Python or SQL annotated with `@dlt.table`
- Handles incremental updates, schema evolution, and checkpointing automatically
- Enforces data quality expectations with `@dlt.expect` — quarantines bad records
- Runs serverless (no cluster management) on a scheduled or triggered basis

## Prerequisites
- Delta Lake tables or external data sources as input
- Pipeline notebook stored in the workspace
- SQL Warehouse for the pipeline's query execution

## Setup
1. Create a pipeline notebook in the workspace with `@dlt.table` decorated functions
2. Create the pipeline via AI Dev Kit `create_or_update_pipeline` or the Pipelines UI
3. Set `DLT_PIPELINE_ID` in `app.yaml`
4. Trigger via the REST API (`start_update`) from a FastAPI endpoint or Workflow
5. Monitor pipeline status via `get_pipeline` to show progress in the demo UI

## Connection to the Demo
Use Declarative Pipelines to showcase the data lineage story. A "Data Freshness" panel
in the dashboard can show the last pipeline run time and row counts at each layer,
making the Bronze → Silver → Gold medallion architecture tangible to the customer.
