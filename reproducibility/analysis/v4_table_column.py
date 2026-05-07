#!/usr/bin/env python3
"""Compute the v4 ensemble values for every row of the website comparison table."""
import glob
import numpy as np
import netCDF4 as nc
from scipy import stats

YEARS = [2022, 2023, 2024, 2025, 2026]

with nc.Dataset("/opt/x1.40962.static.nc") as ds:
    areaCell = ds.variables["areaCell"][:]
    ivg = ds.variables["ivgtyp"][:]
    if ivg.ndim == 2: ivg = ivg[0]

sample = "/host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_2025_prescribed_ccn_salt/history.2025-01-12_00.00.00.nc"
with nc.Dataset(sample) as ds:
    lat = np.degrees(ds.variables["latCell"][:])
    lon = np.degrees(ds.variables["lonCell"][:])
    lon = np.where(lon > 180, lon - 360, lon)

idx_eq    = np.where((lat > -10) & (lat <  10))[0]
idx_5S    = np.where((lat >  -7) & (lat <  -3))[0]
idx_5N    = np.where((lat >   3) & (lat <   7))[0]
idx_arc   = np.where(lat >  70)[0]
idx_ant   = np.where(lat < -70)[0]


def w_avg(field, idx):
    w = areaCell[idx]
    return float(np.sum(field[idx] * w) / np.sum(w))


def metrics_for(year, phase):
    files = sorted(glob.glob(
        f"/host/GITIGNORE/simulation_outputs/"
        f"results_120km_jan_pohlker_l4_{year}_prescribed_ccn_{phase}/history.*.nc"))
    out = {}
    with nc.Dataset(files[-1]) as ds:
        rain = ds.variables["rainc"][0, :] + ds.variables["rainnc"][0, :]
        t2m  = ds.variables["t2m"][0, :]
        u10  = ds.variables["u10"][0, :]
        v10  = ds.variables["v10"][0, :]
    out["P_eq"]    = w_avg(rain, idx_eq) / 30.0
    out["P_5S"]    = w_avg(rain, idx_5S) / 30.0
    out["P_5N"]    = w_avg(rain, idx_5N) / 30.0
    out["T_arc"]   = w_avg(t2m,  idx_arc)
    out["T_ant"]   = w_avg(t2m,  idx_ant)
    spd = np.sqrt(u10**2 + v10**2)
    out["W_arc"]   = w_avg(spd,  idx_arc)
    return out


print("Computing per-pair deltas...")
deltas = {k: [] for k in ["P_eq", "P_5S", "P_5N", "T_arc", "T_ant", "W_arc"]}
for y in YEARS:
    print(f"  {y} ...")
    s = metrics_for(y, "salt")
    n = metrics_for(y, "nosalt")
    for k in deltas:
        d = s[k] - n[k]
        deltas[k].append(d)
        print(f"     {k}: salt={s[k]:.4f}  nosalt={n[k]:.4f}  delta={d:+.4f}")

print("\n=== ENSEMBLE STATS (one-sample t-test against zero) ===")
units = {"P_eq":"mm/day", "P_5S":"mm/day", "P_5N":"mm/day",
         "T_arc":"K", "T_ant":"K", "W_arc":"m/s"}
labels = {"P_eq":"Equatorial rain (band avg, -10..+10)",
          "P_5S":"Rain at 5S zonal",
          "P_5N":"Rain at 5N zonal",
          "T_arc":"Arctic temp (>70N)",
          "T_ant":"Antarctic temp (<70S)",
          "W_arc":"Arctic 10m wind (>70N)"}
for k, arr in deltas.items():
    a = np.array(arr)
    t, p = stats.ttest_1samp(a, 0)
    sig = "p<0.01 ✓✓" if p < 0.01 else "p<0.05 ✓" if p < 0.05 else "p<0.10 marg" if p < 0.10 else "n.s."
    print(f"  {labels[k]:38s} mean={a.mean():+8.4f} ± {a.std(ddof=1):6.4f} {units[k]:7s} "
          f"t={t:+5.2f}  p={p:.4f}  {sig}")

# Also pull 30S transport from existing npz
print("\n=== 30S TRANSPORT FROM EXISTING NPZ ===")
data = np.load("/host/mpas_analysis/v4_figures/v4_ensemble_data.npz", allow_pickle=True)
results = data["results"].item()
deltas_30S = [results[y]["salt_lhf"][-30] - results[y]["nosalt_lhf"][-30] for y in YEARS]
a = np.array(deltas_30S)
t, p = stats.ttest_1samp(a, 0)
sig = "p<0.01 ✓✓" if p < 0.01 else "p<0.05 ✓" if p < 0.05 else "p<0.10 marg" if p < 0.10 else "n.s."
print(f"  30S transport per-year: {[f'{d:+.1f}' for d in deltas_30S]}")
print(f"  30S transport: mean={a.mean():+8.2f} ± {a.std(ddof=1):6.2f} TW  t={t:+5.2f}  p={p:.4f}  {sig}")
