import pandas as pd

df = pd.read_csv("dataset/labels.csv")

print("\nCategory counts:")
print(df['category'].value_counts(dropna=False))

print("\nSample rows:")
print(df.head())
