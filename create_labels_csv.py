# create_labels_csv.py
import os, csv
from pathlib import Path

IMAGE_DIR = Path("dataset/images")
OUT_CSV = Path("dataset/labels.csv")
IMG_EXT = {".jpg",".jpeg",".png",".bmp",".webp"}

def main():
    rows=[]
    for category in ["leaf","residue"]:
        folder = IMAGE_DIR / category
        for img in folder.rglob("*"):
            if img.suffix.lower() in IMG_EXT:
                rows.append({
                    "image_path": f"{category}/{img.name}",
                    "category": category,
                    "health": "",
                    "mass_kg": "",
                    "moisture_percent": "",
                    "vs_fraction": "",
                    "notes": "",
                    "labeled": "0",
                })
    with open(OUT_CSV,"w",newline="",encoding="utf-8") as f:
        writer=csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print("labels.csv created:", len(rows),"rows")

if __name__ == "__main__":
    main()
