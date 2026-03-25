# Live Feed

The Live Feed engine simulates real-time streaming data for demos that need to show
time-series telemetry, sensor readings, or event streams updating in the UI.

## What it does
- Runs as a background `asyncio.Task` inside the FastAPI app process
- Inserts rows into Delta Lake tables via the Statement Execution API on a configurable cadence
- Supports multiple concurrent streams (e.g., temperature, pressure, throughput) per demo
- Includes geo-interpolation for spatial entities (lat/lon progress along a route with GPS jitter)
- Exposes `/api/streaming/start-live-feed`, `/stop-live-feed`, and `/live-feed-status` endpoints

## Prerequisites
- SQL Warehouse running during the demo (all inserts go through the warehouse)
- Delta Lake streaming tables created (see `notebooks/04_streaming_setup.py`)
- `LiveFeedEngine` configured in `main.py` with stream definitions and entity configs

## Setup
1. Define streaming table schemas in `notebooks/04_streaming_setup.py`
2. Define `StreamConfig` and `EntityConfig` objects in `main.py`
3. Instantiate `LiveFeedEngine` and call `engine.configure(streams=[...], entities=[...])`
4. Mount the streaming router: `app.include_router(create_streaming_router(engine))`
5. Add "Start Live Feed" toggle button in the frontend (see template comment blocks)

## Connection to the Demo
Live Feed creates the "real-time" effect that makes demos compelling. The frontend polls
`/api/streaming/live-feed-status` every 15 seconds when active and refreshes KPI tiles.
The feed auto-stops after the configured duration (default 5 minutes) to conserve warehouse credits.
