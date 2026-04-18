# GCCN Physics — Key References and Data for Modified Thompson

## Kappa-Kohler Theory

**Petters & Kreidenweis (2007)** — "A single parameter representation of
hygroscopic growth and cloud condensation nucleus activity."
*Atmospheric Chemistry and Physics*, 7, 1961-1971.

### The Equation

```
S_c = exp(sqrt(4 * A^3 / (27 * kappa * Dd^3)))

where:
  A = 4 * sigma_w * Mw / (R * T * rho_w)
  A ≈ 2.1e-9 m at T = 298 K

  sigma_w = 0.072 J/m²  (surface tension of water)
  Mw = 0.018015 kg/mol   (molecular weight of water)
  R = 8.314 J/(mol·K)    (universal gas constant)
  rho_w = 997 kg/m³      (density of water)
```

### Fortran Implementation

```fortran
A_kohler = 4.0_RKIND * 0.072_RKIND * 0.018015_RKIND &
         / (8.314_RKIND * T * 997.0_RKIND)
ss_crit = SQRT(4.0_RKIND * A_kohler**3 &
         / (27.0_RKIND * kappa * Dd**3))
```

Note: ss_crit for 0.1 um (NH4)2SO4 = 0.15% (verified by GPT cross-check,
corrected from initial estimate of 0.3%)

### Kappa Values

| Substance | kappa | Source |
|-----------|-------|--------|
| NaCl (sea/tree salt) | 1.28 | Petters & Kreidenweis 2007 |
| KCl (tree salt) | 0.99 | Derived from thermodynamics |
| (NH4)2SO4 (pollution) | 0.61 | Petters & Kreidenweis 2007 |
| H2SO4 | 0.90 | Petters & Kreidenweis 2007 |
| Secondary organic aerosol | 0.1-0.3 | Various |
| Black carbon (soot) | ~0.0 | Hydrophobic |

### Critical Supersaturation for NaCl (kappa = 1.28)

| Dry diameter | Critical SS | Meaning |
|-------------|------------|---------|
| 0.1 μm | 0.15% | Standard small CCN — verified by GPT cross-check |
| 0.5 μm | 0.013% | Activates easily |
| 1.0 μm | 0.005% | Activates in any cloud |
| 5.0 μm | 0.0004% | Activates in sub-cloud humid air |
| 10.0 μm | 0.0001% | Activates spontaneously at any humidity >100% |

Key: typical cloud base supersaturation is 0.1-1%. Salt particles >1 μm
activate instantly. This is what makes them GCCN — they bypass the
normal activation barrier.

---

## Collision-Coalescence Efficiencies

**Hall (1980)** — "A detailed microphysical model within a two-dimensional
dynamic framework." *J. Atmos. Sci.*, 37, 2486-2507.

| Collector R (μm) | Collected r (μm) | Efficiency E |
|-------------------|-------------------|-------------|
| 20 | 10 | 0.02 (the "coalescence gap") |
| 30 | 10 | 0.1 |
| 40 | 10 | 0.4 |
| **50** | **10** | **0.6-0.7** |
| 60 | 10 | 0.8 |
| 100 | 10 | 0.9 |

The coalescence gap (E ≈ 0 for R < 20 μm) is why autoconversion is slow.
A single GCCN-activated 50 μm drop bridges this gap with E ≈ 0.6.

Collection kernel:
```
K(R,r) = π * (R+r)² * |V(R) - V(r)| * E(R,r)
```

---

## Amazon Salt Particle Measurements

**Pöhlker et al. (2012)** — *Science*, 337(6098), 1075-1078.

- Salt core size: ~200 nm (0.2 μm) diameter
- 74 of 77 particles (96%) contained potassium salts
- Up to 20% potassium by mass
- Structure: KCl/K2SO4 core coated with secondary organic aerosol
- Source: fungal spore ejection (osmotic bursting of asci)
- Morning particles richest in potassium (before organic condensation)

Note: The 200 nm cores are at the small end of GCCN. However, in the
high-humidity Amazon boundary layer (>80% RH), these hygroscopic salt
cores swell significantly. A 200 nm KCl particle (kappa=0.99) at 99% RH
grows to roughly 1-2 μm wet diameter, entering the GCCN activation range.

---

## Cloud Seeding Experimental Results

### Rosenfeld et al. (2010)
*J. Applied Meteorology and Climatology*, 49(7), 1548-1562.
- Optimal salt particle diameter for seeding: 2-4 μm
- Salt powder seeding 100x more productive than hygroscopic flares
- Mechanism: finely milled salt produces GCCN that initiate warm rain

### Mather et al. (1997) — South Africa
*J. Applied Meteorology*, 36(11), 1433-1447.
- 48 seeded vs 49 unseeded storms
- **30-60% rainfall increase** from seeded storms
- Seeded storms lasted 25-30 minutes longer

### CAIPEEX India (2023)
*Bull. Amer. Meteorol. Soc.*, 104(11).
- 618 cases analyzed
- **28% average rainfall enhancement** (>95% confidence)

### Salt Powder Experiments
*Atmos. Chem. Phys.*, 10, 8011-8023, 2010.
- **2-3x increase** in precipitation flux
- Even at high salt concentrations, no overseeding effect
- Low consumption rates can initiate precipitation from non-precipitating clouds

---

## Autoconversion Timescales

### Without GCCN (standard autoconversion)
- First 100 μm drop: ~17 minutes
- 10% mass conversion to rain: ~24 minutes

### With GCCN (>1 per liter at >20 μm)
- GCCN-activated drops start at 20-50 μm
- Immediately bridge the coalescence gap
- Effective autoconversion timescale: ~5-8 minutes
- Acceleration factor: 3-5x

### Jensen & Lee (2008)
*J. Atmos. Sci.*, 65, 2218-2236.
- GCCN defined as > 1 μm dry diameter
- At concentrations of 10⁻² to 10⁻⁴ cm⁻³ (10-0.1 per liter)
- Produce drizzle embryos that bridge the coalescence gap
- Drops reach >20 μm radius by condensation alone in sub-cloud layer

---

## Berry & Reinhardt in Thompson — Where to Modify

### Current Thompson Code (module_mp_thompson.F, ~line 2178)

```fortran
if (rc(k).gt. 0.01e-3) then
  Dc_g = ((ccg(3,nu_c)*ocg2(nu_c))**obmr / lamc) * 1.E6
  Dc_b = (xDc*xDc*xDc*Dc_g*Dc_g*Dc_g - xDc**6)**(1./6.)
  zeta1 = 0.5*((6.25E-6*xDc*Dc_b**3 - 0.4) + abs(...))
  zeta = 0.027*rc(k)*zeta1
  taud = 0.5*((0.5*Dc_b - 7.5) + abs(0.5*Dc_b - 7.5)) + R1
  tau  = 3.72/(rc(k)*taud)
  prr_wau(k) = zeta/tau
endif
```

### GCCN Implementation (integrated 2026-04-16)

After the Berry-Reinhardt autoconversion, the full GCCN lifecycle code runs:

```fortran
! Full GCCN lifecycle: activation → growth → collection
if (rc(k).gt.0.01e-3 .and. ngccn1d(k).gt.1.0D3) then

   ! 1. Kappa-Kohler activation (temperature-dependent)
   A_koh = 4.0D0 * sigma_water * Mw_water / (Rgas_kk * temp(k) * rho_w_kk)
   ss_crit_gccn = DSQRT(4.0D0 * A_koh**3 / (27.0D0 * kappa_KCl * Dd_salt**3))

   ! 2. Condensational growth: R(t+dt) = sqrt(R^2 + 2*G*ss*dt)
   R_current = DSQRT(R_gccn_min**2 + 2.0D0 * G_growth * ss_ambient * dtsave)

   ! 3. Size-dependent V (Beard 1976) and E (Hall 1980) lookup
   ! V: 0 → 0.12 → 0.25 → 0.50 m/s
   ! E: 0 → 0.05 → 0.2 → 0.5 → 0.65 → 0.8

   ! 4. Collection rate and add to accretion pathway
   prr_gccn(k) = PI * R_current**2 * V_gccn_drop * E_gccn_coll * rc(k) * N_gccn_act
   prr_rcw(k) = prr_rcw(k) + prr_gccn(k)  ! accretion, NOT autoconversion

   ! 5. Cloud droplet depletion + rain number production
   ! 6. Wet scavenging of GCCN by rain (below cloud)
endif
```

Note: This replaces the earlier simplified version that used fixed E=0.6, V=0.25, R=50μm.

### Key Thompson Parameters

```fortran
D0c = 1.E-6      ! minimum cloud droplet diameter (1 μm)
D0r = 50.E-6     ! minimum rain drop diameter (50 μm)
Nt_c = 100.E6    ! default droplet concentration (maritime, 100/cm³)
am_r = PI*rho_w/6.  ! mass-diameter coefficient
```

---

## Full Reference List

1. Petters, M. D. & Kreidenweis, S. M. (2007). ACP, 7, 1961-1971.
2. Pöhlker, C. et al. (2012). Science, 337(6098), 1075-1078.
3. Hall, W. D. (1980). J. Atmos. Sci., 37, 2486-2507.
4. Berry, E. X. & Reinhardt, R. L. (1974). J. Atmos. Sci., 31, 2127-2135.
5. Jensen, J. B. & Lee, S. (2008). J. Atmos. Sci., 65, 2218-2236.
6. Feingold, G. et al. (1999). J. Atmos. Sci., 56, 4100-4111.
7. Rosenfeld, D. et al. (2010). J. Appl. Meteor. Climatol., 49(7), 1548-1562.
8. Mather, G. K. et al. (1997). J. Appl. Meteor., 36(11), 1433-1447.
9. Beard, K. V. & Ochs, H. T. (1984). J. Atmos. Sci., 41, 1755-1774.
10. Gunthe, S. S. et al. (2009). ACP, 9, 7551-7575.
11. Pöschl, U. et al. (2010). Science, 329(5998), 1513-1516.
