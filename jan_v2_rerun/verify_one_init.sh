#!/bin/bash
# Quick one-shot verifier for the 2022 jan v2 init file.
# After step1 finishes, run this to confirm the pattern matches the
# 2025-style "IGBP-2 ~150, non-IGBP-2 ~thousands" target.
docker_exec_local() { docker exec mpas8 "$@"; }

INIT=/opt/jan_v2/x1.40962.init.2022.jan.pristine_v2.nc

if [ -n "${IN_CONTAINER:-}" ]; then
  FILE=$INIT
else
  # Called from host — re-enter container
  exec docker exec -e IN_CONTAINER=1 mpas8 bash /host/jan_v2_rerun/verify_one_init.sh
fi

python3 - <<PY
import netCDF4 as nc, numpy as np
ds = nc.Dataset("$FILE")
ivg = ds.variables['ivgtyp'][:]
if ivg.ndim == 2: ivg = ivg[0]
nwfa = ds.variables['nwfa'][0,:,:]
ig2 = (ivg == 2)
def cm3(arr, level): return float((arr[:,level]*1.15e-6).mean()) if arr.ndim==2 else float((arr*1.15e-6).mean())
g_s  = cm3(nwfa, 0)
i_s  = cm3(nwfa[ig2], 0) if ig2.any() else float('nan')
n_s  = cm3(nwfa[~ig2], 0)
i_cb = float((nwfa[ig2,5:9].mean(1)*1e-6).mean()) if ig2.any() else float('nan')
n_cb = float((nwfa[~ig2,5:9].mean(1)*1e-6).mean())
g_cb = float((nwfa[:,5:9].mean(1)*1e-6).mean())
print(f"Global  surface={g_s:7.0f} /cm3   cloud-base={g_cb:7.0f} /cm3")
print(f"IGBP-2  surface={i_s:7.0f} /cm3   cloud-base={i_cb:7.0f} /cm3")
print(f"non-IG2 surface={n_s:7.0f} /cm3   cloud-base={n_cb:7.0f} /cm3")
print()
print("PASS criteria (2025-style target):")
print(f"  IGBP-2 surface in [100, 250] /cm3 :  {'PASS' if 100<=i_s<=250 else 'FAIL'}")
print(f"  non-IGBP-2 surface > 600    /cm3 :  {'PASS' if n_s>600 else 'FAIL'}")
print(f"  global surface > 600        /cm3 :  {'PASS' if g_s>600 else 'FAIL'}")
PY
