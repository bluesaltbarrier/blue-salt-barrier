"""120 km January Run — Analysis and Plots"""
import os, glob, numpy as np
from netCDF4 import Dataset
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

BASE = os.environ.get("BASE", os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
OUT = os.path.join(BASE, "mpas_analysis")
os.makedirs(OUT, exist_ok=True)
G, LV = 9.81, 2.5e6

NS = os.path.join(BASE, "results_120km_jan_nosalt")
SL = os.path.join(BASE, "results_120km_jan_salt_real")

# Use first no-salt file for mesh geometry
ref_file = sorted(glob.glob(os.path.join(NS, "history.*.nc")))[0]
ref = Dataset(ref_file)
latDeg = np.array(ref.variables["latCell"][:]) * 57.2958
lonDeg = np.array(ref.variables["lonCell"][:]) * 57.2958
lonPlot = np.where(lonDeg > 180, lonDeg - 360, lonDeg)
areaCell = np.array(ref.variables["areaCell"][:])
nCells = len(latDeg)
ref.close()
print(f"Mesh: {nCells} cells")

lat_bins = np.arange(-90, 91, 5)
lat_c = 0.5*(lat_bins[:-1]+lat_bins[1:])

def bin_avg(field):
    r = np.zeros(len(lat_c))
    for b in range(len(lat_c)):
        m = (latDeg>=lat_bins[b])&(latDeg<lat_bins[b+1])
        if np.any(m): r[b] = np.average(field[m], weights=areaCell[m])
    return r

def avg_t2m(d):
    files = sorted(glob.glob(os.path.join(d, "history.*.nc")))
    s = np.zeros(nCells)
    for f in files: ds = Dataset(f); s += np.array(ds.variables["t2m"][0,:]); ds.close()
    return s / len(files)

def get_rain(d):
    files = sorted(glob.glob(os.path.join(d, "history.*.nc")))
    ds0 = Dataset(files[0]); ds1 = Dataset(files[-1])
    r0 = np.array(ds0.variables["rainnc"][0,:]) + np.array(ds0.variables["rainc"][0,:])
    r1 = np.array(ds1.variables["rainnc"][0,:]) + np.array(ds1.variables["rainc"][0,:])
    ds0.close(); ds1.close()
    return (r1-r0)/(len(files)*0.5)

def get_vq(d):
    files = sorted(glob.glob(os.path.join(d, "history.*.nc")))
    s = np.zeros(nCells)
    for f in files:
        ds = Dataset(f)
        v = np.array(ds.variables["uReconstructMeridional"][0,:,:])
        q = np.array(ds.variables["qv"][0,:,:])
        p = np.array(ds.variables["pressure"][0,:,:])
        nk = v.shape[1]
        dp = np.zeros_like(p)
        for k in range(nk):
            if k==0: dp[:,k]=p[:,0]-p[:,1]
            elif k==nk-1: dp[:,k]=p[:,k-1]-p[:,k]
            else: dp[:,k]=0.5*(p[:,k-1]-p[:,k+1])
        dp = np.abs(dp)
        s += np.sum(v*q*dp/G, axis=1)
        ds.close()
    return s / len(files)

def globe_map(data, title, label, fname, cmap, vmin, vmax):
    fig = plt.figure(figsize=(16, 9))
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Robinson())
    ax.set_global()
    ax.add_feature(cfeature.OCEAN, facecolor="#e8f0f8", zorder=0)
    ax.add_feature(cfeature.LAND, facecolor="#f0ebe0", zorder=0)
    ax.add_feature(cfeature.COASTLINE, linewidth=0.5, edgecolor="#444", zorder=2)
    sc = ax.scatter(lonPlot, latDeg, c=data, cmap=cmap, s=4, vmin=vmin, vmax=vmax,
                    edgecolors="none", alpha=0.9, transform=ccrs.PlateCarree(), zorder=1)
    ax.plot([-180,180],[10,10],"k--",lw=1,alpha=0.3,transform=ccrs.PlateCarree())
    ax.plot([-180,180],[-10,-10],"k--",lw=1,alpha=0.3,transform=ccrs.PlateCarree())
    cb = fig.colorbar(sc, ax=ax, orientation="horizontal", shrink=0.6, pad=0.05, aspect=30)
    cb.set_label(label, fontsize=13)
    ax.set_title(title, fontsize=14, fontweight="bold")
    fig.savefig(os.path.join(OUT, fname), dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()

print("Computing 120km January fields...")
t2m_ns = avg_t2m(NS); t2m_sl = avg_t2m(SL)
rain_ns = get_rain(NS); rain_sl = get_rain(SL)
print("  Fluxes...")
vq_ns = get_vq(NS); vq_sl = get_vq(SL)

dt = t2m_sl - t2m_ns
dr = rain_sl - rain_ns
dvq = (vq_sl - vq_ns) * LV

eq_mask = (latDeg >= -10) & (latDeg <= 10)
arctic_mask = latDeg >= 60
antarctic_mask = latDeg <= -60
lat30n_mask = (latDeg >= 28) & (latDeg <= 32)
lat30s_mask = (latDeg >= -32) & (latDeg <= -28)

eq_rain = np.average(dr[eq_mask], weights=areaCell[eq_mask])
arctic_t = np.average(dt[arctic_mask], weights=areaCell[arctic_mask])
antarctic_t = np.average(dt[antarctic_mask], weights=areaCell[antarctic_mask])
transport_30n = np.average(dvq[lat30n_mask], weights=areaCell[lat30n_mask])
transport_30s = np.average(dvq[lat30s_mask], weights=areaCell[lat30s_mask])

# Convert W/m (zonal integral) to TW across circle at 30N
circ_30n = 2*np.pi*6.371e6*np.cos(np.radians(30))
circ_30s = 2*np.pi*6.371e6*np.cos(np.radians(30))
tw_30n = transport_30n * circ_30n / 1e12
tw_30s = transport_30s * circ_30s / 1e12

print(f"\n=== 120km January Results (CONTROL minus NO-SALT) ===")
print(f"  Equatorial rain change:  {eq_rain:+.3f} mm/day")
print(f"  30N transport:           {tw_30n:+.0f} TW")
print(f"  30S transport:           {tw_30s:+.0f} TW")
print(f"  Arctic temperature:      {arctic_t:+.3f} K")
print(f"  Antarctic temperature:   {antarctic_t:+.3f} K")

# Maps
print("\n  Temp map...")
globe_map(dt,
    "120km January: Temperature Change (CONTROL minus NO-SALT)\nFull GCCN lifecycle | Peak NH winter transport season",
    "Temperature Change (K)", "jan120_map_temp.png", "RdBu_r", -2, 2)

print("  Precip map...")
globe_map(dr,
    "120km January: Precipitation Change (CONTROL minus NO-SALT)\nGreen = more rain with salt | Rainforest emission",
    "Precipitation Change (mm/day)", "jan120_map_precip.png", "BrBG", -2, 2)

print("  Flux map...")
globe_map(dvq,
    "120km January: Latent Heat Flux Change (CONTROL minus NO-SALT)",
    "LH Flux Change (W/m)", "jan120_map_flux.png", "RdBu_r", -5e6, 5e6)

# 4-panel summary with comparison to April full GCCN
print("\n  Loading April full GCCN for comparison...")
NS_APR = os.path.join(BASE, "results_fullgccn_nosalt")
SL_APR = os.path.join(BASE, "results_fullgccn_salt")

# Load April mesh (different — 240km)
ref_apr = Dataset(sorted(glob.glob(os.path.join(NS_APR, "history.*.nc")))[0])
latDeg_apr = np.array(ref_apr.variables["latCell"][:]) * 57.2958
areaCell_apr = np.array(ref_apr.variables["areaCell"][:])
nCells_apr = len(latDeg_apr)
ref_apr.close()

lat_bins_apr = np.arange(-90, 91, 5)
lat_c_apr = 0.5*(lat_bins_apr[:-1]+lat_bins_apr[1:])

def bin_avg_apr(field):
    r = np.zeros(len(lat_c_apr))
    for b in range(len(lat_c_apr)):
        m = (latDeg_apr>=lat_bins_apr[b])&(latDeg_apr<lat_bins_apr[b+1])
        if np.any(m): r[b] = np.average(field[m], weights=areaCell_apr[m])
    return r

def avg_t2m_apr(d):
    files = sorted(glob.glob(os.path.join(d, "history.*.nc")))
    s = np.zeros(nCells_apr)
    for f in files: ds = Dataset(f); s += np.array(ds.variables["t2m"][0,:]); ds.close()
    return s / len(files)

def get_rain_apr(d):
    files = sorted(glob.glob(os.path.join(d, "history.*.nc")))
    ds0 = Dataset(files[0]); ds1 = Dataset(files[-1])
    r0 = np.array(ds0.variables["rainnc"][0,:]) + np.array(ds0.variables["rainc"][0,:])
    r1 = np.array(ds1.variables["rainnc"][0,:]) + np.array(ds1.variables["rainc"][0,:])
    ds0.close(); ds1.close()
    return (r1-r0)/(len(files)*0.5)

t2m_apr_ns = avg_t2m_apr(NS_APR); t2m_apr_sl = avg_t2m_apr(SL_APR)
rain_apr_ns = get_rain_apr(NS_APR); rain_apr_sl = get_rain_apr(SL_APR)
dt_apr = t2m_apr_sl - t2m_apr_ns
dr_apr = rain_apr_sl - rain_apr_ns

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Temperature: Jan 120km vs Apr 240km
ax = axes[0,0]
ax.plot(lat_c_apr, bin_avg_apr(dt_apr), color="#e67e22", lw=2.5, label="April (240km)", alpha=0.7)
ax.plot(lat_c, bin_avg(dt), color="#2980b9", lw=3, label="January (120km)")
ax.set_xlabel("Latitude"); ax.set_ylabel("Temp Change (K)")
ax.set_title("Temperature: Seasonal + Resolution Comparison", fontweight="bold")
ax.legend(fontsize=10); ax.grid(True, alpha=0.3); ax.set_xlim(-80,80)
ax.axhline(y=0, color="k", lw=0.5)

# Precipitation
ax = axes[0,1]
ax.plot(lat_c_apr, bin_avg_apr(dr_apr), color="#e67e22", lw=2.5, label="April (240km)", alpha=0.7)
ax.plot(lat_c, bin_avg(dr), color="#2980b9", lw=3, label="January (120km)")
ax.set_xlabel("Latitude"); ax.set_ylabel("Precip Change (mm/day)")
ax.set_title("Precipitation: Seasonal + Resolution Comparison", fontweight="bold")
ax.legend(fontsize=10); ax.grid(True, alpha=0.3); ax.set_xlim(-80,80)
ax.axhline(y=0, color="k", lw=0.5)
ax.axvline(x=-10, color="gray", ls="--", alpha=0.4)
ax.axvline(x=10, color="gray", ls="--", alpha=0.4)

# Absolute precipitation
ax = axes[1,0]
ax.plot(lat_c, bin_avg(rain_ns), "k-", lw=2, label="Jan NO-SALT")
ax.plot(lat_c, bin_avg(rain_sl), "b-", lw=2, label="Jan CONTROL")
ax.set_xlabel("Latitude"); ax.set_ylabel("Precip (mm/day)")
ax.set_title("120km January: Absolute Precipitation", fontweight="bold")
ax.legend(); ax.grid(True, alpha=0.3); ax.set_xlim(-80,80)

# Summary
ax = axes[1,1]; ax.axis("off")
txt = (f"120km JANUARY RUN\n"
       f"MPAS v8.3.1, 30-day, 40,962 cells\n"
       f"Full GCCN lifecycle\n"
       f"Salt: rainforest only (ivgtyp=2)\n\n"
       f"Eq rain:       {eq_rain:+.2f} mm/day\n"
       f"30N transport: {tw_30n:+.0f} TW\n"
       f"30S transport: {tw_30s:+.0f} TW\n"
       f"Arctic:        {arctic_t:+.2f} K\n"
       f"Antarctic:     {antarctic_t:+.2f} K\n\n"
       f"COMPARISON TO APRIL (240km):\n"
       f"  Arctic Apr:      +0.43 K\n"
       f"  Arctic Jan:      {arctic_t:+.2f} K\n"
       f"  Antarctic Apr:   -1.03 K\n"
       f"  Antarctic Jan:   {antarctic_t:+.2f} K\n\n"
       f"Does Arctic cool in winter?")
ax.text(0.05, 0.95, txt, transform=ax.transAxes, fontsize=10.5,
        verticalalignment="top", fontfamily="monospace",
        bbox=dict(boxstyle="round", facecolor="#e3f2fd", alpha=0.8))

fig.suptitle("120km January Run — Seasonal Test of the Blue Salt Barrier",
             fontsize=16, fontweight="bold", y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "jan120_summary.png"), dpi=180, bbox_inches="tight", facecolor="white")
plt.close()

print("\nAll 120km January plots saved!")
