#!/bin/bash
# 120 km validation pair for the prescribed-CCN patch.
# Replicates the v3 §6.9 l=4 primary configuration: Jan 2025 start,
# Pohlker pristine init, Pohlker-Dg-matched activation (l=4).
# Uses the patched prescribed_ccn_{salt,nosalt} binaries.
#
# Pass criterion: SALT - NOSALT Amazon ΔP > 0 (matches v3 sign-flip claim)
# Compute estimate: ~6 hr per run, ~12 hr total.

set -e
export OMP_NUM_THREADS=1

WORKDIR=/mpas/run_120km
cd "$WORKDIR"

PIPELINE_LOG=/mpas/run_120km/pipeline_validation_2025_prescribed_ccn.log
echo "===== 120 km validation pair (2025, prescribed-CCN) started $(date) =====" > "$PIPELINE_LOG"

# Save original init.nc and swap in pristine
if [ ! -f x1.40962.init.gocart_backup.nc ]; then
   echo "Backing up current init.nc → x1.40962.init.gocart_backup.nc"
   cp x1.40962.init.nc x1.40962.init.gocart_backup.nc
fi
echo "Swapping pristine init in"
cp /opt/jan_120km/x1.40962.init.pristine.nc x1.40962.init.nc

# Make sure namelist is set for 2025-01-12 start
sed -i "s|config_start_time = .*|config_start_time = '2025-01-12_00:00:00'|" namelist.atmosphere

# --- SALT run ---
rm -f atmosphere_model history.*.nc diag.*.nc log.atmosphere.*
cp /mpas/run_120km/atmosphere_model.prescribed_ccn_salt atmosphere_model
echo "  SALT starting at $(date)"
echo "[$(date)] SALT starting" >> "$PIPELINE_LOG"
mpirun --allow-run-as-root --oversubscribe -np 12 ./atmosphere_model > log.salt.2025.prescribed_ccn.out 2>&1
echo "  SALT finished at $(date)"
echo "[$(date)] SALT finished" >> "$PIPELINE_LOG"

HOST_DIR=/host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_2025_prescribed_ccn_salt
mkdir -p "$HOST_DIR"
mv history.*.nc diag.*.nc "$HOST_DIR/" 2>/dev/null || true
cp log.atmosphere.0000.out log.salt.2025.prescribed_ccn.out "$HOST_DIR/" 2>/dev/null || true

# --- NOSALT run ---
rm -f atmosphere_model history.*.nc diag.*.nc log.atmosphere.*
cp /mpas/run_120km/atmosphere_model.prescribed_ccn_nosalt atmosphere_model
echo "  NOSALT starting at $(date)"
echo "[$(date)] NOSALT starting" >> "$PIPELINE_LOG"
mpirun --allow-run-as-root --oversubscribe -np 12 ./atmosphere_model > log.nosalt.2025.prescribed_ccn.out 2>&1
echo "  NOSALT finished at $(date)"
echo "[$(date)] NOSALT finished" >> "$PIPELINE_LOG"

HOST_DIR=/host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_2025_prescribed_ccn_nosalt
mkdir -p "$HOST_DIR"
mv history.*.nc diag.*.nc "$HOST_DIR/" 2>/dev/null || true
cp log.atmosphere.0000.out log.nosalt.2025.prescribed_ccn.out "$HOST_DIR/" 2>/dev/null || true

# Restore original init for safety
echo "Restoring original init.nc from backup"
cp x1.40962.init.gocart_backup.nc x1.40962.init.nc

echo
echo "===== 120 km validation pair complete ====="
echo "[$(date)] All complete" >> "$PIPELINE_LOG"
date
echo
echo "Outputs:"
ls -d /host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_2025_prescribed_ccn_{salt,nosalt}/ 2>/dev/null
