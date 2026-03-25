"""Vector Search routes — semantic similarity search via Databricks Vector Search."""
import asyncio
import os
import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
log = logging.getLogger("vector_search")

VS_INDEX_NAME = os.environ.get("VS_INDEX_NAME", "")
VS_ENDPOINT_NAME = os.environ.get("VS_ENDPOINT_NAME", "")


class SearchQueryRequest(BaseModel):
    query: str
    top_k: int = 5
    filters: Optional[dict[str, Any]] = None


def _run_search(query: str, top_k: int, filters: Optional[dict]) -> dict:
    from databricks.sdk import WorkspaceClient
    from databricks.vector_search.client import VectorSearchClient

    w = WorkspaceClient()
    vsc = VectorSearchClient(
        workspace_url=w.config.host,
        service_principal_client_id=None,
        service_principal_client_secret=None,
    )
    index = vsc.get_index(endpoint_name=VS_ENDPOINT_NAME, index_name=VS_INDEX_NAME)

    kwargs: dict[str, Any] = {
        "query_text": query,
        "num_results": top_k,
    }
    if filters:
        kwargs["filters_json"] = filters

    response = index.similarity_search(**kwargs)
    result = response.get("result", {})
    data_array = result.get("data_array", [])
    columns = result.get("primary_keys", []) + result.get("columns", [])

    results = []
    scores = []
    for row in data_array:
        # Last element is typically the similarity score
        score = row[-1] if row else 0.0
        scores.append(float(score))
        if columns:
            results.append(dict(zip(columns, row[:-1])))
        else:
            results.append({"raw": row[:-1]})

    return {"results": results, "scores": scores, "total": len(results)}


@router.get("/search/info")
async def get_search_info():
    """Return configured Vector Search index metadata."""
    return {
        "index_name": VS_INDEX_NAME,
        "endpoint_name": VS_ENDPOINT_NAME,
        "status": "configured" if (VS_INDEX_NAME and VS_ENDPOINT_NAME) else "not_configured",
    }


@router.post("/search/query")
async def query_vector_search(body: SearchQueryRequest):
    """
    Perform a semantic similarity search against the configured Vector Search index.
    Returns matched documents and their similarity scores.
    """
    if not VS_INDEX_NAME:
        raise HTTPException(
            status_code=503,
            detail="Vector Search not configured — set VS_INDEX_NAME in app.yaml",
        )
    if not VS_ENDPOINT_NAME:
        raise HTTPException(
            status_code=503,
            detail="Vector Search not configured — set VS_ENDPOINT_NAME in app.yaml",
        )
    if body.top_k < 1 or body.top_k > 100:
        raise HTTPException(status_code=400, detail="top_k must be between 1 and 100")

    try:
        result = await asyncio.to_thread(
            _run_search, body.query, body.top_k, body.filters
        )
        return result
    except Exception as exc:
        log.exception("Vector Search query failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/search/query")
async def query_vector_search_get(q: str, top_k: int = 5):
    """
    GET convenience endpoint for simple semantic searches.
    Use POST /search/query for filter support.
    """
    if not VS_INDEX_NAME or not VS_ENDPOINT_NAME:
        raise HTTPException(
            status_code=503,
            detail="Vector Search not configured — set VS_INDEX_NAME and VS_ENDPOINT_NAME in app.yaml",
        )

    try:
        result = await asyncio.to_thread(_run_search, q, top_k, None)
        return result
    except Exception as exc:
        log.exception("Vector Search GET query failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
