"""Genie Space routes — proxy natural language queries to Databricks Genie."""
import asyncio
import os
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from databricks.sdk import WorkspaceClient

router = APIRouter()
log = logging.getLogger("genie")

GENIE_SPACE_ID = os.environ.get("GENIE_SPACE_ID", "")


class GenieQueryRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None


def _get_client() -> WorkspaceClient:
    return WorkspaceClient()


@router.get("/genie/spaces")
async def get_genie_info():
    """Return configured Genie Space metadata."""
    return {
        "space_id": GENIE_SPACE_ID,
        "status": "configured" if GENIE_SPACE_ID else "not_configured",
    }


@router.post("/genie/query")
async def query_genie(body: GenieQueryRequest):
    """
    Send a natural language question to the configured Genie Space.
    Returns the answer and any generated SQL.
    """
    if not GENIE_SPACE_ID:
        raise HTTPException(
            status_code=503,
            detail="Genie not configured — set GENIE_SPACE_ID in app.yaml",
        )

    def _run():
        w = _get_client()
        result = w.genie.execute_message_query(
            space_id=GENIE_SPACE_ID,
            conversation_id=body.conversation_id or "",
            content=body.question,
        )
        return result

    try:
        result = await asyncio.to_thread(_run)
        return {
            "answer": getattr(result, "content", ""),
            "conversation_id": getattr(result, "conversation_id", None),
            "query_id": getattr(result, "id", None),
            "space_id": GENIE_SPACE_ID,
        }
    except Exception as exc:
        log.exception("Genie query failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/genie/conversations")
async def list_conversations():
    """List recent Genie conversations for the configured space."""
    if not GENIE_SPACE_ID:
        raise HTTPException(
            status_code=503,
            detail="Genie not configured — set GENIE_SPACE_ID in app.yaml",
        )

    def _run():
        w = _get_client()
        convos = list(w.genie.list_conversations(space_id=GENIE_SPACE_ID))
        return [
            {
                "id": getattr(c, "id", None),
                "title": getattr(c, "title", ""),
                "created_at": getattr(c, "created_at", None),
            }
            for c in convos
        ]

    try:
        conversations = await asyncio.to_thread(_run)
        return {"conversations": conversations, "total": len(conversations)}
    except Exception as exc:
        log.exception("Failed to list Genie conversations")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
