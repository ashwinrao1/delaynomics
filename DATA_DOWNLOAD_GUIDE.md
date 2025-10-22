# 📥 How to Download Real BTS Flight Data

## Quick Steps

### 1️⃣ Go to the BTS Website

**Option A: Direct Link (Recommended)**
```
https://www.transtats.bts.gov/DL_SelectFields.aspx?gnoyr_VQ=FGJ&QO_fu146_anzr=b0-gvzr
```

**Option B: Manual Navigation**
1. Go to: https://www.transtats.bts.gov/
2. Click "Aviation" → "Airline On-Time Performance Data"
3. Click "Download"

---

### 2️⃣ Select Your Data

#### **Geography & Time Period:**
- **Geography:** All
- **Year:** 2024 (or your preferred year)
- **Period:** January (pick one month for testing)
  - **Tip:** Start with 1 month (~500K rows). One month downloads in ~30 seconds.

#### **Select Variables (IMPORTANT!):**

You need these specific columns. Check these boxes:

**✅ Required Columns:**

**Time Period:**
- Year
- Month
- DayofMonth

**Airline:**
- Reporting_Airline (or Carrier)

**Origin & Destination:**
- Origin
- Dest

**Departure Performance:**
- DepDelay
- DepDelayMinutes

**Arrival Performance:**
- ArrDelay
- ArrDelayMinutes

**Flight Details:**
- Distance
- Cancelled
- Diverted

#### **What to Skip:**
- ❌ Don't select: Tail Number, Flight Number, Taxi times, Air time (not needed)
- ❌ Avoid selecting ALL fields (file will be huge!)

---

### 3️⃣ Download the File

1. Click **"Download"** button at bottom
2. File will be named something like: `On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2024_1.zip`
3. Wait for download (usually 10-30 MB compressed)
4. **Unzip the file** - you'll get a CSV

---

### 4️⃣ Move File to Project

```bash
# Move the CSV to the data directory
mv ~/Downloads/On_Time_*.csv data/airline_ontime.csv

# Or if you prefer to keep original name, create a symlink
ln -s ~/Downloads/On_Time_*.csv data/airline_ontime.csv
```

**Expected location:**
```
Delaynomics/
  data/
    airline_ontime.csv  <- Your file should be here
```

---

### 5️⃣ Run the Analysis

```bash
# Open Jupyter
cd notebooks
jupyter notebook analysis.ipynb
```

**In Jupyter:**
1. Click **"Run All"** or run cells one by one
2. Watch the progress:
   - ✓ Data loading (30 sec - 2 min)
   - ✓ Data cleaning
   - ✓ Feature computation
   - ✓ Aggregation
   - ✓ Regression analysis
   - ✓ Export CSVs

**Expected outputs in `outputs/` directory:**
- `airline_summary.csv`
- `airport_summary.csv`
- `full_dataset_for_tableau.csv`
- `regression_plot.png`

---

### 6️⃣ Launch the Dashboard

```bash
# Go back to project root
cd ..

# Launch premium dashboard
python3 dashboard_app_premium.py
```

**Open:** http://localhost:8050

You should now see **real flight data** in your dashboard! 🎉

---

## 🔧 Troubleshooting

### "File too large" or "Memory error"

**Solution 1: Use a smaller time period**
- Download just 1 month instead of multiple months
- BTS data for 1 month = ~500K rows = manageable

**Solution 2: Use fewer carriers**
- The analysis automatically filters to top 5 carriers
- Edit this in the notebook if needed

**Solution 3: Sample the data**
```python
# In the notebook, after loading, add this line:
df = df.sample(n=50000, random_state=42)  # Use 50K random rows
```

### "Columns not found"

The BTS column names change slightly by year. Update the notebook:

**Common name variations:**
- `Reporting_Airline` vs `Carrier` vs `UniqueCarrier`
- `ArrDelayMinutes` vs `ArrDelay`

**Fix:** Edit the notebook's column mapping section

### "Data looks wrong"

Check that you:
1. Selected the right year/month
2. Downloaded U.S. flights only (not international)
3. Unzipped the file

---

## 📊 Data Size Guide

| Time Period | File Size (Compressed) | Rows | Processing Time |
|-------------|----------------------|------|-----------------|
| 1 month | ~10-20 MB | ~500K | 1-2 minutes |
| 3 months | ~30-60 MB | ~1.5M | 3-5 minutes |
| 1 year | ~200-400 MB | ~6M | 10-20 minutes |

**Recommendation for MVP:** Start with **1 month** of data.

---

## 🎯 Alternative: Pre-filtered Download

If the website is confusing, use this simpler approach:

### Using BTS Data Library (Python)

```python
# Install library
pip install bts-data

# Download programmatically
from bts_data import download_ontime_data

# Download January 2024
download_ontime_data(
    year=2024,
    month=1,
    output_path='data/airline_ontime.csv'
)
```

---

## 📅 Recommended Months

**Good months for analysis:**
- **January:** Post-holiday, winter weather delays
- **July:** Summer travel peak, high volume
- **December:** Holiday travel, interesting patterns

**Avoid:**
- February (shortest month, skews averages)
- Months with major disruptions (hurricanes, etc.)

---

## ✅ Verification Checklist

Before running analysis, verify:

- [ ] CSV file is in `data/airline_ontime.csv`
- [ ] File size is > 10 MB
- [ ] Can open CSV in text editor (shows column headers)
- [ ] Headers include: Year, Month, Carrier, Origin, Dest, ArrDelay, Distance
- [ ] File has ~500K rows for 1 month (check with `wc -l data/airline_ontime.csv`)

---

## 🚀 Quick Command Summary

```bash
# 1. Download from BTS website (manual step)

# 2. Move file
mv ~/Downloads/On_Time_*.csv data/airline_ontime.csv

# 3. Run analysis
cd notebooks && jupyter notebook analysis.ipynb
# Click "Run All"

# 4. Launch dashboard
cd .. && python3 dashboard_app_premium.py
```

---

## 📚 Additional Resources

- **BTS Homepage:** https://www.transtats.bts.gov/
- **Data Dictionary:** https://www.transtats.bts.gov/Fields.asp
- **FAQ:** https://www.transtats.bts.gov/DatabaseInfo.asp?QO_VQ=EFD

---

## 💡 Pro Tips

1. **Download multiple months** and compare trends over time
2. **Save your column selection** - BTS allows you to bookmark your query
3. **Compare years** - Download January 2023 vs January 2024
4. **Focus on specific routes** - Filter to specific origin/destination pairs
5. **Check data freshness** - BTS updates monthly, usually 2 months delayed

---

## 🎉 You're Ready!

Once you have the data:
1. Run analysis notebook → generates CSVs
2. Launch premium dashboard → visualize results
3. Explore filters → compare carriers

**Expected total time:** 15-20 minutes from download to dashboard

Good luck! 🚀
