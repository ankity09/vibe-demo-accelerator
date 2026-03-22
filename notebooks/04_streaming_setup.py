# Databricks notebook source
# Streaming Data Setup — Generic Template
# Creates Delta Lake tables for real-time streaming, defines entities/routes,
# generates 24h historical backfill, and optionally configures ZeroBus SDK.
#
# Cell 0:   Parameters (vibe fills from demo-config.yaml)
# Cell 1:   Create streaming Delta tables
# Cell 2:   Grant SP permissions
# Cell 3:   Define entities and routes/scenarios
# Cell 4:   Historical backfill (bulk, no ZeroBus)
# Cell 5-6: ZeroBus SDK install + init (skip if simulation-only)
# Cell 7:   Live streaming burst (5 min)
# Cell 8:   Verify row counts

# COMMAND ----------

# ── Cell 0: Parameters ──────────────────────────────────────────────────────────
# TODO: Vibe fills these from demo-config.yaml streaming section

CATALOG = "TODO_CATALOG"
SCHEMA = "TODO_SCHEMA"

# Service Principal credentials (required for ZeroBus and table grants)
CLIENT_ID = "<service-principal-client-id>"
CLIENT_SECRET = "<service-principal-client-secret>"
WORKSPACE_URL = "https://TODO_WORKSPACE_URL"
ZEROBUS_URL = "https://TODO_ZEROBUS_URL"  # Leave empty if simulation-only mode

# Streaming mode: "zerobus" or "simulation"
STREAMING_MODE = "zerobus"  # TODO: Set from demo-config.yaml streaming.mode

# ── Stream definitions ──
# Each stream targets one Delta table with a specific cadence.
# TODO: Vibe generates these based on streaming.streams in demo-config.yaml
#
# Format:
#   STREAMS = [
#       {
#           "name": "<stream name>",
#           "table": f"{CATALOG}.{SCHEMA}.<table_name>",
#           "cadence_seconds": 10|30|60,
#           "description": "<what this stream represents>",
#       },
#   ]
#
# Example (fleet telemetry):
#   STREAMS = [
#       {"name": "gps", "table": f"{CATALOG}.{SCHEMA}.fleet_gps_pings", "cadence_seconds": 10, "description": "GPS position pings"},
#       {"name": "sensors", "table": f"{CATALOG}.{SCHEMA}.fleet_sensor_readings", "cadence_seconds": 30, "description": "Sensor telemetry"},
#       {"name": "diagnostics", "table": f"{CATALOG}.{SCHEMA}.fleet_diagnostics", "cadence_seconds": 60, "description": "Vehicle diagnostics"},
#   ]

STREAMS = []  # TODO: Vibe fills this

spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")

print(f"Catalog:  {CATALOG}")
print(f"Schema:   {SCHEMA}")
print(f"Mode:     {STREAMING_MODE}")
print(f"Streams:  {len(STREAMS)}")
for s in STREAMS:
    print(f"  {s['name']}  -> {s['table']}  (every {s['cadence_seconds']}s)")

# COMMAND ----------

# ── Cell 1: Create streaming Delta tables ─────────────────────────────────────
# TODO: Vibe generates CREATE TABLE statements based on the streaming entity type.
#
# Each stream needs a Delta table with:
#   - entity_id (STRING) — identifier for the streaming entity
#   - timestamp (TIMESTAMP) — when the reading was taken
#   - Domain-specific columns based on stream type
#
# Example patterns by archetype:
#
# FLEET TELEMETRY (GPS):
#   spark.sql(f"""
#   CREATE TABLE IF NOT EXISTS {STREAMS[0]['table']} (
#       vehicle_id      STRING    COMMENT 'Vehicle identifier',
#       timestamp        TIMESTAMP COMMENT 'UTC timestamp of the reading',
#       latitude         DOUBLE    COMMENT 'WGS-84 latitude',
#       longitude        DOUBLE    COMMENT 'WGS-84 longitude',
#       heading_degrees  DOUBLE    COMMENT 'Compass heading 0-360',
#       speed_mph        DOUBLE    COMMENT 'Ground speed in mph',
#       route_id         STRING    COMMENT 'Active route identifier'
#   ) USING DELTA
#   COMMENT 'GPS pings — {STREAMS[0]["cadence_seconds"]}-second cadence'
#   """)
#
# IOT SENSORS:
#   spark.sql(f"""
#   CREATE TABLE IF NOT EXISTS {STREAMS[0]['table']} (
#       sensor_id        STRING    COMMENT 'Sensor identifier',
#       timestamp        TIMESTAMP COMMENT 'UTC timestamp',
#       reading_value    DOUBLE    COMMENT 'Primary sensor reading',
#       reading_unit     STRING    COMMENT 'Unit of measurement',
#       status           STRING    COMMENT 'Sensor status: normal, warning, alarm',
#       location_id      STRING    COMMENT 'Facility/zone location'
#   ) USING DELTA
#   COMMENT 'Sensor readings — {STREAMS[0]["cadence_seconds"]}-second cadence'
#   """)
#
# PATIENT VITALS:
#   spark.sql(f"""
#   CREATE TABLE IF NOT EXISTS {STREAMS[0]['table']} (
#       patient_id       STRING    COMMENT 'Patient identifier',
#       timestamp        TIMESTAMP COMMENT 'UTC timestamp',
#       heart_rate_bpm   INT       COMMENT 'Heart rate',
#       blood_pressure   STRING    COMMENT 'Systolic/diastolic',
#       spo2_pct         DOUBLE    COMMENT 'Oxygen saturation',
#       temperature_f    DOUBLE    COMMENT 'Body temperature'
#   ) USING DELTA
#   COMMENT 'Patient vitals — {STREAMS[0]["cadence_seconds"]}-second cadence'
#   """)

# TODO: Vibe generates actual CREATE TABLE statements here
# for stream in STREAMS:
#     spark.sql(f"CREATE TABLE IF NOT EXISTS {stream['table']} (...) USING DELTA")

print("[TODO] Vibe generates CREATE TABLE statements for each stream")

# COMMAND ----------

# ── Cell 2: Grant SP permissions ──────────────────────────────────────────────
# The app's service principal needs MODIFY + SELECT on streaming tables
# to INSERT data via the Statement Execution API during live feed.

for stream in STREAMS:
    spark.sql(f"GRANT MODIFY, SELECT ON TABLE {stream['table']} TO `{CLIENT_ID}`")
    print(f"  MODIFY + SELECT on {stream['table']}")

spark.sql(f"GRANT USE CATALOG ON CATALOG {CATALOG} TO `{CLIENT_ID}`")
spark.sql(f"GRANT USE SCHEMA ON SCHEMA {CATALOG}.{SCHEMA} TO `{CLIENT_ID}`")
print(f"[OK] Permissions granted to SP {CLIENT_ID}")

# COMMAND ----------

# ── Cell 3: Define entities and routes/scenarios ──────────────────────────────
# TODO: Vibe generates domain-specific entity definitions.
#
# Each entity represents a "thing" that generates streaming data (vehicle,
# sensor, patient, etc.). Entities have:
#   - entity_id: unique identifier
#   - origin/destination: lat/lon for geo entities (None for non-geo)
#   - scenario: what "drama" this entity creates during the live feed
#   - metadata: domain-specific attributes
#
# Example (fleet):
#   ENTITIES = [
#       {"entity_id": "VEH-001", "origin": (42.73, -110.93), "destination": (45.52, -122.68),
#        "scenario": "normal", "metadata": {"product": "Frozen Fries", "mode": "truck"}},
#       {"entity_id": "VEH-002", "origin": (42.73, -110.93), "destination": (41.88, -87.63),
#        "scenario": "fault", "metadata": {"product": "Fertilizer", "mode": "rail"}},
#   ]
#
# Example (IoT sensors):
#   ENTITIES = [
#       {"entity_id": "SENSOR-A1", "origin": None, "destination": None,
#        "scenario": "normal", "metadata": {"type": "temperature", "zone": "Zone A"}},
#       {"entity_id": "SENSOR-B3", "origin": None, "destination": None,
#        "scenario": "fault", "metadata": {"type": "vibration", "zone": "Zone B"}},
#   ]
#
# Scenarios determine behavior during live feed:
#   - "normal": steady-state readings with small random variation
#   - "fault": gradual drift then spike at ~60% progress (e.g., temp excursion)
#   - "warning": oscillation near threshold values
#   - "deviation": sudden step change at random progress point
#   - "depletion": monotonic decrease toward critical level (e.g., low fuel)

import hashlib
import math
from datetime import datetime, timedelta, timezone

ENTITIES = []  # TODO: Vibe fills this

# ── Deterministic helpers ──
def _hash_float(seed: str, lo: float, hi: float) -> float:
    """Deterministic float in [lo, hi] from a seed string."""
    h = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
    return lo + (h / 0xFFFFFFFF) * (hi - lo)

def _hash_int(seed: str, lo: int, hi: int) -> int:
    return int(_hash_float(seed, lo, hi + 0.999))

def _hash_choice(seed: str, options: list):
    return options[_hash_int(seed, 0, len(options) - 1)]

# ── Haversine distance (miles) ──
def _haversine(lat1, lon1, lat2, lon2):
    R = 3959.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(min(1.0, a)))

# ── Geo interpolation with jitter ──
def interpolate_position(origin, dest, progress, noise_seed):
    """Linear lat/lon interpolation with GPS jitter. Returns (lat, lon, heading, speed_mph)."""
    if origin is None or dest is None:
        return (0.0, 0.0, 0.0, 0.0)
    lat1, lon1 = origin
    lat2, lon2 = dest
    progress = max(0.0, min(1.0, progress))
    lat = lat1 + (lat2 - lat1) * progress
    lon = lon1 + (lon2 - lon1) * progress
    lat += _hash_float(f"gps-lat-{noise_seed}", -0.002, 0.002)
    lon += _hash_float(f"gps-lon-{noise_seed}", -0.002, 0.002)
    heading = math.degrees(math.atan2(lon2 - lon, lat2 - lat)) % 360
    # Speed ramp: accelerate first 5%, cruise middle, decelerate last 5%
    if progress < 0.05:
        spd_factor = progress / 0.05
    elif progress > 0.95:
        spd_factor = (1.0 - progress) / 0.05
    else:
        spd_factor = 1.0
    speed = _hash_float(f"spd-{noise_seed}", 52.0, 65.0) * spd_factor
    speed = max(0.0, speed + _hash_float(f"spd-n-{noise_seed}", -3.0, 3.0))
    return (round(lat, 6), round(lon, 6), round(heading, 1), round(speed, 1))

# ── Scenario modifier ──
def scenario_value(scenario, progress, base_value, normal_range, fault_peak, noise_seed):
    """Apply scenario-specific modification to a base reading value.

    Args:
        scenario: "normal", "fault", "warning", "deviation", "depletion"
        progress: 0.0 to 1.0 within the feed duration
        base_value: center value for normal operation
        normal_range: (lo, hi) variation around base_value
        fault_peak: value at peak fault condition
        noise_seed: deterministic noise seed
    Returns:
        Modified reading value
    """
    noise = _hash_float(noise_seed, normal_range[0], normal_range[1])
    if scenario == "normal":
        return base_value + noise
    elif scenario == "fault":
        # Gradual drift then spike at progress > 0.6
        if progress < 0.50:
            return base_value + noise
        elif progress < 0.75:
            drift = (progress - 0.50) / 0.25
            return base_value + (fault_peak - base_value) * drift + noise * 0.3
        else:
            return fault_peak + _hash_float(noise_seed + "f", -0.8, 0.8)
    elif scenario == "warning":
        # Oscillation near threshold
        threshold = base_value + (fault_peak - base_value) * 0.7
        osc = math.sin(progress * 20) * abs(fault_peak - base_value) * 0.15
        return threshold + osc + noise * 0.2
    elif scenario == "deviation":
        # Sudden step change at ~40% progress
        if progress > 0.40 and progress < 0.60:
            return fault_peak + noise * 0.5
        return base_value + noise
    elif scenario == "depletion":
        # Monotonic decrease
        start = base_value + abs(normal_range[1])
        end = base_value - abs(fault_peak - base_value) * 0.8
        return start + (end - start) * progress + noise * 0.3
    return base_value + noise

# ── Route duration (for geo entities) ──
def _route_duration_seconds(origin, dest, mode="truck"):
    """Estimate transit time in seconds."""
    if origin is None or dest is None:
        return 24 * 3600  # Default to 24h for non-geo entities
    dist = _haversine(origin[0], origin[1], dest[0], dest[1])
    if mode == "truck":
        return max(3600, dist * 1.3 / 55.0 * 3600)
    elif mode == "rail":
        return max(7200, dist * 1.2 / 28.0 * 3600)
    return max(3600, dist * 1.3 / 45.0 * 3600)


# TODO: Vibe generates domain-specific value generator functions here.
# Each stream needs a generator function that takes (entity, elapsed_seconds,
# total_duration, base_ts) and returns a dict matching the table schema.
#
# Example skeleton:
#
# def generate_stream1_reading(entity, elapsed, duration, base_ts):
#     progress = elapsed / duration if duration > 0 else 0.0
#     noise_seed = f"{entity['entity_id']}-{elapsed}"
#     ts = base_ts + timedelta(seconds=elapsed)
#     # ... compute values using scenario_value() and interpolate_position() ...
#     return {"entity_id": entity["entity_id"], "timestamp": ts, ...}

print(f"[OK] Entity and route engine loaded")
print(f"  {len(ENTITIES)} entities defined")
print(f"  Scenarios: {set(e.get('scenario', 'normal') for e in ENTITIES) if ENTITIES else 'none'}")

# COMMAND ----------

# ── Cell 4: Generate 24h historical data (bulk, no ZeroBus) ──────────────────
# TODO: Vibe generates the backfill loop for each stream.
#
# Pattern:
#   1. For each stream, iterate entities
#   2. For each entity, generate readings at the stream's cadence over 24h
#   3. Collect into a Spark DataFrame and write to the Delta table
#
# Example:
#
# import pandas as pd
# from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
#
# NOW = datetime.now(timezone.utc)
# HISTORY_START = NOW - timedelta(hours=24)
# HISTORY_SECONDS = 24 * 3600
#
# for stream in STREAMS:
#     rows = []
#     for entity in ENTITIES:
#         duration = _route_duration_seconds(entity.get("origin"), entity.get("destination"))
#         t = 0
#         while t < HISTORY_SECONDS:
#             elapsed_in_trip = t % duration
#             row = generate_STREAMNAME_reading(entity, elapsed_in_trip, duration, HISTORY_START)
#             row["timestamp"] = HISTORY_START + timedelta(seconds=t)
#             rows.append(row)
#             t += stream["cadence_seconds"]
#     print(f"  {stream['name']}: {len(rows):,} rows")
#     # Define schema matching CREATE TABLE columns
#     schema = StructType([...])
#     df = spark.createDataFrame(pd.DataFrame(rows), schema=schema)
#     df.write.mode("overwrite").saveAsTable(stream["table"])
#     print(f"  Wrote to {stream['table']}")
#
# print("[OK] 24h historical backfill complete")

print("[TODO] Vibe generates historical backfill for each stream")

# COMMAND ----------

# ── Cell 5: Install ZeroBus SDK ──────────────────────────────────────────────
# Skip this cell if STREAMING_MODE == "simulation"

if STREAMING_MODE == "zerobus":
    # %pip install databricks-zerobus-ingest-sdk>=0.2.0
    # %restart_python
    print("[INFO] Run: %pip install databricks-zerobus-ingest-sdk>=0.2.0")
    print("[INFO] Then: %restart_python")
    print("[INFO] Then proceed to Cell 6")
else:
    print("[SKIP] Simulation mode — ZeroBus SDK not needed")

# COMMAND ----------

# ── Cell 6: ZeroBus SDK setup (after restart) ────────────────────────────────
# NOTE: %restart_python clears all Python state. Re-define parameters here.
# Skip this cell if STREAMING_MODE == "simulation"

# TODO: Vibe re-defines CATALOG, SCHEMA, STREAMS, ENTITIES, and generator
# functions here (compact versions, post-restart). Same values as cells 0+3.

if STREAMING_MODE == "zerobus" and ZEROBUS_URL:
    # from zerobus.sdk.sync import ZerobusSdk
    # from zerobus.sdk.shared import RecordType, StreamConfigurationOptions, TableProperties
    #
    # sdk = ZerobusSdk(ZEROBUS_URL, WORKSPACE_URL)
    # options = StreamConfigurationOptions(record_type=RecordType.JSON)
    #
    # # Create a ZeroBus stream per Delta table
    # zb_streams = {}
    # for stream in STREAMS:
    #     table_props = TableProperties(stream["table"])
    #     zb_stream = sdk.create_stream(CLIENT_ID, CLIENT_SECRET, table_props, options)
    #     zb_streams[stream["name"]] = zb_stream
    #     print(f"  [OK] ZeroBus stream for {stream['name']} -> {stream['table']}")
    #
    # print(f"[OK] {len(zb_streams)} ZeroBus streams initialized")
    print("[TODO] Vibe generates ZeroBus SDK init code here")
else:
    print("[SKIP] Simulation mode or no ZeroBus URL")

# COMMAND ----------

# ── Cell 7: Live streaming burst ─────────────────────────────────────────────
# Pushes BURST_DURATION minutes of live data across all streams.
# For ZeroBus: uses parallel threads per stream.
# For simulation: uses direct INSERT via Statement Execution API.

import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BURST_DURATION_SECONDS = 300  # 5 minutes

# TODO: Vibe generates the streaming burst loop.
#
# ZeroBus pattern (parallel threads per stream):
#
# def stream_worker(stream_name, zb_stream, cadence, generator_fn, entities, duration):
#     """Worker thread for one ZeroBus stream."""
#     start = time.time()
#     rows_sent = 0
#     while (time.time() - start) < duration:
#         elapsed = time.time() - start
#         progress = elapsed / duration
#         base_ts = datetime.now(timezone.utc)
#         for entity in entities:
#             row = generator_fn(entity, elapsed, duration, base_ts)
#             # Convert timestamp to epoch microseconds for ZeroBus
#             if isinstance(row.get("timestamp"), datetime):
#                 row["timestamp"] = int(row["timestamp"].timestamp() * 1_000_000)
#             zb_stream.send(row)
#             rows_sent += 1
#         time.sleep(cadence)
#     return stream_name, rows_sent
#
# with ThreadPoolExecutor(max_workers=len(STREAMS)) as pool:
#     futures = []
#     for stream in STREAMS:
#         f = pool.submit(stream_worker, stream["name"], zb_streams[stream["name"]],
#                         stream["cadence_seconds"], GENERATOR_FNS[stream["name"]],
#                         ENTITIES, BURST_DURATION_SECONDS)
#         futures.append(f)
#     for f in as_completed(futures):
#         name, count = f.result()
#         print(f"  {name}: {count:,} rows sent")
#
# # Close ZeroBus streams
# for name, zb_stream in zb_streams.items():
#     zb_stream.close()
#     print(f"  [OK] Closed {name} stream")

print(f"[TODO] Vibe generates {BURST_DURATION_SECONDS}s live burst across {len(STREAMS)} streams")

# COMMAND ----------

# ── Cell 8: Verify row counts ────────────────────────────────────────────────

print("Streaming table row counts:")
for stream in STREAMS:
    count = spark.sql(f"SELECT COUNT(*) as cnt FROM {stream['table']}").collect()[0]["cnt"]
    print(f"  {stream['table']}: {count:,} rows")

print("\n[OK] Streaming setup complete")
print(f"Mode: {STREAMING_MODE}")
print(f"Streams: {len(STREAMS)}")
print(f"Entities: {len(ENTITIES)}")
