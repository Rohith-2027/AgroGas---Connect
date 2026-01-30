# fill_seed_targets.py
import pandas as pd
import random
from pathlib import Path

SEED = Path("dataset/seed_labels.csv")

df = pd.read_csv(SEED, dtype=str).fillna("")

filled = 0
for i, row in df.iterrows():
    if row["category"] == "residue":
        # If blank, assign synthetic realistic values
        if row.get("moisture_percent","").strip() == "":
            df.at[i,"moisture_percent"] = round(random.uniform(60, 80), 2)

        if row.get("vs_fraction","").strip() == "":
            df.at[i,"vs_fraction"] = round(random.uniform(0.65, 0.80), 3)

        filled += 1

print(f"Filled {filled} residue rows with synthetic moisture & VS values.")

df.to_csv(SEED, index=False)
print("Updated:", SEED)
