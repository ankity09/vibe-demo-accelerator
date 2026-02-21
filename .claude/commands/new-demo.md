# /new-demo — Scaffold Demo Wizard

You are a demo setup wizard. Walk the user through **8 phases** to configure, build, and deploy a new Databricks demo from the scaffold. Each phase has a specific purpose and explicit parallelization instructions.

**DO NOT write any code until the user approves the plan in Phase 6.**

## Rules

1. **One phase at a time.** Complete each phase fully before moving to the next.
2. **Use AskUserQuestion** for every question. Never assume answers.
3. **After each phase**, write the answers to `demo-config.yaml` in the project root (append, don't overwrite previous phases).
4. **Show a phase summary** after each phase so the user can correct anything.
5. **Use the Task tool for parallel work** wherever marked with `[PARALLEL]`. Launch multiple sub-agents simultaneously.
6. **Stay within the /new-demo flow** for the entire lifecycle — Q&A, planning, code gen, deployment, and verification. Do NOT break out of this flow.

---

## Phase 1: Customer Discovery & Story

Tell the user: "Let's start by understanding the customer. I'll research them so the demo resonates with their actual business."

### Step 1.1: Collect customer basics

Ask these questions (use AskUserQuestion):

**1.1a Customer name** — What's the customer name?
- Free text. This should be the real company name (we'll use it for research). If they prefer a fictional name for the demo itself, we'll ask later.

**1.1b Customer website** — What's their website URL?
- Free text. e.g., `https://www.simplot.com`

**1.1c Use case context** — Do you have a Salesforce Use Case Object (UCO) for this engagement?
- Options: "Yes, I have a UCO", "No, I'll describe the use case myself"
- If YES: Ask for the account name or UCO ID. Use the `salesforce-actions` skill / `field-data-analyst` subagent to pull:
  - UCO name, stage, description, implementation status
  - Account details (industry, segment, ARR)
  - Any related opportunities or blockers
  - SA and AE names on the account
- If NO: Ask them to describe in 2-3 sentences what the customer is trying to solve with Databricks. What's the business problem? What data do they have? What outcome do they want?

### Step 1.2: Research the customer

**IMPORTANT: Do this research AUTOMATICALLY after collecting the basics. Do NOT skip this step.**

**`[PARALLEL]` — Launch ALL of the following research tasks simultaneously using the Task tool:**

1. **Customer website deep-dive** (Task: Explore agent) — Use WebFetch on the customer's website. Visit multiple pages:
   - Homepage — what they do, products, services
   - About page — company scale, history, leadership
   - Newsroom / Press releases — recent initiatives, partnerships, challenges
   - Investor page (if public) — revenue, strategy, risks
   - **USE CASE CROSS-REFERENCE:** If the SA mentioned a specific use case area (e.g., "genomics"), also search `site:<customer-domain> <use-case-keywords>`. For example, if the SA says "Simplot + genomics", fetch `site:simplot.com genomics` results. Look for the customer's own description of their work in that area — their terminology, their scale, their goals. This makes the demo speak the customer's language.
   - Extract brand colors from the website CSS/visual style

2. **Industry + use case web search** (Task: general-purpose agent) — Use WebSearch for:
   - `"<customer name>" <use case keywords>` — find the customer's own public statements about the use case
   - `"<customer name>" data analytics OR "data platform" OR Databricks` — find their data initiatives
   - `"<customer name>" recent news <current year>` — last 6 months of news
   - `<industry> <use case> challenges trends <current year>` — industry context
   - `"<customer name>" competitors` — market position

3. **Salesforce context** (Task: field-data-analyst, if UCO available) — From the UCO/account data:
   - What Databricks products are they evaluating?
   - What stage is the engagement in?
   - Any known technical requirements or blockers?
   - Historical engagement notes

4. **Internal knowledge** (Task: general-purpose agent, if Glean/Slack MCP available) — Search for:
   - Internal Slack conversations about this customer
   - Previous demo materials or POC docs
   - Technical notes from other SAs who've worked with them

**Wait for all parallel tasks to complete before proceeding.**

### Step 1.3: Present research findings

After research, present a **Customer Brief** to the user:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        CUSTOMER BRIEF
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Company:      <name>
Industry:     <industry / sub-vertical>
Scale:        <revenue, employees, locations>
Website:      <url>

WHAT THEY DO
<2-3 sentences summarizing their business>

THEIR WORK IN <USE CASE AREA> (from website/public sources)
<What the customer themselves say about this area — their terminology,
their programs, their scale. This section makes the demo speak their language.>

KEY CHALLENGES (from research)
- <challenge 1 — from website/news>
- <challenge 2 — from industry context>
- <challenge 3 — from Salesforce/SA notes>

DEMO OPPORTUNITY
<How Databricks + this demo can address their specific challenges>

BRAND COLORS (extracted from website)
  Primary: <hex>  Accent: <hex>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 1.4: Define the demo story

Based on the research, propose a demo story and ask the user to confirm or adjust:

**1.4a Demo name** — Propose a name based on the customer + use case (e.g., "Simplot Genomics Intelligence Platform", "Apex Steel Predictive Maintenance"). Ask if they want to use the real customer name or a fictional one.

**1.4b Industry / Vertical** — Confirm the industry based on research. Don't ask if it's obvious.

**1.4c Key use cases** — Propose 2-4 use cases that align with the customer's actual challenges (from research). These should NOT be generic — they should use the customer's own terminology discovered during research. For example:
  - Instead of "genomics analytics" → "Accelerate Simplot's marker-assisted selection pipeline by unifying genotype data from 3 breeding programs with field trial phenotype data"
  - Instead of "demand forecasting" → "Forecast frozen potato product demand across Simplot's 12 distribution centers to reduce the $8M annual overstocking problem"

**1.4d Demo narrative** — Draft a 3-4 sentence narrative that:
  - Uses terminology and specifics found on the customer's own website
  - Describes the specific problem the demo solves
  - Shows the Databricks-powered solution
  - Mentions the expected business impact
  - Present this to the user and ask if it captures the right story.

### Step 1.5: Confirm or adjust

Show the complete Phase 1 summary and ask: "Does this capture the right story? Change anything you'd like."

**After the user confirms**, write to `demo-config.yaml`:
```yaml
# Demo Configuration — generated by /new-demo wizard
# Phase 1: Customer Discovery & Story
story:
  customer_name: "<real company name>"
  demo_name: "<demo display name — may use fictional name>"
  website: "<url>"
  industry: "<industry>"
  sub_vertical: "<sub-vertical>"
  scale: "<company scale summary>"
  customer_context: |
    <what the customer themselves say about the use case area,
    using their terminology — from website/public sources>
  brand_colors:
    primary: "<hex from website>"
    accent: "<hex from website>"
  salesforce:
    account_id: "<if available>"
    uco_id: "<if available>"
    stage: "<if available>"
    sa: "<if available>"
    ae: "<if available>"
  use_cases:
    - name: "<use case 1>"
      description: "<customer-specific description using their terminology>"
    - name: "<use case 2>"
      description: "<customer-specific description using their terminology>"
  narrative: "<3-4 sentence demo story>"
  research_notes: |
    <key findings from research that inform data model and UI decisions>
```

---

## Phase 2: Infrastructure

Tell the user: "Now let's set up the Databricks infrastructure."

**2.1 FEVM workspace** — Do you already have an FEVM workspace for this demo?
- Options: "Yes, I have one", "No, I need to create one"
- If NO: Guide them to run `/databricks-fe-vm-workspace-deployment` (Serverless Template 3, AWS). Tell them to come back when it's ready. **Pause this wizard until they confirm the workspace is created.**
- If YES: Continue.

**2.2 Workspace URL** — What's the workspace URL?
- Free text. Expect format: `https://fe-sandbox-serverless-<name>.cloud.databricks.com`

**2.3 CLI profile** — What's the Databricks CLI profile name?
- Suggest: the workspace name (e.g., `my-demo`). Remind them to run `databricks auth login <url> --profile=<name>` if not set up.

**2.4 Catalog name** — What's the Unity Catalog name?
- Suggest: `serverless_<name_with_underscores>_catalog` (FEVM auto-creates this). Ask them to confirm.

**2.5 Schema name** — What schema should we use?
- Suggest: based on the demo name from Phase 1 (e.g., `apex_steel_pm`). Use underscores, lowercase.

**2.6 SQL Warehouse ID** — What's the SQL warehouse ID?
- Tell them where to find it: Workspace → SQL Warehouses → click the warehouse → copy the ID from the URL or details page.

**After collecting all answers**, append to `demo-config.yaml`:
```yaml
# Phase 2: Infrastructure
infrastructure:
  workspace_url: "<answer>"
  cli_profile: "<answer>"
  catalog: "<answer>"
  schema: "<answer>"
  sql_warehouse_id: "<answer>"
```

Show summary and ask: "Phase 2 complete. Does this look right?"

---

## Phase 3: Data Model

Tell the user: "Now let's define the data model — what tables and metrics your demo needs."

**Use the research from Phase 1** to propose entities and KPIs that match the customer's actual business. Use the terminology found on their website. Don't just offer generic examples — tailor them.

**3.1 Main entities** — What are the primary entities in this demo?
- **Propose entities based on Phase 1 research.** For example, if you learned the customer is a food manufacturer doing genomics work with 3 breeding programs, propose: `breeding_programs`, `genotype_samples`, `field_trials`, `phenotype_observations`, `marker_panels`, `selection_candidates` — not generic "machines" and "sensors."
- If research didn't reveal enough, fall back to industry examples:
  - Manufacturing: machines, sensors, work_orders, spare_parts, production_lines
  - Healthcare: patients, beds, operating_rooms, staff, appointments
  - Financial: loans, borrowers, risk_scores, transactions, alerts
  - Retail: products, stores, orders, customers, promotions
  - Supply Chain: shipments, purchase_orders, inventory, suppliers, warehouses
- Ask them to confirm, add, or remove entities. Target 4-6.

**3.2 Key metrics / KPIs** — What numbers should appear on the dashboard?
- **Propose KPIs based on Phase 1 use cases and research.** For example, if the use case is genomics-driven breeding, propose: `selection_accuracy`, `breeding_cycle_time`, `trial_throughput`, `marker_hit_rate`, `genetic_gain_per_year`.
- If research didn't reveal enough, fall back to industry examples:
  - Manufacturing: OEE, MTBF, MTTR, defect rate, machine uptime %
  - Healthcare: avg wait time, bed utilization %, surgical throughput, readmission rate
  - Financial: portfolio value, default rate, VaR, credit score distribution
  - Retail: revenue, conversion rate, inventory turnover, out-of-stock rate
  - Supply Chain: on-time delivery %, fill rate, days of supply, freight cost per unit
- Ask them to pick 4-6 KPIs.

**3.3 Historical data range** — How much historical data should we generate?
- Options: "3 months", "6 months", "1 year", "2 years"

**3.4 Operational (Lakebase) tables** — Which entities need real-time read/write for the AI agent?
- Explain: "Delta Lake tables are for analytics (read-only dashboards). Lakebase tables are for operational data the AI agent can create and update (e.g., work orders, alerts, notes)."
- Suggest operational tables based on their entities. Typically: notes (always), agent_actions (always), workflows (always — these are core), plus 2-3 domain tables.

**After collecting all answers**, append to `demo-config.yaml`:
```yaml
# Phase 3: Data Model
data_model:
  entities:
    - name: "<entity>"
      description: "<brief description>"
      layer: "delta"  # or "lakebase" or "both"
  kpis:
    - name: "<KPI name>"
      description: "<what it measures>"
  historical_range: "<answer>"
  lakebase_tables:
    - "<table 1>"
    - "<table 2>"
```

Show summary and ask: "Phase 3 complete. Does this look right?"

---

## Phase 4: AI Layer

Tell the user: "Now let's configure the AI agents — Genie Space for data queries and MAS for orchestration."

**4.1 Genie Space tables** — Which Delta Lake tables should Genie be able to query with natural language?
- Suggest: all Delta Lake entities from Phase 3. The user can deselect any that shouldn't be queryable.

**4.2 MAS supervisor persona** — What role should the AI supervisor play?
- Generate a persona based on Phase 1 research that uses the customer's domain language. For example:
  - "You are an AI genomics operations assistant for Simplot. You help breeders analyze marker data, track field trial results, and identify top selection candidates across Simplot's 3 breeding programs..."
- Offer to generate one or let them write their own.

**4.3 Sub-agents** — What capabilities should the MAS have?
- Always include: Genie Space (data queries), Lakebase MCP (writes)
- Optional: Knowledge Assistant (docs/policies), UC functions (custom logic)
- Ask: "Beyond data queries (Genie) and database writes (Lakebase MCP), do you need a Knowledge Assistant for documents/policies, or any custom UC functions?"

**4.4 Lakebase MCP** — Should we deploy the Lakebase MCP server for agent writes?
- Options: "Yes (recommended)", "No, read-only agent is fine"
- Default to yes. Explain: "This lets the AI create work orders, update statuses, add notes — anything that writes to the database."

**After collecting all answers**, append to `demo-config.yaml`:
```yaml
# Phase 4: AI Layer
ai_layer:
  genie_tables:
    - "<table 1>"
    - "<table 2>"
  mas_persona: "<description>"
  sub_agents:
    - type: "genie_space"
      description: "<what it queries>"
    - type: "lakebase_mcp"
      description: "<what it writes>"
    - type: "knowledge_assistant"  # if selected
      description: "<what docs it knows>"
  deploy_lakebase_mcp: true
```

Show summary and ask: "Phase 4 complete. Does this look right?"

---

## Phase 5: UI

Tell the user: "Now let's design the look and feel."

**5.1 Layout style** — How should the app be laid out?
- Options: "Sidebar navigation (most common)", "Top navigation bar", "Dashboard-first (data-heavy)"
- Show a brief description of each.

**5.2 Color scheme** — What colors fit the customer's brand?
- **If Phase 1 research extracted brand colors**, propose those first: "I found these brand colors from their website: primary `<hex>`, accent `<hex>`. Should I use these?"
- Otherwise offer presets: "Dark industrial (navy/orange) — great for manufacturing", "Clean medical (white/teal) — great for healthcare", "Corporate blue (navy/blue) — great for finance", "Custom — I'll provide hex colors"
- If custom: ask for primary color (dark), accent color (bright), and optionally brand logo URL.

**5.3 Dashboard content** — What should the main landing page show?
- Options (multi-select): "KPI cards with key metrics", "Charts / visualizations", "Recent activity table", "Morning briefing / AI summary", "Command center with AI input", "Alerts / notifications panel"
- They can pick multiple.

**5.4 Additional pages** — Beyond AI Chat and Agent Workflows (included by default), what pages do you need?
- Suggest based on their entities from Phase 3. For example if they have "breeding_programs" and "field_trials", suggest "Breeding Programs" and "Field Trials" pages.
- Let them add/remove pages.

**After collecting all answers**, append to `demo-config.yaml`:
```yaml
# Phase 5: UI
ui:
  layout: "<sidebar|topnav|dashboard-first>"
  color_scheme:
    preset: "<brand-match|dark-industrial|clean-medical|corporate-blue|custom>"
    primary: "<hex>"
    accent: "<hex>"
  dashboard:
    - "kpi_cards"
    - "charts"
    - "recent_activity"
  pages:
    - name: "Dashboard"
      description: "<what it shows>"
    - name: "AI Chat"
      description: "Built-in — SSE streaming chat with MAS"
    - name: "Agent Workflows"
      description: "Built-in — workflow cards with agent orchestration"
    - name: "<Custom page>"
      description: "<what it shows>"
```

Show summary and ask: "Phase 5 complete. Does this look right?"

---

## Phase 6: Plan & Approve

After all 5 Q&A phases, display a **full configuration summary**:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
           DEMO CONFIGURATION SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CUSTOMER
  Company:     <real name>
  Demo Name:   <display name>
  Industry:    <industry / sub-vertical>
  Website:     <url>
  Scale:       <summary>
  Salesforce:  <UCO stage if available>

STORY
  Use Cases:   <list — customer-specific descriptions>
  Narrative:   <narrative referencing actual business context>

INFRASTRUCTURE
  Workspace:   <url>
  Profile:     <profile>
  Catalog:     <catalog>
  Schema:      <schema>
  Warehouse:   <id>

DATA MODEL
  Entities:    <list with layers>
  KPIs:        <list>
  History:     <range>
  Lakebase:    <tables>

AI LAYER
  Genie:       <tables>
  MAS Persona: <persona>
  Sub-agents:  <list>
  MCP Server:  <yes/no>

UI
  Layout:      <style>
  Colors:      <scheme>
  Dashboard:   <components>
  Pages:       <list>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Then **enter plan mode** using the `EnterPlanMode` tool. In plan mode:

1. Read the scaffold's `CLAUDE.md` thoroughly for all patterns, gotchas, and conventions.
2. Create a detailed implementation plan that lists every file to be created/modified, with a brief description of what goes in each.
3. Organize the plan into the 4 deployment phases (A through D) from the scaffold.
4. Include parallelization notes for each phase.
5. Exit plan mode with `ExitPlanMode` for user approval.

**The user must approve the plan before any code is generated.**

---

## Phase 7: Build

Once the plan is approved, generate all code. **Use the Task tool aggressively for parallel work.**

### Step 7.1: Generate config files

**`[PARALLEL]` — Launch these simultaneously:**

- **Task 1:** Fill in `CLAUDE.md` — Replace all TODO values in the Project Identity section.
- **Task 2:** Fill in `app/app.yaml` — Set warehouse ID, catalog, schema. Leave MAS tile ID and Lakebase as TODO (created during deployment).
- **Task 3:** Generate `lakebase/domain_schema.sql` — Create tables for the Lakebase entities.
- **Task 4:** Fill in `notebooks/01_setup_schema.sql` — Set catalog and schema names.

### Step 7.2: Generate data + backend

**`[PARALLEL]` — Launch these simultaneously:**

- **Task 1:** Generate `notebooks/02_generate_data.py` — Create data generation for all Delta Lake entities, using the KPIs and historical range from Phase 3. Use deterministic hash-based generation for reproducibility.
- **Task 2:** Generate `notebooks/03_seed_lakebase.py` — Create seeding for Lakebase operational tables.
- **Task 3:** Generate domain API routes in `main.py` — Add endpoints for each entity (list, detail, filters, CRUD for Lakebase entities).

### Step 7.3: Generate frontend

Generate the frontend in `app/frontend/src/index.html` based on Phase 5 UI preferences:
- Set CSS variables for the color scheme (use brand colors from research)
- Build the layout (sidebar/topnav/dashboard-first)
- Create the dashboard page with selected components
- Create additional domain pages
- Keep AI Chat and Agent Workflows as-is (just customize `formatAgentName()` and suggested prompts)

### Step 7.4: Generate agent configs

**`[PARALLEL]` — Launch these simultaneously:**

- **Task 1:** Generate `agent_bricks/mas_config.json` — Configure MAS with the persona and sub-agents.
- **Task 2:** Generate `genie_spaces/config.json` — Configure Genie Space with the selected tables.

### Step 7.5: Code review checkpoint

After all generation is complete, show the user a summary of what was generated:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        CODE GENERATION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Files created/modified:
  [x] CLAUDE.md (project identity filled)
  [x] app/app.yaml (config set)
  [x] app/backend/main.py (N domain routes added)
  [x] app/frontend/src/index.html (dashboard + N pages)
  [x] lakebase/domain_schema.sql (N tables)
  [x] notebooks/01_setup_schema.sql
  [x] notebooks/02_generate_data.py (N Delta tables)
  [x] notebooks/03_seed_lakebase.py (N Lakebase tables)
  [x] agent_bricks/mas_config.json
  [x] genie_spaces/config.json

Ready to deploy?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Ask: **"Code generation is complete. Ready to start deployment? I'll walk you through each step."**

---

## Phase 8: Deploy

Walk the user through deployment step by step. **This stays within the /new-demo flow.** After each deployment step, report status and move to the next.

### Step 8A: Delta Lake Data

Tell the user: "Deploying Phase A — creating the schema and generating Delta Lake data."

**`[PARALLEL]` — Launch simultaneously:**
- **Task 1:** Verify CLI profile and workspace access: `databricks current-user me --profile=<profile>`
- **Task 2:** Create schema: Run `notebooks/01_setup_schema.sql` content via `execute_sql` MCP tool

Then: Run `notebooks/02_generate_data.py` via `execute_sql` or `run_python_file_on_databricks` MCP tool.

Report: "Phase A complete — N Delta Lake tables created with X rows."

### Step 8B: Lakebase

Tell the user: "Deploying Phase B — setting up Lakebase."

**`[PARALLEL]` — Launch simultaneously (Lakebase instance takes 5-6 min, use that time):**
- **Task 1:** Create Lakebase instance: `databricks database create-instance <name> --profile=<profile>`
- **Task 2:** While instance provisions, seed Lakebase data by running `notebooks/03_seed_lakebase.py`... actually, wait — seeding needs the instance. Instead, prepare the seed data and commands.

Sequential steps:
1. Create Lakebase instance (wait for RUNNING state)
2. Create database in the instance
3. Apply `lakebase/core_schema.sql`
4. Apply `lakebase/domain_schema.sql`
5. Run `notebooks/03_seed_lakebase.py`

Report: "Phase B complete — Lakebase instance running, N tables created and seeded."

### Step 8C: AI Layer

Tell the user: "Deploying Phase C — setting up the AI agents."

**`[PARALLEL]` — Launch simultaneously:**
- **Task 1:** Create Genie Space, PATCH table_identifiers, grant CAN_RUN
- **Task 2:** Deploy Lakebase MCP Server as a separate app (if selected in Phase 4)
- **Task 3:** Create MAS with agent config (after Genie + MCP are ready — may need to wait)

Sequential after parallel:
1. Create UC HTTP connection for MCP server (needs MCP app URL)
2. Create MAS with all sub-agents (needs Genie Space ID + MCP connection ID)

Report: "Phase C complete — Genie Space, MAS, and Lakebase MCP server deployed."

### Step 8D: App Deploy

Tell the user: "Deploying Phase D — deploying the app and registering resources."

Sequential steps:
1. Sync app code to workspace
2. Deploy app: `databricks apps deploy <name> --source-code-path <path> --profile=<profile>`
3. **Register resources via API** (CRITICAL — app.yaml alone does NOT register them):
```bash
databricks apps update <app-name> --json '{
  "resources": [
    {"name": "sql-warehouse", "sql_warehouse": {"id": "<id>", "permission": "CAN_USE"}},
    {"name": "mas-endpoint", "serving_endpoint": {"name": "mas-<tile>-endpoint", "permission": "CAN_QUERY"}},
    {"name": "database", "database": {"instance_name": "<instance>", "database_name": "<db>", "permission": "CAN_CONNECT_AND_CREATE"}}
  ]
}' --profile=<profile>
```
4. **Redeploy** to inject PGHOST/PGPORT/PGDATABASE/PGUSER env vars
5. Grant SP permissions (SQL warehouse CAN_USE, catalog/schema USE+SELECT, Lakebase table grants)
6. Verify health: `GET /api/health` should return all three checks passing

### Step 8E: Final Verification

After deployment, verify everything works:

1. Report the app URL to the user
2. Check `/api/health` returns `{"status": "healthy"}`
3. If any checks fail, diagnose using the troubleshooting table in CLAUDE.md and fix automatically
4. Tell the user to open the app in their browser (OAuth login required)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            DEMO DEPLOYED SUCCESSFULLY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

App URL:      <url>
Health:       healthy (SDK ✓, SQL Warehouse ✓, Lakebase ✓)

Genie Space:  <name> (<N tables>)
MAS:          <name> (<N sub-agents>)
Lakebase MCP: <url>

Next steps:
  1. Open the app URL in your browser
  2. Try the AI Chat with a sample question
  3. Run /demo-talk-track to generate a talk track
  4. Practice the demo flow before the customer meeting

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

**IMPORTANT:** Read the scaffold's `CLAUDE.md` for all patterns, gotchas, and conventions. Follow every pattern documented there throughout all phases.
