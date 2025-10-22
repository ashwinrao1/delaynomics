# Delaynomics Web Dashboard

## Live Interactive Dashboard (No Tableau Needed!)

This is a fully-functional web dashboard built with **Plotly Dash** that replaces Tableau. You get all the visualizations embedded in your own web interface.

## Features

✅ **Interactive charts** - Hover, zoom, filter in real-time
✅ **Beautiful design** - Professional gradient UI with responsive layout
✅ **Fast performance** - Handles thousands of data points smoothly
✅ **No external dependencies** - Runs entirely on your machine
✅ **Easy deployment** - Can be deployed to cloud platforms
✅ **Mobile responsive** - Works on desktop, tablet, and mobile

## What You'll See

### KPI Cards
- 🏆 Best performing carrier (lowest cost/mile)
- ⚠️ Worst performing carrier
- 💰 Average delay cost per flight
- 📊 Total flights analyzed

### Interactive Charts
1. **Airline Efficiency Bar Chart** - Compare cost per mile across carriers
2. **Airport Performance** - Top 10 airports by delay cost
3. **Delay Rate vs Cost Scatter** - Correlation analysis
4. **Cost Comparison** - Average delay costs by carrier

### Filters
- Filter by carrier to compare specific airlines
- All charts update dynamically

---

## Quick Start

### Option 1: Using Sample Data (Fastest - 2 minutes)

```bash
# 1. Install dependencies
pip install pandas numpy dash plotly scikit-learn matplotlib seaborn jupyter

# 2. Generate sample data
cd notebooks
jupyter notebook generate_sample_data.ipynb
# Run all cells in the notebook

# 3. Run analysis
jupyter notebook analysis.ipynb
# Run all cells in the notebook

# 4. Launch dashboard
cd ..
python3 dashboard_app.py
```

**Access:** Open http://localhost:8050 in your browser

---

### Option 2: Using Real BTS Data (20 minutes)

```bash
# 1. Download BTS data
# Go to: https://catalog.data.gov/dataset/airline-on-time-performance-data
# Download CSV for one month, place in data/ folder

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run analysis
cd notebooks
jupyter notebook analysis.ipynb
# Run all cells

# 4. Launch dashboard
cd ..
python3 dashboard_app.py
```

---

### Option 3: One-Line Launch (if analysis already run)

```bash
./run_dashboard.sh
```

---

## Architecture

```
┌──────────────────────────────────────────────┐
│         Browser (http://localhost:8050)       │
│  ┌────────────────────────────────────────┐  │
│  │   Interactive Plotly.js Charts         │  │
│  │   - Bar charts                         │  │
│  │   - Scatter plots                      │  │
│  │   - KPI cards                          │  │
│  └────────────────────────────────────────┘  │
└────────────────┬─────────────────────────────┘
                 │ WebSocket / HTTP
                 ↓
┌──────────────────────────────────────────────┐
│       Dash Server (Python - Port 8050)        │
│  ┌────────────────────────────────────────┐  │
│  │   Callbacks & Interactivity            │  │
│  │   - Filter logic                       │  │
│  │   - Chart updates                      │  │
│  │   - Data transformations               │  │
│  └────────────────────────────────────────┘  │
└────────────────┬─────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────┐
│            Data Layer (CSV Files)             │
│  - outputs/airline_summary.csv                │
│  - outputs/airport_summary.csv                │
│  - outputs/full_dataset_for_tableau.csv       │
└──────────────────────────────────────────────┘
```

---

## Customization

### Change Colors

Edit [dashboard_app.py](dashboard_app.py), line ~150-180:

```python
# Change color scale
color_continuous_scale='RdYlGn_r'  # Red-Yellow-Green reversed

# Options:
# 'Viridis', 'Plasma', 'Inferno', 'Blues', 'Reds', 'Greens'
# 'RdBu', 'RdYlGn', 'Spectral', 'Turbo'
```

### Add New Charts

```python
@callback(
    Output('my-new-chart', 'figure'),
    Input('carrier-filter', 'value')
)
def update_my_chart(selected_carriers):
    # Your chart logic here
    fig = px.line(...)
    return fig
```

### Change Port

```python
# In dashboard_app.py, last line:
app.run_server(debug=True, host='0.0.0.0', port=8080)  # Change port here
```

---

## Deployment Options

### Option 1: Run Locally (Default)
```bash
python3 dashboard_app.py
# Access: http://localhost:8050
```

### Option 2: Deploy to Heroku (Free)

1. Create `Procfile`:
   ```
   web: gunicorn dashboard_app:server
   ```

2. Add to requirements.txt:
   ```
   gunicorn
   ```

3. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   ```

### Option 3: Deploy to Render (Free)

1. Push to GitHub
2. Go to https://render.com
3. New Web Service → Connect repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `python dashboard_app.py`

### Option 4: Deploy to AWS/GCP/Azure

Use Docker:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8050
CMD ["python", "dashboard_app.py"]
```

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'dash'"
```bash
pip install dash plotly
```

### "FileNotFoundError: outputs/airline_summary.csv"
You need to run the analysis first:
```bash
cd notebooks
jupyter notebook analysis.ipynb
# Run all cells
```

### Dashboard loads but shows errors
Check that CSV files have data:
```bash
wc -l outputs/*.csv
# Should show > 1 line (header + data)
```

### Port 8050 already in use
Change the port in dashboard_app.py:
```python
app.run_server(debug=True, port=8051)  # Use different port
```

### Charts not updating when filtering
Check browser console (F12) for JavaScript errors. Try refreshing the page.

---

## Performance Tips

### For Large Datasets (>1M rows)

1. **Use aggregated data only:**
   ```python
   # Don't load full_dataset_for_tableau.csv if it's huge
   flights_df = None
   ```

2. **Add caching:**
   ```python
   from dash import dcc

   @cache.memoize(timeout=300)  # Cache for 5 minutes
   def expensive_computation(data):
       # Your logic
   ```

3. **Sample data for scatter plots:**
   ```python
   sample_df = full_df.sample(n=10000)  # Use 10k random rows
   ```

---

## Advanced Features

### Add Date Range Filter

```python
dcc.DatePickerRange(
    id='date-range',
    start_date=df['Date'].min(),
    end_date=df['Date'].max()
)
```

### Add Download Button

```python
from dash import dcc

html.A(
    'Download Data',
    id='download-link',
    download="airline_data.csv",
    href="/download",
    target="_blank"
)
```

### Add Authentication

```python
import dash_auth

VALID_USERNAME_PASSWORD_PAIRS = {
    'admin': 'secret'
}

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)
```

---

## Comparison: Dash vs Tableau

| Feature | Plotly Dash (This) | Tableau |
|---------|-------------------|---------|
| **Cost** | Free | $70/month |
| **Customization** | Full control | Limited |
| **Python Integration** | Native | Via TabPy |
| **Deployment** | Anywhere | Tableau Server |
| **Mobile** | Responsive | Good |
| **Learning Curve** | Moderate | Moderate |
| **Interactivity** | Excellent | Excellent |

---

## File Structure

```
dashboard_app.py              # Main dashboard application
run_dashboard.sh              # Quick launcher script
requirements.txt              # Dependencies (includes dash, plotly)
outputs/
  ├── airline_summary.csv     # Data source
  ├── airport_summary.csv     # Data source
  └── full_dataset_for_tableau.csv  # Optional detailed data
```

---

## Tech Stack

- **Framework:** Plotly Dash 2.14+
- **Visualization:** Plotly.js 5.17+
- **Backend:** Flask (included with Dash)
- **Data:** Pandas DataFrames
- **Styling:** Custom CSS (embedded)

---

## Next Steps

1. ✅ **Launch the dashboard** - `python3 dashboard_app.py`
2. 📊 **Explore the visualizations** - Try the filters
3. 🎨 **Customize the design** - Edit colors, layout
4. 🚀 **Deploy to the web** - Share with stakeholders
5. 📈 **Add more features** - New charts, filters, etc.

---

## Screenshots

*(After running, take screenshots and add them here)*

### Dashboard Overview
![Dashboard](screenshots/dashboard.png)

### Airline Efficiency Chart
![Airline Chart](screenshots/airline_chart.png)

### Interactive Filters
![Filters](screenshots/filters.png)

---

## Support

- **Dash Documentation:** https://dash.plotly.com/
- **Plotly Documentation:** https://plotly.com/python/
- **Example Gallery:** https://dash-gallery.plotly.host/Portal/

---

## License

Open source - use and modify as needed.

---

**Ready to launch? Run:**
```bash
python3 dashboard_app.py
```

Then open http://localhost:8050 in your browser! 🚀
