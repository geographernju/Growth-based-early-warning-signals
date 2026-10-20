import os
import numpy as np
import pandas as pd
import xarray as xr

lat0=38.735911
lon0=105.912572
era_dir=r"H:\Climatic data\ERA5"
files=["mixed.nc","mixed2.nc","radiation.nc","RH-VPD.nc","soil.nc"]
spei_file=r"H:\Climatic data\SPEI\SPEI2025month\SPEI_0.5deg.nc"
out_dir=r"D:/data/Processed data/Climate"
os.makedirs(out_dir,exist_ok=True)

def ensure_datetime64(da):
    if np.issubdtype(da.dtype,np.datetime64):
        return da
    return xr.decode_cf(da.to_dataset(name="t"))["t"]

def find_latlon(ds):
    lat=None
    lon=None
    for k in ["latitude","lat"]:
        if k in ds.coords or k in ds.variables:
            lat=k
            break
    for k in ["longitude","lon"]:
        if k in ds.coords or k in ds.variables:
            lon=k
            break
    if lat is None or lon is None:
        raise ValueError("Latitude/longitude coordinates not found")
    if lat not in ds.coords:
        ds=ds.set_coords(lat)
    if lon not in ds.coords:
        ds=ds.set_coords(lon)
    return ds,lat,lon

def da_to_series(da,time_name="valid_time"):
    if time_name not in da.dims:
        return None
    da=da.squeeze(drop=True)
    extra_dims=[d for d in da.dims if d!=time_name]
    if len(extra_dims)>0:
        da=da.mean(dim=extra_dims,skipna=True)
    if da.ndim!=1 or da.dims[0]!=time_name:
        return None
    t=pd.to_datetime(da[time_name].values)
    v=np.asarray(da.values).reshape(-1)
    s=pd.Series(v,index=t)
    s=s[~s.index.isna()]
    s=s.sort_index()
    return s

all_dfs=[]

for fn in files:
    path=os.path.join(era_dir,fn)
    ds=xr.open_dataset(path,decode_times=True)
    if "valid_time" not in ds.coords and "valid_time" not in ds.variables:
        raise ValueError(f"{fn} is missing valid_time")
    ds=ds.assign_coords({"valid_time":ensure_datetime64(ds["valid_time"])})
    ds,lat_name,lon_name=find_latlon(ds)
    pt=ds.sel({lat_name:lat0,lon_name:lon0},method="nearest")
    year_all=pd.to_datetime(pt["valid_time"].values).year
    years=np.unique(year_all)
    rows=[]
    series_dict={}
    for v in pt.data_vars:
        s=da_to_series(pt[v],"valid_time")
        if s is not None and len(s)>0:
            series_dict[v]=s
    for y in years:
        row={"year":int(y)}
        for m in range(1,13):
            for v,s in series_dict.items():
                sm=s[(s.index.year==y)&(s.index.month==m)]
                row[f"{v}_month_{m}"]=float(sm.mean()) if len(sm)>0 else np.nan
        rows.append(row)
    df=pd.DataFrame(rows)
    all_dfs.append(df)

ds=xr.open_dataset(spei_file)
ds,lat_name,lon_name=find_latlon(ds)
pt=ds.sel({lat_name:lat0,lon_name:lon0},method="nearest")

time_raw=pt["time"].values.astype(int)
years=time_raw//100
months=time_raw%100

rows={}
for v in pt.data_vars:
    vals=pt[v].values
    for y,m,val in zip(years,months,vals):
        if y not in rows:
            rows[y]={"year":int(y)}
        rows[y][f"{v}_month_{int(m)}"]=float(val)

df_spei=pd.DataFrame(list(rows.values()))
all_dfs.append(df_spei)

df_all=all_dfs[0]
for df in all_dfs[1:]:
    df_all=pd.merge(df_all,df,on="year",how="outer")

df_all=df_all.sort_values("year").reset_index(drop=True)

out_csv=os.path.join(out_dir,"1.5climate.csv")
df_all.to_csv(out_csv,index=False,encoding="utf-8-sig")
print(out_csv)