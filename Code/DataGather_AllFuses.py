import pandas as pd
from influxdb_client import InfluxDBClient
import matplotlib.pyplot as plt

# Connection settings
username = "homeassistant"
password = "homeassistant"
influx_host = "http://192.168.188.74:8086"
token = f"{username}:{password}"
org = "-"
database_name = "homeassistantdb"

# Initialize client
client = InfluxDBClient(
    url=influx_host,
    token=token,
    org=org
)

fuse_id = [
    "03_solarinput63a_active_power",
    "ams_linje6_po",
    "ams_linje6_p",
    "11_varmepumpe32a_apparent_power",
    "12_vvbereder3kw16a_active_power",
    "u05_billader16a_active_power",
    "04_fyrkjelevarmepump_active_power",
    "03a_kjokken_3p_230vl_active_power",
    "05_kjokkenlys15a_active_power",
    "06_kjeller15a_active_power",
    "07_lysstikk1floor16a_active_power",
    "08_lysstikk2ndfloor1_active_power",
    "10badgammel13a_active_power"
]

results = []

for fuse in fuse_id:

    fuse_results = []

    flux_query = f'''
    from(bucket: "{database_name}/autogen")
      |> range(start: -24h)
      |> filter(fn: (r) => r._measurement == "W" and r._field == "value")
      |> filter(fn: (r) => r.entity_id == "{fuse}")
    '''

    print("Start:", fuse)

    try:
        result = client.query_api().query(query=flux_query)
        for table in result:
            for record in table.records:
                fuse_results.append(record)

        results.append(fuse_results)

    except Exception as e:
        print("An error occurred:", e)

    print("End:", fuse)


# Convert query results into structured data
structured_data = []

for data in results:
    fuse_structured_data = []

    for record in data:
        fuse_structured_data.append({
            'field': record["_field"],
            'value': record["_value"],
            'measurement': record["_measurement"],
            'timestamp': record["_time"],
            'entity_id': record["entity_id"],
            'domain': record.values.get("domain")  # domain might not exist
        })

    structured_data.append(fuse_structured_data)


# Flatten list of lists
flat_structured_data = [
    record for fuse_data in structured_data for record in fuse_data
]

df = pd.DataFrame(flat_structured_data)

# Clean and convert values
df = df.dropna(subset=['value'])
df['value'] = pd.to_numeric(df['value'], errors='coerce')
df = df.dropna(subset=['value'])

# Convert timestamps
df['timestamp'] = pd.to_datetime(df['timestamp'])

# Sort chronologically
df = df.sort_values(by='timestamp')

# Save to CSV
df.to_csv('Data_Signatures_Grid.csv', index=False)

print("Saved file: Data_Signatures_Grid.csv")

# Plot each fuse separately
for fuse in fuse_id:
    fuse_data = df[df['entity_id'] == fuse]

    if fuse_data.empty:
        print(f"⚠️ No data for {fuse}")
        continue

    plt.figure(figsize=(15, 6))
    plt.plot(fuse_data['timestamp'], fuse_data['value'], linestyle='-')
    plt.xlabel('Time')
    plt.ylabel('Value')
    plt.title(f'Value Over Time: {fuse}')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Combined plot
plt.figure(figsize=(15, 8))

for fuse in fuse_id:
    fuse_data = df[df['entity_id'] == fuse]
    if not fuse_data.empty:
        plt.plot(fuse_data['timestamp'], fuse_data['value'], label=fuse)

plt.xlabel('Time')
plt.ylabel('Value')
plt.title('Combined Value Over Time for All Fuses')
plt.xticks(rotation=45)
plt.legend(title='Fuse ID', loc='upper left', bbox_to_anchor=(1, 1))
plt.tight_layout()
plt.show()
