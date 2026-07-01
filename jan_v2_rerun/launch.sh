#!/bin/bash
# Launch the whole Jan v2 pipeline: step 1 (build inits + verify) then
# step 2 (run 5 SALT/NOSALT pairs). Designed to be detached.
#
# Run from host:
#   docker exec -d mpas8 bash /host/jan_v2_rerun/launch.sh
#
# Check progress:
#   docker exec mpas8 tail -30 /mpas/run_120km/pipeline_jan_v2.log
set -e
LOG=/mpas/run_120km/pipeline_jan_v2.log
mkdir -p /mpas/run_120km
echo "===== Jan v2 launch: $(date) =====" >> "$LOG"
echo "[$(date)] step 1: build inits" >> "$LOG"
bash /host/jan_v2_rerun/step1_build_inits.sh >> "$LOG" 2>&1
echo "[$(date)] step 1 complete; step 2: ensemble run" >> "$LOG"
bash /host/jan_v2_rerun/step2_run_ensemble.sh >> "$LOG" 2>&1
echo "===== Jan v2 launch FINISHED: $(date) =====" >> "$LOG"
