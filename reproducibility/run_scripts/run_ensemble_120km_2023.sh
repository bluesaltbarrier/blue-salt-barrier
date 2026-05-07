#!/bin/bash
# 120 km ensemble run for Jan 2023, pristine baseline.
# Uses the patched prescribed_ccn_{salt,nosalt} binaries.
# Total compute: ~22 hr (~11 hr SALT + ~11 hr NOSALT).

set -e
export OMP_NUM_THREADS=1

# === SAFETY CHECK: refuse to run if another mpirun/atmosphere_model active ===
if pgrep -f "mpirun.*atmosphere_model" >/dev/null 2>&1 || \
   pgrep -f "^./atmosphere_model" >/dev/null 2>&1 || \
   pgrep -x "atmosphere_model" >/dev/null 2>&1; then
  echo "ABORT: another atmosphere_model is running. Refusing to launch 2023 to avoid clobbering."
  ps -ef | grep -E "mpirun|atmosphere_model" | grep -v grep
  exit 1
fi
# Also wait an extra 60 seconds after 2022's pipeline log shows "All complete"
# to ensure all cleanup operations and disk syncs have settled.
sleep 60

WORKDIR=/mpas/run_120km
cd "$WORKDIR"

PIPELINE_LOG=/mpas/run_120km/pipeline_ensemble_2023_120km.log
echo "===== 120 km ensemble Jan 2023 pristine started $(date) =====" > "$PIPELINE_LOG"

INIT_FILE=/opt/jan_120km/x1.40962.init.2023.pristine.nc
if [ ! -f "$INIT_FILE" ]; then
  echo "ERROR: $INIT_FILE not found" | tee -a "$PIPELINE_LOG"
  exit 1
fi
rm -f x1.40962.init.nc
cp "$INIT_FILE" x1.40962.init.nc

sed -i "s|config_start_time = .*|config_start_time = '2023-01-12_00:00:00'|" namelist.atmosphere

# --- SALT run ---
rm -f atmosphere_model history.*.nc diag.*.nc log.atmosphere.*
cp /mpas/run_120km/atmosphere_model.prescribed_ccn_salt atmosphere_model
echo "  SALT starting at $(date)"
echo "[$(date)] SALT starting" >> "$PIPELINE_LOG"
mpirun --allow-run-as-root --oversubscribe -np 12 ./atmosphere_model > log.salt.2023.out 2>&1
echo "  SALT finished at $(date)"
echo "[$(date)] SALT finished" >> "$PIPELINE_LOG"

HOST_DIR=/host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_2023_prescribed_ccn_salt
mkdir -p "$HOST_DIR"
mv history.*.nc diag.*.nc "$HOST_DIR/" 2>/dev/null || true
cp log.atmosphere.0000.out log.salt.2023.out "$HOST_DIR/" 2>/dev/null || true

# --- NOSALT run ---
rm -f atmosphere_model history.*.nc diag.*.nc log.atmosphere.*
cp /mpas/run_120km/atmosphere_model.prescribed_ccn_nosalt atmosphere_model
echo "  NOSALT starting at $(date)"
echo "[$(date)] NOSALT starting" >> "$PIPELINE_LOG"
mpirun --allow-run-as-root --oversubscribe -np 12 ./atmosphere_model > log.nosalt.2023.out 2>&1
echo "  NOSALT finished at $(date)"
echo "[$(date)] NOSALT finished" >> "$PIPELINE_LOG"

HOST_DIR=/host/GITIGNORE/simulation_outputs/results_120km_jan_pohlker_l4_2023_prescribed_ccn_nosalt
mkdir -p "$HOST_DIR"
mv history.*.nc diag.*.nc "$HOST_DIR/" 2>/dev/null || true
cp log.atmosphere.0000.out log.nosalt.2023.out "$HOST_DIR/" 2>/dev/null || true

echo
echo "===== 120 km ensemble Jan 2023 complete $(date) ====="
echo "[$(date)] All complete" >> "$PIPELINE_LOG"
