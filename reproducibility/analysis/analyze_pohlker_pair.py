#!/usr/bin/env python3
"""
SALT vs NOSALT analysis for the Pohlker 120km January experiment.

Reads the last history file from each run (which contains accumulated
rainnc/rainc since simulation start) and computes differences.

Outputs:
    - plots/deltaP_global.png         global ΔP map (mm/30day)
    - plots/deltaP_amazon.png         Amazon zoom
    - plots/deltaP_zonal.png          zonal mean ΔP
    - plots/delta_nwfa_surface.png    ΔCCN (nwfa) surface map
    - summary.txt                     numerical summary
    - deltaP_data.npz                 raw arrays for further analysis

Usage:
    python3 analyze_pohlker_pair.py \
        /d/WRF/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_salt \
        /d/WRF/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_nosalt \
        /d/WRF/mpas_analysis/pohlker_pair
"""
import os, sys, glob
import numpy as np
import netCDF4 as nc
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
try:
    import cartopy.crs as ccrs
    import cartopy.feature as cfeature
    HAVE_CARTOPY = True
except ImportError:
    HAVE_CARTOPY = False

def last_history(run_dir):
    files = sorted(glob.glob(os.path.join(run_dir, 'history.*.nc')))
    if not files:
        raise SystemExit(f"no history files in {run_dir}")
    return files[-1]

def load_precip(path):
    """Return (lat_deg, lon_deg, rainnc_mm, rainc_mm, nwfa_sfc, vegfra) from a history file."""
    with nc.Dataset(path) as ds:
        lat = np.degrees(ds.variables['latCell'][:])
        lon = np.degrees(ds.variables['lonCell'][:])
        lon = np.where(lon > 180, lon - 360, lon)
        rainnc = ds.variables['rainnc'][0, :]
        rainc = ds.variables['rainc'][0, :] if 'rainc' in ds.variables else np.zeros_like(rainnc)
        nwfa_sfc = ds.variables['nwfa'][0, :, 0]
        vegfra = ds.variables['vegfra'][0, :]
    return lat, lon, rainnc, rainc, nwfa_sfc, vegfra

def load_nwfa_timeseries(run_dir):
    """Load surface nwfa from every history file in the run. Returns (dates, nwfa[nt,nCells])."""
    files = sorted(glob.glob(os.path.join(run_dir, 'history.*.nc')))
    arrs = []
    dates = []
    for f in files:
        with nc.Dataset(f) as ds:
            arrs.append(ds.variables['nwfa'][0, :, 0])
            dates.append(os.path.basename(f).replace('history.', '').replace('.nc', ''))
    return dates, np.array(arrs)

def load_mesh_polygons(path):
    """Return (polygons, valid_mask): polygons[i] is Nx2 array of (lon,lat) for cell i,
    valid_mask[i]=False if cell crosses dateline (skip to avoid wrap artifacts)."""
    with nc.Dataset(path) as ds:
        latV = np.degrees(ds.variables['latVertex'][:])
        lonV = np.degrees(ds.variables['lonVertex'][:])
        lonV = np.where(lonV > 180, lonV - 360, lonV)
        vOnCell = ds.variables['verticesOnCell'][:]    # 1-indexed
        nEdges = ds.variables['nEdgesOnCell'][:]
    nCells = vOnCell.shape[0]
    polygons = [None] * nCells
    valid = np.ones(nCells, dtype=bool)
    for i in range(nCells):
        n = int(nEdges[i])
        vids = vOnCell[i, :n] - 1   # Fortran->Python indexing
        plon = lonV[vids]
        plat = latV[vids]
        if plon.max() - plon.min() > 180.0:
            valid[i] = False
            polygons[i] = np.zeros((n, 2))   # placeholder
        else:
            polygons[i] = np.c_[plon, plat]
    return polygons, valid

def plot_field(lat, lon, val, title, fname, polygons, valid, vmin=None, vmax=None,
               cmap='RdBu_r', extent=None, label='mm/30-day'):
    """Render MPAS data by coloring the actual Voronoi cell polygons."""
    from matplotlib.collections import PolyCollection
    if vmin is None or vmax is None:
        v = np.nanpercentile(np.abs(val), 98)
        vmin, vmax = -v, v

    # Build list of (polygon, value) for valid cells
    polys = [polygons[i] for i in range(len(polygons)) if valid[i]]
    vals = val[valid]

    if HAVE_CARTOPY:
        if extent:
            proj = ccrs.PlateCarree(); figsize = (10, 6)
        else:
            proj = ccrs.Robinson(); figsize = (13, 6.5)
        fig = plt.figure(figsize=figsize)
        ax = plt.axes(projection=proj)
        if extent:
            ax.set_extent(extent, crs=ccrs.PlateCarree())
        else:
            ax.set_global()
        pc = PolyCollection(polys, array=vals, cmap=cmap,
                            transform=ccrs.PlateCarree(), edgecolors='none')
        pc.set_clim(vmin, vmax)
        ax.add_collection(pc)
        ax.add_feature(cfeature.COASTLINE.with_scale('50m'), linewidth=0.7, edgecolor='black', zorder=3)
        ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=0.5, edgecolor='gray', zorder=3)
        gl = ax.gridlines(draw_labels=bool(extent), linewidth=0.3, alpha=0.4, color='gray', linestyle='--')
        if extent: gl.top_labels = False; gl.right_labels = False
        ax.set_title(title)
        plt.colorbar(pc, ax=ax, shrink=0.7, pad=0.05, label=label)
    else:
        fig, ax = plt.subplots(figsize=(12, 5))
        pc = PolyCollection(polys, array=vals, cmap=cmap, edgecolors='none')
        pc.set_clim(vmin, vmax)
        ax.add_collection(pc)
        if extent:
            ax.set_xlim(extent[0], extent[1]); ax.set_ylim(extent[2], extent[3])
        else:
            ax.set_xlim(-180, 180); ax.set_ylim(-90, 90)
        ax.set_xlabel('Longitude'); ax.set_ylabel('Latitude')
        ax.set_title(title); ax.grid(alpha=0.3)
        plt.colorbar(pc, ax=ax, shrink=0.8, label=label)
    plt.tight_layout(); plt.savefig(fname, dpi=140); plt.close()
    print(f"wrote {fname}")

# backward-compat alias for the two callers in main()
plot_scatter = plot_field

def zonal_mean(lat, val, bin_deg=2.0):
    edges = np.arange(-90, 90 + bin_deg, bin_deg)
    centers = 0.5 * (edges[:-1] + edges[1:])
    zm = np.zeros_like(centers, dtype=float)
    for i, (lo, hi) in enumerate(zip(edges[:-1], edges[1:])):
        m = (lat >= lo) & (lat < hi)
        zm[i] = val[m].mean() if m.any() else np.nan
    return centers, zm

def main():
    if len(sys.argv) != 4:
        print(__doc__); raise SystemExit(1)
    salt_dir, nosalt_dir, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    plot_dir = os.path.join(out_dir, 'plots')
    os.makedirs(plot_dir, exist_ok=True)

    salt_file = last_history(salt_dir)
    nosalt_file = last_history(nosalt_dir)
    print(f"SALT last file:   {os.path.basename(salt_file)}")
    print(f"NOSALT last file: {os.path.basename(nosalt_file)}")

    lat, lon, s_nc, s_c, s_nwfa, vegfra = load_precip(salt_file)
    _,   _,   n_nc, n_c, n_nwfa, _      = load_precip(nosalt_file)

    print("loading Voronoi mesh geometry...")
    polygons, valid = load_mesh_polygons(salt_file)
    print(f"  {valid.sum()} valid cells, {(~valid).sum()} dateline cells skipped")

    # rainnc/rainc are accumulated since start, so each is a 30-day total.
    salt_tot = s_nc + s_c
    nosalt_tot = n_nc + n_c
    dP = salt_tot - nosalt_tot
    dP_nwfa = s_nwfa - n_nwfa

    # Geographic masks
    amazon = (lat > -15) & (lat < 5) & (lon > -75) & (lon < -50) & (vegfra > 0.5)
    congo  = (lat > -10) & (lat < 5) & (lon > 10)  & (lon < 35)  & (vegfra > 0.5)
    seasia = (lat > -10) & (lat < 10) & (lon > 95) & (lon < 140) & (vegfra > 0.3)
    tropical = (np.abs(lat) < 23.5)
    all_forest = amazon | congo | seasia

    # Summary statistics
    lines = []
    lines.append(f"SALT source: {salt_file}")
    lines.append(f"NOSALT source: {nosalt_file}")
    lines.append("")
    lines.append("=== 30-day accumulated precipitation (mm) ===")
    for name, m in [("Amazon (IGBP-2)", amazon), ("Congo (IGBP-2)", congo),
                     ("SE Asia", seasia), ("All tropical forest", all_forest),
                     ("Tropics (|lat|<23.5)", tropical), ("Global", np.ones_like(lat, dtype=bool))]:
        if m.sum() == 0:
            lines.append(f"  {name:30s}: (mask empty)"); continue
        lines.append(f"  {name:30s}: SALT={salt_tot[m].mean():7.2f}  NOSALT={nosalt_tot[m].mean():7.2f}  ΔP={dP[m].mean():+7.3f}  (n={m.sum()})")
    lines.append("")
    lines.append("=== Surface nwfa (#/kg) ===")
    for name, m in [("Amazon", amazon), ("Congo", congo), ("SE Asia", seasia), ("Global", np.ones_like(lat, dtype=bool))]:
        if m.sum() == 0: continue
        lines.append(f"  {name:20s}: SALT={s_nwfa[m].mean():.3e}  NOSALT={n_nwfa[m].mean():.3e}  ratio={s_nwfa[m].mean()/n_nwfa[m].mean():.3f}")

    with open(os.path.join(out_dir, 'summary.txt'), 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print('\n'.join(lines))

    # Plots
    plot_field(lat, lon, dP,
               'ΔP (SALT − NOSALT), mm / 30-day',
               os.path.join(plot_dir, 'deltaP_global.png'),
               polygons, valid)

    plot_field(lat, lon, dP,
               'ΔP over Amazon, mm / 30-day',
               os.path.join(plot_dir, 'deltaP_amazon.png'),
               polygons, valid, extent=(-80, -45, -20, 10))

    plot_field(lat, lon, dP_nwfa,
               'Δnwfa surface end-of-run (day 30, dominated by meteorological divergence)',
               os.path.join(plot_dir, 'delta_nwfa_surface.png'),
               polygons, valid, label='#/kg')

    # Day-1 and time-mean Δnwfa: the scientifically interpretable versions
    print("loading full nwfa time series for both runs...")
    _, s_ts = load_nwfa_timeseries(salt_dir)
    _, n_ts = load_nwfa_timeseries(nosalt_dir)
    dnwfa_day1 = s_ts[0] - n_ts[0]                 # pure forcing signal
    dnwfa_mean = s_ts.mean(0) - n_ts.mean(0)       # averaged over 30 days
    print(f"  day-1  Δnwfa: Amazon mean = {dnwfa_day1[amazon].mean():.3e} (expected ~+3.6e9)")
    print(f"  30-day Δnwfa: Amazon mean = {dnwfa_mean[amazon].mean():.3e}")

    plot_field(lat, lon, dnwfa_day1,
               'Δnwfa day 1 (SALT − NOSALT): applied forcing',
               os.path.join(plot_dir, 'delta_nwfa_day1.png'),
               polygons, valid, label='#/kg')

    plot_field(lat, lon, dnwfa_mean,
               'Δnwfa 30-day time-mean (SALT − NOSALT)',
               os.path.join(plot_dir, 'delta_nwfa_timemean.png'),
               polygons, valid, label='#/kg')

    # Zonal mean
    centers, zm_dP = zonal_mean(lat, dP)
    _, zm_salt = zonal_mean(lat, salt_tot)
    _, zm_nos = zonal_mean(lat, nosalt_tot)
    fig, ax = plt.subplots(1, 2, figsize=(12, 5))
    ax[0].plot(zm_salt, centers, label='SALT', color='tab:red')
    ax[0].plot(zm_nos, centers, label='NOSALT', color='tab:blue')
    ax[0].set_xlabel('Precip (mm / 30-day)'); ax[0].set_ylabel('Latitude')
    ax[0].set_title('Zonal-mean 30-day precipitation'); ax[0].legend(); ax[0].grid(alpha=0.3)
    ax[1].plot(zm_dP, centers, color='tab:purple')
    ax[1].axvline(0, color='k', lw=0.5)
    ax[1].set_xlabel('ΔP (mm / 30-day)'); ax[1].set_ylabel('Latitude')
    ax[1].set_title('SALT − NOSALT'); ax[1].grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(plot_dir, 'deltaP_zonal.png'), dpi=120); plt.close()
    print(f"wrote {os.path.join(plot_dir, 'deltaP_zonal.png')}")

    np.savez(os.path.join(out_dir, 'deltaP_data.npz'),
             lat=lat, lon=lon, salt_tot=salt_tot, nosalt_tot=nosalt_tot,
             dP=dP, s_nwfa=s_nwfa, n_nwfa=n_nwfa, vegfra=vegfra)
    print(f"wrote {os.path.join(out_dir, 'deltaP_data.npz')}")

if __name__ == '__main__':
    main()
