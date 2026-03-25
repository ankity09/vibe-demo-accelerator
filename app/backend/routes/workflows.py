"""Workflow routes — agent overview, single workflow detail, and status updates.

Mounted at /api prefix in main.py, so:
  GET   /api/agent-overview
  GET   /api/workflows/{workflow_id}
  PATCH /api/workflows/{workflow_id}
"""

import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException

from backend.core import run_pg_query, write_pg

log = logging.getLogger("app")

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════
# Workflow Enrichment (Nice-to-Have #14) — reasoning chains, agent flows
# ═══════════════════════════════════════════════════════════════════════════

def _enrich_workflow(wf: dict) -> dict:
    """Enrich a workflow with headline, enriched_summary, reasoning_chain, and agent_flow.

    This is a SKELETON function — domain-specific labels and templates are marked
    with TODO(vibe) comments for vibe to fill during demo creation.
    """
    wf = dict(wf)  # don't mutate original

    # ── Headline ──
    if not wf.get("headline"):
        # TODO(vibe): Add workflow_type -> headline templates for your domain
        # Example: "reorder_po": f"Reorder PO for {wf.get('entity_id', 'unknown')}"
        TYPE_HEADLINES = {}
        wtype = wf.get("workflow_type", "workflow")
        entity = f"{wf.get('entity_type', '')} {wf.get('entity_id', '')}".strip()
        wf["headline"] = TYPE_HEADLINES.get(
            wtype,
            f"{wtype.replace('_', ' ').title()}: {entity}" if entity else wtype.replace("_", " ").title(),
        )

    # ── Enriched Summary ──
    if not wf.get("enriched_summary"):
        summary = wf.get("summary", "")
        # TODO(vibe): Add domain-specific narrative generation
        wf["enriched_summary"] = summary

    # ── Reasoning Chain ──
    chain = wf.get("reasoning_chain")
    if isinstance(chain, str):
        try:
            chain = json.loads(chain)
        except (json.JSONDecodeError, TypeError):
            chain = []
    if not chain or not isinstance(chain, list):
        # Build a template chain from workflow metadata
        chain = [
            {"step": 1, "tool": "monitor", "label": "Trigger detected", "output": wf.get("trigger_source", "monitor"), "status": "completed"},
            {"step": 2, "tool": "analyze", "label": "Analyzing situation", "output": wf.get("summary", "")[:100], "status": "completed"},
        ]
        if wf.get("entity_type"):
            chain.append({"step": 3, "tool": "action", "label": f"Action on {wf.get('entity_type', '')}", "output": wf.get("entity_id", ""), "status": "completed"})
    wf["reasoning_chain"] = chain

    # ── Agent Flow ──
    if not wf.get("agent_flow"):
        # TODO(vibe): Customize agent flow data for your domain
        wf["agent_flow"] = None  # Frontend falls back to buildDomainAgentFlow()

    return wf


# ═══════════════════════════════════════════════════════════════════════════
# Agent Workflows — powers the Agent Workflows page
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/agent-overview")
async def get_agent_overview():
    """Return KPIs, workflows, and recent agent actions for the Agent page."""

    def _cnt(result):
        """Safely extract count from a query result, handling exceptions (Gotcha #41)."""
        if isinstance(result, Exception):
            log.warning("Agent overview sub-query failed: %s", result)
            return 0
        return (result or [{}])[0].get("cnt", 0)

    def _rows(result, default=None):
        """Safely extract rows from a query result, handling exceptions (Gotcha #41)."""
        if isinstance(result, Exception):
            log.warning("Agent overview sub-query failed: %s", result)
            return default if default is not None else []
        return result or (default if default is not None else [])

    try:
        q_pending, q_in_progress, q_completed_7d, q_actions_24h, q_workflows, q_actions, q_open_exceptions = await asyncio.gather(
            asyncio.to_thread(run_pg_query, "SELECT count(*) as cnt FROM workflows WHERE status = 'pending_approval'"),
            asyncio.to_thread(run_pg_query, "SELECT count(*) as cnt FROM workflows WHERE status = 'in_progress'"),
            asyncio.to_thread(run_pg_query, "SELECT count(*) as cnt FROM workflows WHERE status = 'approved' AND completed_at >= NOW() - INTERVAL '7 days'"),
            asyncio.to_thread(run_pg_query, "SELECT count(*) as cnt FROM agent_actions WHERE created_at >= NOW() - INTERVAL '24 hours'"),
            asyncio.to_thread(run_pg_query, "SELECT * FROM workflows ORDER BY created_at DESC LIMIT 50"),
            asyncio.to_thread(run_pg_query, "SELECT * FROM agent_actions ORDER BY created_at DESC LIMIT 20"),
            asyncio.to_thread(run_pg_query, "SELECT count(*) as cnt FROM exceptions WHERE status = 'open'"),
            return_exceptions=True,  # Gotcha #41: don't let one failure kill all queries
        )
        workflows = [_enrich_workflow(wf) for wf in _rows(q_workflows)]
        return {
            "kpis": {
                "pending_approval": _cnt(q_pending),
                "in_progress": _cnt(q_in_progress),
                "completed_7d": _cnt(q_completed_7d),
                "agent_actions_24h": _cnt(q_actions_24h),
                "open_exceptions": _cnt(q_open_exceptions),
            },
            "workflows": workflows,
            "agent_actions_recent": _rows(q_actions),
        }
    except Exception as e:
        log.warning("Agent overview query failed (Lakebase tables may not exist): %s", e)
        return {"kpis": {}, "workflows": [], "agent_actions_recent": []}


@router.get("/workflows/{workflow_id}")
async def get_workflow(workflow_id: int):
    """Return a single workflow by ID (used by the workflow detail modal)."""
    rows = await asyncio.to_thread(
        run_pg_query,
        "SELECT * FROM workflows WHERE workflow_id = %s",
        (workflow_id,),
    )
    if not rows:
        raise HTTPException(404, f"Workflow {workflow_id} not found")
    return rows[0]


@router.patch("/workflows/{workflow_id}")
async def update_workflow(workflow_id: int, body: dict):
    """Update a workflow's status (approve/dismiss)."""
    new_status = body.get("status", "")
    if new_status not in ("approved", "dismissed"):
        raise HTTPException(400, "Status must be 'approved' or 'dismissed'")
    completed = "NOW()" if new_status in ("approved", "dismissed") else "NULL"
    result = await asyncio.to_thread(
        write_pg,
        f"UPDATE workflows SET status = %s, completed_at = {completed} WHERE workflow_id = %s RETURNING *",
        (new_status, workflow_id),
    )
    if not result:
        raise HTTPException(404, f"Workflow {workflow_id} not found")
    return result
