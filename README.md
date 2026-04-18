# The Blue Salt Barrier

**An open research project: how rainforest salt keeps the poles cold.**

A citizen scientist, two AIs, a laptop, and one question that could change how we understand polar ice loss.

Website: [bluesaltbarrier.github.io](https://bluesaltbarrier.github.io) *(update after deployment)*

## The Hypothesis

Equatorial rainforest trees emit hygroscopic salt aerosols that act as giant cloud condensation nuclei (GCCN), triggering local precipitation. This "salt barrier" traps latent heat at the equator. Deforestation removes the salt source, allowing moisture and its heat to travel poleward — a mechanism absent from current climate models.

## Key Results

- **Transport reduction:** −95 TW at 30°N when salt is present (comparable to estimated CO₂-driven transport changes of 100–250 TW)
- **Antarctic cooling:** −1.03 K with salt present (April simulation)
- **Microphysical details matter:** The simplified version gave the wrong transport sign. Only the full GCCN lifecycle (kappa-Köhler activation, condensational growth, Hall 1980 collision efficiencies, Beard 1976 terminal velocities, wet scavenging) produced the correct signal.

## Read More

- **[index.html](index.html)** — The story, in Apple-style visual format
- **[publication_draft.html](publication_draft.html)** — Full paper with equations, methods, and results
- **[Theory/](Theory/)** — Experiment plans, physics references, and design documents

## Tools Used

- **MPAS-Atmosphere** (NCAR/LANL) — global atmospheric model
- **Thompson microphysics** — modified with a dedicated GCCN tracer
- **Claude Code** (Anthropic) — built Docker containers, wrote Fortran modifications, designed experiments
- **ChatGPT** (OpenAI) — cross-verified equations, caught three errors
- **Intel i7-12700H laptop, 64 GB RAM** — all simulations

## Reproduce This Research

The `reproducibility/` folder contains the Dockerfiles, the GCCN physics patch, MPAS namelists, and analysis scripts needed to reproduce the experiments.

See [**reproducibility/REPRODUCE.md**](reproducibility/REPRODUCE.md) for the full step-by-step guide — from building the container to downloading initial conditions to running the analysis.

**What is included:** Dockerfiles, physics modifications, namelists, analysis Python scripts, full paper and website.

**What is NOT included (due to size):** the ~200 GB of simulation output NetCDF files, and the WPS preprocessing toolchain (GFS→MPAS intermediate conversion). The REPRODUCE guide explains how to obtain or regenerate these.

**Minimum hardware:** 16 GB RAM, 4 cores, 100 GB disk. Recommended: 64 GB RAM, 12 cores. No GPU required.

## How to Contribute

This research belongs to everyone. We invite:

- **Cloud microphysicists** to review the GCCN code
- **Tropical ecologists** to improve salt emission inventories
- **Climate modelers** to integrate this into Earth System Models
- **Citizen scientists** to run experiments at different seasons and resolutions
- **Conservation organizations** to quantify the policy implications

Open an issue or pull request. Fork the repo. Run your own experiments.

## License

Text, figures, and analysis: [Creative Commons Attribution 4.0](LICENSE).
Code modifications to MPAS/Thompson: retain original MPAS license terms.

## Citation

If this work informs your research, please cite the repository and the underlying MPAS publications (Skamarock et al. 2012).

---

**Funded by curiosity. Powered by taxpayer-built science tools. Accelerated by AI.**
