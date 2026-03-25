"""Workflows / Jobs routes — list jobs and runs via Databricks SDK."""
import asyncio
import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
log = logging.getLogger("workflows_jobs")

# Optional: scope list to a specific job by default
DEFAULT_JOB_ID = os.environ.get("DEFAULT_JOB_ID", "")


def _list_jobs(name_contains: Optional[str] = None, limit: int = 25) -> list[dict]:
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()
    jobs = list(
        w.jobs.list(name=name_contains, limit=limit, expand_tasks=False)
    )
    return [
        {
            "job_id": getattr(j, "job_id", None),
            "name": getattr(getattr(j, "settings", None), "name", ""),
            "created_time": getattr(j, "created_time", None),
            "creator_user_name": getattr(j, "creator_user_name", None),
        }
        for j in jobs
    ]


def _list_runs(job_id: int, limit: int = 20, active_only: bool = False) -> list[dict]:
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()
    runs = list(
        w.jobs.list_runs(
            job_id=job_id,
            limit=limit,
            active_only=active_only,
            expand_tasks=False,
        )
    )
    return [
        {
            "run_id": getattr(r, "run_id", None),
            "job_id": getattr(r, "job_id", None),
            "run_name": getattr(r, "run_name", ""),
            "state": {
                "life_cycle_state": str(
                    getattr(getattr(r, "state", None), "life_cycle_state", "")
                ).lower(),
                "result_state": str(
                    getattr(getattr(r, "state", None), "result_state", "")
                ).lower(),
                "state_message": getattr(getattr(r, "state", None), "state_message", ""),
            },
            "start_time": getattr(r, "start_time", None),
            "end_time": getattr(r, "end_time", None),
            "execution_duration": getattr(r, "execution_duration", None),
            "trigger": str(getattr(r, "trigger", "")).lower(),
            "run_page_url": getattr(r, "run_page_url", None),
        }
        for r in runs
    ]


def _get_run_output(run_id: int) -> dict:
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()
    output = w.jobs.get_run_output(run_id=run_id)
    return {
        "run_id": run_id,
        "metadata": getattr(output, "metadata", None),
        "notebook_output": {
            "result": getattr(getattr(output, "notebook_output", None), "result", None),
            "truncated": getattr(
                getattr(output, "notebook_output", None), "truncated", False
            ),
        },
        "error": getattr(output, "error", None),
        "error_trace": getattr(output, "error_trace", None),
    }


@router.get("/jobs/list")
async def list_jobs(name_contains: Optional[str] = None, limit: int = 25):
    """
    List Databricks Jobs (Workflow definitions) visible in this workspace.
    Optionally filter by name substring.
    """
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    try:
        jobs = await asyncio.to_thread(_list_jobs, name_contains, limit)
        return {"jobs": jobs, "total": len(jobs)}
    except Exception as exc:
        log.exception("Failed to list jobs")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/jobs/{job_id}/runs")
async def list_job_runs(job_id: int, limit: int = 20, active_only: bool = False):
    """
    List recent runs for a specific Databricks Job.
    Includes lifecycle state, result state, duration, and a link to the run page.
    """
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    try:
        runs = await asyncio.to_thread(_list_runs, job_id, limit, active_only)
        return {"job_id": job_id, "runs": runs, "total": len(runs)}
    except Exception as exc:
        log.exception("Failed to list runs for job %s", job_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/jobs/{job_id}/runs/{run_id}/output")
async def get_run_output(job_id: int, run_id: int):
    """Return the output of a specific job run (notebook result, errors)."""
    try:
        output = await asyncio.to_thread(_get_run_output, run_id)
        return output
    except Exception as exc:
        log.exception("Failed to get run output for run %s", run_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


class RunNowRequest(BaseModel):
    notebook_params: Optional[dict[str, str]] = None
    python_params: Optional[list[str]] = None
    jar_params: Optional[list[str]] = None


@router.post("/jobs/{job_id}/run-now")
async def run_job_now(job_id: int, body: RunNowRequest):
    """Trigger an immediate run of the specified job."""

    def _run():
        from databricks.sdk import WorkspaceClient

        w = WorkspaceClient()
        result = w.jobs.run_now(
            job_id=job_id,
            notebook_params=body.notebook_params,
            python_params=body.python_params,
            jar_params=body.jar_params,
        )
        return {
            "run_id": getattr(result, "run_id", None),
            "number_in_job": getattr(result, "number_in_job", None),
            "triggered": True,
        }

    try:
        result = await asyncio.to_thread(_run)
        return result
    except Exception as exc:
        log.exception("Failed to trigger job %s", job_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/jobs/default/runs")
async def list_default_job_runs(limit: int = 20):
    """
    List recent runs for the default job (set via DEFAULT_JOB_ID env var).
    Convenience endpoint for demos that showcase a single featured workflow.
    """
    if not DEFAULT_JOB_ID:
        raise HTTPException(
            status_code=503,
            detail="Default job not configured — set DEFAULT_JOB_ID in app.yaml",
        )

    try:
        runs = await asyncio.to_thread(_list_runs, int(DEFAULT_JOB_ID), limit, False)
        return {"job_id": int(DEFAULT_JOB_ID), "runs": runs, "total": len(runs)}
    except Exception as exc:
        log.exception("Failed to list default job runs")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
