#!/bin/bash
# Step 3 — generate the 5 July 120 km pristine init files.
# Runs INSIDE the container:
#   docker exec mpas8 bash /opt/july_v5/step3_make_july_init.sh
#
# Reads  /host/v5_july/intermediates/FILE:YYYY-07-12_00
# Writes /opt/jul_120km/x1.40962.init.YYYY.july.pristine.nc  (5 files)
# Mesh files (x1.40962.static/grid/graph) are already in the image at /opt/.
# ---------------------------------------------------------------------------
set -e
export OMP_NUM_THREADS=1

YEARS="2021 2022 2023 2024 2025"
INTDIR=/host/v5_july/intermediates
OUTDIR=/opt/jul_120km
WORKDIR=/mpas/init_jul_120km_5yr
BUNDLE=/opt/july_v5

mkdir -p "$OUTDIR" "$WORKDIR"
cd "$WORKDIR"
LOG="${WORKDIR}/make_july_init.log"
echo "===== July 120 km init prep started $(date) =====" > "$LOG"

find_file () { for p in "$@"; do [ -f "$p" ] && { echo "$p"; return; }; done; echo ""; }
STATIC=$(find_file /opt/x1.40962.static.nc /opt/x1.40962/x1.40962.static.nc)
GRID=$(find_file   /opt/x1.40962.grid.nc   /opt/x1.40962/x1.40962.grid.nc)
GRAPH=$(find_file  /opt/x1.40962.graph.info.part.12 /opt/x1.40962/x1.40962.graph.info.part.12)
for v in STATIC GRID GRAPH; do
  [ -n "${!v}" ] || { echo "ERROR: 120 km $v file not found in image"; exit 1; }
done
echo "static: $STATIC | grid: $GRID | graph: $GRAPH" | tee -a "$LOG"

ln -sf /opt/MPAS-Model/init_atmosphere_model init_atmosphere_model
ln -sf "$STATIC" x1.40962.static.nc
ln -sf "$GRID"   x1.40962.grid.nc
ln -sf "$GRAPH"  x1.40962.graph.info.part.12

cat > streams.init_atmosphere <<'EOF'
<streams>
<immutable_stream name="input"  type="input"
                  filename_template="x1.40962.static.nc" input_interval="initial_only" />
<immutable_stream name="output" type="output"
                  filename_template="x1.40962.init.nc"
                  packages="initial_conds" output_interval="initial_only" />
</streams>
EOF

for YEAR in $YEARS; do
  echo | tee -a "$LOG"; echo "===== ${YEAR} =====" | tee -a "$LOG"; date | tee -a "$LOG"
  INT="${INTDIR}/FILE:${YEAR}-07-12_00"
  [ -f "$INT" ] || { echo "ERROR: intermediate missing: $INT (run Step 2)" | tee -a "$LOG"; exit 1; }
  rm -f FILE:* x1.40962.init.nc log.init_atmosphere.* namelist.init_atmosphere
  ln -sf "$INT" "FILE:${YEAR}-07-12_00"

  cat > namelist.init_atmosphere <<EOF
&nhyd_model
    config_init_case = 7
    config_start_time = '${YEAR}-07-12_00:00:00'
    config_stop_time = '${YEAR}-07-12_00:00:00'
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
  [ -f x1.40962.init.nc ] || { echo "  FAIL — log tail:"; tail -30 "log.init.${YEAR}.out"; exit 1; }

  RAW="x1.40962.init.${YEAR}.july.nc"
  PRISTINE="x1.40962.init.${YEAR}.july.pristine.nc"
  mv x1.40962.init.nc "$RAW"
  echo "  applying pristine modification..." | tee -a "$LOG"
  python3 "${BUNDLE}/make_pristine_init.py" "$RAW" "$PRISTINE" | tee -a "$LOG"
  mv "$RAW" "$PRISTINE" "$OUTDIR/"
  echo "  ${YEAR}: ${OUTDIR}/${PRISTINE}" | tee -a "$LOG"
done

echo | tee -a "$LOG"
echo "===== All July init files complete $(date) =====" | tee -a "$LOG"
ls -lh "$OUTDIR"/x1.40962.init.*.july.pristine.nc | tee -a "$LOG"
echo
echo " Next: Step 4 — docker exec mpas8 bash /opt/july_v5/step4_run_july_ensemble.sh"
