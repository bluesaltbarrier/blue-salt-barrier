# The Blue Salt Barrier

**An open research project on rainforest biogenic salt aerosols in Earth's climate system.**

- **Preprint (v3, EarthArxiv):** DOI assignment pending — update here when live.
- **Software archive (Zenodo):** [10.5281/zenodo.19739392](https://doi.org/10.5281/zenodo.19739392) &nbsp; [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19739392.svg)](https://doi.org/10.5281/zenodo.19739392)
- **Website:** https://bluesaltbarrier.github.io/blue-salt-barrier/
- **Docker container:** `ghcr.io/bluesaltbarrier/mpas8-gccn:slim` (2.2 GB)
- **License:** CC BY 4.0 for text/figures; MPAS-derived code follows the original MPAS license.

## Revision history

| Version | Date | State | Notes |
|---|---|---|---|
| v1 | 2026-04-17 | **withdrawn** | Post-submission audit discovered the Thompson driver never called the GCCN tracer in the compiled binary (coupling bug). v1 results reflected a Twomey-only response, not GCCN warm-rain seeding. Preserved at git tag `v1-archived-2026-04-18` for history. |
| v2 | 2026-04-19 | superseded | Coupling bug fixed; January 120 km paired run added. Drafted but superseded by v3 after a deeper reviewer pass. |
| v3 | 2026-04-22 | **current, submitted to EarthArxiv** | Adds the Phase 7 Pöhlker-anchored baseline-CCN matrix: four K-salt pairs testing the regime-dependence hypothesis. Title reframed as exploratory sensitivity experiments; all reviewer critique items addressed. |

## The Hypothesis

Equatorial rainforest trees and their associated fungi emit hygroscopic potassium-salt (KCl) nanoparticles. These particles can act as giant cloud condensation nuclei (GCCN), accelerating warm-rain formation. Our working hypothesis is that this salt-driven cloud seeding modulates tropical precipitation patterns and, via latent-heat release, the meridional redistribution of heat on a global scale. Deforestation removes this biogenic aerosol source — a mechanism not explicitly represented in current mainstream climate models as a dedicated vegetation-linked warm-rain pathway.

## Key Findings (v3 — exploratory, single-member)

Across **ten single-member 30-day MPAS-Atmosphere integrations** spanning five microphysical implementations at 240 km and four Phase 7 Pöhlker-anchored pairs at 120 km:

**1. Implementation sensitivity is large.** Diagnosed 30°N poleward latent-heat transport ranges from **−211 TW to +153 TW** across the ten runs (standard deviation ≈ 126 TW). This range is comparable in magnitude to published estimates of anthropogenic changes in poleward transport. The result is a statement about how strongly biogenic-salt microphysics couples to circulation diagnostics in the model, not a detection claim.

**2. Amazon rainfall response flips sign with baseline aerosol state.** At MPAS's default polluted baseline (~4,400 nwfa/cm³), K-salt addition **suppresses** Amazon rain by −17.1 mm per 30 days. At a Pöhlker-anchored pristine baseline (~150 nwfa/cm³), the same perturbation **enhances** Amazon rain by +5.4 to +5.6 mm. The regime dependence is qualitatively consistent with established aerosol-cloud theory (Twomey vs. GCCN competition at different background CCN concentrations).

**3. At the observationally-matched particle size, far-field impact is modest.** Using Thompson activation index *l* = 4 (160 nm dry diameter, κ = 0.8 — the lookup option closest to Pöhlker 2012's reported Dg = 150 nm, σ_g = 1.43), we see clear **local** Amazon enhancement (+5.4 mm) with only +31 TW at 30°N and +0.12 K Arctic. This is consistent with — though not proof of — the interpretation that rainforest biogenic aerosol traits are shaped by local hydrological feedbacks, not remote climate effects.

**4. Column-level diagnostic confirms the mechanism.** Comparing 10 max-ΔP and 10 min-ΔP Amazon cells, max-ΔP cells (rain enhanced) have weaker, shallower updrafts and are microphysics-bottlenecked — GCCN seeding unlocks warm-rain initiation. Min-ΔP cells (rain suppressed) have strong, deep convective towers already operating at dynamical capacity — added CCN produces smaller, less efficient droplets (Twomey suppression).

### Limitations (repeated explicitly)

All results are N = 1 single-member 30-day integrations at 120 or 240 km. Signals smaller than the chaotic variability between two such runs cannot be distinguished from internal noise. No detection or attribution claim is made. Definitive testing requires ensembles of 5–10 members at convection-permitting resolution (≤ 30 km) with 90+ day integrations.

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
- **Step 9 adds the Phase 7 baseline-CCN matrix** — apply `patch_pohlker_ccn.sh`, `patch_pohlker_l4.sh`, or `patch_pohlker_size.sh` for each configuration, run the paired experiment, then use the new argparse-driven analysis scripts (`analyze_pohlker_pair.py`, `plot_8run_summary.py`, `make_paper_composites.py`, `column_diag_ensemble_l4.py`).

**Full reproducibility stack:** `reproducibility/` contains Dockerfiles, all GCCN patches (initial, bug-fix, Phase 7), MPAS namelists, and analysis scripts for a from-source build.

**What's NOT included here:** the ~200 GB of simulation output NetCDF files (available on request; planned Zenodo archive) and the WPS preprocessing toolchain (GFS → MPAS intermediate conversion — available at https://github.com/wrf-model/WPS).

**Minimum hardware:** 16 GB RAM, 4 cores, 100 GB free disk. Recommended: 64 GB RAM, 12 cores. No GPU required.

## How to Contribute

This research is explicitly open and incomplete. We invite:

- **HPC-enabled climate modelers** — replicate the Phase 7 matrix at convection-permitting resolution (≤ 30 km). A single paired run would determine whether the implementation spread collapses or persists. Highest-value community contribution.
- **Researchers with cluster/cloud compute** — run 10+ member ensembles or 90+ day integrations to directly test the variance-amplification hypothesis.
- **Cloud microphysicists** — review the GCCN lifecycle code; try the same hypothesis with Morrison or P3 microphysics; check Pöhlker-Dg activation handling.
- **Tropical ecologists** — quantify K-salt emission rates by tree species, canopy density, soil moisture, and diurnal/seasonal cycles.
- **Citizen scientists** — pull the Docker container, reproduce the Phase 7 pairs, try a different season. Three days of laptop time produces a publishable replication.
- **Conservation scientists and policy researchers** — help frame implications for forest preservation given the regime-dependent finding.

Open an issue or pull request. Fork the repo. Tell us what you find — including negative results.

## Citation

If this work informs your research, please cite both the preprint and the software archive:

- **Preprint (v3):** Lue, B. (2026). *Exploratory MPAS Sensitivity Experiments on Rainforest Biogenic Salt Aerosols, Tropical Rainfall, and Poleward Moisture Transport.* EarthArxiv. DOI: *pending — will be updated here once assigned.*
- **Software archive:** Lue, B. (2026). *Blue Salt Barrier: MPAS-Atmosphere sensitivity experiments on rainforest biogenic salt aerosols (v3.0).* Zenodo. [https://doi.org/10.5281/zenodo.19739392](https://doi.org/10.5281/zenodo.19739392)

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
