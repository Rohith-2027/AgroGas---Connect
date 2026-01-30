# first_unlabeled_index.py
from pathlib import Path
import csv

seed_dir = Path("dataset/seed_images")
seed_csv = Path("dataset/seed_labels.csv")

files = sorted([p.name for p in seed_dir.iterdir() if p.is_file()])
labeled = set()
if seed_csv.exists():
    with open(seed_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            labeled.add(r.get("image",""))

# find first index in files that is not labeled
first_unlabeled = None
for i, name in enumerate(files):
    if name not in labeled:
        first_unlabeled = i
        break

print("Total seed images:", len(files))
print("Labeled rows in seed CSV:", len(labeled))
print("First unlabeled index (0-based):", first_unlabeled)
print("If None, all seed images are already labeled.")
