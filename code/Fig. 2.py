
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.patheffects as pe
from matplotlib.lines import Line2D
from scipy.stats import pearsonr
from matplotlib.gridspec import GridSpec
mpl.rcParams["font.family"]="Times New Roman"
mpl.rcParams["savefig.dpi"]=600
mpl.rcParams["font.size"]=24
mpl.rcParams["axes.labelsize"]=26
mpl.rcParams["xtick.labelsize"]=23
mpl.rcParams["ytick.labelsize"]=23
mpl.rcParams["legend.fontsize"]=21
trw_file=r"D:/data/HDY.rwl"
extra_dead_trw_file=r"D:/data/dead-add.rwl"
outfile=r"D:/results/Fig. 2.png"
rw_live_file=r"D:/data/Processed data/Detrending/HDY1.csv"
rw_dead_file=r"D:/data/Processed data/Detrending/HDY2.csv"
bi_live_file=r"D:/data/Processed data/Detrending/HDY_BLW1.csv"
bi_dead_file=r"D:/data/Processed data/Detrending/HDY_BLW2.csv"
os.makedirs(os.path.dirname(outfile),exist_ok=True)
method="Spline"
window=21
min_periods=21
plot_start_year=1937
break_year=1968
std_xticks=[1950,1970,1990,2010]
live_raw_color="#999999"
dead_raw_color="#DE9759"
live_color="#505050"
dead_color="#C36A19"
break_color="blue"
def read_rwl(path):
    data={}
    with open(path,"r",encoding="utf-8") as f:
        for line in f:
            line=line.rstrip()
            if not line:
                continue
            parts=line.split()
            if len(parts)<3:
                continue
            series=parts[0]
            try:
                start_year=int(parts[1])
            except:
                continue
            values=parts[2:]
            for i,v in enumerate(values):
                try:
                    val=int(v)
                except:
                    continue
                if val in [999,9990,-9999]:
                    continue
                year=start_year+i
                if series not in data:
                    data[series]={}
                data[series][year]=val
    all_years=sorted({y for s in data.values() for y in s.keys()})
    df=pd.DataFrame(index=all_years)
    for series,year_vals in data.items():
        df[series]=pd.Series(year_vals)
    df.index.name="year"
    return df.sort_index()
def rename_with_prefix(df,prefix):
    df=df.copy()
    df.columns=[f"{prefix}_{c}" for c in df.columns]
    return df
def prepare_annual_pair(df):
    live_name=f"{method}_live"
    dead_name=f"{method}_dead"
    annual=df[["year",live_name,dead_name]].dropna(subset=["year"]).copy()
    annual["year"]=annual["year"].astype(int)
    annual=annual[annual["year"]>=plot_start_year]
    if annual.empty:
        raise ValueError("No available data in the selected analysis period")
    annual=annual.groupby("year")[[live_name,dead_name]].mean().sort_index()
    full_years=np.arange(plot_start_year,int(annual.index.max())+1)
    return annual.reindex(full_years)
def centered_annual_std(annual):
    live_name=f"{method}_live"
    dead_name=f"{method}_dead"
    live_std=annual[live_name].rolling(window=window,min_periods=min_periods,center=True).std()
    dead_std=annual[dead_name].rolling(window=window,min_periods=min_periods,center=True).std()
    common=live_std.notna()&dead_std.notna()
    return live_std.where(common),dead_std.where(common)
def mean_dead_live_ratio(dead_std,live_std):
    ratio=(dead_std/live_std).replace([np.inf,-np.inf],np.nan)
    return ratio.mean()
def corr_text(df):
    tmp=df[["live","dead"]].dropna()
    if len(tmp)>=3:
        r,p=pearsonr(tmp["live"],tmp["dead"])
        return rf"$\it{{r}}$ = {r:.2f}, $\it{{P}}$ < 0.001" if p<0.001 else rf"$\it{{r}}$ = {r:.2f}, $\it{{P}}$ = {p:.3f}"
    return r"$\it{r}$ = NA"
def set_year_limits(ax,years,series,require_both=False):
    years=np.asarray(years,dtype=float)
    values=np.column_stack([np.asarray(item,dtype=float) for item in series])
    finite=np.isfinite(values)
    valid=np.isfinite(years)&(finite.all(axis=1) if require_both else finite.any(axis=1))
    if valid.any():
        ax.set_xlim(float(years[valid].min())-1,float(years[valid].max())+1)
    else:
        ax.text(0.5,0.5,"No valid observations",transform=ax.transAxes,ha="center",va="center",fontsize=16)
def add_break_label(ax,year):
    ax.axvline(year,color=break_color,linestyle="--",linewidth=1.8,zorder=6)
    ax.text(year,0.04,str(year),color=break_color,ha="center",va="bottom",transform=ax.get_xaxis_transform(),fontsize=20,zorder=20)
df_trw=read_rwl(trw_file)
live_cols=[c for c in df_trw.columns if "HZLY" not in c]
dead_cols=[c for c in df_trw.columns if "HZLY" in c]
if extra_dead_trw_file is not None and os.path.exists(extra_dead_trw_file):
    extra_df=read_rwl(extra_dead_trw_file)
    extra_df=rename_with_prefix(extra_df,"dead_add")
    df_trw=df_trw.join(extra_df,how="outer")
    dead_cols+=list(extra_df.columns)
live_mean=df_trw[live_cols].mean(axis=1,skipna=True)
dead_mean=df_trw[dead_cols].mean(axis=1,skipna=True)
compare_df=pd.DataFrame({"live":live_mean,"dead":dead_mean}).dropna()
compare_df=compare_df.loc[compare_df.index>=plot_start_year]
before_mask=compare_df.index<break_year
after_mask=compare_df.index>break_year
live_before=compare_df.loc[before_mask,"live"].mean()
dead_before=compare_df.loc[before_mask,"dead"].mean()
live_after=compare_df.loc[after_mask,"live"].mean()
dead_after=compare_df.loc[after_mask,"dead"].mean()
print(f"Before {break_year}: Live={live_before:.2f} um, Dead={dead_before:.2f} um, Dead/Live={dead_before/live_before*100:.1f}%")
print(f"After {break_year}: Live={live_after:.2f} um, Dead={dead_after:.2f} um, Dead/Live={dead_after/live_after*100:.1f}%")
rw_live_df=pd.read_csv(rw_live_file)[["year",method]].copy()
rw_dead_df=pd.read_csv(rw_dead_file)[["year",method]].copy()
bi_live_df=pd.read_csv(bi_live_file)[["year",method]].copy()
bi_dead_df=pd.read_csv(bi_dead_file)[["year",method]].copy()
for df in [rw_live_df,rw_dead_df,bi_live_df,bi_dead_df]:
    df["year"]=pd.to_numeric(df["year"],errors="coerce")
    df[method]=pd.to_numeric(df[method],errors="coerce")
df_rw=pd.merge(rw_live_df[["year",method]],rw_dead_df[["year",method]],on="year",how="outer",suffixes=("_live","_dead")).sort_values("year").reset_index(drop=True)
df_bi=pd.merge(bi_live_df[["year",method]],bi_dead_df[["year",method]],on="year",how="outer",suffixes=("_live","_dead")).sort_values("year").reset_index(drop=True)
rw_annual=prepare_annual_pair(df_rw)
bi_annual=prepare_annual_pair(df_bi)
rw_live_std,rw_dead_std=centered_annual_std(rw_annual)
bi_live_std,bi_dead_std=centered_annual_std(bi_annual)
rw_plot=pd.DataFrame({"year":rw_annual.index.to_numpy(),"live":rw_annual[f"{method}_live"].to_numpy(),"dead":rw_annual[f"{method}_dead"].to_numpy(),"live_std":rw_live_std.to_numpy(),"dead_std":rw_dead_std.to_numpy()})
bi_plot=pd.DataFrame({"year":bi_annual.index.to_numpy(),"live":bi_annual[f"{method}_live"].to_numpy(),"dead":bi_annual[f"{method}_dead"].to_numpy(),"live_std":bi_live_std.to_numpy(),"dead_std":bi_dead_std.to_numpy()})
text_rw=corr_text(rw_plot)
text_bi=corr_text(bi_plot)
ratio_D=mean_dead_live_ratio(rw_plot["dead_std"],rw_plot["live_std"])
ratio_E=mean_dead_live_ratio(bi_plot["dead_std"],bi_plot["live_std"])
ratio_D_text="Dead/Live = NA" if pd.isna(ratio_D) else f"Dead/Live = {ratio_D:.1f}"
ratio_E_text="Dead/Live = NA" if pd.isna(ratio_E) else f"Dead/Live = {ratio_E:.1f}"
fig=plt.figure(figsize=(18,17.5))
gs=GridSpec(3,2,figure=fig,height_ratios=[1.32,1,1],hspace=0.22,wspace=0.17)
axA=fig.add_subplot(gs[0,:])
axB=fig.add_subplot(gs[1,0])
axC=fig.add_subplot(gs[1,1])
axD=fig.add_subplot(gs[2,0])
axE=fig.add_subplot(gs[2,1])
for col in live_cols:
    axA.plot(df_trw.index,df_trw[col],color=live_raw_color,linewidth=1.1,alpha=0.58,zorder=1)
for col in dead_cols:
    axA.plot(df_trw.index,df_trw[col],color=dead_raw_color,linewidth=1.1,alpha=0.58,zorder=2)
live_line=axA.plot(df_trw.index,live_mean,color=live_color,linewidth=4.7,zorder=20)[0]
dead_line=axA.plot(df_trw.index,dead_mean,color=dead_color,linewidth=4.7,zorder=21)[0]
for line in [live_line,dead_line]:
    line.set_path_effects([pe.Stroke(linewidth=7.2,foreground="white"),pe.Normal()])
axA.axvline(break_year,color=break_color,linestyle="--",linewidth=2.4,zorder=25)
ymin,ymax=axA.get_ylim()
yr=ymax-ymin
axA.text(break_year,ymin+yr*0.03,f"{break_year}",color=break_color,fontsize=22,ha="center",va="bottom",zorder=26)
table_data=[[f"Before {break_year}",f"{live_before:.0f}",f"{dead_before:.0f}"],[f"After {break_year}",f"{live_after:.0f}",f"{dead_after:.0f}"]]
table=axA.table(cellText=table_data,colLabels=["Period","Live (µm)","Dead (µm)"],cellLoc="center",loc="upper right",bbox=[0.61,0.69,0.38,0.28],colWidths=[0.42,0.29,0.29])
table.auto_set_font_size(False)
table.set_fontsize(21)
table.set_zorder(30)
for _,cell in table.get_celld().items():
    cell.set_linewidth(0.8)
    cell.set_facecolor((1,1,1,0.82))
    cell.set_zorder(30)
    cell.get_text().set_zorder(31)
axA.text(0.01,0.96,"A",transform=axA.transAxes,fontsize=36,fontweight="bold",va="top")
axA.set_ylabel("Raw TRW (µm)")
axA.tick_params(direction="in",labelsize=23)
legend_A=[Line2D([0],[0],color=live_raw_color,lw=2.4,alpha=0.95,label="Live trees"),Line2D([0],[0],color=dead_raw_color,lw=2.4,alpha=0.95,label="Dead trees"),Line2D([0],[0],color=live_color,lw=4.7,label="Mean of live trees"),Line2D([0],[0],color=dead_color,lw=4.7,label="Mean of dead trees")]
axA.legend(handles=legend_A,loc="upper left",bbox_to_anchor=(0.06,0.96),frameon=False,ncol=1,handlelength=2.2,handletextpad=0.7,borderpad=0.2,labelspacing=0.45,columnspacing=1.0,fontsize=19)
for spine in axA.spines.values():
    spine.set_linewidth(1.4)
axB.plot(rw_plot["year"],rw_plot["live"],color=live_color,linewidth=2.8)
axB.plot(rw_plot["year"],rw_plot["dead"],color=dead_color,linewidth=2.8)
add_break_label(axB,break_year)
axB.text(0.02,0.95,"B",transform=axB.transAxes,ha="left",va="top",fontsize=32,fontweight="bold")
axB.text(0.52,0.94,text_rw,transform=axB.transAxes,ha="center",va="top",fontsize=22)
axB.set_ylabel("TRW")
axB.tick_params(direction="in")
legend_B=[Line2D([0],[0],color=live_color,lw=2.8,label="Live trees"),Line2D([0],[0],color=dead_color,lw=2.8,label="Dead trees")]
axB.legend(handles=legend_B,loc="upper left",bbox_to_anchor=(0.02,0.86),frameon=False,ncol=1,handlelength=2.0,handletextpad=0.6,borderpad=0.2,labelspacing=0.35,fontsize=19)
axC.plot(bi_plot["year"],bi_plot["live"],color=live_color,linewidth=2.8)
axC.plot(bi_plot["year"],bi_plot["dead"],color=dead_color,linewidth=2.8)
add_break_label(axC,break_year)
axC.text(0.02,0.95,"C",transform=axC.transAxes,ha="left",va="top",fontsize=32,fontweight="bold")
axC.text(0.52,0.94,text_bi,transform=axC.transAxes,ha="center",va="top",fontsize=22)
axC.set_ylabel("LWBI")
axC.tick_params(direction="in")
axD.plot(rw_plot["year"],rw_plot["live_std"],color=live_color,linewidth=2.8)
axD.plot(rw_plot["year"],rw_plot["dead_std"],color=dead_color,linewidth=2.8)
add_break_label(axD,break_year)
axD.text(0.02,0.95,"D",transform=axD.transAxes,ha="left",va="top",fontsize=32,fontweight="bold")
axD.text(0.55,0.94,ratio_D_text,transform=axD.transAxes,ha="center",va="top",fontsize=22)
axD.set_ylabel("TRW variability (21-yr SD)")
axD.set_xlabel("Year")
axD.tick_params(direction="in")
axE.plot(bi_plot["year"],bi_plot["live_std"],color=live_color,linewidth=2.8)
axE.plot(bi_plot["year"],bi_plot["dead_std"],color=dead_color,linewidth=2.8)
add_break_label(axE,break_year)
axE.text(0.02,0.95,"E",transform=axE.transAxes,ha="left",va="top",fontsize=32,fontweight="bold")
axE.text(0.55,0.94,ratio_E_text,transform=axE.transAxes,ha="center",va="top",fontsize=22)
axE.set_ylabel("LWBI variability (21-yr SD)")
axE.set_xlabel("Year")
axE.tick_params(direction="in")
set_year_limits(axA,df_trw.index.to_numpy(),[live_mean.to_numpy(),dead_mean.to_numpy()])
set_year_limits(axB,rw_plot["year"],[rw_plot["live"],rw_plot["dead"]])
set_year_limits(axC,bi_plot["year"],[bi_plot["live"],bi_plot["dead"]])
set_year_limits(axD,rw_plot["year"],[rw_plot["live_std"],rw_plot["dead_std"]],require_both=True)
set_year_limits(axE,bi_plot["year"],[bi_plot["live_std"],bi_plot["dead_std"]],require_both=True)
axD.set_xticks(std_xticks)
axE.set_xticks(std_xticks)
rw_std_years=rw_plot.loc[rw_plot["live_std"].notna()&rw_plot["dead_std"].notna(),"year"]
bi_std_years=bi_plot.loc[bi_plot["live_std"].notna()&bi_plot["dead_std"].notna(),"year"]
fig.align_ylabels([axA,axB,axD])
fig.align_ylabels([axC,axE])
print("TRW centered 21-year STD valid years:",f"{int(rw_std_years.min())}-{int(rw_std_years.max())}" if len(rw_std_years) else "none")
print("LWBI centered 21-year STD valid years:",f"{int(bi_std_years.min())}-{int(bi_std_years.max())}" if len(bi_std_years) else "none")
for ax in [axB,axC,axD,axE]:
    for spine in ax.spines.values():
        spine.set_linewidth(1.3)
plt.savefig(outfile,bbox_inches="tight")
plt.close()
print("✅ Saved figure:",outfile)
