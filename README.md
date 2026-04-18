# The Blue Salt Barrier

**An open research project: how rainforest salt keeps the poles cold.**

A citizen scientist, two AIs, a laptop, and one question that could change how we understand polar ice loss.

Website: [bluesaltbarrier.github.io](https://bluesaltbarrier.github.io) *(update after deployment)*

## The Hypothesis

Equatorial rainforest trees emit hygroscopic salt aerosols that act as giant cloud condensation nuclei (GCCN), triggering local precipitation. This "salt barrier" traps latent heat at the equator. Deforestation removes the salt source, allowing moisture and its heat to travel poleward — a mechanism absent from current climate models.

## Key Results

**The central finding is that biogenic salt is a remarkably sensitive variable.** Across five different microphysical implementations of the same hypothesis, the 30°N poleward heat transport response ranged from −153 TW to +153 TW — a swing larger than the entire estimated effect of anthropogenic CO₂ on poleward transport. This sensitivity, more than any specific transport number, is what this work demonstrates.

Within our most physically complete configuration (April 240 km bug-fixed after independent AI code review):

- **Equatorial rain enhancement:** +0.17 mm/day, matching published cloud-seeding literature (28–60% in field programs)
- **Antarctic cooling:** −1.26 K in the hemisphere entering its winter season
- **30°S transport reduction:** −61 TW (supporting the hypothesis in the winter-ward hemisphere)
- **30°N transport:** +153 TW (increase — may be convective-parameterization artifact at 240 km)

A January 120 km run with the corrected physics is currently in progress.

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

**Fastest path — pre-built Docker container:**

```bash
docker pull ghcr.io/bluesaltbarrier/mpas8-gccn:slim
docker run -d --name mpas8 -v mpas_data:/mpas ghcr.io/bluesaltbarrier/mpas8-gccn:slim sleep infinity
```

2.2 GB download. Contains MPAS-Atmosphere v8.3.1 compiled with all our bug-fixed GCCN modifications, Thompson microphysics patches, lookup tables, and namelist templates. Then follow [reproducibility/REPRODUCE.md](reproducibility/REPRODUCE.md) starting at Step 3 (mesh and GFS data download).

**Full reproducibility stack:** the `reproducibility/` folder has Dockerfiles, the GCCN physics patches, MPAS namelists, and analysis scripts. See [reproducibility/REPRODUCE.md](reproducibility/REPRODUCE.md) for the full from-source build path.

**What is included in this repo:** Dockerfiles, physics modifications, namelists, analysis Python scripts, full paper and website, plus the pre-built Docker image on GitHub Container Registry.

**What is NOT included:** the ~200 GB of simulation output NetCDF files (available on request pending public data archival), and the WPS preprocessing toolchain (GFS→MPAS intermediate conversion — download from https://github.com/wrf-model/WPS).

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
