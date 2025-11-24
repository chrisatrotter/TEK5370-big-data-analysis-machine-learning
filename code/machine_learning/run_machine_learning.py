#!/usr/bin/env python3
# code/machine_learning/run_machine_learning.py
# FINAL — Runs all ML scripts in correct order

import subprocess
import sys
from pathlib import Path
from datetime import datetime

# === Scripts to run (in order) ===
SCRIPTS = [
    "export_full_archive.py",
    "per_fuse_minutely_forecast_xgboost.py",
    "nilm_per_fuse_detection.py"
]

# === Get this directory (machine_learning/) ===
script_dir = Path(__file__).parent.resolve()

print(f"[{datetime.now().strftime('%H:%M:%S')}] Starting Machine Learning Pipeline")
print(f"Running from: {script_dir}")
print("-" * 80)

for script in SCRIPTS:
    script_path = script_dir / script
    
    if not script_path.exists():
        print(f"ERROR: Script not found: {script_path}")
        print("Available scripts:")
        for p in script_dir.glob("*.py"):
            if p.name != "__init__.py":
                print(f"  • {p.name}")
        sys.exit(1)
    
    print(f"\n→ Running: {script}")
    print(f"   {script_path}")
    
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        cwd=script_dir
    )
    
    if result.returncode != 0:
        print(f"FAILED: {script}")
        print("STDOUT:")
        print(result.stdout)
        print("STDERR:")
        print(result.stderr)
        sys.exit(1)
    else:
        output = result.stdout.strip()
        if output:
            print(output)

print("\n" + "="*80)
print(f"[{datetime.now().strftime('%H:%M:%S')}] MACHINE LEARNING PIPELINE COMPLETED!")
print("="*80)
print("   • Full dataset exported")
print("   • Per-fuse minutely XGBoost models trained")
print("   • NILM (Non-Intrusive Load Monitoring) detection!")
print("   • All plots saved in results/plots/")
print("   • Models saved in models/per_fuse/")
print("="*80)