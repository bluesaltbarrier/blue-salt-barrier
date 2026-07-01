# The Blue Salt Barrier

**An open research project on rainforest biogenic salt aerosols in Earth's climate system.**

- **Preprint (v5, EarthArxiv Version 3):** [10.31223/X5H19T](https://doi.org/10.31223/X5H19T) &nbsp; *(EarthArxiv preserves version history; the DOI resolves to the latest version — v5 — with v4 retained as Version 2 and v3 as Version 1)*
- **Software archive (Zenodo, v5.0):** DOI minted on release — until then, cite the concept DOI below, which always resolves to the latest version.
- **Zenodo concept DOI** (always latest version): [10.5281/zenodo.19739391](https://doi.org/10.5281/zenodo.19739391)
- **Previous software archives:** v4.0 [10.5281/zenodo.20071932](https://doi.org/10.5281/zenodo.20071932) · v3.0 [10.5281/zenodo.19739392](https://doi.org/10.5281/zenodo.19739392)
- **Corrigendum to v4:** [`corrigendum_v4_2026-05-23.md`](corrigendum_v4_2026-05-23.md) — documents the initialization defect that led to the v4 retraction.
- **Website:** https://bluesaltbarrier.github.io/blue-salt-barrier/
- **Docker container:** `ghcr.io/bluesaltbarrier/mpas8-gccn:slim` (2.2 GB)
- **License:** CC BY 4.0 for text/figures; MPAS-derived code follows the original MPAS license.

> **⚠️ v5 corrects and retracts the v4 lead finding.** The v4 preprint reported a statistically-significant reduction in northward latent-heat transport at 30°N of −80 ± 22 TW (p = 0.0013). A post-publication audit found this was an **initialization-defect artifact**: four of the five ensemble members were built without the aerosol fields (`nwfa`/`nifa`), so the model silently substituted a hard-coded globally-uniform pristine background instead of the intended spatially-varying climatology, which artificially suppressed inter-year variance. Re-running all five pairs with a corrected, verified initialization gives **−12 ± 101 TW (p = 0.80)** — indistinguishable from zero. **The v4 30°N transport finding is retracted.** See the corrigendum for the full diagnosis.

## Revision history

| Version | Date | State | Notes |
|---|---|---|---|
| v1 | 2026-04-17 | **withdrawn** | Post-submission audit discovered the Thompson driver never called the GCCN tracer in the compiled binary (coupling bug). v1 results reflected a Twomey-only response, not GCCN warm-rain seeding. Preserved at git tag `v1-archived-2026-04-18`. |
| v2 | 2026-04-19 | superseded | Coupling bug fixed; January 120 km paired run added. Drafted but superseded by v3. |
| v3 | 2026-04-25 | superseded | Added the Phase 7 Pöhlker-anchored baseline-CCN matrix (four single-pair configurations). Headline v3 claim was a baseline-dependent Amazon ΔP sign-flip. EarthArxiv Version 1; Zenodo v3.0 [10.5281/zenodo.19739392](https://doi.org/10.5281/zenodo.19739392). |
| v4 | 2026-05-07 | **superseded — lead finding retracted** | Introduced the Heikenfeld et al. (2019, *ACP*) prescribed-CCN methodology and reported a 5-pair January 120 km ensemble (Phase 9). **Its lead finding (−80 ± 22 TW at 30°N, p = 0.0013) is retracted** — an initialization-defect artifact (see corrigendum). EarthArxiv Version 2; Zenodo v4.0 [10.5281/zenodo.20071932](https://doi.org/10.5281/zenodo.20071932). |
| **v5** | **2026-06-30** | **current** | Corrects the v4 ensemble with a verified initialization pipeline (four-zone check on every init file). Re-running all five January pairs gives **30°N ΔLHF = −12 ± 101 TW (p = 0.80)** — not resolved; the v4 finding is retracted. Adds a **July seasonal-robustness ensemble** (same null) and a **cloud-microphysics consistency check** at the Amazon source (5/5 droplet doubling). Substantive new contributions: a **regime-dependent precipitation bifurcation** across the multi-year ensemble, and the methodological case for an **initial-condition perturbation ensemble** (a completed 5-member 2023 pilot confirms the apparent +159 TW single-run outlier was a chaotic draw; extending to N = 30). EarthArxiv Version 3; Zenodo v5.0. |

## The Hypothesis

Equatorial rainforest trees and their associated fungi emit hygroscopic potassium-salt (KCl) nanoparticles in the accumulation-mode size range (Pöhlker et al. 2012 reported D<sub>g</sub> = 150 nm, σ<sub>g</sub> = 1.43 from ATTO observations). These particles activate readily as cloud condensation nuclei in the tropical boundary layer and accelerate warm-rain formation. Our working hypothesis is that this salt-driven cloud seeding retains latent heat near the equator by raining out moisture before it can be transported poleward through the Hadley circulation — modulating the meridional heat-transport budget. Deforestation removes this biogenic aerosol source — a mechanism not explicitly represented in current mainstream climate models as a dedicated vegetation-linked warm-rain pathway.

## Key Findings (v5)

### The corrected transport result — not statistically resolved

Re-running all five January pairs (2022–2026) at 120 km with a corrected, four-zone-verified initialization (Pöhlker-pristine over IGBP-2 forest cells, GoCart climatology elsewhere, held by the prescribed-CCN reset) gives:

- **30°N ΔLHF = −12 ± 101 TW (t = −0.26, p = 0.80, 4/5 pairs negative)** — indistinguishable from zero.
- A **v5 July** seasonal-robustness ensemble (2021–2025) shows the same null: 30°N = −30 ± 92 TW (p = 0.51).
- The published v4 significance was an artifact: σ rose from 22 TW (defective globally-uniform background) to 101 TW once realistic CCN gradients were restored. **No transport metric is statistically resolved at N = 5.**

### The mechanism's first step is reproduced (consistency check, not a new finding)

At the Amazon source, the K-salt 2× perturbation produces the expected Twomey/Köhler activation response in **all five** corrected pairs — cloud-droplet number +79 to +105 % (mean ≈ +91 %), cloud liquid water path positive every year. This is the textbook response any aerosol-aware scheme must produce given a doubling of CCN; we report it as confirmation that the corrected pipeline applies the forcing as designed, **not** as a discovery.

### The substantive new contributions

- **Regime-dependent precipitation bifurcation.** The same constant microphysical forcing produces sign-dependent Amazon-mean precipitation by year (3 pairs invigoration, 2 suppression) — the aerosol-cloud duality of Stevens & Feingold (2009), demonstrated cleanly across an internally-consistent multi-year ensemble. (Amazon-mean ΔP itself is unresolved: +2.6 ± 11.3 mm/30-day, p = 0.64.)
- **The transport response is dominated by internal variability.** A decisive natural experiment — two near-identical weak La Niña Januaries (2022 and 2023) producing opposite-sign responses (−52.8 and +158.7 TW) — shows no resolvable initial-state predictor controls the per-pair sign.
- **A completed initial-condition perturbation pilot.** Re-running the 2023 pair as a 5-member ensemble (tiny ≈0.01 K IC perturbations) gives a forced mean of −28 ± 29 TW (4/5 negative, t = −0.97); **no member reproduces the +159 TW single run**, confirming it was a chaotic draw. This is the experiment that can resolve the forced transport magnitude; it is being extended to N = 15 (checkpoint) then N = 30.

### Retractions carried forward from earlier revisions

- **v4 30°N transport finding** (−80 ± 22 TW, p = 0.0013) — retracted (initialization defect; corrigendum).
- **v3 polluted-baseline Amazon ΔP sign-flip narrative** — retired in v4, still retired: the Thompson single-species framework cannot represent real multi-species pollution chemistry; the proper test needs MPAS-CMAQ / WRF-Chem-MOSAIC (planned follow-up).
- **v3 polar-temperature claims, the polar-ice-survival argument, and the two-pathway framework** — retracted in v4, still retracted: polar temperatures are not statistically resolved at N = 5.

### Limitations

All v3-era phases (1–7) are single-pair (N = 1). The v4/v5 ensembles are 5 pairs at 120 km on a single configuration; none is convection-permitting (that needs ≤ 30 km and HPC). No detection or attribution transport claim is made. Definitive quantification of the forced transport response requires the initial-condition perturbation ensemble (above), larger single-realization ensembles, additional seasons, multi-species chemistry, and convection-permitting resolution.

## Read More

- **[index.html](index.html)** — the visual, web-native summary
- **[publication_draft_v3.html](publication_draft_v3.html)** — the full v5 paper (methods, equations, results, corrected ensembles, perturbation pilot)
- **[corrigendum_v4_2026-05-23.md](corrigendum_v4_2026-05-23.md)** — the formal correction of the v4 record
- **[jan_v2_rerun/](jan_v2_rerun/)** — the corrected initialization pipeline and four-zone verification that produced the v5 January ensemble
- **[reproducibility/REPRODUCE.md](reproducibility/REPRODUCE.md)** — step-by-step replication guide
- **[Theory/gccn_live_code.F](Theory/gccn_live_code.F)** — the live Fortran excerpt for the GCCN physics, extracted from the patched MPAS container
- **[Theory/gccn_physics_references.md](Theory/gccn_physics_references.md)** — equations and citations
- **[Theory/experiment_plan.md](Theory/experiment_plan.md)** — experimental design

## Tools Used

- **MPAS-Atmosphere** v7.0 and v8.3.1 (NCAR/LANL) — global atmospheric model on a Voronoi mesh
- **Thompson microphysics** — extended with a dedicated GCCN tracer (κ-Köhler activation, Rogers & Yau condensational growth, Hall 1980 collision efficiency, Beard 1976 terminal velocity, wet scavenging); v4/v5 use the Heikenfeld (2019) prescribed-CCN methodology
- **Claude Code** (Anthropic) — built Docker containers, wrote Fortran modifications, ran and analyzed experiments, and (on review) identified the v4 initialization defect
- **ChatGPT** (OpenAI) — cross-verified the microphysics equations during design and caught three errors before the Fortran was written
- **Consumer laptop** (Intel i7-12700H, 64 GB RAM, Docker Desktop on Windows 11) — all simulations

## Reproduce This Research

**Fastest path — pull the pre-built Docker container (2.2 GB, free, public):**

```bash
docker pull ghcr.io/bluesaltbarrier/mpas8-gccn:slim
docker run -d --name mpas8 -v mpas_data:/mpas \
  ghcr.io/bluesaltbarrier/mpas8-gccn:slim sleep infinity
```

The image contains MPAS v8.3.1 compiled with the GCCN patches, Thompson modifications, lookup tables, and namelist templates. Then:

- **v5 corrected January ensemble** — the corrected initialization pipeline is in [`jan_v2_rerun/`](jan_v2_rerun/): `step1_build_inits.sh` injects the climatological `nwfa`/`nifa` fields from a verified-correct source into each year's init file *before* the IGBP-2 pristine modification, and `verify_jan_v2_data.py` runs the **four-zone check** (Amazon IGBP-2 cells, non-IGBP-2 cells, global mean, latitude bands) that aborts on any drift. `step2_run_ensemble.sh` runs the five SALT/NOSALT pairs (resume-safe). `compare_v2_vs_v4_fast.py` reproduces the corrected-vs-defective comparison.
- **v3-era single-pair and Phase 7 matrix** — follow [reproducibility/REPRODUCE.md](reproducibility/REPRODUCE.md) Steps 1–9.
- **v4 (retracted) ensemble** — the original v4 run scripts are preserved in `reproducibility/` for the record; note that this ensemble is the one the corrigendum retracts.

**What's NOT included here:** the ~200 GB of simulation output NetCDF files (available on request; Zenodo archive of diagnostics planned) and the WPS preprocessing toolchain (available at https://github.com/wrf-model/WPS).

**Minimum hardware:** 16 GB RAM, 4 cores, 100 GB free disk. Recommended: 64 GB RAM, 12 cores. No GPU required.

## How to Contribute

This research is explicitly open and incomplete. We invite:

- **Anyone with cluster/cloud compute — the highest-value contribution right now: the initial-condition perturbation ensemble.** Re-run the 2023 January pair (or others) as a 20–30-member ensemble with tiny IC perturbations through both SALT and NOSALT arms, on a single machine with an identical binary. This is the experiment that resolves whether the forced K-salt transport response is small-but-real, regime-conditional, or chaotically dominated. A 5-member pilot is complete and public.
- **HPC-enabled climate modelers** — replicate the corrected v5 ensemble at convection-permitting resolution (≤ 30 km) to test whether anything survives when the convective parameterization stops dominating tropical rainfall.
- **Researchers with compute** — extend the single-realization ensembles back to 2015 (N = 11) using the same NCAR RDA d084.1 GFS analyses, adding strong El Niño years, to test the candidate climate-mode correlations recorded as hypotheses in the paper.
- **Multi-species aerosol-cloud modelers** — integrate the K-salt pathway into MPAS-CMAQ (Wong et al. 2024) or WRF-Chem with MOSAIC (Polonik et al. 2020) to properly test K-salt-versus-pollution chemistry — the test the single-species framework cannot do.
- **Cloud microphysicists** — review the prescribed-CCN patch and GCCN lifecycle code; try Morrison or P3 microphysics; note the disclosed giant-CCN (`ngccn`) suppression under the prescribed-CCN patch.
- **Tropical ecologists** — quantify K-salt emission rates by species, canopy density, soil moisture, and season.
- **Conservation and policy researchers** — note that v5 retracts the transport-magnitude and polar-ice arguments; the conservation case now rests on the verified source-step mechanism, the regime-dependent precipitation response, and the pathway's absence from major climate models.

Open an issue or pull request. Fork the repo. Tell us what you find — including negative results.

## Citation

If this work informs your research, please cite both the preprint and the software archive:

- **Preprint (v5):** Lue, B. (2026). *Exploratory MPAS Sensitivity Experiments on Rainforest Biogenic Salt Aerosols, Tropical Rainfall, and Poleward Moisture Transport* (v5). EarthArxiv. [https://doi.org/10.31223/X5H19T](https://doi.org/10.31223/X5H19T) &nbsp; *(the DOI resolves to the latest version; v4 retained as Version 2, v3 as Version 1)*
- **Software archive:** Lue, B. (2026). *Blue Salt Barrier: MPAS-Atmosphere sensitivity experiments on rainforest biogenic salt aerosols (v5.0).* Zenodo. Cite the concept DOI [https://doi.org/10.5281/zenodo.19739391](https://doi.org/10.5281/zenodo.19739391) to always resolve to the latest version.

Underlying tools and observations that should also be cited when appropriate:

- MPAS-Atmosphere: Skamarock, W. C., et al. (2012). *Monthly Weather Review* 140, 3090–3105.
- Biogenic K-salt emission source: Pöhlker, C., et al. (2012). *Science* 337(6098), 1075–1078.
- Prescribed-CCN methodology: Heikenfeld, M., et al. (2019). *Atmos. Chem. Phys.* 19, 2601–2627.
- Microphysics: Thompson & Eidhammer (2014); Hall (1980); Beard (1976); Petters & Kreidenweis (2007).

A machine-readable citation is provided in [`CITATION.cff`](CITATION.cff) — GitHub renders it as a "Cite this repository" button.

## License

Text, figures, and analysis scripts: [Creative Commons Attribution 4.0](LICENSE).
Code modifications to MPAS / Thompson microphysics: retain the original MPAS license terms.

---

**Funded by curiosity. Powered by taxpayer-built science tools. Accelerated by AI. Open for anyone to improve.**
