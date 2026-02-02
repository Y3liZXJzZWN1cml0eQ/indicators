import os
import csv
import requests
import ipaddress
from datetime import datetime, timedelta, timezone
from typing import Set, Optional

OTX_API_KEY = os.getenv("OTX_API_KEY")
OTX_URL = "https://otx.alienvault.com/api/v1/indicators/export"
CSV_PATH = "iocs/otx_ipv4.csv"

# How far back to fetch indicators (hours). Override via env var if you want.
LOOKBACK_HOURS = int(os.getenv("OTX_LOOKBACK_HOURS", "24"))

if not OTX_API_KEY:
    raise RuntimeError("OTX_API_KEY environment variable not set")


def is_valid_ipv4(value: str) -> bool:
    try:
        ipaddress.IPv4Address(value)
        return True
    except ValueError:
        return False


def iso_utc(dt: datetime) -> str:
    # OTX expects ISO datetime; using Zulu keeps it consistent
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_otx_ipv4() -> Set[str]:
    """
    Fetch IPv4 indicators from OTX export endpoint.
    Parses JSON results and follows pagination via 'next' when present.
    """
    headers = {"X-OTX-API-KEY": OTX_API_KEY}

    modified_since = iso_utc(datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS))
    params = {
        "types": "IPv4",
        "modified_since": modified_since,
    }

    valid_ips: Set[str] = set()

    next_url: Optional[str] = OTX_URL
    next_params: Optional[dict] = params  # only send params on first request

    while next_url:
        r = requests.get(next_url, headers=headers, params=next_params, timeout=60)
        r.raise_for_status()

        # Endpoint returns JSON body (with 'results' and optionally 'next')
        payload = r.json()

        results = payload.get("results", []) if isinstance(payload, dict) else []
        for item in results:
            # OTX commonly uses fields: 'indicator' and 'type'
            if not isinstance(item, dict):
                continue
            if item.get("type") != "IPv4":
                continue

            ip = (item.get("indicator") or "").strip()
            if is_valid_ipv4(ip):
                valid_ips.add(ip)

        # Pagination: 'next' may be null/empty or a URL
        next_url = payload.get("next") if isinstance(payload, dict) else None
        next_params = None  # next already contains query string if provided by API

    return valid_ips


def load_existing(csv_path: str) -> Set[str]:
    existing: Set[str] = set()
    if os.path.exists(csv_path):
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                val = (row.get("IndicatorValue") or "").strip()
                if is_valid_ipv4(val):
                    existing.add(val)
    return existing


def write_csv(csv_path: str, indicators: Set[str]) -> None:
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["IndicatorValue"])
        for ip in sorted(indicators):
            writer.writerow([ip])


def main() -> None:
    existing = load_existing(CSV_PATH)
    fetched = fetch_otx_ipv4()
    merged = existing | fetched

    write_csv(CSV_PATH, merged)

    print(
        f"[+] Existing: {len(existing)} | "
        f"Fetched(valid): {len(fetched)} | "
        f"Total: {len(merged)} | "
        f"LookbackHours: {LOOKBACK_HOURS}"
    )


if __name__ == "__main__":
    main()
