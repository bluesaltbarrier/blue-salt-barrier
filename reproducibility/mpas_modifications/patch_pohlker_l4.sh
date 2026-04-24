#!/bin/bash
# Build l=4 (160 nm diameter) binaries for the Pohlker-Dg-matched run pair.
# Thompson activ_ncloud indices: l=4 (0.08 um radius = 160 nm diameter), m=4 (kappa=0.8).
# Pohlker 2012 reports accumulation-mode Dg = 150 nm for pristine Amazon -
# l=4 is the closest available Thompson lookup option to this observed value.

set -e
THOMP=/opt/MPAS-Model/src/core_atmosphere/physics/physics_wrf/module_mp_thompson.F
INIT=/opt/MPAS-Model/src/core_atmosphere/physics/mpas_atmphys_init_microphysics.F

# --- Set Thompson activ_ncloud to l=4, m=4 (idempotent) ---
python3 << 'PYEOF'
THOMP = '/opt/MPAS-Model/src/core_atmosphere/physics/physics_wrf/module_mp_thompson.F'
with open(THOMP) as f: code = f.read()

marker = '!..The next two values are indexes of mean aerosol radius and'
idx = code.find(marker)
assert idx > 0, "activation-index block not found"
block = code[idx:idx+500]

# Replace whatever l=N is there with l=4
import re
new_block = re.sub(r'l = \d+  ![^\n]*', 'l = 4  ! Pohlker K-salt: 0.08 um radius (160 nm diam, matches Dg=150 nm)', block, count=1)
# Ensure m=4 is set
if 'm = 4' in new_block:
    pass  # already correct
else:
    new_block = re.sub(r'm = \d+  ![^\n]*', 'm = 4  ! Pohlker K-salt: kappa=0.8 (KCl)', new_block, count=1)

code = code[:idx] + new_block + code[idx+500:]
with open(THOMP, 'w') as f: f.write(code)
print("Thompson activ_ncloud patched to l=4, m=4")
PYEOF

# helper to set init-microphysics sentinel
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
  rm -f atmosphere_model
  make gfortran CORE=atmosphere PRECISION=single -j6 2>&1 | tail -15
  if [ ! -x /opt/MPAS-Model/atmosphere_model ]; then
    echo "ERROR: build for $label did not produce atmosphere_model binary -- aborting"
    exit 1
  fi
  cp atmosphere_model /mpas/run_120km/"$target_name"
  echo "built: $target_name ($(md5sum /mpas/run_120km/$target_name | cut -c1-8))"
}

# SALT variant (sentinel=2) and NOSALT variant (sentinel=-999)
build_binary SALT 2 atmosphere_model.pohlker_l4_salt
build_binary NOSALT -999 atmosphere_model.pohlker_l4_nosalt

echo "patch_pohlker_l4: DONE"
