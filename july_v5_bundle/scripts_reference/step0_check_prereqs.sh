#!/bin/bash
# Step 0 — verify the mpas8 container has what the v5 July ensemble needs.
# Run INSIDE the container:  docker exec mpas8 bash /host_bundle/step0_check_prereqs.sh
#
# Reports PASS/FAIL for each prerequisite. Nothing is modified.

echo "=================================================================="
echo " v5 July ensemble — prerequisite check"
echo "=================================================================="
echo

MISSING=0

check_file () {
  if [ -f "$1" ]; then
    echo "  [PASS] $2"
    echo "         $1"
  else
    echo "  [FAIL] $2"
    echo "         missing: $1"
    MISSING=$((MISSING+1))
  fi
}

echo "--- Patched MPAS binaries (v4 prescribed-CCN) ---"
check_file /mpas/run_120km/atmosphere_model.prescribed_ccn_salt   "SALT binary"
check_file /mpas/run_120km/atmosphere_model.prescribed_ccn_nosalt "NOSALT binary"
echo

echo "--- init_atmosphere ---"
check_file /opt/MPAS-Model/init_atmosphere_model "init_atmosphere_model executable"
echo

echo "--- 120 km static / mesh files ---"
check_file /opt/x1.40962.static.nc            "120 km static file"
# grid + graph files live in a couple of possible places — check both
if [ -f /opt/x1.40962.grid.nc ] || [ -f /opt/x1.40962/x1.40962.grid.nc ]; then
  echo "  [PASS] 120 km grid file"
else
  echo "  [FAIL] 120 km grid file (x1.40962.grid.nc)"
  MISSING=$((MISSING+1))
fi
if [ -f /opt/x1.40962.graph.info.part.12 ] || [ -f /opt/x1.40962/x1.40962.graph.info.part.12 ]; then
  echo "  [PASS] 120 km graph partition (12-way)"
else
  echo "  [FAIL] 120 km graph partition x1.40962.graph.info.part.12"
  MISSING=$((MISSING+1))
fi
echo

echo "--- MPAS physics lookup tables (sample check) ---"
check_file /mpas/run/QNWFA_QNIFA_SIGMA_MONTHLY.dat "Thompson aerosol table"
check_file /mpas/run/CCN_ACTIVATE_DATA            "CCN activation table"
echo

echo "--- Python analysis stack ---"
if python3 -c "import netCDF4, numpy, scipy, matplotlib" 2>/dev/null; then
  echo "  [PASS] python3 + netCDF4 + numpy + scipy + matplotlib"
else
  echo "  [FAIL] python3 analysis stack incomplete"
  echo "         install with: pip3 install netCDF4 numpy scipy matplotlib"
  MISSING=$((MISSING+1))
fi
echo

echo "--- Disk space on /host ---"
df -h /host 2>/dev/null | tail -1
echo "         (need ~600 GB free for the full ensemble)"
echo

echo "=================================================================="
if [ "$MISSING" -eq 0 ]; then
  echo " ALL PREREQUISITES PRESENT — proceed to Step 1 (download_gfs)."
else
  echo " $MISSING prerequisite(s) missing."
  echo
  echo " If only the prescribed_ccn binaries are missing, the container"
  echo " predates v4 — build them with:"
  echo "     docker exec mpas8 bash /host_bundle/build_patched_binaries.sh"
  echo
  echo " If static/mesh files are missing, see REPRODUCE.md in the main"
  echo " repo for how to fetch the x1.40962 mesh from NCAR."
fi
echo "=================================================================="
