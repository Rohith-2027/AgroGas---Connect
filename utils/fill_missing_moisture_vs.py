# utils/fill_missing_moisture_vs.py
import os, sys, random
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LABELS = ROOT / "dataset" / "labels.csv"
OUT = ROOT / "dataset" / "labels_filled.csv"

# sensible defaults (from your seed)
SEED_RESIDUE_MOIST = 69.317
SEED_RESIDUE_VS = 0.7296

# leaf defaults (dry/healthy leaf => low VS, moderate moisture)
DEFAULT_LEAF_MOIST = 30.0
DEFAULT_LEAF_VS = 0.15

def is_image_path_ok(p: str):
    pth = (ROOT / p).resolve()
    return pth.exists()

def main():
    if not LABELS.exists():
        print("labels.csv not found at", LABELS)
        return
    df = pd.read_csv(LABELS)
    if "category" not in df.columns:
        print("labels.csv missing 'category' column")
        return

    # normalize column names / ensure columns present
    for c in ("moisture_percent","vs_fraction","labeled"):
        if c not in df.columns:
            df[c] = pd.NA

    filled = 0
    missing_images = 0
    for i, row in df.iterrows():
        img_path = str(row["image_path"])
        # normalize path if it is relative incorrectly (some rows have dataset/images/... as prefix already)
        if not (ROOT / img_path).exists():
            # try with dataset/images prefix
            alt = Path("dataset") / img_path
            if alt.exists():
                img_path = str(alt)
            else:
                # try stripping a duplicated prefix
                if img_path.startswith("dataset/dataset/"):
                    cand = img_path.replace("dataset/dataset/","dataset/")
                    if (ROOT / cand).exists():
                        img_path = cand

        if not is_image_path_ok(img_path):
            missing_images += 1
            continue

        cat = str(row.get("category") or "").strip().lower()
        # if already present and numeric, skip
        m = row.get("moisture_percent")
        v = row.get("vs_fraction")
        has_m = False
        try:
            if m is not None and (str(m).strip() != "" and not pd.isna(m)):
                float(m)
                has_m = True
        except Exception:
            has_m = False

        if has_m and v is not None and str(v).strip() != "" and not pd.isna(v):
            continue

        # Fill according to category
        if cat == "residue":
            # use seed average + tiny random noise to avoid identical entries
            noisemoist = SEED_RESIDUE_MOIST + random.uniform(-1.5, 1.5)
            noisyvs = SEED_RESIDUE_VS + random.uniform(-0.03, 0.03)
            df.at[i, "moisture_percent"] = round(max(0.0, min(100.0, noisemoist)), 3)
            df.at[i, "vs_fraction"] = round(max(0.0, min(1.0, noisyvs)), 4)
            df.at[i, "notes"] = (str(row.get("notes") or "") + " auto-filled-from-seed").strip()
            filled += 1
        elif cat == "leaf":
            df.at[i, "moisture_percent"] = DEFAULT_LEAF_MOIST
            df.at[i, "vs_fraction"] = DEFAULT_LEAF_VS
            df.at[i, "notes"] = (str(row.get("notes") or "") + " auto-filled-leaf-default").strip()
            filled += 1
        else:
            # Unknown category: leave as NaN (we don't guess)
            pass

    df.to_csv(OUT, index=False)
    print("✔ Wrote", OUT)
    print("✔ Filled values for", filled, "rows")
    print("⚠ Missing images:", missing_images)
    print("If missing images > 0, inspect dataset/images paths and labels.image_path values.")
    print("If everything looks good, replace dataset/labels.csv with labels_filled.csv (or keep as backup).")

if __name__ == "__main__":
    main()
