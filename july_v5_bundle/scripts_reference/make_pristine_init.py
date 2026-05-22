#!/usr/bin/env python3
"""
Build a pristine-Amazon init file for MPAS from an existing init.

Scales nwfa over IGBP-2 (evergreen broadleaf forest) cells so surface
concentration matches Pohlker 2012 observations of pristine Amazon
(~150/cm^3 without K-salt contribution). Vertical profile shape is
preserved by applying a per-cell scaling factor uniformly to all levels.

Usage:
    python3 make_pristine_init.py <input_init.nc> <output_init.nc>

Two output files recommended:
    x1.40962.init.pristine.nc    nwfa_surface = ~150/cm^3 over IGBP-2
                                 (used with both pohlker_salt and pohlker_nosalt
                                  binaries; salt binary doubles at init to 300/cm^3)
"""
import sys, shutil
import netCDF4 as nc
import numpy as np

TARGET_CM3 = 150.0       # target surface nwfa concentration (#/cm^3)
RHO_SFC = 1.15           # tropical surface air density (kg/m^3)
TARGET_PER_KG = TARGET_CM3 / (RHO_SFC * 1e-6)   # = 1.304e8 /kg

def main(src, dst):
    shutil.copy(src, dst)
    ds = nc.Dataset(dst, 'r+')
    ivgtyp = ds.variables['ivgtyp'][:]
    if ivgtyp.ndim == 2:
        ivgtyp = ivgtyp[0]
    nwfa = ds.variables['nwfa'][:]   # (Time, nCells, nLevels)
    nifa = ds.variables['nifa'][:]

    ig2 = (ivgtyp == 2)
    n_ig2 = int(ig2.sum())
    print(f"IGBP-2 cells to modify: {n_ig2}")
    if n_ig2 == 0:
        raise SystemExit("no IGBP-2 cells found")

    # per-cell scale factor: target_surface / current_surface
    current_sfc = nwfa[0, ig2, 0]             # surface level
    scale = TARGET_PER_KG / current_sfc       # shape (n_ig2,)

    # apply the same per-cell scale to every vertical level (preserves profile shape)
    nwfa_ig2 = nwfa[0, ig2, :] * scale[:, None]   # (n_ig2, nLevels)
    nwfa[0, ig2, :] = nwfa_ig2

    ds.variables['nwfa'][:] = nwfa

    # sanity: re-read and report
    new_sfc = ds.variables['nwfa'][0, ig2, 0]
    print(f"Before: IGBP-2 surface nwfa median = {np.median(current_sfc):.3e} /kg "
          f"({np.median(current_sfc)*RHO_SFC*1e-6:.0f} /cm^3)")
    print(f"After:  IGBP-2 surface nwfa median = {np.median(new_sfc):.3e} /kg "
          f"({np.median(new_sfc)*RHO_SFC*1e-6:.0f} /cm^3)")
    print(f"Target: {TARGET_PER_KG:.3e} /kg ({TARGET_CM3:.0f} /cm^3)")

    ds.sync(); ds.close()
    print(f"Wrote pristine init: {dst}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        raise SystemExit(1)
    main(sys.argv[1], sys.argv[2])
