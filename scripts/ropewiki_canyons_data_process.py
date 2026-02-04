#!/usr/bin/env python3
import requests
import json
import os

# Output configuration
output_dir = os.environ.get("OUTPUT_DIR", "datasets")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "canyons.geojson")

ROPEWIKI_URL = "https://ropewiki.com/api.php"
QUERY = "[[Category:Canyons]][[Has coordinates::+]][[Located in region.Located in regions::X||Australia]]|?Has_coordinates|?Has_summary|?Has_info_regions|?Has_info_major_region|?Has_info_rappels|?Has_longest_rappel|?Has_pageid|limit=1000|order=ascending|sort=Has name"


def fetch_canyons():
    """Fetch canyon data from Ropewiki API."""
    params = {
        "action": "ask",
        "format": "json",
        "query": QUERY
    }
    response = requests.get(ROPEWIKI_URL, params=params)
    response.raise_for_status()
    return response.json()


def process_canyons(data):
    """Convert Ropewiki response to GeoJSON features."""
    features = []
    results = data.get("query", {}).get("results", {})

    for canyon_name, canyon_data in results.items():
        try:
            coords = canyon_data.get("printouts", {}).get("Has coordinates", [])
            if not coords:
                continue

            lat = coords[0].get("lat")
            lon = coords[0].get("lon")
            if lat is None or lon is None:
                continue

            printouts = canyon_data.get("printouts", {})

            # Extract longest rappel and convert to meters
            longest_rappel_raw = printouts.get("Has longest rappel", [None])[0] if printouts.get("Has longest rappel") else None
            longest_rappel_m = None
            if longest_rappel_raw and isinstance(longest_rappel_raw, dict):
                value = longest_rappel_raw.get("value")
                if value is not None:
                    # Convert feet to meters (1 ft = 0.3048 m)
                    longest_rappel_m = round(value * 0.3048, 1)

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "name": canyon_data.get("fulltext"),
                    "url": canyon_data.get("fullurl"),
                    "summary": printouts.get("Has summary", [""])[0] if printouts.get("Has summary") else None,
                    "regions": printouts.get("Has info regions", []),
                    "major_region": printouts.get("Has info major region", [""])[0] if printouts.get("Has info major region") else None,
                    "rappels": printouts.get("Has info rappels", [None])[0] if printouts.get("Has info rappels") else None,
                    "longest_rappel": longest_rappel_raw,
                    "longest_rappel_m": longest_rappel_m,
                    "pageid": printouts.get("Has pageid", [None])[0] if printouts.get("Has pageid") else None
                }
            }
            features.append(feature)
        except Exception as e:
            print(f"Error processing canyon {canyon_name}: {e}")
            continue

    return features


def main():
    print("Fetching canyons from Ropewiki...")
    data = fetch_canyons()

    features = process_canyons(data)
    print(f"Processed {len(features)} canyons")

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2)

    print(f"GeoJSON file created: {output_path}")


if __name__ == "__main__":
    main()
