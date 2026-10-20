import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
from matplotlib.patches import Patch
mpl.rcParams["font.family"]="Times New Roman"
mpl.rcParams["mathtext.fontset"]="custom"
mpl.rcParams["mathtext.rm"]="Times New Roman"
mpl.rcParams["mathtext.it"]="Times New Roman:italic"
mpl.rcParams["savefig.dpi"]=600
mpl.rcParams["font.size"]=26
mpl.rcParams["axes.labelsize"]=30
mpl.rcParams["xtick.labelsize"]=24
mpl.rcParams["ytick.labelsize"]=24
mpl.rcParams["legend.fontsize"]=21
mpl.rcParams["axes.linewidth"]=1.8
baseline_years=[2019,2020]
start_2021=pd.Timestamp("2021-04-30")
start_2023=pd.Timestamp("2023-05-24")
growth_dir=r"D:/data/Processed data/Growth/standardized"
twd_dir=r"D:/data/Processed data/TWD/standardized"
out_png=r"D:/results/Fig. 6.png"
os.makedirs(os.path.dirname(out_png),exist_ok=True)
colors={"growth":"#7B3294","twd":"#8C510A"}
ref_values=[(45,55),(170,190),(25,35),(190,220)]
legend_settings=[("lower center",(0.52,0.04)),("upper left",(0.09,0.88)),("upper center",(0.52,0.87)),("lower right",(0.98,0.04))]
def read_biweight(path):
    df=pd.read_csv(path)
    df["Date"]=pd.to_datetime(df["Date"],errors="coerce")
    df["Biweight_chronology"]=pd.to_numeric(df["Biweight_chronology"],errors="coerce")
    df=df.dropna(subset=["Date","Biweight_chronology"]).sort_values("Date").copy()
    df["year"]=df["Date"].dt.year
    return df
def standardize_with_ref(series,ref):
    s=pd.to_numeric(series,errors="coerce")
    r=pd.to_numeric(ref,errors="coerce")
    m=r.mean()
    sd=r.std(ddof=0)
    if pd.isna(sd) or sd==0:
        return pd.Series(s-m,index=s.index)
    return (s-m)/sd
def normalize_twd(dfs):
    sph,spl,ssl=dfs
    live_ref=pd.concat([sph.loc[sph["year"].isin(baseline_years),"Biweight_chronology"],spl.loc[spl["year"].isin(baseline_years),"Biweight_chronology"]],ignore_index=True)
    dead_ref=ssl.loc[ssl["year"].isin(baseline_years),"Biweight_chronology"]
    if live_ref.empty or dead_ref.empty:
        raise ValueError("No TWD observations for the 2019-2020 reference period")
    for df in (sph,spl):
        df["relative_raw"]=standardize_with_ref(df["Biweight_chronology"],live_ref)
    ssl["relative_raw"]=standardize_with_ref(ssl["Biweight_chronology"],dead_ref)
    pooled=pd.concat([sph["relative_raw"],spl["relative_raw"],ssl["relative_raw"]],ignore_index=True)
    vmin=pooled.min()
    vmax=pooled.max()
    if not np.isfinite(vmin) or not np.isfinite(vmax) or vmax==vmin:
        raise ValueError("Cannot perform min-max normalization of TWD")
    for df in (sph,spl,ssl):
        df["relative"]=(df["relative_raw"]-vmin)/(vmax-vmin)
    return dfs
def cumulative_ratio(dfs,col,start,end):
    frames=[]
    for df,name in zip(dfs,["sph","spl","dead"]):
        d=df.loc[df["Date"].between(start,end),["Date",col]].dropna().sort_values("Date").copy()
        if d.empty:
            raise ValueError(f"No {name} records between {start.date()} and {end.date()}")
        d=d.groupby("Date",as_index=False)[col].mean()
        d[name]=d[col].cumsum()
        frames.append(d.set_index("Date")[[name]])
    out=pd.concat(frames,axis=1).sort_index().ffill()
    out["ratio_sph"]=np.where(out["sph"]!=0,out["dead"]/out["sph"]*100,np.nan)
    out["ratio_spl"]=np.where(out["spl"]!=0,out["dead"]/out["spl"]*100,np.nan)
    out["low"]=out[["ratio_sph","ratio_spl"]].min(axis=1)
    out["high"]=out[["ratio_sph","ratio_spl"]].max(axis=1)
    out["mid"]=out[["ratio_sph","ratio_spl"]].mean(axis=1)
    out=out.replace([np.inf,-np.inf],np.nan).dropna(subset=["mid"])
    if out.empty:
        raise ValueError(f"No finite dead/live ratios between {start.date()} and {end.date()}")
    return out.reset_index()
def final_date(dfs,year,start):
    ends=[df.loc[(df["year"]==year)&(df["Date"]>=start),"Date"].max() for df in dfs]
    ends=[e for e in ends if pd.notna(e)]
    if not ends:
        raise ValueError(f"No valid observations in {year}")
    return min(max(ends),pd.Timestamp(f"{year}-12-31"))
growth=[read_biweight(os.path.join(growth_dir,f"{name}.csv")) for name in ["SPH","SPL","SSL"]]
twd=normalize_twd([read_biweight(os.path.join(twd_dir,f"daily_twd_{name}.csv")) for name in ["SPH","SPL","SSL"]])
end_2021=final_date(growth+twd,2021,start_2021)
end_2023=final_date(growth+twd,2023,start_2023)
series=[cumulative_ratio(growth,"Biweight_chronology",start_2021,end_2021),cumulative_ratio(twd,"relative",start_2021,end_2021),cumulative_ratio(growth,"Biweight_chronology",start_2023,end_2023),cumulative_ratio(twd,"relative",start_2023,end_2023)]
fig,axs=plt.subplots(4,1,figsize=(18,23),sharex=False)
labels=["A","B","C","D"]
years=[2021,2021,2023,2023]
for i,(ax,d) in enumerate(zip(axs,series)):
    color=colors["growth"] if i%2==0 else colors["twd"]
    ax.fill_between(d["Date"].to_numpy(),d["low"].to_numpy(),d["high"].to_numpy(),color=color,alpha=0.22,linewidth=0,zorder=2)
    line,=ax.plot(d["Date"],d["mid"],linewidth=3.5,color=color,label="Mean dead/live ratio",zorder=4)
    for v in ref_values[i]:
        ax.axhline(v,color="#999999",linestyle="--",linewidth=1.8,alpha=0.75,zorder=1)
    ax.set_ylabel("Cumulative growth\nratio (%)" if i%2==0 else "Cumulative normalized\nTWD ratio (%)",fontsize=30)
    handles=[line,Patch(facecolor=color,edgecolor="none",alpha=0.22,label="Dead/live ratio range")]
    loc,bbox=legend_settings[i]
    ax.legend(handles=handles,loc=loc,bbox_to_anchor=bbox,ncol=2,frameon=False,fontsize=21,handlelength=2.5,columnspacing=1.7,handletextpad=0.7)
    ax.text(0.01,0.96,labels[i],transform=ax.transAxes,fontsize=32,fontweight="bold",va="top",ha="left")
    ax.text(0.98,0.96,str(years[i]),transform=ax.transAxes,fontsize=27,fontweight="bold",va="top",ha="right")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both",which="major",direction="out",length=8,width=1.8,labelsize=24)
    ax.yaxis.set_label_coords(-0.05,0.5)
    start,end=(start_2021,end_2021) if i<2 else (start_2023,end_2023)
    ax.set_xlim(start,end)
    xpos=end-pd.Timedelta(days=15 if i==3 else 6)
    for v in ref_values[i]:
        ax.text(xpos,v,str(v),ha="left",va="bottom",fontsize=23,color="#777777")
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonthday=1,interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    plt.setp(ax.get_xticklabels(),rotation=0,ha="center",fontsize=24)
plt.subplots_adjust(left=0.15,right=0.97,bottom=0.06,top=0.98,hspace=0.20)
plt.savefig(out_png,dpi=600,bbox_inches="tight")
plt.close()
print('✅ Saved figure:',out_png)