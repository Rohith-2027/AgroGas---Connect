import pandas as pd
from pathlib import Path

seed_csv = Path("dataset/seed_labels.csv")

df = pd.read_csv(seed_csv, dtype=str)

# Normalize
df["image_path"] = df["image_path"].astype(str)
df["category"] = df["category"].astype(str)

# Set health automatically
df.loc[df["category"]=="leaf", "health"] = "healthy"
df.loc[df["category"]=="residue", "health"] = "dried"

# Mark all rows as labeled
df["labeled"] = "1"

df.to_csv(seed_csv, index=False)

print("✔ Updated seed_labels.csv")
print("Total rows:", len(df))
print(df["category"].value_counts())
print(df["health"].value_counts())
print("Labeled count:", (df['labeled']=="1").sum())
