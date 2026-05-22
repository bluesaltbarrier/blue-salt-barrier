#!/bin/bash
# =============================================================================
#  v5 July bundle — one-step Ubuntu setup
#
#  Reassembles the split Docker image, verifies it, loads it into Docker,
#  and optionally starts the container. Just run this script.
#
#  HOW TO RUN on Ubuntu:
#    - Easiest: open the folder in Files, right-click empty space ->
#      "Open in Terminal", then type:   bash SETUP_ubuntu.sh
#    - Or double-click: in Files -> menu -> Preferences -> Behavior ->
#      "Executable Text Files" -> "Run them", then double-click this file.
#    - Or from any terminal:   bash /path/to/SETUP_ubuntu.sh
# =============================================================================

cd "$(dirname "$0")" || exit 1

TAR="mpas8-v5-july.tar"
EXPECTED_MD5="795fbb5649dbc23ef15a10ec78a5f1a4"
IMAGE="mpas8-v5-july:latest"

pause() { echo; read -rp "Press Enter to close..." _; }

echo "=================================================================="
echo "  v5 July bundle — reassemble, verify, load"
echo "  working folder: $(pwd)"
echo "=================================================================="
echo

# --- 0. docker available? ----------------------------------------------------
DOCKER="docker"
if ! docker info >/dev/null 2>&1; then
  if sudo docker info >/dev/null 2>&1; then
    DOCKER="sudo docker"
    echo "[note] docker needs sudo on this machine — using 'sudo docker'."
  else
    echo "ERROR: Docker is not running or not installed."
    echo "Install Docker and make sure the daemon is started, then re-run."
    pause; exit 1
  fi
fi

# --- 1. check the 4 parts are present ----------------------------------------
for p in 00 01 02 03; do
  if [ ! -f "${TAR}.part.${p}" ]; then
    echo "ERROR: missing piece  ${TAR}.part.${p}"
    echo "All four parts (.part.00 .01 .02 .03) must be in this folder."
    pause; exit 1
  fi
done

# --- 2. reassemble (skip if a good tar is already here) ----------------------
if [ -f "$TAR" ] && [ "$(md5sum "$TAR" | cut -d' ' -f1)" = "$EXPECTED_MD5" ]; then
  echo "[1/4] $TAR already present and verified — skipping reassembly."
else
  echo "[1/4] reassembling 4 parts into $TAR  (this takes a minute)..."
  cat "${TAR}".part.* > "$TAR" || { echo "ERROR: reassembly failed (disk full?)."; pause; exit 1; }
  echo "      done."
fi

# --- 3. verify ----------------------------------------------------------------
echo "[2/4] verifying MD5 checksum..."
GOT="$(md5sum "$TAR" | cut -d' ' -f1)"
if [ "$GOT" != "$EXPECTED_MD5" ]; then
  echo "      MD5 MISMATCH — the tar is corrupt."
  echo "        expected: $EXPECTED_MD5"
  echo "        got:      $GOT"
  echo "      One of the .part. files copied incorrectly off the USB stick."
  echo "      Re-copy all four .part. files and run this script again."
  rm -f "$TAR"
  pause; exit 1
fi
echo "      OK — checksum matches ($GOT)."

# --- 4. docker load -----------------------------------------------------------
echo "[3/4] loading the image into Docker (this takes a few minutes)..."
$DOCKER load -i "$TAR" || { echo "ERROR: docker load failed."; pause; exit 1; }
echo "      image loaded: $IMAGE"

# --- 5. optionally start the container ---------------------------------------
echo
echo "[4/4] start the container now?"
echo "      The run needs a folder on a big local disk for output (~300 GB)."
echo "      Enter a path to use as the run folder, or just press Enter to skip."
read -rp "      run folder [default: \$HOME/v5run]: " RUNDIR
RUNDIR="${RUNDIR:-$HOME/v5run}"

if [ -n "$RUNDIR" ]; then
  mkdir -p "$RUNDIR"
  # remove any old container of the same name
  $DOCKER rm -f mpas8 >/dev/null 2>&1 || true
  $DOCKER run -d --name mpas8 -v "${RUNDIR}:/host" "$IMAGE" sleep infinity \
    && echo "      container 'mpas8' started, run output -> $RUNDIR"
fi

echo
echo "=================================================================="
echo "  SETUP COMPLETE"
echo "=================================================================="
echo
echo "  Next, run the ensemble steps (see README_v5_JULY.md for detail):"
echo
echo "    $DOCKER exec mpas8 bash /opt/july_v5/step0_check_prereqs.sh"
echo "    $DOCKER exec -it mpas8 bash /opt/july_v5/step1_download_gfs.sh"
echo "    $DOCKER exec mpas8 bash /opt/july_v5/step2_make_intermediates.sh"
echo "    $DOCKER exec mpas8 bash /opt/july_v5/step3_make_july_init.sh"
echo "    $DOCKER exec -d mpas8 bash /opt/july_v5/step4_run_july_ensemble.sh"
echo "    $DOCKER exec mpas8 python3 /opt/july_v5/step5_analyze_july.py"
echo
echo "  Step 4 is ~90 hours and resume-safe. Check progress with:"
echo "    $DOCKER exec mpas8 tail -20 /mpas/run_120km/pipeline_july_v5.log"
echo
echo "  You can delete the .part. files now to free space — the verified"
echo "  $TAR (and the loaded image) are all you need."
pause
