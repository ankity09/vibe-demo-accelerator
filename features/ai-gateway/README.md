# AI Gateway

Databricks AI Gateway provides enterprise governance over all LLM traffic in a workspace.
It sits in front of model serving endpoints and enforces rate limits, usage tracking,
input/output guardrails, and PII redaction.

## What it does
- Centralizes access control for all LLM endpoints behind a single governed route
- Tracks token usage per user/team for cost allocation and chargeback
- Applies configurable input guardrails (topic blocking, PII detection)
- Enables fallback routing between models (e.g., primary → backup on rate limit)

## Prerequisites
- At least one Model Serving or Foundation Model API endpoint configured
- AI Gateway enabled in the workspace (enterprise tier)
- Route configured via the Model Serving UI or `list_serving_endpoints`

## Setup
1. Open Model Serving in the workspace and navigate to AI Gateway
2. Create a route pointing at your target endpoint(s)
3. Configure rate limits, guardrails, and usage tracking as needed
4. Set `AI_GATEWAY_ROUTE_NAME` in `app.yaml`
5. Update FastAPI routes to call the gateway URL instead of the endpoint directly

## Connection to the Demo
AI Gateway is a strong enterprise governance talking point. Enable it in the demo to show
usage dashboards, demonstrate PII redaction in action, and illustrate how the platform
provides the same controls over AI that customers already have over their data.
