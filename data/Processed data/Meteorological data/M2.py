import pandas as pd,os
infile=r"D:/data/Processed data/Meteorological data/M.csv"
outfile=r"D:/data/Processed data/Meteorological data/M2.csv"
os.makedirs(os.path.dirname(outfile),exist_ok=True)
df=pd.read_csv(infile)
df["Date"]=pd.to_datetime(df["Date"],errors="coerce")
mask2016=df["Date"].dt.year==2016
df.loc[mask2016,"Date"]=df.loc[mask2016,"Date"]-pd.Timedelta(days=2)
df["Date"]=df["Date"].dt.strftime("%Y/%m/%d")
df.to_csv(outfile,index=False,encoding="utf-8-sig")