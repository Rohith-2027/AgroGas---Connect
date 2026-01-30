# fill_realistic_labels.py
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import shutil
import sys

SRC = Path("dataset/labels.csv")
OUT = Path("dataset/labels_real.csv")
BACKUP_DIR = Path("dataset/backups")
SEED = 42

if not SRC.exists():
    print("ERROR: dataset/labels.csv not found. Run create_labels_csv.py first.")
    sys.exit(1)

# load
df = pd.read_csv(SRC)
print("Loaded", len(df), "rows from", SRC)

# backup
BACKUP_DIR.mkdir(parents=True, exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
backup = BACKUP_DIR / f"labels_backup_{ts}.csv"
shutil.copy2(SRC, backup)
print("Backup written to", backup)

# ranges (you confirmed these)
leaf_moist_min, leaf_moist_max = 60.0, 75.0
leaf_vs_min, leaf_vs_max = 0.65, 0.75

res_moist_min, res_moist_max = 20.0, 40.0
res_vs_min, res_vs_max = 0.70, 0.85

rng = np.random.RandomState(SEED)

# Ensure columns present
for c in ["moisture_percent","vs_fraction","category","image_path","labeled","mass_kg","notes"]:
    if c not in df.columns:
        df[c] = pd.NA

# Normalise category strings (lowercase) and trim
df['category'] = df['category'].astype(str).str.strip().str.lower().replace({'nan':pd.NA})

# Function to sample value in range
def sample_range(n, lo, hi):
    return (rng.rand(n) * (hi - lo) + lo).round(3)

# Fill leaf rows
leaf_idx = df[df['category']=='leaf'].index
n_leaf = len(leaf_idx)
print("Found leaf rows:", n_leaf)
if n_leaf > 0:
    df.loc[leaf_idx, "moisture_percent"] = sample_range(n_leaf, leaf_moist_min, leaf_moist_max)
    df.loc[leaf_idx, "vs_fraction"] = sample_range(n_leaf, leaf_vs_min, leaf_vs_max)
    df.loc[leaf_idx, "notes"] = (df.loc[leaf_idx, "notes"].fillna("") + " auto-filled-leaf-realistic").str.strip()

# Fill residue rows
res_idx = df[df['category']=='residue'].index
n_res = len(res_idx)
print("Found residue rows:", n_res)
if n_res > 0:
    df.loc[res_idx, "moisture_percent"] = sample_range(n_res, res_moist_min, res_moist_max)
    df.loc[res_idx, "vs_fraction"] = sample_range(n_res, res_vs_min, res_vs_max)
    df.loc[res_idx, "notes"] = (df.loc[res_idx, "notes"].fillna("") + " auto-filled-residue-realistic").str.strip()

# For any remaining unknown category rows, fill with a safe default (leaf-like)
other_idx = df[~df['category'].isin(['leaf','residue'])].index
n_other = len(other_idx)
print("Found other/unknown rows:", n_other)
if n_other > 0:
    df.loc[other_idx, "moisture_percent"] = sample_range(n_other, 45.0, 65.0)
    df.loc[other_idx, "vs_fraction"] = sample_range(n_other, 0.68, 0.78)
    df.loc[other_idx, "notes"] = (df.loc[other_idx, "notes"].fillna("") + " auto-filled-unknown-realistic").str.strip()

# Clean formatting: numeric columns
df["moisture_percent"] = pd.to_numeric(df["moisture_percent"], errors="coerce").round(3)
df["vs_fraction"] = pd.to_numeric(df["vs_fraction"], errors="coerce").round(4)

# Mark labeled=1 for those we filled (so train scripts can pick them)
df["labeled"] = df["labeled"].fillna(0).astype(str)
# if category is leaf or residue, ensure labeled=1
df.loc[df['category'].isin(['leaf','residue']), "labeled"] = "1"

# write out
df.to_csv(OUT, index=False)
print("Wrote realistic labels to", OUT)
print("Summary after fill:")
print(df['category'].value_counts(dropna=False))
print("\nMoisture stats (filled rows):")
print(df.loc[df['labeled'].astype(str)=="1", "moisture_percent"].describe())
print("\nVS stats (filled rows):")
print(df.loc[df['labeled'].astype(str)=="1", "vs_fraction"].describe())

print("\nIMPORTANT:")
print(" - labels_real.csv created. If it looks good, replace dataset/labels.csv with it or update train script to use labels_real.csv.")
print(" - Backup was stored at", backup)
