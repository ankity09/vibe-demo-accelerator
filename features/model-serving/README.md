# Model Serving

Databricks Model Serving hosts custom ML models (MLflow, scikit-learn, PyTorch, XGBoost) as
low-latency REST endpoints. Use it to surface domain-specific predictions — risk scores,
anomaly flags, demand forecasts — directly in the demo UI.

## What it does
- Deploys MLflow-tracked models as autoscaling REST endpoints
- Supports CPU and GPU serving with configurable scale-to-zero
- Returns predictions in milliseconds, suitable for real-time scoring in the frontend
- Can be called as a Unity Catalog function from within MAS tool calling

## Prerequisites
- Model registered in Unity Catalog MLflow registry
- Model Serving endpoint created and in `Ready` state
- App SP has `CAN_QUERY` on the serving endpoint

## Setup
1. Train and log a model with MLflow: `mlflow.sklearn.log_model(...)`
2. Register to Unity Catalog: `mlflow.register_model(uri, "catalog.schema.model_name")`
3. Create a serving endpoint via the Serving UI or `query_serving_endpoint`
4. Set `MODEL_ENDPOINT_NAME` in `app.yaml`
5. Call from FastAPI: `POST /serving-endpoints/{name}/invocations` with input JSON

## Connection to the Demo
Model Serving enables the demo to show real ML predictions (not mocked data) in the UI.
For example, a risk score badge on each asset card can call the endpoint in real time
and display the returned probability as a color-coded indicator.
