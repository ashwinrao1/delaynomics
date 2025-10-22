"""
Combine multiple CSV files in the data/ directory into a single CSV file for analysis.
Usage: Place all monthly CSVs in data/, then run this script.
"""
import os
import glob
import pandas as pd

DATA_DIR = "data"
OUTPUT_FILE = os.path.join(DATA_DIR, "airline_ontime.csv")

# Find all monthly CSV files (e.g., airline_ontime_2020_01.csv)
csv_files = sorted(glob.glob(os.path.join(DATA_DIR, "airline_ontime_*.csv")))

print(f"Found {len(csv_files)} files to combine.")

# Read and concatenate all CSVs
frames = []
for file in csv_files:
    print(f"Reading {file} ...")
    df = pd.read_csv(file)
    frames.append(df)

combined = pd.concat(frames, ignore_index=True)
print(f"Combined shape: {combined.shape}")

# Save to output file
combined.to_csv(OUTPUT_FILE, index=False)
print(f"Saved combined CSV to {OUTPUT_FILE}")
