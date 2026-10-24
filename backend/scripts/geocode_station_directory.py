"""Geocode the local 344-record Gujarat Gas directory using OpenStreetMap Nominatim.

This is an approximate matching helper, not an official Google Maps geocoder.
It preserves the input rows, adds coordinates only when Nominatim returns a
candidate, and labels each match with its confidence/precision. Review matches
before using them for coverage or expansion decisions.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_INPUT = Path("member-3-forecasting/data/gujarat_gas_directory_344_records.csv")
DEFAULT_OUTPUT = Path("member-3-forecasting/data/gujarat_gas_directory_344_geocoded.csv")
USER_AGENT = "CNG-Network-Intelligence-SFIC2026/1.0 (student prototype)"


def get(row, *names):
    lowered = {str(k).strip().lower(): v for k, v in row.items()}
    for name in names:
        value = lowered.get(name.lower())
        if value is not None and str(value).strip():
            return str(value).strip()
    return ""


def query_nominatim(query: str):
    url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode({
        "q": query, "format": "jsonv2", "limit": 1, "countrycodes": "in"
    })
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as response:
        data = json.loads(response.read().decode("utf-8"))
    if not data:
        return None
    hit = data[0]
    return {
        "latitude": hit.get("lat", ""),
        "longitude": hit.get("lon", ""),
        "geocode_display_name": hit.get("display_name", ""),
        "geocode_type": hit.get("type", ""),
        "geocode_class": hit.get("class", ""),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--limit", type=int, default=344, help="Maximum rows to process")
    args = parser.parse_args()

    source = Path(args.input)
    destination = Path(args.output)
    if not source.exists():
        raise SystemExit(f"Input CSV not found: {source}")

    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        original_fields = list(reader.fieldnames or [])
        rows = list(reader)[:args.limit]
    if not original_fields:
        raise SystemExit("Input CSV has no header row")

    extra_fields = [
        "latitude", "longitude", "geocode_display_name", "geocode_type",
        "geocode_class", "coordinate_precision", "geocode_status"
    ]
    output_rows = []
    for index, row in enumerate(rows, start=1):
        lat = get(row, "latitude", "lat", "Latitude")
        lon = get(row, "longitude", "lon", "lng", "Longitude")
        existing = bool(lat and lon)
        name = get(row, "station_name", "name", "outlet_name", "station", "pump_name")
        address = get(row, "address", "full_address", "location", "street_address")
        city = get(row, "city", "district", "town") or "Gujarat"
        query = ", ".join(part for part in [name, address, city, "Gujarat", "India"] if part)
        row.update({
            "latitude": lat,
            "longitude": lon,
            "geocode_display_name": "",
            "geocode_type": "",
            "geocode_class": "",
            "coordinate_precision": "existing_source_coordinates" if existing else "",
            "geocode_status": "existing_coordinates" if existing else "pending",
        })
        if not existing and name:
            try:
                hit = query_nominatim(query)
                if hit:
                    row.update(hit)
                    row["coordinate_precision"] = "approximate_geocoded_match"
                    row["geocode_status"] = "needs_manual_review"
                else:
                    row["geocode_status"] = "not_found"
            except Exception as exc:
                row["geocode_status"] = "geocoder_error:" + type(exc).__name__
            # Nominatim public service policy requires at most one request/second.
            time.sleep(1.1)
        elif not name and not existing:
            row["geocode_status"] = "missing_station_name"
        output_rows.append(row)
        if index % 25 == 0:
            print(f"Processed {index}/{len(rows)} rows")

    destination.parent.mkdir(parents=True, exist_ok=True)
    fields = original_fields + [field for field in extra_fields if field not in original_fields]
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(output_rows)
    counts = {}
    for row in output_rows:
        key = row["geocode_status"]
        counts[key] = counts.get(key, 0) + 1
    print(json.dumps({
        "input": str(source), "output": str(destination), "rows_processed": len(rows),
        "status_counts": counts,
        "note": "Geocoded coordinates are approximate candidate matches; manually review before spatial decisions."
    }, indent=2))


if __name__ == "__main__":
    main()
