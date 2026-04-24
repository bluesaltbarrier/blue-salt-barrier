#!/usr/bin/env python3
"""
Build composite multi-panel figures for the paper directly from the stored
.npz data, using consistent styling (Robinson projection, horizontal
colorbars below, uniform aspect).

Inputs (expected in --pair-dir):
  deltaP_data.npz     produced by analyze_pohlker_pair.py
  heat_flux_data.npz  produced by analyze_pohlker_heat_flux.py
  wind_data.npz       produced by analyze_pohlker_winds.py
  plots/delta_nwfa_day1.png  produced by analyze_pohlker_pair.py

Outputs (written to --out-dir):
  l4_mechanism_4panel.png
  l4_polar_winds.png
  l4_nwfa_day1.png

Example (inside the mpas8 Docker container):
  python3 make_paper_composites.py \\
    --pair-dir /host/mpas_analysis/l4_pair \\
    --out-dir /host/mpas_analysis \\
    --salt-ref /host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_salt/history.2025-02-11_00.00.00.nc
"""
import os, argparse
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from netCDF4 import Dataset


def parse_args():
    p = argparse.ArgumentParser(
        description="Build paper composite figures from per-pair .npz data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--pair-dir", required=True,
                   help="Directory containing deltaP_data.npz, heat_flux_data.npz, wind_data.npz, and plots/delta_nwfa_day1.png")
    p.add_argument("--out-dir",  required=True,
                   help="Output directory for composite figures")
    p.add_argument("--salt-ref", required=True,
                   help="Path to any SALT-run history.*.nc file — used to read the Voronoi mesh")
    p.add_argument("--label",    default="Pristine baseline + Pöhlker Dg (l=4, 160 nm, κ=0.8)",
                   help="Configuration label to show in the figure suptitle")
    p.add_argument("--prefix",   default="l4",
                   help="Filename prefix for output PNGs. Default: 'l4'")
    args = p.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    return args


def load_polys(path):
    with Dataset(path) as ds:
        latV = np.degrees(ds.variables['latVertex'][:])
        lonV = np.degrees(ds.variables['lonVertex'][:])
        lonV = np.where(lonV > 180, lonV - 360, lonV)
        vOC = ds.variables['verticesOnCell'][:]
        nE = ds.variables['nEdgesOnCell'][:]
    nCells = vOC.shape[0]
    polys = [None] * nCells
    valid = np.ones(nCells, dtype=bool)
    for i in range(nCells):
        n = int(nE[i])
        vids = vOC[i, :n] - 1
        plon = lonV[vids]; plat = latV[vids]
        if plon.max() - plon.min() > 180:
            valid[i] = False; polys[i] = np.zeros((n, 2))
        else:
            polys[i] = np.c_[plon, plat]
    return polys, valid


def draw_field(ax, polys, valid, field, vmin, vmax, cmap, title, cbar_label):
    pvs = [polys[i] for i in range(len(polys)) if valid[i]]
    vvs = field[valid]
    ax.set_global()
    pc = PolyCollection(pvs, array=vvs, cmap=cmap,
                        transform=ccrs.PlateCarree(), edgecolors="none")
    pc.set_clim(vmin, vmax)
    ax.add_collection(pc)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"),
                   linewidth=0.5, edgecolor="#333", zorder=3)
    ax.set_title(title, fontsize=11)
    cb = plt.colorbar(pc, ax=ax, orientation="horizontal",
                      shrink=0.75, pad=0.05, aspect=35)
    cb.set_label(cbar_label, fontsize=9)
    cb.ax.tick_params(labelsize=8)


def make_4panel(args, polys, valid):
    dp = np.load(os.path.join(args.pair_dir, "deltaP_data.npz"))
    hf = np.load(os.path.join(args.pair_dir, "heat_flux_data.npz"))
    wd = np.load(os.path.join(args.pair_dir, "wind_data.npz"))

    dP = dp["dP"] / 30.0
    dT = hf["dT"]
    dVq = hf["dvq_Wm"] / 1e9
    dW = wd["dw"]

    fig = plt.figure(figsize=(16, 9))
    projR = ccrs.Robinson()

    ax1 = fig.add_subplot(2, 2, 1, projection=projR)
    v = max(np.nanpercentile(np.abs(dP), 98), 0.3)
    draw_field(ax1, polys, valid, dP, -v, v, "BrBG",
               "ΔPrecipitation rate", "mm/day")

    ax2 = fig.add_subplot(2, 2, 2, projection=projR)
    v = max(np.nanpercentile(np.abs(dT), 98), 0.5)
    draw_field(ax2, polys, valid, dT, -v, v, "RdBu_r",
               "Δ2-m temperature", "K")

    ax3 = fig.add_subplot(2, 2, 3, projection=projR)
    v = max(np.nanpercentile(np.abs(dVq), 98), 0.05)
    draw_field(ax3, polys, valid, dVq, -v, v, "RdBu_r",
               "ΔMeridional latent-heat flux", "GW/m")

    ax4 = fig.add_subplot(2, 2, 4, projection=projR)
    v = max(np.nanpercentile(np.abs(dW), 98), 0.3)
    draw_field(ax4, polys, valid, dW, -v, v, "RdBu_r",
               "Δ10-m wind speed", "m/s")

    fig.suptitle(f"Primary configuration, SALT − NOSALT: {args.label}",
                 fontsize=13, fontweight="bold", y=0.995)
    plt.subplots_adjust(left=0.02, right=0.98, top=0.93,
                        bottom=0.04, wspace=0.08, hspace=0.22)

    out = os.path.join(args.out_dir, f"{args.prefix}_mechanism_4panel.png")
    plt.savefig(out, dpi=150, facecolor="white")
    plt.close()
    print(f"wrote {out}")


def make_polar_winds(args, polys, valid):
    wd = np.load(os.path.join(args.pair_dir, "wind_data.npz"))
    dw = wd["dw"]
    v = max(np.nanpercentile(np.abs(dw), 98), 0.3)

    fig = plt.figure(figsize=(14, 7))

    def polar_panel(pos, proj, extent, title):
        ax = fig.add_subplot(1, 2, pos, projection=proj)
        ax.set_extent(extent, crs=ccrs.PlateCarree())
        pvs = [polys[i] for i in range(len(polys)) if valid[i]]
        vvs = dw[valid]
        pc = PolyCollection(pvs, array=vvs, cmap="RdBu_r",
                            transform=ccrs.PlateCarree(), edgecolors="none")
        pc.set_clim(-v, v); ax.add_collection(pc)
        ax.add_feature(cfeature.COASTLINE.with_scale("50m"),
                       linewidth=0.5, edgecolor="#333", zorder=3)
        ax.gridlines(linewidth=0.3, alpha=0.4, color="gray", linestyle="--")
        ax.set_title(title, fontsize=11)
        cb = plt.colorbar(pc, ax=ax, orientation="horizontal",
                          shrink=0.7, pad=0.06, aspect=30)
        cb.set_label("m/s", fontsize=9); cb.ax.tick_params(labelsize=8)

    polar_panel(1, ccrs.NorthPolarStereo(),
                [-180, 180, 50, 90], "Δ10-m wind speed — Arctic")
    polar_panel(2, ccrs.SouthPolarStereo(),
                [-180, 180, -90, -50], "Δ10-m wind speed — Antarctic")

    fig.suptitle(f"Primary configuration, SALT − NOSALT: {args.label}",
                 fontsize=13, fontweight="bold", y=0.995)
    plt.subplots_adjust(left=0.02, right=0.98, top=0.90,
                        bottom=0.04, wspace=0.08)

    out = os.path.join(args.out_dir, f"{args.prefix}_polar_winds.png")
    plt.savefig(out, dpi=150, facecolor="white")
    plt.close()
    print(f"wrote {out}")


def copy_day1_verification(args):
    from PIL import Image
    src = os.path.join(args.pair_dir, "plots", "delta_nwfa_day1.png")
    dst = os.path.join(args.out_dir, f"{args.prefix}_nwfa_day1.png")
    if not os.path.isfile(src):
        print(f"(skipped: {src} not found)")
        return
    Image.open(src).save(dst, optimize=True)
    print(f"wrote {dst}")


def main():
    args = parse_args()
    print("loading mesh polygons...")
    polys, valid = load_polys(args.salt_ref)
    make_4panel(args, polys, valid)
    make_polar_winds(args, polys, valid)
    copy_day1_verification(args)


if __name__ == "__main__":
    main()
