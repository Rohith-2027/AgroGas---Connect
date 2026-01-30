# label_seed_fixed.py
import streamlit as st
from pathlib import Path
import pandas as pd

ROOT = Path(".")
SEED_DIR = ROOT / "dataset" / "seed_images"
CSV_OUT = ROOT / "dataset" / "seed_labels.csv"

st.title("AgroGas — Seed Labeler")

# Build list of images
imgs = []
for cat in ("residue", "leaf"):
    d = SEED_DIR / cat
    if d.exists():
        for p in sorted(d.glob("*.*")):
            imgs.append({"path": str((p).relative_to(ROOT)).replace("\\", "/"), "category": cat})

if not imgs:
    st.error("No images found in dataset/seed_images/.")
    st.stop()

# Load or create CSV
if CSV_OUT.exists():
    df = pd.read_csv(CSV_OUT)
else:
    df = pd.DataFrame(columns=["image_path","category","health","mass_kg","moisture_percent","vs_fraction","notes","labeled"])

# Index selector
idx = st.number_input("Image index", min_value=0, max_value=len(imgs)-1, value=0, step=1)
entry = imgs[idx]

st.image(entry["path"], width=400)
st.write(f"Image {idx+1}/{len(imgs)} — category detected from folder → {entry['category']}")

# Find existing row
row = df[df["image_path"] == entry["path"]]
if not row.empty:
    existing = row.iloc[0].to_dict()
else:
    existing = {
        "image_path": entry["path"],
        "category": entry["category"],
        "health": "",
        "mass_kg": "",
        "moisture_percent": "",
        "vs_fraction": "",
        "notes": "",
        "labeled": "0",
    }

# Inputs
health = st.selectbox("Health (only for leaf)", ["", "healthy", "dried"], index=0)
notes = st.text_input("Notes", existing["notes"])
labeled = st.checkbox("Mark as labeled", value=(existing["labeled"] == "1"))

if st.button("Save Label"):
    new = {
        "image_path": entry["path"],
        "category": entry["category"],
        "health": health if entry["category"] == "leaf" else "",
        "mass_kg": "",
        "moisture_percent": "",
        "vs_fraction": "",
        "notes": notes,
        "labeled": "1" if labeled else "0",
    }

    df = df[df["image_path"] != entry["path"]]
    df = pd.concat([df, pd.DataFrame([new])], ignore_index=True)
    df.to_csv(CSV_OUT, index=False)
    st.success("Saved!")
