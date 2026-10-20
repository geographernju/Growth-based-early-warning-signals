import os
os.makedirs("D:/results", exist_ok=True)
import os,pandas as pd,matplotlib.pyplot as plt,matplotlib.dates as mdates,matplotlib as mpl
from matplotlib.lines import Line2D
mpl.rcParams["font.family"]="Times New Roman"
mpl.rcParams["savefig.dpi"]=300
mpl.rcParams["font.size"]=18
mpl.rcParams["axes.labelsize"]=24
mpl.rcParams["xtick.labelsize"]=20
mpl.rcParams["ytick.labelsize"]=18
mpl.rcParams["legend.fontsize"]=22
mpl.rcParams["axes.linewidth"]=1.2
infile=r"D:/data/dendrometer.csv"
outfile=r"D:/results/Fig. 9.png"
os.makedirs(os.path.dirname(outfile),exist_ok=True)
df=pd.read_csv(infile)
df["Date"]=pd.to_datetime(df["Date"],errors="coerce")
df=df.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
df["Date_day"]=df["Date"].dt.normalize()
tree_cols=[c for c in df.columns if c not in ["Date","Date_day"]]
max_gap=pd.Timedelta(days=3)
ssl_period_start=pd.Timestamp("2019-01-01")
ssl_period_end=pd.Timestamp("2023-12-31")
live_color="#4C78A8"
pre_mortality_color="#E45756"
segments=[]
for col in tree_cols:
    s=pd.to_numeric(df[col],errors="coerce")
    sub=df.loc[s.notna(),["Date_day"]].drop_duplicates().sort_values("Date_day").reset_index(drop=True)
    if sub.empty:
        continue
    sub["gap"]=sub["Date_day"].diff()
    sub["new_seg"]=sub["gap"].isna()|(sub["gap"]>max_gap)
    sub["seg_id"]=sub["new_seg"].cumsum()
    segs=sub.groupby("seg_id")["Date_day"].agg(["min","max"]).reset_index(drop=True)
    is_ssl="SSL" in str(col).upper()
    for _,r in segs.iterrows():
        st=r["min"]
        ed=r["max"]
        if not is_ssl:
            segments.append([col,st,ed,"Live"])
        else:
            if st<ssl_period_start:
                a=st
                b=min(ed,ssl_period_start-pd.Timedelta(days=1))
                if a<=b:
                    segments.append([col,a,b,"Live"])
            if st<=ssl_period_end and ed>=ssl_period_start:
                a=max(st,ssl_period_start)
                b=min(ed,ssl_period_end)
                if a<=b:
                    segments.append([col,a,b,"PreMortality"])
            if ed>ssl_period_end:
                a=max(st,ssl_period_end+pd.Timedelta(days=1))
                b=ed
                if a<=b:
                    segments.append([col,a,b,"Live"])
seg_df=pd.DataFrame(segments,columns=["Tree","Start","End","Type"])
tree_order=seg_df.groupby("Tree")["Start"].min().sort_values().index.tolist() if not seg_df.empty else []
fig_h=max(7,len(tree_order)*0.55)
fig,ax=plt.subplots(figsize=(18,fig_h))
for i,tree in enumerate(tree_order):
    tmp=seg_df[seg_df["Tree"]==tree]
    for _,r in tmp.iterrows():
        st=mdates.date2num(r["Start"])
        ed=mdates.date2num(r["End"]+pd.Timedelta(days=1))
        color=live_color if r["Type"]=="Live" else pre_mortality_color
        ax.broken_barh([(st,ed-st)],(i-0.38,0.76),facecolors=color)
ax.set_ylim(-0.8,len(tree_order)-0.2)
ax.set_yticks(range(len(tree_order)))
ax.set_yticklabels(tree_order,fontsize=18)
ax.set_xlabel("Date",fontsize=24,labelpad=10)
xmin=pd.Timestamp(df["Date_day"].min().year,1,1)
xmax=pd.Timestamp(df["Date_day"].max().year+1,1,1)
year_ticks=pd.date_range(xmin,xmax,freq="YS")
ax.set_xlim(xmin,xmax)
ax.set_xticks(year_ticks)
ax.set_xticklabels([str(x.year) for x in year_ticks],fontsize=20)
ax.minorticks_off()
plt.setp(ax.get_xticklabels(),rotation=0,ha="center")
ax.tick_params(axis="both",which="major",width=1.2,length=7)
ax.grid(axis="x",which="major",linestyle="--",alpha=0.5)
handles=[Line2D([0],[0],color=live_color,lw=8,label="Live trees"),Line2D([0],[0],color=pre_mortality_color,lw=8,label="Dead trees")]
ax.legend(handles=handles,loc="upper left",frameon=True,fontsize=22,handlelength=3,handleheight=1.5,borderpad=0.8,labelspacing=0.8)
fig.tight_layout()
fig.savefig(outfile,bbox_inches="tight")
plt.close(fig)
print(outfile)