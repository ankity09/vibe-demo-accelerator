"""Chat routes — MAS streaming, history, and clear.

Mounted at /api prefix in main.py, so:
  POST /api/chat
  GET  /api/chat/history
  POST /api/chat/clear
"""

import asyncio
import json
import logging
import uuid as _uuid
from datetime import date

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse

from backend.core.streaming import stream_mas_chat, _sse_keepalive, get_mcp_pending, clear_mcp_pending
from backend.core import run_pg_query, write_pg, _get_mas_auth

log = logging.getLogger("app")

router = APIRouter()

# ─── Chat history (in-memory, per-process) ────────────────────────────────
_chat_history: list[dict] = []

# ─── Chat Persistence (Lakebase-backed session & message history) ─────────
# Requires chat_sessions and chat_messages tables (see lakebase/core_schema.sql).
# Falls back gracefully if tables don't exist yet.

_chat_session_id: str | None = None


def _ensure_chat_session() -> str:
    global _chat_session_id
    if _chat_session_id:
        return _chat_session_id
    try:
        rows = run_pg_query("SELECT session_id FROM chat_sessions ORDER BY updated_at DESC LIMIT 1")
        if rows:
            _chat_session_id = rows[0]["session_id"]
            return _chat_session_id
    except Exception:
        pass
    return _new_chat_session()


def _new_chat_session() -> str:
    global _chat_session_id
    sid = f"chat-{date.today().isoformat()}-{_uuid.uuid4().hex[:6]}"
    try:
        write_pg("INSERT INTO chat_sessions (session_id) VALUES (%s) ON CONFLICT DO NOTHING", (sid,))
    except Exception as e:
        log.warning("Could not create chat session: %s", e)
    _chat_session_id = sid
    return sid


def _save_chat_message(role: str, content: str):
    sid = _ensure_chat_session()
    try:
        write_pg(
            "INSERT INTO chat_messages (session_id, role, content) VALUES (%s, %s, %s)",
            (sid, role, content),
        )
        if role == "user":
            title = content[:100] + ("..." if len(content) > 100 else "")
            write_pg(
                "UPDATE chat_sessions SET updated_at = NOW(), title = COALESCE(NULLIF(title, 'New conversation'), %s) WHERE session_id = %s",
                (title, sid),
            )
        else:
            write_pg("UPDATE chat_sessions SET updated_at = NOW() WHERE session_id = %s", (sid,))
    except Exception as e:
        log.warning("Could not save chat message: %s", e)


def _load_chat_history() -> list[dict]:
    sid = _ensure_chat_session()
    try:
        rows = run_pg_query(
            "SELECT role, content FROM chat_messages WHERE session_id = %s ORDER BY created_at ASC",
            (sid,),
        )
        return [{"role": r["role"], "content": r["content"]} for r in rows]
    except Exception:
        return []


def _clear_chat_history():
    global _chat_session_id
    if _chat_session_id:
        try:
            write_pg("DELETE FROM chat_sessions WHERE session_id = %s", (_chat_session_id,))
        except Exception:
            pass
    _chat_session_id = None


# ─── Action card config for your domain ───────────────────────────────────
# Override this list to detect entities created by the MAS agent during chat.
# Each entry maps a Lakebase table to an action card in the chat UI.
#
# ACTION_CARD_TABLES = [
#     {
#         "table": "work_orders",
#         "card_type": "work_order",
#         "id_col": "work_order_id",
#         "title_template": "Work Order {wo_number}",
#         "actions": ["approve", "dismiss"],
#         "detail_cols": {"asset": "asset_name", "priority": "priority", "status": "status"},
#     },
# ]
ACTION_CARD_TABLES: list[dict] = []


# ─── Chat endpoint (MAS streaming) ───────────────────────────────────────

@router.post("/chat")
async def chat(request: Request, body: dict):
    """Streaming SSE endpoint for MAS chat with MCP approval flow.

    Normal message:   {"message": "Create a PO...", "auto_approve_mcp": true}
    MCP approval:     {"approve_mcp": true}  or  {"approve_mcp": false}
    """
    approve_mcp = body.get("approve_mcp", None)
    auto_approve_mcp = body.get("auto_approve_mcp", False)
    message = body.get("message", "").strip()
    context = body.get("context", "").strip()

    # Extract OBO token for MAS calls (required for MCP tools, auto-refreshes on expiry)
    user_token = request.headers.get("x-forwarded-access-token", "")

    # Determine starting state
    mcp_state = get_mcp_pending()
    if approve_mcp is not None and mcp_state:
        # Continuing from MCP approval — build input from saved state
        log.info("MCP APPROVAL received: approve=%s", approve_mcp)
        all_accumulated = mcp_state["accumulated"]
        tools_called = mcp_state["tools_called"]
        lakebase_called = mcp_state["lakebase_called"]
        approval_round = mcp_state["round"]

        for req in mcp_state["pending"]:
            all_accumulated.append({
                "type": "mcp_approval_response",
                "id": f"approval-{approval_round}-{req.get('id', '')}",
                "approval_request_id": req.get("id", ""),
                "approve": bool(approve_mcp),
            })
        start_messages = list(_chat_history[-10:]) + all_accumulated
        clear_mcp_pending()
    elif approve_mcp is not None and not mcp_state:
        # Stale approval — no pending state
        async def stale():
            yield f"data: {json.dumps({'type': 'error', 'text': 'No pending MCP approval.'})}\n\n"
            yield "data: [DONE]\n\n"
        return StreamingResponse(stale(), media_type="text/event-stream")
    else:
        # New user message
        if not message:
            raise HTTPException(400, "Empty message")
        full_message = f"Context: {context}\n\nQuestion: {message}" if context else message
        _chat_history.append({"role": "user", "content": full_message})
        try:
            _save_chat_message("user", full_message)
        except Exception:
            pass
        start_messages = list(_chat_history[-10:])
        all_accumulated = []
        tools_called = set()
        lakebase_called = False
        approval_round = 0

    async def event_stream():
        final_text = ""
        async for chunk in stream_mas_chat(
            message, _chat_history, ACTION_CARD_TABLES,
            user_token=user_token,
            auto_approve_mcp=auto_approve_mcp,
            start_messages=start_messages,
            initial_accumulated=all_accumulated,
            initial_tools_called=tools_called,
            initial_lakebase_called=lakebase_called,
            initial_approval_round=approval_round,
        ):
            yield chunk
            # Track final text for chat history
            if chunk.startswith("data: ") and chunk.strip() != "data: [DONE]":
                try:
                    evt = json.loads(chunk[6:])
                    if evt.get("type") == "delta":
                        final_text += evt.get("text", "")
                except (json.JSONDecodeError, KeyError):
                    pass
        # Save final response to chat history
        if final_text:
            _chat_history.append({"role": "assistant", "content": final_text})
            try:
                _save_chat_message("assistant", final_text)
            except Exception:
                pass

    return StreamingResponse(
        _sse_keepalive(event_stream()),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


# ─── Chat History & Clear Endpoints ──────────────────────────────────────

@router.get("/chat/history")
async def get_chat_history():
    """Return all messages from the current chat session."""
    messages = await asyncio.to_thread(_load_chat_history)
    return {"session_id": _chat_session_id or "", "messages": messages}


@router.post("/chat/clear")
async def clear_chat():
    """Clear chat history (both in-memory and Lakebase)."""
    _chat_history.clear()
    await asyncio.to_thread(_clear_chat_history)
    return {"status": "cleared"}
