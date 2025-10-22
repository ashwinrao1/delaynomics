#!/bin/bash

# Delaynomics Project Setup Script
# This script helps you get started quickly

echo "======================================"
echo "   Delaynomics Setup Script"
echo "======================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

echo "✓ Virtual environment created"
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✓ Dependencies installed"
echo ""

# Create outputs directory if it doesn't exist
mkdir -p outputs

echo "✓ Project structure verified"
echo ""

echo "======================================"
echo "   Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Generate sample data (for testing):"
echo "   cd notebooks"
echo "   jupyter notebook generate_sample_data.ipynb"
echo ""
echo "2. Run analysis:"
echo "   jupyter notebook analysis.ipynb"
echo ""
echo "3. Build Tableau dashboard:"
echo "   See TABLEAU_GUIDE.md for instructions"
echo ""
echo "OR download real BTS data:"
echo "   https://catalog.data.gov/dataset/airline-on-time-performance-data"
echo "   Place in data/ directory and run analysis.ipynb"
echo ""
echo "For more help, see QUICKSTART.md or README.md"
echo ""
