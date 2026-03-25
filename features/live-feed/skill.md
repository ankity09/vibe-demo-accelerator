# Live Feed Integration (VDA)

## Prerequisites
- AI Dev Kit with `databricks-demo` skill
- MCP tools: `run_notebook_or_sql`
- Delta Lake streaming tables created (via `notebooks/04_streaming_setup.py`)
- SQL warehouse running (live feed inserts via Statement Execution API — warehouse must be active)
- `demo-config.yaml` has `streaming.enabled: true` with stream definitions

## Provisioning (via AI Dev Kit)
Use AI Dev Kit MCP tools — do NOT use raw REST API calls:
1. `run_notebook_or_sql` — Run `notebooks/04_streaming_setup.py` to create Delta streaming tables, define entities and routes/scenarios, and generate 24h historical backfill.
2. The notebook also optionally configures ZeroBus SDK for real-time streaming. If ZeroBus is not available, the app uses the `LiveFeedEngine` simulation mode (INSERTs via Statement Execution API).

Note: ZeroBus SDK only works in notebooks — it is NOT compatible with Databricks Apps runtime. The app always uses `core/livefeed.py` for simulation. Use `notebooks/04_streaming_setup.py` only for ZeroBus burst tests.

## VDA App Wiring
1. `core/livefeed.py` is the generic engine — DO NOT MODIFY. It handles background tasks, stream cadence, geo interpolation, and entity/scenario management.
2. In `app/backend/main.py`, configure and mount the live feed engine after the core imports section:
   ```python
   from backend.core.livefeed import LiveFeedEngine, StreamConfig, EntityConfig, create_streaming_router

   # 1. Instantiate engine
   engine = LiveFeedEngine(run_query_fn=run_query, catalog=CATALOG, schema=SCHEMA)

   # 2. Define domain-specific value generators
   def my_sensor_generator(entity, progress, elapsed, scenario):
       base_temp = 72.0
       if scenario == "fault": base_temp = 95.0
       elif scenario == "warning": base_temp = 85.0
       jitter = random.uniform(-2, 2)
       return {
           "sensor_id": f"'{entity.entity_id}'",
           "temperature": str(round(base_temp + jitter, 2)),
           "timestamp": "CURRENT_TIMESTAMP()",
       }

   # 3. Configure streams and entities
   engine.configure(
       streams=[
           StreamConfig(name="sensors", table="sensor_readings", cadence_seconds=30, generator=my_sensor_generator),
       ],
       entities=[
           EntityConfig(entity_id="SENSOR-001", scenario="normal"),
           EntityConfig(entity_id="SENSOR-002", scenario="fault"),
       ],
   )

   # 4. Mount streaming router (adds /api/streaming/* endpoints)
   app.include_router(create_streaming_router(engine))
   ```
3. Streaming router endpoints mounted at `/api/streaming/`:
   - `POST /start-live-feed` — Start background feed (auto-stops after `duration` seconds, default 300)
   - `POST /stop-live-feed` — Stop gracefully
   - `GET /live-feed-status` — Running state, elapsed time, per-stream stats
   - `GET /stats` — Row counts per stream and per entity
4. No additional env vars needed beyond `CATALOG`, `SCHEMA`, and `DATABRICKS_WAREHOUSE_ID`.
5. Frontend: Add a Telemetry Status Bar with KPI tiles and a "Start Live Feed" toggle button. The frontend polls `/api/streaming/live-feed-status` every 15s when the feed is active:
   ```javascript
   async function toggleLiveFeed(start) {
     await fetchApi(`/streaming/${start ? 'start' : 'stop'}-live-feed`, { method: 'POST' });
     if (start) liveFeedPoller = setInterval(refreshTelemetry, 15000);
     else clearInterval(liveFeedPoller);
   }
   ```

## MAS Integration
Live feed data is written to Delta Lake tables. These tables are queryable by Genie Space — add streaming tables to the Genie Space `serialized_space` so MAS can answer questions about real-time data:
```json
{"identifier": "<catalog>.<schema>.sensor_readings"},
{"identifier": "<catalog>.<schema>.fleet_gps_pings"}
```
MAS instructions should distinguish between historical (batch) and live (streaming) tables:
```
Use sensor_readings for real-time sensor data (updated every 30s during live demos).
Use sensor_history for historical trend analysis.
```

## Streaming Scenarios
The `LiveFeedEngine` supports per-entity scenarios that the generator function uses to produce realistic anomaly data:
- `normal` — Nominal values within expected ranges
- `fault` — Critical values indicating equipment failure
- `warning` — Elevated values approaching fault threshold
- `deviation` — Drift from baseline, slow degradation pattern
- `depletion` — Inventory/capacity declining toward zero

Use `EntityConfig(entity_id="...", scenario="fault")` to pre-assign scenarios. The scenario affects all generators for that entity.

## Manual Setup (fallback without AI Dev Kit)
1. Run `notebooks/04_streaming_setup.py` in a Databricks notebook.
2. Fill in the `STREAMS`, `ENTITIES`, and table `CREATE TABLE` statements in the notebook.
3. Run Cell 0 (params), Cell 1 (create tables), Cell 2 (grant SP permissions), Cell 3 (define entities), Cell 4 (historical backfill).
4. Skip Cells 5-7 (ZeroBus) if using simulation mode.
5. Verify row counts in Cell 8.

Grant the app SP INSERT access to streaming tables:
```sql
GRANT INSERT ON TABLE <catalog>.<schema>.sensor_readings TO `<app-sp-client-id>`;
GRANT SELECT ON TABLE <catalog>.<schema>.sensor_readings TO `<app-sp-client-id>`;
```
