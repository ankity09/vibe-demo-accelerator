# Feature Store

Databricks Feature Store provides a centralized repository for ML features stored as Unity Catalog
tables. Features are versioned, documented, and reusable across training and online serving.

## What it does
- Stores pre-computed features (aggregations, rolling statistics, embeddings) as Delta tables
- Enables point-in-time correct feature lookups for training data generation
- Supports online feature serving via Lakebase or DynamoDB for low-latency inference
- Documents feature lineage and enables feature reuse across models and teams

## Prerequisites
- Unity Catalog enabled in the workspace
- `databricks-feature-engineering` package installed
- Delta Lake tables with entity keys (e.g., asset_id, customer_id, order_id)

## Setup
1. Install `databricks-feature-engineering` in `requirements.txt`
2. Define a `FeatureTable` with a primary key matching your entity
3. Write features using `FeatureEngineeringClient.write_table()`
4. Set `FEATURE_TABLE_NAME` in `app.yaml`
5. Use `create_training_set()` for training and `score_batch()` for batch inference

## Connection to the Demo
Feature Store makes the ML story more credible in the demo. Show a "features" panel
that displays the latest computed features for a selected entity (e.g., asset health
indicators, customer lifetime value signals) before the model scoring step.
