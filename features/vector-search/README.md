# Vector Search

Databricks Vector Search enables semantic similarity search over Delta Lake tables.
It indexes embeddings computed from text columns and returns the most relevant rows
for a given natural language query.

## What it does
- Creates and manages vector indexes backed by Delta Lake tables
- Supports both direct-access indexes (external embeddings) and delta-sync indexes (auto-embedded)
- Provides nearest-neighbor lookup for RAG, recommendation, and anomaly detection use cases
- Powers the Knowledge Assistant document retrieval layer

## Prerequisites
- Delta Lake table with a text column to embed
- Vector Search endpoint provisioned in the workspace
- Embedding model endpoint available (e.g., `databricks-bge-large-en`)

## Setup
1. Create a Vector Search endpoint via AI Dev Kit `create_or_update_vs_endpoint`
2. Create a delta-sync index pointing at your Delta table
3. Set `VS_ENDPOINT_NAME` and `VS_INDEX_NAME` in `app.yaml`
4. Install `databricks-vectorsearch` in `requirements.txt`
5. Query the index via `VectorSearchClient` or via the Knowledge Assistant

## Connection to the Demo
Vector Search is the retrieval backbone for the Knowledge Assistant. It also enables
"find similar" features in the frontend — e.g., "show me cases similar to this one" —
by embedding the query and returning the top-k matching rows from Delta Lake.
