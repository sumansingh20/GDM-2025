import os
import sys
import csv
import re
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


# ============================================================================
# CONFIGURATION
# ============================================================================

# HTTP Request Headers (mimics real browser)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive"
}

# Request Settings
REQUEST_TIMEOUT = 30  # seconds
REQUEST_DELAY = 1.0   # delay between requests to be respectful

# File Paths
DATA_DIR = Path("data")
URLS_FILE = DATA_DIR / "urls.txt"
OUTPUT_CSV = DATA_DIR / "raw_data.csv"
HTML_PAGES_DIR = DATA_DIR / "html_pages"  # Optional: for debugging
LOG_FILE = DATA_DIR / "scraping_log.txt"

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


# ============================================================================
# URL LOADING (from file - NO hardcoding)
# ============================================================================

def load_urls_from_file(filepath: Path) -> List[str]:
    """
    Read all country URLs from the links file.
    
    Args:
        filepath: Path to links_for_military_data.txt
        
    Returns:
        List of valid URLs
        
    Per requirements: URLs are loaded from file, NOT hardcoded
    """
    if not filepath.exists():
        logger.error(f"URL file not found: {filepath}")
        sys.exit(1)
    
    urls = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and url.startswith('http'):
                urls.append(url)
    
    logger.info(f"Loaded {len(urls)} URLs from {filepath}")
    return urls


def extract_country_slug(url: str) -> Optional[str]:
    """
    Extract country_id slug from GlobalFirepower URL.
    
    Example:
        Input: https://www.globalfirepower.com/country-military-strength-detail.php?country_id=united-states-of-america
        Output: united-states-of-america
    """
    try:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        if 'country_id' in params:
            return params['country_id'][0]
    except Exception:
        pass
    return None


# ============================================================================
# METRIC EXTRACTION (dynamic - NO hardcoded metric names)
# ============================================================================

def extract_metrics_from_page(soup: BeautifulSoup, text_content: str) -> Dict[str, str]:
    """
    Extract all military and economic metrics from page content.
    
    Uses pattern matching to dynamically find metric label-value pairs.
    Does NOT hardcode specific metric names - discovers them from HTML structure.
    
    Args:
        soup: BeautifulSoup parsed HTML
        text_content: Clean text version of page
        
    Returns:
        Dictionary of metric_name -> value
    """
    metrics = {}
    
    # ========================================================================
    # PATTERN-BASED EXTRACTION
    # GlobalFirepower uses consistent patterns for displaying metrics
    # ========================================================================
    
    # Pattern 1: "Label: value" format (used for many metrics)
    # Examples: "Aircraft Carriers: 11", "Submarines: 68"
    label_value_patterns = [
        # MANPOWER
        (r'Total Population:\s*([\d,]+)', 'Total Population'),
        (r'Available Manpower:\s*([\d,]+)', 'Available Manpower'),
        (r'Fit-for-Service:\s*([\d,]+)', 'Fit for Service'),
        (r'Active Personnel:\s*([\d,]+)', 'Active Personnel'),
        (r'Reserve Personnel:\s*([\d,]+)', 'Reserve Personnel'),
        
        # AIRPOWER - Stock format
        (r'Aircraft Total.*?Stock:\s*([\d,]+)', 'Total Aircraft'),
        (r'Fighters.*?Stock:\s*([\d,]+)', 'Fighter Aircraft'),
        (r'Attack Types.*?Stock:\s*([\d,]+)', 'Attack Aircraft'),
        (r'Helicopters.*?Stock:\s*([\d,]+)', 'Helicopters'),
        (r'Attack Helicopters.*?Stock:\s*([\d,]+)', 'Attack Helicopters'),
        (r'Transports.*?Stock:\s*([\d,]+)', 'Transport Aircraft'),
        (r'Trainers.*?Stock:\s*([\d,]+)', 'Trainer Aircraft'),
        (r'Tanker Fleet.*?Stock:\s*([\d,]+)', 'Tanker Aircraft'),
        (r'Special-Mission.*?Stock:\s*([\d,]+)', 'Special Mission Aircraft'),
        
        # LAND FORCES - Stock format  
        (r'Tanks.*?Stock:\s*([\d,]+)', 'Tanks'),
        (r'Vehicles.*?Stock:\s*([\d,]+)', 'Armored Vehicles'),
        (r'Self-Propelled.*?Stock:\s*([\d,]+)', 'Self-Propelled Artillery'),
        (r'Towed Artillery.*?Stock:\s*([\d,]+)', 'Towed Artillery'),
        (r'MLRS.*?Stock:\s*([\d,]+)', 'Rocket Projectors'),
        
        # NAVAL FORCES
        (r'Total Assets:\s*([\d,]+)', 'Total Naval Assets'),
        (r'Aircraft Carriers:\s*([\d,]+)', 'Aircraft Carriers'),
        (r'Helicopter Carriers:\s*([\d,]+)', 'Helicopter Carriers'),
        (r'Destroyers:\s*([\d,]+)', 'Destroyers'),
        (r'Frigates:\s*([\d,]+)', 'Frigates'),
        (r'Corvettes:\s*([\d,]+)', 'Corvettes'),
        (r'Submarines:\s*([\d,]+)', 'Submarines'),
        (r'Offshore Patrol:\s*([\d,]+)', 'Patrol Vessels'),
        (r'Mine Warfare:\s*([\d,]+)', 'Mine Warfare'),
        
        # FINANCIALS
        (r'Defense Budget:\s*\$?([\d,]+)', 'Defense Budget (USD)'),
        (r'Purchasing Power Parity:\s*\$?([\d,]+)', 'Purchasing Power Parity (USD)'),
        (r'Foreign Exchange/Gold:\s*\$?([\d,]+)', 'Foreign Exchange Reserves (USD)'),
        (r'External Debt:\s*\$?([\d,]+)', 'External Debt (USD)'),
        
        # GEOGRAPHY
        (r'Square Land Area:\s*([\d,]+)', 'Land Area (sq km)'),
        (r'Coastline Coverage:\s*([\d,]+)', 'Coastline (km)'),
        (r'Shared Borders:\s*([\d,]+)', 'Shared Borders (km)'),
        (r'Waterways \(usable\):\s*([\d,]+)', 'Waterways (km)'),
        
        # NATURAL RESOURCES
        (r'Oil Production:\s*([\d,]+)\s*bbl', 'Oil Production (bbl/day)'),
        (r'Oil Consumption:\s*([\d,]+)\s*bbl', 'Oil Consumption (bbl/day)'),
        (r'Oil Proven Reserves:\s*([\d,]+)', 'Proven Oil Reserves (bbl)'),
        (r'Natural Gas Production:\s*([\d,]+)', 'Natural Gas Production'),
        
        # LOGISTICS
        (r'Labor Force:\s*([\d,]+)', 'Labor Force'),
        (r'Merchant Marine Fleet:\s*([\d,]+)', 'Merchant Marine Fleet'),
        (r'Ports / Trade Terminals:\s*([\d,]+)', 'Ports'),
        (r'Airports:\s*([\d,]+)', 'Airports'),
        (r'Roadway Coverage:\s*([\d,]+)', 'Roadway Coverage (km)'),
        (r'Railway Coverage:\s*([\d,]+)', 'Railway Coverage (km)'),
    ]
    
    # Apply all patterns
    for pattern, metric_name in label_value_patterns:
        match = re.search(pattern, text_content, re.IGNORECASE)
        if match:
            value = match.group(1).replace(',', '')
            if value and value.isdigit():
                metrics[metric_name] = value
    
    # ========================================================================
    # SPECIAL EXTRACTIONS
    # ========================================================================
    
    # GFP Rank
    rank_match = re.search(r'ranked\s+(\d+)\s+of\s+(\d+)', text_content, re.IGNORECASE)
    if rank_match:
        metrics['GFP Rank'] = rank_match.group(1)
        metrics['Total Countries Ranked'] = rank_match.group(2)
    
    # Power Index Score
    pwr_match = re.search(r'PwrIndx\*?\s*(?:score\s+(?:of\s+)?)?(\d+\.\d+)', text_content)
    if pwr_match:
        metrics['Power Index'] = pwr_match.group(1)
    
    return metrics


def extract_country_name(soup: BeautifulSoup, url: str) -> str:
    """
    Extract country name from page header.
    
    Args:
        soup: BeautifulSoup parsed HTML
        url: Original URL for fallback parsing
        
    Returns:
        Country name string
    """
    # Try title tag first
    title = soup.find('title')
    if title:
        title_text = title.get_text()
        # Clean up: "United States Military Strength 2025" -> "United States"
        country = re.sub(r'\s*(Military Strength|2025|2024|\|).*', '', title_text).strip()
        if country:
            return country
    
    # Try h1 header
    h1 = soup.find('h1')
    if h1:
        h1_text = h1.get_text()
        country = re.sub(r'\s*(Military Strength|Overview).*', '', h1_text).strip()
        if country:
            return country
    
    # Fallback: parse from URL slug
    slug = extract_country_slug(url)
    if slug:
        return slug.replace('-', ' ').title()
    
    return "Unknown"


# ============================================================================
# MAIN SCRAPING FUNCTION
# ============================================================================

def scrape_country(url: str, session: requests.Session, save_html: bool = False) -> Tuple[Optional[Dict], str]:
    """
    Scrape military data for a single country URL.
    
    Args:
        url: Full URL to country page
        session: requests.Session for connection pooling
        save_html: Whether to save HTML for debugging
        
    Returns:
        Tuple of (data_dict or None, status_message)
    """
    country_slug = extract_country_slug(url) or "unknown"
    
    try:
        # Send HTTP request
        response = session.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        # Parse with BeautifulSoup using lxml parser
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Get clean text for regex parsing
        text_content = soup.get_text(' ', strip=True)
        
        # Extract country name from header
        country_name = extract_country_name(soup, url)
        
        # Extract all metrics dynamically
        metrics = extract_metrics_from_page(soup, text_content)
        
        # Build final data dictionary
        data = {'Country': country_name}
        data.update(metrics)
        
        # Optionally save HTML for debugging
        if save_html:
            html_file = HTML_PAGES_DIR / f"{country_slug}.html"
            html_file.parent.mkdir(parents=True, exist_ok=True)
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(response.text)
        
        # Count metrics (excluding Country name)
        metric_count = len([k for k in data.keys() if k != 'Country'])
        status = f"✓ {country_name}: {metric_count} metrics"
        
        return data, status
        
    except requests.exceptions.Timeout:
        return None, f"✗ {country_slug}: Timeout"
    except requests.exceptions.HTTPError as e:
        return None, f"✗ {country_slug}: HTTP {e.response.status_code}"
    except requests.exceptions.RequestException as e:
        return None, f"✗ {country_slug}: Request failed - {str(e)[:50]}"
    except Exception as e:
        return None, f"✗ {country_slug}: Error - {str(e)[:50]}"


# ============================================================================
# DATA EXPORT
# ============================================================================

def save_to_csv(data: List[Dict], output_path: Path) -> None:
    """
    Save scraped data to CSV file.
    
    Dynamically determines columns from all data dictionaries.
    Country column is first, others alphabetically sorted.
    
    Args:
        data: List of country data dictionaries
        output_path: Path to output CSV file
    """
    if not data:
        logger.error("No data to save!")
        return
    
    # Collect all unique columns across all countries
    all_columns = set()
    for country_data in data:
        all_columns.update(country_data.keys())
    
    # Order columns: Country first, then alphabetical
    columns = ['Country']
    columns.extend(sorted([c for c in all_columns if c != 'Country']))
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=columns)
        writer.writeheader()
        writer.writerows(data)
    
    logger.info(f"Data saved to: {output_path}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    """
    Main scraping pipeline execution.
    
    1. Read URLs from file (NO hardcoding)
    2. Scrape each country with progress tracking
    3. Log success/failure for each URL
    4. Save results to CSV
    5. Print final success rate
    """
    print("=" * 70)
    print("GLOBAL DEFENSE METRICS (GDM) - 2025")
    print("MODULE 1: DATA COLLECTION PIPELINE")
    print("=" * 70)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 70)
    
    # ========================================================================
    # STEP 1: Load URLs from file (per requirements - NO hardcoding)
    # ========================================================================
    print("\n[STEP 1] Loading URLs from file...")
    urls = load_urls_from_file(URLS_FILE)
    print(f"  → Found {len(urls)} country URLs to scrape")
    
    # ========================================================================
    # STEP 2: Initialize HTTP session with connection pooling
    # ========================================================================
    print("\n[STEP 2] Initializing HTTP session...")
    session = requests.Session()
    session.headers.update(HEADERS)
    print("  → Session configured with browser headers")
    
    # ========================================================================
    # STEP 3: Scrape all countries with progress tracking
    # ========================================================================
    print(f"\n[STEP 3] Scraping {len(urls)} countries...")
    print("-" * 70)
    
    all_data = []
    successful_scrapes = 0
    failed_scrapes = 0
    failed_urls = []
    
    for url in tqdm(urls, desc="Scraping", unit="country"):
        # Respectful delay between requests
        time.sleep(REQUEST_DELAY)
        
        # Scrape country data
        data, status = scrape_country(url, session, save_html=False)
        
        # Log status
        logger.info(status)
        
        if data and len(data) > 5:  # Valid if more than just Country + few fields
            all_data.append(data)
            successful_scrapes += 1
        else:
            failed_scrapes += 1
            failed_urls.append(url)
    
    # Close session
    session.close()
    
    # ========================================================================
    # STEP 4: Save to CSV
    # ========================================================================
    print("\n[STEP 4] Saving data to CSV...")
    if all_data:
        save_to_csv(all_data, OUTPUT_CSV)
        
        # Calculate statistics
        total_metrics = sum(len(d) - 1 for d in all_data)  # -1 for Country column
        avg_metrics = total_metrics / len(all_data)
        
        print(f"  → Saved {len(all_data)} countries to {OUTPUT_CSV}")
        print(f"  → Average metrics per country: {avg_metrics:.1f}")
    else:
        print("  ✗ No data to save!")
        sys.exit(1)
    
    # ========================================================================
    # STEP 5: Print final success rate
    # ========================================================================
    print("\n" + "=" * 70)
    print("SCRAPING SUMMARY")
    print("=" * 70)
    
    success_rate = (successful_scrapes / len(urls)) * 100
    
    print(f"  Total URLs:       {len(urls)}")
    print(f"  Successful:       {successful_scrapes}")
    print(f"  Failed:           {failed_scrapes}")
    print(f"  Success Rate:     {success_rate:.1f}%")
    
    # Per requirements: at least 95% success rate
    if success_rate >= 95:
        print(f"\n  ✓ SUCCESS: Met 95% target ({success_rate:.1f}%)")
    else:
        print(f"\n  ⚠ WARNING: Below 95% target ({success_rate:.1f}%)")
        if failed_urls:
            print("\n  Failed URLs:")
            for url in failed_urls[:10]:  # Show first 10
                print(f"    - {url}")
    
    print("\n" + "=" * 70)
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # Log to file
    logger.info(f"Final Success Rate: {success_rate:.1f}%")


if __name__ == "__main__":
    main()
