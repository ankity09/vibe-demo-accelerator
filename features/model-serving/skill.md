# Model Serving Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-demo` skill
- MCP tools: `create_model_serving_endpoint`, `query_serving_endpoint`
- A registered MLflow model in Unity Catalog (trained and logged to `<catalog>.<schema>.models/<model-name>`)
- Compute type selected: CPU (latency-tolerant) or GPU (real-time inference); Serverless compute available for supported frameworks

## Provisioning (via AI Dev Kit)
Use AI Dev Kit MCP tools — do NOT use raw REST API calls:
1. `create_model_serving_endpoint` — Deploy a registered MLflow model from Unity Catalog to a Model Serving endpoint. Specify model name, version, compute size, and scaling config (`min_provisioned_throughput: 0` for scale-to-zero).
2. `query_serving_endpoint` — Send a test payload to validate the endpoint is live and responding correctly.

For demo purposes, use serverless compute when the model framework supports it (scikit-learn, XGBoost, LightGBM, Python models with standard dependencies). This eliminates cold-start wait time.

## VDA App Wiring
1. Create `app/backend/routes/model_serving.py`:
   ```python
   import asyncio, os
   from fastapi import APIRouter
   from pydantic import BaseModel
   from databricks.sdk import WorkspaceClient

   router = APIRouter()
   w = WorkspaceClient()
   ENDPOINT_NAME = os.getenv("MODEL_ENDPOINT_NAME", "")

   class PredictRequest(BaseModel):
       inputs: list[dict]

   @router.post("/predict")
   async def predict(body: PredictRequest):
       response = await asyncio.to_thread(
           w.serving_endpoints.query,
           name=ENDPOINT_NAME,
           dataframe_records=body.inputs,
       )
       return {"predictions": response.predictions}
   ```
2. Mount in `app/backend/main.py`:
   ```python
   from backend.routes.model_serving import router as model_router
   app.include_router(model_router, prefix="/api")
   ```
3. Add env vars in `app/app.yaml`:
   ```yaml
   - name: MODEL_ENDPOINT_NAME
     value: "<serving-endpoint-name>"
   ```
4. Register as app resource and redeploy:
   ```bash
   databricks apps update <app-name> --json '{
     "resources": [
       ...,
       {"name":"model-endpoint","serving_endpoint":{"name":"<endpoint-name>","permission":"CAN_QUERY"}}
     ]
   }' --profile=<profile>
   databricks apps deploy <app-name> --source-code-path <path> --profile=<profile>
   ```
5. Grant `CAN_QUERY` on the endpoint to the app SP (does not require redeploy):
   ```bash
   # Get endpoint UUID
   databricks api get /api/2.0/serving-endpoints --profile=<profile> | \
     jq '.endpoints[] | select(.name=="<endpoint-name>") | .id'
   # Grant
   databricks api patch /api/2.0/permissions/serving-endpoints/<uuid> \
     --json '{"access_control_list":[{"service_principal_name":"<app-sp-client-id>","permission_level":"CAN_QUERY"}]}' \
     --profile=<profile>
   ```
6. Frontend: Build a domain-specific scoring panel — e.g., a form that takes entity inputs and renders the model prediction with a confidence score badge. Use VDA `.card`, `.badge-*`, and `animateKPIs()` for the result display.

## MAS Integration
Expose the model serving endpoint as a Unity Catalog function so MAS can call it during chat:
```sql
CREATE FUNCTION <catalog>.<schema>.score_<entity>(
  feature1 DOUBLE, feature2 DOUBLE, feature3 DOUBLE
)
RETURNS DOUBLE
LANGUAGE PYTHON AS $$
from databricks.sdk import WorkspaceClient
w = WorkspaceClient()
r = w.serving_endpoints.query(
    name="<endpoint-name>",
    dataframe_records=[{"feature1": feature1, "feature2": feature2, "feature3": feature3}]
)
return r.predictions[0]
$$;
```
Add to MAS agents via REST API PATCH (UC function type not supported by `create_or_update_mas`):
```json
{
  "agent_type": "unity-catalog-function",
  "unity_catalog_function": { "uc_path": { "catalog": "<catalog>", "schema": "<schema>", "name": "score_<entity>" } },
  "name": "<demo>_predictor",
  "description": "Score <entities> using the ML model. Provide feature values to get a prediction and risk score."
}
```

## Manual Setup (fallback without AI Dev Kit)
```bash
# 1. Create serving endpoint from a registered UC model
databricks api post /api/2.0/serving-endpoints --json '{
  "name": "<endpoint-name>",
  "config": {
    "served_models": [{
      "name": "<model-name>",
      "model_name": "<catalog>.<schema>.models.<model-name>",
      "model_version": "1",
      "workload_size": "Small",
      "scale_to_zero_enabled": true
    }]
  }
}' --profile=<profile>

# 2. Poll until state = READY
databricks api get /api/2.0/serving-endpoints/<endpoint-name> --profile=<profile> | jq '.state'

# 3. Test
databricks api post "/api/2.0/serving-endpoints/<endpoint-name>/invocations" \
  --json '{"dataframe_records":[{"feature1":1.0,"feature2":2.0}]}' \
  --profile=<profile>
```
