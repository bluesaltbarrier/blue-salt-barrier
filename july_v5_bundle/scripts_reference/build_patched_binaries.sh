#!/bin/bash
# build_patched_binaries.sh — FALLBACK: rebuild the v4 prescribed-CCN binaries
# from MPAS source, inside the container.
#
#   docker exec mpas8 bash /host_bundle/build_patched_binaries.sh
#
# ===========================================================================
# USE extract_v4_binaries.sh INSTEAD IF YOU CAN.
# Copying the already-compiled binaries off the v4 desktop is faster and
# guaranteed bit-correct. Only use this rebuild path if the v4 desktop is
# unavailable and the slim container lacks the prescribed-CCN binaries.
# ===========================================================================
#
# This produces:
#   /mpas/run_120km/atmosphere_model.prescribed_ccn_salt
#   /mpas/run_120km/atmosphere_model.prescribed_ccn_nosalt
#
# Build recipe (see apply_prescribed_ccn_patch.py docstring + patch_pohlker_l4.sh):
#   1. set Thompson activation to l=4, m=4 (Pohlker-Dg-matched, kappa=0.8)
#   2. apply the prescribed-CCN source patch with IF_SALT = ".eq. 2", compile
#      -> save as prescribed_ccn_salt
#   3. re-apply the patch with IF_SALT = ".eq. -999", compile
#      -> save as prescribed_ccn_nosalt
#
# Compile time: ~30-60 min total (two builds).

set -e
BUNDLE=/host_bundle
SRC=/opt/MPAS-Model
RUN=/mpas/run_120km
mkdir -p "$RUN"

echo "=================================================================="
echo " Rebuilding v4 prescribed-CCN binaries from source"
echo "=================================================================="

if [ ! -d "$SRC" ]; then
  echo "ERROR: MPAS source tree not found at $SRC"
  echo "The slim container ships compiled binaries but may not include full"
  echo "source. In that case you must use extract_v4_binaries.sh from the v4"
  echo "desktop machine instead — there is no from-source path here."
  exit 1
fi

# --- Step 1: Thompson activation l=4, m=4 ---------------------------------
echo
echo "[1/3] Setting Thompson activation indices to l=4, m=4 ..."
# patch_pohlker_l4.sh contains the activ_ncloud edit. We run only that edit
# block by sourcing the python heredoc portion. The simplest robust approach:
# run the whole patch script but it ALSO builds pohlker_l4 binaries we discard.
# To avoid the wasted builds, apply just the Thompson edit here directly:
python3 - <<'PYEOF'
THOMP = '/opt/MPAS-Model/src/core_atmosphere/physics/physics_wrf/module_mp_thompson.F'
import re
with open(THOMP) as f: code = f.read()
marker = '!..The next two values are indexes of mean aerosol radius and'
idx = code.find(marker)
assert idx > 0, "activation-index block not found in module_mp_thompson.F"
block = code[idx:idx+500]
block = re.sub(r'l = \d+  ![^\n]*',
                'l = 4  ! Pohlker K-salt: 0.08 um radius (160 nm diam, Dg=150 nm)',
                block, count=1)
if 'm = 4' not in block:
    block = re.sub(r'm = \d+  ![^\n]*', 'm = 4  ! Pohlker K-salt: kappa=0.8 (KCl)',
                    block, count=1)
code = code[:idx] + block + code[idx+500:]
with open(THOMP, 'w') as f: f.write(code)
print("  Thompson activ_ncloud set to l=4, m=4")
PYEOF

# --- Step 2: SALT binary ---------------------------------------------------
echo
echo "[2/3] Building SALT binary (prescribed-CCN patch, IF_SALT = .eq. 2) ..."
# apply_prescribed_ccn_patch.py defaults to IF_SALT = ".eq. 2"
sed -i 's|^IF_SALT = .*|IF_SALT = ".eq. 2"|' "$BUNDLE/apply_prescribed_ccn_patch.py"
python3 "$BUNDLE/apply_prescribed_ccn_patch.py"
cd "$SRC"
rm -f atmosphere_model
make gfortran CORE=atmosphere PRECISION=single -j6 2>&1 | tail -12
if [ ! -x "$SRC/atmosphere_model" ]; then
  echo "ERROR: SALT build did not produce atmosphere_model"
  exit 1
fi
cp "$SRC/atmosphere_model" "$RUN/atmosphere_model.prescribed_ccn_salt"
echo "  built atmosphere_model.prescribed_ccn_salt"

# --- Step 3: NOSALT binary -------------------------------------------------
echo
echo "[3/3] Building NOSALT binary (prescribed-CCN patch, IF_SALT = .eq. -999) ..."
# Restore pristine source, then re-apply with the nosalt sentinel.
# The patch edits 3 files; re-running with the toggled sentinel is the
# documented procedure (see apply_prescribed_ccn_patch.py docstring).
sed -i 's|^IF_SALT = .*|IF_SALT = ".eq. -999"|' "$BUNDLE/apply_prescribed_ccn_patch.py"
python3 "$BUNDLE/apply_prescribed_ccn_patch.py"
cd "$SRC"
rm -f atmosphere_model
make gfortran CORE=atmosphere PRECISION=single -j6 2>&1 | tail -12
if [ ! -x "$SRC/atmosphere_model" ]; then
  echo "ERROR: NOSALT build did not produce atmosphere_model"
  exit 1
fi
cp "$SRC/atmosphere_model" "$RUN/atmosphere_model.prescribed_ccn_nosalt"
echo "  built atmosphere_model.prescribed_ccn_nosalt"

# restore the script's default for tidiness
sed -i 's|^IF_SALT = .*|IF_SALT = ".eq. 2"   # change to ".eq. -999" before recompiling for nosalt binary|' "$BUNDLE/apply_prescribed_ccn_patch.py"

echo
echo "=================================================================="
echo " DONE. Binaries in $RUN/:"
ls -lh "$RUN"/atmosphere_model.prescribed_ccn_* 2>/dev/null
echo
echo " IMPORTANT: verify the salt/nosalt binaries differ —"
echo "   md5sum $RUN/atmosphere_model.prescribed_ccn_*"
echo " If the two md5sums are identical the IF_SALT toggle did not take"
echo " effect; in that case use extract_v4_binaries.sh from the v4 desktop."
echo "=================================================================="
