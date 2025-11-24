#!/usr/bin/env python3
# check_influx_retention.py

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
INFLUX_DB = INFLUX_BUCKET.split("/")[0]  # e.g., "homeassistantdb"

print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Checking retention policies for database '{INFLUX_DB}'...")
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
    client.ping()
except Exception as e:
    print(f"Cannot connect to InfluxDB: {e}")
    sys.exit(1)


# =====================================================
# === Retention Policy Check ==========================
# =====================================================

try:
    rp_result = client.query(f"SHOW RETENTION POLICIES ON {INFLUX_DB}")
    rps = list(rp_result.get_points())

    if not rps:
        print("ERROR: No retention policies found!")
        sys.exit(2)

    print("\n=== Retention Policies ===")
    default_rp = None

    for rp in rps:
        name = rp["name"]
        duration = rp["duration"]
        default = rp["default"]

        print(f" - {name}: duration={duration}, default={default}")

        if default:
            default_rp = rp

    print("\n=== Default Retention Policy ===")
    if default_rp:
        name = default_rp["name"]
        duration = default_rp["duration"]

        if duration == "0s":
            print(f"Default RP: {name} (keeps data forever)")
        else:
            hours = int(duration.split("h")[0])
            print(f"Default RP: {name} (retains data for {hours} hours)")
    else:
        print("ERROR: No default retention policy found!")
        sys.exit(2)

except Exception as e:
    print(f"Failed to read retention policies: {e}")
    sys.exit(2)

print("\nRetention check completed successfully.")
