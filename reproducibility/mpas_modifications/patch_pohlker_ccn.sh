#!/bin/bash
# Path A: Pohlker-calibrated CCN perturbation.
# Replace the GCCN emission over rainforest with a modest (~2x) nwfa boost,
# representing biogenic K-salt as ordinary CCN (the mechanism Pohlker 2012
# actually documented). GCCN emission is zeroed so the GCCN lifecycle code
# is inert but remains available.

set -e
INIT=/opt/MPAS-Model/src/core_atmosphere/physics/mpas_atmphys_init_microphysics.F

python3 << 'PYEOF'
INIT = '/opt/MPAS-Model/src/core_atmosphere/physics/mpas_atmphys_init_microphysics.F'
with open(INIT) as f: code = f.read()

old = '''!------ BIOGENIC SALT GCCN EMISSION (rainforest only) ------
!   IGBP class 2 = Evergreen Broadleaf Forest (Amazon, Congo, SE Asia)
!   Emission rate: 1% of baseline nwfa2d rate, representing giant (~200 nm)
!   KCl nuclei emitted by tropical trees and associated fungi.
    if (salt_ivgtyp(iCell) .eq. 2) then
       ngccn2d(iCell) = nwfa2d(iCell) * 0.01_RKIND
       ngccn(k,iCell) = nwfa(k,iCell) * 0.01_RKIND
    else
       ngccn2d(iCell) = 0._RKIND
       ngccn(k,iCell) = 0._RKIND
    end if
!------ END BIOGENIC SALT GCCN EMISSION ------'''

new = '''!------ BIOGENIC K-SALT CCN ENHANCEMENT (Pohlker 2012 calibrated) ------
!   IGBP class 2 = Evergreen Broadleaf Forest (Amazon, Congo, SE Asia).
!   Pohlker et al. Science 2012 documented that rainforest K-salt particles
!   are 0.1-1 um diameter accumulation-mode CCN (NOT giant CCN), acting as
!   seeds for SOA growth. The perturbation below doubles nwfa and nwfa2d over
!   IGBP-2 cells, representing the biogenic-salt-enabled portion of pristine
!   Amazon CCN. The 2x factor corresponds to ~50% of accumulation-mode CCN
!   being dependent on K-salt seeding (Pohlker text S2.4, K fraction of OA
!   particles median ~2.6 percent, 50 ng m-3 atmospheric K concentration).
    if (salt_ivgtyp(iCell) .eq. 2) then
       nwfa2d(iCell) = nwfa2d(iCell) * 2.0_RKIND
       nwfa(k,iCell) = nwfa(k,iCell) * 2.0_RKIND
    end if
!   GCCN pathway kept inert: no biogenic giant-mode observed in Pohlker.
    ngccn2d(iCell) = 0._RKIND
    ngccn(k,iCell) = 0._RKIND
!------ END BIOGENIC K-SALT CCN ENHANCEMENT ------'''

assert old in code, "block not found"
code = code.replace(old, new, 1)
with open(INIT, 'w') as f: f.write(code)
print("Init patched to Pohlker CCN mode")
PYEOF

echo "Verify patch:"
grep -A2 'BIOGENIC K-SALT' $INIT | head -20
