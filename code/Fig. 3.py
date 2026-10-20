import os
import re
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib as mpl
from scipy.stats import pearsonr

mpl.rcParams["font.family"] = "Times New Roman"
mpl.rcParams["savefig.dpi"] = 300

clim_csv = r"D:/data/Processed data/climate/1.5climate.csv"
tree_live_rw = r"D:/data/Processed data/Detrending/HDY1.csv"
tree_dead_rw = r"D:/data/Processed data/Detrending/HDY2.csv"
tree_live_blw = r"D:/data/Processed data/Detrending/HDY_BLW1.csv"
tree_dead_blw = r"D:/data/Processed data/Detrending/HDY_BLW2.csv"
out_dir = r"D:/results"
os.makedirs(out_dir, exist_ok=True)

method = "Spline"
vars_keep = ["SPEI1", "SPEI6", "SPEI12", "swvl1", "swvl3", "stl1", "stl3"]
months_all = list(range(1, 13))
months_mean = [5, 6, 7]

dfc = pd.read_csv(clim_csv)
pattern = re.compile(r"^(.*)_month_(\d+)$")
clim_cols = [c for c in dfc.columns if c != "year"]
var_month_map = {}
for c in clim_cols:
    m = pattern.match(c)
    if m:
        var_name = m.group(1)
        month_num = int(m.group(2))
        if var_name in vars_keep and 1 <= month_num <= 12:
            if var_name not in var_month_map:
                var_month_map[var_name] = {}
            var_month_map[var_name][month_num] = c

def compute_matrix(tree_csv, method, label):
    dft = pd.read_csv(tree_csv)
    df = pd.merge(dfc, dft, on="year", how="inner")
    df = df[df["year"] >= 1970].copy()
    df = df.sort_values("year").reset_index(drop=True)
    y = df[method].diff()
    mat = np.full((len(vars_keep), 12), np.nan)
    sig = np.zeros((len(vars_keep), 12), dtype=bool)
    labels = []
    for i, var in enumerate(vars_keep):
        for j, month in enumerate(months_all):
            if var in var_month_map and month in var_month_map[var]:
                x = df[var_month_map[var][month]].diff()
                mask = np.isfinite(x) & np.isfinite(y)
                if mask.sum() > 5:
                    r, p = pearsonr(x[mask], y[mask])
                    mat[i, j] = r
                    if p < 0.01:
                        sig[i, j] = True
        vals = np.array([mat[i, month - 1] for month in months_mean], dtype=float)
        mean_val = np.nanmean(vals) if np.any(np.isfinite(vals)) else np.nan
        if np.isfinite(mean_val):
            labels.append(f"{var} ({mean_val:.2f})")

        else:
            labels.append(f"{var} (nan)")

    return mat, sig, labels

def draw_panel(ax, mat, sig, labels, show_xlabel=False, show_ylabel=False, title_text=""):
    im = ax.imshow(mat, aspect="auto", origin="upper", vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(np.arange(12))
    ax.set_xticklabels([str(i) for i in range(1, 13)], fontsize=16)
    ax.set_yticks(np.arange(len(labels)))
    ax.set_yticklabels(labels, fontsize=16)
    if show_xlabel:
        ax.set_xlabel("Month", fontsize=22)
    if show_ylabel:
        ax.set_ylabel("Climate variable", fontsize=22)
    ax.set_title(title_text, fontsize=20, pad=12)
    for i in range(mat.shape[0]):
        for j in range(mat.shape[1]):
            if np.isfinite(mat[i, j]) and sig[i, j]:
                ax.text(j, i, "*", ha="center", va="center", fontsize=18, fontweight="bold")
    return im

mat1, sig1, lab1 = compute_matrix(tree_live_rw, method, "live_rw")
mat2, sig2, lab2 = compute_matrix(tree_dead_rw, method, "dead_rw")
mat3, sig3, lab3 = compute_matrix(tree_live_blw, method, "live_blw")
mat4, sig4, lab4 = compute_matrix(tree_dead_blw, method, "dead_blw")

fig = plt.figure(figsize=(16, 9))
gs = fig.add_gridspec(2, 2)

ax1 = fig.add_subplot(gs[0, 0])
ax2 = fig.add_subplot(gs[0, 1])
ax3 = fig.add_subplot(gs[1, 0])
ax4 = fig.add_subplot(gs[1, 1])

im = draw_panel(ax1, mat1, sig1, lab1, show_xlabel=False, show_ylabel=True, title_text="TRW (Live trees)")
draw_panel(ax2, mat2, sig2, lab2, show_xlabel=False, show_ylabel=False, title_text="TRW (Dead trees)")
draw_panel(ax3, mat3, sig3, lab3, show_xlabel=True, show_ylabel=True, title_text="LWBI (Live trees)")
draw_panel(ax4, mat4, sig4, lab4, show_xlabel=True, show_ylabel=False, title_text="LWBI (Dead trees)")

ax1.text(-0.1, 1.05, "A", transform=ax1.transAxes, fontsize=28, fontweight="bold")
ax2.text(-0.1, 1.05, "B", transform=ax2.transAxes, fontsize=28, fontweight="bold")
ax3.text(-0.1, 1.05, "C", transform=ax3.transAxes, fontsize=28, fontweight="bold")
ax4.text(-0.1, 1.05, "D", transform=ax4.transAxes, fontsize=28, fontweight="bold")

plt.tight_layout(rect=[0, 0, 0.92, 1])

cax = fig.add_axes([0.93, 0.15, 0.015, 0.7])
cbar = fig.colorbar(im, cax=cax, extend="both")
cbar.set_label(r"First-difference correlation ($r$)", fontsize=18)
cbar.ax.tick_params(labelsize=16)

out_png = os.path.join(out_dir, "Fig. 3.png")
fig.savefig(out_png, bbox_inches="tight")
plt.close()

print("✅ Saved figure:", out_png)