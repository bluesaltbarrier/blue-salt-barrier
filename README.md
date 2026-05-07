# The Blue Salt Barrier

**An open research project on rainforest biogenic salt aerosols in Earth's climate system.**

- **Preprint (v4, EarthArxiv):** [10.31223/X5H19T](https://doi.org/10.31223/X5H19T) &nbsp; *(EarthArxiv preserves version history; the DOI now resolves to v4, with v3 retained as Version 1)*
- **Software archive (Zenodo, v4.0):** [10.5281/zenodo.20071932](https://doi.org/10.5281/zenodo.20071932) &nbsp; [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20071932.svg)](https://doi.org/10.5281/zenodo.20071932)
- **Zenodo concept DOI** (always latest version): [10.5281/zenodo.19739391](https://doi.org/10.5281/zenodo.19739391)
- **Website:** https://bluesaltbarrier.github.io/blue-salt-barrier/
- **Docker container:** `ghcr.io/bluesaltbarrier/mpas8-gccn:slim` (2.2 GB)
- **License:** CC BY 4.0 for text/figures; MPAS-derived code follows the original MPAS license.

## Revision history

| Version | Date | State | Notes |
|---|---|---|---|
| v1 | 2026-04-17 | **withdrawn** | Post-submission audit discovered the Thompson driver never called the GCCN tracer in the compiled binary (coupling bug). v1 results reflected a Twomey-only response, not GCCN warm-rain seeding. Preserved at git tag `v1-archived-2026-04-18` for history. |
| v2 | 2026-04-19 | superseded | Coupling bug fixed; January 120 km paired run added. Drafted but superseded by v3 after a deeper reviewer pass. |
| v3 | 2026-04-25 | superseded | Added the Phase 7 Pöhlker-anchored baseline-CCN matrix: four single-pair K-salt configurations at 120 km. Headline v3 claim was a baseline-dependent Amazon ΔP sign-flip. EarthArxiv-published as Version 1 of record [10.31223/X5H19T](https://doi.org/10.31223/X5H19T); Zenodo v3.0 archive at [10.5281/zenodo.19739392](https://doi.org/10.5281/zenodo.19739392). |
| **v4** | **2026-05-07** | **current** | Introduces the Heikenfeld et al. (2019, *ACP*) prescribed-CCN methodology and reports a 5-pair January 120 km ensemble (Phase 9) on the Pöhlker-D<sub>g</sub>-matched configuration. **Lead finding: 30°N northward latent-heat transport reduced by −80 ± 22 TW (5/5 pairs negative, p = 0.0013)** — first statistically resolved finding in the paper series. Retracts v3's polluted-baseline sign-flip narrative (single-species framework cannot represent multi-species pollution chemistry) and the polar-temperature / polar-ice-survival claims (not statistically resolved at N = 5). Multi-species follow-up planned via MPAS-CMAQ. EarthArxiv Version 2 at the same DOI [10.31223/X5H19T](https://doi.org/10.31223/X5H19T); Zenodo v4.0 archive at [10.5281/zenodo.20071932](https://doi.org/10.5281/zenodo.20071932). |
| v5 | planned | future | July seasonal-robustness ensemble to test whether the 30°N reduction reverses under SH-winter / NH-summer Hadley geometry. |

## The Hypothesis

Equatorial rainforest trees and their associated fungi emit hygroscopic potassium-salt (KCl) nanoparticles in the accumulation-mode size range (Pöhlker et al. 2012 reported D<sub>g</sub> = 150 nm, σ<sub>g</sub> = 1.43 from ATTO observations). These particles activate readily as cloud condensation nuclei in the tropical boundary layer and accelerate warm-rain formation. Our working hypothesis is that this salt-driven cloud seeding retains latent heat near the equator by raining out moisture before it can be transported poleward through the Hadley circulation — modulating the meridional heat-transport budget. Deforestation removes this biogenic aerosol source — a mechanism not explicitly represented in current mainstream climate models as a dedicated vegetation-linked warm-rain pathway.

## Key Findings

### v4 lead finding (statistically resolved at N = 5)

In a 5-pair January 120 km prescribed-CCN ensemble (starts 2022 through 2026) on the Pöhlker-D<sub>g</sub>-matched pristine configuration, **K-salt addition produces a robust reduction in northward latent heat transport at 30°N**:

- Mean **−80 ± 22 TW**, all 5 pairs negative
- t = −7.98, **p = 0.0013** (one-sample t-test against zero)
- Sign-consistent positive 30°S response (+33 TW ensemble mean — reduced southward export in the northward-positive convention; not resolved at N = 5 but in the direction the hypothesis predicts)
- Two-sided geometry: equator exporting less latent heat toward both poles — the canonical fingerprint of equatorial heat retention

This is the only metric across the entire paper series that survives a one-sample t-test against zero. v4 makes no quantitative claim about polar temperatures, ice-mass balance, Amazon-mean rainfall, or 30°S transport magnitude — those are not statistically resolved at N = 5 and require larger ensembles, longer integrations, July repeats, and convection-permitting resolution to settle.

### v3 single-pair findings preserved as historical context

Across **ten v3-era single-pair MPAS-Atmosphere integrations** (Phases 2–7), 30°N poleward latent-heat transport ranged from −211 TW to +153 TW (σ ≈ 126 TW). The v4 ensemble narrows this dramatically when implementation is held fixed at the Pöhlker-D<sub>g</sub>-matched configuration — the wide v3 spread reflected microphysical-implementation differences plus single-realization weather variance, not variance amplification of K-salt itself.

### v3 claims retracted in v4

- **Polluted-baseline Amazon ΔP sign-flip narrative.** v3 reported Amazon rain suppression of −17.1 mm/30-day at MPAS's default polluted baseline and enhancement of +5.4 to +5.6 mm at the Pöhlker-anchored pristine baseline, framing this as evidence of K-salt's regime-dependent hydrological effect. **v4 retracts this claim** because the Thompson aerosol-aware single-species framework cannot represent the chemistry of real anthropogenic pollution (sulfate, biomass-burning soot, secondary organic aerosol) at the levels v3's "polluted" baseline implied. The proper test of K-salt-versus-pollution chemistry interactions requires multi-species frameworks (MPAS-CMAQ; WRF-Chem with MOSAIC) and is the planned subject of a follow-up manuscript.
- **Polar-temperature claims and polar-ice-survival policy implication.** v3 cited a single-pair April Antarctic cooling of −1.26 K and built a polar-ice-preservation argument scaled against the pre-industrial Antarctic warming signal. **v4 retracts this** because the v4 5-pair ensemble shows polar temperatures are not statistically resolved at N = 5 (Arctic +1.16 ± 3.40 K, p = 0.49; Antarctic −0.50 ± 1.10 K, p = 0.36); the single-pair value is one weather realization within the ensemble's noise floor. Whether reduced 30°N latent-heat export eventually translates into measurable polar-ice consequences is an open question for higher-fidelity follow-up.
- **Two-pathway polar-temperature framework** (Northern path → cooling, Southern path → warming). v4 retracts this as not supported by the data: the framework matched the April single-pair but was contradicted by the January single-pair, and the v4 ensemble cannot test it.

### Limitations (repeated explicitly)

v3 phases (1–7) are single-pair (N = 1) at 120 or 240 km. v4 (Phase 9) is a 5-pair ensemble at 120 km on a single configuration; it resolves the 30°N transport response but not other metrics. None of this is convection-permitting (true convection-permitting needs 30 km or finer resolution and HPC compute). No detection or attribution claim beyond the v4 30°N ensemble result is made. Definitive testing requires larger ensembles, additional seasons, multi-species chemistry frameworks, and convection-permitting resolution.

## Read More

- **[index.html](index.html)** — the visual, web-native summary
- **[publication_draft.html](publication_draft.html)** — full paper with methods, equations, and results
- **[reproducibility/REPRODUCE.md](reproducibility/REPRODUCE.md)** — step-by-step replication guide (Steps 1–9, including the Phase 7 matrix)
- **[Theory/gccn_live_code.F](Theory/gccn_live_code.F)** — the live Fortran excerpt for the GCCN physics, extracted from the patched MPAS container (ground truth)
- **[Theory/gccn_physics_references.md](Theory/gccn_physics_references.md)** — equations and citations
- **[Theory/experiment_plan.md](Theory/experiment_plan.md)** — experimental design

## Tools Used

- **MPAS-Atmosphere** v7.0 and v8.3.1 (NCAR/LANL) — global atmospheric model on a Voronoi mesh
- **Thompson microphysics** — extended with a dedicated GCCN tracer (κ-Köhler activation, Rogers & Yau condensational growth, Hall 1980 collision efficiency, Beard 1976 terminal velocity, wet scavenging)
- **Claude Code** (Anthropic) — built Docker containers, wrote Fortran modifications, ran and analyzed experiments
- **ChatGPT** (OpenAI) — cross-verified the microphysics equations during the design phase and caught three errors (terminal-velocity approximation, pathway assignment, critical supersaturation for (NH₄)₂SO₄) that were corrected before the Fortran was written
- **Consumer laptop** (Intel i7-12700H, 64 GB RAM, Docker Desktop on Windows 11) — all simulations

## Reproduce This Research

**Fastest path — pull the pre-built Docker container (2.2 GB, free, public):**

```bash
docker pull ghcr.io/bluesaltbarrier/mpas8-gccn:slim
docker run -d --name mpas8 -v mpas_data:/mpas \
  ghcr.io/bluesaltbarrier/mpas8-gccn:slim sleep infinity
```

The image contains MPAS v8.3.1 compiled with all the bug-fixed GCCN patches, Thompson microphysics modifications, lookup tables, and namelist templates. Then follow [reproducibility/REPRODUCE.md](reproducibility/REPRODUCE.md):

- Steps 1–8 build and run the baseline CONTROL + NO-SALT pair (240 km April or 120 km January).
- **Step 9 adds the Phase 7 baseline-CCN matrix** (v3-era single-pair) — apply `patch_pohlker_ccn.sh`, `patch_pohlker_l4.sh`, or `patch_pohlker_size.sh` for each configuration, run the paired experiment, then use the analysis scripts (`analyze_pohlker_pair.py`, `plot_8run_summary.py`, `make_paper_composites.py`, `column_diag_ensemble_l4.py`).
- **v4 reproducibility section** (added in v4) — apply `apply_prescribed_ccn_patch.py` (Heikenfeld 2019 prescribed-CCN methodology) on top of the Pöhlker-l=4 patch, run the 5-pair January ensemble (`run_ensemble_120km_2022.sh` through `run_ensemble_2023_2026.sh` for years 2022–2026), then generate Figures 21–24 with `v4_figures.py` and the additional ensemble metrics with `v4_table_column.py`. Boundary-layer-preservation diagnostics (`bl_preservation_120km_prescribed_ccn.py`, `bl_preservation_240km_prescribed_ccn.py`) reproduce Figure 20 in the manuscript.

**Full reproducibility stack:** `reproducibility/` contains Dockerfiles, all GCCN patches (initial, bug-fix, Phase 7, v4 prescribed-CCN), MPAS namelists, run scripts (`reproducibility/run_scripts/`), and analysis scripts for a from-source build.

**What's NOT included here:** the ~200 GB of simulation output NetCDF files (available on request; planned Zenodo archive) and the WPS preprocessing toolchain (GFS → MPAS intermediate conversion — available at https://github.com/wrf-model/WPS).

**Minimum hardware:** 16 GB RAM, 4 cores, 100 GB free disk. Recommended: 64 GB RAM, 12 cores. No GPU required.

## How to Contribute

This research is explicitly open and incomplete. We invite:

- **HPC-enabled climate modelers** — replicate the v4 prescribed-CCN ensemble at convection-permitting resolution (≤ 30 km). A 5-pair 30 km ensemble would directly test whether the v4 30°N transport reduction (−80 ± 22 TW at 120 km) survives when the convective parameterization stops dominating tropical rainfall. Highest-value community contribution.
- **Researchers with cluster/cloud compute** — extend the v4 ensemble to 10–20 pairs and add a July seasonal-robustness ensemble (planned for v5). Push Amazon ΔP, 30°S transport, polar temperatures, and Arctic 10 m wind into statistical resolution. 90+ day integrations would reduce per-realization noise on intraseasonal modes (MJO, monsoon variability).
- **Multi-species aerosol-cloud modelers** — integrate the K-salt emission pathway into MPAS-CMAQ (Wong et al. 2024) or WRF-Chem with MOSAIC (Polonik et al. 2020). This is the path to properly testing K-salt-versus-pollution chemistry interactions that v4 retracted from v3 because the Thompson aerosol-aware single-species framework cannot resolve them.
- **Cloud microphysicists** — review the prescribed-CCN patch (`reproducibility/mpas_modifications/apply_prescribed_ccn_patch.py`) and the GCCN lifecycle code; try the same hypothesis with Morrison or P3 microphysics; check Pöhlker-D<sub>g</sub> activation handling.
- **Tropical ecologists** — quantify K-salt emission rates by tree species, canopy density, soil moisture, and diurnal/seasonal cycles. Pre-industrial vs. current vs. projected-deforestation emission scenarios would let modelers test forcing magnitudes directly.
- **Citizen scientists** — pull the Docker container, reproduce the v4 5-pair January ensemble, or try a single 30 km pair if you have HPC access. Three days of laptop time per pair-half (5 pairs ≈ 7–14 days for the full v4 reproduction).
- **Conservation scientists and policy researchers** — help frame implications for forest preservation. Note that v4 retracts the explicit polar-ice-survival argument; the conservation argument now rests on the 30°N latent-heat-export reduction and the broader implication that this rainforest-emission warm-rain pathway is missing from major climate models as a dedicated vegetation-linked process.

Open an issue or pull request. Fork the repo. Tell us what you find — including negative results.

## Citation

If this work informs your research, please cite both the preprint and the software archive:

- **Preprint (v4):** Lue, B. (2026). *Exploratory MPAS Sensitivity Experiments on Rainforest Biogenic Salt Aerosols, Tropical Rainfall, and Poleward Moisture Transport* (v4). EarthArxiv. [https://doi.org/10.31223/X5H19T](https://doi.org/10.31223/X5H19T) &nbsp; *(EarthArxiv preserves version history; the DOI resolves to v4, with v3 retained as Version 1)*
- **Software archive (v4):** Lue, B. (2026). *Blue Salt Barrier: MPAS-Atmosphere sensitivity experiments on rainforest biogenic salt aerosols (v4.0).* Zenodo. [https://doi.org/10.5281/zenodo.20071932](https://doi.org/10.5281/zenodo.20071932)
- **Zenodo concept DOI** (cite this if you want the citation to always resolve to the latest version): [https://doi.org/10.5281/zenodo.19739391](https://doi.org/10.5281/zenodo.19739391)

Underlying tools and observations that should also be cited when appropriate:

- MPAS-Atmosphere: Skamarock, W. C., et al. (2012). *Monthly Weather Review* 140, 3090–3105.
- Biogenic K-salt emission source: Pöhlker, C., et al. (2012). *Science* 337(6098), 1075–1078.
- Microphysics: Thompson & Eidhammer (2014); Hall (1980); Beard (1976); Petters & Kreidenweis (2007).

A machine-readable citation is provided in [`CITATION.cff`](CITATION.cff) — GitHub renders it as a "Cite this repository" button.

## License

Text, figures, and analysis scripts: [Creative Commons Attribution 4.0](LICENSE).
Code modifications to MPAS / Thompson microphysics: retain the original MPAS license terms.

---

**Funded by curiosity. Powered by taxpayer-built science tools. Accelerated by AI. Open for anyone to improve.**
