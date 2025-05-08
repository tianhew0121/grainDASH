import geopandas as gpd
import matplotlib.pyplot as plt

# Load river geometries
rivers = gpd.read_file("/Users/wangtianhe/Desktop/大豆/grainDASH/data/water_geo_data/water_output/dash_ready_rivers.geojson")

# Set plot bounding box (must match Mapbox image overlay coordinates)
bbox = [-125, 25, -65, 50]  # [lon_min, lat_min, lon_max, lat_max]

# Calculate aspect ratio for proper width/height scaling
aspect_ratio = (bbox[2] - bbox[0]) / (bbox[3] - bbox[1])  # width / height
width = 2400
height = int(width / aspect_ratio)
dpi = 100

# Set up transparent figure with exact map extent
fig, ax = plt.subplots(figsize=(width / dpi, height / dpi), dpi=dpi)
fig.subplots_adjust(left=0, right=1, top=1, bottom=0)  # remove all padding/margin
ax.set_facecolor("none")
fig.patch.set_alpha(0)

# Clip to bbox for performance and rendering consistency
rivers = rivers.cx[bbox[0]:bbox[2], bbox[1]:bbox[3]]
rivers.plot(ax=ax, color="blue", linewidth=1)

# Match geographic extent
ax.set_xlim(bbox[0], bbox[2])
ax.set_ylim(bbox[1], bbox[3])
ax.axis("off")

# Save to assets folder for Dash (DO NOT use bbox_inches or pad_inches)
plt.savefig("/Users/wangtianhe/Desktop/大豆/grainDASH/assets/rivers_overlay.png", dpi=dpi, transparent=True)
plt.close()
