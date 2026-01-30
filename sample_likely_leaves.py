# sample_likely_leaves.py
from pathlib import Path
from PIL import Image
import numpy as np
import shutil
import random

PROJECT = Path(".").resolve()
ALL_DIR = PROJECT / "dataset" / "images"
SEED_DIR = PROJECT / "dataset" / "seed_images"
SEED_CSV = PROJECT / "dataset" / "seed_labels.csv"

N_TO_ADD = 220   # number of likely leaf images to copy
RANDOM_SEED = 42
random.seed(RANDOM_SEED)

# Load already-labeled names
existing_names = set()
if SEED_CSV.exists():
    import csv
    with open(SEED_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            existing_names.add(r.get("image",""))

# Candidate images
img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
candidates = [p for p in ALL_DIR.rglob("*")
              if p.is_file() and p.suffix.lower() in img_exts and p.name not in existing_names]

if not candidates:
    print("No candidate images found or all already in seed.")
    exit()

scores = []
for p in candidates:
    try:
        im = Image.open(p).convert("RGB")
        a = np.array(im, dtype=np.float32)
        r = a[:,:,0].mean()
        g = a[:,:,1].mean()
        b = a[:,:,2].mean()
        score = (g + 1e-6) / ((r + b)/2 + 1e-6)  # green dominance
        scores.append((score, p))
    except:
        continue

scores.sort(reverse=True, key=lambda x: x[0])

SEED_DIR.mkdir(parents=True, exist_ok=True)
copied = 0

for score, p in scores[:N_TO_ADD]:
    dst = SEED_DIR / p.name
    try:
        shutil.copy2(p, dst)
        copied += 1
    except Exception as e:
        print("Skipping", p, e)

print(f"Copied {copied} likely leaf images into seed_images.")
print("Restart Streamlit and label these new images.")
