# v5 July Ensemble — Run Instructions (Docker image delivery)

This package runs the **v5 July seasonal-robustness ensemble** for the Blue Salt
Barrier project: a 5-pair July 120 km prescribed-CCN ensemble mirroring the v4
January ensemble, to test whether the v4 30°N latent-heat-transport reduction
reverses under flipped (NH-summer / SH-winter) Hadley geometry.

## What you received

| File | Size | What it is |
|---|---|---|
| `mpas8-v5-july.tar` | ~10 GB | A complete Docker image — MPAS, init_atmosphere, the v4 patched binaries, the 120 km mesh, physics tables, WPS ungrib, and all the v5 step scripts, baked in. |
| `README_v5_JULY.md` | — | This file |

Everything needed to run v5 is **inside the image**. The only external step is
downloading GFS analysis data (needs a free NCAR RDA account).

## Travel-machine requirements

- **Docker Desktop**, running (WSL2 backend on Windows)
- **~400 GB free local disk** for the run (GFS ~3 GB + intermediates ~3 GB +
  init files ~2 GB + ~250 GB simulation output + headroom)
- **≥ 32 GB RAM**
- A free **NCAR RDA account** — register at https://rda.ucar.edu (for Step 1)

## The years: July 2021–2025

The ensemble uses **July 2021, 2022, 2023, 2024, 2025** — five complete
historical Julys. (July 2026 had not happened when this image was built, so its
GFS analysis does not exist. The one-year offset from the v4 January window
2022–2026 is scientifically immaterial.)

---

## Setup — load the image and start the container

```bash
# 1. Load the image (one time, ~5-10 min)
docker load -i mpas8-v5-july.tar

# 2. Start a container. Mount a big local disk as /host for the run output.
#    Replace D:\v5run with any folder on your large local drive.
docker run -d --name mpas8 -v D:\v5run:/host mpas8-v5-july:latest sleep infinity
```

That is the whole setup. The container now has everything; `/host` is where the
run data and output land on your local disk.

## Run — five steps, all inside the container

```bash
# Step 0 — sanity check (everything should PASS)
docker exec mpas8 bash /opt/july_v5/step0_check_prereqs.sh

# Step 1 — download GFS analysis for the 5 July dates.
#          Use -it so the RDA password prompt works.
docker exec -it mpas8 bash /opt/july_v5/step1_download_gfs.sh

# Step 2 — convert GRIB2 to MPAS intermediate format (ungrib)
docker exec mpas8 bash /opt/july_v5/step2_make_intermediates.sh

# Step 3 — build the 5 July pristine init files
docker exec mpas8 bash /opt/july_v5/step3_make_july_init.sh

# Step 4 — run the 5-pair ensemble (~90 hours; resume-safe, see below)
docker exec mpas8 bash /opt/july_v5/step4_run_july_ensemble.sh

# Step 5 — generate v5 figures + statistics
docker exec mpas8 python3 /opt/july_v5/step5_analyze_july.py
```

Each step prints clear PASS/FAIL messages and tells you the next command.

### Step 4 is long — running it in the background

The ensemble is ~90 hours of compute. Run it detached and check on it:

```bash
# launch detached
docker exec -d mpas8 bash /opt/july_v5/step4_run_july_ensemble.sh
# check progress any time
docker exec mpas8 tail -20 /mpas/run_120km/pipeline_july_v5.log
```

**Resume-safe:** if the machine reboots or a run dies, just re-launch Step 4 —
it skips any year-pair already finished and continues from where it stopped.

## Where the output lands

On your local disk under the folder you mounted as `/host`:

```
D:\v5run\v5_july\gfs\                  GFS GRIB2 files
D:\v5run\v5_july\intermediates\        WPS intermediate files
D:\v5run\v5_july\simulation_outputs\   the 10 simulation output directories
D:\v5run\v5_july\v5_figures\           the v5 figures + summary (Step 5)
```

The figures and `v5_july_ensemble_summary.txt` in `v5_figures\` are the
deliverables — copy those back when you return.

## Optional — the January-vs-July comparison panel

Step 5 also draws a January-vs-July seasonal comparison **if** the v4 January
ensemble output is present. To enable it, copy the v4 January result
directories into `D:\v5run\v5_july\jan_v4_outputs\` before running Step 5
(directory names `results_120km_jan_pohlker_l4_YYYY_prescribed_ccn_{salt,nosalt}`).
If they are absent, Step 5 simply skips that one panel.

---

## The scientific prediction (what success looks like)

v4 (January, NH-winter / SH-summer): 30°N latent-heat transport reduced by
−80 ± 22 TW, p = 0.0013 — statistically resolved.

**v5 (July, NH-summer / SH-winter) prediction:** the roles swap.
- **30°S** should become the *statistically resolved* signal — a reduction in
  southward transport (the dominant Hadley cell is now SH-side).
- **30°N** should become the *noisy* one (NH-summer weak secondary cell +
  monsoon variability).

If v5 shows a resolved 30°S reduction in July mirroring v4's resolved 30°N
reduction in January, that confirms equatorial heat retention as a two-season
result. Step 5's summary file reports the one-sample t-tests that decide this.

## After the runs

Keep the `simulation_outputs` directories — they are the raw material for the
v5 manuscript revision (EarthArxiv Version 3). The manuscript edit (adding a v5
subsection to §6.9, marking §9 Future Work item #1 complete) is a separate task
for when you are back at the main project repo.

---

## Troubleshooting

- **Step 0 reports a FAIL** — the image may not have loaded fully; re-run
  `docker load`. If only disk space is low, free space on the `/host` drive.
- **Step 1 download fails** — check RDA credentials; or download the five
  `gfs.0p25.YYYY071200.f000.grib2` files manually from RDA dataset d084.1 and
  place them in `D:\v5run\v5_july\gfs\`.
- **A simulation dies mid-run** — just re-launch Step 4; it resumes.
- **Out of disk** — each pair produces ~50 GB; the full ensemble ~250 GB. Make
  sure the `/host` drive has room before launching Step 4.
