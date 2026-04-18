# GCCN Physics Verification Request

## Context

We are modifying the Thompson microphysics scheme in the MPAS-Atmosphere 
global weather model to add Giant Cloud Condensation Nuclei (GCCN) physics.
This models the effect of hygroscopic salt particles (KCl, NaCl) emitted 
by tropical rainforest trees that accelerate local rain formation.

The standard Thompson scheme treats all aerosols as small CCN (~0.1 um) 
which SUPPRESS rain (Twomey effect). But tree-emitted salt particles are 
GCCN (1-10 um, highly hygroscopic) which ENHANCE rain through coalescence.
We need to add this missing physics.

Please verify every equation, coefficient, unit, and numerical value below.
Point out ANY errors. This will be compiled into Fortran and run in a 
global atmospheric simulation.

---

## Equation 1: Kappa-Kohler Critical Supersaturation

Source: Petters, M. D. and Kreidenweis, S. M. (2007), "A single parameter 
representation of hygroscopic growth and cloud condensation nucleus activity,"
Atmospheric Chemistry and Physics, 7, 1961-1971.

The critical supersaturation at which a dry particle of diameter Dd and 
hygroscopicity parameter kappa activates as a cloud droplet:

```
ss_crit = sqrt(4 * A^3 / (27 * kappa * Dd^3))
```

where the Kelvin curvature parameter A is:

```
A = (4 * sigma_w * Mw) / (R * T * rho_w)
```

Constants:
- sigma_w = 0.072 J/m^2 (surface tension of water at ~298K)
- Mw = 0.018015 kg/mol (molecular weight of water)
- R = 8.314 J/(mol*K) (universal gas constant)
- rho_w = 997 kg/m^3 (density of water)
- T = temperature in Kelvin

At T = 298 K:
```
A = 4 * 0.072 * 0.018015 / (8.314 * 298 * 997)
  = 0.005189 / 2469832
  = 2.1 x 10^-9 m
```

**VERIFY THIS VALUE OF A.**

Kappa values (from Petters & Kreidenweis 2007, Table 1):
- NaCl: kappa = 1.28
- KCl: kappa = 0.99 (derived from thermodynamic properties)
- (NH4)2SO4: kappa = 0.61

**VERIFY THESE KAPPA VALUES.**

For a 2 um dry diameter NaCl particle (kappa = 1.28):
```
Dd = 2.0 x 10^-6 m
ss_crit = sqrt(4 * (2.1e-9)^3 / (27 * 1.28 * (2.0e-6)^3))
        = sqrt(4 * 9.261e-27 / (27 * 1.28 * 8.0e-18))
        = sqrt(3.704e-26 / 2.765e-16)
        = sqrt(1.340e-10)
        = 1.16 x 10^-5
        = 0.00116%
```

**VERIFY THIS CALCULATION. Is ss_crit approximately 0.001% for 2um NaCl?**

For comparison, 0.1 um (NH4)2SO4 (kappa = 0.61):
```
ss_crit = sqrt(4 * (2.1e-9)^3 / (27 * 0.61 * (0.1e-6)^3))
        = sqrt(3.704e-26 / (1.647e-20 * 1.0e-21))
        = sqrt(3.704e-26 / 1.647e-20)
        ... this needs to be recalculated carefully
```

**PLEASE COMPUTE ss_crit for 0.1um (NH4)2SO4 and confirm it is ~0.3%.**

---

## Equation 2: Collision-Coalescence Efficiency

Source: Hall, W. D. (1980), "A detailed microphysical model within a 
two-dimensional dynamic framework," J. Atmos. Sci., 37, 2486-2507.

The gravitational collision efficiency E(R, r) between a collector drop 
of radius R and a collected droplet of radius r:

Values we are using:
- E(R=50 um, r=10 um) = 0.6
- E(R=40 um, r=10 um) = 0.4
- E(R=30 um, r=10 um) = 0.1
- E(R=20 um, r=10 um) = 0.02 (the "coalescence gap")

**VERIFY these collision efficiency values against Hall 1980 or other 
standard references (Pruppacher & Klett, Rogers & Yau).**

The coalescence gap (E near zero for R < 20 um) is the fundamental reason 
why autoconversion from a uniform cloud droplet distribution is slow. 
GCCN-activated drops at 50 um bypass this gap.

**CONFIRM that the coalescence gap concept is physically correct and that 
50 um drops indeed have E ~ 0.6 for collecting 10 um droplets.**

---

## Equation 3: Terminal Velocity

For a 50 um radius water droplet, using Stokes law:

```
V = (2/9) * rho_w * g * R^2 / mu_air
```

where:
- rho_w = 997 kg/m^3
- g = 9.81 m/s^2
- R = 50 x 10^-6 m
- mu_air = 1.8 x 10^-5 Pa*s (dynamic viscosity of air at ~298K)

```
V = (2/9) * 997 * 9.81 * (50e-6)^2 / 1.8e-5
  = 0.2222 * 997 * 9.81 * 2.5e-9 / 1.8e-5
  = 0.2222 * 2.445e-5 / 1.8e-5
  = 0.2222 * 1.358
  = 0.302 m/s
```

Wait, let me redo this more carefully:
```
V = (2/9) * 997 * 9.81 * (50e-6)^2 / (1.8e-5)
  = (2/9) * 997 * 9.81 * 2.5e-9 / 1.8e-5
  = (2/9) * 9780.57 * 2.5e-9 / 1.8e-5
  = (2/9) * 2.445e-5 / 1.8e-5
  = (2/9) * 1.358
  = 0.302 m/s
```

**VERIFY: Is 0.27-0.30 m/s correct for a 50 um (radius) water drop?**

**ALSO: Is Stokes law valid at this size, or should we use a different 
drag formulation? The Reynolds number is Re = 2*rho_air*V*R/mu_air.
At rho_air~1.2 kg/m3, V~0.3, R=50e-6: Re = 2*1.2*0.3*50e-6/1.8e-5 = 2.0.
Stokes is valid for Re << 1. At Re=2, there is some correction needed.**

**What is the correct terminal velocity for a 100 um diameter (50 um radius)
water drop in air?**

---

## Equation 4: GCCN Collection Rate

The continuous collection equation for GCCN drops collecting cloud droplets:

```
dM/dt = pi * R^2 * V * E * LWC * N_gccn
```

where:
- R = GCCN drop radius (m)
- V = terminal velocity of GCCN drop (m/s)
- E = collision-coalescence efficiency (dimensionless)
- LWC = liquid water content of cloud = rc in Thompson (kg/m^3)
- N_gccn = number concentration of GCCN drops (#/m^3)

Units: m^2 * m/s * kg/m^3 * m^-3 = kg/(m^3 * s)

This gives a mass concentration tendency (kg/m^3/s).

In Thompson, the autoconversion variable prr_wau has units of kg/kg/s 
(mixing ratio tendency). To convert:

```
prr_gccn = pi * R^2 * V * E * rc * N_gccn / rho_air
```

Dividing by rho_air (kg/m^3) converts kg/(m^3*s) to kg/(kg*s) = 1/s.

**VERIFY: Is dividing by rho_air the correct way to convert from mass 
concentration tendency to mixing ratio tendency?**

**VERIFY: In the Thompson scheme (module_mp_thompson.F), is prr_wau in 
units of kg/kg/s or kg/m^3/s? This determines whether /rho is needed.**

Looking at the Thompson code:
```fortran
prr_wau(k) = zeta/tau
prr_wau(k) = MIN(DBLE(rc(k)*odts), prr_wau(k))
```
where rc(k) is cloud water mixing ratio in kg/kg and odts is 1/dt.
So prr_wau has units of kg/kg/s (mixing ratio tendency).
And rc(k) in Thompson is mixing ratio (kg/kg), not mass concentration.

**BUT WAIT: if rc(k) is mixing ratio (kg/kg), then the collection equation
should use mixing ratio not mass concentration:**

```
prr_gccn = pi * R^2 * V * E * rc(k) * N_gccn
```

where rc(k) is in kg/kg. But N_gccn is in #/m^3 (number per volume).
Units: m^2 * m/s * kg/kg * m^-3 = kg/(kg*m*s) ??? This doesn't work.

**THERE IS A UNITS ISSUE. PLEASE HELP RESOLVE IT.**

The correct approach may be:
- Convert rc from mixing ratio to mass concentration: rc_mass = rc * rho_air
- Compute collection: dM/dt = pi*R^2*V*E*rc_mass*N_gccn (kg/m^3/s)
- Convert back to mixing ratio: prr_gccn = dM/dt / rho_air (kg/kg/s)
- Net: prr_gccn = pi*R^2*V*E*rc*N_gccn (if rc is mixing ratio)

Wait, that simplifies back. Let me think again...

rc_mass = rc(k) * rho(k)   [kg/m^3]
dM/dt = pi * R^2 * V * E * rc_mass * N_gccn  [kg/m^3/s]... 

No, units: m^2 * m/s * kg/m^3 * #/m^3 = kg*#/(m^4*s)
This has an extra # and m^-1.

The standard continuous collection equation is:
```
dq_r/dt = pi * R^2 * V_R * E * q_c * N_R
```
where q_c is cloud water mass concentration (kg/m^3) and N_R is collector
number concentration (#/m^3). This gives kg/(m^3*s) * m^-3 = ...

**PLEASE DERIVE THE CORRECT CONTINUOUS COLLECTION EQUATION WITH PROPER 
UNITS, STARTING FROM FIRST PRINCIPLES, AND SHOW WHAT THE FORTRAN CODE 
SHOULD LOOK LIKE IN THE CONTEXT OF THOMPSON'S prr_wau.**

---

## Equation 5: Integration into Thompson Berry-Reinhardt

The current Thompson autoconversion:
```fortran
!..Autoconversion follows Berry & Reinhardt (1974)
if (rc(k).gt. 0.01e-3) then
  ...
  prr_wau(k) = zeta/tau
  prr_wau(k) = MIN(DBLE(rc(k)*odts), prr_wau(k))
  pnr_wau(k) = prr_wau(k) / (am_r*nu_c*200.*D0r*D0r*D0r)  ! RAIN2M
  pnc_wau(k) = MIN(DBLE(nc(k)*odts), ...)                    ! Qc2M
endif
```

Our proposed addition after this block:
```fortran
if (prr_gccn(k) .gt. 0.0) then
   prr_wau(k) = prr_wau(k) + prr_gccn(k)
   prr_wau(k) = MIN(DBLE(rc(k)*odts), prr_wau(k))
   pnr_wau(k) = pnr_wau(k) + prr_gccn(k)/(am_r*D0r*D0r*D0r)
   pnc_wau(k) = pnc_wau(k) + prr_gccn(k)/(am_r*mvd_c(k)**3)
   pnc_wau(k) = MIN(DBLE(nc(k)*odts), pnc_wau(k))
endif
```

**VERIFY: Is adding prr_gccn to prr_wau the correct approach? Or should 
GCCN collection be a separate tendency term (like prr_rcw for rain 
collecting cloud water)?**

**VERIFY: Are the pnr_wau and pnc_wau adjustments correct for the 
number tendencies?**

---

## Summary of Values to Verify

| Parameter | Our Value | Source | Verify? |
|-----------|-----------|--------|---------|
| A (Kohler, 298K) | 2.1e-9 m | P&K 2007 | YES |
| kappa(NaCl) | 1.28 | P&K 2007 | YES |
| kappa(KCl) | 0.99 | derived | YES |
| ss_crit(2um NaCl) | 0.001% | calculated | YES |
| E(50um,10um) | 0.6 | Hall 1980 | YES |
| E(20um,10um) | 0.02 | Hall 1980 | YES |
| V(50um drop) | 0.27-0.30 m/s | Stokes | YES |
| Collection equation | see above | first principles | YES |
| Units of prr_wau | kg/kg/s | Thompson code | YES |
| GCCN fraction | 1% of nwfa | estimate | DISCUSS |
| Salt dry diameter | 2 um | Rosenfeld 2010 | YES |
| Activated wet radius | 50 um | Kohler equilibrium | YES |

---

## Key Papers to Reference

1. Petters & Kreidenweis (2007) ACP 7:1961 — kappa-Kohler theory
2. Hall (1980) J.Atmos.Sci. 37:2486 — collision efficiencies
3. Berry & Reinhardt (1974) J.Atmos.Sci. 31:2127 — autoconversion
4. Jensen & Lee (2008) J.Atmos.Sci. 65:2218 — GCCN parameterization
5. Pohlker et al. (2012) Science 337:1075 — Amazon salt particles
6. Rosenfeld et al. (2010) J.Appl.Met.Clim. 49:1548 — salt seeding
7. Pruppacher & Klett (2010) "Microphysics of Clouds" — general reference
