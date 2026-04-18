"""Full GCCN Lifecycle — Final Results Plots"""
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

NS = os.path.join(BASE, "results_fullgccn_nosalt")
SL = os.path.join(BASE, "results_fullgccn_salt")

ref = Dataset(os.path.join(NS, "history.2026-04-12_00.00.00.nc"))
latDeg = np.array(ref.variables["latCell"][:]) * 57.3
lonDeg = np.array(ref.variables["lonCell"][:]) * 57.3
lonPlot = np.where(lonDeg > 180, lonDeg - 360, lonDeg)
areaCell = np.array(ref.variables["areaCell"][:])
nCells = len(latDeg)
ref.close()

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
    sc = ax.scatter(lonPlot, latDeg, c=data, cmap=cmap, s=10, vmin=vmin, vmax=vmax,
                    edgecolors="none", alpha=0.9, transform=ccrs.PlateCarree(), zorder=1)
    ax.plot([-180,180],[10,10],"k--",lw=1,alpha=0.3,transform=ccrs.PlateCarree())
    ax.plot([-180,180],[-10,-10],"k--",lw=1,alpha=0.3,transform=ccrs.PlateCarree())
    cb = fig.colorbar(sc, ax=ax, orientation="horizontal", shrink=0.6, pad=0.05, aspect=30)
    cb.set_label(label, fontsize=13)
    ax.set_title(title, fontsize=14, fontweight="bold")
    fig.savefig(os.path.join(OUT, fname), dpi=180, bbox_inches="tight", facecolor="white")
    plt.close()

print("Computing full GCCN fields...")
t2m_ns = avg_t2m(NS); t2m_sl = avg_t2m(SL)
rain_ns = get_rain(NS); rain_sl = get_rain(SL)
print("  Fluxes...")
vq_ns = get_vq(NS); vq_sl = get_vq(SL)

dt = t2m_sl - t2m_ns
dr = rain_sl - rain_ns
dvq = (vq_sl - vq_ns) * LV

# Key metrics
eq_mask = (latDeg >= -10) & (latDeg <= 10)
arctic_mask = latDeg >= 60
antarctic_mask = latDeg <= -60

eq_rain = np.average(dr[eq_mask], weights=areaCell[eq_mask])
arctic_t = np.average(dt[arctic_mask], weights=areaCell[arctic_mask])
antarctic_t = np.average(dt[antarctic_mask], weights=areaCell[antarctic_mask])

# Transport at 30N
lat30_mask = (latDeg >= 28) & (latDeg <= 32)
transport_30n = np.average(dvq[lat30_mask], weights=areaCell[lat30_mask])

print(f"\n=== Full GCCN Lifecycle Results ===")
print(f"  Equatorial rain change:  {eq_rain:+.3f} mm/day")
print(f"  30N transport change:    {transport_30n:+.0f} W/m (~ {transport_30n*2*3.14159*6.371e6*np.cos(np.radians(30))/1e12:+.0f} TW)")
print(f"  Arctic temperature:      {arctic_t:+.3f} K")
print(f"  Antarctic temperature:   {antarctic_t:+.3f} K")

# Temperature map
print("\n  Temp map...")
globe_map(dt,
    "Full GCCN Lifecycle: Temperature Change (CONTROL minus NO-SALT)\nHall 1980 E(R) | Beard 1976 V(R) | Condensational growth | Wet scavenging",
    "Temperature Change (K)", "fullgccn_map_temp.png", "RdBu_r", -2, 2)

# Precipitation map
print("  Precip map...")
globe_map(dr,
    "Full GCCN Lifecycle: Precipitation Change (CONTROL minus NO-SALT)\nGreen = more rain with salt | Rainforest emission only",
    "Precipitation Change (mm/day)", "fullgccn_map_precip.png", "BrBG", -2, 2)

# Heat flux map
print("  Flux map...")
globe_map(dvq,
    "Full GCCN Lifecycle: Latent Heat Flux Change (CONTROL minus NO-SALT)\nRed = more northward | Blue = more southward",
    "LH Flux Change (W/m)", "fullgccn_map_flux.png", "RdBu_r", -5e6, 5e6)

# 4-panel comparison: all phases
print("  Loading previous phases for comparison...")
# v7 25%
t2m_v7_ns = avg_t2m(os.path.join(BASE, "mpas30_nosalt"))
t2m_v7_25 = avg_t2m(os.path.join(BASE, "mpas30_025"))
rain_v7_ns = get_rain(os.path.join(BASE, "mpas30_nosalt"))
rain_v7_25 = get_rain(os.path.join(BASE, "mpas30_025"))
# v8 Twomey
t2m_v8_ns = avg_t2m(os.path.join(BASE, "results_v8_nosalt"))
t2m_v8_sl = avg_t2m(os.path.join(BASE, "results_v8_salt"))
rain_v8_ns = get_rain(os.path.join(BASE, "results_v8_nosalt"))
rain_v8_sl = get_rain(os.path.join(BASE, "results_v8_salt"))
# v8 simplified tracer
t2m_t2_ns = avg_t2m(os.path.join(BASE, "results_tracer2_nosalt"))
t2m_t2_sl = avg_t2m(os.path.join(BASE, "results_tracer2_salt"))
rain_t2_ns = get_rain(os.path.join(BASE, "results_tracer2_nosalt"))
rain_t2_sl = get_rain(os.path.join(BASE, "results_tracer2_salt"))

fig, axes = plt.subplots(2, 2, figsize=(16, 12))

# Panel 1: Temperature comparison all phases
ax = axes[0,0]
ax.plot(lat_c, bin_avg(t2m_v7_25 - t2m_v7_ns), color="#e67e22", lw=2, label="v7 autoconv 25%", alpha=0.7)
ax.plot(lat_c, bin_avg(t2m_v8_sl - t2m_v8_ns), color="#c0392b", lw=2, label="v8 Twomey", alpha=0.7)
ax.plot(lat_c, bin_avg(t2m_t2_sl - t2m_t2_ns), color="#7f8c8d", lw=2, ls="--", label="v8 GCCN simplified", alpha=0.7)
ax.plot(lat_c, bin_avg(dt), color="#2980b9", lw=3, label="v8 GCCN full lifecycle")
ax.set_xlabel("Latitude"); ax.set_ylabel("Temp Change (K)")
ax.set_title("Temperature Response — All Phases", fontweight="bold")
ax.legend(fontsize=9); ax.grid(True, alpha=0.3); ax.set_xlim(-80,80)
ax.axhline(y=0, color="k", lw=0.5)

# Panel 2: Precipitation comparison
ax = axes[0,1]
ax.plot(lat_c, bin_avg(rain_v7_25 - rain_v7_ns), color="#e67e22", lw=2, label="v7 autoconv 25%", alpha=0.7)
ax.plot(lat_c, bin_avg(rain_v8_sl - rain_v8_ns), color="#c0392b", lw=2, label="v8 Twomey", alpha=0.7)
ax.plot(lat_c, bin_avg(rain_t2_sl - rain_t2_ns), color="#7f8c8d", lw=2, ls="--", label="v8 GCCN simplified", alpha=0.7)
ax.plot(lat_c, bin_avg(dr), color="#2980b9", lw=3, label="v8 GCCN full lifecycle")
ax.set_xlabel("Latitude"); ax.set_ylabel("Precip Change (mm/day)")
ax.set_title("Precipitation Response — All Phases", fontweight="bold")
ax.legend(fontsize=9); ax.grid(True, alpha=0.3); ax.set_xlim(-80,80)
ax.axhline(y=0, color="k", lw=0.5)
ax.axvline(x=-10, color="gray", ls="--", alpha=0.4)
ax.axvline(x=10, color="gray", ls="--", alpha=0.4)

# Panel 3: Absolute precipitation
ax = axes[1,0]
ax.plot(lat_c, bin_avg(rain_ns), "k-", lw=2, label="Full GCCN NO-SALT")
ax.plot(lat_c, bin_avg(rain_sl), "b-", lw=2, label="Full GCCN CONTROL")
ax.set_xlabel("Latitude"); ax.set_ylabel("Precip (mm/day)")
ax.set_title("Full GCCN: Absolute Precipitation", fontweight="bold")
ax.legend(); ax.grid(True, alpha=0.3); ax.set_xlim(-80,80)

# Panel 4: Summary
ax = axes[1,1]; ax.axis("off")
txt = (f"FINAL MODEL: Full GCCN Lifecycle\n"
       f"MPAS v8.3.1, 30-day, 240km\n"
       f"Hall 1980 E(R), Beard 1976 V(R)\n"
       f"Condensational growth, wet scavenging\n"
       f"Salt: rainforest only (ivgtyp=2)\n\n"
       f"Eq rain:     {eq_rain:+.2f} mm/day\n"
       f"30N transport: {transport_30n*2*3.14159*6.371e6*np.cos(np.radians(30))/1e12:+.0f} TW\n"
       f"Arctic:      {arctic_t:+.2f} K\n"
       f"Antarctic:   {antarctic_t:+.2f} K\n\n"
       f"Comparison (eq rain):\n"
       f"  v7 autoconv:     -0.10 mm/day\n"
       f"  v8 Twomey:       +0.05 mm/day\n"
       f"  GCCN simplified: +0.19 mm/day\n"
       f"  GCCN full:       {eq_rain:+.2f} mm/day")
ax.text(0.05, 0.95, txt, transform=ax.transAxes, fontsize=10.5,
        verticalalignment="top", fontfamily="monospace",
        bbox=dict(boxstyle="round", facecolor="#e3f2fd", alpha=0.8))

fig.suptitle("Salt Aerosol Experiment — Full GCCN Lifecycle vs All Previous Phases",
             fontsize=16, fontweight="bold", y=1.01)
fig.tight_layout()
fig.savefig(os.path.join(OUT, "fullgccn_all_phases.png"), dpi=180, bbox_inches="tight", facecolor="white")
plt.close()

print("\nAll full GCCN plots saved!")
