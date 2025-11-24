<<<<<<< HEAD
# TEK5370 – Big Data and Machine Learning Analysis
Data gathering scripts for querying an InfluxDB instance connected to a Home Assistant setup.
=======
# TEK5370 – Smart Grid & IoT: Big Data Project (2025)
>>>>>>> 551e1e2 (adding group project.)

**Real-time Energy Monitoring, Archiving, Forecasting & Non-Intrusive Load Monitoring (NILM) · Minutely XGBoost forecasting · Full MariaDB + Parquet archive**

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Pandas](https://img.shields.io/badge/pandas-2.0%2B-150458)
![XGBoost](https://img.shields.io/badge/xgboost-2.0%2B-brightgreen)
![InfluxDB 1.8](https://img.shields.io/badge/InfluxDB-1.8-orange)
![MariaDB](https://img.shields.io/badge/MariaDB-10.6%2B-003545)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)

## Project Overview

This repository contains Python code for a **full end-to-end smart home energy monitoring pipeline**:

- Connects to an InfluxDB 1.8 instance (Home Assistant)
- Queries, cleans, and structures minutely power measurements
- Exports data to MariaDB and Parquet for long-term storage
- Performs **per-fuse minutely forecasting** using XGBoost
- Conducts **Non-Intrusive Load Monitoring (NILM)** for appliances
- Fully automated master pipeline via `project.py`
- Secure remote access via **WireGuard VPN**

## Repository Structure

```
.
├── code/                        # Core Python scripts
│   ├── check_fuse_data.py
│   ├── export_fuse_data_daily.py
│   ├── project.py
│   └── machine_learning/        # ML pipeline
│       ├── export_full_archive.py
│       ├── nilm_per_fuse_detection.py
│       ├── per_fuse_minutely_forecast_xgboost.py
│       └── run_machine_learning.py
├── data/
│   └── energy_fuse_archive.parquet
├── env/
│   └── README.md                # Environment variable management
├── models/                      # Trained ML models (XGBoost)
│   ├── per_fuse/*.json
│   └── xgboost_minutely.json
├── results/                     # ML outputs
│   ├── nilm_minutely_summary.csv
│   ├── per_fuse_results.csv
│   └── plots/
│       ├── *.png                # NILM plots
│       └── per_fuse/*.png       # Per-fuse forecast plots
├── requirements.txt
└── README.md
```

## Prerequisites

- Python 3.9+
- WireGuard VPN access to your smart home network
- Access to Home Assistant InfluxDB and MariaDB
- Required Python packages installed via:

```bash
pip install -r requirements.txt
```

## WireGuard VPN Setup

1. **macOS (Homebrew)**

```bash
brew install wireguard-tools
```

2. **Linux (Debian/Ubuntu)**

```bash
sudo apt update
sudo apt install wireguard
```

3. **Windows**

Download the official client: https://www.wireguard.com/install/

### Using Your WireGuard Configuration

Save your configuration as `wireguard.conf`. Example:

```
[Interface]
PrivateKey = <secret>
Address = 192.168.188.211/24
DNS = 192.168.188.1
DNS = fritz.box

[Peer]
PublicKey = <secret>
PresharedKey = <secret>
AllowedIPs = 192.168.188.0/24,0.0.0.0/0
Endpoint = ae2gdjgkr5pqbdbn.myfritz.net:52623
PersistentKeepalive = 25
```

Connect via macOS/Linux:

```bash
chmod 600 wireguard.conf
sudo wg-quick up ./wireguard.conf
sudo wg-quick down ./wireguard.conf
sudo wg  # Verify connection
```

## Running the Pipeline

### Step 1: Check Fuse Data

```bash
python3 code/check_fuse_data.py
```
In this script, we check that we are able to receive data from the fuses.

### Step 2: Export Daily Data to MariaDB

```bash
python3 code/export_fuse_data_daily.py
```
Here we extract the data from the Influx DB to store for persistent storage to MariaDB.

### Step 3: Run Full ML Pipeline

```bash
python3 code/machine_learning/run_machine_learning.py
```
Finally, we run the machine learning pipeline to forcast based on XGBoost and do a NILM per fuse detection on a minute by minute basis.

### Step 4: Run Full Project (ML pipeline/Check Fuse/Export Daily)

```bash
python3 code/project.py
```

This will sequentially:
- Check fuse data
- Export InfluxDB → MariaDB
- Export full archive to Parquet
- Train per-fuse XGBoost models
- Perform NILM detection
- Save all plots and models

---

# 🌱 Managing Environment Variables

This project supports multiple environments using `.env` files stored in
the **env/** directory.


👉 **See: [`env/README.md`](./env/README.md)**

The environment README explains how to configure and load:

-   `local.env` -- local development
-   `dev.env` -- development server
-   `.env` -- production environment

To load an environment file into your shell:
## Authors
Farah Said Omar\
Christopher A. Trotter

Built during TEK5370 – Smart Grid & IoT, University of Oslo, 2025

## License

MIT License – feel free to use, modify, and impress your professors.