# Tableau Dashboard Guide

Step-by-step instructions for building the Delaynomics dashboard in Tableau.

## Prerequisites

- Tableau Desktop or Tableau Public installed
- Analysis complete (ran [analysis.ipynb](notebooks/analysis.ipynb))
- Output files generated in `outputs/` directory

---

## Step 1: Connect Data Sources

### 1.1 Import Airline Summary

1. Open Tableau Desktop
2. Click **Text file** under "Connect"
3. Navigate to `outputs/airline_summary.csv`
4. Click **Open**

### 1.2 Import Airport Summary

1. In the Data Source pane, click **Add** (next to Connections)
2. Click **Text file**
3. Navigate to `outputs/airport_summary.csv`
4. Click **Open**

### 1.3 (Optional) Import Full Dataset

For deeper analysis:
1. Add `outputs/full_dataset_for_tableau.csv` as a third data source
2. This allows flight-level filtering and time series analysis

---

## Step 2: Create Calculated Fields

These fields enhance the analysis and improve labeling.

### In Airline Summary Data Source:

**Cost per Mile (Formatted)**
```
"$" + STR(ROUND([avg_cost_per_mile], 2))
```

**Delay Rate (%)**
```
[delay_rate] * 100
```

**Average Delay (Formatted)**
```
STR(ROUND([avg_delay_min], 1)) + " min"
```

### In Airport Summary Data Source:

**Cost per Mile (Formatted)**
```
"$" + STR(ROUND([avg_cost_per_mile], 2))
```

**Delay Rate (%)**
```
[delay_rate] * 100
```

---

## Step 3: Build Visualizations

### Viz 1: Airline Cost Comparison (Bar Chart)

**Goal:** Show which airlines are most cost-efficient

1. Create a new worksheet, name it "Airline Efficiency"
2. Drag `Carrier` to Rows
3. Drag `avg_cost_per_mile` to Columns
4. Sort descending (click the sort icon)
5. Add `avg_cost_per_mile` to Color
   - Edit colors: Green (low) → Red (high)
6. Add `avg_delay_min` to Label
7. Format:
   - Axis title: "Average Cost per Mile ($)"
   - Title: "Airline Efficiency: Cost per Mile"

**Result:** Horizontal bar chart showing carrier efficiency rankings

---

### Viz 2: Airport Heatmap

**Goal:** Visualize which airports have the highest delay costs

1. Create a new worksheet, name it "Airport Performance"
2. Drag `Airport` to Rows
3. Drag `avg_delay_cost` to Color
4. Drag `avg_delay_cost` to Text (for labels)
5. Format:
   - Mark type: Square
   - Color: Red-Green diverging (reverse so red = high cost)
   - Size: Increase mark size for visibility
   - Number format: Currency ($)
6. Sort by `avg_delay_cost` descending

**Result:** Color-coded list showing airport inefficiency

---

### Viz 3: Delay Rate vs Cost Efficiency (Scatter Plot)

**Goal:** Show relationship between delay frequency and cost

1. Create a new worksheet, name it "Delay Rate vs Cost"
2. Drag `Delay Rate (%)` to Columns
3. Drag `avg_cost_per_mile` to Rows
4. Drag `Carrier` to Detail (shows each carrier as a point)
5. Drag `num_flights` to Size (larger bubbles = more flights)
6. Drag `Carrier` to Label
7. Format:
   - Add reference lines for median delay rate and median cost
   - Title: "Delay Rate vs Cost Efficiency by Carrier"

**Result:** Scatter plot showing efficiency quadrants

---

### Viz 4: KPI Cards

**Goal:** Show headline metrics

Create 3 separate worksheets:

#### KPI 1: Best Carrier
1. Create worksheet "Best Carrier"
2. Drag `Carrier` to Text
3. Add filter: `avg_cost_per_mile` = MIN
4. Format: Large text, green background
5. Add subtitle with cost value

#### KPI 2: Average Delay Cost
1. Create worksheet "Avg Delay Cost"
2. Drag `avg_delay_cost` to Text
3. Add table calculation: Average across all carriers
4. Format: Currency, large text

#### KPI 3: Total Impact
1. Create worksheet "Total Cost Impact"
2. Drag `total_delay_cost` to Text
3. Add table calculation: Sum across all carriers
4. Format: Currency, large text
5. Title: "Total Delay Cost Across All Flights"

---

## Step 4: Build Dashboard

### 4.1 Create Dashboard Layout

1. Click the **New Dashboard** button
2. Set size: **Desktop (1366 x 768)** or **Automatic**

### 4.2 Arrange Components

**Layout Structure:**

```
┌────────────────────────────────────────────────────────┐
│  TITLE: Airline Delay Economics Dashboard              │
├────────────────────────────────────────────────────────┤
│  [Best Carrier] [Avg Delay Cost] [Total Cost Impact]   │  <- KPI Row
├─────────────────────────┬──────────────────────────────┤
│                         │                              │
│  Airline Efficiency     │  Airport Performance         │  <- Main Row
│  (Bar Chart)            │  (Heatmap)                   │
│                         │                              │
├─────────────────────────┴──────────────────────────────┤
│  Delay Rate vs Cost (Scatter Plot)                     │  <- Bottom Row
└────────────────────────────────────────────────────────┘
```

### 4.3 Drag Sheets to Dashboard

1. Drag KPI worksheets to top row (use Horizontal container)
2. Drag "Airline Efficiency" to left middle panel
3. Drag "Airport Performance" to right middle panel
4. Drag "Delay Rate vs Cost" to bottom panel

---

## Step 5: Add Interactivity

### 5.1 Add Filters

1. Drag `Carrier` from any sheet to the dashboard
2. Set to **Single Value (dropdown)** or **Multiple Values (list)**
3. Click "Apply to Worksheets" → "Selected Worksheets" → Choose all relevant sheets

Optional filters:
- `Airport` (if using full dataset)
- `Month` (if multi-month analysis)

### 5.2 Add Dashboard Actions

**Highlight Action:**
1. Dashboard → Actions → Add Action → Highlight
2. Source: "Airline Efficiency"
3. Target: All sheets
4. Run on: Hover
5. Effect: When you hover over a bar, all related visualizations highlight that carrier

**Filter Action (Optional):**
1. Dashboard → Actions → Add Action → Filter
2. Source: "Airline Efficiency"
3. Target: "Delay Rate vs Cost"
4. Run on: Select
5. Effect: Clicking a carrier filters the scatter plot

---

## Step 6: Format and Polish

### 6.1 Dashboard Title

1. Double-click the default title
2. Change to: **"Airline Delay Economics: Which Carriers Deliver Value?"**
3. Format:
   - Font: 18pt, Bold
   - Color: Dark blue or black
   - Alignment: Center

### 6.2 Add Text Annotations

Add a Text object with key insights:

```
KEY FINDINGS:
• Best value carrier: [Carrier] at $[X.XX] per mile
• Worst value carrier: [Carrier] at $[X.XX] per mile
• Total economic impact: $[XXX,XXX] in delay costs
• Average delay: [X.X] minutes per flight
```

### 6.3 Color Consistency

Ensure all visualizations use consistent color scheme:
- **Green** = Efficient / Low cost
- **Red** = Inefficient / High cost
- **Blue** = Neutral / Information

### 6.4 Add Data Source Note

Add Text object at bottom:

```
Data Source: Bureau of Transportation Statistics (BTS)
Analysis Period: [Month/Year]
Cost Calculation: $74 per minute of delay (FAA estimate)
```

---

## Step 7: Publish (Optional)

### Tableau Public:

1. File → Save to Tableau Public
2. Sign in to your account
3. Add description and tags
4. Click **Save**
5. Share the public URL

### Tableau Server:

1. Server → Publish Workbook
2. Select project
3. Set permissions
4. Click **Publish**

---

## Advanced Enhancements

### Multi-Month Trend Analysis

If you have multiple months of data:

1. Create line chart: `Month` (Columns) vs `avg_delay_cost` (Rows)
2. Add `Carrier` to Color
3. Add reference lines for each carrier's average
4. Title: "Delay Cost Trends Over Time"

### Route-Level Analysis

If using full dataset:

1. Create calculated field: `Route = [Origin] + " → " + [Dest]`
2. Build bar chart of top 10 most expensive routes
3. Filter by carrier for comparison

### Distance Segmentation

Create bins for flight distance:

1. Right-click `Distance` → Create → Bins
2. Size: 500 miles
3. Build bar chart: `Distance (bin)` vs `avg_delay_min`
4. Shows if short/medium/long flights have different delay patterns

---

## Design Best Practices

### Color Use
- Use **diverging color palettes** for comparisons (green-red)
- Use **sequential palettes** for magnitudes (light-dark blue)
- Avoid red-green for colorblind accessibility (use red-blue or orange-blue)

### Text & Labels
- Always format currency fields with `$` symbol
- Round to 2 decimal places for money
- Round to 1 decimal place for minutes
- Use clear, descriptive titles

### Layout
- Most important viz in top-left (Western reading pattern)
- KPIs at the top for immediate visibility
- Use white space to avoid clutter
- Align objects on a grid

---

## Troubleshooting

### "Cannot blend the data sources"
→ Make sure field names match exactly across data sources
→ Use a join instead of blend if possible

### "Null values appearing"
→ Check for missing data in the CSV
→ Filter out nulls: Right-click field → Filter → Exclude Null

### "Colors not showing correctly"
→ Check that the field is on Color shelf
→ Edit color palette: Right-click Color → Edit Colors

### "Dashboard is too cluttered"
→ Remove gridlines: Format → Lines → None
→ Remove row/column dividers
→ Increase white space between objects

---

## Sample Dashboard Ideas

### Dashboard Variant 1: Executive Summary
- Focus: High-level KPIs and rankings
- Audience: Leadership
- Emphasis: Cost impact, best/worst performers

### Dashboard Variant 2: Operational Deep-Dive
- Focus: Detailed metrics, airport-level analysis
- Audience: Operations teams
- Emphasis: Delay patterns, efficiency metrics

### Dashboard Variant 3: Trend Analysis
- Focus: Time series, seasonality
- Audience: Analysts
- Emphasis: Month-over-month changes, forecasting

---

## Next Steps

1. **Iterate:** Get feedback and refine
2. **Schedule refreshes:** If connecting to live data
3. **Add parameters:** Let users adjust cost-per-minute value
4. **Build stories:** Use Tableau Stories to narrate findings
5. **Export insights:** Dashboard → Export → Image/PDF

---

## Resources

- [Tableau Public Gallery](https://public.tableau.com/gallery) - Inspiration
- [Tableau Help](https://help.tableau.com/) - Official documentation
- [Color Brewer](https://colorbrewer2.org/) - Colorblind-safe palettes

---

**Dashboard Status:** Template ready for customization

**Questions?** Review the notebook output for specific values to highlight in your dashboard.
