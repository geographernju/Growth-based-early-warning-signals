import os
import pandas as pd

infile=r"D:/data/Processed data/Dendrometer_dayily/dendrometer_diff.csv"
out_dir=r"D:/data/Processed data/Growth"
os.makedirs(out_dir,exist_ok=True)

date_ranges=[
    ("2019-06-14","2019-08-24"),
    ("2020-04-16","2020-08-24"),
    ("2021-04-01","2021-08-21"),
    ("2022-04-13","2022-08-29"),
    ("2023-04-06","2023-09-27"),
]

df=pd.read_csv(infile)
df["Date"]=pd.to_datetime(df["Date"],errors="coerce")
df=df.dropna(subset=["Date"]).copy()

mask=pd.Series(False,index=df.index)
for start,end in date_ranges:
    start=pd.to_datetime(start)
    end=pd.to_datetime(end)
    mask=mask|df["Date"].between(start,end)

df=df.loc[mask].copy()

all_cols=df.columns.tolist()
sph_cols=["Date"]+[c for c in all_cols if c!="Date" and "SPH" in str(c)]
spl_cols=["Date"]+[c for c in all_cols if c!="Date" and "SPL" in str(c)]
ssl_cols=["Date"]+[c for c in all_cols if c!="Date" and "SSL" in str(c)]

df_sph=df[sph_cols].copy()
df_spl=df[spl_cols].copy()
df_ssl=df[ssl_cols].copy()

df_sph["Date"]=df_sph["Date"].apply(lambda x:f"{x.year}/{x.month}/{x.day}")
df_spl["Date"]=df_spl["Date"].apply(lambda x:f"{x.year}/{x.month}/{x.day}")
df_ssl["Date"]=df_ssl["Date"].apply(lambda x:f"{x.year}/{x.month}/{x.day}")

df_sph.to_csv(os.path.join(out_dir,"SPH.csv"),index=False,encoding="utf-8-sig")
df_spl.to_csv(os.path.join(out_dir,"SPL.csv"),index=False,encoding="utf-8-sig")
df_ssl.to_csv(os.path.join(out_dir,"SSL.csv"),index=False,encoding="utf-8-sig")

print("Done")
print("SPH column count:",len(df_sph.columns)-1,"Output file:",os.path.join(out_dir,"SPH.csv"))
print("SPL column count:",len(df_spl.columns)-1,"Output file:",os.path.join(out_dir,"SPL.csv"))
print("SSL column count:",len(df_ssl.columns)-1,"Output file:",os.path.join(out_dir,"SSL.csv"))