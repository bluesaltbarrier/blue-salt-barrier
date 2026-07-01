#!/usr/bin/env python3
"""Side-by-side comparison: v4 buggy ensemble vs v2 corrected ensemble.

For each year-pair that v2 has completed, compute meridional latent heat
transport (TW) at standard latitudes and Amazon-mean precipitation (mm),
then print v4 (from preserved npz) vs v2 (computed fresh from history files).

Read-only. Safe to run alongside the in-progress ensemble.
"""
import netCDF4 as nc
import numpy as np
import glob, os

LV = 2.5e6
G  = 9.81
R_E = 6371000.

V4_NPZ   = "/host/mpas_analysis/v4_figures/v4_ensemble_data.npz"
V2_ROOT  = "/host/GITIGNORE/simulation_outputs"
STATIC   = "/opt/x1.40962.static.nc"

LATITUDES = [-70, -50, -30, 30, 50, 70]
YEARS     = [2022, 2023, 2024, 2025, 2026]

print("Loading mesh + masks...")
with nc.Dataset(STATIC) as ds:
    areaCell = ds.variables["areaCell"][:]
    ivg = ds.variables["ivgtyp"][:]
    if ivg.ndim == 2: ivg = ivg[0]

# Pull lat/lon from any v2 history file
sample = None
for y in YEARS:
    for ph in ("salt","nosalt"):
        cand = sorted(glob.glob(f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_{ph}/history.*.nc"))
        if len(cand) >= 25:
            sample = cand[0]; break
    if sample: break
if not sample:
    raise SystemExit("No complete v2 pair found yet.")
with nc.Dataset(sample) as ds:
    lat = np.degrees(ds.variables["latCell"][:])
    lon = np.degrees(ds.variables["lonCell"][:])
    lon = np.where(lon > 180, lon - 360, lon)

amz_idx  = np.where((lat > -15) & (lat < 5) & (lon > -75) & (lon < -50) & (ivg == 2))[0]
band_idx = {lt: np.where((lat > lt - 2) & (lat < lt + 2))[0] for lt in LATITUDES}
A_band   = {lt: areaCell[band_idx[lt]] for lt in LATITUDES}
dy_band  = R_E * np.radians(4.0)


def lhf_transport(files, lt):
    band = band_idx[lt]
    A = A_band[lt]
    accum = 0.0; n = 0
    for f in files:
        with nc.Dataset(f) as ds:
            qv = ds.variables["qv"][0, band, :]
            v  = ds.variables["uReconstructMeridional"][0, band, :]
            p  = ds.variables["pressure"][0, band, :]
        dp = -np.diff(p, axis=1)
        H  = LV * np.sum(qv[:, :-1] * v[:, :-1] * dp / G, axis=1)
        accum += np.sum(A * H) / dy_band
        n += 1
    return accum / n / 1e12   # TW


def amz_precip(path):
    with nc.Dataset(path) as ds:
        return float((ds.variables["rainc"][0,:] + ds.variables["rainnc"][0,:])[amz_idx].mean())


# Load v4 numbers
v4 = np.load(V4_NPZ, allow_pickle=True)["results"].item()
print(f"v4 npz years: {sorted(v4.keys())}\n")

complete_years = []
for y in YEARS:
    salt_dir   = f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_salt"
    nosalt_dir = f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_nosalt"
    sf = sorted(glob.glob(f"{salt_dir}/history.*.nc"))
    nf = sorted(glob.glob(f"{nosalt_dir}/history.*.nc"))
    if len(sf) >= 25 and len(nf) >= 25:
        complete_years.append(y)

if not complete_years:
    raise SystemExit("No v2 year-pair is complete yet.")
print(f"v2 complete years: {complete_years}\n")

print(f"{'='*100}")
print(f"PER-YEAR COMPARISON   (v4 = buggy global-pristine baseline; v2 = corrected GoCart baseline)")
print(f"{'='*100}\n")

for y in complete_years:
    print(f"---- {y} ----")
    sf = sorted(glob.glob(f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_salt/history.*.nc"))
    nf = sorted(glob.glob(f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_nosalt/history.*.nc"))

    # Amazon precip
    v2_amz_s = amz_precip(sf[-1])
    v2_amz_n = amz_precip(nf[-1])
    v4_amz_d = v4[y]["salt_p"] - v4[y]["nosalt_p"]
    v2_amz_d = v2_amz_s - v2_amz_n
    print(f"  Amazon delta-P (mm/30d) : v4 = {v4_amz_d:+7.2f}    v2 = {v2_amz_d:+7.2f}    delta = {v2_amz_d - v4_amz_d:+7.2f}")

    # LHF transports
    print(f"  Lat   v4 dLHF (TW)   v2 dLHF (TW)   diff (TW)")
    for lt in LATITUDES:
        v4_d = v4[y]["salt_lhf"][lt] - v4[y]["nosalt_lhf"][lt]
        v2_s = lhf_transport(sf, lt)
        v2_n = lhf_transport(nf, lt)
        v2_d = v2_s - v2_n
        print(f"  {lt:+4d}    {v4_d:+8.1f}      {v2_d:+8.1f}     {v2_d - v4_d:+8.1f}")
    print()

# Ensemble-level comparison for the headline 30N metric (with however many years we have)
print(f"{'='*100}")
print(f"HEADLINE 30N delta-LHF (over years available so far)")
print(f"{'='*100}")
v4_30N = [v4[y]["salt_lhf"][30] - v4[y]["nosalt_lhf"][30] for y in complete_years]
v2_30N = []
for y in complete_years:
    sf = sorted(glob.glob(f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_salt/history.*.nc"))
    nf = sorted(glob.glob(f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_nosalt/history.*.nc"))
    v2_30N.append(lhf_transport(sf, 30) - lhf_transport(nf, 30))
print(f"  v4 (buggy global-pristine):  {v4_30N}")
print(f"     mean = {np.mean(v4_30N):+.2f}  std = {np.std(v4_30N, ddof=1) if len(v4_30N)>1 else float('nan'):.2f}")
print(f"  v2 (corrected GoCart bg):    {[round(x,2) for x in v2_30N]}")
print(f"     mean = {np.mean(v2_30N):+.2f}  std = {np.std(v2_30N, ddof=1) if len(v2_30N)>1 else float('nan'):.2f}")
print(f"  v2/v4 magnitude ratio = {np.mean(v2_30N)/np.mean(v4_30N) if np.mean(v4_30N) != 0 else float('nan'):.2f}")
print()
print(f"(N={len(complete_years)} pairs so far; full ensemble = 5.)")
