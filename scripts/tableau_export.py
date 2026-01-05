"""
Global Defense Metrics (GDM) - 2025
Tableau Data Export Module

Creates Tableau-optimized data files (.hyper compatible CSV)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).parent.parent / "data"
TABLEAU_DIR = DATA_DIR / "tableau"

def export_for_tableau():
    """Export data optimized for Tableau."""
    
    logger.info("=" * 60)
    logger.info("EXPORTING DATA FOR TABLEAU")
    logger.info("=" * 60)
    
    TABLEAU_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load source data
    clean_data = pd.read_csv(DATA_DIR / "clean_data.csv")
    kpi_data = pd.read_csv(DATA_DIR / "kpi_data.csv")
    
    # Standardize column names
    if "Country" in clean_data.columns:
        clean_data.rename(columns={"Country": "Country Name"}, inplace=True)
    if "country_name" in clean_data.columns:
        clean_data.rename(columns={"country_name": "Country Name"}, inplace=True)
    
    if "Country" in kpi_data.columns:
        kpi_data.rename(columns={"Country": "Country Name"}, inplace=True)
    if "country_name" in kpi_data.columns:
        kpi_data.rename(columns={"country_name": "Country Name"}, inplace=True)
    
    # Merge data
    combined = clean_data.merge(kpi_data, on="Country Name", how="left", suffixes=("", "_kpi"))
    
    # Add geographic data for Tableau mapping
    regions = {
        "United States": ("North America", "USA", 37.0902, -95.7129),
        "Russia": ("Europe", "RUS", 61.5240, 105.3188),
        "China": ("Asia", "CHN", 35.8617, 104.1954),
        "India": ("Asia", "IND", 20.5937, 78.9629),
        "United Kingdom": ("Europe", "GBR", 55.3781, -3.4360),
        "France": ("Europe", "FRA", 46.2276, 2.2137),
        "Germany": ("Europe", "DEU", 51.1657, 10.4515),
        "Japan": ("Asia", "JPN", 36.2048, 138.2529),
        "South Korea": ("Asia", "KOR", 35.9078, 127.7669),
        "Italy": ("Europe", "ITA", 41.8719, 12.5674),
        "Brazil": ("South America", "BRA", -14.2350, -51.9253),
        "Australia": ("Oceania", "AUS", -25.2744, 133.7751),
        "Canada": ("North America", "CAN", 56.1304, -106.3468),
        "Turkey": ("Middle East", "TUR", 38.9637, 35.2433),
        "Israel": ("Middle East", "ISR", 31.0461, 34.8516),
        "Egypt": ("Africa", "EGY", 26.8206, 30.8025),
        "Pakistan": ("Asia", "PAK", 30.3753, 69.3451),
        "Iran": ("Middle East", "IRN", 32.4279, 53.6880),
        "Saudi Arabia": ("Middle East", "SAU", 23.8859, 45.0792),
        "Indonesia": ("Asia", "IDN", -0.7893, 113.9213),
    }
    
    combined["Region"] = combined["Country Name"].map(lambda x: regions.get(x, ("Other", "", 0, 0))[0])
    combined["ISO Code"] = combined["Country Name"].map(lambda x: regions.get(x, ("", "OTH", 0, 0))[1])
    combined["Latitude"] = combined["Country Name"].map(lambda x: regions.get(x, ("", "", 0, 0))[2])
    combined["Longitude"] = combined["Country Name"].map(lambda x: regions.get(x, ("", "", 0, 0))[3])
    
    # Add calculated fields for Tableau
    if "Defense Budget" in combined.columns and "Total Population" in combined.columns:
        combined["Budget Per Capita"] = (combined["Defense Budget"] / combined["Total Population"]).replace([np.inf, -np.inf], 0).fillna(0)
    
    # Add Power Tier classification
    combined["Power Tier"] = pd.cut(
        combined.index, 
        bins=[0, 5, 15, 40, 200],
        labels=["Superpower", "Major Power", "Regional Power", "Developing"]
    )
    
    # Export main data
    combined.to_csv(TABLEAU_DIR / "gdm_tableau_data.csv", index=False)
    logger.info(f"Exported: {TABLEAU_DIR / 'gdm_tableau_data.csv'}")
    
    # Create summary for Tableau dashboard
    summary = pd.DataFrame({
        "Metric": ["Total Countries", "Total Defense Budget", "Total Aircraft", "Total Personnel"],
        "Value": [
            len(combined),
            combined["Defense Budget"].sum() if "Defense Budget" in combined.columns else 0,
            combined["Total Aircraft"].sum() if "Total Aircraft" in combined.columns else 0,
            combined["Active Personnel"].sum() if "Active Personnel" in combined.columns else 0
        ]
    })
    summary.to_csv(TABLEAU_DIR / "gdm_summary.csv", index=False)
    
    logger.info("=" * 60)
    logger.info("TABLEAU EXPORT COMPLETE")
    logger.info(f"Files saved to: {TABLEAU_DIR}")
    logger.info("=" * 60)
    
    print(f"\n✅ Tableau data exported to: {TABLEAU_DIR}")
    print("\nTo use in Tableau:")
    print("1. Open Tableau Desktop or Tableau Public")
    print("2. Connect to Text File")
    print("3. Select gdm_tableau_data.csv")
    print("4. Drag fields to create visualizations")

if __name__ == "__main__":
    export_for_tableau()
