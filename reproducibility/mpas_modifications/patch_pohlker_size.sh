#!/bin/bash
# Build two new binaries with Thompson CCN activation indices set to
# Pohlker K-salt size+hygroscopicity:
#   l = 5  -> ta_Ra(5) = 0.16 um radius (320 nm diameter)
#   m = 4  -> ta_Ka(4) = 0.8 hygroscopicity (KCl-like)
#
# Caveat: this applies globally (all aerosols modeled as K-salt-like).
# SALT-NOSALT contrast over IGBP-2 still isolates K-salt number effect;
# non-Amazon regions will have off climate.
#
# Builds both variants:
#   atmosphere_model.pohlker_size_salt   (2x over IGBP-2 + l=5, m=4)
#   atmosphere_model.pohlker_size_nosalt (no 2x + l=5, m=4)

set -e
THOMP=/opt/MPAS-Model/src/core_atmosphere/physics/physics_wrf/module_mp_thompson.F
INIT=/opt/MPAS-Model/src/core_atmosphere/physics/mpas_atmphys_init_microphysics.F

# --- Modify activ_ncloud indices to K-salt values (idempotent) ---
python3 << 'PYEOF'
THOMP = '/opt/MPAS-Model/src/core_atmosphere/physics/physics_wrf/module_mp_thompson.F'
with open(THOMP) as f: code = f.read()

marker = '!..The next two values are indexes of mean aerosol radius and'
idx = code.find(marker)
assert idx > 0, "activation-index block not found"
block = code[idx:idx+500]
if 'l = 5' in block and 'm = 4' in block:
    print("Thompson activ_ncloud already patched (l=5, m=4) — skipping")
else:
    assert 'l = 3' in block and 'm = 2' in block, "expected l=3/m=2 defaults not present"
    new_block = block.replace('      l = 3', '      l = 5  ! Pohlker K-salt: 0.16 um radius (320 nm diam)', 1)
    new_block = new_block.replace('      m = 2', '      m = 4  ! Pohlker K-salt: kappa=0.8 (KCl)', 1)
    code = code[:idx] + new_block + code[idx+500:]
    with open(THOMP, 'w') as f: f.write(code)
    print("Thompson activ_ncloud patched: l=5, m=4 globally")
PYEOF

# helper: set init-microphysics Pohlker sentinel to 2 (salt) or -999 (nosalt)
set_sentinel() {
  local val="$1"
  python3 -c "
INIT='/opt/MPAS-Model/src/core_atmosphere/physics/mpas_atmphys_init_microphysics.F'
with open(INIT) as f: code=f.read()
import re
code = re.sub(r'if \(salt_ivgtyp\(iCell\) \.eq\. -?\d+\)', 'if (salt_ivgtyp(iCell) .eq. $val)', code, count=1)
with open(INIT,'w') as f: f.write(code)
print('init sentinel ->', '$val')
"
}

build_binary() {
  local label="$1"
  local sentinel="$2"
  local target_name="$3"
  set_sentinel "$sentinel"
  cd /opt/MPAS-Model
  rm -f atmosphere_model   # ensure we notice if build fails
  make gfortran CORE=atmosphere PRECISION=single -j6 2>&1 | tail -30
  if [ ! -x /opt/MPAS-Model/atmosphere_model ]; then
    echo "ERROR: build for $label did not produce atmosphere_model binary — aborting"
    exit 1
  fi
  cp atmosphere_model /mpas/run_120km/"$target_name"
  echo "built: $target_name ($(md5sum /mpas/run_120km/$target_name | cut -c1-8))"
}

# --- Build SALT variant (sentinel = 2, l=5, m=4) ---
build_binary SALT 2 atmosphere_model.pohlker_size_salt

# --- Build NOSALT variant (sentinel = -999, l=5, m=4) ---
build_binary NOSALT -999 atmosphere_model.pohlker_size_nosalt

# --- Restore source to pristine-pair ready state (sentinel = -999 for pohlker_nosalt) ---
# (source l=5, m=4 remains for now; will be reverted separately if needed)
echo "patch_pohlker_size: DONE"
