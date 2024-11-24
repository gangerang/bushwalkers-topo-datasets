import subprocess
import xml.etree.ElementTree as ET
import geopandas as gpd
from shapely.geometry import Point
from datetime import datetime
from pathlib import Path
import sys

def download_xml(url):
    """Download XML data using curl with enhanced headers"""
    try:
        # Construct curl command with expanded headers
        cmd = [
            'curl',
            '--fail',
            '--silent',
            '--show-error',
            '--location',
            '--retry', '3',
            '--retry-delay', '2',
            '-H', 'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36',
            '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            '-H', 'Accept-Language: en-US,en;q=0.9',
            '-H', 'Accept-Encoding: gzip, deflate, br',
            '-H', 'Connection: keep-alive',
            '-H', 'Upgrade-Insecure-Requests: 1',
            '-H', 'Sec-Fetch-Dest: document',
            '-H', 'Sec-Fetch-Mode: navigate',
            '-H', 'Sec-Fetch-Site: none',
            '-H', 'Sec-Fetch-User: ?1',
            '--compressed',  # Handle gzip encoding
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
        print(f"Curl command failed. Status code: {e.returncode}")
        print(f"Stderr: {e.stderr.decode()}")
        print(f"Stdout: {e.stdout.decode()}")
        # Print the exact curl command for debugging
        print("Curl command:", ' '.join(cmd))
        raise
    except Exception as e:
        print(f"Download failed with error: {str(e)}")
        raise

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
    url = "https://realtimedata.waternsw.com.au/wgen/sites.rs.anon.xml?1732452028107"
    
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
        print(f"Failed to parse XML data: {e}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()