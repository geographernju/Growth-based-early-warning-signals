import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy.stats import pearsonr
mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["savefig.dpi"] = 600
mpl.rcParams["font.size"] = 20
mpl.rcParams["axes.labelsize"] = 24
mpl.rcParams["xtick.labelsize"] = 20
mpl.rcParams["ytick.labelsize"] = 20
mpl.rcParams["legend.fontsize"] = 20
mpl.rcParams["axes.linewidth"] = 1.3
mpl.rcParams["mathtext.fontset"] = "custom"
mpl.rcParams["mathtext.rm"] = "Times New Roman"
mpl.rcParams["mathtext.it"] = "Times New Roman:italic"
csv_tree = r"D:/data/Processed data/Detrending/HDY.csv"
csv_blw = r"D:/data/Processed data/Detrending/HDY_BLW.csv"
nc_file = r"H:\Climatic data\SPEI\SPEI2025month\SPEI_0.5deg.nc"
metfile = r"D:/data/Processed data/meteorological data/M.csv"
out_png = r"D:/results/Fig. 8.png"
os.makedirs(os.path.dirname(out_png), exist_ok=True)
lat0 = 38.735911
lon0 = 105.912572
method = "Spline"
def zscore(s):
    s = pd.Series(s, dtype=float)
    std = s.std(ddof=0)
    if pd.isna(std) or std == 0:
        return pd.Series(np.zeros(len(s)), index=s.index)
    return (s - s.mean()) / std
df_tree = pd.read_csv(csv_tree)
df_blw = pd.read_csv(csv_blw)
df_tree["year"] = pd.to_numeric(df_tree["year"], errors="coerce")
df_blw["year"] = pd.to_numeric(df_blw["year"], errors="coerce")
df_tree[method] = pd.to_numeric(df_tree[method], errors="coerce")
df_blw[method] = pd.to_numeric(df_blw[method], errors="coerce")
df_tree = df_tree[["year", method]].rename(columns={method: "Tree_ring_width"})
df_blw = df_blw[["year", method]].rename(columns={method: "Latewood_blue_intensity"})
df_tree_plot = df_tree.dropna(subset=["year", "Tree_ring_width"]).copy()
df_blw_plot = df_blw.dropna(subset=["year", "Latewood_blue_intensity"]).copy()
df_tree_plot = df_tree_plot[df_tree_plot["year"] >= 1980].sort_values("year").reset_index(drop=True)
df_blw_plot = df_blw_plot[df_blw_plot["year"] >= 1980].sort_values("year").reset_index(drop=True)
df_tree_plot["Tree_ring_width_z"] = zscore(df_tree_plot["Tree_ring_width"])
df_blw_plot["Latewood_blue_intensity_z"] = zscore(df_blw_plot["Latewood_blue_intensity"])
ds = xr.open_dataset(nc_file)
spei = ds.sel(latitude=lat0, longitude=lon0, method="nearest")["SPEI1"]
time_raw = spei["time"].values.astype(str)
time = pd.to_datetime(time_raw, format="%Y%m", errors="coerce")
df_spei = pd.DataFrame({"time": time, "SPEI1": spei.values})
df_spei["year"] = df_spei["time"].dt.year
df_spei["month"] = df_spei["time"].dt.month
df_spei = df_spei[df_spei["month"].isin([5, 6])]
df_spei = df_spei.groupby("year", as_index=False)["SPEI1"].mean()
df_spei_plot = df_spei.dropna(subset=["year", "SPEI1"]).copy()
df_spei_plot = df_spei_plot[(df_spei_plot["year"] >= 1980) & (df_spei_plot["year"] <= 2025)].sort_values("year").reset_index(drop=True)
df_spei_plot["Summer_SPEI1_z"] = zscore(df_spei_plot["SPEI1"])
df_corr = df_tree.merge(df_blw, on="year", how="inner")
df_corr = df_corr.merge(df_spei[["year", "SPEI1"]].rename(columns={"SPEI1": "Summer_SPEI1"}), on="year", how="inner")
df_corr = df_corr.dropna(subset=["year", "Tree_ring_width", "Latewood_blue_intensity", "Summer_SPEI1"]).sort_values("year").reset_index(drop=True)
df_corr = df_corr[df_corr["year"] >= 1980].copy()
r_tree, p_tree = pearsonr(df_corr["Summer_SPEI1"], df_corr["Tree_ring_width"])
r_blw, p_blw = pearsonr(df_corr["Summer_SPEI1"], df_corr["Latewood_blue_intensity"])
df_wc = pd.read_csv(metfile)
df_wc["Date"] = pd.to_datetime(df_wc["Date"], format="%Y/%m/%d", errors="coerce")
df_wc["Water Content"] = pd.to_numeric(df_wc["Water Content"], errors="coerce")
df_wc = df_wc.dropna(subset=["Date", "Water Content"]).sort_values("Date")
df_wc = df_wc[df_wc["Date"] >= "2018-01-01"]
threshold = 0.065
periods = []
years = [2022, 2023, 2024]
for y in years:
    start = pd.Timestamp(f"{y-1}-07-01")
    end = pd.Timestamp(f"{y}-06-30")
    d = df_wc[(df_wc["Date"] >= start) & (df_wc["Date"] <= end)]
    days = (d["Water Content"] < threshold).sum()
    periods.append([f"{y-1}.07–{y}.06", days])
points = []
df_2022 = df_wc[df_wc["Date"].dt.year == 2022]
h1_2022 = df_2022[df_2022["Date"].dt.month <= 6]
if not h1_2022.empty:
    idx = h1_2022["Water Content"].idxmin()
    points.append(df_wc.loc[idx])
df_2023 = df_wc[df_wc["Date"].dt.year == 2023]
h1_2023 = df_2023[df_2023["Date"].dt.month <= 6]
h2_2023 = df_2023[df_2023["Date"].dt.month > 6]
if not h1_2023.empty:
    idx = h1_2023["Water Content"].idxmin()
    points.append(df_wc.loc[idx])
if not h2_2023.empty:
    idx = h2_2023["Water Content"].idxmin()
    points.append(df_wc.loc[idx])
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 10.5))
ax1.plot(df_tree_plot["year"], df_tree_plot["Tree_ring_width_z"], linewidth=2.4, color="C0", label="TRW")
ax1.plot(df_blw_plot["year"], df_blw_plot["Latewood_blue_intensity_z"], linewidth=2.4, color="C1", label="LWBI")
ax1.plot(df_spei_plot["year"], df_spei_plot["Summer_SPEI1_z"], linewidth=2.4, color="C2", label="SPEI1 (May–Jun)")
ax1.axhline(0, linestyle="--", linewidth=1.4, color="gray")
ax1.set_xlim(1980, 2025)
ymin, ymax = ax1.get_ylim()
yrange = ymax - ymin
ax1.set_ylim(ymin - 0.12 * yrange, ymax)
ax1.set_xlabel("Year", fontsize=24, labelpad=8)
ax1.set_ylabel("Standardized value", fontsize=24, labelpad=8)
ax1.legend(frameon=False, fontsize=20, loc="lower left", bbox_to_anchor=(0.02, 0.02))
p_tree_text = "< 0.001" if p_tree < 0.001 else f"= {p_tree:.3f}"
p_blw_text = "< 0.001" if p_blw < 0.001 else f"= {p_blw:.3f}"
ax1.text(0.52, 0.95, fr"SPEI1 vs TRW: $\it{{r}}$ = {r_tree:.2f}, $\it{{p}}$ {p_tree_text}", transform=ax1.transAxes, ha="center", va="top", fontsize=20)
ax1.text(0.52, 0.87, fr"SPEI1 vs LWBI: $\it{{r}}$ = {r_blw:.2f}, $\it{{p}}$ {p_blw_text}", transform=ax1.transAxes, ha="center", va="top", fontsize=20)
ax1.tick_params(axis="both", which="major", width=1.3, length=7, labelsize=20)
ax1.text(0.02, 0.95, "A", transform=ax1.transAxes, ha="left", va="top", fontsize=28, fontweight="bold")
ax2.plot(df_wc["Date"], df_wc["Water Content"], lw=2.2, color="blue")
xmin = df_wc["Date"].min()
xmax = df_wc["Date"].max()
ax2.set_xlim(xmin - pd.DateOffset(months=3), xmax + pd.DateOffset(months=3))
ax2.axhline(threshold, linestyle="--", linewidth=1.5, color="black")
ax2.set_xlabel("Date", fontsize=24, labelpad=8)
ax2.set_ylabel("Water content (m³ m⁻³)", fontsize=24, labelpad=8)
ax2.tick_params(axis="both", which="major", labelsize=20, width=1.3, length=7)
ax2.tick_params(axis="x", rotation=45)
ax2.text(xmin - pd.Timedelta(days=40), threshold, "0.065", va="top", ha="left", fontsize=20)
for r in points:
    ax2.scatter(r["Date"], r["Water Content"], color="black", s=70)
    ax2.text(r["Date"] + pd.Timedelta(days=25), r["Water Content"], f'{r["Water Content"]:.3f}', ha="left", va="center", fontsize=20)
table = ax2.table(cellText=periods, colLabels=["Period", "Days (WC < 0.065)"], bbox=[0.39, 0.66, 0.43, 0.30], cellLoc="center")
table.auto_set_font_size(False)
table.set_fontsize(16)
for _, cell in table.get_celld().items():
    cell.set_linewidth(1.0)
ax2.text(0.02, 0.95, "B", transform=ax2.transAxes, ha="left", va="top", fontsize=28, fontweight="bold")
plt.tight_layout()
plt.savefig(out_png, dpi=600, bbox_inches="tight")
plt.close()
print('✅ Saved figure:', out_png)