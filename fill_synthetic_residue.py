# fill_synthetic_residue.py
import pandas as pd, os, random, statistics
from pathlib import Path
from PIL import Image

CSV = Path("dataset/labels.csv")
IMG_ROOT = CSV.parent

df = pd.read_csv(CSV)
residue_mask = (df["category"]=="residue")
to_fill = residue_mask & (df["mass_kg"].isnull() | df["mass_kg"].astype(str).str.strip()=="")
print("Residue rows to fill:", int(to_fill.sum()))
if int(to_fill.sum())==0:
    print("Nothing to fill.")
    exit(0)

# compute median area across dataset
areas=[]
for i,row in df.iterrows():
    p = IMG_ROOT / row["image_path"]
    try:
        with Image.open(p) as im:
            w,h = im.size
    except:
        w,h = (640,480)
    areas.append(w*h)
median_area = statistics.median(areas) if areas else 640*480

def estimate(area):
    base = random.uniform(0.5,3.0)
    scale = max(0.4, min(area/median_area, 3.0))
    noise = random.uniform(0.85,1.15)
    mass = round(max(0.1, min(base*scale*noise, 12.0)),3)
    moisture = round(random.uniform(53.0,66.0) + random.gauss(0,1.8),2)
    factor = random.uniform(0.80,0.95)
    vs = round(max(0.2, min((100-moisture)/100*factor,0.95)),3)
    return mass,moisture,vs

for i in df[to_fill].index:
    p = IMG_ROOT / df.at[i,"image_path"]
    try:
        with Image.open(p) as im:
            w,h = im.size
    except:
        w,h = (640,480)
    mass,moisture,vs = estimate(w*h)
    df.at[i,"mass_kg"]=mass
    df.at[i,"moisture_percent"]=moisture
    df.at[i,"vs_fraction"]=vs
    df.at[i,"notes"]="synthetic_generated"
    df.at[i,"synthetic"]=1
    df.at[i,"labeled"]=1

df.to_csv(CSV,index=False)
print("Filled synthetic values and saved CSV.")
