#!/usr/bin/env python3
"""
Phase 7 summary figure: ΔP maps across an N-pair K-salt sensitivity matrix.
Each pair contributes two panels (Amazon zoom + global Robinson).

Defaults match the paper's Phase 7 matrix (polluted, pristine, pristine+l=4
Pöhlker-Dg, pristine+l=5 upper-bound), but any subset or extension can be
specified via --pairs.

Inputs: for each pair KEY listed in --pairs, expects <base>/<KEY>/deltaP_data.npz
(as produced by analyze_pohlker_pair.py).

Example (inside the mpas8 Docker container):
  python3 plot_8run_summary.py \\
    --base /host/mpas_analysis \\
    --salt-ref /host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_salt/history.2025-02-11_00.00.00.nc \\
    --out-file /host/mpas_analysis/8run_summary.png
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


DEFAULT_PAIRS = [
    ("pohlker_pair",   "1. Polluted baseline\n(4,400 → 8,800 /cm³, default size)"),
    ("pristine_pair",  "2. Pristine baseline\n(150 → 300 /cm³, default size)"),
    ("l4_pair",        "3. Pristine + Pöhlker Dg (l=4)\n(150 → 300 /cm³, 160 nm, κ=0.8)"),
    ("size_pair",      "4. Pristine + upper-bound (l=5)\n(150 → 300 /cm³, 320 nm, κ=0.8)"),
]


def parse_args():
    p = argparse.ArgumentParser(
        description="Build the multi-pair Phase 7 ΔP summary figure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument("--base",     required=True,
                   help="Base directory containing per-pair subdirectories with deltaP_data.npz")
    p.add_argument("--out-file", required=True,
                   help="Output PNG path")
    p.add_argument("--salt-ref", required=True,
                   help="Path to any SALT history.*.nc file — used to read the Voronoi mesh")
    p.add_argument("--pairs",    default=None,
                   help="Comma-separated list of pair subdirectory names. "
                        "Labels will be generic unless --pair-labels is also passed. "
                        "Default: the 4-pair Phase 7 matrix (pohlker_pair,pristine_pair,l4_pair,size_pair).")
    p.add_argument("--pair-labels", default=None,
                   help="Pipe-separated (|) list of panel labels (one per --pairs entry). "
                        "Use \\n for line breaks.")
    p.add_argument("--amazon-box", default="-80,-45,-20,10",
                   help="Amazon zoom extent as 'lon_w,lon_e,lat_s,lat_n'. Default: -80,-45,-20,10")
    p.add_argument("--title",    default="Phase 7: K-salt precipitation response across baseline-CCN regimes and particle sizes")
    args = p.parse_args()

    if args.pairs is None:
        args.pair_spec = DEFAULT_PAIRS
    else:
        keys = args.pairs.split(",")
        if args.pair_labels is None:
            labels = [f"{i+1}. {k}" for i, k in enumerate(keys)]
        else:
            raw = args.pair_labels.split("|")
            if len(raw) != len(keys):
                raise SystemExit("--pair-labels count must match --pairs count")
            labels = [s.replace("\\n", "\n") for s in raw]
        args.pair_spec = list(zip(keys, labels))

    args.amazon_extent = tuple(float(x) for x in args.amazon_box.split(","))
    os.makedirs(os.path.dirname(args.out_file) or ".", exist_ok=True)
    return args


def load_polys(path):
    with Dataset(path) as ds:
        latV = np.degrees(ds.variables['latVertex'][:])
        lonV = np.degrees(ds.variables['lonVertex'][:])
        lonV = np.where(lonV > 180, lonV - 360, lonV)
        vOC = ds.variables['verticesOnCell'][:]
        nE = ds.variables['nEdgesOnCell'][:]
    nCells = vOC.shape[0]
    polys = [None]*nCells
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


def draw_panel(ax, polys, valid, dP, vmin, vmax, cmap, extent, title):
    pvs = [polys[i] for i in range(len(polys)) if valid[i]]
    vvs = dP[valid]
    if extent:
        ax.set_extent(extent, crs=ccrs.PlateCarree())
    else:
        ax.set_global()
    pc = PolyCollection(pvs, array=vvs, cmap=cmap,
                        transform=ccrs.PlateCarree(), edgecolors="none")
    pc.set_clim(vmin, vmax)
    ax.add_collection(pc)
    ax.add_feature(cfeature.COASTLINE.with_scale("50m"),
                   linewidth=0.5, edgecolor="#333", zorder=3)
    ax.add_feature(cfeature.BORDERS.with_scale("50m"),
                   linewidth=0.4, edgecolor="gray", zorder=3)
    ax.set_title(title, fontsize=9.5)
    return pc


def main():
    args = parse_args()
    print("loading mesh polygons...")
    polys, valid = load_polys(args.salt_ref)
    data = {}
    for key, _ in args.pair_spec:
        npz = os.path.join(args.base, key, "deltaP_data.npz")
        if not os.path.isfile(npz):
            raise SystemExit(f"missing input: {npz}")
        d = np.load(npz)
        data[key] = {"lat": d["lat"], "lon": d["lon"], "dP": d["dP"]}
        amz = (d['lat'] > -15) & (d['lat'] < 5) & (d['lon'] > -75) & (d['lon'] < -50)
        print(f"  {key}: Amazon ΔP = {d['dP'][amz].mean():+.2f} mm")

    all_dP = np.concatenate([data[k]["dP"] for k, _ in args.pair_spec])
    v = np.percentile(np.abs(all_dP), 98)
    vmin, vmax = -v, v
    print(f"shared color scale: ±{v:.1f} mm")

    ncols = len(args.pair_spec)
    fig = plt.figure(figsize=(5.5 * ncols, 10))

    for col, (key, label) in enumerate(args.pair_spec):
        ax_top = fig.add_subplot(2, ncols, col+1, projection=ccrs.PlateCarree())
        draw_panel(ax_top, polys, valid, data[key]["dP"], vmin, vmax,
                   "RdBu_r", args.amazon_extent, label)
        ax_top.text(0.5, -0.08, "Amazon zoom", transform=ax_top.transAxes,
                    ha="center", va="top", fontsize=8, color="#555")
        ax_bot = fig.add_subplot(2, ncols, col+1+ncols, projection=ccrs.Robinson())
        pc = draw_panel(ax_bot, polys, valid, data[key]["dP"], vmin, vmax,
                        "RdBu_r", None, "Global")

    cbar_ax = fig.add_axes([0.30, 0.04, 0.4, 0.02])
    cb = fig.colorbar(pc, cax=cbar_ax, orientation="horizontal")
    cb.set_label("ΔP = SALT − NOSALT (mm / 30-day)", fontsize=11)

    fig.suptitle(args.title, fontsize=14, fontweight="bold", y=0.985)
    plt.subplots_adjust(left=0.02, right=0.98, top=0.86, bottom=0.10, wspace=0.10, hspace=0.18)
    plt.savefig(args.out_file, dpi=150, facecolor="white")
    plt.close()
    print(f"wrote {args.out_file}")


if __name__ == "__main__":
    main()
