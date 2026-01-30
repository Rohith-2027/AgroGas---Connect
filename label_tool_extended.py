# label_tool_extended.py (fixed rerun fallback)
import streamlit as st
import pandas as pd
from pathlib import Path
from PIL import Image

DATASET_DIR = Path("dataset")
IMAGES_DIR = DATASET_DIR / "images"
CSV_PATH = DATASET_DIR / "labels.csv"

st.set_page_config(page_title="Label Tool — AgroGas", layout="wide")
st.title("AgroGas — Labeling (category + leaf health + residue labels)")
st.write("Mark category = residue/leaf. For leaves set health. For residue enter mass_kg, moisture_percent, vs_fraction or leave blank for synthetic later.")

if not CSV_PATH.exists():
    st.error(f"CSV not found: {CSV_PATH}. Run create_labels_csv.py first.")
    st.stop()

df = pd.read_csv(CSV_PATH)

mode = st.radio("Mode", ("Unlabeled only", "All images"))
if mode == "Unlabeled only":
    df_view = df[df["labeled"].fillna(0).astype(int) == 0]
else:
    df_view = df

st.sidebar.write(f"Total images: {len(df)}   Filtered: {len(df_view)}")
if len(df_view) == 0:
    st.info("No images to show with current filter.")
    st.stop()

idx = st.sidebar.number_input("Index (0-based in filtered set)", min_value=0, max_value=max(0,len(df_view)-1), value=0, step=1)

# locate the real index in the original dataframe
row = df_view.reset_index().iloc[idx]
orig_index = int(row["index"]) if "index" in row else df.index[df["image_path"] == row["image_path"]][0]
row = df.loc[orig_index]

img_path = DATASET_DIR / Path(row["image_path"])
st.sidebar.write(f"File: {row['image_path']}")
if img_path.exists():
    st.image(Image.open(img_path), use_column_width=True)
else:
    st.warning("Image not found: " + str(img_path))

with st.form("form"):
    # set the default indices safely
    def select_index(value, options):
        try:
            return options.index(value)
        except Exception:
            return 0

    category_options = ["","residue","leaf"]
    health_options = ["","healthy","dried"]
    category_default = select_index(str(row.get("category") or ""), category_options)
    health_default = select_index(str(row.get("health") or ""), health_options)

    category = st.selectbox("Category", options=category_options, index=category_default)
    health = st.selectbox("Leaf health (only for leaf)", options=health_options, index=health_default)
    mass = st.text_input("mass_kg (kg)", value=str(row.get("mass_kg") if pd.notna(row.get("mass_kg")) else ""))
    moisture = st.text_input("moisture_percent (%)", value=str(row.get("moisture_percent") if pd.notna(row.get("moisture_percent")) else ""))
    vs = st.text_input("vs_fraction (0-1)", value=str(row.get("vs_fraction") if pd.notna(row.get("vs_fraction")) else ""))
    notes = st.text_area("Notes", value=str(row.get("notes") if pd.notna(row.get("notes")) else ""), height=80)
    save = st.form_submit_button("Save label")

if save:
    df.at[orig_index,"category"] = category
    df.at[orig_index,"health"] = health
    df.at[orig_index,"mass_kg"] = mass
    df.at[orig_index,"moisture_percent"] = moisture
    df.at[orig_index,"vs_fraction"] = vs
    df.at[orig_index,"notes"] = notes
    df.at[orig_index,"labeled"] = 1
    df.to_csv(CSV_PATH,index=False)
    st.success("Saved ✅")

    # Try to rerun programmatically if available; otherwise ask the user to refresh manually.
    try:
        rerun = getattr(st, "experimental_rerun", None)
        if callable(rerun):
            rerun()
        else:
            st.info("Saved — please refresh the browser page to continue.")
            st.stop()
    except Exception:
        st.info("Saved — please refresh the browser page to continue.")
        st.stop()

st.markdown("### Current row data")
st.json(row.to_dict())
