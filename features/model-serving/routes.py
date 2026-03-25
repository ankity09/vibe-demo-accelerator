"""Model Serving routes — query a Databricks Model Serving endpoint for predictions."""
import asyncio
import os
import logging
from typing import Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
log = logging.getLogger("model_serving")

MODEL_ENDPOINT_NAME = os.environ.get("MODEL_ENDPOINT_NAME", "")


class PredictRequest(BaseModel):
    inputs: list[dict[str, Any]]
    params: dict[str, Any] | None = None


def _run_predict(inputs: list[dict[str, Any]], params: dict[str, Any] | None) -> dict:
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()
    payload: dict[str, Any] = {"inputs": inputs}
    if params:
        payload["params"] = params

    response = w.serving_endpoints.query(name=MODEL_ENDPOINT_NAME, **payload)

    # Normalize response — SDK returns QueryEndpointResponse
    predictions = getattr(response, "predictions", None)
    if predictions is None:
        # Fallback: some endpoints return a 'choices' field (chat-style)
        predictions = getattr(response, "choices", [])

    return {
        "predictions": predictions if isinstance(predictions, list) else [predictions],
        "endpoint": MODEL_ENDPOINT_NAME,
        "metadata": {
            "num_inputs": len(inputs),
            "num_predictions": len(predictions) if isinstance(predictions, list) else 1,
        },
    }


@router.get("/predict/info")
async def get_endpoint_info():
    """Return configured Model Serving endpoint metadata."""
    if not MODEL_ENDPOINT_NAME:
        return {"endpoint": "", "status": "not_configured"}

    def _run():
        from databricks.sdk import WorkspaceClient

        w = WorkspaceClient()
        ep = w.serving_endpoints.get(name=MODEL_ENDPOINT_NAME)
        return {
            "endpoint": MODEL_ENDPOINT_NAME,
            "status": "configured",
            "state": getattr(ep.state, "config_update", None),
            "creator": getattr(ep, "creator", None),
        }

    try:
        info = await asyncio.to_thread(_run)
        return info
    except Exception as exc:
        log.exception("Failed to fetch endpoint info")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/predict")
async def predict(body: PredictRequest):
    """
    Send input features to the configured Model Serving endpoint and return predictions.
    Accepts a list of feature dicts; returns a list of predictions in the same order.
    """
    if not MODEL_ENDPOINT_NAME:
        raise HTTPException(
            status_code=503,
            detail="Model Serving not configured — set MODEL_ENDPOINT_NAME in app.yaml",
        )
    if not body.inputs:
        raise HTTPException(status_code=400, detail="inputs must be a non-empty list")

    try:
        result = await asyncio.to_thread(_run_predict, body.inputs, body.params)
        return result
    except Exception as exc:
        log.exception("Model serving prediction failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/predict/single")
async def predict_single(features: dict[str, Any]):
    """
    Convenience endpoint: wrap a single feature dict and return the first prediction.
    """
    if not MODEL_ENDPOINT_NAME:
        raise HTTPException(
            status_code=503,
            detail="Model Serving not configured — set MODEL_ENDPOINT_NAME in app.yaml",
        )

    try:
        result = await asyncio.to_thread(_run_predict, [features], None)
        predictions = result.get("predictions", [])
        return {
            "prediction": predictions[0] if predictions else None,
            "endpoint": MODEL_ENDPOINT_NAME,
        }
    except Exception as exc:
        log.exception("Single prediction failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
