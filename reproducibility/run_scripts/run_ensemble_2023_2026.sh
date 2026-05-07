#!/bin/bash
# Variance ensemble: 4 remaining year-pairs (2023, 2024, 2025, 2026) at
# 240 km l=4 Pohlker-Dg-matched pristine. SALT then NOSALT for each year.
# 2022 already done as the validation pair.
#
# Total compute: ~16 hours wall time at 12 cores.
# Outputs land in /host/GITIGNORE/simulation_outputs/results_240km_jan_l4_<year>_{salt,nosalt}/
#
# Run inside the mpas8 container.

set -e
export OMP_NUM_THREADS=1

WORKDIR=/mpas/run_240km_5yr
mkdir -p "$WORKDIR"
cd "$WORKDIR"

# Common static resources (only need to link once)
ln -sf /opt/x1.10242/x1.10242.graph.info x1.10242.graph.info
ln -sf /opt/x1.10242/x1.10242.graph.info.part.12 x1.10242.graph.info.part.12
ln -sf /opt/x1.10242/x1.10242.static.nc x1.10242.static.nc
for f in CAM_ABS_DATA.DBL CAM_AEROPT_DATA.DBL GENPARM.TBL LANDUSE.TBL OZONE_DAT.TBL OZONE_LAT.TBL OZONE_PLEV.TBL RRTMG_LW_DATA RRTMG_LW_DATA.DBL RRTMG_SW_DATA RRTMG_SW_DATA.DBL SOILPARM.TBL VEGPARM.TBL VERSION CCN_ACTIVATE_DATA MP_THOMPSON_QIautQS_DATA.DBL MP_THOMPSON_QRacrQG_DATA.DBL MP_THOMPSON_QRacrQS_DATA.DBL MP_THOMPSON_freezeH2O_DATA.DBL QNWFA_QNIFA_SIGMA_MONTHLY.dat stream_list.atmosphere.diagnostics stream_list.atmosphere.output stream_list.atmosphere.surface; do
  ln -sf /mpas/run/${f} ${f} 2>/dev/null || true
done

# Common streams config
cp /mpas/run/streams.atmosphere streams.atmosphere

PIPELINE_LOG=/mpas/run_240km_5yr/pipeline_2023_2026.log
echo "===== Variance ensemble pipeline started $(date) =====" > "$PIPELINE_LOG"

run_year_pair () {
  local YEAR=$1

  echo
  echo "===== ${YEAR} pair starting ====="
  echo "[$(date)] ${YEAR} pair starting" >> "$PIPELINE_LOG"

  # Year-specific init link (pristine init applied per make_pristine_init.py)
  rm -f x1.10242.init.nc
  ln -sf /opt/jan_5yr_pristine/x1.10242.init.${YEAR}.pristine.nc x1.10242.init.nc

  # Year-specific namelist: same template as 2022, only the start date changes
  cp /mpas/run/namelist.atmosphere namelist.atmosphere
  sed -i "s|config_start_time = .*|config_start_time = '${YEAR}-01-12_00:00:00'|" namelist.atmosphere

  # --- SALT run ---
  rm -f atmosphere_model history.*.nc diag.*.nc log.atmosphere.*
  cp /mpas/run_120km/atmosphere_model.pohlker_l4_salt atmosphere_model
  echo "  ${YEAR} SALT starting at $(date)"
  echo "[$(date)] ${YEAR} SALT starting" >> "$PIPELINE_LOG"
  mpirun --allow-run-as-root --oversubscribe -np 12 ./atmosphere_model > log.salt.${YEAR}.out 2>&1
  echo "  ${YEAR} SALT finished at $(date)"
  echo "[$(date)] ${YEAR} SALT finished" >> "$PIPELINE_LOG"

  HOST_DIR=/host/GITIGNORE/simulation_outputs/results_240km_jan_l4_${YEAR}_salt
  mkdir -p "$HOST_DIR"
  mv history.*.nc diag.*.nc "$HOST_DIR/" 2>/dev/null || true
  cp log.atmosphere.0000.out log.salt.${YEAR}.out "$HOST_DIR/" 2>/dev/null || true

  # --- NOSALT run ---
  rm -f atmosphere_model history.*.nc diag.*.nc log.atmosphere.*
  cp /mpas/run_120km/atmosphere_model.pohlker_l4_nosalt atmosphere_model
  echo "  ${YEAR} NOSALT starting at $(date)"
  echo "[$(date)] ${YEAR} NOSALT starting" >> "$PIPELINE_LOG"
  mpirun --allow-run-as-root --oversubscribe -np 12 ./atmosphere_model > log.nosalt.${YEAR}.out 2>&1
  echo "  ${YEAR} NOSALT finished at $(date)"
  echo "[$(date)] ${YEAR} NOSALT finished" >> "$PIPELINE_LOG"

  HOST_DIR=/host/GITIGNORE/simulation_outputs/results_240km_jan_l4_${YEAR}_nosalt
  mkdir -p "$HOST_DIR"
  mv history.*.nc diag.*.nc "$HOST_DIR/" 2>/dev/null || true
  cp log.atmosphere.0000.out log.nosalt.${YEAR}.out "$HOST_DIR/" 2>/dev/null || true

  echo "  ${YEAR} pair complete: outputs in /host/GITIGNORE/simulation_outputs/results_240km_jan_l4_${YEAR}_{salt,nosalt}/"
  echo "[$(date)] ${YEAR} pair COMPLETE" >> "$PIPELINE_LOG"
}

for YEAR in 2023 2024 2025 2026; do
  run_year_pair ${YEAR}
done

echo
echo "===== All 4 ensemble pairs complete ====="
echo "[$(date)] All 4 pairs complete" >> "$PIPELINE_LOG"
date
echo
echo "Pipeline log: $PIPELINE_LOG"
echo "Output directories:"
ls -d /host/GITIGNORE/simulation_outputs/results_240km_jan_l4_202[3-6]_{salt,nosalt}/ 2>/dev/null
