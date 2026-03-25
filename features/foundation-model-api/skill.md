# Foundation Model API Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-demo` skill
- MCP tools: `query_databricks_model` (if available), or direct REST API
- Databricks workspace with Foundation Model API enabled (available in all FEVM workspaces)
- Model name selected: `databricks-claude-sonnet-4-5` or `databricks-claude-sonnet-4` (preferred for demos)

## Provisioning (via AI Dev Kit)
Foundation Model API requires no provisioning — models are pre-deployed in every Databricks workspace as pay-per-token serving endpoints. No cluster or endpoint setup needed.

Available models (use these for demos):
- `databricks-claude-sonnet-4-5` — Best quality, recommended default
- `databricks-claude-sonnet-4` — Good quality, slightly lower latency
- `databricks-meta-llama-3-3-70b-instruct` — Fast, open-weight option
- `databricks-mixtral-8x7b-instruct` — Lightweight option

Use AI Dev Kit MCP tools to validate model access:
1. `query_databricks_model` — Send a test prompt to confirm the model endpoint is accessible from your workspace.

## VDA App Wiring
1. No routes to copy for basic FMAPI usage — calls go directly from `app/backend/main.py` or custom route files via the Databricks SDK.
2. Add a custom route in `app/backend/main.py` or `app/backend/routes/<feature>.py`:
   ```python
   import asyncio
   from databricks.sdk import WorkspaceClient

   w = WorkspaceClient()

   async def call_fmapi(prompt: str, model: str = "databricks-claude-sonnet-4-5") -> str:
       response = await asyncio.to_thread(
           w.serving_endpoints.query,
           name=model,
           messages=[{"role": "user", "content": prompt}],
           max_tokens=1024,
       )
       return response.choices[0].message.content
   ```
3. For streaming responses, use `httpx` directly with the `Authorization: Bearer <token>` header from `WorkspaceClient().config.token`:
   ```python
   WORKSPACE_URL = os.getenv("DATABRICKS_HOST", "")
   MODEL = "databricks-claude-sonnet-4-5"
   url = f"{WORKSPACE_URL}/serving-endpoints/{MODEL}/invocations"
   ```
4. Register the serving endpoint as an app resource in `app/app.yaml`:
   ```yaml
   resources:
     - name: fmapi-endpoint
       serving_endpoint:
         name: "databricks-claude-sonnet-4-5"
         permission: CAN_QUERY
   ```
5. Register the resource via API and redeploy:
   ```bash
   databricks apps update <app-name> --json '{
     "resources": [
       ...,
       {"name":"fmapi-endpoint","serving_endpoint":{"name":"databricks-claude-sonnet-4-5","permission":"CAN_QUERY"}}
     ]
   }' --profile=<profile>
   databricks apps deploy <app-name> --source-code-path <path> --profile=<profile>
   ```
6. Frontend: If building a direct summarization or generation UI (not through MAS), create a React component that calls your custom endpoint and streams the response using `fetch` with `ReadableStream`.

## MAS Integration
FMAPI is typically used inside MAS system instructions or via a Unity Catalog function sub-agent that calls FMAPI internally. It is not a direct MAS agent type.

To call FMAPI inside a UC function registered as a MAS sub-agent:
```python
# In your UC function (Python)
from databricks.sdk import WorkspaceClient
def my_uc_function(input_text: str) -> str:
    w = WorkspaceClient()
    response = w.serving_endpoints.query(
        name="databricks-claude-sonnet-4-5",
        messages=[{"role":"user","content":input_text}],
        max_tokens=512,
    )
    return response.choices[0].message.content
```

## Manual Setup (fallback without AI Dev Kit)
No setup needed — models are available at:
```
POST https://<workspace>/serving-endpoints/<model-name>/invocations
Authorization: Bearer <personal-access-token>
Content-Type: application/json

{
  "messages": [{"role": "user", "content": "Hello"}],
  "max_tokens": 512
}
```
Grant `CAN_QUERY` on the model endpoint to the app SP:
```bash
# Get endpoint UUID
databricks api get /api/2.0/serving-endpoints --profile=<profile> | \
  jq '.endpoints[] | select(.name=="databricks-claude-sonnet-4-5") | .id'

# Grant
databricks api patch /api/2.0/permissions/serving-endpoints/<uuid> \
  --json '{"access_control_list":[{"service_principal_name":"<app-sp-client-id>","permission_level":"CAN_QUERY"}]}' \
  --profile=<profile>
```
