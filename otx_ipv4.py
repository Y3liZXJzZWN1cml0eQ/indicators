import requests
import csv
import os
from datetime import datetime, timedelta, timezone

OTX_API_KEY = os.getenv("OTX_API_KEY")
OTX_URL = "https://otx.alienvault.com/api/v1/indicators/export"

end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(hours=24)

params = {
    "since": start_time.isoformat(),
    "until": end_time.isoformat(),
    "types": "IPv4",
    "format": "json"
}

headers = {
    "X-OTX-API-KEY": OTX_API_KEY
}

response = requests.get(OTX_URL, headers=headers, params=params)
response.raise_for_status()

data = response.json()

if isinstance(data, dict) and "results" in data:
    indicators = data["results"]
elif isinstance(data, list):
    indicators = data
else:
    raise ValueError("Unexpected OTX response format")

ipv4_set = sorted({
    item["indicator"]
    for item in indicators
    if item.get("type") == "IPv4"
})

os.makedirs("iocs", exist_ok=True)

csv_path = "iocs/otx_ipv4.csv"

with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["IndicatorType", "IndicatorValue", "Source", "CollectedUTC"])
    for ip in ipv4_set:
        writer.writerow(["IPv4", ip, "AlienVault OTX", end_time.isoformat()])

print(f"Saved {len(ipv4_set)} IPv4 indicators to {csv_path}")
