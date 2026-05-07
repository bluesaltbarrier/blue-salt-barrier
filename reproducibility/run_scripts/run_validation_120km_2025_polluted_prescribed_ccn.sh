#!/bin/bash
# 120 km polluted-baseline validation pair for the prescribed-CCN patch.
# Replicates v3 §6.9's polluted column: GoCart-default init (NOT pristine),
# Pohlker-Dg-matched activation (l=4), Jan 2025 start.
# Tests v3's claim that pristine + salt gives +5.4 mm but
# polluted + salt gives -17 mm (full sign-flip).
#
# Compute estimate: ~22 hr total (matches the pristine pair we just did).

set -e
export OMP_NUM_THREADS=1

WORKDIR=/mpas/run_120km
cd "$WORKDIR"

PIPELINE_LOG=/mpas/run_120km/pipeline_validation_2025_polluted_prescribed_ccn.log
echo "===== 120 km POLLUTED validation pair (2025, prescribed-CCN) started $(date) =====" > "$PIPELINE_LOG"

# Restore GoCart-default init (was backed up when we swapped pristine in earlier).
if [ ! -f x1.40962.init.gocart_backup.nc ]; then
  echo "ERROR: gocart backup missing — cannot run polluted pair without it" >&2
  exit 1
fi
echo "Restoring GoCart-default init for polluted baseline"
cp x1.40962.init.gocart_backup.nc x1.40962.init.nc

sed -i "s|config_start_time = .*|config_start_time = '2025-01-12_00:00:00'|" namelist.atmosphere

# --- SALT run ---
rm -f atmosphere_model history.*.nc diag.*.nc log.atmosphere.*
cp /mpas/run_120km/atmosphere_model.prescribed_ccn_salt atmosphere_model
echo "  SALT starting at $(date)"
echo "[$(date)] SALT starting" >> "$PIPELINE_LOG"
mpirun --allow-run-as-root --oversubscribe -np 12 ./atmosphere_model > log.salt.2025.polluted.out 2>&1
echo "  SALT finished at $(date)"
echo "[$(date)] SALT finished" >> "$PIPELINE_LOG"

HOST_DIR=/host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_2025_polluted_prescribed_ccn_salt
mkdir -p "$HOST_DIR"
mv history.*.nc diag.*.nc "$HOST_DIR/" 2>/dev/null || true
cp log.atmosphere.0000.out log.salt.2025.polluted.out "$HOST_DIR/" 2>/dev/null || true

# --- NOSALT run ---
rm -f atmosphere_model history.*.nc diag.*.nc log.atmosphere.*
cp /mpas/run_120km/atmosphere_model.prescribed_ccn_nosalt atmosphere_model
echo "  NOSALT starting at $(date)"
echo "[$(date)] NOSALT starting" >> "$PIPELINE_LOG"
mpirun --allow-run-as-root --oversubscribe -np 12 ./atmosphere_model > log.nosalt.2025.polluted.out 2>&1
echo "  NOSALT finished at $(date)"
echo "[$(date)] NOSALT finished" >> "$PIPELINE_LOG"

HOST_DIR=/host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_2025_polluted_prescribed_ccn_nosalt
mkdir -p "$HOST_DIR"
mv history.*.nc diag.*.nc "$HOST_DIR/" 2>/dev/null || true
cp log.atmosphere.0000.out log.nosalt.2025.polluted.out "$HOST_DIR/" 2>/dev/null || true

echo
echo "===== 120 km polluted validation pair complete ====="
echo "[$(date)] All complete" >> "$PIPELINE_LOG"
date
echo
echo "Outputs:"
ls -d /host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_2025_polluted_prescribed_ccn_{salt,nosalt}/ 2>/dev/null
