import pandas as pd

df = pd.read_csv("dataset/train.csv")

print("\nMoisture Stats:")
print(df["moisture_percent"].describe())

print("\nVS Stats:")
print(df["vs_fraction"].describe())

print("\nSample rows:")
print(df.head())
