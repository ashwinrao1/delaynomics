# Delaynomics: Airline Delay Economics Analysis

**"Which Airlines Deliver the Best Value for Money?"**

An interactive data-driven analysis of flight delay costs and efficiency using Python, Dash, and advanced visualizations including a comprehensive US flight network map.

## Project Overview

This project translates flight delay data into economic efficiency metrics to determine which airlines and airports offer the best "value for money" in on-time performance. By combining operational data with economic analysis, we answer the question: **Which carriers minimize the cost impact of delays per mile flown?**

## Business Question

> *Which airlines and airports offer the best "value for money" in on-time performance?*

## Key Metrics

- **delay_cost**: Economic cost of delays (passenger-focused by default: $47.10/hour — see FAA source below). The project also exports an operator-focused cost measure where relevant.
- **cost_per_mile**: Normalized efficiency metric (delay cost / distance, with optional sqrt-distance normalization to reduce short-haul bias)
- **delay_rate**: Percentage of flights with delays > 15 minutes
- **avg_delay_per_flight**: Mean arrival delay in minutes

## Tech Stack

| Purpose | Tool |
|---------|------|
| Data loading, cleaning, and analysis | Python (pandas, numpy) |
| Interactive Dashboard | Dash/Plotly |
| Geographic Visualization | Plotly Scattergeo (US flight network map) |
| AI-Powered Insights | Google Gemini API |
| Statistical modeling | scikit-learn |
| Notebook environment | Jupyter |

## Project Structure

```
Delaynomics/
├── data/                           # Raw data files
│   ├── airline_ontime.csv         # BTS data (download separately)
│   └── airport_coords.csv         # Airport coordinates for mapping
├── notebooks/
│   └── analysis.ipynb             # Main analysis notebook
├── outputs/                        # Generated analysis files
│   ├── airline_summary.csv        # Airline-level metrics
│   ├── airport_summary.csv        # Airport-level metrics
│   ├── route_summary.csv          # Route-level analysis
│   └── full_dataset_for_tableau.csv # Complete dataset (5.4M flights)
├── dashboard_app_enhanced.py       # Interactive Dash dashboard
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Download Data

**Source:** [Bureau of Transportation Statistics - Airline On-Time Performance](https://catalog.data.gov/dataset/airline-on-time-performance-data)

**Required fields:**
- `Carrier` (airline code)
- `Origin`, `Dest` (airport codes)
- `ArrDelay`, `DepDelay` (in minutes)
- `Distance` (in miles)
- `Month`, `Year`
- `Cancelled`, `Diverted`

**For MVP:** Download a single month (e.g., January 2024)

Place the CSV file in the `data/` directory and update the filename in the notebook.

### 3. Run the Analysis

```bash
cd notebooks
jupyter notebook analysis.ipynb
```

Run all cells in order. The notebook will:
1. Load and clean the data
2. Compute economic metrics
3. Generate airline and airport summaries
4. Perform regression analysis
5. Export CSV files for Tableau

### 4. Launch Interactive Dashboard

```bash
python dashboard_app_enhanced.py
```

Open your browser to `http://localhost:8050` to explore the interactive dashboard featuring:
- **US Flight Network Map**: Geographic visualization of 300+ routes
- **AI-Powered Insights**: Gemini-generated analysis and recommendations
- **Route Performance Matrix**: Efficiency analysis by distance and frequency
- **Hub Connectivity Analysis**: Airport network performance
- **Interactive Filtering**: Real-time carrier and route filtering

## Analysis Pipeline

### Step 1: Data Cleaning
- Remove cancelled and diverted flights
- Filter out missing values
- Remove extreme outliers (delays > 500 min or < -60 min)
- Subset to top 5 carriers and top 10 airports

### Step 2: Feature Engineering

This project computes both passenger- and operator-focused delay costs so you can pick the view that matches your audience.

- **delay_cost (passenger VOT)** = ArrDelay × $47.10 (FAA passenger Value-of-Time, default — see citation below)
- **delay_cost (operator / FAA system)** = ArrDelay × operator_cost_per_minute (configurable; historically higher values have been used for system/operator impact)
- **cost_per_mile** = delay_cost / Distance (the notebook applies a sqrt-distance normalization by default to avoid over-penalizing short-haul flights; you can change this)
- **is_delayed** = 1 if ArrDelay > 15 minutes

### Step 3: Aggregation
- **Airline-level**: Mean delay, cost per mile, delay rate
- **Airport-level**: Mean delay, total delay cost, efficiency

### Step 4: Regression Analysis
Simple linear regression testing: **Does flight distance predict arrival delay?**

Model: `ArrDelay ~ Distance`

Interpretation:
- **Slope**: Extra delay minutes per 100 miles flown
- **R²**: How well distance explains delay variability
- Expected result: Low R² (distance is weak predictor; other factors dominate)

### Step 5: Export for Visualization
Generate summary CSV files for Tableau dashboard creation.

## Interactive Dashboard Features

### Main Visualizations

| Component | Description | Key Insights |
|-----------|-------------|--------------|
| **KPI Cards** | Best/worst carriers, average costs, total flights | Quick performance overview |
| **AI Insights** | Gemini-powered analysis and recommendations | Data-driven insights and travel tips |
| **Cost Efficiency Ranking** | Horizontal bar chart of cost per mile | Which airlines deliver best value |
| **US Flight Network Map** | Geographic route visualization with 300+ routes | Network patterns and route efficiency |
| **Airport Performance** | Delay costs by origin airport | Geographic delay hotspots |
| **Efficiency Matrix** | Delay rate vs cost efficiency scatter plot | Performance quadrant analysis |
| **Route Performance Matrix** | Distance vs frequency analysis | Route type efficiency patterns |
| **Hub Connectivity Network** | Airport network size vs efficiency | Hub performance analysis |
| **Day of Week Analysis** | Delay patterns by day | When to fly for best performance |
| **Interactive Chatbot** | AI-powered Q&A about the data | Natural language data exploration |

### Advanced Features
- **Real-time Filtering**: Interactive airline selection with visual feedback
- **Geographic Network Mapping**: Curved flight paths sized by delay cost and colored by severity
- **Smart Route Selection**: Mixed strategy showing high-cost, high-volume, and diverse routes
- **Comprehensive Airport Coverage**: 329+ airports with precise coordinates
- **Responsive Design**: Mobile-friendly interface with premium styling

### Dashboard Layout

```
┌─────────────────────────────────────────────────────┐
│  TITLE: Airline Delay Economics                     │
├─────────────────────────────────────────────────────┤
│  [KPI: Best Carrier] [KPI: Avg Cost] [KPI: Total $] │
├──────────────────────────┬──────────────────────────┤
│                          │                          │
│  BAR CHART:              │  HEATMAP:                │
│  Avg Delay Cost          │  Airport vs Carrier      │
│  by Airline              │  Delay Costs             │
│  (Sorted)                │                          │
│                          │                          │
├──────────────────────────┴──────────────────────────┤
│  SCATTER PLOT: Cost per Mile vs Delay Rate          │
├─────────────────────────────────────────────────────┤
│  FILTERS: [Airline] [Airport] [Month]               │
└─────────────────────────────────────────────────────┘
```

### Visual Design Notes
- Use currency formatting (`$`) for all cost metrics
- Apply color gradient: green (efficient) → red (costly)
- Add text annotations for key insights
- Include data source and date range in footer

## Key Insights Template

After running the analysis, you'll be able to answer:

1. **Which airline has the lowest cost per mile?**
   - Metric: `avg_cost_per_mile` from airline_summary

2. **Which airport is most efficient?**
   - Metric: `avg_delay_cost` from airport_summary

3. **Does distance predict delays?**
   - Metric: R² from regression analysis
   - Expected: Low correlation (distance is weak predictor)

4. **What's the economic impact?**
   - Metric: `total_delay_cost` across all flights

## Sample Insights (Once Analysis is Run)

```
🏆 BEST CARRIER: [Carrier Code]
   • Avg delay: X.X minutes
   • Cost per mile: $X.XX
   • Delay rate: XX.X%

⚠️ WORST CARRIER: [Carrier Code]
   • Avg delay: X.X minutes
   • Cost per mile: $X.XX
   • Delay rate: XX.X%

💰 VALUE GAP: [Worst] costs $X.XX more per mile than [Best]
   That's XX% higher cost per mile!
```

## Extensions & Future Work

- **Multi-month analysis**: Identify seasonal trends
- **Weather integration**: Add weather data as predictor
- **Route-level analysis**: Analyze specific city pairs
- **Predictive modeling**: Build ML model to forecast delays
- **Real-time dashboard**: Connect to live flight data APIs

## Data Source

**Bureau of Transportation Statistics (BTS)**
- Official source: https://catalog.data.gov/dataset/airline-on-time-performance-data
- Update frequency: Monthly
- Coverage: All domestic US flights

## FAA Cost Estimates (Value-of-Time)

For customer-facing comparisons this project uses the FAA's published passenger Value-of-Time (VOT) estimate:

- **$47.10 per minute** (FAA passenger VOT estimate)

We also expose an operator/system-level cost metric if you want to view the analysis from the airline or infrastructure perspective. Historically some internal analyses reference higher per-minute operational costs (for example, $74/min), but that represents a different aggregation of airline and system impacts.

Source / citation (FAA VOT):

https://www.faa.gov/sites/faa.gov/files/regulations_policies/policy_guidance/benefit_cost/econ-value-section-1-tx-time.pdf

The dashboard footer links to the FAA document so users can inspect the source directly. If you prefer a different VOT (leisure vs business travellers), change the parameter in the notebook where cost-per-minute is defined.

## License

This project is for educational and analytical purposes. The BTS data is public domain.

## Author

Built as an MVP for exploring airline operational efficiency through economic metrics.

## Deliverables

- [x] [analysis.ipynb](notebooks/analysis.ipynb) - Python notebook with full pipeline
- [x] [dashboard_app_enhanced.py](dashboard_app_enhanced.py) - Interactive Dash dashboard
- [x] [airline_summary.csv](outputs/airline_summary.csv) - Airline performance metrics
- [x] [airport_summary.csv](outputs/airport_summary.csv) - Airport performance metrics
- [x] [route_summary.csv](outputs/route_summary.csv) - Route-level analysis
- [x] [full_dataset_for_tableau.csv](outputs/full_dataset_for_tableau.csv) - Complete dataset (5.4M flights)
- [x] [airport_coords.csv](data/airport_coords.csv) - Geographic coordinates for 329+ airports
- [x] [requirements.txt](requirements.txt) - Python dependencies
- [x] [README.md](README.md) - Project documentation

## Questions?

For issues or questions about this analysis:
1. Check the notebook comments
2. Review the data cleaning steps
3. Ensure your BTS data has all required columns

---

**Project Status:** ✅ Complete - Interactive dashboard with AI insights and geographic network visualization

**Last Updated:** October 2024

## Quick Start

1. `pip install -r requirements.txt`
2. `python dashboard_app_enhanced.py`
3. Open `http://localhost:8050`
4. Explore 5.4M flights across 329 airports with AI-powered insights!
