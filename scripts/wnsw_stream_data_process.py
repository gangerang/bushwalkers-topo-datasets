import subprocess
import xml.etree.ElementTree as ET
import geopandas as gpd
from shapely.geometry import Point
from datetime import datetime
from pathlib import Path
import sys

def download_xml(url):
    """Download XML data using curl"""
    try:
        # Construct curl command
        cmd = [
            'curl',
            '--fail',
            '--silent',
            '--show-error',
            '--location',
            '--retry', '3',
            '--retry-delay', '2',
            '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            url
        ]
        
        # Run curl command and capture output
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True
        )
        
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        print(f"Curl command failed with error: {e.stderr.decode()}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"Download failed with error: {str(e)}", file=sys.stderr)
        raise

# Function to format datetime
def format_datetime(raw_datetime):
    if raw_datetime:
        try:
            return datetime.strptime(raw_datetime, "%Y%m%d%H%M%S").isoformat() + "Z"
        except ValueError:
            return None
    return None

def main():
    # Output file path in the datasets folder
    output_file = "datasets/stream_height_data.gpkg"
    
    # Ensure output directory exists
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # URL of the XML data
    url = "https://realtimedata.waternsw.com.au/wgen/sites.rs.anon.xml"
    
    try:
        # Fetch the XML data using curl
        xml_data = download_xml(url)
        
        # Parse the XML data
        root = ET.fromstring(xml_data)
        
        # Prepare data storage
        data = []
        
        # Process each <site> element
        for site in root.findall(".//site"):
            site_data = {
                "site_station": site.get("station"),
                "grpvals": site.get("grpvals"),
                "grpvalsdesc": site.get("grpvalsdesc"),
                "latdec": float(site.get("latdec")) if site.get("latdec") else None,
                "lngdec": float(site.get("lngdec")) if site.get("lngdec") else None,
                "shortname": site.get("shortname"),
                "stname": site.get("stname"),
                "height": float(site.get("var_100x00_100")) if site.get("var_100x00_100") else None,
                "height_datetime": format_datetime(site.get("var_100x00_100_dt")),
                "colour": site.get("colour")
            }
            data.append(site_data)
        
        # Create GeoDataFrame
        geometry = [Point(d["lngdec"], d["latdec"]) if d["lngdec"] and d["latdec"] else None for d in data]
        gdf = gpd.GeoDataFrame(data, geometry=geometry, crs="EPSG:4326")
        
        # Save to GeoPackage
        gdf.to_file(output_file, layer="site_data", driver="GPKG")
        
        print(f"GeoPackage saved to {output_file}")
        
    except ET.ParseError as e:
        print(f"Failed to parse XML data: {e}", file=sys.stderr)
        raise
    except Exception as e:
        print(f"An error occurred: {e}", file=sys.stderr)
        raise

if __name__ == "__main__":
    main()