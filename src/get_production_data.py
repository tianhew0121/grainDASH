import requests
import pandas as pd

# Replace with your USDA NASS API key
API_KEY = "3D3B23A0-BC1D-3537-AF29-AFA32A05DDFF"

def fetch_usda_crop_data(year, crop, agg_level="COUNTY"):
    """
    Fetch crop production data from USDA NASS Quick Stats API.

    :param year: Year as string (e.g., '2023')
    :param crop: Crop name, e.g., 'SOYBEANS' or 'CORN'
    :param agg_level: 'COUNTY', 'STATE', etc.
    :return: pandas.DataFrame with results
    """
    base_url = "https://quickstats.nass.usda.gov/api/api_GET/"
    params = {
        "key": API_KEY,
        "source_desc": "SURVEY",
        "sector_desc": "CROPS",
        "group_desc": "FIELD CROPS",
        "commodity_desc": crop.upper(),
        "statisticcat_desc": "PRODUCTION",
        "unit_desc": "BU",  # BU for bushels, can also use "METRIC TONS" if available
        "freq_desc": "ANNUAL",
        "agg_level_desc": agg_level,
        "year": year,
        "format": "JSON"
    }

    response = requests.get(base_url, params=params)
    response.raise_for_status()
    data = response.json()["data"]
    df = pd.DataFrame(data)
    return df

# Example usage:
if __name__ == "__main__":
    df_corn = fetch_usda_crop_data("2023", "CORN")
    df_soy = fetch_usda_crop_data("2023", "SOYBEANS")

    # Keep relevant columns and save
    for name, df in [("corn", df_corn), ("soybeans", df_soy)]:
        df_filtered = df[["state_name", "county_name", "year", "Value", "unit_desc", "state_fips_code", "county_code"]]
        df_filtered.to_csv(f"/Users/wangtianhe/Desktop/大豆/grainDASH/data/production_data/{name}_county_production_2023.csv", index=False)
