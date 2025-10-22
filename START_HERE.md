# 🚀 START HERE - Delaynomics Project

Welcome! This project answers: **"Which airlines deliver the best value for money?"**

---

## ⚡ Quick Start (Choose Your Path)

### Path A: Just Show Me the Dashboard! (5 minutes)

```bash
# 1. Install dependencies
pip install pandas numpy dash plotly scikit-learn matplotlib seaborn jupyter

# 2. Generate sample data
cd notebooks
jupyter notebook generate_sample_data.ipynb
# → Click "Run All" in Jupyter

# 3. Run analysis
jupyter notebook analysis.ipynb
# → Click "Run All" in Jupyter

# 4. Launch dashboard
cd ..
python3 dashboard_app.py
```

**Then open:** http://localhost:8050

---

### Path B: Use Real Flight Data (30 minutes)

```bash
# 1. Download data
# Go to: https://catalog.data.gov/dataset/airline-on-time-performance-data
# Download CSV → save to data/airline_ontime.csv

# 2. Run automated setup
./setup.sh

# 3. Run analysis
cd notebooks
jupyter notebook analysis.ipynb
# → Click "Run All"

# 4. Launch dashboard
cd ..
./run_dashboard.sh
```

---

## 📂 What's Inside?

### Core Files (Start Here)

| File | What It Does | When to Use |
|------|--------------|-------------|
| [START_HERE.md](START_HERE.md) | This file - your entry point | **Read first** |
| [QUICKSTART.md](QUICKSTART.md) | Fast 5-minute setup guide | Just want to run it |
| [DASHBOARD_README.md](DASHBOARD_README.md) | Dashboard guide & customization | Working with the web UI |
| [dashboard_app.py](dashboard_app.py) | **THE WEB DASHBOARD** | Run this for the UI |

### Documentation

| File | What It Does | When to Use |
|------|--------------|-------------|
| [README.md](README.md) | Full project documentation | Want complete details |
| [FRONTEND_ARCHITECTURE.md](FRONTEND_ARCHITECTURE.md) | Web architecture options | Building custom frontend |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Project overview & specs | Understanding the project |
| [TABLEAU_GUIDE.md](TABLEAU_GUIDE.md) | Tableau instructions (optional) | Using Tableau instead |

### Analysis Code

| File | What It Does | When to Use |
|------|--------------|-------------|
| [notebooks/analysis.ipynb](notebooks/analysis.ipynb) | **Main analysis pipeline** | Run this to process data |
| [notebooks/generate_sample_data.ipynb](notebooks/generate_sample_data.ipynb) | Creates test data | Testing without BTS data |

### Helper Scripts

| File | What It Does | When to Use |
|------|--------------|-------------|
| [setup.sh](setup.sh) | Auto-install everything | First time setup |
| [run_dashboard.sh](run_dashboard.sh) | Launch dashboard quickly | After analysis is done |
| [requirements.txt](requirements.txt) | Python dependencies | Installing packages |

---

## 🎯 What You'll Get

### Interactive Web Dashboard

```
┌─────────────────────────────────────────────────────┐
│  ✈️ Delaynomics Dashboard                           │
│  Which airlines deliver the best value for money?   │
├─────────────────────────────────────────────────────┤
│  🏆 Best: DL    ⚠️ Worst: B6    💰 Avg: $458        │
├──────────────────────────┬──────────────────────────┤
│  📊 Airline Efficiency    │  🏢 Airport Performance  │
│  (Interactive bar chart)  │  (Color-coded heatmap)   │
├──────────────────────────┴──────────────────────────┤
│  📈 Delay Rate vs Cost    │  💵 Cost Comparison      │
│  (Scatter with filters)   │  (Bar chart)             │
└─────────────────────────────────────────────────────┘
```

**Features:**
- ✅ Interactive filtering by airline
- ✅ Hover for detailed stats
- ✅ Zoom, pan, download charts
- ✅ Mobile responsive
- ✅ Professional design

---

## 🏗️ Architecture

### Option 1: Dashboard App (Recommended - What We Built)

```
Python Analysis → CSV Files → Dash Web App → Browser
     ↓              ↓            ↓            ↓
  analysis.ipynb   outputs/  dashboard_app.py  localhost:8050
```

**Benefits:**
- ✅ Full control over UI/UX
- ✅ No Tableau license needed
- ✅ Can deploy anywhere
- ✅ Reuses Python analysis code

### Option 2: Tableau (Alternative)

```
Python Analysis → CSV Files → Tableau Desktop → Dashboard
```

**Benefits:**
- ✅ Drag-and-drop interface
- ✅ Built-in chart gallery
- ⚠️ Costs $70/month
- ⚠️ Less customization

---

## 📊 What the Analysis Does

### Input
- Flight data (BTS or sample)
- Carriers, airports, delays, distances

### Process
1. **Clean data** - Remove cancelled flights, outliers
2. **Compute metrics** - Cost per mile, delay rates
3. **Aggregate** - Airline & airport summaries
4. **Analyze** - Regression (distance vs delay)
5. **Export** - CSV files for visualization

### Output
- `airline_summary.csv` - Efficiency by carrier
- `airport_summary.csv` - Performance by airport
- `full_dataset_for_tableau.csv` - Complete data
- **Web dashboard** - Interactive visualizations

---

## 💡 Key Insights You'll Discover

After running the analysis, you'll know:

1. **Which airline is most cost-efficient?**
   - Measured by: Cost per mile
   - Example: "Delta: $0.46/mile vs JetBlue: $0.84/mile"

2. **Which airports have worst delays?**
   - Measured by: Average delay cost
   - Identifies operational bottlenecks

3. **Does distance predict delays?**
   - Measured by: R² from regression
   - Understanding delay patterns

4. **What's the economic impact?**
   - Measured by: Total delay costs
   - Business case for improvements

---

## 🛠️ Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| **Frontend** | Plotly Dash + HTML/CSS | Interactive charts without JavaScript coding |
| **Backend** | Python + Flask (via Dash) | Reuse analysis code |
| **Analysis** | Pandas + NumPy + scikit-learn | Industry standard for data science |
| **Visualization** | Plotly.js | Publication-quality interactive charts |
| **Data** | CSV files | Simple, portable, no database needed |

---

## 🎓 Learn By Doing

### Beginner Path
1. Run sample data pipeline
2. Launch dashboard, explore filters
3. Read DASHBOARD_README.md
4. Customize colors/layout

### Intermediate Path
1. Download real BTS data
2. Run full analysis
3. Deploy dashboard to cloud
4. Add new charts/metrics

### Advanced Path
1. Multi-month time series
2. Add weather data integration
3. Build predictive ML models
4. Real-time data pipeline

---

## 🚢 Deployment Options

### Local (Default)
```bash
python3 dashboard_app.py
# Access: http://localhost:8050
```

### Cloud (Free Options)
- **Heroku** - `git push heroku main`
- **Render** - Connect GitHub repo
- **Railway** - One-click deploy
- **AWS/GCP/Azure** - Docker container

See [DASHBOARD_README.md](DASHBOARD_README.md) for detailed deployment instructions.

---

## 🐛 Common Issues

### "Module not found"
```bash
pip install -r requirements.txt
```

### "CSV file not found"
Run the analysis notebook first:
```bash
cd notebooks
jupyter notebook analysis.ipynb
```

### "Port 8050 in use"
Change port in dashboard_app.py:
```python
app.run_server(port=8051)
```

### Charts not loading
Clear browser cache and refresh (Cmd+Shift+R / Ctrl+Shift+R)

---

## 📈 Project Status

| Component | Status | Action |
|-----------|--------|--------|
| Python Analysis | ✅ Complete | Run analysis.ipynb |
| Sample Data Generator | ✅ Complete | Run generate_sample_data.ipynb |
| Web Dashboard | ✅ Complete | Run dashboard_app.py |
| Documentation | ✅ Complete | Read START_HERE.md |
| Tableau Alternative | ✅ Complete | See TABLEAU_GUIDE.md |

**Next Step:** Run the Quick Start above! ⬆️

---

## 🎯 Success Checklist

After setup, you should be able to:

- [ ] Run analysis on sample or real data
- [ ] See 3-5 carriers ranked by efficiency
- [ ] View 10 airports with delay metrics
- [ ] Access web dashboard at localhost:8050
- [ ] Filter charts by carrier
- [ ] Understand which airline offers best value

If all checked ✅ - **you're done!**

---

## 🤝 Next Steps

### Today
1. ✅ Follow Quick Start (Path A or B)
2. ✅ Launch dashboard
3. ✅ Explore visualizations

### This Week
1. Customize dashboard design
2. Add your own charts
3. Deploy to cloud (optional)

### This Month
1. Expand to multi-month data
2. Add predictive models
3. Share with stakeholders

---

## 📚 Additional Resources

- **Dash Docs:** https://dash.plotly.com/
- **Plotly Gallery:** https://plotly.com/python/
- **BTS Data:** https://catalog.data.gov/dataset/airline-on-time-performance-data
- **FAA Delay Costs:** https://www.faa.gov/

---

## 🎉 You're Ready!

**Quick Command Reference:**

```bash
# Generate sample data
cd notebooks && jupyter notebook generate_sample_data.ipynb

# Run analysis
jupyter notebook analysis.ipynb

# Launch dashboard
cd .. && python3 dashboard_app.py

# Quick launch (after analysis)
./run_dashboard.sh
```

**Need help?** Check the relevant guide:
- Web dashboard → [DASHBOARD_README.md](DASHBOARD_README.md)
- Quick setup → [QUICKSTART.md](QUICKSTART.md)
- Full details → [README.md](README.md)

---

**Let's go! Start with the Quick Start above** ⬆️
