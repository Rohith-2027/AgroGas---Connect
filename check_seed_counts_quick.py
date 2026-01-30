import pandas as pd

df = pd.read_csv("dataset/seed_labels.csv")
print("Total seed labeled:", (df["labeled"]=="1").sum())
print("\nCategory counts:")
print(df["category"].value_counts())
print("\nHealth counts:")
print(df["health"].value_counts())
