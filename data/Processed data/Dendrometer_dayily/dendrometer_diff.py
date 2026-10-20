import os
import pandas as pd
in_csv=r"D:/data/Dendrometer.csv"
out_csv=r"D:/data/Processed data/Dendrometer_dayily/dendrometer_diff.csv"
os.makedirs(os.path.dirname(out_csv),exist_ok=True)
df=pd.read_csv(in_csv,low_memory=False)
df.columns=df.columns.str.strip()
if "Date" not in df.columns:
    raise ValueError("Date column not found")
df["Date"]=pd.to_datetime(df["Date"],errors="coerce")
df=df.dropna(subset=["Date"]).copy()
exclude={"Date","Month","Year","year","month","sheet","Sheet","Time","time"}
cols=[c for c in df.columns if c not in exclude]
df[cols]=df[cols].apply(pd.to_numeric,errors="coerce")
cols=[c for c in cols if df[c].notna().any()]
if not cols:
    raise ValueError("No numeric measurement columns found")
df["Date"]=df["Date"]-pd.Timedelta(minutes=30)
df=df.set_index("Date")[cols].sort_index()
daily=df.resample("D").max()
daily_diff=daily.diff().clip(lower=0)
daily_diff.index.name="Date"
daily_diff=daily_diff.reset_index()
daily_diff["Date"]=daily_diff["Date"].dt.strftime("%Y/%m/%d")
daily_diff.to_csv(out_csv,index=False,encoding="utf-8-sig")
print("Measurement columns:",len(cols))
print("Daily records:",len(daily_diff))
print('✅ Saved file:',out_csv)