#!/usr/bin/env python3
import requests
import json
import os

# create geojson file of hr burns from rfs api
# pubic web version https://www.rfs.nsw.gov.au/fire-information/hazard-reductions
# api is json response but not geojson so this script converts it to geojson

local_directory = "datasets"
os.makedirs(local_directory, exist_ok=True)  # Ensure the local directory exists
output_filename = "rfs_hr_burns.geojson"
output_path = os.path.join(local_directory, output_filename)

def parse_polygon(polygon_str):
    """
    Convert a polygon string of the format:
      "lat;lon|lat;lon|lat;lon|…"
    into a list of [lon, lat] coordinates.
    """
    coords = []
    for point in polygon_str.split("|"):
        if point.strip():
            try:
                lat, lon = point.split(";")
                coords.append([float(lon), float(lat)])
            except ValueError:
                continue  # skip if the point can't be parsed
    return coords

def main():
    # Define the API endpoint and query parameters; you can update these as needed.
    url = "https://www.rfs.nsw.gov.au/funnelback/hr-map-data"
    params = {
        # "form": "custom",
        # "profile": "_default_preview",
        # "num_ranks": "10000",
        # "collection": "nsw-rfs-hazard-xml-new",
        # "maxdist": "298.33570444097364",
        # "origin": "-33.80274510369129,150.51471689357462"
    }
    
    # Query the API
    print("Querying the API...")
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"Error: API request failed with status {response.status_code}")
        return
    
    data = response.json()
    
    features = []
    for result in data.get("results", []):
        multi_polygon_coords = []
        # Process each polygon in the result.
        for poly in result.get("polygons", []):
            polygon_str = poly.get("polygon")
            if polygon_str:
                coords = parse_polygon(polygon_str)
                # Ensure the linear ring is closed (first point equals the last)
                if coords and coords[0] != coords[-1]:
                    coords.append(coords[0])
                # For GeoJSON MultiPolygon, each polygon must be an array of linear rings.
                multi_polygon_coords.append([coords])
        
        # Build the geometry using the geometryType (default to "MultiPolygon")
        geometry = {
            "type": result.get("geometryType", "MultiPolygon"),
            "coordinates": multi_polygon_coords
        }
        
        # Build a properties dictionary from the result
        properties = {
            "leadAgency": result.get("leadAgency"),
            "lga": result.get("lga"),
            "supportingAgencies": result.get("supportingAgencies"),
            "size": result.get("size"),
            "location": result.get("location"),
            "guarReference": result.get("guarReference"),
            "tenure": result.get("tenure"),
            "startDate": result.get("startDate"),
            "endDate": result.get("endDate")
        }
        
        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": properties
        }
        features.append(feature)
    
    # Assemble the FeatureCollection for GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # Write the GeoJSON to a file
    with open(output_path, "w") as f:
        json.dump(geojson, f, indent=2)
    print(f"GeoJSON file '{output_path}' created successfully.")

if __name__ == "__main__":
    main()
