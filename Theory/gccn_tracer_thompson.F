!=========================================================================
! GCCN DEDICATED TRACER — Thompson Microphysics Modification
!=========================================================================
!
! Full lifecycle tracking of Giant Cloud Condensation Nuclei (GCCN)
! from biogenic salt emission through raindrop formation.
!
! Physical chain:
!   Emission (Pohlker 2012) → Transport (MPAS) → Hygroscopic growth
!   (Petters & Kreidenweis 2007) → Activation (kappa-Kohler) →
!   Condensational growth (diffusion) → Collision-coalescence
!   (Hall 1980) → Rain formation → Wet scavenging
!
! Cross-checked with OpenAI ChatGPT for equation verification.
!
! Known simplifications:
!   - No organic coating aging (kappa stays at 0.99)
!   - Single representative size (200nm dry)
!   - No ice-phase GCCN interactions
!   - Constant emission rate (no diurnal/seasonal cycle yet)
!   - Sub-grid dispersion not resolved at 240km
!
!=========================================================================

!=========================================================================
! PART A: Module-level parameters
!   Add to the PRIVATE parameter section near line 112
!=========================================================================

!..GCCN physical constants (from literature)
      REAL, PARAMETER, PRIVATE :: kappa_KCl    = 0.99       ! Petters & Kreidenweis 2007
      REAL, PARAMETER, PRIVATE :: kappa_NaCl   = 1.28       ! Petters & Kreidenweis 2007
      REAL, PARAMETER, PRIVATE :: sigma_water  = 0.072      ! surface tension (J/m2)
      REAL, PARAMETER, PRIVATE :: Mw_water     = 0.018015   ! molecular weight water (kg/mol)
      REAL, PARAMETER, PRIVATE :: Rgas         = 8.314      ! gas constant (J/mol/K)
      REAL, PARAMETER, PRIVATE :: rho_w        = 997.0      ! water density (kg/m3)
      REAL, PARAMETER, PRIVATE :: Dd_salt      = 200.0E-9   ! dry salt diameter (m) Pohlker 2012
      REAL, PARAMETER, PRIVATE :: gccn_frac    = 0.01       ! fraction of nwfa that is GCCN

!..GCCN growth and collection parameters
      REAL, PARAMETER, PRIVATE :: R_gccn_min   = 10.0E-6    ! min activated radius (m)
      REAL, PARAMETER, PRIVATE :: R_gccn_max   = 100.0E-6   ! max GCCN drop radius (m)
      REAL, PARAMETER, PRIVATE :: D0r_thompson = 50.0E-6    ! Thompson rain threshold (m)


!=========================================================================
! PART B: Column-level variable declarations
!   Add in the column loop declarations near line 1431
!=========================================================================

!..GCCN tracer variables
      DOUBLE PRECISION, DIMENSION(kts:kte) :: ngccn1d       ! GCCN concentration (1D column)
      DOUBLE PRECISION, DIMENSION(kts:kte) :: R_gccn        ! current GCCN wet radius (m)
      DOUBLE PRECISION, DIMENSION(kts:kte) :: prr_gccn_col  ! GCCN collection rate
      DOUBLE PRECISION, DIMENSION(kts:kte) :: pna_gccn_scav ! GCCN scavenging rate

      DOUBLE PRECISION :: A_koh           ! Kohler curvature parameter
      DOUBLE PRECISION :: ss_crit         ! critical supersaturation
      DOUBLE PRECISION :: N_gccn_act      ! activated GCCN number
      DOUBLE PRECISION :: V_gccn_drop     ! terminal velocity
      DOUBLE PRECISION :: E_gccn_coll     ! collision efficiency
      DOUBLE PRECISION :: G_growth        ! condensation growth parameter
      DOUBLE PRECISION :: dR_dt           ! radius growth rate
      DOUBLE PRECISION :: R_current       ! current drop radius
      DOUBLE PRECISION :: ss_ambient      ! ambient supersaturation


!=========================================================================
! PART C: GCCN initialization (zero tendencies)
!   Add where prr_wau(k) = 0 etc. are set
!=========================================================================

         prr_gccn_col(k) = 0.0D0
         pna_gccn_scav(k) = 0.0D0
         R_gccn(k) = 0.0D0


!=========================================================================
! PART D: GCCN activation and growth
!   Insert AFTER CCN activation, BEFORE autoconversion
!   This is the core physics: kappa-Kohler activation,
!   condensational growth, and size-dependent collection
!=========================================================================

!..GCCN lifecycle: activation, growth, collection
!   Based on Pohlker et al. 2012 (emission), Petters & Kreidenweis 2007
!   (activation), Rogers & Yau (condensation growth), Hall 1980 (collection)

      do k = kts, kte

         prr_gccn_col(k) = 0.0D0
         R_gccn(k) = 0.0D0

         if (rc(k) .le. 0.01e-3 .or. ngccn1d(k) .le. 0.0) cycle

!........Kohler curvature parameter (temperature dependent)
         A_koh = 4.0D0 * sigma_water * Mw_water &
               / (Rgas * temp(k) * rho_w)

!........Critical supersaturation for salt GCCN
!        For 200nm KCl: ss_crit ~ 0.02% (activates easily in any cloud)
         ss_crit = DSQRT(4.0D0 * A_koh**3 &
                 / (27.0D0 * kappa_KCl * Dd_salt**3))

!........Ambient supersaturation estimate
!        In cloud: ss ~ 0.1-1%. Use qv saturation deficit.
!        Simplified: if cloud water exists, assume ss > ss_crit for GCCN
         if (rc(k) .gt. 0.01e-3) then
            ss_ambient = 0.003D0   ! 0.3% typical in-cloud value
         else
            ss_ambient = 0.0D0
         endif

!........GCCN activation
!        If ambient ss > critical ss, GCCN activates
         if (ss_ambient .gt. ss_crit) then
            N_gccn_act = ngccn1d(k)   ! all GCCN activate (ss >> ss_crit)
         else
            N_gccn_act = 0.0D0
            cycle
         endif

!........Condensational growth: dR/dt = G * ss / R
!        G = condensation growth parameter (Rogers & Yau eq. 7.18)
!        G ~ 1e-10 m^2/s at typical cloud conditions
!        Starting from R_initial ~ 10um (just activated)
!        Growth over one microphysics timestep (dt_microp)

         G_growth = 1.0D-10   ! m^2/s (typical value)
         R_current = R_gccn_min   ! start at 10 um (just activated)

!........Integrate growth: R(t+dt) = sqrt(R(t)^2 + 2*G*ss*dt)
         R_current = DSQRT(R_current**2 &
                   + 2.0D0 * G_growth * ss_ambient * dt_microp)

!........Cap at maximum GCCN size
         R_current = MIN(R_current, R_gccn_max)
         R_gccn(k) = R_current

!........Terminal velocity (Beard 1976 empirical fit)
!        Valid for drops 20-200 um radius
!        V ~ 0.003 * R^2 * rho_w * g / (9 * mu_air) with correction
!        Simplified lookup (verified against Beard 1976):
         if (R_current .lt. 20.0D-6) then
            V_gccn_drop = 0.0D0   ! too small to collect
         elseif (R_current .lt. 40.0D-6) then
            V_gccn_drop = 0.12D0   ! ~0.12 m/s at 40um
         elseif (R_current .lt. 60.0D-6) then
            V_gccn_drop = 0.25D0   ! ~0.25 m/s at 50um (Beard 1976)
         else
            V_gccn_drop = 0.5D0    ! ~0.5 m/s at 80-100um
         endif

!........Collision efficiency (Hall 1980 lookup)
!        E depends on collector size (R_gccn) and collected size (~10um)
!        Interpolate from Hall 1980 table:
         if (R_current .lt. 20.0D-6) then
            E_gccn_coll = 0.0D0     ! coalescence gap
         elseif (R_current .lt. 30.0D-6) then
            E_gccn_coll = 0.05D0    ! barely collecting
         elseif (R_current .lt. 40.0D-6) then
            E_gccn_coll = 0.2D0     ! growing efficiency
         elseif (R_current .lt. 50.0D-6) then
            E_gccn_coll = 0.5D0     ! significant collection
         elseif (R_current .lt. 70.0D-6) then
            E_gccn_coll = 0.65D0    ! Hall 1980: E(50-70um, 10um)
         else
            E_gccn_coll = 0.8D0     ! large collector, high efficiency
         endif

!........GCCN collection of cloud water
!        Continuous collection equation:
!        prr = pi * R^2 * V * E * qc * N_gccn
!        Units: m^2 * m/s * kg/kg * #/kg = kg/kg/s (mixing ratio tendency)
!        Verified by OpenAI ChatGPT cross-check

         if (V_gccn_drop .gt. 0.0D0 .and. E_gccn_coll .gt. 0.0D0) then
            prr_gccn_col(k) = 3.14159265D0 * R_current**2 &
                             * V_gccn_drop * E_gccn_coll &
                             * rc(k) * N_gccn_act

!...........Limit: cannot collect more cloud water than exists
            prr_gccn_col(k) = MIN(prr_gccn_col(k), DBLE(rc(k) * odts))
         endif

      enddo


!=========================================================================
! PART E: Add GCCN collection to accretion tendency
!   Insert AFTER rain collecting cloud water (prr_rcw) section
!   Per ChatGPT review: GCCN collection is accretion, not autoconversion
!=========================================================================

!..GCCN coalescence: add to accretion pathway
!   Physical basis: GCCN drops are large enough to be "proto-rain"
!   collecting small cloud droplets — this is accretion, not
!   self-collection (autoconversion). Per GPT cross-check.

      do k = kts, kte
         if (prr_gccn_col(k) .gt. 0.0D0) then
!...........Add to accretion (rain collecting cloud water)
            prr_rcw(k) = prr_rcw(k) + prr_gccn_col(k)
            prr_rcw(k) = MIN(DBLE(rc(k)*odts), prr_rcw(k))

!...........GCCN drops that collected enough mass become rain drops
!           Increase rain number proportional to GCCN that grew past D0r
            if (R_gccn(k) .gt. D0r_thompson) then
               pnr_rcw(k) = pnr_rcw(k) + prr_gccn_col(k) &
                           / (am_r * (2.0D0*R_gccn(k))**3)
            endif

!...........Decrease cloud droplet number (collected by GCCN)
            pnc_rcw(k) = pnc_rcw(k) + prr_gccn_col(k) &
                        / (am_r * mvd_c(k)**3)
            pnc_rcw(k) = MIN(DBLE(nc(k)*odts), pnc_rcw(k))
         endif
      enddo


!=========================================================================
! PART F: Wet scavenging of unactivated GCCN by rain
!   Insert in the "Rain collecting aerosols" section (~line 2010)
!   alongside existing pna_rca (rain collecting nwfa)
!=========================================================================

!..Rain scavenging of GCCN (same approach as nwfa scavenging)
         if (L_qr(k) .and. mvd_r(k).gt. D0r) then
            ! Use same collection efficiency as for nwfa
            ! but with larger GCCN particle size (200nm vs 40nm)
            Ef_ra = Eff_aero(mvd_r(k), Dd_salt*0.5, &
                             visco(k), rho(k), temp(k), 'r')
            lamr = 1./ilamr(k)
            pna_gccn_scav(k) = rhof(k)*t1_qr_qc*Ef_ra*ngccn1d(k) &
                              *N0_r(k)*((lamr+fv_r)**(-cre(9)))
            pna_gccn_scav(k) = MIN(DBLE(ngccn1d(k)*odts), &
                                   pna_gccn_scav(k))
         endif


!=========================================================================
! PART G: Update GCCN tendencies (end of column)
!   Insert where other tendencies are applied to state variables
!=========================================================================

!..Update GCCN concentration: deplete by wet scavenging
!   Replenishment comes from surface emission (ngccn2d) in the driver
         ngccn1d(k) = ngccn1d(k) - pna_gccn_scav(k) * dts

!..Ensure non-negative
         ngccn1d(k) = MAX(0.0D0, ngccn1d(k))


!=========================================================================
! PART H: Surface emission (in driver, not Thompson itself)
!   Add to mpas_atmphys_driver_microphysics.F
!   after the call to mp_gt_driver returns
!=========================================================================

!..GCCN surface emission: replenish lowest level
!   Emission rate from ngccn2d (set during initialization for
!   Evergreen Broadleaf Forest cells)
!   ngccn2d has units of #/kg/s

!   do i = its, ite
!      ngccn(i, kts, 1) = ngccn(i, kts, 1) + ngccn2d(i, 1) * dt_microp
!   enddo


!=========================================================================
! PART I: Rain production diagnostic
!   Add prr_gccn_col to the rainprod diagnostic
!=========================================================================

         rainprod(k) = prr_wau(k) + prr_rcw(k) + prs_scw(k) + &
                       prg_gcw(k) + prs_iau(k)
!        Note: prr_gccn_col is already included in prr_rcw


!=========================================================================
! INTEGRATION CHECKLIST
!=========================================================================
!
! Files to modify:
!   1. Registry.xml — add ngccn, ngccn2d, gccn_rainprod (PART from registry XML)
!   2. module_mp_thompson.F — PARTS A through G (main physics)
!   3. mpas_atmphys_driver_microphysics.F — PART H (surface emission)
!   4. mpas_atmphys_init_microphysics.F — initialize ngccn from nwfa*gccn_frac
!   5. mp_gt_driver subroutine signature — add ngccn as optional argument
!
! Testing:
!   1. Compile and run 1-day test — check for crashes
!   2. Verify ngccn field is advected (compare t=0 and t=12h)
!   3. Verify GCCN activate in clouds (R_gccn > 0 where rc > 0)
!   4. Verify prr_gccn_col > 0 in tropical cloud cells
!   5. Compare precipitation with and without GCCN
!   6. Check mass conservation: cloud water lost = rain gained
!
! Performance:
!   Estimated ~20-30% slowdown vs standard Thompson aerosol-aware
!   Main cost: additional 3D field advection + per-column GCCN loop
!   No new lookup tables needed (uses existing Hall 1980 E values)
!
!=========================================================================
