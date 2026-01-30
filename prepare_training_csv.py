# prepare_training_csv.py
import pandas as pd
from pathlib import Path

LABELS = Path("dataset/labels.csv")
OUT = Path("dataset/train.csv")

df = pd.read_csv(LABELS, dtype=str).fillna("")

# Only residue images need regression labels
df = df[df["category"].str.lower() == "residue"]

# Ensure labeled == 1
df = df[df["labeled"] == "1"]

# Convert targets
df["moisture_percent"] = pd.to_numeric(df["moisture_percent"], errors="coerce")
df["vs_fraction"] = pd.to_numeric(df["vs_fraction"], errors="coerce")

# Drop rows missing any target
df = df.dropna(subset=["moisture_percent", "vs_fraction"])

df.to_csv(OUT, index=False)
print(f"✔ Training CSV created: {OUT}")
print(f"Total training rows: {len(df)}")
