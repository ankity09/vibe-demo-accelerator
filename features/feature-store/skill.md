# Feature Store Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-demo` skill
- MCP tools: `run_notebook_or_sql` (for feature table creation), `query_serving_endpoint`
- A Delta Lake table with domain entities and raw features (created via `notebooks/02_generate_data.py`)
- Feature Store workspace feature enabled (available in all FEVM workspaces as part of Unity Catalog)
- SQL warehouse available for feature table queries

## Provisioning (via AI Dev Kit)
Use AI Dev Kit MCP tools — do NOT use raw REST API calls:
1. `run_notebook_or_sql` — Run the feature engineering notebook that creates Feature Store tables in Unity Catalog using `databricks.feature_engineering.FeatureEngineeringClient`. Tables are registered as standard Delta tables with feature metadata.
2. After feature table creation, use `create_model_serving_endpoint` to deploy an endpoint that uses the Feature Store for online serving with automatic feature lookup by primary key.

Feature engineering notebook pattern (run in serverless):
```python
from databricks.feature_engineering import FeatureEngineeringClient, FeatureLookup
fe = FeatureEngineeringClient()
fe.create_table(
    name=f"{CATALOG}.{SCHEMA}.<entity>_features",
    primary_keys=["<entity_id>"],
    df=feature_df,
    description="<Domain> features for ML scoring",
)
fe.write_table(name=f"{CATALOG}.{SCHEMA}.<entity>_features", df=feature_df, mode="merge")
```

## VDA App Wiring
1. Feature Store is primarily used at training/serving time, not directly at runtime. The VDA app typically reads pre-computed feature values from the Delta feature table directly via `run_query()`.
2. For real-time feature lookup during inference, create `app/backend/routes/features.py`:
   ```python
   import asyncio, os
   from fastapi import APIRouter
   from backend.core import run_query, _safe

   router = APIRouter()
   CATALOG = os.getenv("CATALOG", "")
   SCHEMA = os.getenv("SCHEMA", "")

   @router.get("/features/{entity_id}")
   async def get_features(entity_id: str):
       rows = await asyncio.to_thread(
           run_query,
           f"SELECT * FROM {CATALOG}.{SCHEMA}.<entity>_features WHERE entity_id = '{_safe(entity_id)}' LIMIT 1"
       )
       return rows[0] if rows else {}
   ```
3. Mount in `app/backend/main.py`:
   ```python
   from backend.routes.features import router as features_router
   app.include_router(features_router, prefix="/api")
   ```
4. No additional env vars needed beyond `CATALOG` and `SCHEMA` (already in `app/app.yaml`).
5. Frontend: Feature values are often displayed inline in entity detail panels. Add a "Feature Profile" section to domain entity pages that calls `GET /api/features/<entity_id>` and renders key feature values using `.kpi-row` tiles.

## MAS Integration
Feature Store tables are just Unity Catalog Delta tables — Genie Space can query them natively. Add the feature table to the Genie Space `serialized_space` alongside other domain tables:
```json
{"identifier": "<catalog>.<schema>.<entity>_features"}
```
For point-in-time feature lookup during inference via MAS, register a UC function:
```sql
CREATE FUNCTION <catalog>.<schema>.get_<entity>_features(entity_id STRING)
RETURNS TABLE(feature1 DOUBLE, feature2 DOUBLE, feature3 STRING)
LANGUAGE SQL AS
SELECT feature1, feature2, feature3
FROM <catalog>.<schema>.<entity>_features
WHERE entity_id = entity_id;
```

## Manual Setup (fallback without AI Dev Kit)
```python
# In a Databricks notebook (serverless, Python)
from databricks.feature_engineering import FeatureEngineeringClient
import pyspark.sql.functions as F

fe = FeatureEngineeringClient()

# Create and populate feature table
feature_df = spark.table(f"{CATALOG}.{SCHEMA}.<source_table>").select(
    "<entity_id>",
    F.col("raw_col1").alias("feature1"),
    (F.col("raw_col2") / F.col("raw_col3")).alias("feature_ratio"),
    # ... additional feature engineering
)

fe.create_table(
    name=f"{CATALOG}.{SCHEMA}.<entity>_features",
    primary_keys=["<entity_id>"],
    df=feature_df,
    description="Engineered features for <entity> ML scoring",
)
```

Grant access to the app SP:
```sql
GRANT SELECT ON TABLE <catalog>.<schema>.<entity>_features TO `<app-sp-client-id>`;
```
