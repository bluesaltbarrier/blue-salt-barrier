#!/usr/bin/env python3
"""
Extended column diagnostic for the l=4 Pöhlker-Dg pair.

Produces three figures per invocation:
  (1) column_timemean_ens.png — N max-ΔP cells vs N min-ΔP cells inside a
      lat/lon box; each group plotted as median + 10-90 percentile band,
      SALT and NOSALT overlaid.
  (2) column_heat_budget.png  — per-level differential (SALT − NOSALT)
      latent-heat release and θ anomaly for the same two cell groups.
      (Uses Δqv and Δθ as microphysics diagnostics since explicit
      microphysics-tendency outputs are not in the default history stream.)
  (3) column_peak_snapshot.png — per-cell peak-rain-rate instantaneous
      snapshot, rather than 30-day mean, so the droplet-size / Re_drop
      story is not washed out by temporal averaging.

Example (inside the mpas8 Docker container with /d/WRF mounted at /host):
  python3 column_diag_ensemble_l4.py \\
    --salt-dir /host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_salt \\
    --nosalt-dir /host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_nosalt \\
    --dp-npz /host/mpas_analysis/l4_pair/deltaP_data.npz \\
    --out-dir /host/mpas_analysis/l4_pair
"""
import os, glob, argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from netCDF4 import Dataset

# --- physical constants ---
G = 9.81; Rd = 287.0; cp = 1004.0; Lv = 2.5e6
p0 = 1.0e5; RHO_W = 1000.0; MU_AIR = 1.8e-5

VARS_3D  = ["qv","qc","qr","qi","qs","nc","nr","ni",
            "theta","pressure","rho",
            "uReconstructZonal","uReconstructMeridional"]
VARS_3DI = ["w"]
VARS_2D  = ["lh","hfx","qfx","hpbl","u10","v10","t2m","q2","rainnc","rainc"]


# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(
        description="Ensemble column diagnostic (max/min ΔP cells inside a lat/lon box).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--salt-dir",   required=True,
                   help="Run directory containing SALT history files (history.*.nc)")
    p.add_argument("--nosalt-dir", required=True,
                   help="Run directory containing NOSALT history files")
    p.add_argument("--dp-npz",     required=True,
                   help="Path to deltaP_data.npz produced by analyze_pohlker_pair.py")
    p.add_argument("--out-dir",    required=True,
                   help="Output directory for figures and summary text")
    p.add_argument("--n-cells",    type=int, default=10,
                   help="Cells per ensemble group (top and bottom by ΔP). Default: 10")
    p.add_argument("--box-lat",    default="-15,5",
                   help="Latitude range of region of interest as 'min,max'. Default: -15,5 (Amazon)")
    p.add_argument("--box-lon",    default="-75,-50",
                   help="Longitude range of region of interest as 'min,max'. Default: -75,-50 (Amazon)")
    args = p.parse_args()
    args.box_lat = tuple(float(x) for x in args.box_lat.split(","))
    args.box_lon = tuple(float(x) for x in args.box_lon.split(","))
    os.makedirs(args.out_dir, exist_ok=True)
    return args


# ------------------------------------------------------------
# Cell selection
# ------------------------------------------------------------
def select_ensembles(args):
    d = np.load(args.dp_npz)
    lat = d["lat"]; lon = d["lon"]; dP = d["dP"]
    in_box = ((lat >= args.box_lat[0]) & (lat <= args.box_lat[1])
              & (lon >= args.box_lon[0]) & (lon <= args.box_lon[1]))
    idx_box = np.where(in_box)[0]
    dP_box = dP[idx_box]
    order = np.argsort(dP_box)
    bottom = idx_box[order[:args.n_cells]]
    top    = idx_box[order[-args.n_cells:][::-1]]
    return top, bottom, lat, lon, dP


# ------------------------------------------------------------
# Cached file list
# ------------------------------------------------------------
_FILES = {}
def files_for(run_dir):
    if run_dir not in _FILES:
        _FILES[run_dir] = sorted(glob.glob(os.path.join(run_dir, "history.*.nc")))
        if not _FILES[run_dir]:
            raise RuntimeError(f"No history.*.nc files found in {run_dir}")
    return _FILES[run_dir]


# ------------------------------------------------------------
# 30-day time-mean profiles
# ------------------------------------------------------------
def timemean_at_cells(run_dir, cell_indices):
    flist = files_for(run_dir)
    n = len(cell_indices); nvert = 55
    out3  = {v: np.zeros((n, nvert)) for v in VARS_3D}
    out3i = {v: np.zeros((n, nvert + 1)) for v in VARS_3DI}
    out2  = {v: np.zeros(n) for v in VARS_2D}
    ntime = 0
    for f in flist:
        with Dataset(f) as ds:
            for v in VARS_3D:
                out3[v] = out3[v] + ds.variables[v][0, cell_indices, :].astype(np.float64)
            for v in VARS_3DI:
                out3i[v] = out3i[v] + ds.variables[v][0, cell_indices, :].astype(np.float64)
            for v in VARS_2D:
                out2[v] = out2[v] + ds.variables[v][0, cell_indices].astype(np.float64)
        ntime += 1
    for d in (out3, out3i):
        for k in d: d[k] /= ntime
    for k in out2: out2[k] /= ntime
    return out3, out3i, out2, ntime


# ------------------------------------------------------------
# Peak-rain-rate snapshot
# ------------------------------------------------------------
def peak_snapshot_at_cells(run_dir, cell_indices):
    """For each cell, find the history file at which that cell's
    column-integrated qr is maximum; return the instantaneous snapshot
    profile at that time."""
    flist = files_for(run_dir)
    n = len(cell_indices); nvert = 55
    best_idx = np.full(n, -1, dtype=int)
    best_qr_col = np.full(n, -np.inf)
    # First pass: locate the file of peak column qr for each cell
    for fi, f in enumerate(flist):
        with Dataset(f) as ds:
            qr = ds.variables["qr"][0, cell_indices, :].astype(np.float64)
            rho = ds.variables["rho"][0, cell_indices, :].astype(np.float64)
            zgrid = ds.variables["zgrid"][cell_indices, :].astype(np.float64)
            dz = np.diff(zgrid, axis=1)
            qr_col = np.sum(qr * rho * dz, axis=1)
        for j in range(n):
            if qr_col[j] > best_qr_col[j]:
                best_qr_col[j] = qr_col[j]
                best_idx[j] = fi
    # Second pass: gather profiles at the selected times
    out3  = {v: np.zeros((n, nvert)) for v in VARS_3D}
    out3i = {v: np.zeros((n, nvert + 1)) for v in VARS_3DI}
    out2  = {v: np.zeros(n) for v in VARS_2D}
    groups = {}
    for j, fi in enumerate(best_idx):
        groups.setdefault(int(fi), []).append(j)
    for fi, jlist in groups.items():
        cells = cell_indices[jlist]
        with Dataset(flist[fi]) as ds:
            for v in VARS_3D:
                out3[v][jlist] = ds.variables[v][0, cells, :].astype(np.float64)
            for v in VARS_3DI:
                out3i[v][jlist] = ds.variables[v][0, cells, :].astype(np.float64)
            for v in VARS_2D:
                out2[v][jlist] = ds.variables[v][0, cells].astype(np.float64)
    return out3, out3i, out2, best_idx, best_qr_col


# ------------------------------------------------------------
# Derived fields
# ------------------------------------------------------------
def derive(p3, p3i, z_mid):
    p  = p3["pressure"]; theta = p3["theta"]; rho = p3["rho"]
    qv = p3["qv"];       u = p3["uReconstructZonal"];  v = p3["uReconstructMeridional"]
    w_iface = p3i["w"]
    w_mid = 0.5 * (w_iface[:, :-1] + w_iface[:, 1:])

    exner = (p / p0) ** (Rd / cp)
    T = theta * exner

    dtheta_dz = np.gradient(theta, axis=1) / np.gradient(z_mid, axis=1)
    Nsq = (G / theta) * dtheta_dz
    du_dz = np.gradient(u, axis=1) / np.gradient(z_mid, axis=1)
    dv_dz = np.gradient(v, axis=1) / np.gradient(z_mid, axis=1)
    shear = np.sqrt(du_dz**2 + dv_dz**2)
    with np.errstate(divide="ignore", invalid="ignore"):
        Ri = np.where(shear > 1e-6, Nsq / (shear**2), np.nan)

    qc = np.maximum(p3["qc"], 1e-20); nc = np.maximum(p3["nc"], 1e-20)
    qr = np.maximum(p3["qr"], 1e-20); nr = np.maximum(p3["nr"], 1e-20)
    Dc = (6.0 * qc / (np.pi * RHO_W * nc)) ** (1.0 / 3.0)
    Dr = (6.0 * qr / (np.pi * RHO_W * nr)) ** (1.0 / 3.0)
    Dc = np.where(p3["qc"] > 1e-8, Dc, np.nan)
    Dr = np.where(p3["qr"] > 1e-8, Dr, np.nan)

    v_stk_c = (RHO_W * G * Dc**2) / (18.0 * MU_AIR)
    Rec = rho * Dc * v_stk_c / MU_AIR
    v_stk_r = (RHO_W * G * Dr**2) / (18.0 * MU_AIR)
    Rer = rho * Dr * v_stk_r / MU_AIR

    return dict(T=T, Ri=Ri, shear=shear, Nsq=Nsq,
                Dc=Dc, Dr=Dr, Rec=Rec, Rer=Rer, w_mid=w_mid,
                qc=p3["qc"], qr=p3["qr"], qv=p3["qv"],
                theta=p3["theta"], rho=p3["rho"],
                dtheta_dz=dtheta_dz)


def get_z(args, cell_indices):
    with Dataset(files_for(args.salt_dir)[0]) as ds:
        zg = ds.variables["zgrid"][cell_indices, :].astype(np.float64)
    z_mid = 0.5 * (zg[:, :-1] + zg[:, 1:])
    return z_mid, zg


# ------------------------------------------------------------
# Plotting helpers
# ------------------------------------------------------------
def band(ax, z, data, color, label, linestyle="-"):
    data = np.asarray(np.ma.getdata(data), dtype=np.float64)
    z    = np.asarray(np.ma.getdata(z),    dtype=np.float64)
    with np.errstate(all="ignore"):
        med = np.nanmedian(data, axis=0)
        q10 = np.nanpercentile(data, 10, axis=0)
        q90 = np.nanpercentile(data, 90, axis=0)
    z_km = np.nanmedian(z, axis=0) / 1000.0
    ax.fill_betweenx(z_km, q10, q90, color=color, alpha=0.15, linewidth=0)
    ax.plot(med, z_km, color=color, linewidth=1.6, linestyle=linestyle, label=label)


def finish(ax, xlabel, title, logx=False, xlim=None, ymax=20):
    ax.set_xlabel(xlabel); ax.set_ylabel("Altitude (km)")
    ax.set_title(title, fontsize=10); ax.grid(alpha=0.3)
    if logx: ax.set_xscale("log")
    if xlim is not None: ax.set_xlim(xlim)
    ax.set_ylim(0, ymax)
    ax.legend(fontsize=7, loc="best")


# ------------------------------------------------------------
# Figures
# ------------------------------------------------------------
def fig_timemean_ensemble(args, top_idx, bot_idx, lat, lon, dP):
    print("\nTime-mean ensemble figure...")
    print(f"  top-{args.n_cells} mean ΔP = {dP[top_idx].mean():+.2f} mm   "
          f"range [{dP[top_idx].min():+.2f}, {dP[top_idx].max():+.2f}]")
    print(f"  bot-{args.n_cells} mean ΔP = {dP[bot_idx].mean():+.2f} mm   "
          f"range [{dP[bot_idx].min():+.2f}, {dP[bot_idx].max():+.2f}]")

    z_t, _ = get_z(args, top_idx); z_b, _ = get_z(args, bot_idx)

    top_s3, top_s3i, top_s2, nt = timemean_at_cells(args.salt_dir,   top_idx)
    top_n3, top_n3i, top_n2, _  = timemean_at_cells(args.nosalt_dir, top_idx)
    bot_s3, bot_s3i, bot_s2, _  = timemean_at_cells(args.salt_dir,   bot_idx)
    bot_n3, bot_n3i, bot_n2, _  = timemean_at_cells(args.nosalt_dir, bot_idx)
    print(f"  averaged over {nt} snapshots per cell per run")

    Dts = derive(top_s3, top_s3i, z_t); Dtn = derive(top_n3, top_n3i, z_t)
    Dbs = derive(bot_s3, bot_s3i, z_b); Dbn = derive(bot_n3, bot_n3i, z_b)

    col_max = "#c0392b"; col_min = "#2874a6"
    fig, axs = plt.subplots(3, 2, figsize=(12, 14))

    band(axs[0,0], z_t, Dts["qc"]*1000, col_max, "max-ΔP SALT")
    band(axs[0,0], z_t, Dtn["qc"]*1000, col_max, "max-ΔP NOSALT", linestyle="--")
    band(axs[0,0], z_b, Dbs["qc"]*1000, col_min, "min-ΔP SALT")
    band(axs[0,0], z_b, Dbn["qc"]*1000, col_min, "min-ΔP NOSALT", linestyle="--")
    finish(axs[0,0], "Cloud water qc (g/kg)", "(a) Cloud-water profile")

    band(axs[0,1], z_t, np.maximum(Dts["qr"]*1000,1e-8), col_max, "max-ΔP SALT")
    band(axs[0,1], z_t, np.maximum(Dtn["qr"]*1000,1e-8), col_max, "max-ΔP NOSALT", linestyle="--")
    band(axs[0,1], z_b, np.maximum(Dbs["qr"]*1000,1e-8), col_min, "min-ΔP SALT")
    band(axs[0,1], z_b, np.maximum(Dbn["qr"]*1000,1e-8), col_min, "min-ΔP NOSALT", linestyle="--")
    finish(axs[0,1], "Rain qr (g/kg, log)", "(b) Rain mass", logx=True, xlim=(1e-6, 1e-1))

    band(axs[1,0], z_t, Dts["w_mid"], col_max, "max-ΔP SALT")
    band(axs[1,0], z_t, Dtn["w_mid"], col_max, "max-ΔP NOSALT", linestyle="--")
    band(axs[1,0], z_b, Dbs["w_mid"], col_min, "min-ΔP SALT")
    band(axs[1,0], z_b, Dbn["w_mid"], col_min, "min-ΔP NOSALT", linestyle="--")
    finish(axs[1,0], "Vertical velocity w (m/s)", "(c) Vertical velocity")

    band(axs[1,1], z_t, Dts["Dc"]*1e6, col_max, "max-ΔP SALT")
    band(axs[1,1], z_t, Dtn["Dc"]*1e6, col_max, "max-ΔP NOSALT", linestyle="--")
    band(axs[1,1], z_b, Dbs["Dc"]*1e6, col_min, "min-ΔP SALT")
    band(axs[1,1], z_b, Dbn["Dc"]*1e6, col_min, "min-ΔP NOSALT", linestyle="--")
    finish(axs[1,1], "Cloud-drop Dc (µm)", "(d) Cloud-drop volume diameter")

    def clipRi(a): return np.clip(a, -2, 5)
    band(axs[2,0], z_t, clipRi(Dts["Ri"]), col_max, "max-ΔP SALT")
    band(axs[2,0], z_t, clipRi(Dtn["Ri"]), col_max, "max-ΔP NOSALT", linestyle="--")
    band(axs[2,0], z_b, clipRi(Dbs["Ri"]), col_min, "min-ΔP SALT")
    band(axs[2,0], z_b, clipRi(Dbn["Ri"]), col_min, "min-ΔP NOSALT", linestyle="--")
    axs[2,0].axvline(0.25, color="gray", linestyle=":", linewidth=0.8)
    finish(axs[2,0], "Bulk Richardson number (clipped)", "(e) Ri: Ri<0.25 turbulent")

    band(axs[2,1], z_t, np.maximum(Dts["Rec"],1e-6), col_max, "max-ΔP SALT")
    band(axs[2,1], z_t, np.maximum(Dtn["Rec"],1e-6), col_max, "max-ΔP NOSALT", linestyle="--")
    band(axs[2,1], z_b, np.maximum(Dbs["Rec"],1e-6), col_min, "min-ΔP SALT")
    band(axs[2,1], z_b, np.maximum(Dbn["Rec"],1e-6), col_min, "min-ΔP NOSALT", linestyle="--")
    axs[2,1].axvline(1.0, color="gray", linestyle=":", linewidth=0.8)
    finish(axs[2,1], "Cloud-drop Re_d (log)", "(f) Droplet Reynolds number", logx=True, xlim=(1e-4, 1e3))

    fig.suptitle(
        f"Pöhlker-Dg pair — {args.n_cells}+{args.n_cells} ensemble time-mean "
        f"(top median ΔP={np.median(dP[top_idx]):+.1f} mm, "
        f"bot median ΔP={np.median(dP[bot_idx]):+.1f} mm); band = 10-90 pctile",
        fontsize=12, fontweight="bold", y=0.995)
    plt.subplots_adjust(left=0.07, right=0.97, top=0.94,
                        bottom=0.04, wspace=0.22, hspace=0.32)
    out = os.path.join(args.out_dir, "column_timemean_ens.png")
    plt.savefig(out, dpi=140, facecolor="white"); plt.close()
    print(f"  wrote {out}")

    return dict(z_t=z_t, z_b=z_b,
                Dts=Dts, Dtn=Dtn, Dbs=Dbs, Dbn=Dbn,
                top_s2=top_s2, top_n2=top_n2,
                bot_s2=bot_s2, bot_n2=bot_n2,
                top_s3=top_s3, top_n3=top_n3,
                bot_s3=bot_s3, bot_n3=bot_n3)


def fig_heat_budget(args, B, top_idx, bot_idx, dP):
    print("\nHeat-budget figure...")
    z_t = B["z_t"]; z_b = B["z_b"]
    Dts = B["Dts"]; Dtn = B["Dtn"]; Dbs = B["Dbs"]; Dbn = B["Dbn"]

    dqv_top = (Dtn["qv"] - Dts["qv"]) * Dts["rho"] * Lv
    dqv_bot = (Dbn["qv"] - Dbs["qv"]) * Dbs["rho"] * Lv
    dH_top  = (Dts["T"]  - Dtn["T"])  * Dts["rho"] * cp
    dH_bot  = (Dbs["T"]  - Dbn["T"])  * Dbs["rho"] * cp

    col_max = "#c0392b"; col_min = "#2874a6"
    fig, axs = plt.subplots(1, 2, figsize=(12, 7))

    band(axs[0], z_t, dqv_top, col_max, "max-ΔP cells")
    band(axs[0], z_b, dqv_bot, col_min, "min-ΔP cells")
    axs[0].axvline(0, color="gray", linestyle=":", linewidth=0.8)
    finish(axs[0], "(qv_NOSALT − qv_SALT)·ρ·Lv   [J/m^3 over 30 d]",
           "(a) Differential latent heat released by SALT\n(positive = more condensation in SALT)")

    band(axs[1], z_t, dH_top, col_max, "max-ΔP cells")
    band(axs[1], z_b, dH_bot, col_min, "min-ΔP cells")
    axs[1].axvline(0, color="gray", linestyle=":", linewidth=0.8)
    finish(axs[1], "(T_SALT − T_NOSALT)·ρ·cp   [J/m^3 over 30 d]",
           "(b) Thermal anomaly density from θ\n(positive = layer warmer in SALT)")

    fig.suptitle(
        f"Pöhlker-Dg pair — per-level microphysics-driven heat budget\n"
        f"(SALT − NOSALT differentials, median + 10-90 pctile band over {args.n_cells} cells)",
        fontsize=12, fontweight="bold", y=0.995)
    plt.subplots_adjust(left=0.08, right=0.97, top=0.88,
                        bottom=0.08, wspace=0.25)
    out = os.path.join(args.out_dir, "column_heat_budget.png")
    plt.savefig(out, dpi=140, facecolor="white"); plt.close()
    print(f"  wrote {out}")


def fig_peak_snapshot(args, top_idx, bot_idx, lat, lon, dP):
    print("\nPeak-qr snapshot figure...")
    z_t, _ = get_z(args, top_idx); z_b, _ = get_z(args, bot_idx)

    top_s3, top_s3i, _, _, top_s_qrc = peak_snapshot_at_cells(args.salt_dir,   top_idx)
    top_n3, top_n3i, _, _, _         = peak_snapshot_at_cells(args.nosalt_dir, top_idx)
    bot_s3, bot_s3i, _, _, bot_s_qrc = peak_snapshot_at_cells(args.salt_dir,   bot_idx)
    bot_n3, bot_n3i, _, _, _         = peak_snapshot_at_cells(args.nosalt_dir, bot_idx)
    print(f"  max-ΔP cells: median peak column qr (SALT) = {np.median(top_s_qrc):.4f} kg/m^2")
    print(f"  min-ΔP cells: median peak column qr (SALT) = {np.median(bot_s_qrc):.4f} kg/m^2")

    Dts = derive(top_s3, top_s3i, z_t); Dtn = derive(top_n3, top_n3i, z_t)
    Dbs = derive(bot_s3, bot_s3i, z_b); Dbn = derive(bot_n3, bot_n3i, z_b)

    col_max = "#c0392b"; col_min = "#2874a6"
    fig, axs = plt.subplots(3, 2, figsize=(12, 14))

    band(axs[0,0], z_t, Dts["qc"]*1000, col_max, "max-ΔP SALT")
    band(axs[0,0], z_t, Dtn["qc"]*1000, col_max, "max-ΔP NOSALT", linestyle="--")
    band(axs[0,0], z_b, Dbs["qc"]*1000, col_min, "min-ΔP SALT")
    band(axs[0,0], z_b, Dbn["qc"]*1000, col_min, "min-ΔP NOSALT", linestyle="--")
    finish(axs[0,0], "Cloud water qc (g/kg)", "(a) qc at peak-qr snapshot")

    band(axs[0,1], z_t, np.maximum(Dts["qr"]*1000,1e-8), col_max, "max-ΔP SALT")
    band(axs[0,1], z_t, np.maximum(Dtn["qr"]*1000,1e-8), col_max, "max-ΔP NOSALT", linestyle="--")
    band(axs[0,1], z_b, np.maximum(Dbs["qr"]*1000,1e-8), col_min, "min-ΔP SALT")
    band(axs[0,1], z_b, np.maximum(Dbn["qr"]*1000,1e-8), col_min, "min-ΔP NOSALT", linestyle="--")
    finish(axs[0,1], "Rain qr (g/kg, log)", "(b) Rain at peak-qr snapshot", logx=True, xlim=(1e-6, 1e-1))

    band(axs[1,0], z_t, Dts["w_mid"], col_max, "max-ΔP SALT")
    band(axs[1,0], z_t, Dtn["w_mid"], col_max, "max-ΔP NOSALT", linestyle="--")
    band(axs[1,0], z_b, Dbs["w_mid"], col_min, "min-ΔP SALT")
    band(axs[1,0], z_b, Dbn["w_mid"], col_min, "min-ΔP NOSALT", linestyle="--")
    finish(axs[1,0], "w (m/s)", "(c) Vertical velocity (snapshot)")

    band(axs[1,1], z_t, Dts["Dc"]*1e6, col_max, "max-ΔP SALT")
    band(axs[1,1], z_t, Dtn["Dc"]*1e6, col_max, "max-ΔP NOSALT", linestyle="--")
    band(axs[1,1], z_b, Dbs["Dc"]*1e6, col_min, "min-ΔP SALT")
    band(axs[1,1], z_b, Dbn["Dc"]*1e6, col_min, "min-ΔP NOSALT", linestyle="--")
    finish(axs[1,1], "Dc (µm)", "(d) Cloud-drop volume diameter (snapshot)")

    band(axs[2,0], z_t, Dts["Dr"]*1e6, col_max, "max-ΔP SALT")
    band(axs[2,0], z_t, Dtn["Dr"]*1e6, col_max, "max-ΔP NOSALT", linestyle="--")
    band(axs[2,0], z_b, Dbs["Dr"]*1e6, col_min, "min-ΔP SALT")
    band(axs[2,0], z_b, Dbn["Dr"]*1e6, col_min, "min-ΔP NOSALT", linestyle="--")
    finish(axs[2,0], "Rain-drop Dr (µm)", "(e) Rain-drop volume diameter (snapshot)")

    band(axs[2,1], z_t, np.maximum(Dts["Rer"], 1e-4), col_max, "max-ΔP SALT")
    band(axs[2,1], z_t, np.maximum(Dtn["Rer"], 1e-4), col_max, "max-ΔP NOSALT", linestyle="--")
    band(axs[2,1], z_b, np.maximum(Dbs["Rer"], 1e-4), col_min, "min-ΔP SALT")
    band(axs[2,1], z_b, np.maximum(Dbn["Rer"], 1e-4), col_min, "min-ΔP NOSALT", linestyle="--")
    axs[2,1].axvline(1.0, color="gray", linestyle=":", linewidth=0.8)
    finish(axs[2,1], "Rain-drop Re_d (log)", "(f) Rain-drop Reynolds number (snapshot)", logx=True, xlim=(1e-2, 1e5))

    fig.suptitle(
        f"Pöhlker-Dg pair — peak-qr snapshot per cell\n"
        f"({args.n_cells} max-ΔP + {args.n_cells} min-ΔP cells; each cell's own peak-qr hour)",
        fontsize=12, fontweight="bold", y=0.995)
    plt.subplots_adjust(left=0.07, right=0.97, top=0.94,
                        bottom=0.04, wspace=0.22, hspace=0.32)
    out = os.path.join(args.out_dir, "column_peak_snapshot.png")
    plt.savefig(out, dpi=140, facecolor="white"); plt.close()
    print(f"  wrote {out}")


# ------------------------------------------------------------
def main():
    args = parse_args()
    top_idx, bot_idx, lat, lon, dP = select_ensembles(args)
    print(f"Selected {args.n_cells} top cells (ΔP range "
          f"{dP[top_idx].min():+.1f} to {dP[top_idx].max():+.1f} mm)")
    print(f"Selected {args.n_cells} bottom cells (ΔP range "
          f"{dP[bot_idx].min():+.1f} to {dP[bot_idx].max():+.1f} mm)")

    B = fig_timemean_ensemble(args, top_idx, bot_idx, lat, lon, dP)
    fig_heat_budget(args, B, top_idx, bot_idx, dP)
    fig_peak_snapshot(args, top_idx, bot_idx, lat, lon, dP)

    out_txt = os.path.join(args.out_dir, "column_ensemble_summary.txt")
    summary_lines = [
        f"=== Pöhlker-Dg pair — {args.n_cells}+{args.n_cells} ensemble column diagnostic ===",
        f"Region of interest: lat {args.box_lat}, lon {args.box_lon}",
        "",
        f"Top-{args.n_cells} max-ΔP cells (median ΔP={np.median(dP[top_idx]):+.2f} mm, "
        f"range {dP[top_idx].min():+.1f} to {dP[top_idx].max():+.1f}):",
    ]
    for i in top_idx:
        summary_lines.append(f"  idx {i:6d}  lat={lat[i]:+6.2f}  lon={lon[i]:+7.2f}  ΔP={dP[i]:+7.2f} mm")
    summary_lines.append("")
    summary_lines.append(f"Bottom-{args.n_cells} min-ΔP cells "
                         f"(median ΔP={np.median(dP[bot_idx]):+.2f} mm, "
                         f"range {dP[bot_idx].min():+.1f} to {dP[bot_idx].max():+.1f}):")
    for i in bot_idx:
        summary_lines.append(f"  idx {i:6d}  lat={lat[i]:+6.2f}  lon={lon[i]:+7.2f}  ΔP={dP[i]:+7.2f} mm")
    with open(out_txt, "w") as f:
        f.write("\n".join(summary_lines) + "\n")
    print(f"\nwrote {out_txt}")


if __name__ == "__main__":
    main()
