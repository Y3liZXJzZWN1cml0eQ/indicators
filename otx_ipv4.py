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

CSV_PATH = "iocs/otx_ipv4.csv"

# ======================
# TIME WINDOW (LAST 24 HOURS)
# ======================
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

# ======================
# LOAD EXISTING IOCs
# ======================
existing_ips = set()

if os.path.exists(CSV_PATH):
    with open(CSV_PATH, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("IndicatorValue"):
                existing_ips.add(row["IndicatorValue"])

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
# EXTRACT NEW IPv4s
# ======================
new_ips = {
    item["indicator"]
    for item in indicators
    if item.get("type") == "IPv4"
    and item.get("indicator")
    and item.get("title") != "Expired"
}

# ======================
# MERGE + DEDUP
# ======================
merged_ips = sorted(existing_ips | new_ips)

# ======================
# WRITE CLEAN CSV
# ======================
os.makedirs("iocs", exist_ok=True)

with open(CSV_PATH, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["IndicatorValue"])
    for ip in merged_ips:
        writer.writerow([ip])

print(
    f"[+] Existing: {len(existing_ips)} | "
    f"New: {len(new_ips)} | "
    f"Total: {len(merged_ips)} → {CSV_PATH}"
)
