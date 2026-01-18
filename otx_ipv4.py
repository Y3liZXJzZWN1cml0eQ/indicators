import os
import csv
import requests
import ipaddress

OTX_API_KEY = os.getenv("OTX_API_KEY")
OTX_URL = "https://otx.alienvault.com/api/v1/indicators/export"
CSV_PATH = "iocs/otx_ipv4.csv"

if not OTX_API_KEY:
    raise RuntimeError("OTX_API_KEY environment variable not set")

def is_valid_ipv4(value: str) -> bool:
    try:
        ipaddress.IPv4Address(value)
        return True
    except ValueError:
        return False

def fetch_otx_ipv4():
    headers = {"X-OTX-API-KEY": OTX_API_KEY}
    params = {"types": "IPv4"}

    r = requests.get(OTX_URL, headers=headers, params=params, timeout=60)
    r.raise_for_status()

    valid_ips = set()

    for line in r.text.splitlines():
        line = line.strip()
        if is_valid_ipv4(line):
            valid_ips.add(line)

    return valid_ips

def load_existing(csv_path):
    existing = set()
    if os.path.exists(csv_path):
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if is_valid_ipv4(row.get("IndicatorValue", "")):
                    existing.add(row["IndicatorValue"])
    return existing

def write_csv(csv_path, indicators):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["IndicatorValue"])
        for ip in sorted(indicators):
            writer.writerow([ip])

def main():
    existing = load_existing(CSV_PATH)
    fetched = fetch_otx_ipv4()
    merged = existing | fetched

    write_csv(CSV_PATH, merged)

    print(
        f"[+] Existing: {len(existing)} | "
        f"Fetched(valid): {len(fetched)} | "
        f"Total: {len(merged)}"
    )

if __name__ == "__main__":
    main()
