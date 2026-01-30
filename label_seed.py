# label_seed.py  (final version — supports all Streamlit versions)
import streamlit as st
import pandas as pd
from pathlib import Path
from PIL import Image

SEED_DIR = Path("dataset/seed_images")
OUT_CSV = Path("dataset/seed_labels.csv")

st.set_page_config(page_title="Seed Labeler — AgroGas", layout="wide")
st.title("AgroGas — Seed Image Labeling (Residue / Leaf)")

# Load images
imgs = sorted([p for p in SEED_DIR.iterdir() if p.suffix.lower() in [".jpg", ".jpeg", ".png"]])
if not imgs:
    st.error("No seed images found in dataset/seed_images. Run sample_seed.py first.")
    st.stop()

# Load existing labels
if OUT_CSV.exists():
    df = pd.read_csv(OUT_CSV)
else:
    df = pd.DataFrame(columns=["image", "category", "health"])

# UI index slider
i = st.number_input("Image Index", min_value=0, max_value=len(imgs)-1, value=0, step=1)
img_path = imgs[int(i)]

# Show image
st.subheader(f"Image: {img_path.name}")
st.image(Image.open(img_path), use_column_width=True)

# load existing row if exists
existing = df[df["image"] == img_path.name]
old_category = existing["category"].values[0] if not existing.empty else ""
old_health = existing["health"].values[0] if not existing.empty else ""

# Select boxes
category = st.selectbox(
    "Category",
    ["", "residue", "leaf"],
    index=["", "residue", "leaf"].index(old_category) if old_category in ["", "residue", "leaf"] else 0
)

health = st.selectbox(
    "Leaf health (only if leaf)",
    ["", "healthy", "dried"],
    index=["", "healthy", "dried"].index(old_health) if old_health in ["", "healthy", "dried"] else 0
)

# Save button
if st.button("Save Label"):
    new_row = pd.DataFrame([{
        "image": img_path.name,
        "category": category,
        "health": health
    }])

    # Remove old entry before replacing
    df = df[df["image"] != img_path.name]

    # Append new row
    df = pd.concat([df, new_row], ignore_index=True)

    # Save CSV
    df.to_csv(OUT_CSV, index=False)
    st.success("Saved successfully! ✅")

    # ---- RERUN FIX FOR ALL STREAMLIT VERSIONS ----
    try:
        st.rerun()            # New API (Streamlit ≥ 1.30)
    except:
        try:
            st.experimental_rerun()   # Old API (Streamlit < 1.30)
        except:
            st.info("Please manually refresh the page (Ctrl+R).")
            st.stop()

st.write("Labeled:", len(df), "/", len(imgs))
