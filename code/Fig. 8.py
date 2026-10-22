import os
import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.dates as mdates
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
nc_file = r"H:\Climatic data\SPEI\SPEI2025month\SPEI_0.5deg.nc"
metfile = r"D:/data/Processed data/meteorological data/M.csv"
out_png = r"D:/results/Fig. 8.png"
os.makedirs(os.path.dirname(out_png), exist_ok=True)
lat0 = 38.735911
lon0 = 105.912572
ds = xr.open_dataset(nc_file)
spei = ds.sel(latitude=lat0, longitude=lon0, method="nearest")["SPEI1"]
time_raw = spei["time"].values.astype(str)
time = pd.to_datetime(time_raw, format="%Y%m", errors="coerce")
df_spei = pd.DataFrame({"time": time, "SPEI1": spei.values})
df_spei["year"] = df_spei["time"].dt.year
df_spei["month"] = df_spei["time"].dt.month
df_spei = df_spei[df_spei["month"].isin([6, 7, 8])]
df_spei = df_spei.groupby("year", as_index=False)["SPEI1"].mean()
df_spei_plot = df_spei.dropna(subset=["year", "SPEI1"]).copy()
df_spei_plot = df_spei_plot[(df_spei_plot["year"] >= 1980) & (df_spei_plot["year"] <= 2025)].sort_values("year").reset_index(drop=True)
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
ax1.plot(df_spei_plot["year"], df_spei_plot["SPEI1"], linewidth=2.4, color="C2", label="SPEI1 (Jun–Aug)")
ax1.axhline(0, linestyle="--", linewidth=1.4, color="gray")
ax1.set_xlim(1980, 2025)
ymin, ymax = ax1.get_ylim()
yrange = ymax - ymin
ax1.set_ylim(ymin - 0.12 * yrange, ymax)
ax1.set_xlabel("Year", fontsize=24, labelpad=8)
ax1.set_ylabel("SPEI1", fontsize=24, labelpad=8)
ax1.legend(frameon=False, fontsize=20, loc="lower left", bbox_to_anchor=(0.02, 0.02))
for year in [2019, 2024]:
    ax1.axvline(year, color="blue", linestyle="--", linewidth=1.8, zorder=3)
    ax1.text(year, 0.04, str(year), color="blue", fontsize=20, ha="center", va="bottom", transform=ax1.get_xaxis_transform())
for year, dx, ha in [(2021, -0.35, "right"), (2023, 0.35, "left")]:
    row = df_spei_plot[df_spei_plot["year"] == year]
    if not row.empty:
        x = row["year"].iloc[0]
        y = row["SPEI1"].iloc[0]
        ax1.scatter(x, y, color="red", s=45, zorder=5)
        ax1.text(x + dx, y + 0.08, f"{y:.2f}", color="red", fontsize=18,
                 ha=ha, va="bottom")
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
ax2.xaxis.set_major_locator(mdates.YearLocator(1, month=1, day=1))
ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
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