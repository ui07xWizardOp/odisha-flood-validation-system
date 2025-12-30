import os
import geopandas as gpd
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load env
load_dotenv()

def import_bhuvan_shapefile(shp_path: str, table_name: str = "ground_truth", event_name: str = "Unknown"):
    """
    Imports ISRO Bhuvan flood extent shapefile into PostGIS.
    """
    # Database connection
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fallback for local testing
        db_url = "postgresql://flood_admin:flood_secure_password_2024@localhost:5432/flood_validation"
    
    engine = create_engine(db_url)

    # Read Shapefile
    print(f"Reading shapefile: {shp_path}")
    gdf = gpd.read_file(shp_path)

    # Ensure CRS is WGS84 (EPSG:4326)
    if gdf.crs != "EPSG:4326":
        print("Reprojecting to EPSG:4326...")
        gdf = gdf.to_crs("EPSG:4326")

    # Add metadata columns if they don't exist
    if 'event_name' not in gdf.columns:
        gdf['event_name'] = event_name
    
    # Rename geometry column to 'flood_extent' if needed matching DB schema? 
    # Or rely on GeoPandas default 'geometry' and let PostGIS handle it.
    # The existing schema has `flood_extent GEOGRAPHY(MULTIPOLYGON, 4326)`.
    # Using to_postgis (requires geoalchemy2) is easiest.
    
    # We might need to map columns to the schema defined in setup_database.sql
    # Let's prepare a subset DataFrame matching target schema roughly or just append raw.
    # For ground_truth table: truth_id, event_name, event_date, flood_extent...
    
    # Simplification: Upload as is, then SQL to insert into main table, or clean here.
    # Let's rename geometry to flood_extent for clarity if using specific loaders, 
    # but geopandas .to_postgis uses 'geometry' by default.
    
    print(f"Uploading {len(gdf)} features to database...")
    try:
        gdf.to_postgis(table_name, engine, if_exists='append', index=False)
        print("Import successful!")
    except Exception as e:
        print(f"Import failed: {e}")

if __name__ == "__main__":
    # Example
    # import_bhuvan_shapefile("data/raw/bhuvan/fani_2019/fani_flood.shp", event_name="Cyclone Fani 2019")
    pass
