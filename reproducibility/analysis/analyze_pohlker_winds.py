#!/usr/bin/env python3
"""
Wind analysis for MPAS Pohlker paired runs.

Convective/advective processes — not conduction — dominate polar ice loss.
This script computes the time-averaged wind fields in each run and the
differences between the two runs, with emphasis on:

  - 10m surface wind SPEED (drives turbulent sensible/latent heat exchange
    over sea ice and open ocean — "how efficiently is warm air in contact
    with the ice surface dumping heat into it")
  - Meridional wind component (drives poleward mass and heat advection)
  - Polar-region averages and zonal-mean profiles

Usage:
    python3 analyze_pohlker_winds.py <run_a_dir> <run_b_dir> <out_dir>
    # reports Δ = A − B
"""
import os, sys, glob
import numpy as np
from netCDF4 import Dataset
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAVE_CARTOPY = True
except ImportError:
    HAVE_CARTOPY = False

def mesh(run):
    f = sorted(glob.glob(os.path.join(run, "history.*.nc")))[0]
    with Dataset(f) as ds:
        lat = np.degrees(ds.variables["latCell"][:])
        lon = np.degrees(ds.variables["lonCell"][:])
        lon = np.where(lon > 180, lon - 360, lon)
        area = ds.variables["areaCell"][:] if "areaCell" in ds.variables else np.ones_like(lat)
    return lat, lon, area

def time_mean_winds(run):
    """Return (u10_mean, v10_mean, wspd10_mean, vmerid_sfc_mean) over all history files."""
    files = sorted(glob.glob(os.path.join(run, "history.*.nc")))
    u10_sum = v10_sum = wspd_sum = vmerid_sum = None
    for f in files:
        with Dataset(f) as ds:
            u = ds.variables["u10"][0, :]
            v = ds.variables["v10"][0, :]
            vmerid_sfc = ds.variables["uReconstructMeridional"][0, :, 0]  # lowest level
        w = np.sqrt(u*u + v*v)
        if u10_sum is None:
            u10_sum = np.zeros_like(u); v10_sum = np.zeros_like(v)
            wspd_sum = np.zeros_like(w); vmerid_sum = np.zeros_like(vmerid_sfc)
        u10_sum += u; v10_sum += v; wspd_sum += w; vmerid_sum += vmerid_sfc
    n = len(files)
    return u10_sum/n, v10_sum/n, wspd_sum/n, vmerid_sum/n

def load_polys(run):
    f = sorted(glob.glob(os.path.join(run, "history.*.nc")))[0]
    with Dataset(f) as ds:
        latV = np.degrees(ds.variables["latVertex"][:])
        lonV = np.degrees(ds.variables["lonVertex"][:])
        lonV = np.where(lonV > 180, lonV - 360, lonV)
        vOC = ds.variables["verticesOnCell"][:]
        nE = ds.variables["nEdgesOnCell"][:]
    nCells = vOC.shape[0]
    polys = [None]*nCells; valid = np.ones(nCells, dtype=bool)
    for i in range(nCells):
        n = int(nE[i])
        vids = vOC[i, :n] - 1
        plon = lonV[vids]; plat = latV[vids]
        if plon.max() - plon.min() > 180:
            valid[i] = False; polys[i] = np.zeros((n, 2))
        else:
            polys[i] = np.c_[plon, plat]
    return polys, valid

def plot_polar(lat, lon, polys, valid, val, title, fname, vmin, vmax, cmap, label,
               hemisphere="both"):
    """Hemisphere='N' renders only NH polar cap; 'S' only SH; 'both' = global Robinson."""
    from matplotlib.collections import PolyCollection
    pvs = [polys[i] for i in range(len(polys)) if valid[i]]
    vvs = val[valid]

    if HAVE_CARTOPY:
        if hemisphere == "N":
            proj = ccrs.NorthPolarStereo()
            fig = plt.figure(figsize=(9, 9))
            ax = plt.axes(projection=proj)
            ax.set_extent([-180, 180, 50, 90], crs=ccrs.PlateCarree())
        elif hemisphere == "S":
            proj = ccrs.SouthPolarStereo()
            fig = plt.figure(figsize=(9, 9))
            ax = plt.axes(projection=proj)
            ax.set_extent([-180, 180, -90, -50], crs=ccrs.PlateCarree())
        else:
            proj = ccrs.Robinson()
            fig = plt.figure(figsize=(13, 6.5))
            ax = plt.axes(projection=proj)
            ax.set_global()
        pc = PolyCollection(pvs, array=vvs, cmap=cmap,
                            transform=ccrs.PlateCarree(), edgecolors="none")
        pc.set_clim(vmin, vmax); ax.add_collection(pc)
        ax.add_feature(cfeature.COASTLINE.with_scale("50m"),
                       linewidth=0.6, edgecolor="#333", zorder=3)
        ax.gridlines(linewidth=0.3, alpha=0.4, color="gray", linestyle="--")
        ax.set_title(title, fontsize=13)
        plt.colorbar(pc, ax=ax, shrink=0.7, pad=0.05, label=label)
    plt.tight_layout()
    plt.savefig(fname, dpi=140, bbox_inches="tight", facecolor="white"); plt.close()
    print(f"wrote {fname}")

def main():
    if len(sys.argv) != 4:
        print(__doc__); raise SystemExit(1)
    run_a, run_b, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(os.path.join(out_dir, "plots"), exist_ok=True)
    a_name = os.path.basename(os.path.normpath(run_a))
    b_name = os.path.basename(os.path.normpath(run_b))

    lat, lon, area = mesh(run_a)
    print(f"Computing wind fields ({a_name})...")
    u_a, v_a, wspd_a, vmerid_a = time_mean_winds(run_a)
    print(f"Computing wind fields ({b_name})...")
    u_b, v_b, wspd_b, vmerid_b = time_mean_winds(run_b)

    dw = wspd_a - wspd_b
    dvm = vmerid_a - vmerid_b

    # Regional means
    arc = lat >= 60
    aa = lat <= -60
    arc_high = lat >= 70
    aa_high = lat <= -70
    bnd30n = (lat >= 28) & (lat <= 32)
    bnd30s = (lat >= -32) & (lat <= -28)

    def avg(x, m): return np.average(x[m], weights=area[m])

    lines = [
        f"=== Wind analysis: {a_name} minus {b_name} ===",
        "",
        "Absolute 10m wind speed (m/s, time-avg):",
        f"  Arctic (lat>=60):   A={avg(wspd_a, arc):.2f}  B={avg(wspd_b, arc):.2f}  Δ={avg(dw, arc):+.3f}",
        f"  Arctic core (>=70): A={avg(wspd_a, arc_high):.2f}  B={avg(wspd_b, arc_high):.2f}  Δ={avg(dw, arc_high):+.3f}",
        f"  Antarctic (<=-60):  A={avg(wspd_a, aa):.2f}  B={avg(wspd_b, aa):.2f}  Δ={avg(dw, aa):+.3f}",
        f"  Antarctic (<=-70):  A={avg(wspd_a, aa_high):.2f}  B={avg(wspd_b, aa_high):.2f}  Δ={avg(dw, aa_high):+.3f}",
        "",
        "Surface meridional wind (m/s, time-avg; + = northward):",
        f"  30N band:  A={avg(vmerid_a, bnd30n):+.3f}  B={avg(vmerid_b, bnd30n):+.3f}  Δ={avg(dvm, bnd30n):+.3f}",
        f"  30S band:  A={avg(vmerid_a, bnd30s):+.3f}  B={avg(vmerid_b, bnd30s):+.3f}  Δ={avg(dvm, bnd30s):+.3f}",
        f"  Arctic:    A={avg(vmerid_a, arc):+.3f}  B={avg(vmerid_b, arc):+.3f}  Δ={avg(dvm, arc):+.3f}",
        f"  Antarctic: A={avg(vmerid_a, aa):+.3f}  B={avg(vmerid_b, aa):+.3f}  Δ={avg(dvm, aa):+.3f}",
    ]
    print("\n" + "\n".join(lines))
    with open(os.path.join(out_dir, "wind_summary.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    polys, valid = load_polys(run_a)

    # Δ wind speed — global and both polar caps
    dw_lim = max(np.nanpercentile(np.abs(dw), 98), 0.5)
    plot_polar(lat, lon, polys, valid, dw,
               f"Δ 10m wind speed ({a_name} − {b_name})",
               os.path.join(out_dir, "plots", "delta_wind_speed_global.png"),
               vmin=-dw_lim, vmax=dw_lim, cmap="RdBu_r", label="m/s", hemisphere="both")
    plot_polar(lat, lon, polys, valid, dw,
               f"Δ 10m wind speed — Arctic ({a_name} − {b_name})",
               os.path.join(out_dir, "plots", "delta_wind_speed_arctic.png"),
               vmin=-dw_lim, vmax=dw_lim, cmap="RdBu_r", label="m/s", hemisphere="N")
    plot_polar(lat, lon, polys, valid, dw,
               f"Δ 10m wind speed — Antarctic ({a_name} − {b_name})",
               os.path.join(out_dir, "plots", "delta_wind_speed_antarctic.png"),
               vmin=-dw_lim, vmax=dw_lim, cmap="RdBu_r", label="m/s", hemisphere="S")

    # Δ meridional wind
    dvm_lim = max(np.nanpercentile(np.abs(dvm), 98), 0.5)
    plot_polar(lat, lon, polys, valid, dvm,
               f"Δ meridional wind (surface) ({a_name} − {b_name}); + = more northward",
               os.path.join(out_dir, "plots", "delta_meridional_wind.png"),
               vmin=-dvm_lim, vmax=dvm_lim, cmap="RdBu_r", label="m/s", hemisphere="both")

    np.savez(os.path.join(out_dir, "wind_data.npz"),
             lat=lat, lon=lon, area=area,
             wspd_a=wspd_a, wspd_b=wspd_b, dw=dw,
             vmerid_a=vmerid_a, vmerid_b=vmerid_b, dvm=dvm)
    print(f"wrote {os.path.join(out_dir, 'wind_data.npz')}")

if __name__ == "__main__":
    main()
