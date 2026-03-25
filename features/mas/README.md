# Multi-Agent Supervisor (MAS)

The Multi-Agent Supervisor (MAS) is the central orchestration layer in Agent Bricks.
It routes user messages to the right sub-agents, combines their outputs, and streams
the final response back to the demo frontend via Server-Sent Events (SSE).

## What it does
- Orchestrates sub-agents: Genie (data queries), Knowledge Assistant (RAG), MCP (writes), UC functions (compute)
- Handles multi-round tool calling with automatic MCP approval (see `core/streaming.py`)
- Streams reasoning steps, tool invocations, and final answers to the frontend
- Exposes a serving endpoint named `mas-{8-char-tile-id}-endpoint`

## Prerequisites
- At least one sub-agent configured (Genie Space is the most common starting point)
- `CAN_QUERY` granted on the MAS serving endpoint to the app SP (Gotcha #25)
- OBO (on-behalf-of) user token forwarded via `x-forwarded-access-token` for MCP writes (Gotcha #29)

## Setup
1. Create MAS via POST to `/api/2.0/multi-agent-supervisors` with simpler agents first
2. Add MCP agents via PATCH (POST fails with external-mcp-server — see Gotcha #37)
3. Discover the full tile UUID via serving endpoints list (Gotcha #24)
4. Set `MAS_TILE_ID` to the first 8 characters of the tile UUID in `app.yaml`
5. Register and grant `CAN_QUERY` on the serving endpoint (Gotcha #25)

## Connection to the Demo
MAS powers the AI Chat page. Every message sent from the frontend goes through `core/streaming.py`
which proxies the SSE stream, auto-approves MCP tool calls, and emits typed events
(`thinking`, `delta`, `tool_call`, `action_card`) that the frontend renders in real time.
