#!/usr/bin/env python3
"""
Step 5 — v5 July ensemble analysis.

Run INSIDE the container:
    docker exec mpas8 python3 /host_bundle/step5_analyze_july.py

Computes, for the 5-pair July prescribed-CCN ensemble:
  - per-year delta-LHF at 30 deg S, 30 deg N, 50 deg N, 70 deg N
  - meridional delta-LHF profile (ensemble mean +/- 1 sigma)
  - sign-consistency + one-sample t-tests
  - Amazon-mean delta-P
  - if the v4 January ensemble output is also present, a January-vs-July
    seasonal-comparison panel

v5 scientific focus: in July (NH-summer / SH-winter) the prediction is that
30 deg S becomes the statistically resolved signal (dominant SH-winter Hadley
cell), mirroring v4's resolved 30 deg N reduction in January.

Outputs land in /host/mpas_analysis/v5_figures/.
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

# === YEARS — keep in sync with the run steps ===
YEARS = [2021, 2022, 2023, 2024, 2025]
LATITUDES = [-70, -60, -50, -40, -30, -20, -10, 10, 20, 30, 40, 50, 60, 70, 80]

# July ensemble output (this v5 run, on the travel machine's /host disk)
JUL_TMPL = "/host/v5_july/simulation_outputs/results_120km_jul_pohlker_l4_{year}_prescribed_ccn_{phase}"
# January (v4) output — only present if you copied the v4 results onto this
# machine; the Jan-vs-July comparison panel is skipped gracefully if absent.
JAN_TMPL = "/host/v5_july/jan_v4_outputs/results_120km_jan_pohlker_l4_{year}_prescribed_ccn_{phase}"
OUT_DIR = "/host/v5_july/v5_figures"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams.update({
    "font.size": 11, "axes.labelsize": 11, "axes.titlesize": 12,
    "legend.fontsize": 9, "savefig.dpi": 300, "savefig.bbox": "tight",
    "axes.grid": True, "grid.alpha": 0.3,
})


def load_mesh():
    with nc.Dataset("/opt/x1.40962.static.nc") as ds:
        areaCell = ds.variables["areaCell"][:]
        ivg = ds.variables["ivgtyp"][:]
        if ivg.ndim == 2:
            ivg = ivg[0]
    # any history file gives lat/lon
    sample = None
    for y in YEARS:
        cand = sorted(glob.glob(JUL_TMPL.format(year=y, phase="salt") + "/history.*.nc"))
        if cand:
            sample = cand[0]
            break
    if sample is None:
        raise SystemExit("No July history files found — has Step 4 run?")
    with nc.Dataset(sample) as ds:
        lat = np.degrees(ds.variables["latCell"][:])
        lon = np.degrees(ds.variables["lonCell"][:])
        lon = np.where(lon > 180, lon - 360, lon)
    return areaCell, ivg, lat, lon


def process(folder, areaCell, band_idx, A_band, dy_band, amz_idx):
    """Return (amazon_precip_end, {lat: LHF_TW}) for one run folder."""
    files = sorted(glob.glob(folder + "/history.*.nc"))
    if not files:
        return None
    with nc.Dataset(files[-1]) as ds:
        precip_end = float((ds.variables["rainc"][0, :] + ds.variables["rainnc"][0, :])[amz_idx].mean())
    lhf = {lt: 0. for lt in LATITUDES}
    n = 0
    for f in files:
        with nc.Dataset(f) as ds:
            qv = ds.variables["qv"][0, :, :]
            v = ds.variables["uReconstructMeridional"][0, :, :]
            press = ds.variables["pressure"][0, :, :]
        dp = -np.diff(press, axis=1)
        for lt in LATITUDES:
            idx = band_idx[lt]
            H = LV * np.sum(qv[idx, :-1] * v[idx, :-1] * dp[idx] / G, axis=1)
            lhf[lt] += np.sum(A_band[lt] * H) / dy_band
        n += 1
    return precip_end, {k: v / n / 1e12 for k, v in lhf.items()}


def gather(tmpl, areaCell, ivg, lat, lon):
    """Gather an ensemble (jan or jul). Returns dict[year] -> result, or {} if absent."""
    amz_idx = np.where((lat > -15) & (lat < 5) & (lon > -75) & (lon < -50) & (ivg == 2))[0]
    band_idx = {lt: np.where((lat > lt - 2) & (lat < lt + 2))[0] for lt in LATITUDES}
    A_band = {lt: areaCell[idx] for lt, idx in band_idx.items()}
    dy_band = R_E * np.radians(4.)
    out = {}
    for y in YEARS:
        s = process(tmpl.format(year=y, phase="salt"), areaCell, band_idx, A_band, dy_band, amz_idx)
        n = process(tmpl.format(year=y, phase="nosalt"), areaCell, band_idx, A_band, dy_band, amz_idx)
        if s is None or n is None:
            continue
        out[y] = {"salt_p": s[0], "nosalt_p": n[0], "salt_lhf": s[1], "nosalt_lhf": n[1]}
    return out


def tstat(arr):
    a = np.array(arr, float)
    t, p = stats.ttest_1samp(a, 0)
    return a.mean(), a.std(ddof=1), t, p


def main():
    areaCell, ivg, lat, lon = load_mesh()
    print("Gathering July ensemble...")
    jul = gather(JUL_TMPL, areaCell, ivg, lat, lon)
    if not jul:
        raise SystemExit("No complete July pairs found.")
    yrs = sorted(jul.keys())
    print(f"  July pairs found: {yrs}")

    np.savez(f"{OUT_DIR}/v5_july_ensemble_data.npz", results=jul, years=yrs, latitudes=LATITUDES)

    # ---- Figure 1: per-year delta-LHF at 30S / 30N / 50N / 70N --------------
    focus = [-30, 30, 50, 70]
    fig, axes = plt.subplots(1, 4, figsize=(17, 4.5))
    for ax, lt in zip(axes, focus):
        deltas = [jul[y]["salt_lhf"][lt] - jul[y]["nosalt_lhf"][lt] for y in yrs]
        colors = ["tab:red" if d < 0 else "tab:blue" for d in deltas]
        ax.bar(range(len(yrs)), deltas, color=colors, edgecolor="black", linewidth=0.7)
        ax.set_xticks(range(len(yrs)))
        ax.set_xticklabels([str(y) for y in yrs])
        ax.axhline(0, color="black", lw=1)
        lbl = f"{abs(lt)}°{'S' if lt < 0 else 'N'}"
        ax.set_title(f"{lbl} northward latent heat transport")
        ax.set_ylabel("ΔLHF (SALT − NOSALT, TW)")
        ax.set_xlabel("July-start year")
        m, s, t, p = tstat(deltas)
        sig = "p<0.01 ✓✓" if p < 0.01 else "p<0.05 ✓" if p < 0.05 else "p<0.10 marg" if p < 0.10 else "n.s."
        ax.text(0.5, 0.97, f"mean={m:+.1f} ± {s:.1f} TW\nt={t:+.2f}, p={p:.4f}\n{sig}",
                transform=ax.transAxes, ha="center", va="top", fontsize=9, family="monospace",
                bbox=dict(boxstyle="round,pad=0.4", facecolor="white", edgecolor="gray", alpha=0.85))
    fig.suptitle("v5 July 5-pair ensemble — ΔLHF (SALT − NOSALT) by year",
                 fontsize=13, weight="bold")
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/v5_fig1_per_year_dLHF.png", dpi=300)
    plt.close(fig)
    print("  wrote v5_fig1_per_year_dLHF.png")

    # ---- Figure 2: meridional profile --------------------------------------
    fig, ax = plt.subplots(figsize=(9, 5.5))
    all_d = []
    for y in yrs:
        d = [jul[y]["salt_lhf"][lt] - jul[y]["nosalt_lhf"][lt] for lt in LATITUDES]
        all_d.append(d)
        ax.plot(LATITUDES, d, "o-", alpha=0.4, lw=1, label=str(y))
    all_d = np.array(all_d)
    mp, sp = all_d.mean(0), all_d.std(0, ddof=1)
    ax.plot(LATITUDES, mp, "k-o", lw=2.5, ms=7, label="ensemble mean")
    ax.fill_between(LATITUDES, mp - sp, mp + sp, color="black", alpha=0.15, label="±1σ")
    ax.axhline(0, color="black", lw=0.8)
    ax.axvline(0, color="black", lw=0.8, ls="--", alpha=0.5)
    ax.set_xlabel("Latitude (°)")
    ax.set_ylabel("Δ northward LHF (TW)")
    ax.set_title("v5 July ensemble — meridional ΔLHF profile (mean ± 1σ)")
    ax.legend(loc="best", ncol=2, fontsize=9)
    fig.tight_layout()
    fig.savefig(f"{OUT_DIR}/v5_fig2_meridional_dLHF.png", dpi=300)
    plt.close(fig)
    print("  wrote v5_fig2_meridional_dLHF.png")

    # ---- text summary ------------------------------------------------------
    metrics = {
        "30°S ΔLHF": [jul[y]["salt_lhf"][-30] - jul[y]["nosalt_lhf"][-30] for y in yrs],
        "30°N ΔLHF": [jul[y]["salt_lhf"][30] - jul[y]["nosalt_lhf"][30] for y in yrs],
        "50°N ΔLHF": [jul[y]["salt_lhf"][50] - jul[y]["nosalt_lhf"][50] for y in yrs],
        "70°N ΔLHF": [jul[y]["salt_lhf"][70] - jul[y]["nosalt_lhf"][70] for y in yrs],
        "Amazon ΔP": [jul[y]["salt_p"] - jul[y]["nosalt_p"] for y in yrs],
    }
    with open(f"{OUT_DIR}/v5_july_ensemble_summary.txt", "w") as fh:
        fh.write("=" * 70 + "\nv5 July 5-pair ensemble (120 km Pohlker l=4) - summary\n" + "=" * 70 + "\n\n")
        fh.write(f"Years: {yrs}\n\n")
        fh.write("Ensemble stats (one-sample t-test against zero):\n")
        for label, d in metrics.items():
            m, s, t, p = tstat(d)
            sig = "p<0.01" if p < 0.01 else "p<0.05" if p < 0.05 else "p<0.10" if p < 0.10 else "n.s."
            unit = "TW" if "LHF" in label else "mm/30d"
            fh.write(f"  {label:<14s} mean={m:+8.2f}  std={s:6.2f} {unit:8s} t={t:+6.2f}  p={p:.4f}  {sig}\n")
        fh.write("\nv5 prediction: 30S should be the statistically resolved metric in July\n")
        fh.write("(SH winter, dominant Hadley cell), mirroring v4's resolved 30N in January.\n")
    print("  wrote v5_july_ensemble_summary.txt")

    # ---- optional January-vs-July comparison -------------------------------
    print("Checking for v4 January ensemble output...")
    jan = gather(JAN_TMPL, areaCell, ivg, lat, lon)
    if jan:
        jy = sorted(jan.keys())
        print(f"  January pairs found: {jy} — building seasonal comparison")
        fig, ax = plt.subplots(figsize=(9, 5.5))
        for label, ens, yy, col in [("January (v4)", jan, jy, "tab:blue"),
                                    ("July (v5)", jul, yrs, "tab:red")]:
            allp = np.array([[ens[y]["salt_lhf"][lt] - ens[y]["nosalt_lhf"][lt]
                              for lt in LATITUDES] for y in yy])
            m, s = allp.mean(0), allp.std(0, ddof=1)
            ax.plot(LATITUDES, m, "-o", lw=2.5, ms=6, color=col, label=label + " mean")
            ax.fill_between(LATITUDES, m - s, m + s, color=col, alpha=0.15)
        ax.axhline(0, color="black", lw=0.8)
        ax.axvline(0, color="black", lw=0.8, ls="--", alpha=0.5)
        ax.set_xlabel("Latitude (°)")
        ax.set_ylabel("Δ northward LHF (TW)")
        ax.set_title("Seasonal comparison — January (v4) vs July (v5) ensemble ΔLHF")
        ax.legend(loc="best")
        fig.tight_layout()
        fig.savefig(f"{OUT_DIR}/v5_fig3_jan_vs_jul.png", dpi=300)
        plt.close(fig)
        print("  wrote v5_fig3_jan_vs_jul.png")
    else:
        print("  no January ensemble output on this machine — skipping comparison")
        print("  (copy the v4 results_120km_jan_* directories here to enable it)")

    print(f"\n=== v5 analysis complete. Outputs in {OUT_DIR} ===")
    for f in sorted(os.listdir(OUT_DIR)):
        print(f"  {f}")


if __name__ == "__main__":
    main()
