import pandas as pd
import geopandas as gpd
import requests
import re
import hashlib
import os

# Define constants
SOURCE_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ8EJKOwIGPMQlyBKPjeetZXSdH5vnxNvWJIAzftzclQ6m2UMjk_D42gE--WxvtsPRdMvDGbXtIqpNx/pub?gid=0&single=true&output=tsv"

LOCAL_DIRECTORY = 'datasets'

OUTPUT_ACTIVE_FILE = os.path.join(LOCAL_DIRECTORY, "crown_road_sales_active.geojson")
OUTPUT_INACTIVE_FILE = os.path.join(LOCAL_DIRECTORY, "crown_road_sales_inactive.geojson")
LOCAL_FILE = os.path.join(LOCAL_DIRECTORY, "crown_road_sales_new.tsv")
BACKUP_FILE = os.path.join(LOCAL_DIRECTORY, "crown_road_sales.tsv")


def hash_file(file_path):
    """Compute the hash of a file's contents."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as file:
        while chunk := file.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()


def download_tsv(url, output_path):
    """Download the TSV file from the given URL."""
    response = requests.get(url)
    response.raise_for_status()  # Raise an error for bad responses
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(response.text)


def is_file_updated(new_file, backup_file):
    """Check if the newly downloaded file is different from the backup."""
    if not os.path.exists(backup_file):
        return True  # No backup file means new processing is required
    return hash_file(new_file) != hash_file(backup_file)


def process_tsv_to_geojson(input_file):
    """Process the TSV file into active and inactive GeoJSON files."""
    # Read TSV into a DataFrame
    df = pd.read_csv(input_file, sep="\t")

    # Clean column names: lowercase, replace spaces with underscores, and fix typos
    def clean_column_names(columns):
        corrected_columns = []
        for col in columns:
            col = col.strip().lower().replace(" ", "_")  # Lowercase and replace spaces with underscores
            # Fix specific column name issues
            if col == "longtitude":
                col = "longitude"
            elif col == "latitiude":
                col = "latitude"
            corrected_columns.append(col)
        return corrected_columns

    # Apply the function to clean the column names
    df.columns = clean_column_names(df.columns)

    # Drop specified fields
    fields_to_drop = ["date", "comments"]
    df = df.drop(columns=fields_to_drop, errors="ignore")

    # Function to extract cluster, file_ref, and contact_email
    def extract_fields_from_html(html):
        if pd.isna(html):
            return None, None, None

        # Find the text in brackets containing "file"
        bracket_match = re.search(r"\(([^)]*file[^)]*)\)", html, re.IGNORECASE)
        bracket_text = bracket_match.group(1) if bracket_match else ""

        # Extract file_ref
        file_ref_match = re.search(r"\b\d+/\d+\b", bracket_text)  # Format: "1234/5678"
        file_ref = file_ref_match.group(0) if file_ref_match else None

        # Extract cluster
        cluster_match = re.search(r"(?:cluster|cluster_no|cluster_number)[^\d]*(\d+)", bracket_text, re.IGNORECASE)
        cluster = cluster_match.group(1) if cluster_match else None

        # Extract email address
        email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", html)
        email = email_match.group(0) if email_match else None

        return cluster, file_ref, email

    # Apply extraction function to the 'html' column
    df[["cluster", "file_ref", "contact_email"]] = df["html"].apply(
        lambda html: pd.Series(extract_fields_from_html(html))
    )

    # Function to extract the first list from the HTML and return it as plain text
    def extract_description_from_html(html):
        if pd.isna(html):
            return None

        # Find the first <ul>...</ul> block
        list_match = re.search(r"<ul>(.*?)</ul>", html, re.DOTALL | re.IGNORECASE)
        if not list_match:
            return None  # Return None if no list is found

        # Extract all list items (<li>...</li>) within the block
        list_content = list_match.group(1)
        items = re.findall(r"<li.*?>(.*?)</li>", list_content, re.DOTALL | re.IGNORECASE)

        # Clean up each list item to remove HTML tags and trailing "&nbsp;"
        clean_items = [re.sub(r"<.*?>", "", item).replace("&nbsp;", "").strip() for item in items]

        # Join the items with semicolons
        return "; ".join(clean_items)

    # Apply the function to the 'html' column
    df["description"] = df["html"].apply(extract_description_from_html)

    # Convert to GeoDataFrame
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["longitude"], df["latitude"]),
        crs="EPSG:4326"
    )

    # Add an 'active' column based on the 'expiry_date' column
    if "expiry_date" in df.columns:
        gdf["active"] = pd.to_datetime(gdf["expiry_date"], errors="coerce") > pd.Timestamp.now()
    else:
        raise ValueError("The TSV file must contain an 'expiry_date' column.")

    # Split into active and inactive sales
    active_gdf = gdf[gdf["active"]]
    inactive_gdf = gdf[~gdf["active"]]

    # Save to GeoJSON files
    active_gdf.to_file(OUTPUT_ACTIVE_FILE, driver="GeoJSON")
    inactive_gdf.to_file(OUTPUT_INACTIVE_FILE, driver="GeoJSON")
    print(f"GeoJSON files created: {OUTPUT_ACTIVE_FILE}, {OUTPUT_INACTIVE_FILE}")


# Main script
if __name__ == "__main__":
    # Step 1: Download the file
    print("Downloading TSV file...")
    download_tsv(SOURCE_URL, LOCAL_FILE)

    # Step 2: Check if the file has been updated
    if is_file_updated(LOCAL_FILE, BACKUP_FILE):
        print("File has been updated. Processing...")

        # Process the file
        process_tsv_to_geojson(LOCAL_FILE)

        # Step 3: Save a copy of the new file as backup
        os.replace(LOCAL_FILE, BACKUP_FILE)
    else:
        print("File has not been updated. No further processing required.")
        os.remove(LOCAL_FILE)