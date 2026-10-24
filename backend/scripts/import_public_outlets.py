"""Download and normalize the public outlet mapping into the GIS station schema.

This is a discovery layer, NOT a verified Gujarat Gas station register. Rows keep
source flags and provenance so the UI can label them as provisional.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import io
import json
import os
import urllib.request
from pathlib import Path

SOURCE_URL = (
    "https://raw.githubusercontent.com/herrrickshaw/"
    "cng-cgd-retail-outlet-mapping/main/data/outlets_cgd.csv.gz"
)
DEFAULT_OUT = Path("data/processed/stations.csv")
USER_AGENT = "CNG-Network-Intelligence-hackathon/1.0"


def get_rows(url: str):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read()
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as zipped:
        text = io.TextIOWrapper(zipped, encoding="utf-8-sig", newline="")
        yield from csv.DictReader(text)


def first(row, *names):
    lower = {str(k).strip().lower(): v for k, v in row.items()}
    for name in names:
        value = lower.get(name.lower())
        if value not in (None, ""):
            return str(value).strip()
    return ""


def normalize(rows, state_filter="Gujarat"):
    seen = set()
    for index, row in enumerate(rows, start=1):
        state = first(row, "state", "state_name")
        if state_filter and state.casefold() not in {state_filter.casefold(), "gujarat"}:
            continue
        lat_text = first(row, "latitude", "lat")
        lon_text = first(row, "longitude", "lon", "lng")
        try:
            lat, lon = float(lat_text), float(lon_text)
        except (TypeError, ValueError):
            continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            continue
        outlet_id = first(row, "outlet_id", "id", "pump_id") or f"public-outlet-{index}"
        # Preserve identity and deduplicate exact outlet coordinates.
        dedup_key = (outlet_id, round(lat, 6), round(lon, 6))
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        has_cng = first(row, "has_cng", "cng", "is_cng")
        yield {
            "station_id": "public-outlet-" + outlet_id,
            "station_name": first(row, "name", "outlet_name", "pump_name") or "Unnamed public outlet",
            "latitude": lat,
            "longitude": lon,
            "district": first(row, "district"),
            "state": state or state_filter,
            "source": "herrrickshaw/cng-cgd-retail-outlet-mapping",
            "source_url": SOURCE_URL,
            "source_outlet_id": outlet_id,
            "has_cng": has_cng,
            "source_status": first(row, "status"),
            "operator": first(row, "omc", "company", "operator"),
            "authorized_cgd_entity": first(row, "authorized_cgd_entity", "cgd_entity", "entity"),
            "data_confidence": "provisional_public_outlet_mapping",
            "verified_gujarat_gas_station": "false",
        }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--source-url", default=SOURCE_URL)
    parser.add_argument("--state", default="Gujarat")
    args = parser.parse_args()

    destination = Path(args.out)
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = list(normalize(get_rows(args.source_url), args.state))
    fields = [
        "station_id", "station_name", "latitude", "longitude", "district", "state",
        "source", "source_url", "source_outlet_id", "has_cng", "source_status",
        "operator", "authorized_cgd_entity", "data_confidence",
        "verified_gujarat_gas_station",
    ]
    with destination.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({
        "output": str(destination),
        "rows_written": len(rows),
        "state_filter": args.state,
        "warning": "Public outlet candidates only; not verified Gujarat Gas operating stations.",
        "source_url": args.source_url,
    }, indent=2))


if __name__ == "__main__":
    main()
