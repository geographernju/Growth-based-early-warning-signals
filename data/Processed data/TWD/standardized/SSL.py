import os
import pandas as pd
import numpy as np
from scipy.stats import zscore
tree_file=r"D:/data/Processed data/TWD/daily_twd_SSL.csv"
out_csv=r"D:/data/Processed data/TWD/standardized/daily_twd_SSL.csv"
os.makedirs(os.path.dirname(out_csv),exist_ok=True)
tree=pd.read_csv(tree_file)
tree["Date"]=pd.to_datetime(tree["Date"],errors="coerce")
tree=tree.dropna(subset=["Date"])
date_ranges=[
("2016-05-17","2016-08-25"),
("2017-04-07","2017-08-27"),
("2018-04-04","2018-08-18"),
("2019-04-08","2019-08-24"),
("2020-04-16","2020-08-24"),
("2021-04-01","2021-08-21"),
("2022-04-13","2022-08-29"),
("2023-04-06","2023-08-27"),
("2024-04-28","2024-08-26"),
("2025-04-18","2025-08-26")

]
mask=pd.Series(False,index=tree.index)
for start,end in date_ranges:
    mask|=(tree["Date"]>=pd.to_datetime(start))&(tree["Date"]<=pd.to_datetime(end))
df=tree[mask].copy()
cols=[c for c in df.columns if c!="Date"]
data=df[cols].apply(pd.to_numeric,errors="coerce")
zdata=pd.DataFrame(zscore(data,nan_policy="omit"),columns=data.columns,index=data.index)
valid_mask=~zdata.isna().all(axis=1)
zdata=zdata.loc[valid_mask].copy()
df=df.loc[valid_mask].copy()
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
chrono=zdata.apply(biweight_mean,axis=1)
out=pd.DataFrame({"Date":df["Date"].values,"Biweight_chronology":chrono.values})
growth=pd.to_numeric(out["Biweight_chronology"],errors="coerce")
if growth.notna().any():
    shift=growth.min()
    out["Biweight_chronology"]=growth-shift
out["Date"]=pd.to_datetime(out["Date"]).dt.strftime("%Y/%m/%d")
out.to_csv(out_csv,index=False,encoding="utf-8-sig")