import requests
import os
import json

# Constants
NAMING_URL = "https://dcok8xuap4.execute-api.ap-southeast-2.amazonaws.com/prod/public/placenames/advertised-proposals"
GEONAME_URL_TEMPLATE = "https://dcok8xuap4.execute-api.ap-southeast-2.amazonaws.com/prod/public/placenames/geonames/{}"

# Output configuration
output_dir = os.environ.get("OUTPUT_DIR", "datasets")
os.makedirs(output_dir, exist_ok=True)
OUTPUT_FILE = os.path.join(output_dir, "naming_proposals.geojson")

def fetch_json(url):
    """Fetch JSON data from a URL."""
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def process_naming_records():
    """Fetch naming records and process them into a GeoJSON file."""
    print("Fetching naming proposals...")
    data = fetch_json(NAMING_URL)
    naming_records = data.get("naming", {}).get("current", [])

    features = []
    for record in naming_records:
        geoname_id = record.get("geoname_identifier")
        if not geoname_id:
            continue

        # Fetch geoname details with graceful error handling
        geoname_url = GEONAME_URL_TEMPLATE.format(geoname_id)
        try:
            geoname_data = fetch_json(geoname_url)
        except Exception as e:
            print(f"Skipping record {geoname_id} due to error fetching geoname data: {e}")
            continue

        # Extract required fields
        try:
            longitude = float(geoname_data.get("longitude", 0))
            latitude = float(geoname_data.get("latitude", 0))
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [longitude, latitude]
                },
                "properties": {
                    "advertisement_identifier": record.get("advertisement_identifier"),
                    "geoname_identifier": geoname_id,
                    "advertisement_url": f"https://proposals.gnb.nsw.gov.au/currentproposals/{record.get('advertisement_identifier')}",
                    "geoname_url": f"https://proposals.gnb.nsw.gov.au/public/geonames/{geoname_id}",
                    "geographical_name": geoname_data.get("geographical_name"),
                    "date_start": record.get("date_start"),
                    "date_end": record.get("date_end"),
                    "designation": record.get("designation")
                }
            }

            features.append(feature)
        except Exception as e:
            print(f"Error processing record {geoname_id}: {e}")

    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    # Save to file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(geojson, f, indent=4)

    print(f"GeoJSON file created: {OUTPUT_FILE}")

if __name__ == "__main__":
    process_naming_records()
