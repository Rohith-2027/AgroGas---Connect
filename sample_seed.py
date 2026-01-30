# sample_seed.py
import pandas as pd
from pathlib import Path
import random
import shutil

SRC_CSV = Path("dataset/labels.csv")
OUT_DIR = Path("dataset/seed_images")
N = 400  # choose 200-500 (adjust)

random.seed(42)

if not SRC_CSV.exists():
    raise SystemExit("dataset/labels.csv not found")

df = pd.read_csv(SRC_CSV)
all_images = df["image_path"].tolist()
if len(all_images) < N:
    N = len(all_images)
sampled = random.sample(all_images, N)

OUT_DIR.mkdir(parents=True, exist_ok=True)
for p in sampled:
    src = Path("dataset") / p
    if src.exists():
        dst = OUT_DIR / Path(p).name
        shutil.copy2(src, dst)
    else:
        print("Missing:", src)

print(f"Seed images copied to {OUT_DIR} ({len(list(OUT_DIR.iterdir()))} files).")
