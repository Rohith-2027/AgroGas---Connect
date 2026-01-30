# inspect_fix_health.py
import pandas as pd
from pathlib import Path

CSV = Path("dataset/seed_labels.csv")
if not CSV.exists():
    print("dataset/seed_labels.csv not found")
    raise SystemExit(1)

df = pd.read_csv(CSV)

print("TOTAL rows:", len(df))
print("\nUnique category counts:")
print(df["category"].fillna("").value_counts(dropna=False))

print("\nUnique health values and counts:")
print(df.get("health", pd.Series([])).fillna("").value_counts(dropna=False))

# Fix obvious mistakes:
# If there are >len(df) 'dried' counts or invalid tokens, normalize to lowercase and trim
if "health" in df.columns:
    df["health"] = df["health"].astype(str).str.strip().str.lower()
    # replace obvious bad tokens (like 'nan' or 'none') with ""
    df.loc[df["health"].isin({"nan","none","null","nan.0"}),"health"] = ""
    # If a row has health set but category != 'leaf', clear it
    mask = (df["health"] != "") & (df["category"] != "leaf")
    if mask.sum():
        print(f"\nCorrecting {mask.sum()} rows: clearing health where category != 'leaf'")
        df.loc[mask, "health"] = ""

    df.to_csv(CSV, index=False)
    print("\nAfter normalization, health counts:")
    print(df["health"].value_counts(dropna=False))
else:
    print("No health column present.")

print("\nDone. If counts still look wrong, open dataset/seed_labels.csv and inspect sample rows.")
