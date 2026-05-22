#!/bin/bash
# Step 4 — run the v5 July 5-pair prescribed-CCN ensemble at 120 km.
# Runs INSIDE the container:
#   docker exec mpas8 bash /opt/july_v5/step4_run_july_ensemble.sh
#
# 5 years x (SALT + NOSALT), 30-day integrations. ~90 hours total at 12 cores.
# Uses the v4 prescribed-CCN binaries (baked in image at /mpas/run_120km/).
# Reads  /opt/jul_120km/x1.40962.init.YYYY.july.pristine.nc
# Writes /host/v5_july/simulation_outputs/results_120km_jul_pohlker_l4_YYYY_prescribed_ccn_{salt,nosalt}/
#
# RESUME-SAFE: a phase whose output dir already has >=25 history files is skipped.
# If a run dies, just re-launch this script.
# ---------------------------------------------------------------------------
set -e
export OMP_NUM_THREADS=1

YEARS="2021 2022 2023 2024 2025"
WORKDIR=/mpas/run_120km
INITDIR=/opt/jul_120km
OUTROOT=/host/v5_july/simulation_outputs
NPROC=12
mkdir -p "$OUTROOT"
cd "$WORKDIR"

SALT_BIN=/mpas/run_120km/atmosphere_model.prescribed_ccn_salt
NOSALT_BIN=/mpas/run_120km/atmosphere_model.prescribed_ccn_nosalt
for b in "$SALT_BIN" "$NOSALT_BIN"; do
  [ -f "$b" ] || { echo "ERROR: patched binary missing: $b"; exit 1; }
done

PIPELINE_LOG="${WORKDIR}/pipeline_july_v5.log"
echo "===== v5 July ensemble started $(date) =====" >> "$PIPELINE_LOG"

n_history () { ls "$1"/history.*.nc 2>/dev/null | wc -l; }

run_phase () {
  local YEAR=$1 PHASE=$2 BIN=$3
  local OUTDIR="${OUTROOT}/results_120km_jul_pohlker_l4_${YEAR}_prescribed_ccn_${PHASE}"
  if [ "$(n_history "$OUTDIR")" -ge 25 ]; then
    echo "  [$YEAR $PHASE] already complete — skipping"
    return
  fi
  mkdir -p "$OUTDIR"
  rm -f atmosphere_model history.*.nc diag.*.nc log.atmosphere.*
  cp "$BIN" atmosphere_model
  echo "  [$YEAR $PHASE] starting $(date)"
  echo "[$(date)] $YEAR $PHASE starting" >> "$PIPELINE_LOG"
  mpirun --allow-run-as-root --oversubscribe -np "$NPROC" ./atmosphere_model \
      > "log.${PHASE}.${YEAR}.out" 2>&1 || {
    echo "  [$YEAR $PHASE] FAILED — log tail:"; tail -25 "log.${PHASE}.${YEAR}.out"
    echo "[$(date)] $YEAR $PHASE FAILED" >> "$PIPELINE_LOG"; exit 1; }
  echo "  [$YEAR $PHASE] finished $(date)"
  echo "[$(date)] $YEAR $PHASE finished" >> "$PIPELINE_LOG"
  mv history.*.nc diag.*.nc "$OUTDIR/" 2>/dev/null || true
  cp log.atmosphere.0000.out "log.${PHASE}.${YEAR}.out" "$OUTDIR/" 2>/dev/null || true
}

for YEAR in $YEARS; do
  echo; echo "================ ${YEAR} pair ================"
  INIT_FILE="${INITDIR}/x1.40962.init.${YEAR}.july.pristine.nc"
  [ -f "$INIT_FILE" ] || { echo "ERROR: July init missing: $INIT_FILE (run Step 3)"; exit 1; }
  rm -f x1.40962.init.nc
  cp "$INIT_FILE" x1.40962.init.nc
  sed -i "s|config_start_time = .*|config_start_time = '${YEAR}-07-12_00:00:00'|" namelist.atmosphere
  run_phase "$YEAR" salt   "$SALT_BIN"
  run_phase "$YEAR" nosalt "$NOSALT_BIN"
  echo "  [$YEAR] pair complete"
done

echo; echo "===== v5 July ensemble COMPLETE $(date) ====="
echo "[$(date)] v5 July ensemble COMPLETE" >> "$PIPELINE_LOG"
ls -d "${OUTROOT}"/results_120km_jul_pohlker_l4_*_prescribed_ccn_* 2>/dev/null
echo
echo " Next: Step 5 — docker exec mpas8 python3 /opt/july_v5/step5_analyze_july.py"
