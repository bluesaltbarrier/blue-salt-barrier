#!/bin/bash
# Apply bug fixes to the GCCN Thompson microphysics based on DoubleCheckFolder review
#
# Fixes:
#   1. R_current reset bug: replace one-step growth with R_current = 25 um (activated embryo)
#   2. Missing rho(k): add to collection rate formula
#   3. Remove pnr_wau update (wrong pathway for GCCN rain number)
#   4. Remove pnc_rcw divisor issues (keep for now, monitor)
#   5. Fix comment: 0.02% -> 0.042% for 200nm KCl ss_crit

set -e
F=/opt/MPAS-Model/src/core_atmosphere/physics/physics_wrf/module_mp_thompson.F

# Backup
cp $F ${F}.bugfix_backup
echo "Backed up to ${F}.bugfix_backup"

python3 << 'PYEOF'
with open('/opt/MPAS-Model/src/core_atmosphere/physics/physics_wrf/module_mp_thompson.F', 'r') as f:
    code = f.read()

# ============================================================
# FIX 1 + 5: Replace the one-step growth with pragmatic activated embryo size
# Also fixes the ss_crit comment
# ============================================================
old_growth = '''!...........Ambient supersaturation (in-cloud estimate)
            ss_ambient = 0.003D0   ! 0.3% typical in-cloud

!...........GCCN activation: all activate if ss > ss_crit
!           For 200nm KCl, ss_crit ~ 0.02% so this is always true in cloud
            if (ss_ambient .gt. ss_crit_gccn) then
               N_gccn_act = ngccn1d(k)
            else
               N_gccn_act = 0.0D0
            endif

            if (N_gccn_act .gt. 0.0D0) then

!..............Condensational growth: R(t+dt) = sqrt(R^2 + 2*G*ss*dt)
!              Rogers & Yau eq. 7.18, G ~ 1e-10 m^2/s
               R_current = R_gccn_min
               R_current = DSQRT(R_current**2 &
                         + 2.0D0 * G_growth * ss_ambient * dtsave)
               R_current = MIN(R_current, R_gccn_max)
               R_gccn(k) = R_current'''

new_growth = '''!...........Ambient supersaturation (in-cloud estimate)
            ss_ambient = 0.003D0   ! 0.3% typical in-cloud

!...........GCCN activation: all activate if ss > ss_crit
!           For 200 nm KCl at 298 K, ss_crit ~ 0.042%, so activation
!           usually occurs in any cloud where rc > 0.01e-3.
            if (ss_ambient .gt. ss_crit_gccn) then
               N_gccn_act = ngccn1d(k)
            else
               N_gccn_act = 0.0D0
            endif

            if (N_gccn_act .gt. 0.0D0) then

!..............Activated GCCN embryo size (pragmatic fix per DoubleCheckFolder review).
!              The previous one-step condensational growth from 10 um only reached
!              ~19-23 um per timestep, keeping collision efficiency E near zero. A
!              fully physically continuous solution would require a persistent wet
!              radius state. As an interim pragmatic choice, assume an activated
!              GCCN embryo has humidified and grown to a representative collector
!              size of 25 um once it is in a cloud with rc > 0.01e-3 kg/kg.
               R_current = 25.0D-6
               R_gccn(k) = R_current'''

if old_growth in code:
    code = code.replace(old_growth, new_growth, 1)
    print("FIX 1+5: Growth block replaced with R_current = 25 um")
else:
    raise SystemExit("ERROR: Could not find growth block to replace!")

# ============================================================
# FIX 2: Add rho(k) to collection rate formula
# ============================================================
old_collection = '''                  prr_gccn(k) = 3.14159265D0 * R_current**2 &
                     * V_gccn_drop * E_gccn_coll * rc(k) * N_gccn_act'''

new_collection = '''                  prr_gccn(k) = rho(k) * 3.14159265D0 * R_current**2 &
                     * V_gccn_drop * E_gccn_coll * rc(k) * N_gccn_act'''

if old_collection in code:
    code = code.replace(old_collection, new_collection, 1)
    print("FIX 2: Added rho(k) to collection rate formula")
else:
    raise SystemExit("ERROR: Could not find collection formula!")

# ============================================================
# FIX 3: Remove the pnr_wau update (wrong pathway)
# Also fixes radius vs diameter comparison issue (by removing the block)
# ============================================================
old_pnr = '''!.................Add rain drops from GCCN that grew past rain threshold
                  if (R_current .gt. D0r) then
                     pnr_wau(k) = pnr_wau(k) + prr_gccn(k) &
                        / MAX(1.0D-20, am_r * (2.0D0*R_current)**3)
                  endif'''

new_pnr = '''!.................Rain-number creation from GCCN threshold crossing is handled
!                 by the standard Thompson accretion conversion logic, not by
!                 adding to pnr_wau. The previous line was removed per the
!                 DoubleCheckFolder review (wrong pathway and radius vs diameter bug).'''

if old_pnr in code:
    code = code.replace(old_pnr, new_pnr, 1)
    print("FIX 3: Removed pnr_wau update (wrong pathway)")
else:
    raise SystemExit("ERROR: Could not find pnr_wau block!")

with open('/opt/MPAS-Model/src/core_atmosphere/physics/physics_wrf/module_mp_thompson.F', 'w') as f:
    f.write(code)

print("\nAll bugfixes applied.")
PYEOF

echo ""
echo "Verifying changes..."
echo ""
echo "=== New activation/growth block ==="
grep -n "R_current = 25.0D-6\|ss_crit ~ 0.042" $F | head -5
echo ""
echo "=== New collection formula with rho(k) ==="
grep -n "prr_gccn(k) = rho(k)" $F
echo ""
echo "=== pnr_wau should be gone (only the comment remains) ==="
grep -c "pnr_wau(k) = pnr_wau(k) + prr_gccn" $F || echo "0 (good - fully removed)"
echo ""
echo "Patch complete. Ready to rebuild MPAS."
