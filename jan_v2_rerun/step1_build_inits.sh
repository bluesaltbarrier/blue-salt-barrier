#!/bin/bash
# Step 1 — build the 5 January 120 km pristine init files using the
# CORRECT IGBP-2-only make_pristine_init.py (the v5-bundled, 2025-style).
#
# This replaces the v4 buggy global-uniform-pristine init files for
# 2022, 2023, 2024, 2026.  2025 is rebuilt for ensemble consistency.
#
# Reads  /opt/jan_intermediates_5yr/FILE:YYYY-01-12_00
# Writes /opt/jan_v2/x1.40962.init.YYYY.jan.pristine_v2.nc  (5 files)
#
# After each year's init builds, verifies:
#   - IGBP-2 surface nwfa ~150 /cm^3  (PASS within 100..250)
#   - non-IGBP-2 surface nwfa >> 150 /cm^3  (PASS > 600)
# Fails LOUDLY if any year drifts from the 2025-style spec.
# ---------------------------------------------------------------------------
set -e
export OMP_NUM_THREADS=1

YEARS="2022 2023 2024 2025 2026"
INTDIR=/opt/jan_intermediates_5yr
OUTDIR=/opt/jan_v2
WORKDIR=/mpas/init_jan_v2
SCRIPT=/opt/july_v5/make_pristine_init.py

mkdir -p "$OUTDIR" "$WORKDIR"
cd "$WORKDIR"
LOG="${WORKDIR}/build_inits.log"
echo "===== Jan v2 init prep started $(date) =====" > "$LOG"

ln -sf /opt/MPAS-Model/init_atmosphere_model init_atmosphere_model
ln -sf /opt/x1.40962.static.nc            x1.40962.static.nc
ln -sf /opt/x1.40962.grid.nc              x1.40962.grid.nc
ln -sf /opt/x1.40962.graph.info.part.12   x1.40962.graph.info.part.12

cat > streams.init_atmosphere <<'EOF'
<streams>
<immutable_stream name="input"  type="input"
                  filename_template="x1.40962.static.nc" input_interval="initial_only" />
<immutable_stream name="output" type="output"
                  filename_template="x1.40962.init.nc"
                  packages="initial_conds" output_interval="initial_only" />
</streams>
EOF

verify_init () {
  local FILE=$1
  python3 - "$FILE" <<'PY'
import sys, netCDF4 as nc, numpy as np
f = sys.argv[1]
ds = nc.Dataset(f)
ivg = ds.variables['ivgtyp'][:]
if ivg.ndim == 2: ivg = ivg[0]
nwfa = ds.variables['nwfa'][0,:,:]
ig2 = (ivg == 2)
glob = float((nwfa[:,0]*1.15e-6).mean())
ig2v = float((nwfa[ig2,0]*1.15e-6).mean()) if ig2.any() else float('nan')
nonv = float((nwfa[~ig2,0]*1.15e-6).mean())
print(f"  IGBP-2 surface = {ig2v:.0f} /cm^3   non-IGBP-2 surface = {nonv:.0f} /cm^3   global = {glob:.0f}")
ok = (100 <= ig2v <= 250) and (nonv > 600)
print("  VERIFY:", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
PY
}

for YEAR in $YEARS; do
  echo | tee -a "$LOG"
  echo "===== ${YEAR} =====" | tee -a "$LOG"
  date | tee -a "$LOG"

  RAW="${OUTDIR}/x1.40962.init.${YEAR}.jan.nc"
  PRISTINE="${OUTDIR}/x1.40962.init.${YEAR}.jan.pristine_v2.nc"

  if [ -f "$PRISTINE" ] && verify_init "$PRISTINE" >/dev/null 2>&1; then
    echo "  ${YEAR} already built and verified — skipping" | tee -a "$LOG"
    verify_init "$PRISTINE" | tee -a "$LOG"
    continue
  fi

  INT="${INTDIR}/FILE:${YEAR}-01-12_00"
  [ -f "$INT" ] || { echo "ERROR: intermediate missing: $INT" | tee -a "$LOG"; exit 1; }
  rm -f FILE:* x1.40962.init.nc log.init_atmosphere.* namelist.init_atmosphere
  ln -sf "$INT" "FILE:${YEAR}-01-12_00"

  cat > namelist.init_atmosphere <<EOF
&nhyd_model
    config_init_case = 7
    config_start_time = '${YEAR}-01-12_00:00:00'
    config_stop_time = '${YEAR}-01-12_00:00:00'
    config_theta_adv_order = 3
    config_coef_3rd_order = 0.25
    config_interface_projection = 'linear_interpolation'
/
&dimensions
    config_nvertlevels = 55
    config_nsoillevels = 4
    config_nfglevels = 38
    config_nfgsoillevels = 4
/
&data_sources
    config_geog_data_path = '/NOT_NEEDED'
    config_met_prefix = 'FILE'
    config_sfc_prefix = 'FILE'
    config_fg_interval = 21600
    config_landuse_data = 'MODIFIED_IGBP_MODIS_NOAH'
    config_soilcat_data = 'STATSGO'
    config_topo_data = 'GMTED2010'
    config_vegfrac_data = 'MODIS'
    config_albedo_data = 'MODIS'
    config_maxsnowalbedo_data = 'MODIS'
    config_supersample_factor = 3
    config_use_spechumd = false
/
&vertical_grid
    config_ztop = 30000.0
    config_nsmterrain = 1
    config_smooth_surfaces = true
    config_dzmin = 0.3
    config_nsm = 30
    config_tc_vertical_grid = true
    config_blend_bdy_terrain = false
/
&interpolation_control
    config_extrap_airtemp = 'lapse-rate'
/
&preproc_stages
    config_static_interp = false
    config_native_gwd_static = false
    config_native_gwd_gsl_static = false
    config_vertical_grid = true
    config_met_interp = true
    config_input_sst = false
    config_frac_seaice = true
/
&io
    config_pio_num_iotasks = 0
    config_pio_stride = 1
/
&decomposition
    config_block_decomp_file_prefix = 'x1.40962.graph.info.part.'
/
EOF

  echo "  running init_atmosphere..." | tee -a "$LOG"
  mpirun --allow-run-as-root --oversubscribe -np 12 ./init_atmosphere_model \
      > "log.init.${YEAR}.out" 2>&1 || true
  [ -f x1.40962.init.nc ] || { echo "  FAIL — log tail:" | tee -a "$LOG"; tail -30 "log.init.${YEAR}.out" | tee -a "$LOG"; exit 1; }
  mv x1.40962.init.nc "$RAW"

  # *** v4 BUG FIX *** : init_atmosphere with our streams config does not emit
  # nwfa/nifa.  If absent, MPAS falls back to a hard-coded globally-uniform
  # pristine default (~130 /cm^3), which is exactly the v4 2022/2023/2024/2026
  # bug.  We inject nwfa/nifa from the working 2025-style init that DOES have
  # them (monthly aerosol climatology is identical year-to-year on Jan 12).
  echo "  injecting nwfa/nifa from /opt/jan_120km/x1.40962.init.nc ..." | tee -a "$LOG"
  python3 - "$RAW" <<'PY' 2>&1 | tee -a "$LOG"
import sys, netCDF4 as nc
SRC = "/opt/jan_120km/x1.40962.init.nc"   # the working 2025 init (has nwfa)
dst_path = sys.argv[1]
src = nc.Dataset(SRC)
dst = nc.Dataset(dst_path, "r+")
for v in ("nwfa", "nifa"):
    if v not in src.variables:
        raise SystemExit(f"FATAL: source {SRC} has no {v}")
    sv = src.variables[v]
    if v in dst.variables:
        dst.variables[v][:] = sv[:]
        print(f"  overwrote {v}")
    else:
        new = dst.createVariable(v, sv.dtype, sv.dimensions)
        for a in sv.ncattrs(): new.setncattr(a, getattr(sv, a))
        new[:] = sv[:]
        print(f"  created {v}  shape={sv.shape}")
src.close(); dst.close()
PY

  echo "  applying make_pristine_init.py (IGBP-2 only)..." | tee -a "$LOG"
  python3 "$SCRIPT" "$RAW" "$PRISTINE" 2>&1 | tee -a "$LOG"

  echo "  verifying ${YEAR}..." | tee -a "$LOG"
  if ! verify_init "$PRISTINE" 2>&1 | tee -a "$LOG"; then
    echo "  *** ${YEAR} FAILED VERIFICATION — aborting pipeline ***" | tee -a "$LOG"
    exit 2
  fi
done

echo | tee -a "$LOG"
echo "===== All 5 January init files built and verified $(date) =====" | tee -a "$LOG"
ls -lh "$OUTDIR"/x1.40962.init.*.jan.pristine_v2.nc | tee -a "$LOG"
echo
echo " Next: step2_run_ensemble.sh"
