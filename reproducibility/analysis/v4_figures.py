#!/usr/bin/env python3
"""
v4 publication figures — one-pass version (reads each file once for all latitudes).
"""
import os
import glob
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy import stats

LV = 2.5e6
G = 9.81
R_E = 6371000.

OUT_DIR = "/host/mpas_analysis/v4_figures"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams.update({
    "font.size": 11, "axes.labelsize": 11, "axes.titlesize": 12,
    "legend.fontsize": 10, "xtick.labelsize": 10, "ytick.labelsize": 10,
    "savefig.dpi": 300, "savefig.bbox": "tight",
    "axes.grid": True, "grid.alpha": 0.3,
})

YEARS = [2022, 2023, 2024, 2025, 2026]
LATITUDES = [-70, -60, -50, -40, -30, -20, -10, 10, 20, 30, 40, 50, 60, 70, 80]

print("Loading mesh...")
with nc.Dataset("/opt/x1.40962.static.nc") as ds:
    areaCell = ds.variables["areaCell"][:]
    ivg = ds.variables["ivgtyp"][:]
    if ivg.ndim == 2: ivg = ivg[0]
sample = "/host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_2025_prescribed_ccn_salt/history.2025-01-12_00.00.00.nc"
with nc.Dataset(sample) as ds:
    lat = np.degrees(ds.variables["latCell"][:])
    lon = np.degrees(ds.variables["lonCell"][:])
    lon = np.where(lon > 180, lon - 360, lon)

amz_idx = np.where((lat > -15) & (lat < 5) & (lon > -75) & (lon < -50) & (ivg == 2))[0]
band_idx = {lat_t: np.where((lat > lat_t - 2) & (lat < lat_t + 2))[0] for lat_t in LATITUDES}
A_band = {lat_t: areaCell[idx] for lat_t, idx in band_idx.items()}
dy_band = R_E * np.radians(4.)


def process(year, phase):
    files = sorted(glob.glob(f"/host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_{year}_prescribed_ccn_{phase}/history.*.nc"))
    if not files: return None
    with nc.Dataset(files[-1]) as ds:
        precip_end = float((ds.variables["rainc"][0, :] + ds.variables["rainnc"][0, :])[amz_idx].mean())
    lhf = {lat_t: 0. for lat_t in LATITUDES}
    n = 0
    for f in files:
        with nc.Dataset(f) as ds:
            qv = ds.variables["qv"][0, :, :]
            v = ds.variables["uReconstructMeridional"][0, :, :]
            press = ds.variables["pressure"][0, :, :]
        dp = -np.diff(press, axis=1)
        for lat_t in LATITUDES:
            idx = band_idx[lat_t]
            H = LV * np.sum(qv[idx, :-1] * v[idx, :-1] * dp[idx] / G, axis=1)
            lhf[lat_t] += np.sum(A_band[lat_t] * H) / dy_band
        n += 1
    return precip_end, {k: v / n / 1e12 for k, v in lhf.items()}


print("Gathering ensemble data...")
results = {}
for y in YEARS:
    print(f"  {y}...")
    s, n = process(y, "salt"), process(y, "nosalt")
    results[y] = {"salt_p": s[0], "nosalt_p": n[0], "salt_lhf": s[1], "nosalt_lhf": n[1]}
np.savez(f"{OUT_DIR}/v4_ensemble_data.npz", results=results, years=YEARS, latitudes=LATITUDES)

# Figure 1: per-year ΔLHF at 30°N, 50°N, 70°N
print("\nFigure 1...")
fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
for ax, lat_t in zip(axes, [30, 50, 70]):
    deltas = [results[y]["salt_lhf"][lat_t] - results[y]["nosalt_lhf"][lat_t] for y in YEARS]
    colors = ["tab:red" if d < 0 else "tab:blue" for d in deltas]
    ax.bar(range(len(YEARS)), deltas, color=colors, edgecolor="black", linewidth=0.7)
    ax.set_xticks(range(len(YEARS)))
    ax.set_xticklabels([str(y) for y in YEARS])
    ax.axhline(0, color="black", lw=1)
    ax.set_title(f"{lat_t}°N northward latent heat transport")
    ax.set_ylabel("ΔLHF (SALT − NOSALT, TW)")
    ax.set_xlabel("year")
    arr = np.array(deltas)
    t, p = stats.ttest_1samp(arr, 0)
    sig = "p < 0.01 ✓✓" if p < 0.01 else ("p < 0.05 ✓" if p < 0.05 else ("p < 0.10 (marg)" if p < 0.10 else "n.s."))
    txt = f"mean = {arr.mean():+.1f} ± {arr.std(ddof=1):.1f} TW\nt = {t:+.2f},  p = {p:.4f}\n{sig}"
    ax.text(0.5, 0.97, txt, transform=ax.transAxes, ha="center", va="top",
            fontsize=10, family="monospace",
            bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="gray", alpha=0.85))
fig.suptitle("v4 5-pair ensemble — ΔLHF (SALT − NOSALT) by year", fontsize=13, weight="bold")
fig.tight_layout()
fig.savefig(f"{OUT_DIR}/fig1_per_year_dLHF.png", dpi=300)
plt.close(fig)

# Figure 2: meridional profile
print("Figure 2...")
fig, ax = plt.subplots(figsize=(9, 5.5))
all_deltas = []
for y in YEARS:
    deltas = [results[y]["salt_lhf"][lt] - results[y]["nosalt_lhf"][lt] for lt in LATITUDES]
    all_deltas.append(deltas)
    ax.plot(LATITUDES, deltas, "o-", alpha=0.4, lw=1, label=str(y))
all_deltas = np.array(all_deltas)
mp = all_deltas.mean(axis=0)
sp = all_deltas.std(axis=0, ddof=1)
ax.plot(LATITUDES, mp, "k-o", lw=2.5, ms=7, label="ensemble mean")
ax.fill_between(LATITUDES, mp - sp, mp + sp, color="black", alpha=0.15, label="±1σ")
ax.axhline(0, color="black", lw=0.8)
ax.axvline(0, color="black", lw=0.8, ls="--", alpha=0.5)
ax.set_xlabel("Latitude (°)")
ax.set_ylabel("Δ northward LHF (TW)")
ax.set_title("Meridional profile of ΔLHF (5-pair ensemble mean ± 1σ)")
ax.legend(loc="best", ncol=2, fontsize=9)
fig.tight_layout()
fig.savefig(f"{OUT_DIR}/fig2_meridional_dLHF.png", dpi=300)
plt.close(fig)

# Figure 3: Amazon ΔP per year
print("Figure 3...")
fig, ax = plt.subplots(figsize=(8, 5))
deltas_p = [results[y]["salt_p"] - results[y]["nosalt_p"] for y in YEARS]
colors = ["tab:blue" if d > 0 else "tab:red" for d in deltas_p]
ax.bar(range(len(YEARS)), deltas_p, color=colors, edgecolor="black", linewidth=0.7)
ax.axhline(0, color="black", lw=1)
ax.set_xticks(range(len(YEARS)))
ax.set_xticklabels([str(y) for y in YEARS])
ax.set_xlabel("year")
ax.set_ylabel("Amazon mean ΔP (SALT − NOSALT, mm/30-day)")
arr = np.array(deltas_p)
t, p = stats.ttest_1samp(arr, 0)
ax.set_title(f"Amazon mean ΔP per year — N=5 ensemble\n"
             f"mean = {arr.mean():+.2f} ± {arr.std(ddof=1):.2f} mm,  t = {t:+.2f},  p = {p:.3f}  (not significant)")
fig.tight_layout()
fig.savefig(f"{OUT_DIR}/fig3_amazon_dP.png", dpi=300)
plt.close(fig)

# Figure 4: sign-consistency summary
print("Figure 4...")
metrics = {
    "30°N ΔLHF": [results[y]["salt_lhf"][30] - results[y]["nosalt_lhf"][30] for y in YEARS],
    "50°N ΔLHF": [results[y]["salt_lhf"][50] - results[y]["nosalt_lhf"][50] for y in YEARS],
    "70°N ΔLHF": [results[y]["salt_lhf"][70] - results[y]["nosalt_lhf"][70] for y in YEARS],
    "Amazon ΔP": [results[y]["salt_p"] - results[y]["nosalt_p"] for y in YEARS],
}
fig, axes = plt.subplots(1, 2, figsize=(13, 4.5))
ax = axes[0]
labels = list(metrics.keys())
pos_counts = [sum(1 for d in deltas if d > 0) for deltas in metrics.values()]
neg_counts = [sum(1 for d in deltas if d < 0) for deltas in metrics.values()]
x = np.arange(len(labels))
ax.bar(x - 0.2, pos_counts, 0.4, color="tab:blue", label="positive")
ax.bar(x + 0.2, neg_counts, 0.4, color="tab:red", label="negative")
ax.set_xticks(x); ax.set_xticklabels(labels, rotation=10)
ax.set_ylabel("number of pairs (out of 5)")
ax.set_yticks(range(6))
ax.set_title("Sign consistency across 5-pair ensemble")
ax.legend(loc="upper right")
for i, (p_, n_) in enumerate(zip(pos_counts, neg_counts)):
    ax.text(i - 0.2, p_ + 0.05, str(p_), ha="center", fontsize=10, weight="bold")
    ax.text(i + 0.2, n_ + 0.05, str(n_), ha="center", fontsize=10, weight="bold")
ax = axes[1]; ax.axis("off")
table_data = []
for label, deltas in metrics.items():
    arr = np.array(deltas)
    t, p = stats.ttest_1samp(arr, 0)
    sig = ("p<0.01 ✓✓" if p < 0.01 else "p<0.05 ✓" if p < 0.05 else
           "p<0.10 marg" if p < 0.10 else "n.s.")
    units = "TW" if "LHF" in label else "mm/30d"
    table_data.append([label, f"{arr.mean():+.2f}", f"{arr.std(ddof=1):.2f}", units, f"{t:+.2f}", f"{p:.4f}", sig])
table = ax.table(cellText=table_data,
                 colLabels=["metric", "mean", "std", "units", "t", "p", "significance"],
                 loc="center", cellLoc="center")
table.auto_set_font_size(False); table.set_fontsize(10); table.scale(1, 1.5)
ax.set_title("Statistical summary  (one-sample t-test against zero, N=5)")
fig.tight_layout()
fig.savefig(f"{OUT_DIR}/fig4_sign_consistency.png", dpi=300)
plt.close(fig)

# Summary text
with open(f"{OUT_DIR}/v4_ensemble_summary.txt", "w") as fh:
    fh.write("=" * 70 + "\nv4 5-pair ensemble (120 km Pohlker l=4) — summary\n" + "=" * 70 + "\n\n")
    fh.write("Per-year:\n")
    fh.write(f"  {'Year':<6s} {'AmzΔP':>8s} {'30°N':>8s} {'50°N':>8s} {'70°N':>8s}\n")
    for y in YEARS:
        r = results[y]
        fh.write(f"  {y:<6d} "
                 f"{r['salt_p']-r['nosalt_p']:>+8.2f} "
                 f"{r['salt_lhf'][30]-r['nosalt_lhf'][30]:>+8.1f} "
                 f"{r['salt_lhf'][50]-r['nosalt_lhf'][50]:>+8.1f} "
                 f"{r['salt_lhf'][70]-r['nosalt_lhf'][70]:>+8.1f}\n")
    fh.write("\nEnsemble stats (one-sample t-test):\n")
    for label, deltas in metrics.items():
        arr = np.array(deltas); t, p = stats.ttest_1samp(arr, 0)
        sig = ("p<0.01" if p < 0.01 else "p<0.05" if p < 0.05 else "p<0.10" if p < 0.10 else "n.s.")
        fh.write(f"  {label:<14s} mean={arr.mean():+8.2f}  std={arr.std(ddof=1):>6.2f}  "
                 f"t={t:+6.2f}  p={p:.4f}  {sig}\n")

print(f"\n=== All figures saved to {OUT_DIR} ===")
for f in sorted(os.listdir(OUT_DIR)):
    sz = os.path.getsize(f"{OUT_DIR}/{f}")
    print(f"  {f}  ({sz/1024:.1f} KB)")
