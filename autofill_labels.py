# autofill_labels.py
import pandas as pd
from pathlib import Path
ROOT = Path(".")
MASTER = ROOT / "dataset" / "labels.csv"
SEED = ROOT / "dataset" / "seed_labels.csv"

df = pd.read_csv(MASTER, dtype=str).fillna("")
seed = pd.read_csv(SEED, dtype=str).fillna("")

# Ensure numeric columns exist in seed and convert
seed = seed[seed["category"] == "residue"]
seed["moisture_percent"] = pd.to_numeric(seed["moisture_percent"], errors="coerce")
seed["vs_fraction"] = pd.to_numeric(seed["vs_fraction"], errors="coerce")

avg_moist = float(seed["moisture_percent"].mean())
avg_vs = float(seed["vs_fraction"].mean())

print(f"Seed residue avg moisture = {avg_moist:.2f}%, avg VS = {avg_vs:.3f}")

# Fill only for residue rows in master where moisture or vs missing or non-numeric
def is_empty(x):
    s = str(x).strip()
    return s == "" or s.lower() in ("nan","none")

filled = 0
for i,row in df.iterrows():
    cat = str(row.get("category","")).strip()
    if cat == "residue":
        if is_empty(row.get("moisture_percent","")):
            df.at[i,"moisture_percent"] = round(avg_moist,3)
            filled += 1
        if is_empty(row.get("vs_fraction","")):
            df.at[i,"vs_fraction"] = round(avg_vs,4)
            # filled count only once above

df.to_csv(MASTER, index=False)
print(f"Filled moisture/VS for {filled} residue rows in {MASTER}")
