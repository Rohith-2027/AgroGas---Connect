# merge_seed_labels.py  (updated, overwrite existing)
import pandas as pd

MASTER = "dataset/labels.csv"
SEED = "dataset/seed_labels.csv"

print("Loading master and seed CSVs...")
master = pd.read_csv(MASTER, dtype=str).fillna("")
seed = pd.read_csv(SEED, dtype=str).fillna("")

# Normalize paths
master["image_path"] = master["image_path"].astype(str).str.replace("\\", "/")
seed["image_path"] = seed["image_path"].astype(str).str.replace("\\", "/")

print("Master rows:", len(master))
print("Seed rows:", len(seed))

# Merge by image_path (seed columns get suffix _seed)
merged = master.merge(seed, on="image_path", how="left", suffixes=("", "_seed"))

# Copy seed fields over master (force seed when available)
for col in ["category", "health", "mass_kg", "moisture_percent", "vs_fraction", "notes", "labeled"]:
    seed_col = col + "_seed"
    if seed_col in merged.columns:
        # if seed has non-empty value use it; otherwise keep master
        merged[col] = merged[seed_col].where(merged[seed_col].astype(str).str.strip() != "", merged[col])
    else:
        # fallback: keep existing master value
        merged[col] = merged[col]

# Normalize labeled column to "1"/"0" strings
if "labeled" not in merged.columns:
    merged["labeled"] = "0"

merged["labeled"] = merged["labeled"].astype(str).fillna("").str.strip().str.lower().apply(
    lambda x: "1" if x in ("1", "true", "yes") else "0"
)

# Drop any leftover *_seed columns
cols_to_keep = [c for c in merged.columns if not c.endswith("_seed")]
merged = merged[cols_to_keep]

# Save result
merged.to_csv(MASTER, index=False)

# Print verification
total_rows = len(merged)
labeled_count = (merged["labeled"] == "1").sum()
cat_counts = merged["category"].value_counts(dropna=False).to_dict()
health_counts = merged.get("health", pd.Series()).value_counts(dropna=False).to_dict()

print("✔ merge completed")
print("Final master rows:", total_rows)
print("Labeled rows:", labeled_count)
print("Category counts sample:", cat_counts)
print("Health counts sample:", health_counts)
print("\nSample merged rows (first 10):")
print(merged[["image_path","category","health","labeled"]].head(10).to_string(index=False))
