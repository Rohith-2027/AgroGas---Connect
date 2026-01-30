# make_train_from_labels.py
import pandas as pd
df = pd.read_csv("dataset/labels_real.csv")
# keep only labeled rows (where labeled==1) and filled moisture/vs
df = df[df['labeled'].astype(str) == '1'].copy()
# filter to rows that have moisture and vs
df = df[df['moisture_percent'].notna() & df['vs_fraction'].notna()]
# keep image_path, moisture_percent, vs_fraction
out = df[["image_path","moisture_percent","vs_fraction"]].copy()
out.to_csv("dataset/train.csv", index=False)
print("Wrote dataset/train.csv with", len(out), "rows")
