# AI/BI Dashboard

Databricks AI/BI Dashboards are next-generation, auto-generated business intelligence dashboards
that combine traditional charts with natural language editing and AI-assisted visualization design.

## What it does
- Creates publication-quality dashboards from Delta Lake tables with drag-and-drop and NL editing
- Supports scheduled refresh, embedding via iframe, and public sharing links
- AI can suggest chart types, write SQL widgets, and explain charts in plain language
- Can be embedded directly in the demo frontend via iframe for a seamless experience

## Prerequisites
- Delta Lake tables populated with domain data
- SQL Warehouse for dashboard query execution
- Dashboard created and published in the workspace
- App SP has `CAN_VIEW` or `CAN_RUN` on the dashboard

## Setup
1. Create a dashboard via AI Dev Kit `create_or_update_dashboard` or the workspace UI
2. Add widgets and configure the SQL queries backing each visualization
3. Publish the dashboard with `publish_dashboard`
4. Set `AIBI_DASHBOARD_ID` in `app.yaml`
5. Embed in the frontend using an iframe pointing at the dashboard's embedded URL

## Connection to the Demo
AI/BI Dashboards add an instant "wow" moment to any demo. Embed the published dashboard
in a dedicated page of the frontend, then show the audience how the AI can edit it —
"make that bar chart a line chart and add a 30-day moving average" — in real time.
