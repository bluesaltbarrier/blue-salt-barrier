#!/bin/bash
# Validation run for the prescribed-CCN patch.
# 240 km mesh, Jan 2022, SALT then NOSALT pair.
# Outputs go to /host/GITIGNORE/simulation_outputs/results_240km_jan_l4_2022_prescribed_ccn_{salt,nosalt}/
#
# This is the "(B) plan" validation: confirm the patched binary holds nwfa
# at init pristine values throughout the 30-day run, before committing to
# the full 5-pair re-run.

set -e
export OMP_NUM_THREADS=1

WORKDIR=/mpas/run_240km_5yr
cd "$WORKDIR"

PIPELINE_LOG=/mpas/run_240km_5yr/pipeline_validation_2022_prescribed_ccn.log
echo "===== Validation pair (2022, prescribed-CCN) started $(date) =====" > "$PIPELINE_LOG"

# Year-specific init link
rm -f x1.10242.init.nc
ln -sf /opt/jan_5yr_pristine/x1.10242.init.2022.pristine.nc x1.10242.init.nc

# Year-specific namelist
cp /mpas/run/namelist.atmosphere namelist.atmosphere
sed -i "s|config_start_time = .*|config_start_time = '2022-01-12_00:00:00'|" namelist.atmosphere

# --- SALT run ---
rm -f atmosphere_model history.*.nc diag.*.nc log.atmosphere.*
cp /mpas/run_120km/atmosphere_model.prescribed_ccn_salt atmosphere_model
echo "  SALT starting at $(date)"
echo "[$(date)] SALT starting" >> "$PIPELINE_LOG"
mpirun --allow-run-as-root --oversubscribe -np 12 ./atmosphere_model > log.salt.2022.prescribed_ccn.out 2>&1
echo "  SALT finished at $(date)"
echo "[$(date)] SALT finished" >> "$PIPELINE_LOG"

HOST_DIR=/host/GITIGNORE/simulation_outputs/results_240km_jan_l4_2022_prescribed_ccn_salt
mkdir -p "$HOST_DIR"
mv history.*.nc diag.*.nc "$HOST_DIR/" 2>/dev/null || true
cp log.atmosphere.0000.out log.salt.2022.prescribed_ccn.out "$HOST_DIR/" 2>/dev/null || true

# --- NOSALT run ---
rm -f atmosphere_model history.*.nc diag.*.nc log.atmosphere.*
cp /mpas/run_120km/atmosphere_model.prescribed_ccn_nosalt atmosphere_model
echo "  NOSALT starting at $(date)"
echo "[$(date)] NOSALT starting" >> "$PIPELINE_LOG"
mpirun --allow-run-as-root --oversubscribe -np 12 ./atmosphere_model > log.nosalt.2022.prescribed_ccn.out 2>&1
echo "  NOSALT finished at $(date)"
echo "[$(date)] NOSALT finished" >> "$PIPELINE_LOG"

HOST_DIR=/host/GITIGNORE/simulation_outputs/results_240km_jan_l4_2022_prescribed_ccn_nosalt
mkdir -p "$HOST_DIR"
mv history.*.nc diag.*.nc "$HOST_DIR/" 2>/dev/null || true
cp log.atmosphere.0000.out log.nosalt.2022.prescribed_ccn.out "$HOST_DIR/" 2>/dev/null || true

echo
echo "===== Validation pair complete ====="
echo "[$(date)] All complete" >> "$PIPELINE_LOG"
date
echo
echo "Outputs:"
ls -d /host/GITIGNORE/simulation_outputs/results_240km_jan_l4_2022_prescribed_ccn_{salt,nosalt}/ 2>/dev/null
