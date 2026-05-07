#!/usr/bin/env python3
"""
BL preservation diagnostic for the 240 km l=4 Pohlker pristine SALT run
WITH the prescribed-CCN patch applied.

Compares directly against bl_preservation_240km.py (pre-patch baseline).
Pass criterion for the patch: cloud-base nwfa (lev 5-8) stays within
±5% of init pristine value (~118/cm³) throughout the 30-day run.

Outputs:
  /host/mpas_analysis/bl_preservation_240km_prescribed_ccn.txt
  /host/mpas_analysis/bl_preservation_240km_prescribed_ccn.png
"""
import os
import glob
import numpy as np
import netCDF4 as nc

INIT_PRISTINE = "/opt/jan_5yr_pristine/x1.10242.init.2022.pristine.nc"
RUN_DIR = "/host/GITIGNORE/simulation_outputs/results_240km_jan_l4_2022_prescribed_ccn_salt"
STATIC = "/opt/x1.10242/x1.10242.static.nc"
OUT_TXT = "/host/mpas_analysis/bl_preservation_240km_prescribed_ccn.txt"
OUT_PNG = "/host/mpas_analysis/bl_preservation_240km_prescribed_ccn.png"

# Same level bands as bl_preservation_240km.py for direct comparability.
LEVEL_BANDS = {
    "surface (lev 0)":     slice(0, 1),
    "low-BL (lev 1-4)":    slice(1, 5),
    "cloud-base (lev 5-8)": slice(5, 9),
    "mid-BL/FT (lev 9-12)": slice(9, 13),
}

PASS_TOLERANCE = 0.05  # ±5% of init for cloud-base; pass criterion

print("Loading mesh + IGBP-2 mask...")
with nc.Dataset(STATIC) as ds:
    _ivg = ds.variables["ivgtyp"][:]
    ivgtyp = _ivg[0] if _ivg.ndim == 2 else _ivg

with nc.Dataset(INIT_PRISTINE) as ds:
    lat = np.degrees(ds.variables["latCell"][:])
    lon = np.degrees(ds.variables["lonCell"][:])
    lon = np.where(lon > 180, lon - 360, lon)
    cellsOnCell = ds.variables["cellsOnCell"][:]
    nEdgesOnCell = ds.variables["nEdgesOnCell"][:]
    zgrid = ds.variables["zgrid"][:, :]
    nwfa_init = ds.variables["nwfa"][0, :, :]

amz = (ivgtyp == 2) & (lat > -15) & (lat < 5) & (lon > -75) & (lon < -50)
amz_idx = np.where(amz)[0]
amz_set = set(amz_idx.tolist())

def all_neighbors(c, depth):
    visited = {int(c)}
    frontier = {int(c)}
    for _ in range(depth):
        new_frontier = set()
        for x in frontier:
            n = nEdgesOnCell[x]
            for nb in cellsOnCell[x, :n] - 1:
                if nb >= 0 and int(nb) not in visited:
                    new_frontier.add(int(nb))
        visited |= new_frontier
        frontier = new_frontier
    return visited

interior = []
for c in amz_idx:
    if all_neighbors(c, 1) <= amz_set:
        interior.append(int(c))
interior = np.array(interior, dtype=int)
print(f"Amazon IGBP-2 deep-interior cells (depth=1): {len(interior)}")

zg_int = zgrid[interior, :]
z_mid = 0.5 * (zg_int[:, :-1] + zg_int[:, 1:])
rho = 1.15 * np.exp(-z_mid / 8000.0)

def band_mean_per_cm3(nwfa3d, band):
    sub = nwfa3d[interior, band] * rho[:, band] * 1e-6
    return float(np.mean(sub))

# Init reference values (note: SALT prescribed-CCN doubles nwfa over IGBP-2,
# so init_saved_salt = 2 * pristine init for these cells)
print()
print("Init pristine band means (raw pristine init, before SALT 2x perturbation):")
for name, sl in LEVEL_BANDS.items():
    val = band_mean_per_cm3(nwfa_init, sl)
    print(f"  {name:24s} {val:8.1f} /cm³")

print()
print("Expected SALT-init band means (2x pristine over IGBP-2):")
init_salt_band = {}
for name, sl in LEVEL_BANDS.items():
    val = band_mean_per_cm3(nwfa_init, sl) * 2.0  # SALT 2x perturbation
    init_salt_band[name] = val
    print(f"  {name:24s} {val:8.1f} /cm³")

hist_files = sorted(glob.glob(os.path.join(RUN_DIR, "history.*.nc")))
daily = [f for f in hist_files if "_00.00.00.nc" in f]
print(f"\nSampling {len(daily)} daily history files from {RUN_DIR}")

records = []
for f in daily:
    date = os.path.basename(f).split(".")[1]
    with nc.Dataset(f) as ds:
        nwfa3d = ds.variables["nwfa"][0, :, :]
    row = {"date": date}
    for name, sl in LEVEL_BANDS.items():
        row[name] = band_mean_per_cm3(nwfa3d, sl)
    records.append(row)

# Tabulate
header = f"{'date':<18}" + "".join(f"{name:>22s}" for name in LEVEL_BANDS)
lines = [header, "-" * len(header)]
for r in records:
    line = f"{r['date']:<18}" + "".join(f"{r[name]:>22.2f}" for name in LEVEL_BANDS)
    lines.append(line)

txt = "\n".join(lines)
print()
print(txt)

# Pass criterion: cloud-base (lev 5-8) within ±5% of init SALT value (2x pristine = ~235/cc)
cb_target = init_salt_band["cloud-base (lev 5-8)"]
cb_values = np.array([r["cloud-base (lev 5-8)"] for r in records])
cb_max_dev = np.max(np.abs(cb_values - cb_target) / cb_target) if cb_target > 0 else float("inf")
cb_pass = cb_max_dev <= PASS_TOLERANCE

# Surface (lev 0) check
surf_target = init_salt_band["surface (lev 0)"]
surf_values = np.array([r["surface (lev 0)"] for r in records])
surf_max_dev = np.max(np.abs(surf_values - surf_target) / surf_target) if surf_target > 0 else float("inf")

print()
print("=" * 72)
print(f"PASS CRITERION (cloud-base, lev 5-8): max |Δ|/init ≤ {PASS_TOLERANCE*100:.0f}%")
print(f"  init SALT target: {cb_target:.2f} /cm³")
print(f"  observed range:   {cb_values.min():.2f} to {cb_values.max():.2f} /cm³")
print(f"  max deviation:    {cb_max_dev*100:.2f}%")
print(f"  RESULT: {'PASS' if cb_pass else 'FAIL'}")
print()
print(f"Surface (lev 0): init target {surf_target:.2f}, range {surf_values.min():.2f}–{surf_values.max():.2f}, max dev {surf_max_dev*100:.2f}%")
print("=" * 72)

with open(OUT_TXT, "w") as fh:
    fh.write("BL preservation diagnostic, 240 km l=4 Pohlker pristine SALT, Jan 2022\n")
    fh.write("WITH PRESCRIBED-CCN PATCH (Heikenfeld 2019 ACP precedent)\n")
    fh.write(f"Amazon IGBP-2 deep-interior cells: {len(interior)}\n")
    fh.write(f"Init SALT band targets /cm³ (2x pristine over IGBP-2):\n")
    for name in LEVEL_BANDS:
        fh.write(f"  {name:24s} {init_salt_band[name]:8.1f}\n")
    fh.write("\n")
    fh.write(txt + "\n")
    fh.write("\n")
    fh.write(f"PASS CRITERION (cloud-base lev 5-8 within ±{PASS_TOLERANCE*100:.0f}% of init): {'PASS' if cb_pass else 'FAIL'}\n")
    fh.write(f"  max deviation: {cb_max_dev*100:.2f}%\n")
print(f"\nSaved: {OUT_TXT}")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    days = np.arange(len(records))
    fig, ax = plt.subplots(figsize=(11, 5.5))
    colors = {"surface (lev 0)": "tab:red", "low-BL (lev 1-4)": "tab:orange",
              "cloud-base (lev 5-8)": "tab:blue", "mid-BL/FT (lev 9-12)": "tab:green"}
    for name in LEVEL_BANDS:
        ax.plot(days, [r[name] for r in records], "-o", ms=3, color=colors[name], label=name)
        # Reference line at init target
        ax.axhline(init_salt_band[name], color=colors[name], ls=":", lw=0.6, alpha=0.7)
    ax.axhline(150, color="gray", ls="--", lw=0.8, label="Pohlker pristine (150 /cm³)")
    ax.axhline(11500, color="purple", ls=":", lw=0.8, label="Thompson ceiling (~11500 /cm³)")
    ax.set_yscale("log")
    ax.set_xlabel("simulation day")
    ax.set_ylabel("mean nwfa over Amazon interior IGBP-2 cells (/cm³)")
    title = "240 km l=4 Pohlker pristine SALT with PRESCRIBED-CCN PATCH"
    title += f"\nCloud-base (lev 5-8) max dev: {cb_max_dev*100:.2f}% — {'PASS' if cb_pass else 'FAIL'}"
    ax.set_title(title)
    ax.legend(loc="best", fontsize=9)
    ax.grid(True, which="both", alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=130)
    print(f"Saved: {OUT_PNG}")
except Exception as e:
    print(f"Plot failed: {e}")
