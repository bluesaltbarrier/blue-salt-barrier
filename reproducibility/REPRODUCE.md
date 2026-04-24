# Reproducing The Blue Salt Barrier Experiment

Step-by-step instructions for running the GCCN salt aerosol experiment on your own hardware. All tools are free and open source.

## Hardware Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU cores | 4 | 12+ |
| RAM | 16 GB | 64 GB |
| Disk (SSD) | 100 GB free | 500 GB free |
| OS | Windows 10/11, macOS, or Linux | Linux or WSL2 |
| GPU | Not required | Not required |

The simulations reported in this project ran on an Intel i7-12700H laptop with 64 GB RAM. Each 30-day 240 km simulation takes ~1.5 hours; each 30-day 120 km simulation takes ~8-10 hours.

## Software Prerequisites

1. **Docker Desktop** — https://docker.com/products/docker-desktop (free)
2. **Git** — https://git-scm.com (free)
3. **Python 3.10+** with NumPy, netCDF4, Matplotlib, Cartopy — for running analysis
4. **~50 GB free space for Docker** (can be configured via Docker settings)

For Windows users: enable WSL2 backend in Docker Desktop settings.

---

## Step 1. Clone this repo

```bash
git clone https://github.com/bluesaltbarrier/blue-salt-barrier.git
cd blue-salt-barrier
```

## Step 2. Get the MPAS container

**Fast path (recommended): pull our pre-built container from GitHub Container Registry.** This includes MPAS-Atmosphere v8.3.1 with all our bug-fixed GCCN modifications compiled in. About 2.2 GB download.

```bash
docker pull ghcr.io/bluesaltbarrier/mpas8-gccn:slim
docker run -d --name mpas8 -v mpas_data:/mpas ghcr.io/bluesaltbarrier/mpas8-gccn:slim sleep infinity
```

The `slim` tag contains:
- MPAS-Atmosphere v8.3.1 compiled with our GCCN lifecycle patches (bug-fixed)
- Thompson microphysics modifications (Hall 1980, Beard 1976, κ-Köhler)
- All lookup tables (RRTMG radiation, Thompson aerosol tables, etc.)
- Namelist and streams templates
- Both the SALT-enabled and NO-SALT init files

It does **not** contain mesh files or GFS initial conditions &mdash; those are downloaded in Steps 3 and 4 to keep the image small.

**Alternative path: build from source (30–60 minutes compile time).** The `reproducibility/container/` folder has two Dockerfiles:

- `Dockerfile.mpas8_ubuntu` — Ubuntu 22.04 with MPAS v8.3.1 (the one used for this paper's results)
- `Dockerfile.mpas7_centos` — CentOS 7 with MPAS v7.0 (older, kept for reference)

```bash
cd reproducibility/container
docker build -t mpas8 -f Dockerfile.mpas8_ubuntu .
docker run -d --name mpas8 -v mpas_data:/mpas mpas8 tail -f /dev/null
# Then apply the GCCN patches:
docker cp ../mpas_modifications/patch_gccn_full.sh mpas8:/opt/
docker cp ../mpas_modifications/patch_gccn_bugfixes.sh mpas8:/opt/
docker exec mpas8 bash -c "bash /opt/patch_gccn_full.sh && bash /opt/patch_gccn_bugfixes.sh"
docker exec mpas8 bash -c "cd /opt/MPAS-Model && make -j12 gfortran CORE=atmosphere USE_PIO2=true PRECISION=single AUTOCLEAN=true"
```

The pre-built image is faster to get started; the from-source path lets you see exactly what was done.

## Step 3. Download mesh and static files

MPAS meshes are hosted at NCAR:

```bash
# 240 km uniform mesh (10,242 cells) — fast, used for most results
docker exec mpas8 bash -c "cd /opt && \
  wget https://www2.mmm.ucar.edu/projects/mpas/atmosphere_meshes/x1.10242.tar.gz && \
  tar xzf x1.10242.tar.gz && \
  wget https://www2.mmm.ucar.edu/projects/mpas/atmosphere_meshes/x1.10242_static.tar.gz && \
  tar xzf x1.10242_static.tar.gz"

# 120 km uniform mesh (40,962 cells) — higher resolution
docker exec mpas8 bash -c "cd /opt && \
  wget https://www2.mmm.ucar.edu/projects/mpas/atmosphere_meshes/x1.40962.tar.gz && \
  tar xzf x1.40962.tar.gz && \
  wget https://www2.mmm.ucar.edu/projects/mpas/atmosphere_meshes/x1.40962_static.tar.gz && \
  tar xzf x1.40962_static.tar.gz"
```

## Step 4. Download GFS initial conditions

Pick a date. For an April experiment:

```bash
mkdir -p gfs_data && cd gfs_data

# Four 6-hourly analyses for 2026-04-12 (matches our April run)
for HR in 00 06 12 18; do
  wget https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20260412/$HR/atmos/gfs.t${HR}z.pgrb2.0p50.f000
done
```

For January:

```bash
for HR in 00 06 12 18; do
  wget https://noaa-gfs-bdp-pds.s3.amazonaws.com/gfs.20250112/$HR/atmos/gfs.t${HR}z.pgrb2.0p50.f000
done
```

Convert GRIB2 to MPAS intermediate format using WPS's `ungrib.exe` (requires a WRF/WPS container — see alternatives in "Further Notes" below).

## Step 5. Apply the GCCN physics patch

The critical modification — adds full GCCN lifecycle to Thompson microphysics:
- Kappa-Köhler activation (Petters & Kreidenweis 2007)
- Time-resolved condensational growth (Rogers & Yau)
- Size-dependent collision efficiency (Hall 1980 lookup)
- Beard 1976 terminal velocity
- Wet scavenging
- Cloud droplet depletion and rain number production

```bash
docker cp reproducibility/mpas_modifications/patch_gccn_full.sh mpas8:/opt/
docker exec mpas8 bash /opt/patch_gccn_full.sh
```

The script patches `/opt/MPAS-Model/src/core_atmosphere/physics/physics_wrf/module_mp_thompson.F` and verifies the changes. Then rebuild MPAS:

```bash
docker exec mpas8 bash -c "cd /opt/MPAS-Model && \
  make -j12 gfortran CORE=atmosphere USE_PIO2=true PRECISION=single AUTOCLEAN=true"
```

Also apply the salt emission patch to `mpas_atmphys_init_microphysics.F` (enhanced emission over ivgtyp=2 rainforest cells). The salt version of this file is at `reproducibility/mpas_modifications/` with name `.salt.F`.

## Step 6. Run init_atmosphere to create initial conditions

```bash
docker cp reproducibility/mpas_modifications/namelist.init_atmosphere mpas8:/mpas/run/
docker cp reproducibility/mpas_modifications/streams.init_atmosphere mpas8:/mpas/run/
docker exec mpas8 bash -c "cd /mpas/run && mpirun --allow-run-as-root -np 1 ./init_atmosphere_model"
```

This produces `x1.10242.init.nc` (for 240 km) or `x1.40962.init.nc` (for 120 km).

## Step 7. Run the paired experiment

**CONTROL (salt enabled):**

```bash
# Ensure .salt init file is compiled in
docker exec mpas8 bash -c "cp /opt/MPAS-Model/src/core_atmosphere/physics/mpas_atmphys_init_microphysics.F.salt \
  /opt/MPAS-Model/src/core_atmosphere/physics/mpas_atmphys_init_microphysics.F && \
  cd /opt/MPAS-Model && make -j12 gfortran CORE=atmosphere USE_PIO2=true"

# Run
docker cp reproducibility/mpas_modifications/namelist.atmosphere mpas8:/mpas/run/
docker cp reproducibility/mpas_modifications/streams.atmosphere mpas8:/mpas/run/
docker exec mpas8 bash -c "cd /mpas/run && mpirun --allow-run-as-root -np 12 ./atmosphere_model"
```

Results go to `/mpas/run/history.*.nc` (61 files for a 30-day run). Copy to host:

```bash
docker cp mpas8:/mpas/run/ results_salt/
```

**NO-SALT:** Repeat Step 7 but use `.orig` init file:

```bash
docker exec mpas8 bash -c "cp /opt/MPAS-Model/src/core_atmosphere/physics/mpas_atmphys_init_microphysics.F.orig \
  /opt/MPAS-Model/src/core_atmosphere/physics/mpas_atmphys_init_microphysics.F && \
  cd /opt/MPAS-Model && make -j12 gfortran CORE=atmosphere USE_PIO2=true"
# ...then run and copy results to results_nosalt/
```

## Step 8. Analyze the results

```bash
pip install numpy netCDF4 matplotlib cartopy

# 240 km April analysis
python reproducibility/analysis/plot_fullgccn.py

# 120 km January analysis
python reproducibility/analysis/plot_120km_jan.py
```

Output plots go to `mpas_analysis/`. Compare against our published plots in the same folder.

---

## Step 9 (Phase 7). Baseline-CCN sensitivity matrix

Phase 7 is the Pöhlker-anchored sensitivity matrix that drives the paper's main result: the sign of the Amazon rainfall response to K-salt depends on the background CCN state. It requires four paired runs at 120 km, each using a different Thompson-activation configuration and/or background-nwfa setting. The three patch scripts that prepare the required binaries live in `reproducibility/mpas_modifications/`:

| Patch | Configuration built |
|---|---|
| `patch_pohlker_ccn.sh` | Rainforest K-salt modelled as ordinary CCN (2× nwfa over IGBP-2), GCCN pathway zeroed. Used for the polluted and pristine baseline pairs. |
| `patch_pohlker_l4.sh` | Thompson activation index `l=4` (160 nm dry diameter), `m=4` (κ=0.8). Matches Pöhlker 2012 Dg=150 nm. |
| `patch_pohlker_size.sh` | Thompson activation index `l=5` (320 nm dry diameter), `m=4` (κ=0.8). Upper-bound sensitivity test. |

Apply a patch, rebuild, run the paired simulation, and save output under `mpas_analysis/<pair_key>/` (e.g. `pohlker_pair`, `pristine_pair`, `l4_pair`, `size_pair`).

### Path conventions

All the analysis scripts below are path-portable via argparse. They expect a Docker-mounted `/host` prefix only in the examples — you can point them at any directory.

### Per-pair analysis (repeat for each of the four pairs)

```bash
# Takes three positional args: salt_dir nosalt_dir out_dir
docker exec mpas8 bash -c "python3 /host/reproducibility/analysis/analyze_pohlker_pair.py \
  /host/simulation_outputs/results_120km_jan_pohlker_l4_salt \
  /host/simulation_outputs/results_120km_jan_pohlker_l4_nosalt \
  /host/mpas_analysis/l4_pair"

# Analogous for heat-flux and winds
docker exec mpas8 bash -c "python3 /host/reproducibility/analysis/analyze_pohlker_heat_flux.py \
  /host/simulation_outputs/results_120km_jan_pohlker_l4_salt \
  /host/simulation_outputs/results_120km_jan_pohlker_l4_nosalt \
  /host/mpas_analysis/l4_pair"

docker exec mpas8 bash -c "python3 /host/reproducibility/analysis/analyze_pohlker_winds.py \
  /host/simulation_outputs/results_120km_jan_pohlker_l4_salt \
  /host/simulation_outputs/results_120km_jan_pohlker_l4_nosalt \
  /host/mpas_analysis/l4_pair"
```

Each pair directory ends up containing `deltaP_data.npz`, `heat_flux_data.npz`, `wind_data.npz`, a `plots/` folder with per-field PNGs, and text summaries.

### Phase 7 summary figure (all four pairs)

```bash
docker exec mpas8 bash -c "python3 /host/reproducibility/analysis/plot_8run_summary.py \
  --base /host/mpas_analysis \
  --salt-ref /host/simulation_outputs/results_120km_jan_pohlker_salt/history.2025-02-11_00.00.00.nc \
  --out-file /host/mpas_analysis/8run_summary.png"
```

The `--pairs` and `--pair-labels` flags let you build summary figures for any subset or extension of the default four-pair matrix.

### Paper composite figures (from the l=4 primary pair)

```bash
docker exec mpas8 bash -c "python3 /host/reproducibility/analysis/make_paper_composites.py \
  --pair-dir /host/mpas_analysis/l4_pair \
  --out-dir /host/mpas_analysis \
  --salt-ref /host/simulation_outputs/results_120km_jan_pohlker_l4_salt/history.2025-02-11_00.00.00.nc"
```

Produces `l4_mechanism_4panel.png`, `l4_polar_winds.png`, `l4_nwfa_day1.png` — the figures used in the EarthArxiv preprint.

### Column diagnostic (mechanistic explanation of sign-flip)

```bash
docker exec mpas8 bash -c "python3 /host/reproducibility/analysis/column_diag_ensemble_l4.py \
  --salt-dir /host/simulation_outputs/results_120km_jan_pohlker_l4_salt \
  --nosalt-dir /host/simulation_outputs/results_120km_jan_pohlker_l4_nosalt \
  --dp-npz /host/mpas_analysis/l4_pair/deltaP_data.npz \
  --out-dir /host/mpas_analysis/l4_pair"
```

Produces three figures (`column_timemean_ens.png`, `column_heat_budget.png`, `column_peak_snapshot.png`) and a summary text file documenting the 10 max-ΔP and 10 min-ΔP cells inside the Amazon box. `--n-cells`, `--box-lat`, `--box-lon` let you retune the ensemble and the region of interest.

> **Git Bash on Windows:** if you launch from Git Bash, wrap the whole `docker exec mpas8 ...` invocation in `bash -c "..."` (as shown above) so MSYS doesn't rewrite the `/host/` paths on the way in. On Linux or WSL2 native shells the wrapping is unnecessary.

---

## What Our Results Showed

**240 km April, full GCCN lifecycle physics:**
- Equatorial rain change: +0.05 mm/day
- 30°N transport change: −95 TW (correct sign — salt reduces poleward transport)
- Antarctic temperature: −1.03 K
- Arctic temperature: +0.43 K (seasonal asymmetry in April)

**120 km January:**
- Equatorial rain change: −0.26 mm/day
- 30°N transport change: −17 TW (still correct sign, smaller magnitude)
- Arctic temperature: +1.85 K
- Antarctic temperature: +0.01 K

The January result did not produce the hoped-for Arctic cooling — weather noise at 30 days is large and may dominate the forced signal. Longer runs and ensemble members are needed.

---

## What's NOT in this repo

**Simulation output data (~200 GB total)** — too large for git. If you'd like access to the actual NetCDF output files for direct plot reproduction, contact the author. A Zenodo archive is planned.

**WPS (Weather Research and Forecasting Preprocessing System)** — needed for GFS→MPAS intermediate file conversion. Not included. Options:
- Build from https://github.com/wrf-model/WPS
- Use our CentOS 7 container (`Dockerfile.mpas7_centos`) which has WPS pre-built
- Use pre-converted intermediate files if published to a data archive

---

## Known Issues

1. **The salt init rebuild is easy to forget.** Between CONTROL and NO-SALT runs, you must swap the `mpas_atmphys_init_microphysics.F` file AND rebuild. Our experience: we once ran both phases with the no-salt version and got identical results. The paper draft documents this debugging journey.

2. **GCCN tracer output.** `ngccn` is computed internally but may not appear in `history.*.nc` unless added to the output stream. Check `streams.atmosphere` to confirm.

3. **Floating-point exception warnings** in the log (IEEE_UNDERFLOW_FLAG, IEEE_DENORMAL) are normal for MPAS microphysics and do not indicate errors.

4. **Windows path issues.** Docker bind mounts on Windows require `MSYS_NO_PATHCONV=1` prefix in Git Bash.

---

## Contributing

Found a bug? Improved the physics? Ran at a new resolution or season?

Open an issue or pull request at https://github.com/bluesaltbarrier/blue-salt-barrier

Specifically seeking contributions from:
- Cloud microphysicists (review the GCCN code)
- Tropical ecologists (salt emission inventories)
- Climate modelers (integration into Earth System Models)
- Anyone with HPC access who can run at 60 km or finer

## License

CC BY 4.0. Use, adapt, redistribute, with attribution.
