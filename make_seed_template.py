# make_seed_template.py
from pathlib import Path
import csv

out = Path("dataset/seed_labels.csv")
out.parent.mkdir(parents=True, exist_ok=True)

header = [
    "image_path",
    "category",
    "health",
    "mass_kg",
    "moisture_percent",
    "vs_fraction",
    "notes",
    "labeled"
]

with open(out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=header)
    writer.writeheader()

print("Created dataset/seed_labels.csv — Ready to fill using Streamlit label tool.")
