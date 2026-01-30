# inspect_seed_labels.py
import pandas as pd
from pathlib import Path

p = Path("dataset/seed_labels.csv")
if not p.exists():
    print("ERROR: dataset/seed_labels.csv not found at", p.resolve())
    raise SystemExit(1)

df = pd.read_csv(p, dtype=str).fillna("")
print("File:", p.resolve())
print("Total rows:", len(df))
print("\nFirst 12 rows (image_path, category, labeled):")
print(df[["image_path","category","labeled"]].head(12).to_string(index=False))
print("\nUnique values in 'labeled' column (raw):")
print(df["labeled"].value_counts(dropna=False).to_dict())

# also show trimmed normalized unique values
norm = df["labeled"].astype(str).str.strip().str.lower()
print("\nUnique values in 'labeled' (trimmed lower):")
print(norm.value_counts().to_dict())
print("\nCount where normalized == '1':", (norm == "1").sum())
