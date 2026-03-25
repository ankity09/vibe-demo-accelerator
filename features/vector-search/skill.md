# Vector Search Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-demo` skill
- MCP tools: `create_vector_search_index`, `query_vector_search`
- A Delta Lake table with text data to embed (created via `notebooks/02_generate_data.py`)
- An embedding model endpoint (e.g., `databricks-gte-large-en` — available in all FEVM workspaces)
- Vector Search endpoint provisioned in the workspace

## Provisioning (via AI Dev Kit)
Use AI Dev Kit MCP tools — do NOT use raw REST API calls:
1. `create_vector_search_index` — Create a Vector Search index on the source Delta Lake table. Specify the embedding model endpoint, source column (text to embed), and primary key column. Use `Delta Sync` mode for automatic sync with Delta table changes.
2. `query_vector_search` — Validate the index by running a similarity query against a sample prompt.

Vector Search endpoint creation (one-time per workspace):
```bash
databricks api post /api/2.0/vector-search/endpoints \
  --json '{"name":"<demo>-vs-endpoint","endpoint_type":"STANDARD"}' \
  --profile=<profile>
# Takes ~15 min to provision. Poll until state = ONLINE.
databricks api get /api/2.0/vector-search/endpoints/<endpoint-name> --profile=<profile>
```

## VDA App Wiring
1. Copy or create `app/backend/routes/vector_search.py`:
   ```python
   import asyncio, os
   from fastapi import APIRouter
   from databricks.sdk import WorkspaceClient

   router = APIRouter()
   w = WorkspaceClient()
   VS_INDEX = os.getenv("VS_INDEX_NAME", "")

   @router.get("/vector-search/query")
   async def vector_query(q: str, num_results: int = 5):
       results = await asyncio.to_thread(
           w.vector_search_indexes.query_index,
           index_name=VS_INDEX,
           query_text=q,
           num_results=num_results,
       )
       return {"results": [r.as_dict() for r in results.result.data_array or []]}
   ```
2. Mount in `app/backend/main.py`:
   ```python
   from backend.routes.vector_search import router as vs_router
   app.include_router(vs_router, prefix="/api")
   ```
3. Add env vars in `app/app.yaml`:
   ```yaml
   - name: VS_ENDPOINT_NAME
     value: "<vector-search-endpoint-name>"
   - name: VS_INDEX_NAME
     value: "<catalog>.<schema>.<index-name>"
   ```
4. Grant the app SP `USE CATALOG`, `USE SCHEMA`, and `SELECT` on the source table and index in Unity Catalog:
   ```sql
   GRANT SELECT ON TABLE <catalog>.<schema>.<source_table> TO `<app-sp-client-id>`;
   ```
5. Frontend: Build a search input that calls `GET /api/vector-search/query?q=<text>` and renders ranked results. Use the VDA `.card` and `table` CSS components. Add a "Ask AI about this result" button that calls `askAI()` with the result context.

## MAS Integration
Wire Vector Search as a Unity Catalog function sub-agent in MAS so the AI can run semantic search during chat:
1. Register a UC Python function that calls the VS index:
   ```sql
   CREATE FUNCTION <catalog>.<schema>.semantic_search(query STRING, top_k INT DEFAULT 5)
   RETURNS TABLE(id STRING, text STRING, score DOUBLE)
   LANGUAGE PYTHON AS $$
   from databricks.sdk import WorkspaceClient
   w = WorkspaceClient()
   res = w.vector_search_indexes.query_index(
       index_name="<catalog>.<schema>.<index-name>",
       query_text=query, num_results=top_k
   )
   return [(r[0], r[1], r[2]) for r in res.result.data_array or []]
   $$;
   ```
2. Add to MAS agents array (use REST API PATCH since `create_or_update_mas` doesn't support UC functions):
   ```json
   {
     "agent_type": "unity-catalog-function",
     "unity_catalog_function": { "uc_path": { "catalog": "<catalog>", "schema": "<schema>", "name": "semantic_search" } },
     "name": "<demo>_semantic_search",
     "description": "Find relevant documents and records by semantic similarity. Use for 'find similar', 'what is most relevant to', or document lookup questions."
   }
   ```

## Manual Setup (fallback without AI Dev Kit)
```bash
# 1. Create VS endpoint (skip if one exists in workspace)
databricks api post /api/2.0/vector-search/endpoints \
  --json '{"name":"<demo>-vs","endpoint_type":"STANDARD"}' --profile=<profile>

# 2. Create Delta Sync index
databricks api post /api/2.0/vector-search/indexes \
  --json '{
    "name": "<catalog>.<schema>.<table>_index",
    "endpoint_name": "<demo>-vs",
    "primary_key": "id",
    "index_type": "DELTA_SYNC",
    "delta_sync_index_spec": {
      "source_table": "<catalog>.<schema>.<table>",
      "pipeline_type": "TRIGGERED",
      "embedding_source_columns": [{"name":"<text_column>","embedding_model_endpoint_name":"databricks-gte-large-en"}]
    }
  }' --profile=<profile>

# 3. Trigger initial sync
databricks api post "/api/2.0/vector-search/indexes/<catalog>.<schema>.<table>_index/sync" \
  --profile=<profile>
```
