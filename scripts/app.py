import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from pathlib import Path
import os

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.resolve()
PROJECT_ROOT = SCRIPT_DIR.parent

# Page config
st.set_page_config(
    page_title="Global Defense Metrics",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    """Load and merge military data."""
    try:
        data_dir = PROJECT_ROOT / "data"
        clean_data = pd.read_csv(data_dir / "clean_data.csv")
        derived_data = pd.read_csv(data_dir / "kpi_data.csv")
        
        # Standardize column names
        if "Country" in clean_data.columns:
            clean_data.rename(columns={"Country": "country_name"}, inplace=True)
        if "Country" in derived_data.columns:
            derived_data.rename(columns={"Country": "country_name"}, inplace=True)
        
        # Forward fill country names to handle missing values
        if clean_data["country_name"].isna().any():
            clean_data["country_name"] = clean_data["country_name"].ffill()
        if derived_data["country_name"].isna().any():
            derived_data["country_name"] = derived_data["country_name"].ffill()
        
        # Merge data
        df = clean_data.merge(derived_data, on="country_name", how="left", suffixes=("", "_derived"))
        df = df.dropna(subset=["country_name"])
        
        return df, clean_data, derived_data
    except Exception as e:
        st.error(f"❌ Error loading data: {e}")
        return None, None, None

def format_number(value):
    """Format large numbers with B, M, K suffixes."""
    if pd.isna(value):
        return "N/A"
    value = float(value)
    if value >= 1e9:
        return f"{value / 1e9:.1f}B"
    elif value >= 1e6:
        return f"{value / 1e6:.1f}M"
    elif value >= 1e3:
        return f"{value / 1e3:.1f}K"
    else:
        return f"{value:.0f}"

def safe_int(value, default=0):
    """Safely convert value to int, handling NaN."""
    if pd.isna(value):
        return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default

def page_quick_stats():
    """Global overview dashboard."""
    st.header("🌍 Quick Stats – Global Defense Overview")
    
    df, _, _ = load_data()
    if df is None or df.empty:
        st.error("No data available")
        return
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_aircraft = df["Total Aircraft"].sum()
        st.metric("Global Aircraft", format_number(total_aircraft))
    
    with col2:
        total_personnel = df["Active Personnel"].sum()
        st.metric("Active Personnel", format_number(total_personnel))
    
    with col3:
        total_budget = df["Defense Budget (USD)"].sum()
        st.metric("Total Defense Budget", format_number(total_budget))
    
    with col4:
        total_countries = len(df)
        st.metric("Countries Analyzed", total_countries)
    
    # Top 10 countries by defense budget
    st.subheader("Top 10 Countries by Defense Budget")
    top_10 = df.nlargest(10, "Defense Budget (USD)")[["country_name", "Defense Budget (USD)"]].copy()
    top_10["Defense Budget (Billions)"] = top_10["Defense Budget (USD)"] / 1e9
    
    fig = px.bar(top_10, x="country_name", y="Defense Budget (Billions)", 
                 title="Top 10 Defense Budgets", labels={"country_name": "Country"})
    st.plotly_chart(fig, use_container_width=True)

def page_nation_overview():
    """Country-specific analysis."""
    st.header("🏛️ Nation Overview – Country Analysis")
    
    df, _, _ = load_data()
    if df is None or df.empty:
        st.error("No data available")
        return
    
    countries = sorted(df["country_name"].dropna().unique().tolist())
    if not countries:
        st.error("No countries found in data")
        return
    
    country = st.selectbox("Select Country", countries)
    
    country_data = df[df["country_name"] == country]
    if country_data.empty:
        st.error(f"No data for {country}")
        return
    
    country_data = country_data.iloc[0]
    
    st.subheader(f"{country} Military Profile")
    
    # Display metrics in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Aircraft", safe_int(country_data.get("Total Aircraft", 0)))
        st.metric("Fighter Aircraft", safe_int(country_data.get("Fighter Aircraft", 0)))
        st.metric("Helicopters", safe_int(country_data.get("Helicopters", 0)))
    
    with col2:
        st.metric("Tanks", safe_int(country_data.get("Tanks", 0)))
        st.metric("Active Personnel", format_number(country_data.get("Active Personnel", 0)))
        st.metric("Defense Budget", format_number(country_data.get("Defense Budget (USD)", 0)))
    
    with col3:
        st.metric("Submarines", safe_int(country_data.get("Submarines", 0)))
        st.metric("Naval Vessels", safe_int(country_data.get("Total Naval Assets", 0)))
        st.metric("Population", format_number(country_data.get("Total Population", 0)))

def page_compare_powers():
    """Multi-country comparison."""
    st.header("⚖️ Compare Powers – Comparative Analysis")
    
    df, _, _ = load_data()
    if df is None or df.empty:
        st.error("No data available")
        return
    
    countries = sorted(df["country_name"].dropna().unique().tolist())
    if not countries:
        st.error("No countries found")
        return
    
    # Select metric
    metric = st.selectbox("Select Metric", ["Defense Budget (USD)", "Total Aircraft", "Active Personnel", "Tanks"])
    
    # Select countries
    selected_countries = st.multiselect("Select Countries (2-5)", countries, default=countries[:3])
    
    if not selected_countries:
        st.warning("Please select at least one country")
        return
    
    # Filter and plot
    compare_df = df[df["country_name"].isin(selected_countries)][["country_name", metric]].copy()
    compare_df = compare_df.dropna()
    
    if compare_df.empty:
        st.error("No data for selected countries")
        return
    
    fig = px.bar(compare_df, x="country_name", y=metric, 
                 title=f"{metric} Comparison",
                 labels={"country_name": "Country"})
    st.plotly_chart(fig, use_container_width=True)

def page_coalition_builder():
    """Alliance simulation."""
    st.header("🤝 Coalition Builder – Alliance Strength")
    
    df, _, _ = load_data()
    if df is None or df.empty:
        st.error("No data available")
        return
    
    countries = sorted(df["country_name"].dropna().unique().tolist())
    if not countries:
        st.error("No countries found")
        return
    
    # Select countries for coalition
    coalition = st.multiselect("Select Coalition Countries", countries, default=countries[:3])
    
    if not coalition:
        st.warning("Select at least one country")
        return
    
    coalition_data = df[df["country_name"].isin(coalition)]
    
    # Calculate totals
    total_budget = coalition_data["Defense Budget (USD)"].sum()
    total_aircraft = coalition_data["Total Aircraft"].sum()
    total_personnel = coalition_data["Active Personnel"].sum()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Coalition Budget", format_number(total_budget))
    with col2:
        st.metric("Total Aircraft", safe_int(total_aircraft))
    with col3:
        st.metric("Total Personnel", format_number(total_personnel))
    
    # Pie chart
    coalition_breakdown = coalition_data[["country_name", "Defense Budget (USD)"]].copy()
    fig = px.pie(coalition_breakdown, values="Defense Budget (USD)", names="country_name",
                 title="Coalition Budget Distribution")
    st.plotly_chart(fig, use_container_width=True)

def main():
    """Main app."""
    st.sidebar.title("🛡️ Global Defense Metrics")
    st.sidebar.write("2025 Analytics Platform")
    
    page = st.sidebar.radio(
        "Select Module",
        ["📊 Quick Stats", "🏛️ Nation Overview", "⚖️ Compare Powers", "🤝 Coalition Builder"]
    )
    
    st.sidebar.divider()
    st.sidebar.write("**About GDM**")
    st.sidebar.write("Comprehensive analysis of military and economic indicators for 140+ countries.")
    
    if "Quick Stats" in page:
        page_quick_stats()
    elif "Nation Overview" in page:
        page_nation_overview()
    elif "Compare Powers" in page:
        page_compare_powers()
    elif "Coalition Builder" in page:
        page_coalition_builder()

if __name__ == "__main__":
    main()
