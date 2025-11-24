#!/usr/bin/env python3
# code/export_fuse_data_daily.py

from sqlalchemy import create_engine, text
from influxdb import InfluxDBClient
from datetime import datetime, timedelta
import pandas as pd
import sys
import time
from pathlib import Path
from dotenv import load_dotenv
import os

# === Load .env ===
env_path = Path(__file__).parent.parent / "env" / ".env"
load_dotenv(dotenv_path=env_path)

# === Config ===
DB_USER = os.getenv("MARIADB_USER")
DB_PASS = os.getenv("MARIADB_PASSWORD")
DB_HOST = os.getenv("MARIADB_HOST", "192.168.188.74")
DB_PORT = os.getenv("MARIADB_PORT", "3306")
DB_NAME = os.getenv("MARIADB_DATABASE", "homeassistant")
TABLE_NAME = os.getenv("TABLE_NAME", "energy_fuse_archive")

INFLUX_URL = os.getenv("INFLUX_URL", "http://192.168.188.74:8086")
INFLUX_USER = os.getenv("INFLUX_USER")
INFLUX_PASS = os.getenv("INFLUX_PASSWORD")
INFLUX_DB = os.getenv("INFLUX_BUCKET")  # Must be: homeassistantdb

CHECK_HOURS = int(os.getenv("CHECK_HOURS", "72"))

required = ["MARIADB_USER", "MARIADB_PASSWORD", "INFLUX_USER", "INFLUX_PASSWORD", "INFLUX_BUCKET"]
missing = [v for v in required if not os.getenv(v)]
if missing:
    print(f"ERROR: Missing env vars: {', '.join(missing)}")
    sys.exit(1)

DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

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

print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] Starting streaming export – last {CHECK_HOURS}h")

# === MariaDB ===
engine = create_engine(
    DB_URL,
    pool_pre_ping=True,
    pool_recycle=3600,
    isolation_level="AUTOCOMMIT",
    echo=False
)

with engine.connect() as conn:
    conn.execute(text("SELECT 1"))
print("MariaDB connected")

with engine.begin() as conn:
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id BIGINT AUTO_INCREMENT PRIMARY KEY,
            timestamp DATETIME(6) NOT NULL,
            entity_id VARCHAR(64) NOT NULL,
            value_w DOUBLE NOT NULL,
            CONSTRAINT uq_ts_entity UNIQUE (timestamp, entity_id),
            INDEX idx_timestamp (timestamp DESC),
            INDEX idx_entity (entity_id)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """))
print(f"Table `{TABLE_NAME}` ready")

# === InfluxDB 1.x ===
host = INFLUX_URL.replace("http://", "").replace("https://", "").split(":")[0]
client = InfluxDBClient(
    host=host, port=8086,
    username=INFLUX_USER, password=INFLUX_PASS,
    database=INFLUX_DB, timeout=60, retries=5
)

try:
    client.ping()
    dbs = [db["name"] for db in client.get_list_database()]
    if INFLUX_DB not in dbs:
        print(f"ERROR: Database '{INFLUX_DB}' not found! Available: {dbs}")
        sys.exit(1)
    print(f"InfluxDB 1.8 connected → '{INFLUX_DB}'")
except Exception as e:
    print(f"InfluxDB connection failed: {e}")
    sys.exit(1)

# === Determine cutoff timestamp (only insert newer data) ===
with engine.connect() as conn:
    result = conn.execute(text(f"SELECT MAX(timestamp) FROM {TABLE_NAME}")).scalar()
    cutoff_ts = pd.to_datetime(result, utc=True) if result else None

if cutoff_ts:
    print(f"Last record in DB: {cutoff_ts} → only newer data will be inserted")
else:
    print("First run → all data will be inserted")

# === Streaming fetch + direct insert per chunk ===
chunk_hours = 6
chunks = (CHECK_HOURS + chunk_hours - 1) // chunk_hours
now = datetime.utcnow()
total_inserted = 0

print(f"Streaming data in {chunks} chunks of {chunk_hours}h each → direct DB insert...")

for i in range(chunks):
    start_dt = now - timedelta(hours=CHECK_HOURS) + timedelta(hours=i * chunk_hours)
    end_dt = min(start_dt + timedelta(hours=chunk_hours), now)

    print(f"\nChunk {i+1}/{chunks}: {start_dt:%Y-%m-%d %H:%M} → {end_dt:%Y-%m-%d %H:%M} UTC")

    chunk_records = []

    for fuse in FUSE_IDS:
        query = f'''
            SELECT time, value
            FROM "W"
            WHERE entity_id = '{fuse}'
              AND time >= '{start_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}'
              AND time < '{end_dt.strftime('%Y-%m-%dT%H:%M:%SZ')}'
        '''
        try:
            result = client.query(query, epoch='ns')
            points = list(result.get_points())
            for p in points:
                ts = pd.to_datetime(p['time'], utc=True)
                if cutoff_ts is None or ts > cutoff_ts:
                    chunk_records.append({
                        "timestamp": ts,
                        "entity_id": fuse,
                        "value_w": float(p['value']) if p['value'] is not None else 0.0
                    })
            print(f"  • {fuse:<40} {len(points):>7,} points → {sum(1 for p in points if cutoff_ts is None or pd.to_datetime(p['time'], utc=True) > cutoff_ts):>6} new")
        except Exception as e:
            print(f"  • {fuse} → ERROR: {e}")

    if not chunk_records:
        print("  No new data in this chunk.")
        continue

    df_chunk = pd.DataFrame(chunk_records)
    print(f"  Inserting {len(df_chunk):,} new rows from this chunk...")

    chunk_size = 5000
    for start in range(0, len(df_chunk), chunk_size):
        subchunk = df_chunk.iloc[start:start + chunk_size]
        retries = 0
        while retries < 5:
            try:
                subchunk.to_sql(
                    name=TABLE_NAME,
                    con=engine,
                    if_exists='append',
                    index=False,
                    method='multi',
                    chunksize=1000
                )
                total_inserted += len(subchunk)
                print(f"    Inserted {start+1:,}–{start+len(subchunk):,} (total so far: {total_inserted:,})")
                break
            except Exception as e:
                if any(x in str(e) for x in ["Lock wait timeout", "Deadlock", "1205"]):
                    retries += 1
                    wait = 2 ** retries
                    print(f"    Lock timeout #{retries}, retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"    Fatal insert error: {e}")
                    raise
        else:
            print("    Max retries exceeded. Skipping this subchunk.")

client.close()
print(f"\n[{datetime.now():%H:%M:%S}] Export completed successfully!")
print(f"Total new rows inserted: {total_inserted:,}")
