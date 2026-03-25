"""AI/BI Dashboard routes — serve dashboard metadata and embed URLs."""
import asyncio
import os
import logging
from fastapi import APIRouter, HTTPException

router = APIRouter()
log = logging.getLogger("aibi_dashboard")

DASHBOARD_ID = os.environ.get("DASHBOARD_ID", "")
# Optional: a second dashboard for side-by-side comparisons
DASHBOARD_ID_2 = os.environ.get("DASHBOARD_ID_2", "")


def _get_dashboard_info(dashboard_id: str) -> dict:
    from databricks.sdk import WorkspaceClient

    w = WorkspaceClient()

    # Lakeview dashboards (AI/BI) are accessed via the lakeview API
    try:
        dashboard = w.lakeview.get(dashboard_id=dashboard_id)
        display_name = getattr(dashboard, "display_name", "")
        lifecycle_state = str(getattr(dashboard, "lifecycle_state", "")).lower()
        create_time = getattr(dashboard, "create_time", None)
        update_time = getattr(dashboard, "update_time", None)
        warehouse_id = getattr(
            getattr(dashboard, "warehouse_id", None), "__root__", None
        ) or getattr(dashboard, "warehouse_id", None)
    except Exception:
        # Fallback for older SDK versions or classic dashboards
        log.warning("Lakeview API not available, falling back to basic info")
        display_name = dashboard_id
        lifecycle_state = "unknown"
        create_time = None
        update_time = None
        warehouse_id = None

    # Build the embed URL — standard pattern for AI/BI dashboards
    workspace_url = w.config.host.rstrip("/")
    embed_url = f"{workspace_url}/embed/dashboardsv3/{dashboard_id}?o=0"
    direct_url = f"{workspace_url}/dashboardsv3/{dashboard_id}"

    return {
        "dashboard_id": dashboard_id,
        "display_name": display_name,
        "lifecycle_state": lifecycle_state,
        "embed_url": embed_url,
        "direct_url": direct_url,
        "warehouse_id": warehouse_id,
        "create_time": create_time,
        "update_time": update_time,
    }


@router.get("/dashboard/info")
async def get_dashboard_info():
    """
    Return metadata and embed URL for the configured AI/BI Dashboard.
    Use the embed_url in an <iframe> to surface the dashboard inside the demo app.
    """
    if not DASHBOARD_ID:
        raise HTTPException(
            status_code=503,
            detail="AI/BI Dashboard not configured — set DASHBOARD_ID in app.yaml",
        )

    try:
        info = await asyncio.to_thread(_get_dashboard_info, DASHBOARD_ID)
        return info
    except Exception as exc:
        log.exception("Failed to fetch dashboard info for %s", DASHBOARD_ID)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/dashboard/all")
async def get_all_dashboards():
    """
    Return info for all configured dashboards (primary + optional secondary).
    Useful for demos that display multiple dashboards in tabs.
    """
    ids = [d for d in [DASHBOARD_ID, DASHBOARD_ID_2] if d]
    if not ids:
        raise HTTPException(
            status_code=503,
            detail="No dashboards configured — set DASHBOARD_ID in app.yaml",
        )

    try:
        tasks = [asyncio.to_thread(_get_dashboard_info, did) for did in ids]
        dashboards = await asyncio.gather(*tasks, return_exceptions=True)

        results = []
        for i, result in enumerate(dashboards):
            if isinstance(result, Exception):
                log.error("Failed to fetch dashboard %s: %s", ids[i], result)
                results.append({"dashboard_id": ids[i], "error": str(result)})
            else:
                results.append(result)

        return {"dashboards": results, "total": len(results)}
    except Exception as exc:
        log.exception("Failed to fetch all dashboards")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/dashboard/list")
async def list_dashboards(name_contains: str = "", limit: int = 20):
    """
    List AI/BI dashboards visible in this workspace.
    Useful for a dashboard picker UI in the demo.
    """
    if limit < 1 or limit > 100:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 100")

    def _run():
        from databricks.sdk import WorkspaceClient

        w = WorkspaceClient()
        dashboards = list(w.lakeview.list())
        result = []
        for d in dashboards:
            name = getattr(d, "display_name", "") or ""
            if name_contains and name_contains.lower() not in name.lower():
                continue
            workspace_url = w.config.host.rstrip("/")
            did = getattr(d, "dashboard_id", None)
            result.append(
                {
                    "dashboard_id": did,
                    "display_name": name,
                    "lifecycle_state": str(
                        getattr(d, "lifecycle_state", "")
                    ).lower(),
                    "embed_url": f"{workspace_url}/embed/dashboardsv3/{did}?o=0" if did else None,
                    "direct_url": f"{workspace_url}/dashboardsv3/{did}" if did else None,
                    "create_time": getattr(d, "create_time", None),
                }
            )
            if len(result) >= limit:
                break
        return result

    try:
        dashboards = await asyncio.to_thread(_run)
        return {"dashboards": dashboards, "total": len(dashboards)}
    except Exception as exc:
        log.exception("Failed to list dashboards")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
