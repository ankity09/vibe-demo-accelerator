# Knowledge Assistant Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-demo` skill
- MCP tools: `create_or_update_knowledge_assistant` (if available), or workspace UI for document upload
- Domain documents ready to upload: SOPs, manuals, policies, FAQs, reference materials (PDF, DOCX, TXT)
- MAS provisioned or planned (KA is always a MAS sub-agent)

## Provisioning (via AI Dev Kit)
Use AI Dev Kit MCP tools — do NOT use raw REST API calls:
1. Create the Knowledge Assistant in the Databricks workspace:
   - Navigate to Playground > New Knowledge Assistant
   - Upload domain-specific documents (SOPs, compliance guides, playbooks, FAQs)
   - Note the KA ID from the URL: `/knowledge-assistant/<ka_id>`
2. Set the KA instructions to scope responses to the demo domain.
3. Reference the KA ID in `agent_bricks/ka_config.json` and `agent_bricks/mas_config.json`.
4. Wire into MAS as a `knowledge-assistant` sub-agent (see MAS Integration below).

## VDA App Wiring
1. No `routes.py` for Knowledge Assistant — queries flow through MAS chat.
2. Set env var in `app/app.yaml`:
   ```yaml
   - name: KA_TILE_ID
     value: "<ka_id>"
   ```
3. Update `agent_bricks/ka_config.json` with the actual KA ID, name, and instructions.
4. Add the KA as a sub-agent in `agent_bricks/mas_config.json`:
   ```json
   {
     "agent_type": "knowledge-assistant",
     "knowledge_assistant": { "knowledge_assistant_id": "<ka_id>" },
     "name": "<demo>_knowledge_base",
     "description": "Look up standard operating procedures, policies, and domain-specific reference knowledge. Use when the user asks about best practices, compliance requirements, or procedural guidance."
   }
   ```
5. Frontend: KA responses surface through the existing AI Chat page via the MAS streaming protocol. The `formatAgentName()` function in the frontend should map `<demo>_knowledge_base` to a user-friendly label like `"Knowledge Base"`.

## Document Strategy
Good KA documents for demos:
- **SOPs** — Step-by-step procedures (e.g., equipment inspection checklist, order escalation process)
- **Compliance guides** — Regulatory requirements, safety standards
- **Domain glossary** — Terms specific to the industry vertical
- **Best practices playbooks** — Recommended actions for common scenarios
- **Troubleshooting guides** — Known issues and resolution steps

Keep documents concise and well-structured. The KA retrieves relevant sections by semantic similarity — dense, well-titled sections perform better than large unstructured documents.

## MAS Integration
Add to `agent_bricks/mas_config.json` `agents` array:
```json
{
  "agent_type": "knowledge-assistant",
  "knowledge_assistant": { "knowledge_assistant_id": "<ka_id>" },
  "name": "<demo>_knowledge_base",
  "description": "Look up SOPs, policies, and domain knowledge. Use when the user asks about procedures, best practices, or compliance requirements."
}
```
MAS instructions should explicitly tell the supervisor when to route to KA vs. Genie (e.g., "Use <demo>_knowledge_base for procedural questions; use <demo>_data for numerical/analytical questions").

## Manual Setup (fallback without AI Dev Kit)
1. Open the Databricks workspace.
2. Go to **Playground** in the left sidebar.
3. Click **+ New Knowledge Assistant**.
4. Set the name (e.g., `<Demo> Knowledge Base`) and instructions.
5. Upload documents via the UI (drag-and-drop or file picker).
6. Copy the KA ID from the browser URL: `https://<workspace>/knowledge-assistant/<ka_id>`.
7. Update `agent_bricks/ka_config.json`:
   ```json
   {
     "name": "<Demo> Knowledge Base",
     "description": "...",
     "instructions": "You are a knowledge assistant for <domain>..."
   }
   ```
8. Reference `<ka_id>` in the MAS config.
