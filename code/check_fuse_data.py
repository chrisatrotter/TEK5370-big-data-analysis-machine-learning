#!/usr/bin/env python3
# check_fuse_data.py
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# === Load .env from env/ folder ===
env_path = Path(__file__).parent.parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)

# === Read environment variables ===
INFLUX_URL = os.getenv("INFLUX_URL")
INFLUX_USER = os.getenv("INFLUX_USER")
INFLUX_PASSWORD = os.getenv("INFLUX_PASSWORD")
INFLUX_BUCKET = os.getenv("INFLUX_BUCKET")

# Validate required variables
required = ["INFLUX_URL", "INFLUX_USER", "INFLUX_PASSWORD", "INFLUX_BUCKET"]
missing = [var for var in required if not os.getenv(var)]
if missing:
    print(f"ERROR: Missing required env vars: {', '.join(missing)}")
    print(f"Checked file: {env_path}")
    sys.exit(1)

# Parse database name from bucket
INFLUX_DB = INFLUX_BUCKET.split("/")[0]  # homeassistantdb

# Configurable check window
CHECK_HOURS = int(os.getenv("CHECK_HOURS", "72"))

# === Fuse list ===
FUSE_IDS = [
    "03_solarinput63a_active_power",
    "ams_linje6_po",
    "ams_linje6_p",
    "11_varmepumpe32a_apparent_power",
    "12_vvbereder3kw16a_apparent_power",
    "04_fyrkjelevarmepump_active_power",
    "03a_kjokken_3p_230vl_active_power",
    "u05_billader16a_active_power",
    "05_kjokkenlys15a_active_power",
    "06_kjeller15a_active_power",
    "07_lysstikk1floor16a_active_power",
    "08_lysstikk2ndfloor1_active_power",
    "09_internet16a_active_power",
    "10badgammel13a_active_power",
    "u7_kitchen20a_active_power",
    "u8_kitchenlight16a_active_power",
    "u9_lysstikk16a_active_power",
    "u10_bad2nd16a_active_power"
]

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking fuse data (last {CHECK_HOURS}h)...")
print(f"Loaded config from: {env_path}")

# === Connect to InfluxDB 1.8 ===
from influxdb import InfluxDBClient

try:
    client = InfluxDBClient(
        host=INFLUX_URL.split("://")[1].split(":")[0],
        port=int(INFLUX_URL.split(":")[-1].split("/")[0]),
        username=INFLUX_USER,
        password=INFLUX_PASSWORD,
        database=INFLUX_DB,
        timeout=15
    )
    client.ping()  # Better than get_list_database()
except Exception as e:
    print(f"Cannot connect to InfluxDB: {e}")
    sys.exit(1)

# === Query ===
entity_regex = "|".join(FUSE_IDS)
query = f'''
SELECT entity_id, last(value) AS value
FROM "autogen"."W"
WHERE entity_id =~ /{entity_regex}/
  AND time >= now() - {CHECK_HOURS}h
GROUP BY entity_id
'''

try:
    result = client.query(query)
except Exception as e:
    print(f"Query failed: {e}")
    print("Query:")
    print(query.strip())
    sys.exit(1)

# === Results ===
fuses_with_data = {p["entity_id"] for p in result.get_points() if p.get("entity_id")}
missing_fuses = [f for f in FUSE_IDS if f not in fuses_with_data]

# === Output ===
if not missing_fuses:
    print("All fuses are reporting data!")
else:
    print(f"WARNING: {len(missing_fuses)} fuse(s) have NO data in the last {CHECK_HOURS}h:")
    for fuse in sorted(missing_fuses):
        print(f"   • {fuse}")

print(f"Checked {len(FUSE_IDS)} fuses → {len(fuses_with_data)} active, {len(missing_fuses)} missing.")

if missing_fuses:
    sys.exit(2)   # treat missing fuse as warning only

