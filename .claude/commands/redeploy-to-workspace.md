# /redeploy-to-workspace — Deploy Demo to a New Workspace

You have a working demo and the user wants to deploy it to a different FEVM workspace. This command handles everything: workspace setup, CLI auth, target config creation, infrastructure provisioning, data deployment, and app deployment.

**The user only needs to provide the workspace URL. Everything else is derived from the existing demo.**

## Rules

1. Read `demo-config.yaml` to get the current demo's config (customer name, demo name, schema, data model, etc.)
2. If `demo-config.yaml` doesn't exist, read `CLAUDE.md` Project Identity section and `app/app.yaml` to reconstruct the config.
3. Use AskUserQuestion for any required input. Minimize questions — derive what you can.
4. Use `scripts/deploy.py` for all infrastructure and deployment steps.

---

## Step 1: Gather Workspace Info

Ask the user (use AskUserQuestion):

**1.1 Workspace URL** — What's the new workspace URL?
- Free text. Expect: `https://fe-sandbox-serverless-<name>.cloud.databricks.com`
- If they say "I need to create one": guide them to run `/databricks-fe-vm-workspace-deployment` first, then come back.

**1.2 CLI Profile** — Is the CLI profile already set up?
- Derive the profile name from the workspace URL (e.g., `fe-sandbox-serverless-my-demo` → `my-demo`).
- Options: "Yes, profile `<derived-name>` is ready", "No, I need to set it up"
- If NO: Run the auth command for them:
  ```bash
  databricks auth login <workspace-url> --profile=<derived-name>
  ```
  Verify with: `databricks current-user me --profile=<derived-name>`

## Step 2: Derive Config from Existing Demo

Read the existing demo config and derive ALL values for the new workspace. The user should NOT have to re-answer questions they already answered.

**Auto-derived values:**
- `app_name` — same as current demo (from `demo-config.yaml` or `app/app.yaml`)
- `catalog` — derive from workspace name: `serverless_<name_underscored>_catalog`
- `schema` — same as current demo
- `lakebase_instance` — same as current demo (or derive from app_name with hyphens)
- `lakebase_database` — same as current demo
- `demo_name` — same as current demo
- `demo_customer` — same as current demo
- `workspace_email` — get from `databricks current-user me --profile=<profile>`

**Must discover in the new workspace:**
- `warehouse_id` — List warehouses and pick the first serverless one:
  ```bash
  databricks warehouses list --profile=<profile> -o json
  ```
  If multiple exist, ask the user which one. If none, tell them to create one in the workspace UI.

**Set to empty (will be populated during AI layer setup):**
- `mas_tile_id` — ""
- `genie_space_id` — ""
- `ka_tile_id` — ""

**Show the derived config to the user:**
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    NEW WORKSPACE CONFIG
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Workspace:    <url>
Profile:      <profile>
App Name:     <app_name>
Catalog:      <catalog>
Schema:       <schema>
Warehouse:    <warehouse_id>
Lakebase:     <instance> / <database>
Demo:         <demo_name> for <demo_customer>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Ask: "Does this look right? I'll create the target config and start deploying."

## Step 3: Create DABs Target Config

Write `targets/<profile>.yml`:
```yaml
# Target: <profile> — created by /redeploy-to-workspace
targets:
  <profile>:
    workspace:
      host: <workspace_url>
    variables:
      app_name: "<app_name>"
      warehouse_id: "<warehouse_id>"
      catalog: "<catalog>"
      schema: "<schema>"
      lakebase_instance: "<lakebase_instance>"
      lakebase_database: "<lakebase_database>"
      mas_tile_id: ""
      genie_space_id: ""
      ka_tile_id: ""
      demo_name: "<demo_name>"
      demo_customer: "<demo_customer>"
      workspace_email: "<email>"
```

## Step 4: Deploy Infrastructure

Tell the user: "Deploying infrastructure to the new workspace. This takes ~10 minutes."

### Step 4A: Lakebase + App Template

Run:
```bash
python scripts/deploy.py --target <profile> --step lakebase --step template
```

### Step 4B: Data Notebooks

The Delta Lake data and Lakebase seed data need to be recreated in the new workspace. Run the notebooks in order:

1. Run `notebooks/01_setup_schema.sql` content via `execute_sql` MCP tool (update catalog/schema first)
2. Run `notebooks/02_generate_data.py` via MCP tool or workspace notebook UI
3. Seed Lakebase: Run `notebooks/03_seed_lakebase.py` or apply seed SQL via `databricks psql`

Report progress after each notebook.

### Step 4C: AI Layer

The Genie Space and MAS must be recreated in the new workspace (they don't transfer between workspaces).

Run the AI setup step for guided instructions:
```bash
python scripts/deploy.py --target <profile> --step ai
```

This prints the exact CLI commands. Execute them:

**`[PARALLEL]` — Launch simultaneously:**
- **Task 1:** Create Genie Space (POST → PATCH title → PATCH tables via serialized_space → grant CAN_RUN)
- **Task 2:** Check if shared Lakebase MCP server exists in this workspace. If not, deploy it.

**Sequential (needs Genie Space ID):**
- Create MAS with sub-agents (Genie Space + Lakebase MCP connection)
- Discover MAS tile ID from serving endpoints

**After creating Genie Space and MAS:**
1. Update `targets/<profile>.yml` with the new IDs:
   ```yaml
   mas_tile_id: "<first 8 chars>"
   genie_space_id: "<space_id>"
   ka_tile_id: "<if applicable>"
   ```
2. Update `app/app.yaml` with the new IDs (via template step):
   ```bash
   python scripts/deploy.py --target <profile> --step template
   ```

### Step 4D: Deploy App + Resources + Permissions

Run the remaining deploy steps:
```bash
python scripts/deploy.py --target <profile> --step deploy --step resources --step permissions --step verify
```

This handles:
- App deployment (via DABs or direct CLI)
- Resource registration + redeploy for PGHOST injection
- SP permission grants (catalog, warehouse, MAS endpoint, Lakebase tables)
- Health verification

## Step 5: Final Verification

After the deploy script completes:

1. Report the app URL
2. Check `/api/health` returns `{"status": "healthy"}`
3. If any checks fail, diagnose and fix using CLAUDE.md troubleshooting table

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    REDEPLOYMENT COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

New Workspace:  <url>
App URL:        <app_url>
Health:         healthy (SDK ✓, SQL Warehouse ✓, Lakebase ✓)
Target Config:  targets/<profile>.yml

For future code-only deploys to this workspace:
  databricks bundle deploy --target <profile>

For full redeploy (infrastructure + app):
  python scripts/deploy.py --target <profile>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```
