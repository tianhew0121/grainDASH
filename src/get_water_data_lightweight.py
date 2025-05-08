import overpy
import geopandas as gpd
from shapely.geometry import LineString
from tqdm import tqdm
import time

def fetch_rivers_by_tile(bbox, tile_size=2.0, simplify_tolerance=0.01, retry_limit=3):
    """
    Split a bounding box into tiles and query rivers from Overpass API.
    """
    api = overpy.Overpass(url="https://overpass.kumi.systems/api/interpreter")
    min_lat, min_lon, max_lat, max_lon = bbox

    lat_steps = int((max_lat - min_lat) / tile_size) + 1
    lon_steps = int((max_lon - min_lon) / tile_size) + 1

    all_lines = []

    print(f"⏳ Splitting region into {lat_steps * lon_steps} tiles...")

    for i in tqdm(range(lat_steps), desc="Latitude tiles"):
        for j in range(lon_steps):
            tile_south = min_lat + i * tile_size
            tile_north = min(tile_south + tile_size, max_lat)
            tile_west = min_lon + j * tile_size
            tile_east = min(tile_west + tile_size, max_lon)

            query = f"""
            [out:json][timeout:60];
            (
            way["waterway"="river"]["name"]({tile_south},{tile_west},{tile_north},{tile_east});
            );
            out body;
            >;
            out skel qt;
            """

            attempt = 0
            while attempt < retry_limit:
                try:
                    result = api.query(query)
                    break
                except overpy.exception.OverpassTooManyRequests:
                    print("⚠️ Too many requests. Waiting 10 seconds...")
                    time.sleep(10)
                    attempt += 1
                except overpy.exception.OverpassRuntimeError:
                    print(f"⚠️ Timeout at tile ({i},{j}). Skipping after retries.")
                    attempt += 1
                    break
                except Exception as e:
                    print(f"⚠️ Error: {e}")
                    attempt += 1
                    break

            else:
                continue  # skip to next tile

            for way in result.ways:
                coords = [(float(n.lon), float(n.lat)) for n in way.nodes]
                if len(coords) >= 2:
                    geom = LineString(coords).simplify(simplify_tolerance)
                    all_lines.append({
                        "name": way.tags.get("name", "Unnamed"),
                        "geometry": geom
                    })

    return gpd.GeoDataFrame(all_lines, crs="EPSG:4326")

bbox = [36.0, -100.0, 45.0, -85.0]  # [south, west, north, east]
rivers = fetch_rivers_by_tile(bbox, tile_size=2.0, simplify_tolerance=0.01)
rivers.to_file("/Users/wangtianhe/Desktop/大豆/soydash/data/water_geo_data/water_output/osm_major_rivers.geojson", driver="GeoJSON")
