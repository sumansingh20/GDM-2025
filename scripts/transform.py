import pandas as pd
import numpy as np
import re
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """Configure logging for data transformation pipeline."""
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger("DataTransform")
    logger.setLevel(logging.DEBUG)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(log_dir) / f"transform_{timestamp}.log"
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

# ============================================================================
# CONFIGURATION
# ============================================================================

INPUT_CSV = Path("data/raw_data.csv")
OUTPUT_CSV = Path("data/clean_data.csv")
DERIVED_CSV = Path("data/kpi_data.csv")

# ============================================================================
# UTILITY FUNCTIONS FOR VALUE NORMALIZATION
# ============================================================================

def normalize_numeric_value(value: str) -> Optional[float]:
    """
    Convert string value to numeric (handles millions, billions, etc.)
    
    Examples:
        "12,345" → 12345.0
        "1.5 Million" → 1500000.0
        "2.3 Billion" → 2300000000.0
    """
    if pd.isna(value) or value == "" or value == "-":
        return None
    
    value = str(value).strip()
    multiplier = 1.0
    
    # Check for multipliers
    if "billion" in value.lower():
        multiplier = 1_000_000_000
        value = re.sub(r'billion', '', value, flags=re.IGNORECASE)
    elif "million" in value.lower():
        multiplier = 1_000_000
        value = re.sub(r'million', '', value, flags=re.IGNORECASE)
    elif "thousand" in value.lower() or "k" in value.lower():
        multiplier = 1_000
        value = re.sub(r'(thousand|k)', '', value, flags=re.IGNORECASE)
    
    # Remove currency symbols, commas, and spaces
    value = re.sub(r'[\$€¥£,\s]', '', value)
    
    try:
        return float(value) * multiplier
    except ValueError:
        return None


def extract_numeric(value: str) -> Optional[float]:
    """Extract first numeric value from text."""
    if pd.isna(value) or value == "":
        return None
    
    match = re.search(r'[\d.]+', str(value))
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None

def normalize_personnel_value(value: str) -> Optional[float]:
    """Normalize military personnel counts."""
    return normalize_numeric_value(value)


def normalize_budget_value(value: str) -> Optional[float]:
    """Normalize defense budget values."""
    return normalize_numeric_value(value)


def normalize_gdp_value(value: str) -> Optional[float]:
    """Normalize GDP values."""
    return normalize_numeric_value(value)


def normalize_population_value(value: str) -> Optional[float]:
    """Normalize population values."""
    return normalize_numeric_value(value)


def normalize_equipment_count(value: str) -> Optional[int]:
    """Normalize equipment counts (aircraft, tanks, etc.)."""
    numeric = normalize_numeric_value(value)
    if numeric is not None:
        return int(numeric)
    return None

# ============================================================================
# DATA CLEANING FUNCTIONS
# ============================================================================

def load_raw_data(filepath: Path) -> pd.DataFrame:
    """Load raw data from CSV."""
    logger.info(f"Loading raw data from: {filepath}")
    
    if not filepath.exists():
        logger.error(f"Input file not found: {filepath}")
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    df = pd.read_csv(filepath, encoding='utf-8')
    logger.info(f"Loaded {len(df)} countries with {len(df.columns)} columns")
    
    return df


def identify_metric_columns(df: pd.DataFrame) -> Dict[str, list]:
    """
    Identify and categorize columns by metric type.
    """
    columns_by_type = {
        "equipment": [],
        "personnel": [],
        "financial": [],
        "other": []
    }
    
    equipment_keywords = ["aircraft", "tank", "helicopter", "submarine", "carrier", "vessel", "ship", "artillery", "launcher"]
    personnel_keywords = ["personnel", "active", "reserve", "manpower", "soldier", "troop"]
    financial_keywords = ["budget", "gdp", "spending", "expenditure", "revenue", "income"]
    
    for col in df.columns:
        col_lower = col.lower()
        
        if any(keyword in col_lower for keyword in equipment_keywords):
            columns_by_type["equipment"].append(col)
        elif any(keyword in col_lower for keyword in personnel_keywords):
            columns_by_type["personnel"].append(col)
        elif any(keyword in col_lower for keyword in financial_keywords):
            columns_by_type["financial"].append(col)
        else:
            columns_by_type["other"].append(col)
    
    logger.info(f"Identified metric columns: {columns_by_type}")
    return columns_by_type


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean raw data: normalize values, handle missing data.
    """
    logger.info("Starting data cleaning process...")
    
    df_clean = df.copy()
    
    # PRESERVE COUNTRY COLUMN
    if "Country" in df_clean.columns:
        country_col = df_clean["Country"].copy()
    else:
        country_col = None
    
    columns_by_type = identify_metric_columns(df_clean)
    
    # Clean equipment counts
    for col in columns_by_type["equipment"]:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(normalize_equipment_count)
    
    # Clean personnel counts
    for col in columns_by_type["personnel"]:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(normalize_personnel_value)
    
    # Clean financial values
    for col in columns_by_type["financial"]:
        if col in df_clean.columns:
            df_clean[col] = df_clean[col].apply(normalize_budget_value)
    
    # Clean other numeric columns
    for col in columns_by_type["other"]:
        if col not in ["country_name", "url", "Country"]:
            if col in df_clean.columns:
                df_clean[col] = df_clean[col].apply(extract_numeric)
    
    # RESTORE COUNTRY COLUMN if it was preserved
    if country_col is not None:
        df_clean["Country"] = country_col
    
    logger.info("Data cleaning completed")
    return df_clean


# ============================================================================
# DERIVED METRICS CALCULATION
# ============================================================================

def calculate_derived_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate advanced KPIs from base metrics.
    """
    logger.info("Calculating derived metrics...")
    
    df_derived = pd.DataFrame()
    # Handle both 'country_name' and 'Country' column names
    country_col = 'country_name' if 'country_name' in df.columns else 'Country'
    df_derived["country_name"] = df[country_col]
    
    # 1. POWER INDEX RANKING (simplified)
    # Approximate Power Index = sum of normalized metrics
    power_index_components = []
    
    for col in df.columns:
        if col not in ["country_name", "url", "Power Index Rank"]:
            if df[col].dtype in [np.float64, np.int64]:
                power_index_components.append(col)
    
    if power_index_components:
        # Normalize and sum
        normalized = df[power_index_components].fillna(0).apply(
            lambda x: (x - x.min()) / (x.max() - x.min() + 1) if (x.max() - x.min()) > 0 else 0
        )
        df_derived["Power Index Score"] = normalized.sum(axis=1)
    
    # 2. POWER INDEX RANK GAP (between rank 1 and country)
    if "Power Index Rank" in df.columns:
        df_derived["Power Index Rank"] = df["Power Index Rank"].apply(extract_numeric)
        df_derived["Power Index Rank Gap"] = df_derived["Power Index Rank"] - df_derived["Power Index Rank"].min()
    
    # 3. ASSETS PER CAPITA
    population_cols = [col for col in df.columns if "population" in col.lower()]
    equipment_cols = [col for col in df.columns if any(
        keyword in col.lower() for keyword in ["aircraft", "tank", "helicopter", "vessel"]
    )]
    
    if population_cols and equipment_cols:
        pop_col = population_cols[0]
        for eq_col in equipment_cols:
            assets_per_capita = df[eq_col] / (df[pop_col] + 1)
            df_derived[f"{eq_col}_per_capita"] = assets_per_capita
    
    # 4. DEFENSE BUDGET TO GDP RATIO
    budget_cols = [col for col in df.columns if "budget" in col.lower() and "gdp" not in col.lower()]
    gdp_cols = [col for col in df.columns if "gdp" in col.lower()]
    
    if budget_cols and gdp_cols:
        budget_col = budget_cols[0]
        gdp_col = gdp_cols[0]
        df_derived["Defense_Budget_to_GDP_Ratio"] = (df[budget_col] / (df[gdp_col] + 1)) * 100
    
    # 5. TOTAL MILITARY CAPABILITY SCORE
    equipment_cols = [col for col in df.columns if any(
        keyword in col.lower() for keyword in ["aircraft", "tank", "helicopter", "submarine", "carrier"]
    )]
    personnel_cols = [col for col in df.columns if "personnel" in col.lower() or "active" in col.lower()]
    
    if equipment_cols:
        equipment_score = df[equipment_cols].fillna(0).sum(axis=1)
        df_derived["Equipment_Total"] = equipment_score
    
    if personnel_cols:
        personnel_score = df[personnel_cols].fillna(0).sum(axis=1)
        df_derived["Personnel_Total"] = personnel_score
    
    # 6. MILITARY INTENSITY (military budget / population)
    if budget_cols and population_cols:
        budget_col = budget_cols[0]
        pop_col = population_cols[0]
        df_derived["Military_Spending_per_Capita"] = (df[budget_col] / (df[pop_col] + 1))
    
    logger.info(f"Created {len(df_derived.columns) - 1} derived metrics")
    
    return df_derived


# ============================================================================
# DATA VALIDATION
# ============================================================================

def validate_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and flag data quality issues.
    """
    logger.info("Validating data quality...")
    
    # Count missing values
    missing_counts = df.isnull().sum()
    missing_pct = (missing_counts / len(df) * 100).round(2)
    
    logger.info("Missing data summary:")
    for col, count in missing_counts[missing_counts > 0].items():
        logger.info(f"  {col}: {count} missing ({missing_pct[col]}%)")
    
    # Check for outliers
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        outliers = df[(df[col] < Q1 - 3*IQR) | (df[col] > Q3 + 3*IQR)][col].count()
        
        if outliers > 0:
            logger.warning(f"  {col}: {outliers} potential outliers detected")
    
    return df


# ============================================================================
# MAIN TRANSFORMATION PIPELINE
# ============================================================================

def run_transformation_pipeline() -> None:
    """Execute complete data cleaning and transformation."""
    logger.info("=" * 80)
    logger.info("STARTING DATA CLEANING & TRANSFORMATION PIPELINE")
    logger.info("=" * 80)
    
    try:
        # Load raw data
        df_raw = load_raw_data(INPUT_CSV)
        
        # Clean data
        df_clean = clean_data(df_raw)
        
        # Validate data
        df_clean = validate_data(df_clean)
        
        # Calculate derived metrics
        df_derived = calculate_derived_metrics(df_clean)
        
        # Save clean data
        df_clean.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        logger.info(f"✓ Clean data saved to: {OUTPUT_CSV}")
        
        # Save derived metrics
        df_derived.to_csv(DERIVED_CSV, index=False, encoding='utf-8')
        logger.info(f"✓ Derived metrics saved to: {DERIVED_CSV}")
        
        # Generate summary statistics
        logger.info("=" * 80)
        logger.info("DATA TRANSFORMATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Total countries processed: {len(df_clean)}")
        logger.info(f"Total columns in clean data: {len(df_clean.columns)}")
        logger.info(f"Total derived metrics: {len(df_derived.columns) - 1}")
        logger.info(f"Data completeness: {(1 - df_clean.isnull().sum().sum() / (len(df_clean) * len(df_clean.columns))) * 100:.2f}%")
        logger.info("=" * 80)
        logger.info("TRANSFORMATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.critical(f"Pipeline failed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    run_transformation_pipeline()
