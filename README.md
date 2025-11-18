# TEK5370 – Big Data and Machine Learning Analysis
Data gathering scripts for querying an InfluxDB instance connected to a Home Assistant setup.

This project was originally developed in a hosted Jupyter Notebook environment but can also be run locally using Python, provided all required packages are installed.

---

# 🚀 Project Overview

This repository contains Python code for:

- Connecting to an InfluxDB instance  
- Querying measurement data (e.g., power usage)  
- Cleaning and structuring time-series data  
- Exporting the processed data to CSV for further analysis  

Remote access is achieved through a **WireGuard VPN connection**.

---

# 🛠 Prerequisites

Before running any scripts, make sure you have:

- Python 3.9+
- All Python dependencies installed
- A working WireGuard configuration (the wireguard config can be found here: https://nextcloud.basicinternet.org/s/K7oD4pnHE8s6f9P?dir=/B-BigData_analysis)
- Network access to the Home Assistant InfluxDB instance over VPN

---

# 📦 Python Requirements

Install dependencies:

```
pip install -r requirements.txt
```

requirements.txt:

```
influxdb-client
pandas
matplotlib
python-dateutil
```

---

# 🔐 VPN Access Using WireGuard

## 1. Install WireGuard Tools

### macOS (Homebrew)
```
brew install wireguard-tools
```

### Linux (Debian/Ubuntu)
```
sudo apt update
sudo apt install wireguard
```

### Windows  
Download the official client:  
https://www.wireguard.com/install/

---

# 📄 Using Your WireGuard Configuration

Save your configuration as:

```
wireguard.conf
```

Example:

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

---

# 🔌 Connecting Using WireGuard (macOS/Linux)

```
chmod 600 wireguard.conf

# wg-quick up starts the VPN tunnel and keeps it open.
sudo wg-quick up ./wireguard.conf

# wg-quick down closes the VPN tunnel.
sudo wg-quick down ./wireguard.conf
```

Verify connection:

```
sudo wg
```

---

# 📊 Running the Data Gathering Script

```
python3 DataGather_1Fuse.py
```

This script queries InfluxDB, cleans the data, sorts by timestamp, and outputs `datatest.csv`.

---

# 🧪 Troubleshooting

### ModuleNotFoundError: No module named 'influxdb_client'
```
pip install influxdb-client
```

### Cannot connect to InfluxDB
Ensure WireGuard is connected.

---

# 📬 Support

For help with WireGuard, Home Assistant access, or InfluxDB queries, open an issue or contact the maintainer.
