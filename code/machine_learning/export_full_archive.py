#!/usr/bin/env python3
# code/machine_learning/export_full_archive.py
import pandas as pd
import os, sys
from sqlalchemy import create_engine
from dotenv import load_dotenv
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
env_path = project_root / "env" / ".env"
load_dotenv(dotenv_path=env_path)

DB_USER = os.getenv("MARIADB_USER")
DB_PASS = os.getenv("MARIADB_PASSWORD")
DB_HOST = os.getenv("MARIADB_HOST", "192.168.188.74")
DB_PORT = os.getenv("MARIADB_PORT", "3306")
DB_NAME = os.getenv("MARIADB_DATABASE", "homeassistant")

if not DB_USER or not DB_PASS:
    print("ERROR: Missing credentials")
    sys.exit(1)

DB_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

data_dir = project_root / "data"
data_dir.mkdir(exist_ok=True)
output_path = data_dir / "energy_fuse_archive.parquet"

print(f"Exporting → {output_path}")

engine = create_engine(DB_URL)
df = pd.read_sql(
    "SELECT timestamp, entity_id, value_w FROM energy_fuse_archive ORDER BY timestamp",
    engine,
    parse_dates=['timestamp']
)

# Set timestamp as index and save
df = df.set_index('timestamp')
df.to_parquet(output_path)  # index=True by default
print(f"Exported {len(df):,} rows with timestamp as index")
