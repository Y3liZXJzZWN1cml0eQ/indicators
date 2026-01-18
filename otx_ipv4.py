import requests
import csv
import os
from datetime import datetime, timedelta, timezone

# ======================
# CONFIG
# ======================
OTX_API_KEY = os.getenv("OTX_API_KEY")
OTX_URL = "https://otx.alienvault.com/api/v1/indicators/export"

if not OTX_API_KEY:
    raise RuntimeError("OTX_API_KEY environment variable not set")

# ======================
# TIME WINDOW (LAST 24 HOURS)
# ======================
end_time = datetime.now(timezone.utc)
start_time = end_time - timedelta(Days=7)

params = {
    "since": start_time.isoformat(),
    "until": end_time.isoformat(),
    "types": "IPv4",
    "format": "json"
}

headers = {
    "X-OTX-API-KEY": OTX_API_KEY
}

# ======================
# API REQUEST
# ======================
response = requests.get(
    OTX_URL,
    headers=headers,
    params=params,
    timeout=30
)
response.raise_for_status()

data = response.json()

# ======================
# NORMALIZE RESPONSE
# ======================
if isinstance(data, dict) and "results" in data:
    indicators = data["results"]
elif isinstance(data, list):
    indicators = data
else:
    raise ValueError("Unexpected OTX response format")

# ======================
# EXTRACT + CLEAN IPv4s
# ======================
ipv4_set = sorted({
    item["indicator"]
    for item in indicators
    if item.get("type") == "IPv4"
    and item.get("indicator")
    and item.get("title") != "Expired"   # 👈 optional but recommended
})

# ======================
# WRITE HUNT-READY CSV
# ======================
os.makedirs("iocs", exist_ok=True)
csv_path = "iocs/otx_ipv4.csv"

with open(csv_path, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["IndicatorValue"])
    for ip in ipv4_set:
        writer.writerow([ip])

print(f"[+] Saved {len(ipv4_set)} IPv4 indicators → {csv_path}")
