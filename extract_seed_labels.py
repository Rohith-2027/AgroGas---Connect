# extract_seed_labels.py
import pandas as pd
from pathlib import Path

ROOT = Path(".")
labels_csv = ROOT / "dataset" / "labels.csv"
seed_csv = ROOT / "dataset" / "seed_labels.csv"

if not labels_csv.exists():
    print("ERROR: dataset/labels.csv not found. Run create_labels_csv.py first.")
    raise SystemExit(1)

df = pd.read_csv(labels_csv)

# Normalize column names and string values
if "labeled" not in df.columns:
    print("No 'labeled' column found in dataset/labels.csv — cannot extract seed. Exiting.")
    raise SystemExit(1)

# Consider labeled values: 1, "1", True, "true", non-empty
def is_labeled(v):
    if pd.isna(v):
        return False
    s = str(v).strip().lower()
    return s in ("1","true","yes") or (s != "" and s != "0" and s != "false" and s != "nan")

seed_df = df[df["labeled"].apply(is_labeled)].copy()

if seed_df.empty:
    print("No labeled rows found (no rows with labeled==1). If you have labeled rows elsewhere, point me to that file.")
else:
    seed_df.to_csv(seed_csv, index=False)
    print(f"Written {len(seed_df)} rows to {seed_csv}")
