import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
mpl.rcParams["font.family"]="Times New Roman"
mpl.rcParams["mathtext.fontset"]="custom"
mpl.rcParams["mathtext.rm"]="Times New Roman"
mpl.rcParams["savefig.dpi"]=600
mpl.rcParams["font.size"]=18
mpl.rcParams["axes.labelsize"]=20
mpl.rcParams["xtick.labelsize"]=16
mpl.rcParams["legend.fontsize"]=16
in_dir=r"D:/data/Processed data/TWD/standardized"
file_sph=os.path.join(in_dir,"daily_twd_SPH.csv")
file_spl=os.path.join(in_dir,"daily_twd_SPL.csv")
file_ssl=os.path.join(in_dir,"daily_twd_SSL.csv")
out_png=r"D:/results/Fig. 5.png"
os.makedirs(os.path.dirname(out_png),exist_ok=True)
years=[2019,2020,2021,2022,2023]
baseline_years=[2019,2020]
date_ranges={2019:("2019-06-14","2019-08-24"),2020:("2020-04-16","2020-08-24"),2021:("2021-04-01","2021-08-21"),2022:("2022-04-13","2022-08-29"),2023:("2023-04-06","2023-08-27")}
offset=1.25
living_color="#2873A8"
dead_color="#C84C42"
baseline_color="#6A6A6A"
tick_length=0.09
tick_width=1.8
def baseline_standardize_with_ref(series,ref):
    s=pd.to_numeric(series,errors="coerce")
    r=pd.to_numeric(ref,errors="coerce")
    m=r.mean()
    sd=r.std(ddof=0)
    if pd.isna(sd) or sd==0:
        return pd.Series(s-m,index=s.index)
    return (s-m)/sd
def read_file(path):
    df=pd.read_csv(path)
    df["Date"]=pd.to_datetime(df["Date"],errors="coerce")
    df["Biweight_chronology"]=pd.to_numeric(df["Biweight_chronology"],errors="coerce")
    df=df.dropna(subset=["Date","Biweight_chronology"]).sort_values("Date").copy()
    df["year"]=df["Date"].dt.year
    df["plot_date"]=pd.to_datetime("2000-"+df["Date"].dt.strftime("%m-%d"))
    return df
df_sph=read_file(file_sph)
df_spl=read_file(file_spl)
df_ssl=read_file(file_ssl)
df_sph["group"]="SPH"
df_spl["group"]="SPL"
df_live=pd.concat([df_sph,df_spl],ignore_index=True)
live_ref=df_live.loc[df_live["year"].isin(baseline_years),"Biweight_chronology"]
dead_ref=df_ssl.loc[df_ssl["year"].isin(baseline_years),"Biweight_chronology"]
df_live["relative_raw"]=baseline_standardize_with_ref(df_live["Biweight_chronology"],live_ref)
df_ssl["relative_raw"]=baseline_standardize_with_ref(df_ssl["Biweight_chronology"],dead_ref)
all_raw=pd.concat([df_live["relative_raw"],df_ssl["relative_raw"]],ignore_index=True)
raw_min=all_raw.min()
raw_max=all_raw.max()
if pd.isna(raw_min) or pd.isna(raw_max) or raw_max==raw_min:
    df_live["relative"]=0.0
    df_ssl["relative"]=0.0
else:
    df_live["relative"]=(df_live["relative_raw"]-raw_min)/(raw_max-raw_min)
    df_ssl["relative"]=(df_ssl["relative_raw"]-raw_min)/(raw_max-raw_min)
def filter_plot_dates(df):
    parts=[]
    for year in years:
        start,end=date_ranges[year]
        mask=(df["year"]==year)&(df["Date"]>=pd.Timestamp(start))&(df["Date"]<=pd.Timestamp(end))
        parts.append(df.loc[mask].copy())
    return pd.concat(parts,ignore_index=True)
df_live=filter_plot_dates(df_live)
df_ssl=filter_plot_dates(df_ssl)
df_live_range=df_live.groupby(["year","plot_date"],as_index=False)["relative"].agg(live_min="min",live_max="max")
plot_starts=[]
plot_ends=[]
for year in years:
    start,end=date_ranges[year]
    plot_starts.append(pd.Timestamp("2000-"+pd.Timestamp(start).strftime("%m-%d")))
    plot_ends.append(pd.Timestamp("2000-"+pd.Timestamp(end).strftime("%m-%d")))
xmin=min(plot_starts)
xmax=max(plot_ends)
xmin_plot=xmin-pd.Timedelta(days=6)
x_axis=xmin
x_tick_end=xmin+pd.Timedelta(days=2)
x_label=xmin-pd.Timedelta(days=1)
x_year=xmin+pd.Timedelta(days=3)
x_year_right=xmax-pd.Timedelta(days=3)
month_ticks=pd.date_range("2000-04-01","2000-08-01",freq="MS")
fig,ax=plt.subplots(figsize=(11.5,8))
fig.subplots_adjust(left=0.14,right=0.97,bottom=0.12,top=0.88)
for i,year in enumerate(years):
    base=(len(years)-1-i)*offset
    d1=df_live_range[df_live_range["year"]==year].sort_values("plot_date")
    d2=df_ssl[df_ssl["year"]==year].sort_values("plot_date")
    x1=d1["plot_date"].to_numpy()
    y1_low=(d1["live_min"]+base).to_numpy(dtype=float)
    y1_high=(d1["live_max"]+base).to_numpy(dtype=float)
    x2=d2["plot_date"].to_numpy()
    y2=(d2["relative"]+base).to_numpy(dtype=float)
    ax.plot([x_axis,xmax],[base,base],color=baseline_color,linewidth=0.75,alpha=0.75,zorder=1)
    ax.plot([x_axis,x_axis],[base,base+1],color=baseline_color,linewidth=0.9,zorder=2)
    ax.plot([x_axis,x_tick_end],[base+1,base+1],color=baseline_color,linewidth=0.9,zorder=2)
    for tick_date in month_ticks:
        if x_axis<=tick_date<=xmax:
            ax.plot([tick_date,tick_date],[base,base-tick_length],color=baseline_color,linewidth=tick_width,zorder=20,clip_on=False,solid_capstyle="butt")
    if len(d1)>0:
        ax.fill_between(x1,y1_low,y1_high,color=living_color,alpha=0.28,linewidth=0,zorder=3)
        ax.plot(x1,y1_low,color=living_color,linewidth=1.35,alpha=0.85,zorder=4)
        ax.plot(x1,y1_high,color=living_color,linewidth=1.35,alpha=0.85,zorder=4)
    if len(d2)>0:
        ax.plot(x2,y2,color=dead_color,linewidth=2.5,alpha=0.95,zorder=6,solid_capstyle="round")
    ax.text(x_label,base,"0",ha="right",va="center",fontsize=14,color="#444444")
    ax.text(x_label,base+1,"1",ha="right",va="center",fontsize=14,color="#444444")
    ax.text(x_year,base+0.98,"ABCDE"[i],ha="left",va="top",fontsize=18,fontweight="bold",color="#333333",zorder=10)
    ax.text(x_year_right,base+0.98,str(year),ha="right",va="top",fontsize=18,fontweight="bold",color="#333333",zorder=10)
event_2023=pd.Timestamp("2000-05-23")
base_2023=(len(years)-1-years.index(2023))*offset
ax.plot([event_2023,event_2023],[base_2023,base_2023+0.65],color="#333333",linestyle=(0,(4,3)),linewidth=1.6,zorder=8)
ax.text(event_2023,base_2023+0.75,"05/23",ha="center",va="bottom",fontsize=15,color="#333333",bbox=dict(facecolor="white",edgecolor="none",alpha=0.9,pad=1.5),zorder=9)
event_2021=pd.Timestamp("2000-04-29")
base_2021=(len(years)-1-years.index(2021))*offset
ax.plot([event_2021,event_2021],[base_2021,base_2021+0.65],color="#333333",linestyle=(0,(4,3)),linewidth=1.6,zorder=8)
ax.text(event_2021,base_2021+0.75,"04/29",ha="center",va="bottom",fontsize=15,color="#333333",bbox=dict(facecolor="white",edgecolor="none",alpha=0.9,pad=1.5),zorder=9)
ax.set_xlim(xmin_plot,xmax)
ax.set_ylim(0,(len(years)-1)*offset+1.12)
ax.set_yticks([])
ax.set_ylabel("Normalized TWD",fontsize=20,labelpad=0)
ax.set_xlabel("Date",fontsize=20,labelpad=9)
ax.xaxis.set_major_locator(mdates.MonthLocator(bymonthday=1))
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
ax.tick_params(axis="x",bottom=False,labelbottom=True,labelsize=17,pad=7)
ax.spines["left"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["top"].set_visible(False)
ax.spines["bottom"].set_visible(False)
legend_elements=[Patch(facecolor=living_color,edgecolor=living_color,alpha=0.28,label="Live trees (SPH–SPL range)"),Line2D([0],[0],color=dead_color,linewidth=2.5,label="Dead trees (SSL)")]
ax.legend(handles=legend_elements,loc="upper center",bbox_to_anchor=(0.54,1.00),ncol=2,frameon=False,handlelength=2.4,handletextpad=0.7,columnspacing=2.0,fontsize=16)
plt.savefig(out_png,dpi=600,bbox_inches="tight")
plt.close()
print('✅ Saved figure:', out_png)