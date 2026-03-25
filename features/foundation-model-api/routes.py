"""Foundation Model API routes — text generation via Databricks Foundation Model API."""
import asyncio
import os
import logging
from typing import Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()
log = logging.getLogger("foundation_model_api")

# Default model; override via env var. Examples:
#   databricks-meta-llama-3-3-70b-instruct
#   databricks-dbrx-instruct
#   databricks-mixtral-8x7b-instruct
FMAPI_MODEL = os.environ.get("FMAPI_MODEL", "databricks-meta-llama-3-3-70b-instruct")


class GenerateRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0
    stop: Optional[list[str]] = None
    extra_params: Optional[dict[str, Any]] = None


class ChatRequest(BaseModel):
    messages: list[dict[str, str]]
    temperature: float = 0.7
    max_tokens: int = 1024
    top_p: float = 1.0
    stop: Optional[list[str]] = None


def _run_generate(body: GenerateRequest) -> dict:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

    w = WorkspaceClient()

    messages: list[ChatMessage] = []
    if body.system_prompt:
        messages.append(
            ChatMessage(role=ChatMessageRole.SYSTEM, content=body.system_prompt)
        )
    messages.append(ChatMessage(role=ChatMessageRole.USER, content=body.prompt))

    kwargs: dict[str, Any] = {
        "model": FMAPI_MODEL,
        "messages": messages,
        "temperature": body.temperature,
        "max_tokens": body.max_tokens,
        "top_p": body.top_p,
    }
    if body.stop:
        kwargs["stop"] = body.stop
    if body.extra_params:
        kwargs.update(body.extra_params)

    response = w.serving_endpoints.query(name=FMAPI_MODEL, **kwargs)

    choices = getattr(response, "choices", [])
    text = ""
    if choices:
        first = choices[0]
        message = getattr(first, "message", None)
        if message:
            text = getattr(message, "content", "") or ""
        else:
            text = getattr(first, "text", "") or ""

    usage = getattr(response, "usage", None)
    usage_dict: dict[str, int] = {}
    if usage:
        usage_dict = {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0),
            "completion_tokens": getattr(usage, "completion_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0),
        }

    return {
        "response": text,
        "model": FMAPI_MODEL,
        "usage": usage_dict,
        "finish_reason": getattr(choices[0], "finish_reason", None) if choices else None,
    }


def _run_chat(body: ChatRequest) -> dict:
    from databricks.sdk import WorkspaceClient
    from databricks.sdk.service.serving import ChatMessage, ChatMessageRole

    w = WorkspaceClient()

    role_map = {
        "system": ChatMessageRole.SYSTEM,
        "user": ChatMessageRole.USER,
        "assistant": ChatMessageRole.ASSISTANT,
    }
    messages = [
        ChatMessage(
            role=role_map.get(m.get("role", "user"), ChatMessageRole.USER),
            content=m.get("content", ""),
        )
        for m in body.messages
    ]

    response = w.serving_endpoints.query(
        name=FMAPI_MODEL,
        model=FMAPI_MODEL,
        messages=messages,
        temperature=body.temperature,
        max_tokens=body.max_tokens,
        top_p=body.top_p,
        stop=body.stop or [],
    )

    choices = getattr(response, "choices", [])
    text = ""
    if choices:
        first = choices[0]
        message = getattr(first, "message", None)
        if message:
            text = getattr(message, "content", "") or ""

    usage = getattr(response, "usage", None)
    usage_dict: dict[str, int] = {}
    if usage:
        usage_dict = {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0),
            "completion_tokens": getattr(usage, "completion_tokens", 0),
            "total_tokens": getattr(usage, "total_tokens", 0),
        }

    return {
        "response": text,
        "model": FMAPI_MODEL,
        "usage": usage_dict,
        "finish_reason": getattr(choices[0], "finish_reason", None) if choices else None,
    }


@router.get("/llm/info")
async def get_llm_info():
    """Return which Foundation Model API model is configured."""
    return {
        "model": FMAPI_MODEL,
        "status": "configured" if FMAPI_MODEL else "not_configured",
    }


@router.post("/llm/generate")
async def generate(body: GenerateRequest):
    """
    Generate text from a prompt using the configured Foundation Model.
    Wraps the prompt in a single-turn chat messages format.
    """
    if not FMAPI_MODEL:
        raise HTTPException(
            status_code=503,
            detail="Foundation Model API not configured — set FMAPI_MODEL in app.yaml",
        )

    try:
        result = await asyncio.to_thread(_run_generate, body)
        return result
    except Exception as exc:
        log.exception("Foundation Model generation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/llm/chat")
async def chat(body: ChatRequest):
    """
    Multi-turn chat completion using the configured Foundation Model.
    Pass a full messages array with role/content pairs.
    """
    if not FMAPI_MODEL:
        raise HTTPException(
            status_code=503,
            detail="Foundation Model API not configured — set FMAPI_MODEL in app.yaml",
        )
    if not body.messages:
        raise HTTPException(status_code=400, detail="messages must be a non-empty list")

    try:
        result = await asyncio.to_thread(_run_chat, body)
        return result
    except Exception as exc:
        log.exception("Foundation Model chat failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc
