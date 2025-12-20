
import preprocessing as pp
import requests
import pandas as pd
import json

# Load Data
data_dict, _ = pp.load_data()
master_df = data_dict['master']
print("Data Loaded.")

# Load GeoJSON
geojson_url = pp.get_geojson_url()
response = requests.get(geojson_url)
geojson = response.json()

# Extract State Names from GeoJSON
geojson_states = set()
for feature in geojson['features']:
    props = feature['properties']
    if len(geojson_states) == 0:
        print(f"First Feature Keys: {props.keys()}")
    
    if 'st_nm' in props:
        geojson_states.add(props['st_nm'])
    elif 'state_name' in props:
        geojson_states.add(props['state_name'])
    elif 'NAME_1' in props:
        geojson_states.add(props['NAME_1'])
    else:
        print(f"Unknown properties: {props.keys()}")

print(f"\nGeoJSON States ({len(geojson_states)}):")
print(sorted(list(geojson_states)))

# Extract State Names from DataFrame
df_states = set(master_df['State'].unique())
print(f"\nDataFrame States ({len(df_states)}):")
print(sorted(list(df_states)))

# Find Mismatches
in_geojson_not_df = geojson_states - df_states
in_df_not_geojson = df_states - geojson_states

print(f"\nIn GeoJSON but NOT in DataFrame (Map has it, Data missing): {in_geojson_not_df}")
print(f"\nIn DataFrame but NOT in GeoJSON (Data has it, Map missing): {in_df_not_geojson}")
