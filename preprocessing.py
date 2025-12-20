import pandas as pd
import numpy as np

def load_data():
    """
    Loads and merges the 4 datasets:
    1. Recorded Forest Area
    2. Statewise Tree Cover
    3. Mangroves (Time Series)
    4. Agro India States (Rainfall)
    """
    
    # 1. Load Datasets
    # Update paths as per the actual file structure
    forest_path = "Recorded_Forest_Area.csv"
    tree_path = "StatewiseTreeCover.csv"
    mangrove_path = "19360- Dataful/mangroves-year-and-state-wise-mangrove-forest-cover-in-india-since-1987.csv"
    agro_path = "Agro_India_States.csv"

    try:
        df_forest = pd.read_csv(forest_path)
        df_tree = pd.read_csv(tree_path)
        df_mangrove = pd.read_csv(mangrove_path)
        df_agro = pd.read_csv(agro_path)
    except FileNotFoundError as e:
        return None, f"Error loading file: {e}"

    # 2. Clean & Standardize State Names
    # Helper to standardize state names
    def clean_state_name(name):
        if pd.isna(name): return "Unknown"
        name = name.strip().title()
        # Mapping for common inconsistencies
        replacements = {
            "Andhra Pradesh": "Andhra Pradesh",
            "Arunachal Pradesh": "Arunachal Pradesh",
            "Jammu & Kashmir": "Jammu & Kashmir",
            "A & N Islands": "Andaman & Nicobar Islands",
            "Andaman & Nicobar": "Andaman & Nicobar Islands",
            # Add more as discovered
        }
        return replacements.get(name, name)

    # Apply standardization
    # Adjust column names based on actual CSV headers
    # Forest Data
    # 'State/UTs' seems to be the column name from previous 'head' command
    if 'State/UTs' in df_forest.columns:
        df_forest['State'] = df_forest['State/UTs'].apply(clean_state_name)
    
    # Tree Data
    # 'State/ Uts' (note the space)
    if 'State/ Uts' in df_tree.columns:
        df_tree['State'] = df_tree['State/ Uts'].apply(clean_state_name)

    # Mangrove Data
    # 'state'
    if 'state' in df_mangrove.columns:
        df_mangrove['State'] = df_mangrove['state'].apply(clean_state_name)

    # Agro Data
    # 'States'
    if 'States' in df_agro.columns:
        df_agro['State'] = df_agro['States'].apply(clean_state_name)
    
    # 3. Numeric Conversion
    # Several columns have commas (e.g., "2,75,069")
    def clean_numeric(val):
        if isinstance(val, str):
            val = val.replace(',', '')
            try:
                return float(val)
            except:
                return 0.0
        return val

    # Apply to specific columns
    # Example for Forest
    forest_cols = ['Geographical Area', 'Recorded Forest Area - Total']
    for col in forest_cols:
        if col in df_forest.columns:
            df_forest[col] = df_forest[col].apply(clean_numeric)

    # Example for Mangroves
    if 'value' in df_mangrove.columns:
        df_mangrove['value'] = df_mangrove['value'].apply(clean_numeric)

    # Example for Tree
    if 'Tree Cover - Area' in df_tree.columns:
        df_tree['Tree Cover - Area'] = df_tree['Tree Cover - Area'].apply(clean_numeric)

    # 4. Merging (Creating a Master Dataset for Snapshot Analysis)
    # We will merge on 'State'
    # Base it on Forest Data as it likely has most states
    master_df = df_forest[['State', 'Recorded Forest Area - Total', 'Geographical Area']].copy()
    
    # Merge Tree Cover
    master_df = pd.merge(master_df, df_tree[['State', 'Tree Cover - Area']], on='State', how='left')
    
    # Merge Agro (Rainfall) - 'Precipitation_mm'
    if 'Precipitation_mm' in df_agro.columns:
        master_df = pd.merge(master_df, df_agro[['State', 'Precipitation_mm']], on='State', how='left')

    # Fill NaNs
    master_df.fillna(0, inplace=True)

    return {
        "forest": df_forest,
        "tree": df_tree,
        "mangrove": df_mangrove,
        "agro": df_agro,
        "master": master_df
    }, None

def get_geojson_url():
    # Public GeoJSON for India States
    return "https://gist.githubusercontent.com/jbrobst/56c13bbbf9d97d187fea01ca62ea5112/raw/e388c4cae20aa53cb5090210a42ebb9b765c0a36/india_states.geojson"
