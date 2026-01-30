import pandas as pd

df = pd.read_csv("dataset/seed_labels.csv", dtype=str).fillna("")

def fix_path(p):
    p = p.replace("\\","/")
    # Remove dataset/seed_images/<cat>/ -> dataset/images/<cat>/
    if p.startswith("dataset/seed_images/"):
        p = p.replace("dataset/seed_images/", "dataset/images/")
    return p

df["image_path"] = df["image_path"].apply(fix_path)

df.to_csv("dataset/seed_labels.csv", index=False)
print("✔ seed_labels paths fixed.")
print(df[["image_path","category","health","labeled"]].head(10))
