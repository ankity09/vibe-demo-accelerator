# VDA Feature System + Wizard + Dev Loop — Implementation Plan (Plan 2 of 2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the AI Dev Kit-powered feature system (14 Databricks capabilities as pluggable modules), redesign the `/new-demo` wizard with 3-phase terminal flow, integrate companion browser dev loop, and update all documentation for the React architecture.

**Architecture:** Each Databricks feature is a self-contained module in `features/` with a skill.md (vibe instructions), config.json (metadata + AI Dev Kit dependencies), and optional routes.py/components. The wizard reads AI Dev Kit tool availability to show dynamic feature options. The deploy script gets a `build` step for the React frontend.

**Tech Stack:** Markdown skills, JSON configs, Python (FastAPI routes, deploy script), YAML (demo-config), vibe skills

**Spec:** `docs/superpowers/specs/2026-03-25-vda-react-redesign-design.md` (Sections 6-9)

**Depends on:** Plan 1 (Foundation + Component Library) — completed.

---

## Task 1: Create features/ directory structure with all 14 feature modules

**Files to create:** 14 `features/<name>/config.json` files + 14 `features/<name>/README.md` files

Create the complete features directory with config.json and README.md for each:

- [ ] **Step 1: Create all config.json files**

Create `features/<name>/config.json` for each of these 14 features:

**genie/**
```json
{
  "name": "Genie Space",
  "id": "genie",
  "description": "Natural language SQL queries via Databricks Genie",
  "category": "ai",
  "ai_dev_kit": {
    "required_tools": ["create_or_update_genie", "ask_genie"],
    "required_skills": ["databricks-genie"]
  },
  "env_vars": [
    { "key": "GENIE_SPACE_ID", "description": "Genie Space ID", "example": "01abc..." }
  ],
  "app_dependencies": { "python": [], "npm": [] },
  "requires": ["sql-warehouse"],
  "auto_include_with": []
}
```

**mas/**
```json
{
  "name": "Multi-Agent Supervisor (MAS)",
  "id": "mas",
  "description": "Orchestrated AI chat with multiple sub-agents",
  "category": "ai",
  "ai_dev_kit": {
    "required_tools": ["manage_mas"],
    "required_skills": ["databricks-agent-bricks"]
  },
  "env_vars": [
    { "key": "MAS_TILE_ID", "description": "First 8 chars of MAS tile UUID", "example": "a1b2c3d4" }
  ],
  "app_dependencies": { "python": [], "npm": [] },
  "requires": ["sql-warehouse"],
  "auto_include_with": ["lakebase"]
}
```

**knowledge-assistant/**
```json
{
  "name": "Knowledge Assistant",
  "id": "knowledge-assistant",
  "description": "Document Q&A using Databricks Knowledge Assistant",
  "category": "ai",
  "ai_dev_kit": {
    "required_tools": ["manage_ka"],
    "required_skills": ["databricks-agent-bricks"]
  },
  "env_vars": [
    { "key": "KA_TILE_ID", "description": "Knowledge Assistant tile ID", "example": "e5f6g7h8" }
  ],
  "app_dependencies": { "python": [], "npm": [] },
  "requires": ["sql-warehouse"],
  "auto_include_with": []
}
```

**foundation-model-api/**
```json
{
  "name": "Foundation Model API",
  "id": "foundation-model-api",
  "description": "Direct LLM calls via Databricks Foundation Model API",
  "category": "ai",
  "ai_dev_kit": {
    "required_tools": ["query_serving_endpoint"],
    "required_skills": ["databricks-model-serving"]
  },
  "env_vars": [
    { "key": "FMAPI_MODEL", "description": "Model name", "example": "databricks-claude-sonnet-4" }
  ],
  "app_dependencies": { "python": [], "npm": [] },
  "requires": ["sql-warehouse"],
  "auto_include_with": []
}
```

**vector-search/**
```json
{
  "name": "Vector Search",
  "id": "vector-search",
  "description": "RAG-based document retrieval using Databricks Vector Search",
  "category": "ml",
  "ai_dev_kit": {
    "required_tools": ["create_or_update_vs_endpoint", "create_or_update_vs_index", "query_vs_index"],
    "required_skills": ["databricks-vector-search"]
  },
  "env_vars": [
    { "key": "VS_INDEX_NAME", "description": "Vector Search index name", "example": "catalog.schema.docs_index" },
    { "key": "VS_ENDPOINT_NAME", "description": "Vector Search endpoint", "example": "my-vs-endpoint" }
  ],
  "app_dependencies": { "python": ["databricks-vectorsearch"], "npm": [] },
  "requires": ["sql-warehouse"],
  "auto_include_with": []
}
```

**model-serving/**
```json
{
  "name": "Model Serving",
  "id": "model-serving",
  "description": "Custom ML model inference via Databricks Model Serving",
  "category": "ml",
  "ai_dev_kit": {
    "required_tools": ["query_serving_endpoint", "get_serving_endpoint_status"],
    "required_skills": ["databricks-model-serving"]
  },
  "env_vars": [
    { "key": "MODEL_ENDPOINT_NAME", "description": "Serving endpoint name", "example": "my-model-endpoint" }
  ],
  "app_dependencies": { "python": [], "npm": [] },
  "requires": ["sql-warehouse"],
  "auto_include_with": []
}
```

**feature-store/**
```json
{
  "name": "Feature Store",
  "id": "feature-store",
  "description": "Online feature serving for real-time ML inference",
  "category": "ml",
  "ai_dev_kit": {
    "required_tools": ["manage_uc_objects"],
    "required_skills": ["databricks-unity-catalog"]
  },
  "env_vars": [
    { "key": "FEATURE_TABLE", "description": "Feature table path", "example": "catalog.schema.features" }
  ],
  "app_dependencies": { "python": ["databricks-feature-engineering"], "npm": [] },
  "requires": ["sql-warehouse"],
  "auto_include_with": []
}
```

**ai-gateway/**
```json
{
  "name": "AI Gateway",
  "id": "ai-gateway",
  "description": "LLM routing, rate limiting, and cost tracking",
  "category": "data-platform",
  "ai_dev_kit": {
    "required_tools": ["list_serving_endpoints"],
    "required_skills": ["databricks-model-serving"]
  },
  "env_vars": [],
  "app_dependencies": { "python": [], "npm": [] },
  "requires": ["sql-warehouse"],
  "auto_include_with": []
}
```

**declarative-pipelines/**
```json
{
  "name": "Declarative Pipelines (DLT)",
  "id": "declarative-pipelines",
  "description": "Data quality, lineage, and pipeline orchestration",
  "category": "data-platform",
  "ai_dev_kit": {
    "required_tools": ["create_or_update_pipeline", "get_pipeline", "start_update"],
    "required_skills": ["databricks-spark-declarative-pipelines"]
  },
  "env_vars": [
    { "key": "PIPELINE_ID", "description": "DLT pipeline ID", "example": "abc123..." }
  ],
  "app_dependencies": { "python": [], "npm": [] },
  "requires": ["sql-warehouse"],
  "auto_include_with": []
}
```

**lakeflow-connect/**
```json
{
  "name": "Lakeflow Connect",
  "id": "lakeflow-connect",
  "description": "External source ingestion (Salesforce, Postgres, etc.)",
  "category": "data-platform",
  "ai_dev_kit": {
    "required_tools": [],
    "required_skills": []
  },
  "env_vars": [],
  "app_dependencies": { "python": [], "npm": [] },
  "requires": ["sql-warehouse"],
  "auto_include_with": [],
  "manual_setup_required": true
}
```

**aibi-dashboard/**
```json
{
  "name": "AI/BI Dashboard",
  "id": "aibi-dashboard",
  "description": "Embedded AI/BI Lakeview dashboards",
  "category": "data-platform",
  "ai_dev_kit": {
    "required_tools": ["create_or_update_dashboard", "publish_dashboard"],
    "required_skills": ["databricks-aibi-dashboards"]
  },
  "env_vars": [
    { "key": "DASHBOARD_ID", "description": "Lakeview dashboard ID", "example": "abc123..." }
  ],
  "app_dependencies": { "python": [], "npm": [] },
  "requires": ["sql-warehouse"],
  "auto_include_with": []
}
```

**lakebase/**
```json
{
  "name": "Lakebase",
  "id": "lakebase",
  "description": "Real-time OLTP database for operational data",
  "category": "operational",
  "ai_dev_kit": {
    "required_tools": ["create_or_update_lakebase_database", "generate_lakebase_credential"],
    "required_skills": ["databricks-lakebase-provisioned"]
  },
  "env_vars": [
    { "key": "LAKEBASE_INSTANCE", "description": "Lakebase instance name (hyphens, not underscores)", "example": "my-demo-db" },
    { "key": "LAKEBASE_DATABASE", "description": "Database name", "example": "demo_data" }
  ],
  "app_dependencies": { "python": ["psycopg2-binary"], "npm": [] },
  "requires": [],
  "auto_include_with": []
}
```

**live-feed/**
```json
{
  "name": "Live Feed / Streaming",
  "id": "live-feed",
  "description": "Real-time data simulation via LiveFeedEngine",
  "category": "operational",
  "ai_dev_kit": {
    "required_tools": [],
    "required_skills": []
  },
  "env_vars": [],
  "app_dependencies": { "python": [], "npm": [] },
  "requires": ["sql-warehouse"],
  "auto_include_with": [],
  "uses_core_module": "livefeed.py"
}
```

**workflows-jobs/**
```json
{
  "name": "Workflows / Jobs",
  "id": "workflows-jobs",
  "description": "Scheduled pipeline visibility and job management",
  "category": "operational",
  "ai_dev_kit": {
    "required_tools": ["manage_jobs", "manage_job_runs"],
    "required_skills": ["databricks-jobs"]
  },
  "env_vars": [],
  "app_dependencies": { "python": [], "npm": [] },
  "requires": ["sql-warehouse"],
  "auto_include_with": []
}
```

- [ ] **Step 2: Create README.md for each feature**

Each README.md should be a brief 10-20 line doc explaining what the feature does, prerequisites, and how it connects to the demo.

- [ ] **Step 3: Commit**

```bash
git add features/
git commit -m "feat: create features/ directory with config.json and README.md for 14 Databricks capabilities"
```

---

## Task 2: Write skill.md for all 14 features

Each `features/<name>/skill.md` follows the pattern from the spec: prerequisites, provisioning via AI Dev Kit, VDA app wiring, and manual setup fallback.

- [ ] **Step 1: Write skill.md files for all 14 features**

Each skill.md should include:
1. **Prerequisites** — AI Dev Kit tools and skills needed
2. **Provisioning** — Step-by-step AI Dev Kit MCP tool calls
3. **VDA App Wiring** — How to integrate into the running app (routes, components, config)
4. **Manual Setup** — Fallback instructions when AI Dev Kit is not available
5. **MAS Integration** — If applicable, how to wire as a MAS sub-agent

- [ ] **Step 2: Commit**

```bash
git add features/
git commit -m "feat: add skill.md integration instructions for all 14 feature modules"
```

---

## Task 3: Write feature routes.py files

Create backend route files for features that need runtime API endpoints. Not all features need routes — some only need provisioning.

- [ ] **Step 1: Create routes for features that need them**

Features needing routes.py:
- `features/genie/routes.py` — `/genie/query` endpoint proxying Genie Conversation API
- `features/vector-search/routes.py` — `/search/query` endpoint for vector similarity search
- `features/model-serving/routes.py` — `/predict` endpoint for model inference
- `features/foundation-model-api/routes.py` — `/llm/generate` endpoint for direct LLM calls
- `features/declarative-pipelines/routes.py` — `/pipelines/status` endpoint for pipeline monitoring
- `features/workflows-jobs/routes.py` — `/jobs/status` and `/jobs/runs` endpoints
- `features/aibi-dashboard/routes.py` — `/dashboard/embed` endpoint returning dashboard embed URL

Each route file uses `APIRouter()`, imports from `backend.core`, and follows the async pattern with `asyncio.to_thread()`.

- [ ] **Step 2: Commit**

```bash
git add features/
git commit -m "feat: add FastAPI route templates for 7 feature modules"
```

---

## Task 4: Redesign /new-demo skill with 3-phase wizard

Update the existing skill at `skills/SKILL.md` to implement the 3-phase wizard from the spec.

- [ ] **Step 1: Read the current SKILL.md to understand its structure**
- [ ] **Step 2: Rewrite SKILL.md with the 3-phase wizard**

The new skill should instruct vibe to:

**Phase 1: Identity & Infrastructure**
- Ask for: demo name, customer, industry, use cases (2-4), workspace URL, CLI profile, catalog, schema
- Auto-detect SQL Warehouse ID via AI Dev Kit `get_best_warehouse` if available
- Record all answers

**Phase 2: Databricks Features**
- Detect AI Dev Kit capabilities by checking which MCP tools are available
- Read `features/*/config.json` to build the feature menu
- Pre-select features based on use-case keyword matching:
  - "real-time" / "streaming" / "sensor" / "IoT" → live-feed
  - "anomaly" / "prediction" / "ML" / "model" → model-serving
  - "work order" / "automation" / "agent" / "chat" → mas + lakebase
  - "Q&A" / "document" / "search" / "RAG" → vector-search + knowledge-assistant
  - "query" / "SQL" / "data" / "analytics" → genie
  - "pipeline" / "ETL" / "ingestion" → declarative-pipelines
  - "dashboard" / "report" / "visualization" → aibi-dashboard
- Auto-include dependencies (mas → lakebase)
- Show feature checklist grouped by category with ★ for recommended
- Fallback: if AI Dev Kit not detected, show all features with manual setup note

**Phase 3: UI Preferences**
- Layout: sidebar (default), topnav, dashboard-first
- Theme: recommend based on industry (manufacturing→industrial, healthcare→medical, financial→corporate, default→neutral)
- Mode: dark (default) or light
- Dashboard description: free-form text
- Additional pages: free-form text

**Output:** Write `demo-config.yaml` with all gathered info

**Post-wizard:** Execute the Feature Activation Flow from the spec

- [ ] **Step 3: Commit**

```bash
git add skills/
git commit -m "feat: redesign /new-demo skill with 3-phase wizard and AI Dev Kit detection"
```

---

## Task 5: Update deploy.py with build step

Add React frontend build step to the deployment orchestrator.

- [ ] **Step 1: Read current deploy.py**
- [ ] **Step 2: Add `build` step**

Insert a `build` step between `template` and `lakebase` in the step sequence. The step runs:
```python
def step_build(config):
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "app", "frontend")
    if not os.path.isfile(os.path.join(frontend_dir, "package.json")):
        log.warning("No package.json found — skipping frontend build")
        return
    subprocess.run(["npm", "install"], cwd=frontend_dir, check=True)
    subprocess.run(["npm", "run", "build"], cwd=frontend_dir, check=True)
    print(f"  ✓ Frontend built to {frontend_dir}/dist/")
```

Update `ALL_STEPS` to include `"build"` after `"template"`.

- [ ] **Step 3: Commit**

```bash
git add scripts/deploy.py
git commit -m "feat: add frontend build step to deploy.py"
```

---

## Task 6: Update CLAUDE.md for React architecture

The project CLAUDE.md needs to reflect the new React architecture, component library, theme system, and feature system.

- [ ] **Step 1: Read current CLAUDE.md**
- [ ] **Step 2: Update sections**

Key updates:
- **Architecture section**: Update to describe React + Vite frontend, component library, theme system
- **Project Structure**: Update the directory tree to show new `app/frontend/src/` structure with components/vda/, layouts/, hooks/, stores/, styles/, and `features/`
- **Frontend Patterns**: Replace the single-HTML patterns with React patterns (component imports, route config, useApi, useSSE, theme tokens)
- **CSS Variables**: Update to describe `surface`/`content`/`accent` Tailwind namespace
- **Adding New Pages**: Simplify to "create page in pages/, add route entry"
- **Build & Dev Commands**: Add `cd app/frontend && npm run dev` for Vite HMR, update build command
- **Quality Checklist**: Add `cd app/frontend && npx tsc --noEmit` and `npm run build`
- **Feature System**: New section describing the features/ directory and how to add new features
- **Deployment Sequence**: Add `build` step, reference `scripts/deploy.py`
- Keep ALL existing gotchas — they still apply to the backend

- [ ] **Step 3: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for React architecture, component library, and feature system"
```

---

## Task 7: Update databricks.yml and create demo-config.yaml template

- [ ] **Step 1: Read current databricks.yml**
- [ ] **Step 2: Update databricks.yml**

Ensure the app resource points to the frontend dist directory and the source_code_path is correct for the new structure.

- [ ] **Step 3: Create demo-config.yaml template**

Write `demo-config.template.yaml` as a reference template with all fields documented:
```yaml
# VDA Demo Configuration — Generated by /new-demo wizard
# Copy this to demo-config.yaml and fill in your values

demo:
  name: "TODO"
  customer: "TODO"
  industry: "TODO"
  use_cases:
    - "TODO"

infrastructure:
  workspace_url: "TODO"
  cli_profile: "TODO"
  catalog: "TODO"
  schema: "TODO"
  warehouse_id: "TODO"

features: []  # e.g., [genie, mas, lakebase, live-feed]

ui:
  layout: "sidebar"  # sidebar | topnav | dashboard
  theme: "neutral"   # industrial | medical | corporate | neutral
  mode: "dark"       # dark | light
  dashboard:
    description: "TODO — describe what the landing page should show"
  pages: []  # e.g., ["Equipment health", "Quality metrics"]
```

- [ ] **Step 4: Commit**

```bash
git add databricks.yml demo-config.template.yaml
git commit -m "feat: update databricks.yml and add demo-config template"
```

---

## Task 8: Update examples/ with React reference

- [ ] **Step 1: Update or create examples/react_reference.md**

Write a concise reference showing how to build a typical page using VDA components:
- How to create a new page
- How to use KPIDashboard, DataExplorer, AgentChat
- How to add a route
- How to use the theme system
- How to use useApi for data fetching

- [ ] **Step 2: Commit**

```bash
git add examples/
git commit -m "docs: add React component reference in examples/"
```

---

## Task 9: Final integration verification + push

- [ ] **Step 1: Full TypeScript check**
```bash
cd app/frontend && npx tsc --noEmit
```

- [ ] **Step 2: Full build**
```bash
cd app/frontend && npm run build
```

- [ ] **Step 3: Verify Python imports**
```bash
cd app && python -c "from backend.main import app; print('Backend OK')"
```

- [ ] **Step 4: Verify features directory**
```bash
find features/ -name "config.json" | wc -l  # should be 14
find features/ -name "skill.md" | wc -l     # should be 14
```

- [ ] **Step 5: Git status and final commit if needed**

- [ ] **Step 6: Push to GitHub**
```bash
git push origin main
```

---

## Execution Order

All tasks are sequential (each builds on the previous):
```
Task 1 (configs) → Task 2 (skills) → Task 3 (routes) → Task 4 (wizard) → Task 5 (deploy.py) → Task 6 (CLAUDE.md) → Task 7 (databricks.yml) → Task 8 (examples) → Task 9 (verify + push)
```

Tasks 1-3 can be parallelized (different files in features/). Tasks 4-8 are sequential updates to different files and can also be parallelized.
