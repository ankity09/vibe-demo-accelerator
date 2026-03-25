# Foundation Model API

The Foundation Model API provides pay-per-token access to state-of-the-art LLMs hosted on
Databricks infrastructure — including Meta Llama 3.3, DBRX, and Mixtral.

## What it does
- Exposes LLMs via an OpenAI-compatible `/chat/completions` endpoint
- No cluster management — fully serverless, billed per token
- Supports streaming responses, function calling, and system prompts
- Can be used directly in FastAPI routes for summarization, classification, or extraction tasks

## Prerequisites
- Databricks workspace with Foundation Model API enabled
- App SP has `CAN_QUERY` on the target serving endpoint
- `openai` Python package installed (`pip install openai`)

## Setup
1. No provisioning needed — Databricks-hosted models are available immediately
2. Set `FMAPI_ENDPOINT` in `app.yaml` to the model endpoint name
3. Use the OpenAI SDK with `base_url=f"https://{workspace_url}/serving-endpoints/{endpoint}/v1"`
4. Authenticate with a Databricks token (SP token or user OBO token)

## Connection to the Demo
Use Foundation Model API in FastAPI routes that need LLM inference outside of MAS —
for example, generating a one-line summary of an alert, classifying incoming tickets,
or extracting entities from free-text fields in a background job.
