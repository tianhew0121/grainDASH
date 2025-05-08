import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import pandas as pd
import geopandas as gpd
import overpy
from shapely.geometry import LineString, MultiLineString

# ─────────────────────────────────────────────────────────────
# FILEPATHS
county_shape_filepath = "/Users/wangtianhe/Desktop/大豆/grainDASH/data/cb_2018_us_county_5m/cb_2018_us_county_5m.shp"
production_date_filepath = "/Users/wangtianhe/Desktop/大豆/grainDASH/data/production_data/"
river_data_filepath = "/Users/wangtianhe/Desktop/大豆/grainDASH/data/water_geo_data/Navigable_Waterway_Network_Lines/Navigable_Waterway_Network_Lines.shp"

# ─────────────────────────────────────────────────────────────
# LOAD COUNTY SHAPEFILE
county_gdf = gpd.read_file(county_shape_filepath)
county_gdf["FIPS"] = county_gdf["STATEFP"] + county_gdf["COUNTYFP"]
county_gdf = county_gdf.to_crs("EPSG:4326")
us_boundary = county_gdf.union_all()  # merges all counties into one shape

# # ─────────────────────────────────────────────────────────────
# Load the navigable waterways shapefile
waterways_gdf = gpd.read_file(river_data_filepath)
waterways_gdf = waterways_gdf.to_crs("EPSG:4326")

# Clip to US boundary
waterways_gdf = gpd.clip(waterways_gdf, us_boundary)
major_names =  ["Mississippi", "Ohio", "Illinois", "Arkansas", "Tennessee", "Missouri", "Red", "Columbia"]
uppercased_major_names = [name.upper() for name in major_names]
waterways_gdf = waterways_gdf[waterways_gdf["RIVERNAME"].str.contains('|'.join(uppercased_major_names), na=False)]
# Optional: simplify for performance
waterways_gdf["geometry"] = waterways_gdf["geometry"].simplify(tolerance=0.3, preserve_topology=True)

# Save for later loading
waterways_gdf.to_file("/Users/wangtianhe/Desktop/大豆/grainDASH/data/water_geo_data/water_output/dash_ready_rivers.geojson", driver="GeoJSON")

# ─────────────────────────────────────────────────────────────
rivers_gdf = gpd.read_file("/Users/wangtianhe/Desktop/大豆/grainDASH/data/water_geo_data/water_output/dash_ready_rivers.geojson")

# ─────────────────────────────────────────────────────────────
# LOAD PRODUCTION DATA
def load_production_data(crop, year="2023"):
    df = pd.read_csv(f"{production_date_filepath}{crop}_county_production_{year}.csv")
    df["FIPS"] = df["state_fips_code"].astype(str).str.zfill(2) + df["county_code"].astype(str).str.zfill(3)
    df["Value"] = df["Value"].str.replace(",", "").astype(float)
    return df

corn_df = load_production_data("corn", year="2023")
soybean_df = load_production_data("soybeans", year="2023")
crop_datasets = {"corn": corn_df, "soybeans": soybean_df}

# ─────────────────────────────────────────────────────────────
# DASH LAYOUT
app = dash.Dash(__name__)
app.title = "Grain Production Dashboard"

app.layout = html.Div([
    html.H1("🧺 U.S. Grain Production Dashboard", style={"textAlign": "center"}),

    html.Div([
        html.Label("Select Crop:", style={"fontSize": "18px", "textAlign": "right"}),
        dcc.Dropdown(
            id="crop-selector",
            options=[
                {"label": "Corn", "value": "corn"},
                {"label": "Soybeans", "value": "soybeans"}
            ],
            value="corn",
            clearable=False,
            style={"width": "300px"}
        )
    ], style={"textAlign": "center", "padding": "10px"}),

    html.Div([
        html.Label("Select Year:", style={"fontSize": "18px", "textAlign": "right"}),
        dcc.Dropdown(
            id="year-selector",
            options=[
                {"label": str(year), "value": str(year)} for year in range(2010, 2024)
            ],
            value="2023",
            clearable=False,
            style={"width": "300px"}
        )
    ], style={"textAlign": "center", "padding": "10px"}),

    html.Div([
        html.Label("Map Overlays:", style={"fontSize": "18px"}),
        dcc.Checklist(
            id="overlay-selector",
            options=[
                {"label": "Show Rivers", "value": "rivers"},
            ],
            value=["rivers"],
            labelStyle={'display': 'inline-block', 'margin-right': '15px'},
            style={"textAlign": "center"}
        )
    ], style={"padding": "10px"}),

    dcc.Graph(id="production-map", style={"height": "85vh"})
])

# ─────────────────────────────────────────────────────────────
# CALLBACK
@app.callback(
    Output("production-map", "figure"),
    Input("crop-selector", "value"),
    Input("year-selector", "value"),
    Input("overlay-selector", "value")
)
def update_map(crop, year, overlays):
    df = crop_datasets[crop]
    df = df[df["year"] == int(year)]
    merged = county_gdf.merge(df, on="FIPS", how="left")

    fig = px.choropleth_mapbox(
        merged,
        geojson=merged.geometry,
        locations=merged.index,
        color="Value",
        hover_name="county_name",
        hover_data={"state_name": True, "Value": True},
        mapbox_style="open-street-map",
        zoom=3.5,
        center={"lat": 39.5, "lon": -98.35},
        opacity=0.7,
        color_continuous_scale="YlGn"
    )
    if "rivers" in overlays:
        for _, row in rivers_gdf.iterrows():
            geom = row.geometry

            if isinstance(geom, LineString):
                coords = list(geom.coords)
                lons, lats = zip(*[(x, y) for x, y, *_ in coords])
                fig.add_scattermapbox(
                    lat=lats,
                    lon=lons,
                    mode="lines",
                    line=dict(color="blue", width=1.5),
                    name=row.get("name", "River"),
                    hoverinfo="name",
                    showlegend=False
                )

            elif isinstance(geom, MultiLineString):
                for part in geom.geoms:
                    coords = list(part.coords)
                    lons, lats = zip(*[(x, y) for x, y, *_ in coords])
                    fig.add_scattermapbox(
                        lat=lats,
                        lon=lons,
                        mode="lines",
                        line=dict(color="blue", width=1.5),
                        name=row.get("name", "River"),
                        hoverinfo="name",
                        showlegend=False
                    )

    fig.update_layout(
        title=f"{crop.capitalize()} Production by County ({year})",
        margin={"r": 0, "t": 40, "l": 0, "b": 0}
    )
    return fig

# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run_server(debug=True)
