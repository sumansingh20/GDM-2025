# Global Defense Metrics (GDM) – 2025
## Complete Military Data Analytics Platform

---

## Project Overview

The **Global Defense Metrics** platform is a comprehensive, end-to-end analytics system for analyzing global military power in 2025. The platform covers the complete data pipeline from web scraping to interactive visualization, processing military and economic data from GlobalFirepower.com for **144 countries**.

### Platform Modules

| Module | Script | Description |
|--------|--------|-------------|
| **Module 1** | `scraper.py` | Web scraping pipeline for data collection |
| **Module 2** | `transform.py` | Data cleaning, normalization & KPI calculation |
| **Module 3** | `app.py` | Interactive Streamlit dashboard |
| **Module 4** | `tableau_export.py` | Tableau data export with geo coordinates |

### Key Features

- **Dynamic Data Collection**: Reads URLs from configuration file; extracts metrics without hardcoding
- **Robust Error Handling**: Comprehensive try/except blocks with detailed logging
- **Data Transformation**: Normalizes currencies, units, and calculates derived KPIs
- **Interactive Dashboard**: Streamlit-based visualization with Plotly charts
- **Multi-Country Analysis**: Compare powers, build coalitions, analyze trends
- **Browser Simulation**: HTTP headers mimicking legitimate browser requests
- **Respectful Scraping**: Request delays to avoid overwhelming target servers

---

## Project Structure

```
d:\Miletry\
├── data/
│   ├── urls.txt              # Input: 144 country URLs
│   ├── raw_data.csv          # Module 1 Output: Scraped raw data
│   ├── clean_data.csv        # Module 2 Output: Cleaned data
│   ├── kpi_data.csv          # Module 2 Output: Derived KPIs
│   └── tableau/              # Module 4: Tableau files
│       ├── gdm_tableau_data.csv  # Main data with coordinates
│       └── gdm_summary.csv       # Summary metrics
│
├── scripts/
│   ├── scraper.py            # Module 1: Web scraping
│   ├── transform.py          # Module 2: Data transformation
│   ├── app.py                # Module 3: Streamlit dashboard
│   └── tableau_export.py     # Module 4: Tableau export
│
├── dashboard_preview.html    # Interactive HTML dashboard preview
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

---

## Installation & Setup

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Install Dependencies

```bash
cd d:\Miletry
pip install -r requirements.txt
```

**Dependencies:**
| Package | Purpose |
|---------|---------|
| `requests` | HTTP library for web scraping |
| `beautifulsoup4` + `lxml` | HTML parsing |
| `pandas` + `numpy` | Data manipulation |
| `streamlit` + `plotly` | Dashboard & visualization |
| `tqdm` | Progress bars |

### Step 2: Verify Input Data

The `data/urls.txt` file contains 144 GlobalFirepower URLs:

```
https://www.globalfirepower.com/country-military-strength-detail.php?country_id=united-states-of-america
https://www.globalfirepower.com/country-military-strength-detail.php?country_id=russia
https://www.globalfirepower.com/country-military-strength-detail.php?country_id=china
...
```

---

## Running the Pipeline

### Module 1: Data Collection (Scraper)

```bash
python scripts/scraper.py
```

**What Happens:**
1. Loads URLs from `data/urls.txt`
2. Scrapes each country with browser-like headers
3. Extracts country name and all metrics dynamically
4. Saves raw data to `data/raw_data.csv`
5. Logs progress and success rate

---

### Module 2: Data Transformation

```bash
python scripts/transform.py
```

**What Happens:**
1. Reads `data/raw_data.csv`
2. Normalizes numeric values (handles millions, billions, currencies)
3. Calculates derived KPIs (Power Index Gap, Assets per Capita, etc.)
4. Outputs `data/clean_data.csv` and `data/kpi_data.csv`

**Transformation Features:**
- Currency symbol removal (`$`, `€`, `¥`, `£`)
- Unit conversion (Million → 1,000,000, Billion → 1,000,000,000)
- Missing data handling
- Data validation and quality checks

---

### Module 3: Interactive Dashboard (Streamlit)

```bash
streamlit run scripts/app.py
```

**Dashboard Pages:**

| Page | Icon | Description |
|------|------|-------------|
| **Quick Stats** | 📊 | Global defense overview with aggregated metrics |
| **Nation Overview** | 🏛️ | Country-specific military profiles |
| **Compare Powers** | ⚖️ | Multi-country metric comparisons |
| **Coalition Builder** | 🤝 | Alliance strength simulation |

**Quick Stats Features:**
- Global totals: Aircraft, Personnel, Defense Budget
- Top 10 countries by defense budget (bar chart)
- Country count analysis

**Nation Overview Features:**
- Dropdown country selector
- Military profile: Aircraft, Fighters, Helicopters, Tanks
- Personnel and budget metrics
- Naval assets and population data

**Compare Powers Features:**
- Multi-select countries (2-5)
- Metric selector: Defense Budget, Aircraft, Personnel, Tanks
- Interactive bar chart comparison

**Coalition Builder Features:**
- Multi-select coalition members
- Aggregated coalition strength metrics
- Budget distribution pie chart

---

### Module 4: Tableau Dashboard

```bash
python scripts/tableau_export.py
```

**What Happens:**
1. Creates `data/tableau/` directory
2. Exports data with latitude/longitude for maps
3. Adds region classifications
4. Generates summary metrics

**Tableau Files Generated:**

| File | Description |
|------|-------------|
| `gdm_tableau_data.csv` | Main data with geo coordinates |
| `gdm_summary.csv` | Aggregated summary metrics |

**Next Steps:**
1. Open Tableau Desktop or Tableau Public
2. **Connect** → **Text File** → Select `gdm_tableau_data.csv`
3. Drag fields to create visualizations

---

### HTML Dashboard Preview

Open the instant preview dashboard in any browser:

```bash
start dashboard_preview.html
```

**Features:**
- 📊 Quick Stats with global totals
- 🏛️ Nation Overview with country selector
- ⚖️ Compare Powers with bar charts
- 🤝 Coalition Builder with pie charts
- No installation required - works in any browser

---

## Quick Start (Full Pipeline)

```bash
cd d:\Miletry
pip install -r requirements.txt
python scripts/scraper.py
python scripts/transform.py
streamlit run scripts/app.py
```

### For Tableau Users

```bash
python scripts/tableau_export.py
# Open Tableau → Connect → Text File → gdm_tableau_data.csv
```

### Instant Preview (No Installation)

```bash
start dashboard_preview.html
# Opens interactive dashboard in your browser
```

---

## Output Data Format

### `raw_data.csv` – Scraped Data
Contains one row per country with all metrics as found on GlobalFirepower:
- `country_name` – Country identifier
- `url` – Source URL
- All scraped metric columns (Total Aircraft, Tanks, Personnel, etc.)

### `clean_data.csv` – Normalized Data
Cleaned numeric values with standardized formatting:
- Currency symbols removed
- Units converted to base numbers
- Consistent column names

### `kpi_data.csv` – Derived Metrics
Calculated KPIs for advanced analysis:
- Power Index calculations
- Per-capita metrics
- Budget ratios

---

## Technical Implementation

### Scraper (`scraper.py`)

- **Session Management**: Connection pooling with retry logic
- **Headers**: Browser-like User-Agent to avoid blocking
- **Timeout**: 30 seconds per request
- **Delay**: 1 second between requests (respectful scraping)
- **Logging**: Dual output to console and `data/scraping_log.txt`

### Transformer (`transform.py`)

- **Normalization Functions**:
  - `normalize_numeric_value()` – Handles millions, billions, currencies
  - Regex-based cleaning and conversion
- **Logging**: Timestamped logs in `logs/` directory

### Dashboard (`app.py`)

- **Framework**: Streamlit with wide layout
- **Charts**: Plotly Express (bar charts, pie charts)
- **Data Loading**: Cached with `@st.cache_data`
- **Error Handling**: Graceful fallbacks for missing data

---

## Configuration

### Scraper Settings (`scraper.py`)

```python
REQUEST_TIMEOUT = 30      # seconds
REQUEST_DELAY = 1.0       # delay between requests
DATA_DIR = Path("data")
URLS_FILE = DATA_DIR / "urls.txt"
OUTPUT_CSV = DATA_DIR / "raw_data.csv"
```

### Transformer Settings (`transform.py`)

```python
INPUT_CSV = Path("data/raw_data.csv")
OUTPUT_CSV = Path("data/clean_data.csv")
DERIVED_CSV = Path("data/kpi_data.csv")
```

---

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `FileNotFoundError: urls.txt` | Ensure `data/urls.txt` exists |
| Low success rate | Check logs, verify URLs are valid |
| Empty dashboard | Run scraper and transformer first |
| Streamlit not launching | Check port 8501 is available |

### Log Files

- **Scraper logs**: `data/scraping_log.txt`
- **Transformer logs**: `logs/transform_YYYYMMDD_HHMMSS.log`

---

## Metrics Analyzed

The platform collects and analyzes metrics including:

**Military Assets:**
- Total Aircraft, Fighter Aircraft, Helicopters
- Tanks, Armored Vehicles, Artillery
- Naval Fleet, Submarines, Aircraft Carriers

**Personnel:**
- Active Personnel
- Reserve Personnel

**Economic:**
- Defense Budget (USD)
- GDP
- Total Population

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **v3.0** | Jan 2026 | Added Tableau export & HTML preview |
| **v2.0** | Jan 2026 | Full platform: Scraper + Transformer + Streamlit |
| **v1.0** | Jan 2025 | Initial scraping module |

---

## License & Attribution

**Global Defense Metrics (GDM) 2025**

Data sourced from [GlobalFirepower.com](https://www.globalfirepower.com) (publicly available military data)

---

## Author

GDM Analytics Team

