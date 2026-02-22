import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import preprocessing as pp

# -----------------------------------------------------------------------------
# Configuration & Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="India Forestry Dashboard",
    page_icon="🌳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Dark Theme & CSS
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #262730;
    }
    
    /* Metrics Cards - Glassmorphism */
    .stMetric {
        background-color: #262730;
        border: 1px solid #4f4f4f;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    [data-testid="stMetricLabel"] {
        color: #b0bec5 !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
    }
    [data-testid="stMetricDelta"] {
        color: #dcedc8 !important; 
    }
    
    /* Headers & Text */
    h1, h2, h3 {
        color: #66bb6a !important; /* Light Green */
    }
    p, .stMarkdown {
        color: #e0e0e0;
    }
    
    /* Custom Warning Box */
    .stAlert {
        background-color: #1b5e20; /* Dark Green bg for alert */
        color: #ffffff;
        border: none;
    }
    
    /* Plotly Chart Background */
    .js-plotly-plot .plotly .main-svg {
        background: rgba(0,0,0,0) !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# Data Loading
# -----------------------------------------------------------------------------
@st.cache_data
def get_data():
    return pp.load_data()

data_dict, error = get_data()

if error:
    st.error(f"Failed to load data: {error}")
    st.stop()

df_forest = data_dict['forest']
df_tree = data_dict['tree']
df_mangrove = data_dict['mangrove']
df_agro = data_dict['agro']
master_df = data_dict['master']

# -----------------------------------------------------------------------------
# Sidebar & Navigation
# -----------------------------------------------------------------------------
st.sidebar.title("🌲 Forest Analytics")
page = st.sidebar.radio("Navigate", ["Executive Summary", "Deep Dive Data", "Geospatial Intelligence"])

st.sidebar.markdown("---")
st.sidebar.subheader("📝 Analyst Insights")
insights = st.sidebar.text_area("Write your observations here:", height=150)
if insights:
    st.sidebar.info("Insight saved to session.")

st.sidebar.markdown("---")
st.sidebar.caption("Data Source: India State of Forest Report (ISFR)")

# -----------------------------------------------------------------------------
# Page 1: Executive Summary
# -----------------------------------------------------------------------------
if page == "Executive Summary":
    st.title("🇮🇳 National Forest Cover: Executive Summary")
    
    # 2001 Methodology Change Alert
    st.warning("⚠️ **Data Health Alert:** Standard cleaning methodology was revised in 2001. Comparisons pre-2001 should be interpreted with caution.")

    # KPI Metrics
    # Calculate Total Forest Area (Current)
    total_forest_current = master_df['Recorded Forest Area - Total'].sum()
    
    # Calculate previous reference (SFR 2005) if available
    if 'Recorded Forest Area as in SFR 2005' in df_forest.columns:
        # Need to clean that column too if not done in preprocessing, assume it needs cleaning inside the metric calculation for safety
        # Actually preprocessing only cleaned specific cols, let's do a quick local clean if needed or rely on robust preprocessing
        # Checking preprocessing.py... it only cleaned 'Recorded Forest Area - Total'. 
        # I need to clean SFR 2005 here or it might be strings.
        sfr_2005_series = df_forest['Recorded Forest Area as in SFR 2005'].astype(str).str.replace(',', '', regex=True)
        sfr_2005_total = pd.to_numeric(sfr_2005_series, errors='coerce').sum()
        
        pct_change = ((total_forest_current - sfr_2005_total) / sfr_2005_total) * 100
    else:
        sfr_2005_total = total_forest_current # Fallback
        pct_change = 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Recorded Forest Area", f"{total_forest_current:,.0f} sq km", delta=f"{pct_change:.2f}% vs 2005")
    col2.metric("Total Tree Cover", f"{master_df['Tree Cover - Area'].sum():,.0f} sq km")
    col3.metric("Data Reporting States", f"{len(master_df)}")

    st.markdown("---")

    # Dual Axis Chart: Forest Cover vs Rainfall
    st.subheader("Correlation: Forest Cover vs. Rainfall")
    
    # Sort by Forest Area for better visualization
    chart_df = master_df.sort_values('Recorded Forest Area - Total', ascending=False)
    
    fig = go.Figure()

    # Bar Chart - Rainfall (Secondary Axis likely better for bars if line is primary, but user asked for specific Combo)
    # User: "Line chart for 'Total Forest Cover' and a Bar chart for 'Annual Rainfall/Budget'"
    
    fig.add_trace(go.Bar(
        x=chart_df['State'],
        y=chart_df['Precipitation_mm'],
        name='Annual Rainfall (mm)',
        marker_color='#87CEEB', # Sky Blue
        yaxis='y2'
    ))

    fig.add_trace(go.Scatter(
        x=chart_df['State'],
        y=chart_df['Recorded Forest Area - Total'],
        name='Forest Cover (sq km)',
        mode='lines+markers',
        marker_color='#228B22', # Forest Green
        line=dict(width=3)
    ))

    fig.update_layout(
        title="Forest Cover vs. Annual Rainfall per State",
        xaxis_title="State",
        yaxis=dict(title="Forest Cover (sq km)", side='left', showgrid=False),
        yaxis2=dict(title="Rainfall (mm)", side='right', overlaying='y', showgrid=False),
        legend=dict(x=0.8, y=1.1, orientation='h'),
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)


# -----------------------------------------------------------------------------
# Page 2: Deep Dive (Statistical Insights)
# -----------------------------------------------------------------------------
elif page == "Deep Dive Data":
    st.title("📊 Deep Dive: Forest Quality & Trends")

    col_a, col_b = st.columns([1, 1])

    with col_a:
        st.subheader("Forest Composition (Quality Proxy)")
        st.caption("Ratio of Reserved (High Protection) vs. Protected/Unclassed Forests")
        
        # Proxy Data for Quality: Reserved, Protected, Unclassed
        # We need to clean these columns first as preprocessing only did 'Total'
        for c in ['Recorded Forest Area - Reserved Forests', 'Recorded Forest Area - Protected Forests', 'Recorded Forest Area - Unclassed Forests']:
            if c in df_forest.columns:
                df_forest[c] = pd.to_numeric(df_forest[c].astype(str).str.replace(',', '', regex=True), errors='coerce').fillna(0)

        # Melt for Stacked Area/Bar
        quality_df = df_forest.melt(id_vars=['State'], 
                                   value_vars=['Recorded Forest Area - Reserved Forests', 
                                               'Recorded Forest Area - Protected Forests', 
                                               'Recorded Forest Area - Unclassed Forests'],
                                   var_name='Forest Type', value_name='Area')
        
        # Clean labels
        quality_df['Forest Type'] = quality_df['Forest Type'].str.replace('Recorded Forest Area - ', '')
        
        # Sort by Total area to keep the chart clean
        top_states = df_forest.sort_values('Recorded Forest Area - Total', ascending=False).head(10)['State']
        quality_df_filtered = quality_df[quality_df['State'].isin(top_states)]

        fig_quality = px.area(quality_df_filtered, x='State', y='Area', color='Forest Type',
                             color_discrete_map={
                                 'Reserved Forests': '#006400', # Dark Green
                                 'Protected Forests': '#228B22', # Forest Green
                                 'Unclassed Forests': '#90EE90'  # Light Green
                             })
        fig_quality.update_layout(
            title="Forest Composition (Top 10 States)",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color="white")
        )
        st.plotly_chart(fig_quality, use_container_width=True)

    with col_b:
        st.subheader("Leaderboard: Forest Cover Change")
        st.caption("Top Gainers & Losers (vs 2005 Baseline)")
        
        # Filter out 'Total' row if present to avoid skewing leaderboard
        df_forest = df_forest[df_forest['State'] != 'Total']
        
        # Calculate Delta
        col_sfr = 'Recorded Forest Area as in SFR 2005'
        col_cur = 'Recorded Forest Area - Total'
        
        df_forest['SFR_2005_Clean'] = pd.to_numeric(df_forest[col_sfr].astype(str).str.replace(',', '', regex=True), errors='coerce').fillna(0)
        df_forest['Delta'] = df_forest[col_cur] - df_forest['SFR_2005_Clean']
        
        # Sort
        df_sorted = df_forest.sort_values('Delta', ascending=False)
        
        top_gainers = df_sorted.head(5)[['State', 'Delta']]
        top_losers = df_sorted.tail(5)[['State', 'Delta']].sort_values('Delta', ascending=True)

        # Custom HTML Table Styles for Dark Mode
        def render_custom_table(df, title, color_theme):
            # Use min-height to ensure symmetry while allowing growth for long names
            html = f'<div style="background-color: #262730; padding: 15px; border-radius: 10px; border: 1px solid #4f4f4f; min-height: 520px; display: flex; flex-direction: column;">'
            html += f'<h4 style="color: {color_theme}; text-align: center; margin-bottom: 12px; font-size: 1.1rem;">{title}</h4>'
            html += '<div style="flex-grow: 1; overflow-x: auto;">' # Prevents horizontal overflow
            html += '<table style="width: 100%; border-collapse: collapse; color: #e0e0e0; table-layout: fixed; font-size: 14px;">'
            html += '<thead>'
            html += '<tr style="border-bottom: 2px solid #4f4f4f;">'
            html += '<th style="padding: 10px 5px; text-align: left; width: 62%;">State</th>'
            html += '<th style="padding: 10px 5px; text-align: right; width: 38%;">Change<br>(sq km)</th>'
            html += '</tr></thead><tbody>'
            
            for _, row in df.iterrows():
                val = row['Delta']
                val_fmt = f"{val:+.2f}"
                color = "#66bb6a" if val > 0 else "#ef5350"
                
                html += f'<tr style="border-bottom: 1px solid #383838;">'
                html += f'<td style="padding: 12px 5px; vertical-align: middle; line-height: 1.2; word-wrap: break-word;">{row["State"]}</td>'
                html += f'<td style="padding: 12px 5px; text-align: right; color: {color}; font-weight: bold; vertical-align: middle;">{val_fmt}</td>'
                html += '</tr>'
            
            html += '</tbody></table></div></div>'
            return html

        col_g, col_l = st.columns(2)
        with col_g:
            st.markdown(render_custom_table(top_gainers, "🏆 Top 5 Gainers", "#66bb6a"), unsafe_allow_html=True)
        with col_l:
            st.markdown(render_custom_table(top_losers, "🔻 Top 5 Losers", "#ef5350"), unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Page 3: Geospatial Intelligence
# -----------------------------------------------------------------------------
elif page == "Geospatial Intelligence":
    st.title("🗺️ Geospatial Intelligence Hub")
    
    # Layout: Map Control & Main Map
    col_controls, col_map = st.columns([1, 3])
    
    with col_controls:
        st.subheader("⚙️ Map Layers")
        map_metric = st.radio(
            "Select Metric to Visualize:",
            ["Recorded Forest Area - Total", "Tree Cover - Area", "Precipitation_mm", "Mangroves (2023)"],
            captions=["Total official forest area", "Tree cover outside forests", "Annual Rainfall", "Coastal Mangrove spread"]
        )
        
        # Color Scale Mapping
        color_scales = {
            "Recorded Forest Area - Total": "Greens",
            "Tree Cover - Area": "YlGn",
            "Precipitation_mm": "Blues",
            "Mangroves (2023)": "Teal"
        }
        
        # Add Mangrove data to master_df for mapping if selected
        # We need to treat 'master_df' carefully. It has Forest, Tree, Agro.
        # Mangrove is in df_mangrove. Let's merge the latest mangrove year (2023) into master if needed.
        if "Mangroves (2023)" == map_metric:
            # Quick merge for 2023 Snapshot
            mangrove_2023 = df_mangrove[df_mangrove['year'] == 2023]
            if 'Mangroves (2023)' not in master_df.columns:
                master_df = pd.merge(master_df, mangrove_2023[['State', 'value']], on='State', how='left').rename(columns={'value': 'Mangroves (2023)'})
            master_df['Mangroves (2023)'] = master_df['Mangroves (2023)'].fillna(0)

    # GeoJSON
    geojson_url = pp.get_geojson_url()
    
    # Map Plotting
    max_val = master_df[map_metric].max()
    
    fig_map = px.choropleth(
        master_df,
        geojson=geojson_url,
        featureidkey='properties.ST_NM',
        locations='State',
        color=map_metric,
        color_continuous_scale=color_scales.get(map_metric, "Viridis"),
        range_color=(0, max_val),
        hover_name='State',
        hover_data={
            map_metric: True,
            'State': False
        },
        title=f"India: {map_metric} Distribution"
    )
    
    # Enhanced Geo Layout - Focus on India, remove World Noise
    fig_map.update_geos(
        # fitbounds="locations", # Removed as it fights with manual range sometimes
        visible=True, 
        showcountries=True, countrycolor="#4a4a4a",
        showsubunits=True, subunitcolor="#4a4a4a",
        showocean=True, oceancolor="#1e212b",
        showland=True, landcolor="#0e1117",
        bgcolor='rgba(0,0,0,0)',
        # Strict Bounding Box for India
        lataxis_range=[6, 38],
        lonaxis_range=[68, 98]
    )
    
    fig_map.update_layout(
        height=650,
        margin={"r":0,"t":40,"l":0,"b":0},
        template="plotly_dark",
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        coloraxis_colorbar=dict(title=dict(text="Scale", side="right"))
    )
    
    with col_map:
        st.plotly_chart(fig_map, use_container_width=True)
        
        # dynamic explanation
        explanations = {
            "Recorded Forest Area - Total": "Shows the legal status of the land. High values mean more land is legally designated as forest, regardless of actual tree cover.",
            "Tree Cover - Area": "Actual green cover outside designated forest areas. High values indicate good extensive greenery in cities/farms.",
            "Precipitation_mm": "Average annual rainfall. Crucial for understanding if forest growth is supported by climate.",
            "Mangroves (2023)": "Coastal buffer zones. Only visible in coastal states (WB, Gujarat, etc). Critical for flood protection."
        }
        
        st.info(f"ℹ️ **What am I looking at?**\n\n{explanations.get(map_metric, 'N/A')}")


    st.markdown("---")
    
    # State Drill-Down / Report Card
    st.subheader("🔍 State Drill-Down Analysis")
    st.caption("Select a state below to view its complete forestry profile.")

    selected_state = st.selectbox("Select State:", options=sorted(master_df['State'].unique()))
    
    if selected_state:
        state_data = master_df[master_df['State'] == selected_state].iloc[0]
        
        # Card UI
        with st.container():
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("🌲 Forest Area", f"{state_data.get('Recorded Forest Area - Total', 0):,.0f} sq km")
            c2.metric("🌳 Tree Cover", f"{state_data.get('Tree Cover - Area', 0):,.0f} sq km")
            c3.metric("🌧️ Rainfall", f"{state_data.get('Precipitation_mm', 0):,.0f} mm")
            
            # Mangrove (if exists in master_df, else check df_mangrove)
            mangrove_val = df_mangrove[(df_mangrove['State'] == selected_state) & (df_mangrove['year'] == 2023)]['value'].sum()
            c4.metric("🌊 Mangrove (2023)", f"{mangrove_val:,.2f} sq km")
            
        st.markdown(f"""
        <div style="background-color: #262730; padding: 20px; border-radius: 10px; border: 1px solid #4f4f4f; margin-top: 20px;">
            <h4>📜 Analysis for {selected_state}</h4>
            <p>
                {selected_state} covers a geographical area of <b>{state_data.get('Geographical Area', 0):,.0f} sq km</b>.
                The rain pattern is approximately <b>{state_data.get('Precipitation_mm', 'N/A')} mm</b> annually.
                {'Significant mangrove presence detected.' if mangrove_val > 50 else 'No major mangrove ecosystem detected.'}
            </p>
        </div>
        """, unsafe_allow_html=True)

