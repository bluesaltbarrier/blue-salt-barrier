#!/usr/bin/env python3
"""Verify Jan v2 init files and completed outputs have correct nwfa baseline.

Read-only. Safe to run while ensemble is in progress.
"""
import netCDF4 as nc
import numpy as np
import glob, os

INIT_DIR = "/opt/jan_v2"
OUT_ROOT = "/host/GITIGNORE/simulation_outputs"
STATIC   = "/opt/x1.40962.static.nc"
YEARS    = [2022, 2023, 2024, 2025, 2026]

with nc.Dataset(STATIC) as ds:
    ivg = ds.variables["ivgtyp"][:]
    if ivg.ndim == 2:
        ivg = ivg[0]
ig2 = (ivg == 2)
print(f"IGBP-2 cells globally: {int(ig2.sum())}\n")

def report(nwfa, label):
    rho_s, rho_cb = 1.15, 1.0
    def m(sel, k0, k1):
        rho = rho_s if k0 == 0 else rho_cb
        if k1 - k0 == 1:
            sub = nwfa[sel, k0]
        else:
            sub = nwfa[sel, k0:k1].mean(axis=1)
        return float(sub.mean() * rho * 1e-6)
    s_g  = m(slice(None), 0, 1)
    s_i  = m(ig2,         0, 1)
    s_n  = m(~ig2,        0, 1)
    cb_i = m(ig2,         5, 9)
    cb_n = m(~ig2,        5, 9)
    print(f"  {label:32s}  IGBP-2 surf {s_i:7.0f}  CB {cb_i:6.0f}  |  nonIG surf {s_n:6.0f}  CB {cb_n:6.0f}  |  global surf {s_g:6.0f}")

print("=" * 110)
print("INIT FILES  (/opt/jan_v2/)")
print("=" * 110)
for y in YEARS:
    f = f"{INIT_DIR}/x1.40962.init.{y}.jan.pristine_v2.nc"
    if not os.path.exists(f):
        print(f"  MISSING: {f}")
        continue
    with nc.Dataset(f) as ds:
        nwfa = ds.variables["nwfa"][0, :, :]
    report(nwfa, f"init {y}")

print()
print("=" * 110)
print("COMPLETED OUTPUT DIRS (day-0 init dump vs day-30 final)")
print("=" * 110)
for y in YEARS:
    for phase in ("salt", "nosalt"):
        d = f"{OUT_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_{phase}"
        files = sorted(glob.glob(f"{d}/history.*.nc"))
        if len(files) < 25:
            print(f"  {y} {phase:6s}: {len(files)} files -- not yet complete, skipping")
            continue
        with nc.Dataset(files[0]) as ds:
            nw0 = ds.variables["nwfa"][0, :, :]
        with nc.Dataset(files[-1]) as ds:
            nwL = ds.variables["nwfa"][0, :, :]
        report(nw0, f"{y} {phase} day-0  ")
        report(nwL, f"{y} {phase} day-end")
        s_i_0 = float(nw0[ig2, 0].mean() * 1.15e-6)
        s_i_L = float(nwL[ig2, 0].mean() * 1.15e-6)
        s_n_0 = float(nw0[~ig2, 0].mean() * 1.15e-6)
        s_n_L = float(nwL[~ig2, 0].mean() * 1.15e-6)
        di = 100 * abs(s_i_L - s_i_0) / s_i_0 if s_i_0 > 0 else float("inf")
        dn = 100 * abs(s_n_L - s_n_0) / s_n_0 if s_n_0 > 0 else float("inf")
        ok = di < 1.0 and dn < 1.0
        print(f"  {' ' * 32}  IGBP-2 drift {di:5.2f}%   non-IG drift {dn:5.2f}%   {'PASS' if ok else 'FAIL'}")
        print()

print("=" * 110)
print("Done.")
