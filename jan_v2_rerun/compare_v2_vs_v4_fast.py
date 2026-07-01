#!/usr/bin/env python3
"""Faster v4-vs-v2 comparison: opens each history file ONCE and computes
all latitudes in a single pass. ~6x faster than compare_v2_vs_v4.py.

Read-only. Safe to run alongside the in-progress ensemble.
"""
import netCDF4 as nc
import numpy as np
import glob, os, sys

LV  = 2.5e6
G   = 9.81
R_E = 6371000.

V4_NPZ  = "/host/mpas_analysis/v4_figures/v4_ensemble_data.npz"
V2_ROOT = "/host/GITIGNORE/simulation_outputs"
STATIC  = "/opt/x1.40962.static.nc"

LATITUDES = [-70, -50, -30, 30, 50, 70]
YEARS     = [2022, 2023, 2024, 2025, 2026]

# Mesh + masks
with nc.Dataset(STATIC) as ds:
    areaCell = ds.variables["areaCell"][:]
    ivg = ds.variables["ivgtyp"][:]
    if ivg.ndim == 2: ivg = ivg[0]

sample = None
for y in YEARS:
    for ph in ("salt","nosalt"):
        cand = sorted(glob.glob(f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_{ph}/history.*.nc"))
        if len(cand) >= 25:
            sample = cand[0]; break
    if sample: break
if not sample:
    sys.exit("No complete v2 pair found yet.")

with nc.Dataset(sample) as ds:
    lat = np.degrees(ds.variables["latCell"][:])
    lon = np.degrees(ds.variables["lonCell"][:])
    lon = np.where(lon > 180, lon - 360, lon)

# Build a flat list of (lat_label, cell_indices, area_sum_per_dy) for all bands
band_info = {}
dy_band = R_E * np.radians(4.0)
for lt in LATITUDES:
    idx = np.where((lat > lt - 2) & (lat < lt + 2))[0]
    band_info[lt] = (idx, areaCell[idx])

amz_idx = np.where((lat > -15) & (lat < 5) & (lon > -75) & (lon < -50) & (ivg == 2))[0]


def transports_for_dir(d):
    """Open each history file ONCE and compute LHF at all latitudes."""
    files = sorted(glob.glob(f"{d}/history.*.nc"))
    accum = {lt: 0.0 for lt in LATITUDES}
    n = 0
    for f in files:
        with nc.Dataset(f) as ds:
            qv = ds.variables["qv"][0, :, :]
            v  = ds.variables["uReconstructMeridional"][0, :, :]
            p  = ds.variables["pressure"][0, :, :]
        for lt in LATITUDES:
            idx, A = band_info[lt]
            qv_b = qv[idx, :]
            v_b  = v[idx, :]
            p_b  = p[idx, :]
            dp = -np.diff(p_b, axis=1)
            H  = LV * np.sum(qv_b[:, :-1] * v_b[:, :-1] * dp / G, axis=1)
            accum[lt] += np.sum(A * H) / dy_band
        n += 1
    return {lt: accum[lt] / n / 1e12 for lt in LATITUDES}   # TW


def amz_precip(path):
    with nc.Dataset(path) as ds:
        return float((ds.variables["rainc"][0,:] + ds.variables["rainnc"][0,:])[amz_idx].mean())


v4 = np.load(V4_NPZ, allow_pickle=True)["results"].item()

complete = []
for y in YEARS:
    s_dir = f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_salt"
    n_dir = f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_nosalt"
    if len(glob.glob(f"{s_dir}/history.*.nc")) >= 25 and len(glob.glob(f"{n_dir}/history.*.nc")) >= 25:
        complete.append(y)
if not complete:
    sys.exit("No complete v2 year-pair yet.")

print(f"v2 complete years: {complete}\n")
print(f"{'='*100}")
print(f"PER-YEAR COMPARISON (v4 buggy vs v2 corrected)")
print(f"{'='*100}\n")

v2_results = {}
for y in complete:
    print(f"---- {y} ----", flush=True)
    s_dir = f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_salt"
    n_dir = f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_nosalt"
    s_lhf = transports_for_dir(s_dir)
    n_lhf = transports_for_dir(n_dir)
    s_files = sorted(glob.glob(f"{s_dir}/history.*.nc"))
    n_files = sorted(glob.glob(f"{n_dir}/history.*.nc"))
    s_p = amz_precip(s_files[-1])
    n_p = amz_precip(n_files[-1])
    v2_results[y] = {"salt_lhf": s_lhf, "nosalt_lhf": n_lhf, "salt_p": s_p, "nosalt_p": n_p}
    v4_d_p = v4[y]["salt_p"] - v4[y]["nosalt_p"]
    v2_d_p = s_p - n_p
    print(f"  Amazon delta-P (mm/30d): v4 = {v4_d_p:+7.2f}    v2 = {v2_d_p:+7.2f}    diff = {v2_d_p - v4_d_p:+7.2f}", flush=True)
    print(f"  Lat   v4 dLHF (TW)   v2 dLHF (TW)   diff (TW)", flush=True)
    for lt in LATITUDES:
        v4_d = v4[y]["salt_lhf"][lt] - v4[y]["nosalt_lhf"][lt]
        v2_d = s_lhf[lt] - n_lhf[lt]
        print(f"  {lt:+4d}    {v4_d:+8.1f}      {v2_d:+8.1f}     {v2_d - v4_d:+8.1f}", flush=True)
    print(flush=True)

# Ensemble
print(f"{'='*100}")
print(f"ENSEMBLE STATISTICS (N={len(complete)} pairs)  --  one-sample t-test against zero")
print(f"{'='*100}")
from scipy import stats
def tline(arr):
    m = arr.mean(); s = arr.std(ddof=1) if len(arr) > 1 else float('nan')
    if len(arr) > 1:
        t, p = stats.ttest_1samp(arr, 0)
    else:
        t, p = float('nan'), float('nan')
    neg = int((arr < 0).sum())
    sig = "p<0.01" if p < 0.01 else "p<0.05" if p < 0.05 else "p<0.10" if p < 0.10 else "n.s."
    return m, s, t, p, neg, sig
for lt in LATITUDES:
    v4_arr = np.array([v4[y]["salt_lhf"][lt] - v4[y]["nosalt_lhf"][lt] for y in complete])
    v2_arr = np.array([v2_results[y]["salt_lhf"][lt] - v2_results[y]["nosalt_lhf"][lt] for y in complete])
    m4,s4,t4,p4,n4,sig4 = tline(v4_arr)
    m2,s2,t2,p2,n2,sig2 = tline(v2_arr)
    print(f"  {lt:+4d}N:")
    print(f"        v4: mean={m4:+7.1f}  std={s4:5.1f}  t={t4:+6.2f}  p={p4:.4f}  ({n4}/{len(complete)} neg)  {sig4}")
    print(f"        v2: mean={m2:+7.1f}  std={s2:5.1f}  t={t2:+6.2f}  p={p2:.4f}  ({n2}/{len(complete)} neg)  {sig2}")

# Amazon dP ensemble
print()
print("  Amazon delta-P:")
v4_p = np.array([v4[y]["salt_p"] - v4[y]["nosalt_p"] for y in complete])
v2_p = np.array([v2_results[y]["salt_p"] - v2_results[y]["nosalt_p"] for y in complete])
m4,s4,t4,p4,n4,sig4 = tline(v4_p)
m2,s2,t2,p2,n2,sig2 = tline(v2_p)
print(f"        v4: mean={m4:+7.2f}  std={s4:5.2f}  t={t4:+6.2f}  p={p4:.4f}  {sig4}  (mm/30d)")
print(f"        v2: mean={m2:+7.2f}  std={s2:5.2f}  t={t2:+6.2f}  p={p2:.4f}  {sig2}  (mm/30d)")
