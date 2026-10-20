import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.patches import Patch

mpl.rcParams["font.family"]="Times New Roman"
mpl.rcParams["mathtext.fontset"]="custom"
mpl.rcParams["mathtext.rm"]="Times New Roman"
mpl.rcParams["mathtext.it"]="Times New Roman:italic"
mpl.rcParams["font.size"]=20
mpl.rcParams["axes.labelsize"]=22
mpl.rcParams["xtick.labelsize"]=18
mpl.rcParams["ytick.labelsize"]=19
mpl.rcParams["legend.fontsize"]=17
mpl.rcParams["axes.linewidth"]=1.4

growth_files={
    "SPH":r"D:/data/Processed data/Growth/standardized/SPH.csv",
    "SPL":r"D:/data/Processed data/Growth/standardized/SPL.csv",
    "SSL":r"D:/data/Processed data/Growth/standardized/SSL.csv"
}
rain_file=r"D:/data/Processed data/meteorological data/M1.csv"
out_png=r"D:/results/Fig. 7.png"
os.makedirs(os.path.dirname(out_png),exist_ok=True)

live_color="#2873A8"
dead_color="#C84C42"
bin_edges=[0,2,5,10,20,np.inf]
bin_labels=["0–2","2–5","5–10","10–20",">20"]
threshold=90
min_count=5
curve_min_count=30
rank_grid=np.linspace(0,100,201)

rain_df=pd.read_csv(rain_file)
rain_df["Date"]=pd.to_datetime(rain_df["Date"],errors="coerce")
rain_df["Rain"]=pd.to_numeric(rain_df["Rain"],errors="coerce")*48
rain_df=rain_df.dropna(subset=["Date","Rain"])
rain_df=rain_df[rain_df["Rain"]>=0].copy()

def prepare_group(path,name):
    df=pd.read_csv(path)
    df["Date"]=pd.to_datetime(df["Date"],errors="coerce")
    growth_col=[c for c in df.columns if c!="Date"][0]
    df["Growth"]=pd.to_numeric(df[growth_col],errors="coerce")
    df=df[["Date","Growth"]].dropna()
    df=pd.merge(df,rain_df[["Date","Rain"]],on="Date",how="inner").sort_values("Date")
    df["Year"]=df["Date"].dt.year
    df=df[df["Year"].between(2019,2023)].copy()
    df["Source"]=name
    df["Growth_percentile"]=df.groupby("Year")["Growth"].rank(pct=True)*100
    df["High_growth"]=(df["Growth_percentile"]>threshold).astype(int)
    df["Positive_anomaly"]=(df["Growth"]-df.groupby("Year")["Growth"].transform("median")).clip(lower=0)
    df["Rain_class"]=pd.cut(df["Rain"].where(df["Rain"]>0),bins=bin_edges,labels=bin_labels,include_lowest=False)
    return df

data={name:prepare_group(path,name) for name,path in growth_files.items()}

def concentration_curves(df):
    curves={}
    for year,sub in df.groupby("Year"):
        values=sub.loc[sub["Positive_anomaly"]>0,"Positive_anomaly"].to_numpy(dtype=float)
        values=values[np.isfinite(values)]
        if len(values)<curve_min_count or values.sum()<=0:
            continue
        values=np.sort(values)[::-1]
        cumulative=np.concatenate(([0],np.cumsum(values)/values.sum()*100))
        fractions=np.linspace(0,100,len(values)+1)
        curves[int(year)]=np.interp(rank_grid,fractions,cumulative)
    return curves

curves_sph=concentration_curves(data["SPH"])
curves_spl=concentration_curves(data["SPL"])
curves_ssl=concentration_curves(data["SSL"])

live_curves={}
dead_curves={}
for year in range(2019,2024):
    if year in curves_sph and year in curves_spl:
        live_curves[year]=(curves_sph[year]+curves_spl[year])/2
    if year in curves_ssl:
        dead_curves[year]=curves_ssl[year]

def curve_summary(curves):
    if len(curves)==0:
        return None
    arr=np.vstack([curves[year] for year in sorted(curves)])
    return {"mean":np.mean(arr,axis=0),"low":np.min(arr,axis=0),"high":np.max(arr,axis=0)}

live_summary=curve_summary(live_curves)
dead_summary=curve_summary(dead_curves)

if live_summary is None or dead_summary is None:
    raise ValueError("Insufficient positive-anomaly days for concentration curves")

live_df=pd.concat([data["SPH"],data["SPL"]],ignore_index=True)
dead_df=data["SSL"]

def wilson_interval(k,n):
    p=k/n
    z=1.96
    denom=1+z*z/n
    center=(p+z*z/(2*n))/denom
    half=z*np.sqrt(p*(1-p)/n+z*z/(4*n*n))/denom
    return p*100,max(0,(center-half)*100),min(100,(center+half)*100)

fig,(ax1,ax2)=plt.subplots(1,2,figsize=(17.5,7))
fig.subplots_adjust(left=0.09,right=0.97,bottom=0.17,top=0.93,wspace=0.20)

ax1.plot([0,100],[0,100],color="#9A9A9A",linestyle="--",linewidth=1.5,alpha=0.8,zorder=1)

for summary,color,name in [
    (live_summary,live_color,"Live trees (SPH + SPL)"),
    (dead_summary,dead_color,"Dead trees (SSL)")
]:
    ax1.fill_between(rank_grid,summary["low"],summary["high"],color=color,alpha=0.16,linewidth=0,zorder=2)
    ax1.plot(rank_grid,summary["mean"],color=color,linewidth=3.0,label=name,zorder=4)

live_top20=np.interp(20,rank_grid,live_summary["mean"])
dead_top20=np.interp(20,rank_grid,dead_summary["mean"])

ax1.scatter(20,live_top20,color=live_color,s=80,edgecolor="white",linewidth=1.0,zorder=6)
ax1.scatter(20,dead_top20,color=dead_color,s=80,edgecolor="white",linewidth=1.0,zorder=6)

ax1.text(17.5,dead_top20+5,f"{int(round(dead_top20))}",color=dead_color,fontsize=19,fontweight="bold",ha="right",va="bottom",zorder=8)
ax1.text(22.5,live_top20-5,f"{int(round(live_top20))}",color=live_color,fontsize=19,fontweight="bold",ha="left",va="top",zorder=8)

ax1.axvline(20,color="#777777",linestyle=":",linewidth=1.5,alpha=0.8,zorder=1)

ax1.set_xlim(0,100)
ax1.set_ylim(0,105)
ax1.set_xticks([0,20,40,60,80,100])
ax1.set_yticks(np.arange(0,101,20))
ax1.set_xlabel("Top-ranked growth days (%)",fontsize=22,labelpad=10)
ax1.set_ylabel("Cumulative growth share (%)",fontsize=22)
ax1.legend(loc="upper right",bbox_to_anchor=(0.98,0.82),frameon=False,fontsize=17,handlelength=2.6)

for i,label in enumerate(bin_labels):
    for df,shift,color in [(live_df,-0.18,live_color),(dead_df,0.18,dead_color)]:
        d=df[df["Rain_class"]==label]
        n=len(d)
        if n<min_count:
            continue
        k=int(d["High_growth"].sum())
        prob,lower,upper=wilson_interval(k,n)
        xpos=i+shift
        ax2.bar(xpos,prob,width=0.34,color=color,alpha=0.85,edgecolor=color,linewidth=1.0,zorder=3)
        ax2.errorbar(
            xpos,prob,
            yerr=np.array([[max(0,prob-lower)],[max(0,upper-prob)]]),
            fmt="none",ecolor="#333333",elinewidth=1.5,capsize=4,capthick=1.5,zorder=5
        )

ax2.axhline(10,color="gray",linestyle=":",linewidth=1.5,alpha=0.65,zorder=1)
ax2.set_xticks(np.arange(len(bin_labels)))
ax2.set_xticklabels(bin_labels)
ax2.set_xlim(-0.55,len(bin_labels)-0.45)
ax2.set_ylim(0,105)
ax2.set_yticks(np.arange(0,101,20))
ax2.set_xlabel("Daily precipitation (mm)",fontsize=22,labelpad=10)
ax2.set_ylabel("High-growth occurrence (%)",fontsize=22)

for ax in [ax1,ax2]:
    ax.tick_params(axis="both",which="major",direction="out",length=6,width=1.4,labelsize=19)
    ax.spines["top"].set_linewidth(1.4)
    ax.spines["right"].set_linewidth(1.4)

legend_handles=[
    Patch(facecolor=live_color,edgecolor=live_color,alpha=0.85,label="Live trees (SPH + SPL)"),
    Patch(facecolor=dead_color,edgecolor=dead_color,alpha=0.85,label="Dead trees (SSL)")
]
ax2.legend(handles=legend_handles,loc="upper left",bbox_to_anchor=(0.12,0.82),frameon=False,fontsize=17)

ax1.text(0.02,0.97,"A",transform=ax1.transAxes,ha="left",va="top",fontsize=30,fontweight="bold")
ax2.text(0.02,0.97,"B",transform=ax2.transAxes,ha="left",va="top",fontsize=30,fontweight="bold")

fig.savefig(out_png,dpi=600,bbox_inches="tight")
plt.close(fig)
print('✅ Saved figure:', out_png)