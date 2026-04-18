!=========================================================================
! GCCN MODIFICATION TO THOMPSON MICROPHYSICS
!=========================================================================
!
! Purpose: Add Giant Cloud Condensation Nuclei (GCCN) physics to the
!          Thompson aerosol-aware microphysics scheme to model the effect
!          of hygroscopic salt particles emitted by tropical rainforest
!          trees and fungi.
!
! Physical basis:
!   - Tree-emitted KCl/NaCl salt particles are 0.2-10 um diameter
!   - kappa(KCl) = 0.99, kappa(NaCl) = 1.28 (Petters & Kreidenweis 2007)
!   - At tropical humidity (>80% RH), salt particles swell to >20 um
!   - These large drops bridge the coalescence gap (Hall 1980):
!     E(50um,10um) ~ 0.6 vs E(20um,10um) ~ 0.02
!   - Result: rain forms 3-5x faster (Jensen & Lee 2008)
!   - Observed: 28-60% rainfall enhancement in seeding experiments
!
! Implementation:
!   1. Track GCCN as a subset of nwfa with kappa > 0.9
!   2. Compute kappa-dependent critical supersaturation
!   3. Activate GCCN at lower supersaturation than standard CCN
!   4. GCCN-activated drops collect cloud water via coalescence
!   5. Transfer collected mass to rain category
!
! Code changes are localized to module_mp_thompson.F in three places:
!   A. Variable declarations (~10 lines)
!   B. GCCN activation after CCN activation (~40 lines)
!   C. GCCN coalescence after Berry-Reinhardt autoconversion (~60 lines)
!
! References:
!   Petters & Kreidenweis (2007), ACP 7, 1961-1971
!   Hall (1980), J. Atmos. Sci. 37, 2486-2507
!   Jensen & Lee (2008), J. Atmos. Sci. 65, 2218-2236
!   Berry & Reinhardt (1974), J. Atmos. Sci. 31, 2127-2135
!   Pohlker et al. (2012), Science 337, 1075-1078
!   Rosenfeld et al. (2010), J. Appl. Meteor. Climatol. 49, 1548-1562
!
!=========================================================================

!=========================================================================
! PART A: Additional variable declarations
!         Insert in the column-loop variable declarations section,
!         near line 1431 where prr_wau etc. are declared.
!=========================================================================

!..GCCN variables
      DOUBLE PRECISION, DIMENSION(kts:kte):: prr_gccn    ! GCCN collection rate
      DOUBLE PRECISION :: N_gccn                          ! GCCN number concentration (#/m3)
      DOUBLE PRECISION :: R_gccn_wet                      ! GCCN wet-activated radius (m)
      DOUBLE PRECISION :: V_gccn                          ! GCCN terminal velocity (m/s)
      DOUBLE PRECISION :: E_gccn                          ! GCCN-cloud collision efficiency
      DOUBLE PRECISION :: ss_crit_gccn                    ! GCCN critical supersaturation
      DOUBLE PRECISION :: kappa_salt                      ! hygroscopicity of salt
      DOUBLE PRECISION :: Dd_gccn                         ! GCCN dry diameter (m)
      DOUBLE PRECISION :: A_kohler                        ! Kohler curvature parameter
      DOUBLE PRECISION :: frac_gccn                       ! fraction of nwfa that is GCCN

!..GCCN parameters (from literature)
      DOUBLE PRECISION, PARAMETER :: kappa_KCl  = 0.99D0   ! Petters & Kreidenweis 2007
      DOUBLE PRECISION, PARAMETER :: kappa_NaCl = 1.28D0   ! Petters & Kreidenweis 2007
      DOUBLE PRECISION, PARAMETER :: sigma_w = 0.072D0     ! surface tension of water (J/m2)
      DOUBLE PRECISION, PARAMETER :: Mw = 0.018015D0       ! molecular weight of water (kg/mol)
      DOUBLE PRECISION, PARAMETER :: Rv_gas = 8.314D0      ! universal gas constant (J/mol/K)
      DOUBLE PRECISION, PARAMETER :: rho_water = 997.0D0   ! density of water (kg/m3)
      DOUBLE PRECISION, PARAMETER :: Dd_salt = 2.0D-6      ! assumed dry salt diameter (2 um)
      DOUBLE PRECISION, PARAMETER :: E_gccn_const = 0.6D0  ! Hall(1980): E(50um,10um)
      DOUBLE PRECISION, PARAMETER :: R_gccn_act = 50.0D-6  ! activated GCCN radius (50 um)
      DOUBLE PRECISION, PARAMETER :: gccn_frac = 0.01D0    ! 1% of nwfa is salt GCCN


!=========================================================================
! PART B: GCCN activation
!         Insert after the standard CCN activation code
!         (after the nwfa activation section, before autoconversion).
!         This determines how many GCCN activate in the current column.
!=========================================================================

!..GCCN activation: salt particles activate at much lower supersaturation
!   than standard CCN due to high hygroscopicity and large size.
!   Kappa-Kohler theory (Petters & Kreidenweis 2007):
!     ss_crit = sqrt(4 * A^3 / (27 * kappa * Dd^3))
!   For 2 um KCl (kappa=0.99): ss_crit ~ 0.001% -- activates instantly.

      do k = kts, kte
         prr_gccn(k) = 0.0D0
      enddo

!..Only compute GCCN physics where cloud water exists and nwfa is present
      do k = kts, kte
         if (rc(k) .gt. 0.01e-3 .and. nwfa1d(k) .gt. 1.0) then

            ! Kohler curvature parameter
            A_kohler = 4.0D0 * sigma_w * Mw &
                     / (Rv_gas * temp(k) * rho_water)

            ! Use KCl kappa (dominant salt from tree fungi, Pohlker 2012)
            kappa_salt = kappa_KCl

            ! Critical supersaturation for 2 um salt particle
            Dd_gccn = Dd_salt
            ss_crit_gccn = DSQRT(4.0D0 * A_kohler**3 &
                         / (27.0D0 * kappa_salt * Dd_gccn**3))

            ! GCCN number: fraction of total water-friendly aerosol
            ! In rainforest air, ~1% of aerosol particles are salt GCCN
            ! At nwfa ~ 300e6 m-3, this gives N_gccn ~ 3e6 m-3 (3/cc)
            ! Jensen & Lee (2008): need >1e3 m-3 (0.001/cc) for effect
            N_gccn = nwfa1d(k) * gccn_frac

            ! GCCN activation check:
            ! In-cloud supersaturation typically 0.1-1%
            ! Salt GCCN critical SS is ~0.001% -- always activates in cloud
            ! No activation barrier -- if there's a cloud, salt activates.

            if (N_gccn .gt. 1.0D3) then   ! need at least 0.001/cc

               ! Activated GCCN wet radius: salt + condensed water
               ! A 2 um KCl particle at ss=0.3% grows to ~50 um radius
               ! (from equilibrium Kohler curve)
               R_gccn_wet = R_gccn_act

               ! Terminal velocity for 100 um diameter (50 um radius) drop
               ! Stokes law gives 0.30 m/s but overestimates by 15-20%
               ! at Re~2 (Beard 1976, Rogers & Yau).
               ! Correct value from literature: V ~ 0.25 m/s for 100 um drop.
               ! Use Beard (1976) empirical value instead of Stokes.
               V_gccn = 0.25D0   ! m/s (Beard 1976, Rogers & Yau)

               ! Collision efficiency: Hall (1980)
               ! For 50 um collector, 10 um collected: E ~ 0.6
               E_gccn = E_gccn_const

               ! GCCN collection of cloud water (continuous collection equation)
               ! dM/dt = pi * R^2 * V * E * rho_cloud * N_gccn
               ! Units: (m2) * (m/s) * (-) * (kg/m3) * (#/m3) = kg/m3/s
               prr_gccn(k) = 3.14159D0 * R_gccn_wet**2 &
                            * V_gccn * E_gccn * rc(k) * N_gccn &
                            / rho(k)

               ! Limit: cannot collect more cloud water than exists
               prr_gccn(k) = MIN(prr_gccn(k), DBLE(rc(k) * odts))

            endif
         endif
      enddo


!=========================================================================
! PART C: Add GCCN collection to the autoconversion tendency
!         Insert AFTER the Berry-Reinhardt autoconversion code block
!         (after prr_wau is computed, before the rain collection section).
!         This adds the GCCN coalescence contribution to the cloud-to-rain
!         conversion rate.
!=========================================================================

!..GCCN coalescence enhancement: add GCCN-collected cloud water to
!   the autoconversion rate. This represents salt-activated large drops
!   sweeping up small cloud droplets through collision-coalescence.
!   Physical basis: Berry & Reinhardt autoconversion alone takes ~20 min.
!   With GCCN providing 50-um collector drops, coalescence begins
!   immediately (E=0.6 vs E=0.02 for 20-um drops).
!   Observed effect: 2-4x faster rain formation (Rosenfeld et al. 2010).

         if (prr_gccn(k) .gt. 0.0D0) then
            ! Add GCCN collection to autoconversion
            prr_wau(k) = prr_wau(k) + prr_gccn(k)

            ! Limit total autoconversion
            prr_wau(k) = MIN(DBLE(rc(k)*odts), prr_wau(k))

            ! GCCN-collected drops immediately enter rain category
            ! Each GCCN drop that collects enough cloud water to exceed
            ! D0r (50 um in this version of Thompson) becomes a rain drop.
            ! Assume all GCCN-collected mass transfers to rain.
            pnr_wau(k) = pnr_wau(k) + prr_gccn(k) &
                        / (am_r * D0r * D0r * D0r)

            ! Remove collected cloud droplets from Nc
            pnc_wau(k) = pnc_wau(k) + prr_gccn(k) &
                        / (am_r * mvd_c(k)**3)
            pnc_wau(k) = MIN(DBLE(nc(k)*odts), pnc_wau(k))

            ! Deplete GCCN (wet scavenging by own collection)
            ! Each activated GCCN that becomes a raindrop is removed
            ! from the aerosol population
            pna_rca(k) = pna_rca(k) + N_gccn * gccn_frac &
                        * MIN(1.0D0, prr_gccn(k) / MAX(rc(k), 1.0D-10))
         endif


!=========================================================================
! PART D: Initialize prr_gccn in the tendency zeroing section
!         Insert where prr_wau, prr_rcw etc. are zeroed (near line 1564)
!=========================================================================

         prr_gccn(k) = 0.


!=========================================================================
! PART E: Include prr_gccn in the rain production diagnostic
!         Insert where rainprod is computed (near line 3200)
!=========================================================================

         rainprod(k) = prr_wau(k) + prr_rcw(k) + prs_scw(k) + &
                       prg_gcw(k) + prs_iau(k) + prr_gccn(k)


!=========================================================================
! INTEGRATION NOTES
!=========================================================================
!
! To integrate this into module_mp_thompson.F:
!
! 1. Add PART A declarations near line 1431 (with other column variables)
!
! 2. Add PART D initialization near line 1564 (with other tendency zeros)
!
! 3. Add PART B activation code BEFORE the autoconversion block
!    (insert before "!..Autoconversion follows Berry & Reinhardt")
!    This computes prr_gccn(k) for each level.
!
! 4. Add PART C coalescence code AFTER the autoconversion block
!    (insert after "pnc_wau(k) = MIN(..." line that ends autoconversion)
!    This adds prr_gccn to prr_wau.
!
! 5. Add PART E to the diagnostic output section.
!
! 6. The GCCN fraction (gccn_frac = 0.01) controls the strength:
!    - 0.001 = very conservative (0.1% of aerosol is salt)
!    - 0.01  = moderate (1% of aerosol is salt)
!    - 0.05  = strong (5% of aerosol is salt, high-emission forest)
!    This parameter should ultimately come from the vegetation type
!    and a salt emission inventory, not be hardcoded.
!
! 7. The dry salt diameter (Dd_salt = 2 um) controls activation:
!    - 0.2 um = Pohlker core size (still activates, ss_crit ~ 0.02%)
!    - 2 um   = optimal seeding size (Rosenfeld 2010)
!    - 5 um   = large GCCN (activates sub-cloud)
!    Sensitivity tests should span this range.
!
! 8. No changes to the namelist or registry are needed for the basic
!    implementation. The GCCN fraction is computed from existing nwfa.
!    A more complete implementation would add:
!    - config_gccn_fraction (namelist parameter)
!    - QNGCCN as a new prognostic tracer (registry change)
!    - Salt-specific emission field separate from nwfa2d
!
!=========================================================================
!
! EXPECTED RESULTS:
!   - Rainforest cells with high nwfa (from enhanced emission) will have
!     more GCCN activating and collecting cloud water
!   - Autoconversion rate increases by factor of 2-5 in these cells
!   - Rain forms faster, falls locally
!   - Less moisture available for poleward transport
!   - This is the OPPOSITE of standard Twomey (which suppresses rain)
!   - The sign flip comes from the size difference: GCCN (50 um) vs
!     standard CCN (10 um) — coalescence efficiency jumps from 0.02 to 0.6
!
!=========================================================================
