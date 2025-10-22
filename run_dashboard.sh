#!/bin/bash

# Quick launcher for Delaynomics Dashboard

echo "======================================"
echo "   Delaynomics Dashboard Launcher"
echo "======================================"
echo ""

# Check if outputs exist
if [ ! -f "outputs/airline_summary.csv" ] || [ ! -f "outputs/airport_summary.csv" ]; then
    echo "⚠️  Warning: Output files not found!"
    echo ""
    echo "You need to run the analysis first:"
    echo "  1. cd notebooks"
    echo "  2. jupyter notebook generate_sample_data.ipynb (run all cells)"
    echo "  3. jupyter notebook analysis.ipynb (run all cells)"
    echo ""
    echo "Or download real BTS data and run analysis.ipynb"
    echo ""
    exit 1
fi

# Check if dependencies are installed
if ! python3 -c "import dash" 2>/dev/null; then
    echo "📦 Installing dashboard dependencies..."
    pip install dash plotly
    echo ""
fi

# Launch dashboard
echo "🚀 Launching dashboard..."
echo ""
python3 dashboard_app_enhanced.py
