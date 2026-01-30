# report_seed_sync.py
import pandas as pd
from pathlib import Path

ROOT = Path(".")
seed_csv = ROOT / "dataset" / "seed_labels.csv"
seed_dir = ROOT / "dataset" / "seed_images"

def list_folder_images():
    imgs = []
    for cat in ("residue","leaf"):
        d = seed_dir / cat
        if d.exists():
            for p in sorted(d.glob("*.*")):
                imgs.append(str(p.relative_to(ROOT)).replace("\\","/"))
    return imgs

if not seed_csv.exists():
    print("No dataset/seed_labels.csv found.")
    folder_imgs = list_folder_images()
    print("Images in seed_images folder:", len(folder_imgs))
    for i,p in enumerate(folder_imgs[:50],1):
        print(f"{i:03d} {p}")
    raise SystemExit(0)

df = pd.read_csv(seed_csv, dtype=str)
df["image_path"] = df["image_path"].astype(str).str.replace("\\","/")

folder_imgs = list_folder_images()
set_csv = set(df["image_path"].tolist())
missing = [p for p in folder_imgs if p not in set_csv]

print("Images in seed_images folder:", len(folder_imgs))
print("Rows in seed_labels.csv:", len(df))
print("Missing (in folder but not in CSV):", len(missing))
if missing:
    for i,p in enumerate(missing,1):
        print(f"{i:03d} {p}")
else:
    print("No missing images — seed_labels.csv contains all seed images.")
