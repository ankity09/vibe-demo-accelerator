# /demo-talk-track — Generate Demo Talk Track

Generate a structured talk track / demo script for presenting this demo to the customer.

## Steps

1. **Read `demo-config.yaml`** for the complete demo configuration (story, data model, UI, AI layer).
2. **Read `CLAUDE.md`** Project Identity for any additional context.
3. **Read the frontend** (`app/frontend/src/index.html`) to understand the actual pages, navigation, and features built.
4. **Read `app/backend/main.py`** to understand the API endpoints and what data is available.

## Generate the Talk Track

Create a `TALK_TRACK.md` file in the project root with this structure:

### Opening (2 minutes)
- Who you are, what Databricks does
- Why you're here — reference the customer's specific challenge (from `demo-config.yaml` narrative)
- What you'll show them today

### Architecture Slide (3 minutes)
- Show the 3-layer architecture (Delta Lake + Lakebase + AI agents)
- Map it to their specific use case
- Highlight: "Everything you see is running on Databricks — no external services"

### Dashboard Walkthrough (5 minutes)
- For each KPI card: explain what it measures and why it matters to THEM
- For each chart: tell the data story
- Point out: "This is querying Delta Lake in real-time — same data your analysts would use"

### Domain Pages (5 minutes per page)
- For each custom page: what it shows, what actions are available
- Reference their specific entities and terminology
- Show filtering, detail views, status management

### AI Chat Demo (5 minutes)
- Start with a simple data question (Genie Space handles it)
- Show the sub-agent step indicators ("See how it routes to the right tool?")
- Ask it to CREATE something (Lakebase MCP handles the write)
- Show the action card that appears
- Click through to approve/dismiss

### Agent Workflows (3 minutes)
- Show a workflow card
- Open the modal — show the agent orchestration diagram
- Click "Ask AI" for inline analysis
- Demonstrate approve/dismiss flow

### Closing (2 minutes)
- Recap: "Everything you saw — the data pipeline, the dashboards, the AI agents — runs on one platform"
- Reference their specific pain points from the opening
- Call to action: what the next step looks like

## Suggested Demo Questions

Generate 5-8 suggested questions the presenter can ask the AI chat during the demo, tailored to the customer's domain. These should showcase different capabilities:

1. A data lookup question (Genie Space)
2. A trend/comparison question (Genie Space)
3. A "create something" question (Lakebase MCP write)
4. A "what should I do about X?" question (supervisor reasoning)
5. A follow-up question that builds on a previous answer

## Handling Q&A

Include 5-8 likely questions from the customer and suggested answers:
- "How does the AI know about our data?" → Genie Space + table descriptions
- "Can the AI make mistakes?" → Guardrails, human-in-the-loop (action cards)
- "How long did this take to build?" → Scaffold + vibe, 2-4 hours
- "What about security/governance?" → Unity Catalog, SP permissions, OAuth
- "Can we customize this?" → Yes, everything is code, no black boxes

## Tips for the Presenter

- Open the app in the browser 5 minutes early to trigger OAuth login
- Have a second browser tab with the Databricks workspace open (for "behind the scenes" questions)
- If the AI chat is slow, explain: "The supervisor is orchestrating multiple agents — you can see each step"
- If something breaks: "This is a demo environment — in production, all of this would be monitored and auto-recovered"
