import os
import csv
import requests
import ipaddress
from datetime import datetime, timedelta, timezone
from typing import Set, Optional

OTX_API_KEY = os.getenv("OTX_API_KEY")
OTX_URL = "https://otx.alienvault.com/api/v1/indicators/export"
CSV_PATH = "iocs/otx_ipv4.csv"

# Good default for first run; reduce later to 6-24 for incremental
LOOKBACK_HOURS = int(os.getenv("OTX_LOOKBACK_HOURS", "168"))  # 7 days

if not OTX_API_KEY:
    raise RuntimeError("OTX_API_KEY environment variable not set")


def is_valid_ipv4(value: str) -> bool:
    try:
        ipaddress.IPv4Address(value)
        return True
    except ValueError:
        return False


def iso_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def fetch_otx_ipv4() -> Set[str]:
    headers = {"X-OTX-API-KEY": OTX_API_KEY}
    modified_since = iso_utc(datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS))

    params = {"types": "IPv4", "modified_since": modified_since}

    valid_ips: Set[str] = set()
    next_url: Optional[str] = OTX_URL
    next_params: Optional[dict] = params  # only for first request

    while next_url:
        r = requests.get(next_url, headers=headers, params=next_params, timeout=60)
        r.raise_for_status()
        payload = r.json()

        results = payload.get("results", []) if isinstance(payload, dict) else []
        for item in results:
            if not isinstance(item, dict):
                continue

            # Common field names in OTX exports
            itype = (item.get("type") or "").strip()
            if itype != "IPv4":
                continue

            val = (item.get("indicator") or item.get("Indicator") or item.get("value") or "").strip()
            if is_valid_ipv4(val):
                valid_ips.add(val)

        next_url = payload.get("next") if isinstance(payload, dict) else None
        next_params = None  # 'next' typically includes query args already

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
