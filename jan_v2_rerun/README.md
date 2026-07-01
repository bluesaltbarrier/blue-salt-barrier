# January v2 ensemble rerun — fixes the v4 baseline bug

## Why

v4's published 5-pair January ensemble was contaminated:
- **2025** ran the correct 2025-style setup (Pöhlker pristine over IGBP-2,
  GoCart climatology elsewhere) — IGBP-2 cloud-base 108 /cm³, non-IGBP-2 ~1700.
- **2022, 2023, 2024, 2026** ran with a globally-uniform pristine baseline
  (~130 /cm³ everywhere on Earth, not just IGBP-2 — an unrealistic atmosphere).
  This is the v4 baseline bug.

This rerun rebuilds all 5 January pairs using the same correct 2025-style
init pipeline (the one the v5 July bundle uses). The result will be a clean,
internally consistent 5-pair v2 January ensemble that can be:
- compared directly to v5 July (same setup, different season),
- and used to either confirm or retract the published v4 lead finding
  (-80 ± 22 TW at 30°N).

## What's in this folder

| File | Purpose |
|---|---|
| `step1_build_inits.sh` | Build 5 corrected init files using `make_pristine_init.py` (IGBP-2-only). Verifies each: IGBP-2 ~150, non-IGBP-2 ~thousands. Fails loudly if anything drifts. |
| `step2_run_ensemble.sh` | Run 5 SALT/NOSALT pairs. Resume-safe (skips pairs whose output dir has ≥25 history files). |
| `launch.sh` | Chain step 1 → step 2. Detached, logs to pipeline_jan_v2.log. |
| `verify_one_init.sh` | One-shot check on a single init file (after step 1, before step 2). |

## Output locations

- Init files: `/opt/jan_v2/x1.40962.init.YYYY.jan.pristine_v2.nc` (inside container)
- Simulation outputs (on host disk):
  `D:\WRF\GITIGNORE\simulation_outputs\results_120km_jan_v2_YYYY_prescribed_ccn_{salt,nosalt}\`
- Pipeline log (inside container): `/mpas/run_120km/pipeline_jan_v2.log`

## Compute estimate

- Step 1: ~5 minutes per init × 5 = ~25 minutes total
- Step 2: ~22 hours per pair × 5 pairs ≈ **110 hours (~4.5 days)** at 12 cores

Existing v4 buggy outputs in `results_120km_jan_pohlker_l4_YYYY_prescribed_ccn_*`
are preserved (different directory names).

## How to use

```powershell
# from D:\WRF on the host (not inside container)
docker exec mpas8 bash /host/jan_v2_rerun/step1_build_inits.sh
docker exec mpas8 bash /host/jan_v2_rerun/verify_one_init.sh    # optional sanity check
docker exec -d mpas8 bash /host/jan_v2_rerun/step2_run_ensemble.sh

# check progress
docker exec mpas8 tail -30 /mpas/run_120km/pipeline_jan_v2.log
```

Step 2 is resume-safe — if anything dies, just re-launch.
