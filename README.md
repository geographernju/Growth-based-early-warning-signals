# Code and Figure Reproduction Guide

This repository contains the tree-ring width (TRW), latewood blue intensity (LWBI), dendrometer-derived growth, tree water deficit (TWD), and climate analyses for the study site at 38.735911°N, 105.912572°E.

## 1. Directory structure

```text
D:/
├── README.md
├── code/
│   ├── Fig. 0.py
│   ├── Fig. 1.psd
│   ├── Fig. 2.py ... Fig. 9.py
│   └── run_all.py
├── data/
│   ├── Dendrometer.csv
│   ├── HDY.rwl, HDY1.rwl, HDY2.rwl
│   ├── HDY_BLW.rwl, HDY_BLW1.rwl, HDY_BLW2.rwl
│   ├── dead-add.rwl
│   ├── Map/
│   ├── Picture/
│   └── Processed data/
│       ├── Climate/
│       ├── Dendrometer_dayily/
│       ├── Detrending/
│       ├── Growth/
│       │   └── standardized/
│       ├── Meteorological data/
│       └── TWD/
│           └── standardized/
└── results/
    └── Fig. 0.png ... Fig. 9.png
```

There are nine Python figure scripts (`Fig. 0.py` and `Fig. 2.py`–`Fig. 9.py`), a batch runner, and a PSD file for Fig. 1. The folder name `Dendrometer_dayily` is retained as used in the file paths.

## 2. Software and paths

The Python scripts use NumPy, pandas, SciPy, xarray, Matplotlib, GeoPandas, Shapely, and Cartopy. Reading NetCDF files also requires a suitable backend, such as netCDF4.

```powershell
python -m pip install numpy pandas scipy xarray matplotlib geopandas shapely cartopy netCDF4
```

R preprocessing uses `dplR`, `treenetproc`, and `dplyr`.

```r
install.packages(c("dplR", "treenetproc", "dplyr"))
```

The figures use Times New Roman. Package versions are not pinned.

Most scripts use absolute paths under `D:/code`, `D:/data`, `D:/results`, and `H:/`. Update these paths when running the project on another computer. File and folder capitalization also needs to match on case-sensitive systems.

## 3. Running the figures

Run the Python figure scripts together:

```powershell
python "D:/code/run_all.py"
```

`run_all.py` searches `D:/code` recursively for Python files, excluding itself and `__pycache__`, and executes them alphabetically. Each script runs from its own directory. The runner continues after a script fails and reports the results at the end. It does not execute data-preprocessing scripts or export the PSD file.

Run a single figure:

```powershell
python "D:/code/Fig. 4.py"
```

Figures are saved to `D:/results/`. Existing files with the same names are overwritten. Fig. 1 is supplied as `code/Fig. 1.psd` and `results/Fig. 1.png`; it has no corresponding Python plotting script and must be exported separately from the PSD if changes are made.

## 4. Figure files

| Figure | Source | Description | PNG resolution |
|---|---|---|---|
| Fig. 0 | `code/Fig. 0.py` | Land cover, study location, administrative and maritime boundaries, monsoon boundary, precipitation contours, and regional inset | 600 dpi |
| Fig. 1 | `code/Fig. 1.psd` | Figure artwork supplied as PSD and PNG | 300 dpi |
| Fig. 2 | `code/Fig. 2.py` | Raw TRW, Spline-standardized TRW/LWBI chronologies, and 21-year rolling standard deviations for living and dead trees | 600 dpi |
| Fig. 3 | `code/Fig. 3.py` | Monthly first-difference correlations between TRW/LWBI and climate variables from 1970 onward; May–July summary values | 300 dpi |
| Fig. 4 | `code/Fig. 4.py` | Normalized growing-season radial growth, 2019–2023 | 600 dpi |
| Fig. 5 | `code/Fig. 5.py` | Normalized growing-season TWD, 2019–2023 | 600 dpi |
| Fig. 6 | `code/Fig. 6.py` | Cumulative dead/live growth and normalized TWD ratios, 2021 and 2023 | 600 dpi |
| Fig. 7 | `code/Fig. 7.py` | Concentration of growth on top-ranked days and high-growth occurrence across precipitation classes, 2019–2023 | 600 dpi |
| Fig. 8 | `code/Fig. 8.py` | TRW, LWBI, May–June SPEI1, and soil water-content records | 600 dpi |
| Fig. 9 | `code/Fig. 9.py` | Dendrometer observation periods for individual trees | 300 dpi |

The table lists the resolution recorded for the supplied figure files. Figure dimensions vary.

The analysis treats SPH and SPL as living-tree groups and SSL as the group of trees that subsequently died. Species identities are not encoded in these group names.

## 5. Data files

### 5.1 Tree-ring and dendrometer records

- `data/Dendrometer.csv`: 162,057 measurement records, from 15 May 2016 17:00 to 27 October 2025 14:30. Columns include `Date` and individual trees such as `SPL1`, `SPH1`, and `SSL1`; gaps occur in individual series.
- Seven `.rwl` files contain TRW, LWBI, and additional dead-tree TRW records. Fig. 2 reads `HDY.rwl` and `dead-add.rwl` for the raw TRW panel.
- `Processed data/Detrending/`: six chronology tables with columns including `year`, `ModNegExp`, `samp.depth`, `Spline`, `AgeDepSpline`, `RCS`, `SFRCS`, and `EPS`. `HDY`/`HDY1` and `HDY_BLW`/`HDY_BLW1` cover 1919–2024; `HDY2` covers 1913–2022; `HDY_BLW2` covers 1937–2022.
- `Processed data/Dendrometer_dayily/dendrometer_diff.csv`: 3,453 daily records from 15 May 2016 to 27 October 2025, containing nonnegative day-to-day changes.

### 5.2 Growth and TWD

`Processed data/Growth/` contains daily growth tables for SPH, SPL, and SSL (660 rows per group). `Processed data/TWD/` contains the corresponding daily TWD tables (701 rows per group). Both cover selected growing-season periods during 2019–2023.

The `standardized/` folders contain group chronologies with `Date` and `Biweight_chronology` columns. Each group chronology has 629 records from selected growing-season periods between 14 June 2019 and 27 August 2023. The records are not a continuous daily series.

The processing scripts standardize individual tree series, calculate group biweight chronologies (tuning factor 9), and shift the resulting series by their minimum. Some figures apply further reference-period standardization or Min–Max normalization. These indices are relative measures, not original physical measurements.

### 5.3 Climate and meteorology

- `Processed data/Climate/1.5climate.csv`: annual table for 1950–2025 (76 rows). Monthly columns follow the pattern `<variable>_month_<month>`; some merged columns have suffixes such as `_x`.
- `Processed data/Meteorological data/M.csv`: 3,286 records from 17 May 2016 to 27 October 2025. Variables include `Temp`, `Rain`, `RH`, `Water Content`, `Temp 20cm`, radiation, wind, and pressure.
- `M1.csv`: weather-data variant with dates in 2016 shifted back by one day; other years are unchanged.
- `M2.py`: generates a second variant, shifting 2016 dates back by two days. `M2.csv` is not an input to the figure scripts listed above.

**Precipitation units:** Fig. 7 multiplies the `Rain` column in `M1.csv` by 48 before binning precipitation. Check the sampling interval and original measurement units before using another meteorological dataset.

### 5.4 Maps and photographs

`data/Map/` contains administrative and maritime boundary layers, monsoon/non-monsoon boundaries, Natural Earth shapefiles, and saved precipitation contours. Keep the Shapefile components (`.shp`, `.shx`, `.dbf`, `.prj`) together. Fig. 0 also uses the 2022 external land-cover NetCDF file.

`data/Picture/` contains `Dendrometer.jpg` and `Tree death.jpg`.

## 6. Data-processing workflow

| Script | Processing step | Output or requirement |
|---|---|---|
| `Dendrometer_dayily/dendrometer_diff.py` | Shifts timestamps back 30 minutes, takes daily maxima, calculates consecutive-day differences, and clips negative changes to zero | `Dendrometer_dayily/dendrometer_diff.csv` |
| `Growth/split.py` | Selects growing-season windows from daily differences and separates SPH, SPL, and SSL | Group tables under `Growth/` |
| `Growth/standardized/SPH.py`, `SPL.py`, `SSL.py` | Standardizes individual growth series and calculates group biweight chronologies | `Growth/standardized/` |
| `TWD/4.R` | Processes 30-minute dendrometer measurements using `treenetproc` L1/L2, extracts daily maximum TWD, and separates groups | `TWD/daily_twd_SPH.csv`, `daily_twd_SPL.csv`, `daily_twd_SSL.csv`; timezone `Etc/GMT-8` (UTC+8) |
| `TWD/standardized/SPH.py`, `SPL.py`, `SSL.py` | Standardizes individual TWD series and calculates group biweight chronologies | `TWD/standardized/daily_twd_<group>.csv` |
| `Detrending/RCS+SFRCS.R` | Calculates tree-ring chronologies and associated metrics | Configured to process `HDY2.rwl` into `Detrending/HDY2.csv` |
| `Climate/1.5.py` | Extracts site climate variables and assembles monthly values by year | `Climate/1.5climate.csv`; requires external ERA5 and SPEI data |
| `Meteorological data/M1.py`, `M2.py` | Produces alternative 2016 date alignments | `M1.csv` and optionally `M2.csv` |
| `Map/Precipitation boundary/Precipitation boundary.py` | Calculates 1991–2020 mean annual precipitation, interpolates it, and extracts the main 200, 400, and 600 mm contours | Shapefile used by Fig. 0; requires `climate14.nc` |

For a complete rebuild, the usual order is:

1. Prepare the raw dendrometer, tree-ring, and climate inputs.
2. Generate the tree-ring chronologies and annual climate table.
3. Calculate daily dendrometer changes, split the growth groups, and build standardized growth chronologies.
4. Extract TWD from the raw dendrometer measurements and build standardized TWD chronologies.
5. Generate `M1.csv` and the precipitation-contour Shapefile where needed.
6. Run the figure scripts. Export Fig. 1 separately from its PSD file.

**Configuration notes:** The growing-season windows are set separately in the growth, TWD, standardization, and plotting scripts. `Detrending/RCS+SFRCS.R` is currently configured for `HDY2.rwl` only; rebuilding all chronology tables requires changing its inputs. The script removes the first three lines of each `.rwl` file before reading it, so the input format must be checked. The original preparation of `M.csv` is not included in these scripts.

## 7. External data

These files are referenced through absolute paths on `H:/` and are not included under `D:/data/`.

| File | Use |
|---|---|
| `H:/Land use/C3S-LC-L4-LCCS-Map-300m-P1Y-2022-v2.1.1.nc` | Fig. 0 land cover |
| `H:/Climatic data/SPEI/SPEI2025month/SPEI_0.5deg.nc` | Climate extraction and Fig. 8 |
| `H:/Climatic data/ERA5/mixed.nc` | Climate extraction |
| `H:/Climatic data/ERA5/mixed2.nc` | Climate extraction |
| `H:/Climatic data/ERA5/radiation.nc` | Climate extraction |
| `H:/Climatic data/ERA5/RH-VPD.nc` | Climate extraction |
| `H:/Climatic data/ERA5/soil.nc` | Climate extraction |
| `H:/Climatic data/month/climate14.nc` | Precipitation-contour generation |

Data sources:

- **Land cover:** [Copernicus satellite land-cover dataset](https://cds.climate.copernicus.eu/datasets/satellite-land-cover), 2022, 300 m, version 2.1.1.
- **ERA5:** [Copernicus Climate Data Store](https://cds.climate.copernicus.eu/).
- **CRU:** [Climatic Research Unit data portal](https://crudata.uea.ac.uk/).

The downloaded datasets must match the variables, units, time coordinates, and spatial coverage expected by the scripts. The scripts do not include the full procedure used to assemble the local `climate14.nc` or `SPEI_0.5deg.nc` files from their source data.

## 8. Reproducibility notes

The scripts use a mixture of supplied processed data and external inputs. Running the figure scripts reproduces plots from those inputs; it does not automatically regenerate all intermediate datasets. Figure appearance and results also depend on the versions and contents of the local source files.

Before rerunning the full workflow, check the absolute paths, the configured chronology inputs, the seasonal date windows, and the rainfall conversion used in Fig. 7. The supplied figures have not been regenerated as part of this README revision.
