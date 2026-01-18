import os
import requests
from pathlib import Path

API_KEY = os.environ.get("ABUSEIPDB_API_KEY")
OUTPUT_FILE = Path("data/ips.txt")

URL = "https://api.abuseipdb.com/api/v2/blacklist"
PARAMS = {
    "confidenceMinimum": 75,  # adjust as needed
    "limit": 10000
}
HEADERS = {
    "Key": API_KEY,
    "Accept": "text/plain"
}

def fetch_ips():
    r = requests.get(URL, headers=HEADERS, params=PARAMS, timeout=60)
    r.raise_for_status()
    return set(r.text.splitlines())

def load_existing_ips():
    if not OUTPUT_FILE.exists():
        return set()
    return set(OUTPUT_FILE.read_text().splitlines())

def save_ips(ips):
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text("\n".join(sorted(ips)) + "\n")

def main():
    new_ips = fetch_ips()
    existing_ips = load_existing_ips()
    merged = existing_ips | new_ips
    save_ips(merged)
    print(f"Existing: {len(existing_ips)} | New fetched: {len(new_ips)} | Total: {len(merged)}")

if __name__ == "__main__":
    main()
