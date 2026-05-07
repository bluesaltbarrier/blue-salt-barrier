#!/usr/bin/env python3
"""
Variance-amplification analysis for the 5-year January ensemble (2022-2026
SALT + NOSALT pairs at 240 km l=4 Pohlker-Dg pristine).

Computes:
  1. Per-year Amazon ΔP (SALT - NOSALT) over IGBP-2 cells
  2. Per-run 30°N northward latent-heat transport (Vq integrated)
  3. F-test on Var(SALT)/Var(NOSALT) at 30°N transport (df=4,4)
  4. Per-year sign-flip persistence in Amazon ΔP
  5. Convergence diagnostic on each of the 10 runs (depletion plot data)

Outputs:
  /host/mpas_analysis/5yr_ensemble_summary.txt
  /host/mpas_analysis/5yr_ensemble_results.npz
  /host/mpas_analysis/5yr_ensemble_signflip_panel.png
"""
import os, glob
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

YEARS = [2022, 2023, 2024, 2025, 2026]
RUN_BASE = "/host/GITIGNORE/simulation_outputs/results_240km_jan_l4_{year}_{kind}"
STATIC = "/opt/x1.10242/x1.10242.static.nc"
OUT_DIR = "/host/mpas_analysis"

# Constants
G = 9.81
LV = 2.5e6   # latent heat of vaporization, J/kg
PI = 3.14159265
RE = 6371000.0   # Earth radius, m

def amazon_mask(lat, lon, ivgtyp):
    """IGBP-2 cells inside Amazon lat/lon box."""
    return (ivgtyp == 2) & (lat > -15) & (lat < 5) & (lon > -75) & (lon < -50)

def total_rainfall(run_dir, mask):
    """30-day rainfall (mm) averaged over masked cells. Sum over rainnc + rainc
    at last history file, since these are accumulated since simulation start."""
    files = sorted(glob.glob(os.path.join(run_dir, "history.*.nc")))
    last = files[-1]
    with nc.Dataset(last) as ds:
        # rainnc and rainc are accumulated; just take the last value
        rainnc = ds.variables["rainnc"][0, :]
        try:
            rainc = ds.variables["rainc"][0, :]
            total = rainnc + rainc
        except KeyError:
            total = rainnc
    return float(np.asarray(total[mask]).mean())

def latent_heat_transport_30N(run_dir):
    """Compute time-averaged northward latent heat transport at 30°N.
    Vq = integral(rho * v * qv * dz) summed at lat=30°N, in W/m,
    then integrated zonally. Returns total in TW."""
    files = sorted(glob.glob(os.path.join(run_dir, "history.*.nc")))
    # Use a few midstream files for time-mean, skip first 5 days as spinup
    use_files = files[10:]
    if not use_files:
        use_files = files
    # Get mesh
    with nc.Dataset(files[0]) as ds:
        lat = np.degrees(ds.variables["latCell"][:])
        lon = np.degrees(ds.variables["lonCell"][:])
        lon = np.where(lon > 180, lon - 360, lon)
        zgrid = ds.variables["zgrid"][:, :]   # (nCells, 56)
        areaCell = ds.variables["areaCell"][:]
    z_mid = 0.5 * (zgrid[:, :-1] + zgrid[:, 1:])
    dz = np.diff(zgrid, axis=1)   # (nCells, 55)

    # Pick cells in 28-32°N latitude band
    band_mask = (lat >= 28) & (lat <= 32)
    band_idx = np.where(band_mask)[0]

    transport_per_file = []
    for f in use_files:
        with nc.Dataset(f) as ds:
            v = ds.variables["uReconstructMeridional"][0, band_idx, :]   # (n_band, nVert)
            qv = ds.variables["qv"][0, band_idx, :]
            rho = ds.variables["rho"][0, band_idx, :]
        # Column-integrated v*qv*rho per cell, units: kg/m²/s
        col_vq = (v * qv * rho * dz[band_idx, :]).sum(axis=1)
        # Multiply by Lv to get latent heat flux, W/m² per cell? No, this is W/m²×depth
        # Actually: v(m/s) * qv(kg/kg) * rho(kg/m³) * dz(m) = kg of water vapor per m² per s, integrated through column
        # Multiply by Lv to get J / m² / s per cell × column height (column-integrated flux)
        # To get total transport across the band: sum over cells × cell-area-projected-to-x-axis
        # Use cell area in band, accept this as approximate
        cell_area = areaCell[band_idx]
        # zonal length spanned by cells in this band ≈ sum of cell-edge-projected-on-x
        # crude approximation: use sqrt(cell_area) as effective edge length per cell
        edge_len = np.sqrt(cell_area)
        # Total northward flux in W: sum of per-cell (v*qv*rho*dz_total) * Lv * edge_len
        # but we want band-integrated, so the right quantity is sum over cells:
        # F_band = sum( col_vq[i] * Lv * edge_len[i] )   in J/s = W
        F_band = float((col_vq * LV * edge_len).sum())
        transport_per_file.append(F_band)
    mean_transport = np.mean(transport_per_file)
    return mean_transport / 1e12   # convert W → TW

# ----------------- Main -----------------
print("Loading mesh + IGBP-2 mask from static.nc...")
with nc.Dataset(STATIC) as ds:
    _ivg = ds.variables["ivgtyp"][:]
    ivgtyp = _ivg[0] if _ivg.ndim == 2 else _ivg

# Get lat/lon from any history file
sample_file = sorted(glob.glob(RUN_BASE.format(year=2022, kind="salt") + "/history.*.nc"))[0]
with nc.Dataset(sample_file) as ds:
    lat = np.degrees(ds.variables["latCell"][:])
    lon = np.degrees(ds.variables["lonCell"][:])
    lon = np.where(lon > 180, lon - 360, lon)
amz_mask = amazon_mask(lat, lon, ivgtyp)
print(f"Amazon IGBP-2 cells: {amz_mask.sum()}")

# ----------------- Per-run computations -----------------
results = {}
print()
print("Per-run analysis:")
print(f"{'year':>5} {'run':>8} {'amzP30 (mm)':>13} {'30N tr (TW)':>13}")
print("-" * 45)
for year in YEARS:
    results[year] = {}
    for kind in ["salt", "nosalt"]:
        run_dir = RUN_BASE.format(year=year, kind=kind)
        if not os.path.isdir(run_dir):
            print(f"  MISSING: {run_dir}")
            continue
        amz_P = total_rainfall(run_dir, amz_mask)
        tr30 = latent_heat_transport_30N(run_dir)
        results[year][kind] = {"amz_P_30day": amz_P, "tr30_TW": tr30}
        print(f"{year:>5} {kind:>8} {amz_P:>13.2f} {tr30:>13.2f}")

# ----------------- Sign-flip and variance analysis -----------------
print()
print("Per-year SALT - NOSALT differentials:")
print(f"{'year':>5} {'ΔAmz P (mm)':>14} {'Δtr30 (TW)':>13}")
print("-" * 35)
delta_P = []
delta_tr = []
salt_tr_list = []
nosalt_tr_list = []
for year in YEARS:
    if "salt" not in results[year] or "nosalt" not in results[year]:
        continue
    dP = results[year]["salt"]["amz_P_30day"] - results[year]["nosalt"]["amz_P_30day"]
    dT = results[year]["salt"]["tr30_TW"] - results[year]["nosalt"]["tr30_TW"]
    delta_P.append(dP); delta_tr.append(dT)
    salt_tr_list.append(results[year]["salt"]["tr30_TW"])
    nosalt_tr_list.append(results[year]["nosalt"]["tr30_TW"])
    print(f"{year:>5} {dP:>+14.2f} {dT:>+13.2f}")

delta_P = np.array(delta_P)
delta_tr = np.array(delta_tr)
salt_tr = np.array(salt_tr_list)
nosalt_tr = np.array(nosalt_tr_list)

# ----------------- Statistics -----------------
print()
print("=" * 60)
print("ENSEMBLE STATISTICS")
print("=" * 60)
print()
print(f"Amazon ΔP (mm/30-day, SALT - NOSALT):")
print(f"  mean: {delta_P.mean():+.2f}")
print(f"  std:  {delta_P.std(ddof=1):+.2f}")
print(f"  range: [{delta_P.min():+.2f}, {delta_P.max():+.2f}]")
print(f"  fraction positive (rainfall enhanced): {(delta_P > 0).sum()}/{len(delta_P)} years")
print(f"  fraction negative (rainfall suppressed): {(delta_P < 0).sum()}/{len(delta_P)} years")
print()
print(f"30°N latent heat transport (TW):")
print(f"  SALT mean ± std:    {salt_tr.mean():+.2f} ± {salt_tr.std(ddof=1):.2f}")
print(f"  NOSALT mean ± std:  {nosalt_tr.mean():+.2f} ± {nosalt_tr.std(ddof=1):.2f}")
print(f"  SALT-NOSALT diff:   {delta_tr.mean():+.2f} ± {delta_tr.std(ddof=1):.2f}")
print()
print(f"Variance amplification F-test (one-sided, df=4,4):")
var_salt = np.var(salt_tr, ddof=1)
var_nosalt = np.var(nosalt_tr, ddof=1)
print(f"  Var(SALT) = {var_salt:.2f} TW²")
print(f"  Var(NOSALT) = {var_nosalt:.2f} TW²")
F = var_salt / var_nosalt if var_nosalt > 0 else np.nan
print(f"  F = Var(SALT)/Var(NOSALT) = {F:.3f}")
# Critical value at p=0.05 one-sided, df=4,4
F_crit_05 = stats.f.ppf(0.95, 4, 4)
F_crit_10 = stats.f.ppf(0.90, 4, 4)
print(f"  F-critical at p=0.05 one-sided (df=4,4): {F_crit_05:.3f}")
print(f"  F-critical at p=0.10 one-sided (df=4,4): {F_crit_10:.3f}")
if F > F_crit_05:
    p_val = 1 - stats.f.cdf(F, 4, 4)
    print(f"  RESULT: F > F_crit at p=0.05 → variance amplification SUPPORTED (p ≈ {p_val:.3f})")
elif F > F_crit_10:
    p_val = 1 - stats.f.cdf(F, 4, 4)
    print(f"  RESULT: F > F_crit at p=0.10 (suggestive but not significant at p=0.05); p ≈ {p_val:.3f}")
elif F > 1:
    p_val = 1 - stats.f.cdf(F, 4, 4)
    print(f"  RESULT: F > 1 (variance higher in SALT) but not significant; p ≈ {p_val:.3f}")
else:
    p_val = stats.f.cdf(F, 4, 4)
    print(f"  RESULT: F < 1 (variance lower in SALT) — does NOT support amplification; p ≈ {p_val:.3f}")

# ----------------- Save and plot -----------------
np.savez(os.path.join(OUT_DIR, "5yr_ensemble_results.npz"),
         years=YEARS, delta_P=delta_P, delta_tr=delta_tr,
         salt_tr=salt_tr, nosalt_tr=nosalt_tr,
         var_salt=var_salt, var_nosalt=var_nosalt, F=F)
print(f"\nSaved: {OUT_DIR}/5yr_ensemble_results.npz")

# ----- Sign-flip panel figure -----
fig, axs = plt.subplots(1, 2, figsize=(13, 5.5))
# Panel 1: Amazon ΔP per year
ax = axs[0]
colors = ['#c0392b' if d < 0 else '#2874a6' for d in delta_P]
bars = ax.bar(YEARS, delta_P, color=colors, edgecolor='black', linewidth=0.7)
ax.axhline(0, color='black', linewidth=0.8)
ax.axhline(delta_P.mean(), color='gray', linestyle='--', linewidth=1, label=f"5-yr mean: {delta_P.mean():+.2f} mm")
ax.set_xlabel("Year (Jan 12 0Z init)", fontsize=11)
ax.set_ylabel("Amazon ΔP (mm/30-day, SALT − NOSALT)", fontsize=11)
ax.set_title(f"Amazon rainfall response across 5 January realizations\n"
             f"({sum(d > 0 for d in delta_P)}/5 years positive; range {delta_P.min():+.1f} to {delta_P.max():+.1f} mm)",
             fontsize=11)
ax.grid(alpha=0.3, axis='y')
ax.legend(loc='best', fontsize=9)
for yr, val in zip(YEARS, delta_P):
    ax.text(yr, val + (1 if val >= 0 else -1), f"{val:+.1f}", ha='center', va='bottom' if val >= 0 else 'top', fontsize=9)

# Panel 2: 30°N transport scatter
ax = axs[1]
ax.scatter(YEARS, salt_tr, label="SALT", color="#c0392b", s=80, marker='o', zorder=3)
ax.scatter(YEARS, nosalt_tr, label="NOSALT", color="#2874a6", s=80, marker='s', zorder=3)
for yr, s, n in zip(YEARS, salt_tr, nosalt_tr):
    ax.plot([yr, yr], [s, n], color='gray', linewidth=0.8, alpha=0.5, zorder=1)
ax.axhline(salt_tr.mean(), color='#c0392b', linestyle='--', linewidth=1, alpha=0.5)
ax.axhline(nosalt_tr.mean(), color='#2874a6', linestyle='--', linewidth=1, alpha=0.5)
ax.set_xlabel("Year (Jan 12 0Z init)", fontsize=11)
ax.set_ylabel("30°N northward latent-heat transport (TW)", fontsize=11)
ax.set_title(f"30°N transport per year\n"
             f"Var(SALT)/Var(NOSALT) = {F:.2f}  (F-crit at p=0.05: {F_crit_05:.2f})",
             fontsize=11)
ax.grid(alpha=0.3)
ax.legend(loc='best', fontsize=10)

plt.tight_layout()
out_png = os.path.join(OUT_DIR, "5yr_ensemble_signflip_panel.png")
plt.savefig(out_png, dpi=150, facecolor='white')
plt.close()
print(f"Saved: {out_png}")

# ----- Save text summary -----
out_txt = os.path.join(OUT_DIR, "5yr_ensemble_summary.txt")
with open(out_txt, "w") as f:
    f.write("=" * 60 + "\n")
    f.write("5-year January Ensemble (240 km, l=4 Pohlker-Dg pristine)\n")
    f.write(f"Amazon IGBP-2 cells: {amz_mask.sum()}\n")
    f.write("=" * 60 + "\n\n")
    f.write("Per-year results:\n")
    f.write(f"  {'year':>5}  {'salt amzP':>12}  {'nosalt amzP':>12}  {'ΔP (mm)':>10}  "
            f"{'salt tr30':>11}  {'nosalt tr30':>13}  {'Δtr (TW)':>10}\n")
    for i, year in enumerate(YEARS):
        sP = results[year]["salt"]["amz_P_30day"]
        nP = results[year]["nosalt"]["amz_P_30day"]
        st = results[year]["salt"]["tr30_TW"]
        nt = results[year]["nosalt"]["tr30_TW"]
        f.write(f"  {year:>5}  {sP:>12.2f}  {nP:>12.2f}  {delta_P[i]:>+10.2f}  "
                f"{st:>+11.2f}  {nt:>+13.2f}  {delta_tr[i]:>+10.2f}\n")
    f.write("\n")
    f.write(f"5-year ensemble means and spreads:\n")
    f.write(f"  Amazon ΔP: mean {delta_P.mean():+.2f} mm/30-day, "
            f"std {delta_P.std(ddof=1):.2f}, range [{delta_P.min():+.2f}, {delta_P.max():+.2f}]\n")
    f.write(f"  Δ30°N transport: mean {delta_tr.mean():+.2f} TW, "
            f"std {delta_tr.std(ddof=1):.2f}\n")
    f.write(f"  Sign-flip persistence: {(delta_P > 0).sum()}/{len(delta_P)} years positive\n")
    f.write("\n")
    f.write(f"Variance amplification F-test (Var(SALT)/Var(NOSALT) at 30°N transport):\n")
    f.write(f"  Var(SALT)   = {var_salt:.2f} TW²\n")
    f.write(f"  Var(NOSALT) = {var_nosalt:.2f} TW²\n")
    f.write(f"  F = {F:.3f}  (df=4,4)\n")
    f.write(f"  F-critical at p=0.05 one-sided: {F_crit_05:.3f}\n")
    f.write(f"  F-critical at p=0.10 one-sided: {F_crit_10:.3f}\n")
    if F > F_crit_05:
        f.write(f"  Result: variance amplification SUPPORTED at p<0.05\n")
    elif F > F_crit_10:
        f.write(f"  Result: variance amplification suggestive (p<0.10) but not significant at p=0.05\n")
    elif F > 1:
        f.write(f"  Result: variance higher in SALT but not significant\n")
    else:
        f.write(f"  Result: variance lower in SALT — does NOT support amplification\n")
print(f"Saved: {out_txt}")
print()
print("Done.")
