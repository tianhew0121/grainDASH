import geopandas as gpd
import pandas as pd
import os

# Path to your directory containing all state subfolders
base_path = "/Users/wangtianhe/Desktop/大豆/grainDASH/data/water_geo_data"

# List to hold GeoDataFrames
gdf_list = []

# Walk through folders
for root, dirs, files in os.walk(base_path):
    for file in files:
        if file.endswith(".shp") and "NHDFlowline" in file:
            shp_path = os.path.join(root, file)
            try:
                gdf = gpd.read_file(shp_path)
                # Filter for Stream/River features (FType = 460)
                # print(f"✅ Columns in {file}: {gdf.columns.tolist()}")
                gdf = gdf[gdf["ftype"] == 460]
                # Reproject to WGS84 for web mapping
                gdf = gdf.to_crs("EPSG:4326")
                gdf_list.append(gdf)
                print(f"Loaded: {shp_path} ({len(gdf)} features)")
            except Exception as e:
                print(f"Error reading {shp_path}: {e}")

# Merge all into one
merged_rivers = gpd.GeoDataFrame(pd.concat(gdf_list, ignore_index=True), crs="EPSG:4326")

# Save to file (choose one)
output_master_path = "/Users/wangtianhe/Desktop/大豆/grainDASH/data/water_geo_data/water_output/"
output_path_gpkg = f"{output_master_path}merged_rivers.gpkg"
output_path_geojson = f"{output_master_path}merged_rivers.geojson"

merged_rivers.to_file(output_path_gpkg, layer="rivers", driver="GPKG")
# merged_rivers.to_file(output_path_geojson, driver="GeoJSON")

print(f"Saved merged rivers to:\n- {output_path_gpkg}\n- {output_path_geojson}")
