import os
import csv
import requests

# ======================
# CONFIG
# ======================
OTX_API_KEY = os.getenv("OTX_API_KEY")
OTX_URL = "https://otx.alienvault.com/api/v1/indicators/export"
CSV_PATH = "iocs/otx_ipv4.csv"

if not OTX_API_KEY:
    raise RuntimeError("OTX_API_KEY environment variable not set")

# ======================
# FETCH ALL IPv4 IOCs
# ======================
def fetch_otx_ipv4():
    headers = {
        "X-OTX-API-KEY": OTX_API_KEY
    }
    params = {
        "types": "IPv4"
    }

    r = requests.get(
        OTX_URL,
        headers=headers,
        params=params,
        timeout=60
    )
    r.raise_for_status()

    # Each line = one indicator
    return {
        line.strip()
        for line in r.text.splitlines()
        if line.strip()
    }

# ======================
# LOAD EXISTING IOCs
# ======================
def load_existing(csv_path):
    existing = set()
    if os.path.exists(csv_path):
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                existing.add(row["IndicatorValue"])
    return existing

# ======================
# WRITE MERGED CSV
# ======================
def write_csv(csv_path, indicators):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["IndicatorValue"])
        for ip in sorted(indicators):
            writer.writerow([ip])

# ======================
# MAIN
# ======================
def main():
    existing_ips = load_existing(CSV_PATH)
    new_ips = fetch_otx_ipv4()

    merged = existing_ips | new_ips

    write_csv(CSV_PATH, merged)

    print(
        f"[+] Existing: {len(existing_ips)} | "
        f"Fetched: {len(new_ips)} | "
        f"Total: {len(merged)}"
    )

if __name__ == "__main__":
    main()
