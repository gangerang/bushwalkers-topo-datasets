#!/usr/bin/env python3
import requests
import json
import os
import sys
import time

# Output configuration
output_dir = os.environ.get("OUTPUT_DIR", "datasets")
os.makedirs(output_dir, exist_ok=True)
output_path = os.path.join(output_dir, "canyons.geojson")

ROPEWIKI_URL = os.environ.get("ROPEWIKI_API_URL", "https://ropewiki.com/api.php")
QUERY = "[[Category:Canyons]][[Has coordinates::+]][[Located in region.Located in regions::X||Australia]]|?Has_coordinates|?Has_summary|?Has_info_regions|?Has_info_major_region|?Has_info_rappels|?Has_longest_rappel|?Has_pageid|limit=1000|order=ascending|sort=Has name"

# Ropewiki is a MediaWiki site; identify the bot as wiki etiquette requires.
USER_AGENT = os.environ.get(
    "ROPEWIKI_USER_AGENT",
    "bushwalkers-topo-datasets/1.0 (+https://github.com/gangerang/bushwalkers-topo-datasets)",
)

REQUEST_TIMEOUT = 60
MAX_ATTEMPTS = 4

# Refuse to publish a result that lost more than this fraction of the previous
# run's canyons - an upstream hiccup should not silently wipe the dataset.
MIN_RETAINED_FRACTION = 0.8


class UpstreamBlocked(Exception):
    """Ropewiki refused the request outright (e.g. a bot challenge)."""


def is_bot_challenge(response):
    """Detect a Cloudflare challenge/block served in place of the API response."""
    if response.headers.get("cf-mitigated"):
        return True
    if response.status_code not in (403, 503):
        return False
    body = response.text[:2000].lower()
    return "just a moment" in body or "cf-chl" in body or "challenges.cloudflare.com" in body


def fetch_canyons():
    """Fetch canyon data from Ropewiki API."""
    params = {
        "action": "ask",
        "format": "json",
        "query": QUERY
    }
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            response = requests.get(
                ROPEWIKI_URL, params=params, headers=headers, timeout=REQUEST_TIMEOUT
            )
            if is_bot_challenge(response):
                raise UpstreamBlocked(
                    f"Ropewiki returned a bot challenge (HTTP {response.status_code}, "
                    f"cf-mitigated={response.headers.get('cf-mitigated')!r}) instead of API data."
                )
            response.raise_for_status()
            return response.json()
        except UpstreamBlocked:
            raise
        except (requests.RequestException, ValueError) as e:
            last_error = e
            if attempt == MAX_ATTEMPTS:
                break
            delay = 2 ** attempt
            print(f"Attempt {attempt} failed ({e}); retrying in {delay}s...", file=sys.stderr)
            time.sleep(delay)

    raise RuntimeError(f"Failed to fetch Ropewiki data after {MAX_ATTEMPTS} attempts: {last_error}")


def existing_feature_count():
    """Number of features in the currently published dataset, if any."""
    try:
        with open(output_path, encoding="utf-8") as f:
            return len(json.load(f).get("features", []))
    except (OSError, ValueError):
        return 0


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
    try:
        data = fetch_canyons()
    except UpstreamBlocked as e:
        print(f"ERROR: {e}", file=sys.stderr)
        print(
            "Ropewiki now sits behind a Cloudflare bot challenge that plain HTTP clients "
            "(including GitHub Actions runners) cannot pass. No request header change fixes "
            "this - access has to be granted by the Ropewiki operators. The previously "
            "published dataset has been left untouched.",
            file=sys.stderr,
        )
        sys.exit(1)

    previous_count = existing_feature_count()
    features = process_canyons(data)
    print(f"Processed {len(features)} canyons")

    if not features:
        print("ERROR: Ropewiki returned no canyons; refusing to overwrite existing data.", file=sys.stderr)
        sys.exit(1)

    if previous_count and len(features) < previous_count * MIN_RETAINED_FRACTION:
        drop = (
            f"canyon count dropped from {previous_count} to {len(features)} "
            f"(below {MIN_RETAINED_FRACTION:.0%} of the previous run)"
        )
        if os.environ.get("ALLOW_SHRINK") == "1":
            print(f"WARNING: {drop}; writing anyway because ALLOW_SHRINK=1.", file=sys.stderr)
        else:
            print(
                f"ERROR: {drop}; refusing to overwrite existing data. "
                "Set ALLOW_SHRINK=1 if this drop is genuine.",
                file=sys.stderr,
            )
            sys.exit(1)

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=2)

    print(f"GeoJSON file created: {output_path}")


if __name__ == "__main__":
    main()
