# Corrigendum to "Exploratory MPAS Sensitivity Experiments on Rainforest Biogenic Salt Aerosols, Tropical Rainfall, and Poleward Moisture Transport" (v4)

**Authors:** Brian Lue
**Affiliation:** Independent Researcher
**Contact:** bluesaltbarrier@gmail.com · ORCID 0009-0004-7980-2168
**Code repository:** github.com/bluesaltbarrier/blue-salt-barrier

**Article being corrected:** Lue, B. (2026). *Exploratory MPAS Sensitivity Experiments on Rainforest Biogenic Salt Aerosols, Tropical Rainfall, and Poleward Moisture Transport* (v4). EarthArxiv, DOI [10.31223/X5H19T](https://doi.org/10.31223/X5H19T), published 2026-05-07 as Version 2 of the record. Software archive: Zenodo [10.5281/zenodo.20071932](https://doi.org/10.5281/zenodo.20071932).

**Corrigendum date:** 2026-05-23 (updated 2026-05-28 with completed corrected-ensemble results; updated 2026-06-03 with the completed 5-member 2023 perturbation pilot and the giant-CCN disclosure; finalized and posted alongside the v5 revision on 2026-06-30. The defect was identified 2026-05-22 to 2026-05-23; the corrected ensembles, the July seasonal ensemble, and the perturbation pilot were completed over the following weeks, and this corrected record is posted on 2026-06-30.)

---

## 1. Summary

Post-publication audit of the v4 5-pair January 120 km prescribed-CCN ensemble (§6.9 "v4 (this revision): prescribed-CCN ensemble result", Figures 21–24) has identified a baseline-initialization defect affecting four of the five paired runs. The defect causes the ensemble to combine one pair (January 2025) run under the manuscript's stated experimental design with four pairs (January 2022, 2023, 2024, 2026) run under a different and unintended baseline configuration. The published headline result — a reduction in northward latent heat transport at 30°N of −80 ± 22 TW, p = 0.0013, derived from this 5-pair ensemble — pools two different experimental setups and is therefore not defensible as a single-experiment statistical inference.

**The v4 lead finding (Phase 9 5-pair ensemble at 30°N) is retracted.**

**Update (2026-05-28 / 2026-05-29): the corrected 5-pair ensemble is now complete and the retraction is definitive, not provisional.** Re-running all five January pairs (2022–2026) with the corrected initialization — Pöhlker-pristine over IGBP-2, GoCart climatology elsewhere, held by the prescribed-CCN reset — gives a 30°N latent-heat-transport response of **−12 ± 101 TW (t = −0.26, p = 0.80, 4/5 pairs negative)**, fully consistent with zero. The published −80 ± 22 TW (p = 0.0013) was an artifact of the buggy globally-uniform baseline, which suppressed inter-pair variance (σ rose from 22 TW in the defective ensemble to 101 TW in the corrected one). **No statistically resolved transport finding survives at N = 5 in the corrected ensemble.**

**This is a transport-diagnostic retraction, not a null result for the mechanism.** As a consistency check, the corrected ensemble reproduces the K-salt mechanism's expected microphysical first step at the Amazon source — cloud-droplet number increases by +79 to +105 % and cloud liquid water path increases in *every one* of the five corrected pairs (sign test p < 0.05 against the no-effect null; §6.1). This is the Twomey/Köhler activation response that any aerosol-aware microphysics scheme must produce given a 2× CCN perturbation, so it is a precondition-check confirming the corrected pipeline applies the forcing as designed — not, by itself, a novel finding. The downstream precipitation response is regime-dependent (three pairs invigoration, two pairs suppression — the well-known aerosol-cloud duality), and only at the third level, latent-heat transport at 30°N, does the signal become buried by chaotic eddy/storm-track variability that single 30-day realizations cannot separate from the forced response (§6.2). The retraction concerns the transport quantification, not the existence of the K-salt cloud-microphysical effect. Resolving the transport response under realistic background conditions requires an **initial-condition perturbation ensemble** — multiple perturbed members per year through both SALT and NOSALT; a 5-member 2023 pilot is now complete (forced mean −28 ± 29 TW; the +159 TW single run reproduced by no member) and is being extended to N = 15 then N = 30 (§6.3).

The mechanism, the methodology framework (Heikenfeld et al. 2019 prescribed-CCN), the v3-era Phase 7 single-pair results (§6.9 v3 subsection), and the 2025 single-pair (correctly configured) are not affected by this correction. A July seasonal-robustness ensemble using the same corrected configuration was run in parallel and is reported alongside in the Version 3 revision.

## 2. The defect, in detail

The intended experimental design (per §4.2 and §6.9) is:

- Cloud condensation nuclei concentration over IGBP-2 evergreen broadleaf forest cells set to Pöhlker et al. (2012) pristine target (surface nwfa ≈ 150 /cm³ NOSALT, ≈ 300 /cm³ SALT after the 2× K-salt perturbation).
- Non-IGBP-2 cells retain their MPAS-default (GoCart-derived) aerosol climatology.
- The Heikenfeld 2019 prescribed-CCN methodology then holds this combined field constant at every microphysics timestep throughout the 30-day integration.

This design was implemented correctly for the **January 2025 pair only**. Direct measurement of the model output confirms January 2025 ran with IGBP-2 cloud-base nwfa ≈ 108–117 /cm³ NOSALT and ≈ 216–235 /cm³ SALT over Amazon deep-interior IGBP-2 cells, against a non-IGBP-2 background of GoCart climatology values (~1000–2400 /cm³ depending on region).

The **January 2022, 2023, 2024, and 2026 pairs** were initialized from netCDF files that were missing the `nwfa` and `nifa` variables entirely (verified post hoc: file shapes 135 variables vs. the 137-variable working 2025 init). The init-atmosphere streams configuration used in the year-specific init build (`make_120km_init_4_years.sh`, inherited from the 240 km five-year build pipeline) did not write the aerosol fields to disk. The post-init `make_pristine_init.py` modification step either failed silently or was not invoked for these years. When MPAS-Atmosphere subsequently ran with these init files, the Thompson aerosol-aware microphysics scheme filled the missing nwfa field with a hard-coded globally-uniform pristine default (~130 /cm³ at all latitudes, including ocean cells, the Arctic, and the Sahara). The prescribed-CCN reset then held this unphysical globally-uniform baseline throughout the 30-day integration.

Direct measurement of cloud-base nwfa in the published model output confirms this defect:

| Year | IGBP-2 cloud-base (/cm³) | Non-IGBP-2 cloud-base (/cm³) | Global cloud-base (/cm³) |
|---|---|---|---|
| 2022 | ~130 | ~131 | ~131 |
| 2023 | ~130 | ~131 | ~131 |
| 2024 | ~130 | ~131 | ~131 |
| 2025 | ~108 | ~1707 | ~1656 |
| 2026 | ~130 | ~131 | ~131 |

The four affected pairs ran against a globally-uniform ~130 /cm³ atmosphere — not the realistic GoCart background the manuscript states. The 2025 pair ran against the intended realistic background.

## 3. Effect on the published statistics

Per-year ΔLHF at 30°N (SALT − NOSALT, TW), separated by experimental setup:

| Setup | Year | ΔLHF₃₀ₙ (TW) |
|---|---|---|
| Globally-uniform pristine baseline (defect) | 2022 | −85.0 |
| Globally-uniform pristine baseline (defect) | 2023 | −107.3 |
| Globally-uniform pristine baseline (defect) | 2024 | −63.4 |
| Globally-uniform pristine baseline (defect) | 2026 | −93.8 |
| **Intended design (correct)** | **2025** | **−51.9** |

The intended-design pair (2025) gives the smallest magnitude. The four defect pairs give larger magnitudes (mean ≈ −87 TW). The published 5-pair t-test (t = −7.98, p = 0.0013) assumes the 5 pairs are independent realizations of the same experiment, an assumption that does not hold. The published p-value cannot be defended.

The 2025 single pair, in isolation, sits at N = 1 and is within the single-pair noise floor of the v3-era Phase 2–7 single-pair runs (30°N ΔLHF range −211 to +153 TW, σ ≈ 126 TW). No statistically resolved 30°N finding is supported on the basis of v4 as published.

### 3.1 The corrected N = 5 ensemble (2026-05-28)

Re-running all five January pairs under the corrected initialization yields the following per-year 30°N ΔLHF (SALT − NOSALT, TW):

| Year | ENSO state (DJF ONI, NOAA CPC) | v4 (defective) | v2 (corrected) |
|---|---|---|---|
| 2022 | Weak La Niña (−0.9) | −85.0 | −52.8 |
| 2023 | Weak La Niña (−0.8) | −107.3 | +158.7 |
| 2024 | Strong El Niño (+1.9) | −63.4 | −104.7 |
| 2025 | Neutral (−0.4) | −51.9 | −51.9 |
| 2026 | Neutral (−0.4) | −93.8 | −9.2 |
| **Mean ± SD** | | **−80.3 ± 22.5** | **−12.0 ± 101.3** |
| **t / p** | | **−7.98 / 0.0013** | **−0.26 / 0.80** |

The 2025 pair is bit-identical between the two analyses (it was the one correctly-configured pair in v4), which serves as an internal-consistency check confirming the comparison is sound; the differences in the other four years are genuine baseline effects.

The corrected ensemble samples three distinct ENSO regimes (two weak-La-Niña, one strong-El-Niño, two cold-neutral Januaries). ENSO does not mediate the response at this ensemble size — the two near-identical weak-La-Niña Januaries (ONI −0.9 and −0.8) produced opposite-sign responses (−52.8 and +158.7 TW), establishing that sub-monthly internal atmospheric variability dominates the per-pair response. The ensemble mean is therefore an ENSO-marginal climatology with a single-realization noise floor of order ±100 TW at 30°N.

**Secondary observation (not a claim):** in the corrected ensemble the only metric approaching significance is 30°S ΔLHF (+76.8 ± 80.0 TW, t = +2.15, p = 0.098), in the equatorial-heat-retention direction (reduced southward export). At p < 0.10 with N = 5 this is suggestive, not resolved, and is reported only to motivate the larger ensembles and the July seasonal test, not as a finding. Amazon-mean ΔP remains unresolved in both analyses (v2: +2.6 ± 11.3 mm/30-day, p = 0.64, the mean ± SD of the five per-year values in §6.1).

**No external-forcing confound applies.** Across the five January simulation windows only one event of potential global radiative significance occurred — the Hunga Tonga–Hunga Haʻapai eruption (15 January 2022, VEI 5–6, ~150 Tg stratospheric H₂O). Because the 2022 initial condition is from GFS analysis three days before the eruption, MPAS does not model volcanic forcing, and SSTs are held fixed, the 2022 simulation is a counterfactual no-eruption atmosphere; the eruption does not affect the SALT − NOSALT contrast. No other VEI ≥ 5 eruption occurred in the 2023–2026 windows (Smithsonian GVP / authoritative eruption record).

## 4. What is retracted

The following v4 claims and statistical inferences are withdrawn:

- The 30°N northward latent heat transport reduction of **−80 ± 22 TW (5/5 pairs negative, p = 0.0013)** as a statistically resolved finding (§6.9 v4 subsection, Abstract, Figures 21, 22, 24).
- The framing of this number as "the only metric across the entire paper series that survives a one-sample t-test against zero" (§7.1).
- The "two-sided equatorial-heat-retention signature" framing built on the joint 30°N + 30°S behaviour, as the constituent ensemble means are computed across the heterogeneous setup (Figure 22 caption, Abstract).
- The 70°N positive trend of +15 ± 20 TW (p = 0.16), to the same extent (the metric is computed from the same heterogeneous ensemble).
- All ensemble-derived per-latitude statistics in §6.9 v4 subsection and §7.1 that depend on the 5-pair pool.

## 5. What is preserved

The following are not affected by the defect:

- The Pöhlker et al. (2012) source-aerosol observations and the manuscript's physical-mechanism framework (§3).
- The Heikenfeld et al. (2019) prescribed-CCN methodology as the appropriate experimental framework for the K-salt question.
- The v3-era Phase 2–7 single-pair results (§6.2–§6.9 v3 subsection), which were already presented in the v4 manuscript as single-pair-N-1 and not as resolved ensemble findings.
- The single January 2025 prescribed-CCN pair (correctly configured, ΔLHF₃₀ₙ = −51.9 TW, N = 1, within single-pair noise — physically consistent with the hypothesis but not statistically resolved).
- The methodology critique of the Thompson surface-emission term ("very far from ideal", §6.9), the WRF→MPAS rationale (§4.1), and the v3 retractions already documented in v4 (polluted-baseline narrative, polar-temperature claims).
- The software archive at Zenodo 10.5281/zenodo.20071932 — the code and patches it contains are unchanged. What changed is the validity of the ensemble that was run with them.

The raw model output from the four affected pairs (2022, 2023, 2024, 2026) is preserved on external media for future reference. Comparing the artifact-baseline runs to the corrected v2 runs lets us isolate how much of the published v4 30°N response was driven by the unintended globally-uniform pristine baseline versus the IGBP-2 K-salt perturbation itself; that diagnostic comparison will be reported in the Version 3 revision.

### 5.1 This is a defect, not an alternative valid regime

A reasonable alternative reading — that the four affected pairs simply represent a different but valid experimental regime (rainforest CCN exceeding background, versus the corrected regime where rainforest CCN is below background) — was considered and is rejected. The four affected pairs' non-IGBP-2 background was **globally uniform** (≈130 /cm³ at cloud-base at every latitude — Arctic, Sahara, open Pacific, and Amazon basin all identical). That is not a physical aerosol distribution, and it is not what the GoCart-derived Thompson climatology produces: the correctly-built 2025 pair and all five corrected pairs show a spatially-varying non-IGBP-2 field (≈1000–2400 /cm³, higher over industrialized continents, lower over the clean Arctic). The spatial uniformity is the diagnostic signature of the missing-`nwfa` fallback documented in §7.1, and is corroborated by the missing netCDF variable itself. A globally-uniform pristine atmosphere is an initialization artifact, not a regime; the corrected ensemble is therefore the only one of the two that tests the intended physical configuration.

## 6. Corrected ensemble (complete, 2026-05-28)

The corrected 5-pair January 120 km prescribed-CCN ensemble (v2) is complete. The init pipeline was fixed to inject the climatological nwfa field from a verified-correct source into each year's init file before applying the IGBP-2 pristine modification. Direct measurement confirmed all five v2 January init files satisfy the intended design (IGBP-2 surface ≈ 150 /cm³; non-IGBP-2 surface ≈ 1683 /cm³; global ≈ 1635 /cm³), and the prescribed-CCN reset held these values bit-identically (0.00% drift) across the full 30-day integration in every pair. Results are reported in §3.1: the corrected 30°N response is −12 ± 101 TW (p = 0.80), not statistically resolved.

A July seasonal-robustness ensemble using the identical corrected pipeline (the v5 July ensemble previewed in §9 Future Work item 1) was run in parallel on a separate machine, verified to the same standard (IGBP-2 surface 150 /cm³, non-IGBP-2 ≈ GoCart climatology), and is complete: it gives a 30°N response of −30 ± 92 TW (t = −0.72, p = 0.51), the same null at the same noise floor as the corrected January ensemble.

The next EarthArxiv version of this record (Version 3) will report both the corrected January ensemble and the July ensemble, replacing the §6.9 v4 subsection in full. The DOI 10.31223/X5H19T will resolve to that revised version when posted; v4 will be preserved as Version 2 in the EarthArxiv version history, with this corrigendum attached as a comment to that version.

### 6.1 What the corrected ensemble does establish (mechanism-level)

While the 30°N transport response is not statistically resolved at N = 5, the corrected ensemble does reproduce the mechanism's expected microphysical first step — a consistency check that the corrected pipeline applies the K-salt forcing as designed, not a novel finding. At the Amazon source (IGBP-2 cells), the K-salt 2× perturbation produces a sign-consistent microphysical response in **all five** corrected January pairs:

| Year | Δ cloud-droplet number (%) | Δ liquid water path (%) | Amazon-mean ΔP (mm/30-day) |
|---|---|---|---|
| 2022 | +89 | +25 | +16.2 |
| 2023 | +105 | +8 | −12.6 |
| 2024 | +87 | +15 | −4.6 |
| 2025 | +79 | +18 | +5.8 |
| 2026 | +94 | +30 | +8.0 |

The first link in the mechanism chain — K-salt → more, smaller cloud droplets → retained cloud water — is reproduced consistently: droplet number increases by +79 % to +105 % every year (mean ≈ +91 %), and cloud liquid water path increases in every pair. This confirms the corrected pipeline reproduces the expected Twomey activation response — a consistency check on the hypothesis's premise, not a novel result, since this is the response any aerosol-aware microphysics scheme is constructed to produce given a 2× CCN perturbation.

The precipitation consequence, however, is regime-dependent: Amazon-mean ΔP is positive (precipitation invigoration) in 2022, 2025, and 2026, and negative (precipitation suppression) in 2023 and 2024. This is the well-known aerosol-cloud precipitation duality (Stevens & Feingold 2009): the same constant droplet kick can either delay coalescence (suppression) or loft droplets to the freezing level and invigorate convection, depending on each year's convective regime. The corrected ensemble therefore establishes the *microphysical* response as a clean, reproducible forcing while showing the *precipitation* response to be a bifurcating regime-dependent outcome.

### 6.2 Interpretation: clean forcing at the microphysics level, regime-dependent downstream

The reconciliation of (a) the apparent consistency of the defective v4 ensemble (5/5 negative at 30°N) and (b) the scatter of the corrected ensemble (4/5 negative but mean indistinguishable from zero) follows from the structure of the response chain:

| Level | Behaviour of the K-salt response | Evidence (corrected ensemble) |
|---|---|---|
| Cloud microphysics (droplet number, LWP) | Clean, sign-consistent forcing | §6.1: 5/5 pairs +79 to +105 % Δnc |
| Convective precipitation | Regime-dependent bifurcation (suppression vs invigoration) | §6.1: 3 pairs invigoration, 2 suppression |
| Large-scale circulation transport (ΔLHF at 30°N) | Dominated by chaotic eddy/storm-track variability | §3.1: σ ≈ 101 TW; decomposition shows the eddy component swings sign year-to-year |

The direct microphysical effect is a clean forcing, but its consequences propagate through two bifurcating, regime-dependent stages — first the convective response, then the chaotic large-scale circulation — before they manifest as a transport diagnostic. By the time ΔLHF is measured at 30°N, the clean forcing has been routed through two regime-switches; this is why the downstream signal is sign-variable across years, why the per-year scatter (~101 TW) exceeds the putative forced signal (~80 TW), and why a single 30-day realization per year cannot separate the forced response from internal variability. The defective v4 ensemble's apparent 5/5 consistency reflected the artificial suppression of inter-pair variance under a globally-uniform background, not a stronger forced signal.

### 6.3 The decisive experiment, now underway: initial-condition perturbation ensemble (5-member pilot complete)

Quantifying the forced K-salt response under realistic background conditions requires an initial-condition (IC) perturbation ensemble. For a single year, many copies of the day-0 state are constructed with small (≈0.01 K) potential-temperature perturbations and each is run through both the SALT and NOSALT prescribed-CCN binaries; the ensemble mean isolates the forced response, while the spread quantifies internal variability. The 2023 pair is the natural first target because its single-realization response (+158.7 TW) is the largest in magnitude, giving the cleanest test of whether that value is a forced regime response or a chaotic draw.

**A 5-member pilot on the 2023 pair is complete** (each member = identical setup with an independent ≈0.01 K IC perturbation; SALT and NOSALT; 30-day; 120 km; diagnostics-only), run sequentially on a single consumer machine:

| Member (≈0.01 K IC perturbation) | ΔLHF @ 30°N (TW) |
|---|---|
| mem01 | −32.3 |
| mem02 | −115.4 |
| mem03 | +65.6 |
| mem04 | −17.4 |
| mem05 | −40.4 |
| **Forced mean (N = 5)** | **−28.0 ± 28.9 (SE); σ_internal = 64.6; 4/5 negative; t = −0.97 (n.s.)** |

Two results follow. First, **no member reproduces the +158.7 TW single-run value** — it lies far outside the entire ensemble, confirming it was a chaotic tail draw, not a forced regime response. The 2023 "outlier" is therefore not a contradiction of the other years but a noisy realization of the same weakly-negative forced response; the apparent refutation dissolves into a confirmation of the internal-variability framing. Second, the forced mean is weakly negative and in the publication direction (4/5 members negative, −28 TW), but **not statistically resolved at N = 5** (t = −0.97, p > 0.05) because the internal-variability spread (σ ≈ 65 TW) exceeds the forced mean. The published −80 TW and the corrected single-realization-ensemble −12 TW both lie inside the ±1σ band. (Figure: `mpas_analysis/v5_figures/v5_january_ens2023_distribution.png`.)

**Power analysis (pilot estimates: forced mean −28 TW, σ ≈ 65 TW):**

| N total | SE (TW) | t = mean/SE | resolved at p < 0.05? |
|---|---|---|---|
| 5 (done) | 28.9 | −0.97 | no |
| 15 (checkpoint) | 16.7 | −1.68 | no |
| 20 | 14.4 | −1.94 | no |
| 30 | 11.8 | −2.37 | marginal yes |

The pilot mean is itself uncertain at N = 5: if the true forced response is nearer the published −80 TW, ~10–12 members would resolve it. **We are therefore extending the 2023 ensemble from N = 5 to N = 15, evaluating the running mean and SE at that checkpoint, then continuing to N = 30** (members mem06–mem30, each an independent SALT/NOSALT pair). Decision rule: if the mean firms toward −80 TW it resolves early; if it stays near −28 TW, N ≈ 30 is the minimum to cross p < 0.05. Diagnostics-only output keeps storage at ≈1.3 GB/run; the harness is resume-safe (skips any member-arm with ≥25 diagnostic files). The analysis will report the full per-member distribution of ΔP and ΔLHF (bimodality test, regime-occupation fraction, SALT-vs-NOSALT variance change), not only the mean, because the corrected ensemble indicates K-salt may operate as a regime-changer rather than a pure forcing at the precipitation stage (§6.2).

This perturbation ensemble — not a further extension of single-realization-per-year ensembles — is the experiment that can resolve whether the K-salt transport response is small-but-real, regime-conditional, or chaotically dominated. The pilot is complete; the N = 15 and N = 30 extensions will be reported in the Version 3 revision.

### 6.4 Future work treated as hypotheses, not findings

Several candidate explanations for inter-year variance — climate-mode modulation (AMO, ENSO, IOD, NAO), Hunga Tonga residual stratospheric water, jet-position state-dependent sensitivity — are physically plausible and produce suggestive correlations in the corrected ensemble (e.g., a jet-wander-vs-response correlation of r = +0.66 at N = 5, and a 30°S transport response approaching significance at p ≈ 0.10). These remain hypotheses, not findings, at this ensemble size. They are appropriate motivation for (a) the perturbation ensemble of §6.3 and (b) extending the single-realization ensemble back to 2015 using the same NCAR RDA d084.1 GFS analyses to test the climate-mode hypotheses at N = 11 with multi-mode coverage including two strong El Niño events. They are not reported here as conclusions of the corrected ensemble.

### 6.5 Methodological disclosure: giant-CCN channel suppressed by the prescribed-CCN patch

Independent of the initialization defect, one property of the prescribed-CCN implementation should be disclosed because it was not stated in v4. Holding `nwfa` fixed at the target each microphysics step also sets the Thompson giant-CCN field (`ngccn`) to zero **everywhere, including over ocean**, in both the SALT and NOSALT arms. The warm-rain-initiating microphysics of sea-spray giant-mode CCN is therefore not represented. Because both arms have `ngccn = 0`, this **cancels exactly in the SALT − NOSALT contrast** that carries every reported result, so it does not affect the retraction or any difference reported here; it does bias the *absolute* marine precipitation field in both arms and should be acknowledged. The CAM radiation module's sea-salt (`SSLT`) optical pathway is unaffected (verified present in the binary), so the direct radiative effect of sea salt is retained — only the microphysical giant-CCN channel is off. A prognostic-`ngccn` implementation would be required to study the absolute marine warm-rain response, but is not needed for the K-salt contrast.

## 7. Root cause and how the defect went undetected

### 7.1 Root cause

The defect originated in the init-file build for the four ensemble-extension years. The single 2025 pair was built and verified individually with care, and was correct. When the ensemble was extended to 2022, 2023, 2024, and 2026, the build script (`make_120km_init_4_years.sh`) **reused a `streams.init_atmosphere` configuration adapted from the 240 km build pipeline** (via `sed` substitution of the mesh name). That streams configuration did not emit the `nwfa`/`nifa` aerosol fields, so the four generated init files were missing those variables entirely (135 netCDF variables versus the 137 in the correct 2025 init). The subsequent `make_pristine_init.py` modification had no `nwfa` field to scale and did not produce the intended pristine IGBP-2 condition. At run time, the Thompson aerosol-aware scheme filled the absent field with a hard-coded globally-uniform default (~130 /cm³ at cloud-base), which the prescribed-CCN reset then held fixed for the full integration.

The chain of contributing causes:
1. A configuration was carried across mesh resolutions (240 km → 120 km) without verifying it still emitted the aerosol output the downstream step required.
2. The init files were never opened and checked for the presence and values of `nwfa` before being used in production runs.
3. A missing-variable condition was absorbed silently by a model-level default rather than failing loudly.

### 7.2 How it went undetected

The boundary-layer-preservation diagnostic referenced in §6.9 v4 subsection (`bl_preservation_120km_prescribed_ccn.py`) sampled only Amazon IGBP-2 deep-interior cells, and was run for only one year (2025). For all five pairs those specific cells either were correctly modified (2025) or coincidentally sat near the value that the globally-uniform fallback produced (the four defect pairs). The diagnostic therefore returned PASS, and that single PASS was extrapolated to the whole ensemble. No diagnostic sampled non-IGBP-2 cells, the global field, or the other four years — which is exactly where the defect lived. A check that inspects only the region expected to be correct, on a single realization, confirms an expectation rather than verifying the experiment.

### 7.3 Prevention (now enforced)

The corrected verification procedure checks **four zones — Amazon IGBP-2 cells, non-IGBP-2 cells, the global mean, and selected latitude bands — for every initial-condition file and every ensemble member**, and explicitly confirms that non-IGBP-2 cells carry the GoCart climatology (≈1000–2000 /cm³) rather than the pristine value. A globally-uniform pristine field is treated as a failure signature, not a success signature. The corrected Jan v2 and July v5 pipelines run this verification automatically and abort the run if any year fails. The init-build step additionally injects and confirms the `nwfa`/`nifa` fields before the pristine modification, so a missing-variable condition can no longer be absorbed silently.

This is recorded so that the next person — human or AI — inherits the safeguard rather than the blind spot: **verify the actual output field everywhere it should vary, on every ensemble member, and treat "looks right in the region I expected" as insufficient.**

## 8. Citation update

Until the EarthArxiv Version 3 is posted, the appropriate citation for v4 should include reference to this corrigendum:

> Lue, B. (2026). *Exploratory MPAS Sensitivity Experiments on Rainforest Biogenic Salt Aerosols, Tropical Rainfall, and Poleward Moisture Transport* (v4, with corrigendum 2026-05-23). EarthArxiv, DOI [10.31223/X5H19T](https://doi.org/10.31223/X5H19T).

The Zenodo concept DOI ([10.5281/zenodo.19739391](https://doi.org/10.5281/zenodo.19739391), always-latest) will resolve to the corrected software archive once Version 3 is posted.

## 9. Acknowledgment

The defect was identified during a code/data audit on 2026-05-22 to 2026-05-23, prompted by re-examination of the init-build pipeline while preparing the v5 July seasonal-robustness ensemble. The audit was conducted by the author with the assistance of an AI coding tool (Claude Code, Anthropic), the same tool used in the original v4 work. The same toolchain that introduced the defect identified it on review — a reminder that AI-assisted research benefits from explicit, repeatable, end-to-end verification rather than reliance on intermediate sanity checks.

---

*This corrigendum will be attached as a comment to the v4 record on EarthArxiv and committed to the public repository at github.com/bluesaltbarrier/blue-salt-barrier as `corrigendum_v4_2026-05-23.md`. The corrected January ensemble (§3.1) and the v5 July seasonal-robustness ensemble (§6) are both complete, and a 5-member 2023 initial-condition perturbation pilot (§6.3) is complete with its N = 15 / N = 30 extension underway; the corrected analysis appears as EarthArxiv Version 3.*
