# check_seed_counts.py
import pandas as pd
from pathlib import Path

CSV = Path("dataset/seed_labels.csv")
if not CSV.exists():
    print("dataset/seed_labels.csv not found")
    raise SystemExit(1)

df = pd.read_csv(CSV)
total = len(df)
residue = int((df["category"]=="residue").sum())
leaf = int((df["category"]=="leaf").sum())
healthy = int((df["health"]=="healthy").sum())
dried = int((df["health"]=="dried").sum())

print("Total labeled:", total)
print("Residue:", residue)
print("Leaf:", leaf)
print("  - healthy:", healthy)
print("  - dried:", dried)
print("")
print("Recommended seed: 300 (150 residue, 75 healthy, 75 dried).")
