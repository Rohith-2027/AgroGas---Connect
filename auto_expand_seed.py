# auto_expand_seed.py
"""
Auto-expand the seed_images folder by copying images from dataset/images
so you reach a target seed size (default 300). The script tries to balance
residue vs leaf counts by filling the under-represented class first.
"""

import pandas as pd
from pathlib import Path
import random
import shutil
import os
import sys

# Config
PROJECT_ROOT = Path(".").resolve()
SEED_CSV = PROJECT_ROOT / "dataset" / "seed_labels.csv"
SEED_DIR = PROJECT_ROOT / "dataset" / "seed_images"
ALL_DIR = PROJECT_ROOT / "dataset" / "images"
TARGET = 300   # desired total labeled seed size
RANDOM_SEED = 42

random.seed(RANDOM_SEED)

# Sanity checks
if not ALL_DIR.exists():
    print("ERROR: dataset/images directory not found:", ALL_DIR)
    sys.exit(1)
if not (ALL_DIR.is_dir()):
    print("ERROR: dataset/images must be a directory")
    sys.exit(1)

# Load existing labeled seed CSV (if present)
if SEED_CSV.exists():
    df = pd.read_csv(SEED_CSV)
else:
    df = pd.DataFrame(columns=["image", "category", "health"])

labeled_names = set(df["image"].astype(str).tolist())
current_total = len(df)
print("Current labeled seed:", current_total)

# Count existing classes in seed
res_count = int((df["category"] == "residue").sum()) if "category" in df.columns else 0
leaf_count = int((df["category"] == "leaf").sum()) if "category" in df.columns else 0
print(f"Residue in seed: {res_count} | Leaf in seed: {leaf_count}")

if current_total >= TARGET:
    print("Seed already >= target size. Nothing to do.")
    sys.exit(0)

# Choose candidates from dataset/images not already in seed
img_exts = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}
candidates = [p for p in ALL_DIR.rglob("*") if p.is_file() and p.suffix.lower() in img_exts and p.name not in labeled_names]

if not candidates:
    print("No candidate images found in dataset/images (or all are already in seed).")
    sys.exit(1)

random.shuffle(candidates)

# Determine class targets (aim for ~50/50 residue/leaf)
target_residue = TARGET // 2
target_leaf = TARGET - target_residue

to_copy = []
# Fill residue shortfall
if res_count < target_residue:
    want = target_residue - res_count
    # pick first `want` candidates (we cannot know true class yet)
    for p in candidates:
        to_copy.append(p)
        if len(to_copy) >= want:
            break

# If still short overall, pick more to reach TARGET
if len(to_copy) < (TARGET - current_total):
    need_more = (TARGET - current_total) - len(to_copy)
    # add more candidates not already chosen
    for p in candidates:
        if p in to_copy:
            continue
        to_copy.append(p)
        if len(to_copy) >= (len(to_copy) + need_more):
            break

# Final trimming to not exceed TARGET
max_to_add = TARGET - current_total
to_copy = to_copy[:max_to_add]

SEED_DIR.mkdir(parents=True, exist_ok=True)
copied = 0
for p in to_copy:
    dst = SEED_DIR / p.name
    try:
        shutil.copy2(p, dst)
        copied += 1
    except Exception as e:
        print("Failed to copy", p, ":", e)

print(f"Copied {copied} images to {SEED_DIR}.")
print("Now restart the Streamlit seed labeler and label until Labeled count reaches the target (~300).")
