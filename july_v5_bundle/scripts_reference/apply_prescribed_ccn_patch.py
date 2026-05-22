#!/usr/bin/env python3
"""
Apply prescribed-CCN patch to MPAS source.

Approach (Heikenfeld 2019 ACP, Sun 2024 GMD precedent):
  - Disable Thompson surface-emission feedback by setting nwfa2d=0
  - Save init nwfa/nifa/ngccn 3D profile to module-level arrays
  - On every microphysics call, override MPAS-state nwfa/nifa/ngccn with
    saved init values (both on MPAS-to-driver and driver-to-MPAS paths),
    so Thompson always sees the init pristine profile and dycore-advected
    drift is reset every physics step.

Salt vs nosalt experimental contrast is preserved at init time:
  - SALT compile uses `.eq. 2` (matches IGBP-2), apply 2x perturbation to
    nwfa over all vertical levels in IGBP-2 cells before saving the init.
  - NOSALT compile uses `.eq. -999` (no-op).

Files modified:
  - mpas_atmphys_vars.F                       (add saved-init arrays)
  - mpas_atmphys_init_microphysics.F          (zero nwfa2d, save init)
  - mpas_atmphys_interface.F                  (override MPAS-state on copy)

Caller is expected to compile twice (once with .eq. 2 for salt binary,
once with .eq. -999 for nosalt binary). This script writes the .eq. 2
form by default; toggle the IF_SALT variable to switch.
"""
import os
import re
import sys

PHYS = "/opt/MPAS-Model/src/core_atmosphere/physics"
VARS = f"{PHYS}/mpas_atmphys_vars.F"
INIT = f"{PHYS}/mpas_atmphys_init_microphysics.F"
INTF = f"{PHYS}/mpas_atmphys_interface.F"

IF_SALT = ".eq. 2"   # change to ".eq. -999" before recompiling for nosalt binary

# ---------- File 1: mpas_atmphys_vars.F ----------
with open(VARS, "r") as f:
    vars_src = f.read()

if "nwfa_init_saved" in vars_src:
    print(f"[skip] {VARS}: already patched")
else:
    # Insert the new declarations right after the existing ngccn_p declaration block.
    needle = ( " real(kind=RKIND),dimension(:,:,:),allocatable:: &\n"
               "    nifa_p,           &!\"ice-friendly\" number concentration                                                 [#/kg]\n"
               "    nwfa_p,           &!\"water-friendly\" number concentration                                               [#/kg]\n"
               "    ngccn_p            !giant CCN salt aerosol number concentration                                               [#/kg]\n" )
    addition = ( "\n"
                 "!... Prescribed-CCN saved init profile (Heikenfeld 2019 ACP precedent):\n"
                 " real(kind=RKIND),dimension(:,:),allocatable:: &\n"
                 "    nwfa_init_saved,  &!saved init nwfa(k,iCell) for prescribed-CCN reset\n"
                 "    nifa_init_saved,  &!saved init nifa(k,iCell) for prescribed-CCN reset\n"
                 "    ngccn_init_saved   !saved init ngccn(k,iCell) for prescribed-CCN reset\n" )
    if needle not in vars_src:
        sys.exit(f"FAIL: needle not found in {VARS}")
    vars_src_new = vars_src.replace(needle, needle + addition)
    with open(VARS, "w") as f:
        f.write(vars_src_new)
    print(f"[ok]   {VARS}: added nwfa_init_saved declarations")

# ---------- File 2: mpas_atmphys_init_microphysics.F ----------
with open(INIT, "r") as f:
    init_src = f.read()

if "nwfa_init_saved" in init_src:
    print(f"[skip] {INIT}: already patched")
else:
    # Add USE for vars module (needed for nwfa_init_saved arrays).
    use_old = " use mpas_atmphys_utilities\n"
    use_new = " use mpas_atmphys_utilities\n use mpas_atmphys_vars, only: nwfa_init_saved, nifa_init_saved, ngccn_init_saved\n"
    if use_old in init_src and "mpas_atmphys_vars" not in init_src:
        init_src = init_src.replace(use_old, use_new)

    # Replace the entire surface-emission/salt-perturbation block (lines ~244-268).
    old_block = (
        " k = 1\n"
        " do iCell = 1, nCellsSolve\n"
        "    airmass = rho_zz(k,iCell)*zz(k,iCell)\n"
        "    airmass = airmass*(zgrid(k+1,iCell)-zgrid(k,iCell))*areaCell(iCell) ! (in kg)\n"
        "    nwfa2d(iCell) = nwfa(k,iCell)*0.000196*airmass*0.5e-10\n"
        "    nifa2d(iCell) = 0._RKIND\n"
        "!------ BIOGENIC K-SALT CCN ENHANCEMENT (Pohlker 2012 calibrated) ------\n"
        "!   IGBP class 2 = Evergreen Broadleaf Forest (Amazon, Congo, SE Asia).\n"
        "!   Pohlker et al. Science 2012 documented that rainforest K-salt particles\n"
        "!   are 0.1-1 um diameter accumulation-mode CCN (NOT giant CCN), acting as\n"
        "!   seeds for SOA growth. The perturbation below doubles nwfa and nwfa2d over\n"
        "!   IGBP-2 cells, representing the biogenic-salt-enabled portion of pristine\n"
        "!   Amazon CCN. The 2x factor corresponds to ~50% of accumulation-mode CCN\n"
        "!   being dependent on K-salt seeding (Pohlker text S2.4, K fraction of OA\n"
        "!   particles median ~2.6 percent, 50 ng m-3 atmospheric K concentration).\n"
        "    if (salt_ivgtyp(iCell) .eq. -999) then\n"
        "       nwfa2d(iCell) = nwfa2d(iCell) * 2.0_RKIND\n"
        "       nwfa(k,iCell) = nwfa(k,iCell) * 2.0_RKIND\n"
        "    end if\n"
        "!   GCCN pathway kept inert: no biogenic giant-mode observed in Pohlker.\n"
        "    ngccn2d(iCell) = 0._RKIND\n"
        "    ngccn(k,iCell) = 0._RKIND\n"
        "!------ END BIOGENIC K-SALT CCN ENHANCEMENT ------\n"
        "!   call mpas_log_write('$i $r $r $r',intArgs=(/iCell/),realArgs=(/airmass,nwfa2d(iCell),nifa2d(iCell)/))\n"
        " enddo\n"
    )
    new_block = (
        "!------ PRESCRIBED-CCN PATCH (Heikenfeld 2019 ACP, Sun 2024 GMD) ------\n"
        "!   Disable Thompson surface-emission feedback. nwfa2d=0 means the \"fake\n"
        "!   sfc source\" injection in module_mp_thompson.F line 1227 becomes a\n"
        "!   no-op. nwfa is held at init pristine profile via reset in the\n"
        "!   mpas_atmphys_interface.F driver-to-MPAS copy block.\n"
        "!\n"
        "!   Salt vs nosalt experimental contrast: in the SALT-compile binary the\n"
        "!   conditional below uses `.eq. 2` and applies a 2x enhancement to nwfa\n"
        "!   over ALL vertical levels in IGBP-2 (Evergreen Broadleaf Forest)\n"
        "!   cells. In the NOSALT-compile binary the conditional uses `.eq. -999`\n"
        "!   (sentinel; no real ivgtyp value matches), making it a no-op.\n"
        " do iCell = 1, nCellsSolve\n"
        "    nwfa2d(iCell) = 0._RKIND\n"
        "    nifa2d(iCell) = 0._RKIND\n"
        "    ngccn2d(iCell) = 0._RKIND\n"
        f"    if (salt_ivgtyp(iCell) {IF_SALT}) then\n"
        "       do k = 1, nVertLevels\n"
        "          nwfa(k,iCell) = nwfa(k,iCell) * 2.0_RKIND\n"
        "       enddo\n"
        "    end if\n"
        "    do k = 1, nVertLevels\n"
        "       ngccn(k,iCell) = 0._RKIND\n"
        "    enddo\n"
        " enddo\n"
        "\n"
        "!... Save the init nwfa/nifa/ngccn 3D profile for prescribed-CCN reset.\n"
        " if (.not. allocated(nwfa_init_saved)) then\n"
        "    allocate(nwfa_init_saved(nVertLevels, nCellsSolve))\n"
        "    allocate(nifa_init_saved(nVertLevels, nCellsSolve))\n"
        "    allocate(ngccn_init_saved(nVertLevels, nCellsSolve))\n"
        " endif\n"
        " do iCell = 1, nCellsSolve\n"
        "    do k = 1, nVertLevels\n"
        "       nwfa_init_saved(k,iCell) = nwfa(k,iCell)\n"
        "       nifa_init_saved(k,iCell) = nifa(k,iCell)\n"
        "       ngccn_init_saved(k,iCell) = ngccn(k,iCell)\n"
        "    enddo\n"
        " enddo\n"
        " call mpas_log_write('--- Prescribed-CCN: nwfa2d zeroed, init saved for reset.')\n"
        "!------ END PRESCRIBED-CCN PATCH ------\n"
    )
    if old_block not in init_src:
        sys.exit(f"FAIL: old_block not found in {INIT}")
    # Need to also import vars module for the saved arrays
    init_src_new = init_src.replace(old_block, new_block)
    with open(INIT, "w") as f:
        f.write(init_src_new)
    print(f"[ok]   {INIT}: replaced surface-emission block with prescribed-CCN block")

# ---------- File 3: mpas_atmphys_interface.F ----------
with open(INTF, "r") as f:
    intf_src = f.read()

if "nwfa_init_saved" in intf_src:
    print(f"[skip] {INTF}: already patched")
else:
    # Override MPAS-to-driver copy (line ~705-707):
    old_to_drv = (
        "                   nifa_p(i,k,j)  = nifa(k,i)\n"
        "                   nwfa_p(i,k,j)  = nwfa(k,i)\n"
        "                   ngccn_p(i,k,j) = ngccn_s(k,i)\n"
    )
    new_to_drv = (
        "                   ! Prescribed-CCN: feed Thompson the saved init pristine profile\n"
        "                   nifa_p(i,k,j)  = nifa_init_saved(k,i)\n"
        "                   nwfa_p(i,k,j)  = nwfa_init_saved(k,i)\n"
        "                   ngccn_p(i,k,j) = ngccn_init_saved(k,i)\n"
    )
    if old_to_drv not in intf_src:
        sys.exit(f"FAIL: MPAS-to-driver block not found in {INTF}")
    intf_src = intf_src.replace(old_to_drv, new_to_drv)

    # Override driver-to-MPAS write-back (line ~979-981):
    old_to_mpas = (
        "                      nc(k,i)    = nc_p(i,k,j)\n"
        "                      nifa(k,i)  = nifa_p(i,k,j)\n"
        "                      nwfa(k,i)  = nwfa_p(i,k,j)\n"
        "                      ngccn_s(k,i) = ngccn_p(i,k,j)\n"
    )
    new_to_mpas = (
        "                      nc(k,i)    = nc_p(i,k,j)\n"
        "                      ! Prescribed-CCN: reset MPAS-state nwfa/nifa/ngccn to saved init\n"
        "                      nifa(k,i)  = nifa_init_saved(k,i)\n"
        "                      nwfa(k,i)  = nwfa_init_saved(k,i)\n"
        "                      ngccn_s(k,i) = ngccn_init_saved(k,i)\n"
    )
    if old_to_mpas not in intf_src:
        sys.exit(f"FAIL: driver-to-MPAS block not found in {INTF}")
    intf_src = intf_src.replace(old_to_mpas, new_to_mpas)

    with open(INTF, "w") as f:
        f.write(intf_src)
    print(f"[ok]   {INTF}: overrode MPAS-to-driver and driver-to-MPAS copies")

print()
print(f"Patch applied with IF_SALT = '{IF_SALT}'.")
print("Recompile with this version for the SALT binary.")
print("To produce NOSALT binary: change IF_SALT to '.eq. -999' and re-run + recompile.")
