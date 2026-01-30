import pandas as pd

df = pd.read_csv("dataset/labels.csv", dtype=str).fillna("")

def fix_master(p):
    p = p.replace("\\","/")
    # if path is like "leaf/xxx.jpg", convert to dataset/images/leaf/xxx.jpg
    if not p.startswith("dataset/"):
        if "/" in p:  # e.g. "leaf/10.jpg"
            p = "dataset/images/" + p
    return p

df["image_path"] = df["image_path"].apply(fix_master)

df.to_csv("dataset/labels.csv", index=False)
print("✔ labels.csv paths normalized.")
print(df.head(10))
