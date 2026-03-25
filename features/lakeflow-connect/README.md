# Lakeflow Connect

Lakeflow Connect provides managed, low-code connectors for ingesting data from enterprise SaaS
and database sources (Salesforce, SAP, Workday, ServiceNow, PostgreSQL, MySQL) directly into
Delta Lake with automated schema mapping and incremental sync.

## What it does
- Establishes CDC (change data capture) or scheduled snapshot ingestion from source systems
- Automatically creates Delta Lake tables with matched schemas from the source
- Handles authentication, pagination, rate limiting, and retry logic for each connector
- Feeds into Declarative Pipelines for downstream transformation

## Prerequisites
- Source system credentials (API key, OAuth tokens, JDBC URL)
- Lakeflow Connect connector enabled in the workspace (may require enablement request)
- Target Unity Catalog schema with write permissions

## Setup
1. Navigate to Lakeflow Connect in the Databricks workspace UI (Data Ingestion)
2. Select the source connector and enter credentials
3. Configure target catalog/schema and sync schedule
4. Note the pipeline ID and set `LAKEFLOW_PIPELINE_ID` in `app.yaml`
5. No AI Dev Kit tools are available — configuration is done via the workspace UI or REST API

## Connection to the Demo
Lakeflow Connect makes the data ingestion story concrete. Show customers how their Salesforce
opportunities, SAP inventory records, or Workday HR data flows into Delta Lake automatically —
no custom ETL code, no Spark expertise required.
