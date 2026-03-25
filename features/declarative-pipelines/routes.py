"""Declarative Pipelines routes — monitor DLT pipeline status and health."""
import asyncio
import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
log = logging.getLogger("declarative_pipelines")

PIPELINE_ID = os.environ.get("PIPELINE_ID", "")


def _get_pipeline_status() -> dict:
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()
    pipeline = w.pipelines.get(pipeline_id=PIPELINE_ID)

    state = getattr(pipeline, "state", None)
    last_modified = getattr(pipeline, "last_modified", None)
    name = getattr(pipeline, "name", "")
    cluster_id = getattr(pipeline, "cluster_id", None)

    # Determine health from state
    state_str = str(state).lower() if state else "unknown"
    if state_str in ("running", "idle"):
        health = "healthy"
    elif state_str in ("failed", "error"):
        health = "error"
    elif state_str in ("starting", "resetting", "stopping"):
        health = "transitioning"
    else:
        health = "unknown"

    return {
        "pipeline_id": PIPELINE_ID,
        "name": name,
        "state": state_str,
        "health": health,
        "cluster_id": cluster_id,
        "last_modified": last_modified,
    }


def _get_pipeline_events(max_results: int = 20) -> list[dict]:
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()
    events = list(
        w.pipelines.list_pipeline_events(
            pipeline_id=PIPELINE_ID, max_results=max_results
        )
    )
    return [
        {
            "id": getattr(e, "id", None),
            "timestamp": getattr(e, "timestamp", None),
            "level": getattr(e, "level", None),
            "message": getattr(e, "message", ""),
            "event_type": getattr(e, "event_type", None),
            "origin": {
                "flow_name": getattr(getattr(e, "origin", None), "flow_name", None),
                "dataset_name": getattr(getattr(e, "origin", None), "dataset_name", None),
            },
        }
        for e in events
    ]


def _get_pipeline_updates(max_results: int = 10) -> list[dict]:
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()
    updates = list(
        w.pipelines.list_updates(pipeline_id=PIPELINE_ID, max_results=max_results)
    )
    return [
        {
            "update_id": getattr(u, "update_id", None),
            "state": str(getattr(u, "state", "")).lower(),
            "creation_time": getattr(u, "creation_time", None),
            "full_refresh": getattr(u, "full_refresh", False),
            "cause": getattr(u, "cause", None),
        }
        for u in updates
    ]


@router.get("/pipelines/status")
async def get_pipeline_status():
    """
    Return the current status, last update time, and health of the configured DLT pipeline.
    """
    if not PIPELINE_ID:
        raise HTTPException(
            status_code=503,
            detail="Declarative Pipelines not configured — set PIPELINE_ID in app.yaml",
        )

    try:
        status = await asyncio.to_thread(_get_pipeline_status)
        return status
    except Exception as exc:
        log.exception("Failed to fetch pipeline status")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/pipelines/events")
async def get_pipeline_events(max_results: int = 20):
    """Return recent pipeline events (errors, warnings, info messages)."""
    if not PIPELINE_ID:
        raise HTTPException(
            status_code=503,
            detail="Declarative Pipelines not configured — set PIPELINE_ID in app.yaml",
        )
    if max_results < 1 or max_results > 100:
        raise HTTPException(status_code=400, detail="max_results must be between 1 and 100")

    try:
        events = await asyncio.to_thread(_get_pipeline_events, max_results)
        return {"events": events, "total": len(events)}
    except Exception as exc:
        log.exception("Failed to fetch pipeline events")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/pipelines/updates")
async def get_pipeline_updates(max_results: int = 10):
    """Return recent pipeline update runs (full refresh vs incremental, state, cause)."""
    if not PIPELINE_ID:
        raise HTTPException(
            status_code=503,
            detail="Declarative Pipelines not configured — set PIPELINE_ID in app.yaml",
        )

    try:
        updates = await asyncio.to_thread(_get_pipeline_updates, max_results)
        return {"updates": updates, "total": len(updates)}
    except Exception as exc:
        log.exception("Failed to fetch pipeline updates")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class PipelineActionRequest(BaseModel):
    full_refresh: bool = False


@router.post("/pipelines/start")
async def start_pipeline(body: PipelineActionRequest):
    """Trigger a pipeline update (incremental by default, full refresh if specified)."""
    if not PIPELINE_ID:
        raise HTTPException(
            status_code=503,
            detail="Declarative Pipelines not configured — set PIPELINE_ID in app.yaml",
        )

    def _run():
        from databricks.sdk import WorkspaceClient

        w = WorkspaceClient()
        result = w.pipelines.start_update(
            pipeline_id=PIPELINE_ID, full_refresh=body.full_refresh
        )
        return {"update_id": getattr(result, "update_id", None), "triggered": True}

    try:
        result = await asyncio.to_thread(_run)
        return result
    except Exception as exc:
        log.exception("Failed to start pipeline update")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
