# utils/prepare_training_csv.py
import pandas as pd
from pathlib import Path

ROOT = Path(".").resolve()
LABELS = ROOT / "dataset" / "labels.csv"
OUT = ROOT / "dataset" / "train.csv"

def main():
    df = pd.read_csv(LABELS)
    # keep only rows with category==residue (we train on residue moisture & vs)
    df = df[df["category"].str.strip().str.lower() == "residue"]
    # drop rows without moisture/vs
    df = df[df["moisture_percent"].notna() & df["vs_fraction"].notna()]

    # normalize image_path -> ensure path relative to project root e.g. dataset/images/...
    def norm(p):
        p = str(p)
        if p.startswith("dataset/images/"):
            return p
        # sometimes it's leaf/.. or images/.. adjust:
        if p.startswith("dataset/images"):
            return p
        if p.startswith("images/") or p.startswith("dataset/"):
            return p
        # assume the value is relative from dataset/images
        return f"dataset/images/{p.lstrip('./')}"
    df["image_path"] = df["image_path"].apply(norm)

    # keep necessary columns
    out = df[["image_path", "moisture_percent", "vs_fraction"]].copy()
    out.to_csv(OUT, index=False)
    print("✔ train.csv written:", OUT)
    print("Training samples:", len(out))

if __name__ == "__main__":
    main()
