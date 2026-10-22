import os
import numpy as np
import pandas as pd
from scipy.stats import zscore
root=r"D:/data/Processed data/Growth"
out_dir=os.path.join(root,"standardized")
os.makedirs(out_dir,exist_ok=True)
groups=["SPH","SPL","SSL"]
date_ranges=[
("2019-04-08","2019-08-24"),
("2020-04-16","2020-08-24"),
("2021-04-01","2021-08-21"),
("2022-04-13","2022-08-29"),
("2023-04-06","2023-08-27")
]
def biweight_mean(x):
    x=np.asarray(x,dtype=float)
    x=x[np.isfinite(x)]
    if x.size==0:
        return np.nan
    if x.size==1:
        return x[0]
    m=np.median(x)
    mad=np.median(np.abs(x-m))
    if not np.isfinite(mad) or mad==0:
        return np.mean(x)
    u=(x-m)/(9*mad)
    w=(1-u*u)**2
    w[np.abs(u)>=1]=0
    den=np.sum(w)
    if den==0:
        return np.mean(x)
    return np.sum(w*x)/den
def process_group(group):
    in_csv=os.path.join(root,f"{group}.csv")
    out_csv=os.path.join(out_dir,f"{group}.csv")
    tree=pd.read_csv(in_csv)
    tree["Date"]=pd.to_datetime(tree["Date"],errors="coerce")
    tree=tree.dropna(subset=["Date"]).sort_values("Date").copy()
    mask=pd.Series(False,index=tree.index)
    for start,end in date_ranges:
        mask|=tree["Date"].between(pd.Timestamp(start),pd.Timestamp(end))
    df=tree.loc[mask].copy()
    if df.empty:
        raise ValueError(f"No valid dates for {group}")
    cols=[c for c in df.columns if c!="Date"]
    data=df[cols].apply(pd.to_numeric,errors="coerce")
    valid_cols=data.columns[data.notna().sum(axis=0)>=2]
    data=data[valid_cols]
    if data.empty:
        raise ValueError(f"No valid tree series for {group}")
    zdata=pd.DataFrame(zscore(data,axis=0,nan_policy="omit"),columns=data.columns,index=data.index)
    zdata=zdata.dropna(axis=1,how="all")
    valid_mask=~zdata.isna().all(axis=1)
    zdata=zdata.loc[valid_mask]
    df=df.loc[valid_mask].copy()
    if zdata.empty:
        raise ValueError(f"No valid standardized observations for {group}")
    chrono=zdata.apply(biweight_mean,axis=1)
    out=pd.DataFrame({"Date":df["Date"].values,"Biweight_chronology":chrono.values})
    out=out.dropna(subset=["Biweight_chronology"]).sort_values("Date")
    if out.empty:
        raise ValueError(f"No valid chronology for {group}")
    out["Biweight_chronology"]=out["Biweight_chronology"]-out["Biweight_chronology"].min()
    out["Date"]=pd.to_datetime(out["Date"]).dt.strftime("%Y/%m/%d")
    out.to_csv(out_csv,index=False,encoding="utf-8-sig")
    print(f"Group: {group}")
    print(f"Trees: {zdata.shape[1]}")
    print(f"Valid days: {len(out)}")
    print(f"Period: {out['Date'].min()} - {out['Date'].max()}")
    print(f"Mean: {out['Biweight_chronology'].mean():.4f}")
    print(f"STD: {out['Biweight_chronology'].std():.4f}")
    print("✅ Saved file:",out_csv)
for group in groups:
    process_group(group)