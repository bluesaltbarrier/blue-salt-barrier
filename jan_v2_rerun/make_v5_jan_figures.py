#!/usr/bin/env python3
"""Generate the two missing v5 January figures for V3:
  - v5_jan_fig1_per_year_dLHF.png  (per-year ΔLHF bars at 30°S, 30°N, 50°N, 70°N)
  - v5_jan_fig2_meridional_dLHF.png  (meridional ΔLHF profile mean ± 1σ, N=5)

Reads the v5 January simulation outputs (jan_v2_* dirs), writes PNGs to
/host/mpas_analysis/v5_figures/.  Run inside the mpas8 container.
"""
import os, glob
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

LV = 2.5e6
G = 9.81
R_E = 6371000.

V2_ROOT = "/host/GITIGNORE/simulation_outputs"
OUT_DIR = "/host/mpas_analysis/v5_figures"
STATIC = "/opt/x1.40962.static.nc"
YEARS = [2022, 2023, 2024, 2025, 2026]
LATS_BARS = [-30, 30, 50, 70]
LATS_PROFILE = [-70, -60, -50, -40, -30, -20, -10, 10, 20, 30, 40, 50, 60, 70, 80]

os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams.update({
    "font.size": 11, "axes.labelsize": 11, "axes.titlesize": 12,
    "legend.fontsize": 9, "savefig.dpi": 300, "savefig.bbox": "tight",
    "axes.grid": True, "grid.alpha": 0.3,
})

# Mesh + lat/lon
print("Loading mesh...")
with nc.Dataset(STATIC) as ds:
    areaCell = ds.variables["areaCell"][:]
sample = sorted(glob.glob(
    f"{V2_ROOT}/results_120km_jan_v2_2025_prescribed_ccn_salt/history.*.nc"))[0]
with nc.Dataset(sample) as ds:
    lat = np.degrees(ds.variables["latCell"][:])

dy_band = R_E * np.radians(4.0)
band_idx = {lt: np.where((lat > lt - 2) & (lat < lt + 2))[0] for lt in LATS_PROFILE}
A_band = {lt: areaCell[band_idx[lt]] for lt in LATS_PROFILE}


def transports_for_dir(d):
    """Open each history file ONCE, compute ΔLHF at all latitudes (TW)."""
    files = sorted(glob.glob(f"{d}/history.*.nc"))
    accum = {lt: 0.0 for lt in LATS_PROFILE}
    n = 0
    for f in files:
        with nc.Dataset(f) as ds:
            qv = ds.variables["qv"][0, :, :]
            v = ds.variables["uReconstructMeridional"][0, :, :]
            p = ds.variables["pressure"][0, :, :]
        for lt in LATS_PROFILE:
            idx = band_idx[lt]
            A = A_band[lt]
            qv_b = qv[idx, :]; v_b = v[idx, :]; p_b = p[idx, :]
            dp = -np.diff(p_b, axis=1)
            H = LV * np.sum(qv_b[:, :-1] * v_b[:, :-1] * dp / G, axis=1)
            accum[lt] += np.sum(A * H) / dy_band
        n += 1
    return {lt: accum[lt] / n / 1e12 for lt in LATS_PROFILE}


print("Gathering v5 January ensemble...")
results = {}
for y in YEARS:
    print(f"  {y}...")
    s = transports_for_dir(f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_salt")
    n = transports_for_dir(f"{V2_ROOT}/results_120km_jan_v2_{y}_prescribed_ccn_nosalt")
    results[y] = {lt: s[lt] - n[lt] for lt in LATS_PROFILE}

# Save numerical data alongside the figures
np.savez(f"{OUT_DIR}/v5_jan_ensemble_data.npz",
         results=results, years=YEARS, latitudes=LATS_PROFILE)


# ===== Figure 1: per-year bars at 30°S, 30°N, 50°N, 70°N =====
print("\nFig 1: per-year bars...")
fig, axes = plt.subplots(1, 4, figsize=(17, 4.5))
for ax, lt in zip(axes, LATS_BARS):
    deltas = [results[y][lt] for y in YEARS]
    colors = ["tab:red" if d < 0 else "tab:blue" for d in deltas]
    ax.bar(range(len(YEARS)), deltas, color=colors, edgecolor="black", lw=0.7)
    ax.set_xticks(range(len(YEARS)))
    ax.set_xticklabels([str(y) for y in YEARS])
    ax.axhline(0, color="black", lw=1)
    lbl = f"{abs(lt)}°{'S' if lt < 0 else 'N'}"
    ax.set_title(f"{lbl} northward latent heat transport")
    ax.set_ylabel("ΔLHF (SALT − NOSALT, TW)")
    ax.set_xlabel("January-start year")
    arr = np.array(deltas)
    t, p = stats.ttest_1samp(arr, 0)
    sig = "p<0.01 ✓✓" if p < 0.01 else "p<0.05 ✓" if p < 0.05 else "p<0.10 marg" if p < 0.10 else "n.s."
    ax.text(0.5, 0.97,
            f"mean={arr.mean():+.1f} ± {arr.std(ddof=1):.1f} TW\nt={t:+.2f}, p={p:.4f}\n{sig}",
            transform=ax.transAxes, ha="center", va="top",
            fontsize=9, family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white",
                      edgecolor="gray", alpha=0.85))
fig.suptitle("v5 January 5-pair ensemble (corrected) — ΔLHF (SALT − NOSALT) by year",
             fontsize=13, weight="bold")
fig.tight_layout()
fig.savefig(f"{OUT_DIR}/v5_jan_fig1_per_year_dLHF.png", dpi=300)
plt.close(fig)
print("  wrote v5_jan_fig1_per_year_dLHF.png")


# ===== Figure 2: meridional profile mean ± 1σ =====
print("Fig 2: meridional profile...")
fig, ax = plt.subplots(figsize=(9, 5.5))
all_profiles = []
for y in YEARS:
    d = [results[y][lt] for lt in LATS_PROFILE]
    all_profiles.append(d)
    ax.plot(LATS_PROFILE, d, "o-", alpha=0.4, lw=1, label=str(y))
all_profiles = np.array(all_profiles)
mp = all_profiles.mean(0)
sp = all_profiles.std(0, ddof=1)
ax.plot(LATS_PROFILE, mp, "k-o", lw=2.5, ms=7, label="ensemble mean (N=5)")
ax.fill_between(LATS_PROFILE, mp - sp, mp + sp,
                color="black", alpha=0.15, label="±1σ")
ax.axhline(0, color="black", lw=0.8)
ax.axvline(0, color="black", lw=0.8, ls="--", alpha=0.5)
ax.set_xlabel("Latitude (°)")
ax.set_ylabel("Δ northward LHF (SALT − NOSALT, TW)")
ax.set_title("v5 January ensemble (corrected) — meridional ΔLHF profile, mean ± 1σ")
ax.legend(loc="best", ncol=2, fontsize=9)
fig.tight_layout()
fig.savefig(f"{OUT_DIR}/v5_jan_fig2_meridional_dLHF.png", dpi=300)
plt.close(fig)
print("  wrote v5_jan_fig2_meridional_dLHF.png")

print(f"\nDone. Outputs in {OUT_DIR}/")
for f in sorted(os.listdir(OUT_DIR)):
    if f.startswith("v5_jan_"):
        print(f"  {f}")
