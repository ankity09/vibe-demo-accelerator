# Knowledge Assistant

The Knowledge Assistant (KA) is an Agent Bricks sub-agent that provides RAG (retrieval-augmented
generation) over a curated document corpus — PDFs, wikis, SOPs, and domain documentation.

## What it does
- Ingests and indexes documents into Databricks Vector Search
- Answers questions with cited source passages from the knowledge base
- Works as a sub-agent within MAS for domain-specific Q&A alongside data queries
- Ideal for demos involving SOPs, maintenance manuals, regulatory documents, or product catalogs

## Prerequisites
- Vector Search endpoint and index already created and populated
- Documents uploaded via the Knowledge Assistant UI or API
- `KA_ID` available from the Agent Bricks workspace page

## Setup
1. Create a Knowledge Assistant via Agent Bricks UI or `manage_ka` tool
2. Upload documents (PDFs, text files, URLs)
3. Wait for indexing to complete
4. Add as a `knowledge-assistant` sub-agent in your MAS config (use kebab-case agent type)
5. Add `KA_ID` to `app.yaml` if queried directly

## Connection to the Demo
KA gives the AI Chat page access to unstructured knowledge that lives outside Delta Lake.
For example, when a user asks "what does the SOP say about handling a P1 outage", MAS
routes to KA, which retrieves the relevant SOP passages and includes them in the answer.
