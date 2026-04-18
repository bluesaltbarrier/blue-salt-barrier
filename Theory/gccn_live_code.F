!=========================================================================
! AUTHORITATIVE GCCN LIVE CODE EXCERPT
!
! This file is the ground-truth extract of the GCCN physics as it exists
! in the running MPAS Thompson microphysics module. It is NOT standalone
! compilable code -- it is excerpted from:
!
!   /opt/MPAS-Model/src/core_atmosphere/physics/physics_wrf/module_mp_thompson.F
!
! inside the running mpas8 Docker container, after applying the patches:
!
!   reproducibility/mpas_modifications/patch_gccn_full.sh
!   reproducibility/mpas_modifications/patch_gccn_bugfixes.sh
!
! to vanilla MPAS-Atmosphere v8.3.1 Thompson microphysics.
!
! Extracted on: 2026-04-18, after independent AI code review (DoubleCheck)
! identified three bugs in the previous version. This version reflects
! all known-issue fixes at the time of extraction.
!
! If you want to compile this, do so by applying the patches above to
! vanilla Thompson, not by trying to build this excerpt directly.
!
! Line numbers below refer to the live module_mp_thompson.F at extraction
! time; actual line numbers will shift as patches evolve.
!
!=========================================================================


!=========================================================================
! SECTION A (module parameters, lines ~125-140)
!   Constants used by the GCCN lifecycle physics.
!   Dd_salt = 200 nm matches Pohlker et al. 2012 observed core size.
!=========================================================================

      REAL, PARAMETER, PRIVATE :: kappa_KCl    = 0.99       ! Petters & Kreidenweis 2007
      REAL, PARAMETER, PRIVATE :: sigma_water  = 0.072      ! surface tension (J/m2)
      REAL, PARAMETER, PRIVATE :: Mw_water     = 0.018015   ! mol weight water (kg/mol)
      REAL, PARAMETER, PRIVATE :: Rgas_kk      = 8.314      ! gas constant (J/mol/K)
      REAL, PARAMETER, PRIVATE :: rho_w_kk     = 997.0      ! water density (kg/m3)
      REAL, PARAMETER, PRIVATE :: Dd_salt      = 200.0E-9   ! dry salt diameter (m)
      REAL, PARAMETER, PRIVATE :: R_gccn_min   = 10.0E-6    ! min activated radius (m)
      REAL, PARAMETER, PRIVATE :: R_gccn_max   = 100.0E-6   ! max GCCN drop radius (m)
      REAL, PARAMETER, PRIVATE :: G_growth     = 1.0E-10    ! condensation param (m2/s)


!=========================================================================
! SECTION B (column-level variable declarations, ~line 1455)
!   Working variables for GCCN physics within the column loop.
!=========================================================================

      DOUBLE PRECISION, DIMENSION(kts:kte):: R_gccn
      DOUBLE PRECISION, DIMENSION(kts:kte):: pna_gccn_scav
      DOUBLE PRECISION, DIMENSION(kts:kte):: prr_gccn
      DOUBLE PRECISION :: A_koh, ss_crit_gccn, ss_ambient
      DOUBLE PRECISION :: N_gccn_act, R_current
      DOUBLE PRECISION :: V_gccn_drop, E_gccn_coll


!=========================================================================
! SECTION C (initialization, ~line 1585)
!   Zero-initialize GCCN-related variables each microphysics call.
!=========================================================================

         prr_gccn(k) = 0.
         R_gccn(k) = 0.
         pna_gccn_scav(k) = 0.


!=========================================================================
! SECTION D (GCCN activation/growth/collection, ~lines 2013-2134)
!
!   This is the core GCCN physics. The structure is:
!     1. Check activation criterion (in-cloud + GCCN present)
!     2. Compute kappa-Kohler critical supersaturation for 200 nm KCl
!     3. Assume activated embryo collector size (see bug-fix note below)
!     4. Look up terminal velocity V(R) from Beard 1976 piecewise table
!     5. Look up collision efficiency E(R) from Hall 1980 piecewise table
!     6. Compute mass collection rate: rho * pi * R^2 * V * E * qc * N_gccn
!     7. Route to accretion pathway prr_rcw (NOT autoconversion prr_wau)
!     8. Deplete cloud droplet number via pnc_rcw
!
!   Bug-fix history:
!     v1 (initial): routed GCCN mass to prr_wau (WRONG)
!                    fixed by patch_gccn_full.sh -> prr_rcw
!     v2 (full lifecycle): R_current reset to R_gccn_min each timestep
!                          and grown via dR/dt = G*ss/R. This kept
!                          collectors at 10-23 um where E~0 most of the time
!                          effectively disabling the physics.
!                          fixed by patch_gccn_bugfixes.sh -> R_current = 25 um
!                          (pragmatic activated-embryo assumption).
!     v2 (full lifecycle): prr_gccn formula was missing rho(k) factor.
!                          fixed by patch_gccn_bugfixes.sh
!     v2 (full lifecycle): rain-number creation added to pnr_wau, also
!                          compared a radius to a diameter (D0r is a
!                          diameter threshold). Both bugs. The entire
!                          pnr_wau update was removed by
!                          patch_gccn_bugfixes.sh.
!=========================================================================

!..GCCN full lifecycle: activation, growth, collection
!   Pohlker 2012 (emission), Petters & Kreidenweis 2007 (activation),
!   Rogers & Yau (condensation growth), Hall 1980 (collision efficiency),
!   Beard 1976 (terminal velocity).
         if (rc(k).gt.0.01e-3 .and. ngccn1d(k).gt.1.0D3) then

!...........Kohler curvature parameter (temperature-dependent)
            A_koh = 4.0D0 * sigma_water * Mw_water &
                  / (Rgas_kk * temp(k) * rho_w_kk)

!...........Critical supersaturation for 200nm KCl salt
            ss_crit_gccn = DSQRT(4.0D0 * A_koh**3 &
                    / (27.0D0 * kappa_KCl * Dd_salt**3))

!...........Ambient supersaturation (in-cloud estimate)
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

!..............Activated GCCN embryo size (pragmatic fix per code review).
!              The previous one-step condensational growth from 10 um only
!              reached ~19-23 um per timestep, keeping collision efficiency
!              E near zero. A fully physically continuous solution would
!              require a persistent wet radius state across timesteps. As
!              an interim pragmatic choice, assume an activated GCCN
!              embryo has humidified and grown to a representative
!              collector size of 25 um once it is in a cloud with
!              rc > 0.01e-3 kg/kg.
               R_current = 25.0D-6
               R_gccn(k) = R_current

!..............Terminal velocity (Beard 1976 empirical piecewise)
               if (R_current .lt. 20.0D-6) then
                  V_gccn_drop = 0.0D0
               elseif (R_current .lt. 40.0D-6) then
                  V_gccn_drop = 0.12D0
               elseif (R_current .lt. 60.0D-6) then
                  V_gccn_drop = 0.25D0
               else
                  V_gccn_drop = 0.50D0
               endif

!..............Collision efficiency (Hall 1980 lookup:
!              collector R vs 10 um cloud drop)
               if (R_current .lt. 20.0D-6) then
                  E_gccn_coll = 0.0D0
               elseif (R_current .lt. 30.0D-6) then
                  E_gccn_coll = 0.05D0
               elseif (R_current .lt. 40.0D-6) then
                  E_gccn_coll = 0.2D0
               elseif (R_current .lt. 50.0D-6) then
                  E_gccn_coll = 0.5D0
               elseif (R_current .lt. 70.0D-6) then
                  E_gccn_coll = 0.65D0
               else
                  E_gccn_coll = 0.8D0
               endif

!..............GCCN collection of cloud water (accretion pathway)
!              prr = rho * pi * R^2 * V * E * qc * N_gccn  [kg/kg/s]
!              rho(k) factor added by bug-fix patch for units consistency
!              given ngccn1d is in number mixing ratio (#/kg air).
               if (V_gccn_drop.gt.0.0D0 .and. E_gccn_coll.gt.0.0D0) then
                  prr_gccn(k) = rho(k) * 3.14159265D0 * R_current**2 &
                     * V_gccn_drop * E_gccn_coll * rc(k) * N_gccn_act
                  prr_gccn(k) = MIN(prr_gccn(k), DBLE(rc(k)*odts))

!.................Add to accretion (rain collecting cloud water).
!                 This is the CORRECT pathway per the original ChatGPT
!                 review -- not prr_wau (autoconversion).
                  prr_rcw(k) = prr_rcw(k) + prr_gccn(k)
                  prr_rcw(k) = MIN(DBLE(rc(k)*odts), prr_rcw(k))

!.................Cloud droplet number depletion by GCCN collection
                  pnc_rcw(k) = pnc_rcw(k) + prr_gccn(k) &
                     / MAX(1.0D-20, am_r * mvd_c(k)**3)
                  pnc_rcw(k) = MIN(DBLE(nc(k)*odts), pnc_rcw(k))

!.................Rain-number creation from GCCN threshold crossing is
!                 handled by the standard Thompson accretion conversion
!                 logic, not by adding to pnr_wau. The previous pnr_wau
!                 line (which also compared radius to diameter) was
!                 removed per the DoubleCheckFolder review.
               endif
            endif
         endif


!=========================================================================
! SECTION E (wet scavenging by rain, ~line 2125)
!   GCCN below cloud are swept out by falling rain drops, using the same
!   Thompson Eff_aero framework as nwfa/nifa scavenging.
!=========================================================================

!...........GCCN wet scavenging by rain (same framework, 200nm particle)
            if (ngccn1d(k) .gt. 0.0D0) then
               Ef_ra = Eff_aero(mvd_r(k),Dd_salt*0.5,visco(k),rho(k),  &
                                temp(k),'r')
               pna_gccn_scav(k) = rhof(k)*t1_qr_qc*Ef_ra*ngccn1d(k)    &
                                 *N0_r(k)*((lamr+fv_r)**(-cre(9)))
               pna_gccn_scav(k) = MIN(DBLE(ngccn1d(k)*odts),            &
                                      pna_gccn_scav(k))
            endif


!=========================================================================
! SECTION F (scavenging tendency application, ~line 2815)
!   Apply wet-scavenging removal to ngccn1d with consistent units.
!   orho = 1/rho(k); dtsave is microphysics timestep. This matches the
!   units convention used for nwfaten/nifaten elsewhere in Thompson.
!=========================================================================

!...........GCCN scavenging: deplete ngccn1d directly
            ngccn1d(k) = ngccn1d(k) - pna_gccn_scav(k) * orho * dtsave
            ngccn1d(k) = MAX(0.0D0, ngccn1d(k))


!=========================================================================
! NOTES FOR REVIEWERS
!
! 1. This excerpt shows every GCCN-related modification to Thompson
!    microphysics. There are no other GCCN code blocks elsewhere in
!    module_mp_thompson.F.
!
! 2. If you want to reproduce the live build from scratch:
!      docker pull ghcr.io/bluesaltbarrier/mpas8-gccn:slim
!    or build from source via:
!      cd reproducibility/container
!      docker build -t mpas8 -f Dockerfile.mpas8_ubuntu .
!      bash reproducibility/mpas_modifications/patch_gccn_full.sh
!      bash reproducibility/mpas_modifications/patch_gccn_bugfixes.sh
!      (then standard make command)
!
! 3. Known simplifications (documented in the paper's limitations section):
!    - Single representative GCCN size (200 nm dry KCl core)
!    - No organic coating aging of the salt (kappa stays at 0.99)
!    - Fixed collector-embryo size of 25 um rather than persistent wet
!      radius state. A proper persistent-radius solution is a priority
!      future improvement.
!    - No ice-phase GCCN interactions
!    - Constant emission rate (not coupled to vegetation state)
!
! 4. Feedback on this code is welcome via GitHub Issues at
!    https://github.com/bluesaltbarrier/blue-salt-barrier
!=========================================================================
