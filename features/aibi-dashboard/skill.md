# AI/BI Dashboard Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-demo` skill
- MCP tools: `create_or_update_dashboard` (if available), or workspace UI
- Delta Lake tables populated (via `notebooks/02_generate_data.py`) — dashboards require data to exist
- SQL warehouse available and accessible
- Databricks workspace with AI/BI (Lakeview) enabled — available in all FEVM workspaces

## Provisioning (via AI Dev Kit)
Use AI Dev Kit MCP tools — do NOT use raw REST API calls:
1. Create the AI/BI dashboard using the workspace UI (Dashboards > New Dashboard) or via the REST API. Define datasets (SQL queries against your Delta Lake tables), then add visualizations (bar charts, line charts, scorecards, maps).
2. Use the Databricks Genie integration within the dashboard to add an AI-assisted Q&A panel — customers can ask natural language questions without leaving the dashboard.
3. Publish the dashboard and get the share URL for embedding in the VDA app.

Dashboard creation via API:
```bash
# Create dashboard
databricks api post /api/2.0/lakeview/dashboards --json '{
  "display_name": "<Demo> Analytics Dashboard",
  "serialized_dashboard": "{\"pages\":[{\"name\":\"page1\",\"displayName\":\"Overview\",\"layout\":[]}]}"
}' --profile=<profile>
# Returns: {"dashboard_id": "..."}
```

## VDA App Wiring
1. Create `app/backend/routes/aibi.py` to proxy dashboard embed URLs:
   ```python
   import asyncio, os
   from fastapi import APIRouter
   from databricks.sdk import WorkspaceClient

   router = APIRouter()
   w = WorkspaceClient()
   DASHBOARD_ID = os.getenv("AIBI_DASHBOARD_ID", "")

   @router.get("/aibi/embed-url")
   async def get_embed_url():
       if not DASHBOARD_ID:
           return {"url": ""}
       # Return the published dashboard URL for iframe embedding
       workspace_url = os.getenv("DATABRICKS_HOST", "")
       return {"url": f"{workspace_url}/embed/dashboardsv3/{DASHBOARD_ID}"}
   ```
2. Mount in `app/backend/main.py`:
   ```python
   from backend.routes.aibi import router as aibi_router
   app.include_router(aibi_router, prefix="/api")
   ```
3. Add env var in `app/app.yaml`:
   ```yaml
   - name: AIBI_DASHBOARD_ID
     value: "<dashboard-id>"
   ```
4. Frontend: Add an "Analytics" page that embeds the AI/BI dashboard in an `<iframe>`. This is a powerful pattern — it shows native Databricks capabilities alongside the custom app UI:
   ```javascript
   async function loadAnalytics() {
     const { url } = await fetchApi('/aibi/embed-url');
     document.getElementById('page-analytics').innerHTML = `
       <div class="card" style="padding:0;overflow:hidden;height:85vh;">
         <iframe src="${url}" style="width:100%;height:100%;border:none;" allow="fullscreen"></iframe>
       </div>
     `;
   }
   ```
5. Grant `CAN_VIEW` on the dashboard to the `users` group so demo users can view it:
   ```bash
   databricks api patch /api/2.0/permissions/dashboards/<dashboard-id> \
     --json '{"access_control_list":[{"group_name":"users","permission_level":"CAN_VIEW"}]}' \
     --profile=<profile>
   ```

## MAS Integration
AI/BI dashboards are not directly callable by MAS. However, they complement MAS by providing visual analytics context alongside the AI chat experience.

Pattern: Add a "View Full Dashboard" button in the chat interface that navigates to the Analytics page after the AI surfaces a key insight. Use `askAI()` in the reverse direction — from the Analytics page, add a "Dig Deeper with AI" button that pre-populates a chat prompt with the current dashboard filter context.

## Manual Setup (fallback without AI Dev Kit)
1. In the Databricks workspace, go to **Dashboards > New Dashboard**.
2. Create datasets: click **+ Add Dataset**, write SQL queries against your Delta Lake tables.
3. Add visualizations: click **+ Add Widget** and configure chart type, axes, and filters.
4. Enable Genie for AI-powered Q&A: click the Genie icon in the dashboard header and select a Genie Space.
5. Publish: click **Publish** to make the dashboard accessible.
6. Get the dashboard ID from the URL: `https://<workspace>/dashboardsv3/<dashboard-id>`.
7. Share with `CAN_VIEW` for `account users`:
   ```bash
   databricks api patch /api/2.0/permissions/dashboards/<dashboard-id> \
     --json '{"access_control_list":[{"group_name":"users","permission_level":"CAN_VIEW"}]}' \
     --profile=<profile>
   ```
