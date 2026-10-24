"""Geocode the project's 344-record Gujarat Gas directory.

Preferred provider: Google Maps Geocoding API through Google's official Python
client library (googlemaps). If GOOGLE_MAPS_API_KEY is absent, explicitly fall
back to OpenStreetMap Nominatim with its public-service rate limit.
All geocoding results are candidates that require review before decisions.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
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
        "geocode_provider": "openstreetmap_nominatim",
    }


def query_google(query: str, api_key: str):
    import googlemaps

    client = googlemaps.Client(key=api_key, timeout=10, retry_timeout=15)
    result = client.geocode(query, region="in")
    if not result:
        return None
    # Geocoding may match an area/address instead of the station itself. Keep
    # Google's result type and formatted address so an operator can review it.
    hit = result[0]
    location = hit.get("geometry", {}).get("location", {})
    if "lat" not in location or "lng" not in location:
        return None
    return {
        "latitude": location["lat"],
        "longitude": location["lng"],
        "geocode_display_name": hit.get("formatted_address", ""),
        "geocode_type": "|".join(hit.get("types", [])),
        "geocode_class": "",
        "geocode_provider": "google_maps_geocoding",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--limit", type=int, default=344, help="Maximum rows to process")
    parser.add_argument("--provider", choices=("auto", "google", "nominatim"), default="auto")
    parser.add_argument("--delay", type=float, default=1.1, help="Delay between Nominatim requests")
    args = parser.parse_args()

    source = Path(args.input)
    destination = Path(args.output)
    if not source.exists():
        raise SystemExit(f"Input CSV not found: {source}")

    api_key = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
    provider = args.provider
    if provider == "auto":
        provider = "google" if api_key else "nominatim"
    if provider == "google" and not api_key:
        raise SystemExit("GOOGLE_MAPS_API_KEY is required for --provider google.")
    if provider == "google":
        try:
            import googlemaps  # noqa: F401
        except ImportError as exc:
            raise SystemExit("Install backend dependencies first; googlemaps is required.") from exc

    with source.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        original_fields = list(reader.fieldnames or [])
        rows = list(reader)[:max(0, args.limit)]
    if not original_fields:
        raise SystemExit("Input CSV has no header row")

    extra_fields = [
        "latitude", "longitude", "geocode_display_name", "geocode_type",
        "geocode_class", "geocode_provider", "coordinate_precision", "geocode_status"
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
            "geocode_display_name": get(row, "geocode_display_name"),
            "geocode_type": get(row, "geocode_type"),
            "geocode_class": get(row, "geocode_class"),
            "geocode_provider": get(row, "geocode_provider"),
            "coordinate_precision": "existing_source_coordinates" if existing else "",
            "geocode_status": "existing_coordinates" if existing else "pending",
        })
        if not existing and name:
            try:
                hit = query_google(query, api_key) if provider == "google" else query_nominatim(query)
                if hit:
                    row.update(hit)
                    row["coordinate_precision"] = "provider_geocode_candidate"
                    row["geocode_status"] = "needs_manual_review"
                else:
                    row["geocode_status"] = "not_found"
            except Exception as exc:
                row["geocode_status"] = "geocoder_error:" + type(exc).__name__
            if provider == "nominatim":
                time.sleep(max(1.0, args.delay))
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
        "provider": provider, "status_counts": counts,
        "note": "Geocoded coordinates are candidate matches. Manually review each match before spatial decisions."
    }, indent=2))


if __name__ == "__main__":
    main()
