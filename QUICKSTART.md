# Quick Start Guide

Get up and running with the Delaynomics project in 5 minutes.

## Option A: Test with Sample Data (Fastest)

Perfect for testing the pipeline before working with real BTS data.

### Steps:

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Generate sample data**
   ```bash
   cd notebooks
   jupyter notebook generate_sample_data.ipynb
   ```
   Run all cells to create `data/airline_ontime.csv`

3. **Run analysis**
   ```bash
   jupyter notebook analysis.ipynb
   ```
   Run all cells to generate:
   - `outputs/airline_summary.csv`
   - `outputs/airport_summary.csv`
   - `outputs/full_dataset_for_tableau.csv`

4. **Open in Tableau**
   - Launch Tableau Desktop
   - Connect to the CSV files in `outputs/`
   - Build your dashboard

**Total time:** ~5 minutes

---

## Option B: Use Real BTS Data (Production)

For actual analysis with real flight data.

### Steps:

1. **Download BTS data**

   Go to: https://catalog.data.gov/dataset/airline-on-time-performance-data

   - Select a month (e.g., January 2024)
   - Download the CSV
   - Place it in the `data/` directory
   - Rename to `airline_ontime.csv` (or update the path in the notebook)

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run analysis**
   ```bash
   cd notebooks
   jupyter notebook analysis.ipynb
   ```

   Run all cells. Note: May take 5-15 minutes depending on data size.

4. **Review outputs**
   - Check `outputs/` for generated CSV files
   - Review the regression analysis results
   - Note the key insights printed at the end

5. **Build Tableau dashboard**
   - See [TABLEAU_GUIDE.md](TABLEAU_GUIDE.md) for detailed instructions

**Total time:** ~20-30 minutes (including download)

---

## Project Structure Overview

```
Delaynomics/
├── data/                           # Put your CSV here
├── notebooks/
│   ├── generate_sample_data.ipynb # Generate test data
│   └── analysis.ipynb             # Main analysis (run this)
├── outputs/                        # Generated files
│   ├── airline_summary.csv        # For Tableau
│   ├── airport_summary.csv        # For Tableau
│   └── full_dataset_for_tableau.csv
├── requirements.txt               # Dependencies
├── README.md                      # Full documentation
├── QUICKSTART.md                  # This file
└── TABLEAU_GUIDE.md               # Tableau instructions
```

---

## Expected Outputs

After running [analysis.ipynb](notebooks/analysis.ipynb), you should see:

### Console Output:
- Data cleaning summary
- Feature computation confirmation
- Airline and airport performance tables
- Regression results (Distance vs Delay)
- Key insights summary

### Files Created:
- `outputs/airline_summary.csv` - 5 rows (one per carrier)
- `outputs/airport_summary.csv` - 10 rows (one per airport)
- `outputs/full_dataset_for_tableau.csv` - All cleaned flight records
- `outputs/regression_plot.png` - Visualization of distance vs delay

---

## Troubleshooting

### "FileNotFoundError: data/airline_ontime.csv"
→ You need to either:
- Run `generate_sample_data.ipynb` first (for testing), OR
- Download real BTS data and place it in `data/`

### "ModuleNotFoundError: No module named 'pandas'"
→ Install dependencies:
```bash
pip install -r requirements.txt
```

### Jupyter notebook won't open
→ Install Jupyter:
```bash
pip install jupyter
```

### Memory error with large BTS file
→ The notebook uses memory-efficient loading, but if you still have issues:
- Use a smaller time period (1 month instead of 1 year)
- Increase the subset size gradually
- Consider using a machine with more RAM

---

## What's Next?

After generating the outputs:

1. **Review the insights** in the notebook output
2. **Build your Tableau dashboard** using the CSV files
3. **Customize the analysis** by editing the notebook:
   - Change the cost per minute value
   - Add more carriers/airports
   - Include additional metrics
   - Extend to multi-month analysis

---

## Need Help?

- **Full documentation:** [README.md](README.md)
- **Tableau instructions:** [TABLEAU_GUIDE.md](TABLEAU_GUIDE.md)
- **Questions about the data:** Check BTS documentation
- **Questions about the code:** Review comments in [analysis.ipynb](notebooks/analysis.ipynb)
