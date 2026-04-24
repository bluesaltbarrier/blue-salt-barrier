#!/usr/bin/env python3
"""
Latent heat flux analysis for the Pohlker paired runs.
Uses the same methodology as reproducibility/analysis/plot_120km_jan.py
(Lvq = L_v * sum_k v*q*dp/g, averaged over all history files).

Usage:
    python3 analyze_pohlker_heat_flux.py <salt_dir> <nosalt_dir> <out_dir>
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

G = 9.81
LV = 2.5e6       # J/kg, latent heat of vaporization
REARTH = 6.371e6 # m

def get_mesh(salt_dir):
    f = sorted(glob.glob(os.path.join(salt_dir, "history.*.nc")))[0]
    with Dataset(f) as ds:
        lat = np.degrees(ds.variables["latCell"][:])
        lon = np.degrees(ds.variables["lonCell"][:])
        lon = np.where(lon > 180, lon - 360, lon)
        area = ds.variables["areaCell"][:] if "areaCell" in ds.variables else np.ones_like(lat)
        nCells = lat.size
    return lat, lon, area, nCells

def get_vq(run_dir, nCells):
    """Column-integrated v*q (kg/(m*s)), averaged over all history files."""
    files = sorted(glob.glob(os.path.join(run_dir, "history.*.nc")))
    s = np.zeros(nCells)
    for f in files:
        with Dataset(f) as ds:
            v = np.array(ds.variables["uReconstructMeridional"][0, :, :])
            q = np.array(ds.variables["qv"][0, :, :])
            p = np.array(ds.variables["pressure"][0, :, :])
        nk = v.shape[1]
        dp = np.zeros_like(p)
        dp[:, 0] = p[:, 0] - p[:, 1]
        dp[:, -1] = p[:, -2] - p[:, -1]
        dp[:, 1:-1] = 0.5 * (p[:, :-2] - p[:, 2:])
        dp = np.abs(dp)
        s += np.sum(v * q * dp / G, axis=1)
    return s / len(files)

def get_t2m(run_dir, nCells):
    files = sorted(glob.glob(os.path.join(run_dir, "history.*.nc")))
    s = np.zeros(nCells)
    for f in files:
        with Dataset(f) as ds:
            s += np.array(ds.variables["t2m"][0, :]) if "t2m" in ds.variables else 0
    return s / len(files)

def get_rain_rate(run_dir, nCells):
    files = sorted(glob.glob(os.path.join(run_dir, "history.*.nc")))
    with Dataset(files[0]) as ds:
        r0 = np.array(ds.variables["rainnc"][0, :]) + np.array(ds.variables["rainc"][0, :])
    with Dataset(files[-1]) as ds:
        r1 = np.array(ds.variables["rainnc"][0, :]) + np.array(ds.variables["rainc"][0, :])
    # history output every 12 h -> 0.5 day between files; total days = (n-1)*0.5
    total_days = (len(files) - 1) * 0.5
    return (r1 - r0) / max(total_days, 1.0)

def load_polygons(salt_dir):
    f = sorted(glob.glob(os.path.join(salt_dir, "history.*.nc")))[0]
    with Dataset(f) as ds:
        latV = np.degrees(ds.variables["latVertex"][:])
        lonV = np.degrees(ds.variables["lonVertex"][:])
        lonV = np.where(lonV > 180, lonV - 360, lonV)
        vOC = ds.variables["verticesOnCell"][:]
        nE = ds.variables["nEdgesOnCell"][:]
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

def plot_map(lat, lon, polys, valid, val, title, fname, vmin, vmax, cmap, label):
    from matplotlib.collections import PolyCollection
    pvs = [polys[i] for i in range(len(polys)) if valid[i]]
    vvs = val[valid]
    if HAVE_CARTOPY:
        fig = plt.figure(figsize=(13, 6.5))
        ax = plt.axes(projection=ccrs.Robinson())
        ax.set_global()
        ax.add_feature(cfeature.OCEAN, facecolor="#e8f0f8", zorder=0)
        ax.add_feature(cfeature.LAND, facecolor="#f0ebe0", zorder=0)
        pc = PolyCollection(pvs, array=vvs, cmap=cmap,
                            transform=ccrs.PlateCarree(), edgecolors="none")
        pc.set_clim(vmin, vmax); ax.add_collection(pc)
        ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.5, edgecolor="#444", zorder=3)
        ax.plot([-180, 180], [10, 10], "k--", lw=0.8, alpha=0.3, transform=ccrs.PlateCarree(), zorder=4)
        ax.plot([-180, 180], [-10, -10], "k--", lw=0.8, alpha=0.3, transform=ccrs.PlateCarree(), zorder=4)
        ax.set_title(title, fontsize=13, fontweight="bold")
        plt.colorbar(pc, ax=ax, orientation="horizontal", shrink=0.6, pad=0.05, label=label)
    plt.tight_layout(); plt.savefig(fname, dpi=150, bbox_inches="tight", facecolor="white"); plt.close()
    print(f"wrote {fname}")

def main():
    if len(sys.argv) != 4:
        print(__doc__); raise SystemExit(1)
    salt_dir, nosalt_dir, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(os.path.join(out_dir, "plots"), exist_ok=True)

    lat, lon, area, nCells = get_mesh(salt_dir)
    print("Computing latent-heat flux (integrating v*q*dp/g over column + time)...")
    vq_sl = get_vq(salt_dir, nCells)
    vq_ns = get_vq(nosalt_dir, nCells)
    dvq = (vq_sl - vq_ns) * LV      # W/m

    print("Computing temperature & precip differences...")
    t_sl = get_t2m(salt_dir, nCells); t_ns = get_t2m(nosalt_dir, nCells)
    dT = t_sl - t_ns
    r_sl = get_rain_rate(salt_dir, nCells); r_ns = get_rain_rate(nosalt_dir, nCells)
    dR = r_sl - r_ns  # mm/day

    # Zonal-band integrals
    eq_mask = (lat >= -10) & (lat <= 10)
    arc_mask = lat >= 60
    aa_mask = lat <= -60
    l30n = (lat >= 28) & (lat <= 32)
    l30s = (lat >= -32) & (lat <= -28)

    eq_rain = np.average(dR[eq_mask], weights=area[eq_mask])
    arc_T = np.average(dT[arc_mask], weights=area[arc_mask])
    aa_T = np.average(dT[aa_mask], weights=area[aa_mask])
    lhf_30n = np.average(dvq[l30n], weights=area[l30n])  # W/m
    lhf_30s = np.average(dvq[l30s], weights=area[l30s])  # W/m

    circ_30 = 2 * np.pi * REARTH * np.cos(np.radians(30))
    tw_30n = lhf_30n * circ_30 / 1e12
    tw_30s = lhf_30s * circ_30 / 1e12

    lines = [
        "=== Pohlker SALT − NOSALT (polluted baseline) ===",
        f"Equatorial (|lat|<10) rain change: {eq_rain:+.3f} mm/day",
        f"Arctic (lat>60) T2m change:        {arc_T:+.3f} K",
        f"Antarctic (lat<-60) T2m change:    {aa_T:+.3f} K",
        f"30N latent-heat transport:         {tw_30n:+.0f} TW  (W/m: {lhf_30n:+.2e})",
        f"30S latent-heat transport:         {tw_30s:+.0f} TW  (W/m: {lhf_30s:+.2e})",
    ]
    print("\n" + "\n".join(lines))
    with open(os.path.join(out_dir, "heat_flux_summary.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")

    polys, valid = load_polygons(salt_dir)
    plot_map(lat, lon, polys, valid, dvq,
             "Latent Heat Flux Change (SALT − NOSALT), polluted baseline",
             os.path.join(out_dir, "plots", "delta_latent_flux.png"),
             vmin=-5e6, vmax=5e6, cmap="RdBu_r", label="W/m")
    plot_map(lat, lon, polys, valid, dT,
             "T2m Change (SALT − NOSALT), polluted baseline",
             os.path.join(out_dir, "plots", "delta_T2m.png"),
             vmin=-2, vmax=2, cmap="RdBu_r", label="K")
    plot_map(lat, lon, polys, valid, dR,
             "Precipitation Change (SALT − NOSALT), polluted baseline",
             os.path.join(out_dir, "plots", "delta_precip_rate.png"),
             vmin=-2, vmax=2, cmap="BrBG", label="mm/day")

    np.savez(os.path.join(out_dir, "heat_flux_data.npz"),
             lat=lat, lon=lon, area=area,
             vq_salt=vq_sl, vq_nosalt=vq_ns, dvq_Wm=dvq,
             t2m_salt=t_sl, t2m_nosalt=t_ns, dT=dT,
             rain_salt=r_sl, rain_nosalt=r_ns, dR=dR)
    print(f"wrote {os.path.join(out_dir, 'heat_flux_data.npz')}")

if __name__ == "__main__":
    main()
