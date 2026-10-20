
import os
import numpy as np
import xarray as xr
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy
from cartopy.io.shapereader import NEShpDownloader
_ne_template=r"D:/data/map/natural_earth/{category}/{name}/{resolution}/ne_{resolution}_{name}.shp"
cartopy.config["downloaders"][("shapefiles","natural_earth")]=NEShpDownloader(target_path_template=_ne_template,pre_downloaded_path_template=_ne_template)
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from cartopy.mpl.ticker import LongitudeFormatter,LatitudeFormatter
from matplotlib.colors import ListedColormap,BoundaryNorm
from matplotlib.patches import Rectangle,Patch
from matplotlib.lines import Line2D
from matplotlib.collections import LineCollection
from matplotlib.legend_handler import HandlerTuple
plt.rcParams["font.family"]="Times New Roman"
plt.rcParams["mathtext.fontset"]="custom"
plt.rcParams["mathtext.rm"]="Times New Roman"
plt.rcParams["figure.dpi"]=600
plt.rcParams["savefig.dpi"]=600
lu_file=r"H:\Land use\C3S-LC-L4-LCCS-Map-300m-P1Y-2022-v2.1.1.nc"
shp_file=r"D:/data/map/monsoon_non_monsoon_boundary/monsoon_non_monsoon_boundary.shp"
precip_shp=r"D:/data/Map/Precipitation boundary/precipitation_boundary_1991_2020.shp"
boundary_dir=r"D:/data/map/administrative_boundaries"
marine_shp=r"D:/data/map/maritime_boundaries/korea_japan_maritime_boundary.shp"
boundary_files={"national":os.path.join(boundary_dir,"national_boundary.shp"),"national2":os.path.join(boundary_dir,"pakistan_india_boundary.shp"),"undetermined":os.path.join(boundary_dir,"china_boundary_dashed_lower.shp"),"national_upper":os.path.join(boundary_dir,"china_boundary_solid_upper.shp"),"military1":os.path.join(boundary_dir,"kashmir_boundary_dashed.shp"),"military2":os.path.join(boundary_dir,"north_south_korea_boundary.shp"),"regional":os.path.join(boundary_dir,"kashmir_region.shp")}
out_file=r"D:/results/Fig. 0.png"
center_lat,center_lon=38.735911,105.912572
lat_buffer,lon_buffer=10*2/3,10
main_left,main_bottom,main_width,main_height=0.10,0.10,0.78,0.82
inset_width,inset_height=0.28,0.28
inset_extent=[65,145,5,60]
inset_left_offset=0.003
inset_kashmir_cross_count=2
inset_korea_cross_count=1
national_linewidth=0.25
special_linewidth=0.35
contour_color="#1f78b4"
forest_vals=[50,60,61,62,70,71,72,80,81,82,90,160,170]
grass_vals=[40,100,110,120,121,122,130,140,180]
desert_vals=[150,151,152,153,190,200,201,202,220]
crop_vals=[10,11,12,20,30]
water_vals=[210]
grass_vals=grass_vals+water_vals
lu_cmap=ListedColormap(["#228B22","#ADFF2F","#DEB887","#FFFF00"])
lu_norm=BoundaryNorm([0.5,1.5,2.5,3.5,4.5],lu_cmap.N)
capital_cities=[("Beijing",116.4074,39.9042),("Tianjin",117.2000,39.1333),("Shijiazhuang",114.5149,38.0428),("Taiyuan",112.5492,37.8570),("Hohhot",111.7492,40.8427),("Shenyang",123.4315,41.8057),("Changchun",125.3235,43.8171),("Harbin",126.6424,45.7567),("Shanghai",121.4737,31.2304),("Nanjing",118.7969,32.0603),("Hangzhou",120.1551,30.2741),("Hefei",117.2272,31.8206),("Fuzhou",119.2965,26.0745),("Nanchang",115.8582,28.6829),("Jinan",117.1201,36.6512),("Zhengzhou",113.6254,34.7466),("Wuhan",114.3054,30.5931),("Changsha",112.9388,28.2282),("Guangzhou",113.2644,23.1291),("Nanning",108.3669,22.8170),("Haikou",110.3312,20.0310),("Chongqing",106.5516,29.5630),("Chengdu",104.0665,30.5728),("Guiyang",106.6302,26.6470),("Kunming",102.8329,24.8801),("Lhasa",91.1322,29.6604),("Xi'an",108.9398,34.3416),("Lanzhou",103.8343,36.0611),("Xining",101.7782,36.6171),("Yinchuan",106.2309,38.4872),("Urumqi",87.6168,43.8256),("Taipei",121.5654,25.0330)]
def to_wgs84(gdf):
    return gdf.set_crs("EPSG:4326") if gdf.crs is None else gdf.to_crs("EPSG:4326")
def base_map(ax,extent):
    ax.set_extent(extent,crs=ccrs.PlateCarree())
    ax.add_feature(cfeature.LAND,facecolor="white",edgecolor="none",zorder=0)
    ax.add_feature(cfeature.OCEAN,facecolor="white",edgecolor="none",zorder=0)
def get_coord_name(obj,cands):
    names=list(obj.coords)+list(obj.dims)
    for c in cands:
        if c in names:
            return c
    low_cands=[i.lower() for i in cands]
    for n in names:
        if n.lower() in low_cands:
            return n
    for n in names:
        low=n.lower()
        if any(k in low for k in ["lat","latitude","y"]) and any(k in low_cands for k in ["lat","latitude","y"]):
            return n
        if any(k in low for k in ["lon","longitude","x"]) and any(k in low_cands for k in ["lon","longitude","x"]):
            return n
    raise ValueError("Coordinate name not found")
def get_lu_var(ds):
    prefs=["lccs_class","land_cover","landcover","classification","Band1","band1","LC_Type1"]
    for p in prefs:
        if p in ds.data_vars:
            return p
    vars2=[v for v in ds.data_vars if ds[v].ndim>=2]
    if len(vars2)==0:
        raise ValueError("No suitable land-use variable found")
    return vars2[0]
def label_on_line(seg,lon_min,lon_max,lat_min,lat_max):
    pts=seg[(seg[:,0]>=lon_min+0.8)&(seg[:,0]<=lon_max-0.8)&(seg[:,1]>=lat_min+0.5)&(seg[:,1]<=lat_max-0.5)]
    if len(pts)<3:
        pts=seg
    target_x=lon_min+0.20*(lon_max-lon_min)
    idx=np.argmin(np.abs(pts[:,0]-target_x))
    x=float(np.clip(pts[idx,0],lon_min+0.8,lon_max-0.8))
    y=float(np.clip(pts[idx,1],lat_min+0.5,lat_max-0.5))
    j=np.argmin((seg[:,0]-x)**2+(seg[:,1]-y)**2)
    j0=max(j-1,0)
    j1=min(j+1,len(seg)-1)
    dx=seg[j1,0]-seg[j0,0]
    dy=seg[j1,1]-seg[j0,1]
    ang=np.degrees(np.arctan2(dy,dx))
    if ang>90:
        ang-=180
    if ang<-90:
        ang+=180
    return x,y,ang
def geom_to_lines(geom):
    lines=[]
    if geom is None or geom.is_empty:
        return lines
    gt=geom.geom_type
    if gt=="LineString":
        lines.append(np.asarray(geom.coords))
    elif gt=="MultiLineString":
        for g in geom.geoms:
            lines.extend(geom_to_lines(g))
    elif gt=="Polygon":
        lines.append(np.asarray(geom.exterior.coords))
        for ring in geom.interiors:
            lines.append(np.asarray(ring.coords))
    elif gt=="MultiPolygon":
        for g in geom.geoms:
            lines.extend(geom_to_lines(g))
    elif gt=="GeometryCollection":
        for g in geom.geoms:
            lines.extend(geom_to_lines(g))
    return lines
def gdf_to_lines(gdf):
    lines=[]
    for geom in gdf.geometry:
        lines.extend(geom_to_lines(geom))
    return lines
def add_lines(ax,lines,color="black",linewidth=0.5,linestyle="-",zorder=4):
    if not lines:
        return
    lc=LineCollection(lines,colors=color,linewidths=linewidth,linestyles=linestyle,zorder=zorder,transform=ccrs.PlateCarree()._as_mpl_transform(ax))
    ax.add_collection(lc)
def draw_halo_dashed_boundary(ax,lines,scale=1.0,linewidth=0.35,dashes=(10,5),zorder=6):
    add_lines(ax,lines,color="white",linewidth=(linewidth+0.35)*scale,linestyle="-",zorder=zorder-0.1)
    add_lines(ax,lines,color="black",linewidth=linewidth*scale,linestyle=(0,dashes),zorder=zorder)
def draw_cross_boundary(ax,gdf,scale=1.0,spacing=2.1,zorder=7,count=None):
    lines=[]
    for geom in gdf.geometry:
        if geom is None or geom.is_empty:
            continue
        if geom.geom_type=="LineString":
            parts=[geom]
        elif geom.geom_type=="MultiLineString":
            parts=list(geom.geoms)
        elif geom.geom_type=="GeometryCollection":
            parts=[g for g in geom.geoms if g.geom_type=="LineString"]
        else:
            parts=[]
        for line in parts:
            if line.length<=0:
                continue
            x,y=line.xy
            ax.plot(x,y,color="white",linewidth=0.75*scale,linestyle=(0,(4,3)),transform=ccrs.PlateCarree(),zorder=zorder-0.2)
            ax.plot(x,y,color="black",linewidth=special_linewidth*scale,linestyle=(0,(4,3)),transform=ccrs.PlateCarree(),zorder=zorder-0.1)
            lines.append(line)
    points=[]
    if count is None:
        for line in lines:
            points.extend([line.interpolate(d) for d in np.arange(spacing*0.5,line.length,spacing)])
    elif lines and count>0:
        lengths=np.array([line.length for line in lines])
        cumulative=np.cumsum(lengths)
        for target in np.linspace(0,cumulative[-1],count+2)[1:-1]:
            k=min(int(np.searchsorted(cumulative,target,side="right")),len(lines)-1)
            previous=cumulative[k-1] if k>0 else 0
            points.append(lines[k].interpolate(float(target-previous)))
    if points:
        px=[p.x for p in points]
        py=[p.y for p in points]
        ax.scatter(px,py,marker="x",s=15*scale,linewidths=1.15*scale,color="white",transform=ccrs.PlateCarree(),zorder=zorder)
        ax.scatter(px,py,marker="x",s=9*scale,linewidths=0.60*scale,color="black",transform=ccrs.PlateCarree(),zorder=zorder+0.1)
def draw_boundaries(ax,scale=1.0,inset=False):
    for key in ["national","national2","national_upper"]:
        add_lines(ax,boundary_lines[key],color="black",linewidth=national_linewidth*scale,linestyle="-",zorder=4)
    add_lines(ax,marine_lines,color="black",linewidth=national_linewidth*scale,linestyle="-",zorder=4)
    draw_halo_dashed_boundary(ax,boundary_lines["undetermined"],scale=scale,linewidth=special_linewidth,dashes=(10,5),zorder=6)
    if inset:
        draw_cross_boundary(ax,boundary_layers["military1"],scale=scale,spacing=2.1/scale,zorder=7,count=inset_kashmir_cross_count)
        draw_cross_boundary(ax,boundary_layers["military2"],scale=scale,spacing=2.1/scale,zorder=7,count=inset_korea_cross_count)
    else:
        draw_cross_boundary(ax,boundary_layers["military1"],scale=scale,spacing=2.1/scale,zorder=7)
        draw_cross_boundary(ax,boundary_layers["military2"],scale=scale,spacing=2.1/scale,zorder=7)
    draw_halo_dashed_boundary(ax,boundary_lines["regional"],scale=scale,linewidth=special_linewidth,dashes=(12,5.5),zorder=6)
def draw_capitals(ax,extent,fontsize=8,marker_size=70):
    xmin,xmax,ymin,ymax=extent
    for name,lon,lat in capital_cities:
        if xmin<=lon<=xmax and ymin<=lat<=ymax:
            ax.scatter(lon,lat,s=marker_size,facecolors="white",edgecolors="black",marker="o",linewidths=1.05,transform=ccrs.PlateCarree(),zorder=61)
            ax.scatter(lon,lat,s=marker_size*0.28,facecolors="white",edgecolors="black",marker="o",linewidths=0.80,transform=ccrs.PlateCarree(),zorder=62)
            ax.annotate(name,xy=(lon,lat),xycoords=ccrs.PlateCarree()._as_mpl_transform(ax),xytext=(0,-7),textcoords="offset points",fontsize=fontsize,color="black",ha="center",va="top",zorder=63,bbox=dict(facecolor="white",edgecolor="none",pad=0.05,alpha=0.75))
boundary_layers={k:to_wgs84(gpd.read_file(v)) for k,v in boundary_files.items()}
marine_boundary=to_wgs84(gpd.read_file(marine_shp))
boundary_lines={k:gdf_to_lines(v) for k,v in boundary_layers.items()}
marine_lines=gdf_to_lines(marine_boundary)
lat_min,lat_max=center_lat-lat_buffer,center_lat+lat_buffer
lon_min,lon_max=center_lon-lon_buffer,center_lon+lon_buffer
lu_ds=xr.open_dataset(lu_file)
lu_var=get_lu_var(lu_ds)
lu_da=lu_ds[lu_var]
lu_lat=get_coord_name(lu_da,["lat","latitude","y"])
lu_lon=get_coord_name(lu_da,["lon","longitude","x"])
extra_dims=[d for d in lu_da.dims if d not in [lu_lat,lu_lon]]
for d in extra_dims:
    lu_da=lu_da.isel({d:0})
if float(lu_da[lu_lon].max())>180:
    lu_da=lu_da.assign_coords({lu_lon:((lu_da[lu_lon]+180)%360)-180}).sortby(lu_lon)
lu_da=lu_da.transpose(lu_lat,lu_lon).sortby(lu_lat).sortby(lu_lon)
lat_all=lu_da[lu_lat].values
lon_all=lu_da[lu_lon].values
lat_mask=(lat_all>=lat_min)&(lat_all<=lat_max)
lon_mask=(lon_all>=lon_min)&(lon_all<=lon_max)
lat_sub=lat_all[lat_mask]
lon_sub=lon_all[lon_mask]
cls_arr=lu_da.isel({lu_lat:np.flatnonzero(lat_mask),lu_lon:np.flatnonzero(lon_mask)}).values
new=np.full(cls_arr.shape,np.nan)
new[np.isin(cls_arr,forest_vals)]=1
new[np.isin(cls_arr,grass_vals)]=2
new[np.isin(cls_arr,desert_vals)]=3
new[np.isin(cls_arr,crop_vals)]=4
new=np.ma.masked_invalid(new)
monsoon_line=to_wgs84(gpd.read_file(shp_file))
precip_gdf=to_wgs84(gpd.read_file(precip_shp))
if "level_mm" not in precip_gdf.columns:
    raise ValueError("level_mm not found in precipitation boundary shapefile")
fig=plt.figure(figsize=(8,6))
ax=fig.add_axes([main_left,main_bottom,main_width,main_height],projection=ccrs.PlateCarree())
base_map(ax,[lon_min,lon_max,lat_min,lat_max])
ax.pcolormesh(lon_sub,lat_sub,new,cmap=lu_cmap,norm=lu_norm,shading="auto",transform=ccrs.PlateCarree(),zorder=1)
ax.add_feature(cfeature.LAKES.with_scale("50m"),facecolor="#4da3ff",edgecolor="#4da3ff",linewidth=0.4,zorder=3)
for level in [200,400,600]:
    level_gdf=precip_gdf[precip_gdf["level_mm"]==level]
    segments=[]
    for geom in level_gdf.geometry:
        for seg in geom_to_lines(geom):
            if len(seg)<2:
                continue
            segments.append(seg)
            ax.plot(seg[:,0],seg[:,1],color=contour_color,linestyle="--",linewidth=1.5,transform=ccrs.PlateCarree(),zorder=4)
    if segments:
        seg=max(segments,key=lambda a:np.sum(np.hypot(np.diff(a[:,0]),np.diff(a[:,1]))))
        xlab,ylab,ang=label_on_line(seg,lon_min,lon_max,lat_min,lat_max)
        ax.text(xlab,ylab,f"{level} mm",fontsize=12,ha="center",va="center",rotation=ang,rotation_mode="anchor",color=contour_color,transform=ccrs.PlateCarree(),bbox=dict(facecolor="white",edgecolor="none",pad=0.10,alpha=1.0),zorder=5,clip_on=True)
draw_boundaries(ax,1.0,inset=False)
draw_capitals(ax,[lon_min,lon_max,lat_min,lat_max],fontsize=8,marker_size=70)
ax.scatter(center_lon,center_lat,s=85,facecolors="none",edgecolors="red",marker="o",linewidths=1.3,transform=ccrs.PlateCarree(),zorder=65)
xticks=np.arange(np.ceil(lon_min/5)*5,np.floor(lon_max/5)*5+0.1,5)
yticks=np.arange(np.ceil(lat_min/2)*2,np.floor(lat_max/2)*2+0.1,2)
ax.set_xticks(xticks,crs=ccrs.PlateCarree())
ax.set_yticks(yticks,crs=ccrs.PlateCarree())
ax.xaxis.set_major_formatter(LongitudeFormatter(number_format=".0f"))
ax.yaxis.set_major_formatter(LatitudeFormatter(number_format=".0f"))
ax.tick_params(axis="both",which="major",direction="out",length=4,width=0.8,labelsize=10,top=False,right=False)
city_legend=(Line2D([0],[0],marker="o",markerfacecolor="white",markeredgecolor="black",markeredgewidth=1.05,markersize=7,linestyle="None"),Line2D([0],[0],marker="o",markerfacecolor="white",markeredgecolor="black",markeredgewidth=0.80,markersize=7*np.sqrt(0.28),linestyle="None"))
legend_elements=[Patch(facecolor="#228B22",edgecolor="none"),Patch(facecolor="#ADFF2F",edgecolor="none"),Patch(facecolor="#DEB887",edgecolor="none"),Patch(facecolor="#FFFF00",edgecolor="none"),Patch(facecolor="#4da3ff",edgecolor="none"),Line2D([0],[0],marker="o",color="red",markerfacecolor="none",markeredgecolor="red",markersize=8,linewidth=0),city_legend,Line2D([0],[0],color=contour_color,lw=1.5,linestyle="--"),Line2D([0],[0],color="red",lw=1.4,linestyle="--"),Line2D([0],[0],color="black",lw=national_linewidth)]
legend_labels=["Forest","Grassland","Desert","Cropland","Lakes","Study site","City","Precipitation boundary","Monsoon boundary","National boundary"]
leg=ax.legend(handles=legend_elements,labels=legend_labels,handler_map={tuple:HandlerTuple(ndivide=1,pad=0)},loc="upper right",bbox_to_anchor=(0.995,0.995),frameon=True,facecolor="white",framealpha=0.95,edgecolor="none",fontsize=8.5,borderpad=0.35,labelspacing=0.45,handlelength=2.0,handletextpad=0.6,ncol=2,columnspacing=0.9)
leg.set_zorder(70)
fig.canvas.draw()
renderer=fig.canvas.get_renderer()
map_bbox_fig=fig.transFigure.inverted().transform_bbox(ax.patch.get_window_extent(renderer))
inset_left=max(map_bbox_fig.x0-0.022-inset_left_offset,0.01)
inset_bottom=map_bbox_fig.y1-inset_height
axins=fig.add_axes([inset_left,inset_bottom,inset_width,inset_height],projection=ccrs.PlateCarree())
base_map(axins,inset_extent)
draw_boundaries(axins,0.85,inset=True)
monsoon_line.plot(ax=axins,facecolor="none",edgecolor="red",linewidth=0.8,linestyle="--",transform=ccrs.PlateCarree(),zorder=45)
axins.add_patch(Rectangle((lon_min,lat_min),lon_max-lon_min,lat_max-lat_min,fill=False,edgecolor="black",linewidth=1.2,transform=ccrs.PlateCarree(),zorder=50))
axins.scatter(center_lon,center_lat,s=35,facecolors="none",edgecolors="red",marker="o",linewidths=0.9,transform=ccrs.PlateCarree(),zorder=60)
axins.set_xticks([])
axins.set_yticks([])
os.makedirs(os.path.dirname(out_file),exist_ok=True)
plt.savefig(out_file,bbox_inches="tight")
plt.close()
print('✅ Saved figure:', out_file)
