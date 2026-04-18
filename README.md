# The Blue Salt Barrier

**An open research project on biogenic salt aerosols as a sensitive, unmodeled variable in Earth's heat transport.**

A citizen scientist, two AIs, a laptop, and one question — shared openly so anyone can build on it.

- **Website:** https://bluesaltbarrier.github.io/blue-salt-barrier/
- **Paper draft:** [publication_draft.html](publication_draft.html)
- **Docker container:** `ghcr.io/bluesaltbarrier/mpas8-gccn:slim` (2.2 GB, free, pullable without authentication)
- **License:** CC BY 4.0 for text/figures, MPAS-derived code follows the original MPAS license

## The Hypothesis

Equatorial rainforest trees and their associated fungi emit hygroscopic KCl salt nanoparticles. These particles act as giant cloud condensation nuclei (GCCN), accelerating local rain formation. Our working hypothesis is that this salt-driven cloud seeding modulates tropical precipitation patterns and, via latent heat release, the meridional redistribution of heat on a global scale. Deforestation removes this biogenic aerosol source — a mechanism absent from all current climate models.

## Key Findings (preliminary, single-laptop 240 km simulations)

**Central finding: biogenic salt is a remarkably sensitive variable.** Across five different microphysical implementations of the same hypothesis, the 30°N poleward heat transport response ranged from −153 TW to +153 TW — a swing larger than the entire estimated effect of anthropogenic CO₂ on poleward transport (100–250 TW). This sensitivity itself is the main scientific claim, regardless of which sign is "correct" for the real atmosphere.

Within our most physically complete configuration (April 240 km bug-fixed after independent AI code review):

- **Salt shifts equatorial rain southward** — zonal-mean rainfall rises by +0.62 mm/day at 5°S and falls by −0.31 mm/day at 5°N, toward the winter-ward hemisphere (band average +0.17 mm/day across −10° to +10°).
- **Antarctic cooling:** −1.26 K in the hemisphere entering its winter season.
- **30°S transport reduction:** −61 TW, consistent with a moisture-barrier effect in the winter-ward hemisphere.
- **30°N transport:** +153 TW (increase) — likely an artifact of the 240 km convective parameterization. Testing at convection-permitting resolution (30 km or finer) is the single most important next experiment.

All results are N = 1 single-member 30-day integrations. Weather noise (mean 2.67 K global divergence between CONTROL and NO-SALT) means specific numbers should not yet be treated as statistically significant. A January 120 km paired run with the corrected physics is currently running; a 10-member 240 km ensemble is queued next.

## Read More

- **[index.html](index.html)** — The full story in Apple-style visual format
- **[publication_draft.html](publication_draft.html)** — Full paper with equations, methods, and results
- **[reproducibility/REPRODUCE.md](reproducibility/REPRODUCE.md)** — Step-by-step guide to replicate the experiments
- **[Theory/gccn_live_code.F](Theory/gccn_live_code.F)** — **Authoritative live-code excerpt.** The ground-truth Fortran for the GCCN physics as it actually runs, extracted from the live patched MPAS container. Start here if you want to inspect what produced our results.
- **[Theory/gccn_physics_references.md](Theory/gccn_physics_references.md)** — Physics equations and citations
- **[Theory/experiment_plan.md](Theory/experiment_plan.md)** — Experimental design document

## Tools Used

- **MPAS-Atmosphere v7.0 and v8.3.1** (NCAR/LANL) — global atmospheric model, Voronoi mesh
- **Thompson microphysics** — modified with a dedicated GCCN tracer (κ-Köhler activation, Rogers & Yau condensational growth, Hall 1980 collision efficiency, Beard 1976 terminal velocity, wet scavenging)
- **Claude Code** (Anthropic) — built Docker containers, wrote Fortran modifications, ran and analyzed experiments
- **ChatGPT** (OpenAI) — cross-verified the microphysics equations and caught three errors in early drafts
- A second independent AI (via NVIDIA RAG over our DoubleCheckFolder) — code-reviewed the bug-fixed Fortran and caught three additional implementation bugs, which we subsequently corrected
- **Intel i7-12700H laptop, 64 GB RAM, Docker Desktop on Windows** — all simulations

## Reproduce This Research

**Fastest path — pull the pre-built Docker container (2.2 GB, free, public):**

```bash
docker pull ghcr.io/bluesaltbarrier/mpas8-gccn:slim
docker run -d --name mpas8 -v mpas_data:/mpas \
  ghcr.io/bluesaltbarrier/mpas8-gccn:slim sleep infinity
```

The image contains MPAS v8.3.1 compiled with all our bug-fixed GCCN patches, Thompson microphysics modifications, lookup tables, and namelist templates. Then follow [reproducibility/REPRODUCE.md](reproducibility/REPRODUCE.md) starting at Step 3 (mesh and GFS data download) to run your own paired CONTROL + NO-SALT experiment.

**Full reproducibility stack:** the `reproducibility/` folder has the Dockerfile, both GCCN physics patches (initial + bug-fix), MPAS namelists, and analysis scripts for a from-source build.

**What's included in this repo:** Dockerfiles, physics modifications, namelists, analysis Python scripts, full paper and website, plus the link to the pre-built Docker image.

**What's NOT included here:** the ~200 GB of simulation output NetCDF files (available on request; planned Zenodo archive) and the WPS preprocessing toolchain (GFS → MPAS intermediate conversion — available at https://github.com/wrf-model/WPS).

**Minimum hardware:** 16 GB RAM, 4 cores, 100 GB free disk. Recommended: 64 GB RAM, 12 cores. No GPU required.

## How to Contribute

This research belongs to everyone. We specifically invite:

- **HPC-enabled climate modelers** — run our GCCN code at 30 km or finer (convection-permitting). A single paired run would determine whether the +153 TW at 30°N is real physics or parameterization artifact. This is the highest-value community contribution.
- **Researchers with cluster or cloud compute** — run 10+ member ensembles, or 90+ day integrations, to directly test the variance-amplification hypothesis.
- **Cloud microphysicists** — review the GCCN lifecycle code. Try the same hypothesis with Morrison or P3 microphysics.
- **Tropical ecologists** — quantify salt emission rates by tree species, canopy density, soil moisture, and diurnal/seasonal cycles.
- **Citizen scientists** — pull the Docker container, reproduce the April 240 km experiment, try a different season. Three days of laptop time produces a publishable replication.
- **Conservation scientists and policy researchers** — help frame the implications for forest preservation given our sensitivity finding.

Open an issue or pull request on this repo. Fork it. Run your own experiments. Tell us what you find — including negative results.

## Citation

If this work informs your research, please cite:

- This repository: `The Blue Salt Barrier project, bluesaltbarrier/blue-salt-barrier on GitHub, 2026`
- The underlying MPAS: Skamarock, W. C., et al. (2012), *Monthly Weather Review*, 140, 3090–3105
- The biogenic salt emission source: Pöhlker, C., et al. (2012), *Science*, 337(6098), 1075–1078
- Relevant microphysics: Thompson & Eidhammer (2014), Hall (1980), Beard (1976), Petters & Kreidenweis (2007)

## License

Text, figures, and analysis: [Creative Commons Attribution 4.0](LICENSE).
Code modifications to MPAS/Thompson: retain original MPAS license terms.

---

**Funded by curiosity. Powered by taxpayer-built science tools. Accelerated by AI. Open for anyone to improve.**
