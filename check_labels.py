# check_labels.py
import pandas as pd
import sys

IN = "dataset/labels.csv"

try:
    df = pd.read_csv(IN)
except Exception as e:
    print("ERROR reading", IN, ":", e)
    sys.exit(1)

print("File:", IN)
print("Total rows:", len(df))
print("\nFirst 20 rows (image_path, category, moisture_percent, vs_fraction):")
print(df[["image_path","category","moisture_percent","vs_fraction"]].head(20).to_string(index=False))

print("\nCategory counts:")
print(df['category'].value_counts(dropna=False))

print("\nUnique moisture_percent sample (first 10):")
print(df['moisture_percent'].dropna().unique()[:10])

print("\nUnique vs_fraction sample (first 10):")
print(df['vs_fraction'].dropna().unique()[:10])
