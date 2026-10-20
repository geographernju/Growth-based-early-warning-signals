import os
import numpy as np
import pandas as pd
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import LineString
nc_file=r"H:/Climatic data/month/climate14.nc"
out_dir=r"D:/data/Map/Precipitation boundary"
out_shp=os.path.join(out_dir,"precipitation_boundary_1991_2020.shp")
os.makedirs(out_dir,exist_ok=True)
var_name="pre"
time_name="time"
lat_name="latitude"
lon_name="longitude"
center_lat=38.735911
center_lon=105.912572
lat_buffer=10*2/3
lon_buffer=10
contour_levels=[200,400,600]
interp_factor=5
lat_min=center_lat-lat_buffer
lat_max=center_lat+lat_buffer
lon_min=center_lon-lon_buffer
lon_max=center_lon+lon_buffer
def longest_segment(segs,lon_min,lon_max,lat_min,lat_max):
    best=None
    best_len=-1
    for seg in segs:
        if len(seg)<2:
            continue
        if seg[:,0].max()<lon_min or seg[:,0].min()>lon_max or seg[:,1].max()<lat_min or seg[:,1].min()>lat_max:
            continue
        seg_len=np.sum(np.hypot(np.diff(seg[:,0]),np.diff(seg[:,1])))
        if seg_len>best_len:
            best_len=seg_len
            best=seg
    return best
with xr.open_dataset(nc_file) as ds:
    da=ds[var_name]
    time_str=pd.Series(da[time_name].values).astype(str).str.replace(r"\.0$","",regex=True).str.zfill(6)
    time_values=pd.to_datetime(time_str,format="%Y%m",errors="coerce")
    if time_values.isna().any():
        raise ValueError("Invalid monthly time values")
    da=da.assign_coords({time_name:time_values.to_numpy()})
    da=da.sel({time_name:slice("1991-01-01","2020-12-31")})
    if da.sizes[time_name]==0:
        raise ValueError("No precipitation records for 1991-2020")
    if float(da[lon_name].max())>180:
        da=da.assign_coords({lon_name:((da[lon_name]+180)%360)-180})
    da=da.sortby(lat_name).sortby(lon_name)
    all_lats=da[lat_name].values
    all_lons=da[lon_name].values
    i0=max(np.searchsorted(all_lats,lat_min,side="left")-1,0)
    i1=min(np.searchsorted(all_lats,lat_max,side="right"),len(all_lats)-1)
    j0=max(np.searchsorted(all_lons,lon_min,side="left")-1,0)
    j1=min(np.searchsorted(all_lons,lon_max,side="right"),len(all_lons)-1)
    da=da.isel({lat_name:slice(i0,i1+1),lon_name:slice(j0,j1+1)})
    mean_annual_precip=da.resample({time_name:"YS"}).sum(dim=time_name).mean(dim=time_name)
    region=mean_annual_precip.where(lambda x:x>=0).load()
lat_vals=region[lat_name].values
lon_vals=region[lon_name].values
fine_lats=np.linspace(lat_vals.min(),lat_vals.max(),len(lat_vals)*interp_factor)
fine_lons=np.linspace(lon_vals.min(),lon_vals.max(),len(lon_vals)*interp_factor)
fine_region=region.interp({lat_name:fine_lats,lon_name:fine_lons},method="linear")
lon2d,lat2d=np.meshgrid(fine_region[lon_name].values,fine_region[lat_name].values)
fig,ax=plt.subplots()
cs=ax.contour(lon2d,lat2d,fine_region.values,levels=contour_levels)
records=[]
for i,level in enumerate(contour_levels):
    seg=longest_segment(cs.allsegs[i],lon_min,lon_max,lat_min,lat_max)
    if seg is None:
        print("Contour not found:",level)
        continue
    geom=LineString(seg)
    if geom.is_empty or geom.length==0:
        continue
    records.append({"level_mm":int(level),"period":"1991-2020","geometry":geom})
    print("Extracted:",level,"mm | Points:",len(seg))
plt.close(fig)
if not records:
    raise ValueError("No precipitation boundary segments were extracted")
gdf=gpd.GeoDataFrame(records,geometry="geometry",crs="EPSG:4326")
gdf.to_file(out_shp,driver="ESRI Shapefile",encoding="UTF-8")
print("Boundary count:",len(gdf))
print('✅ Saved file:',out_shp)