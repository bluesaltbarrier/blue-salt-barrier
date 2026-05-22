#!/bin/bash
# Step 1 — download GFS 0.25-degree analysis for 5 July-12 dates.
# Runs INSIDE the container:
#   docker exec -it mpas8 bash /opt/july_v5/step1_download_gfs.sh
#
# Source: NCAR RDA dataset d084.1 (permanent archive, covers 2015-present).
# Free account required: register at https://rda.ucar.edu
#
# Downloads the 0-hour analysis (f000) at 00 UTC on July 12 of each year to
# /host/v5_july/gfs/ . MPAS init_atmosphere (config_init_case=7) cold-starts
# from a single analysis time, so one GRIB2 file per year is enough.
#
# Run with -it (interactive) so the password prompt works.
# ---------------------------------------------------------------------------
set -e

# === YEARS — edit this one line for Option B (2022-2026) ===
YEARS="2021 2022 2023 2024 2025"
MONTHDAY="0712"
HOUR="00"

OUTDIR=/host/v5_july/gfs
mkdir -p "$OUTDIR"

echo "=================================================================="
echo " Step 1 — GFS analysis download   Years: $YEARS   (July ${MONTHDAY:2:2}, ${HOUR}UTC)"
echo " Output: $OUTDIR"
echo "=================================================================="
echo

read -rp  "NCAR RDA account email: " RDA_EMAIL
read -rsp "NCAR RDA password: "      RDA_PASS
echo; echo

COOKIES=$(mktemp)
trap 'rm -f "$COOKIES"' EXIT

echo "Authenticating with NCAR RDA..."
curl -s -o /dev/null -k -c "$COOKIES" \
  -d "email=${RDA_EMAIL}&passwd=${RDA_PASS}&action=login" \
  https://rda.ucar.edu/cgi-bin/login || true

for YEAR in $YEARS; do
  DATE="${YEAR}${MONTHDAY}"
  URL="https://data.rda.ucar.edu/d084001/${YEAR}/${DATE}/gfs.0p25.${DATE}${HOUR}.f000.grib2"
  OUT="${OUTDIR}/gfs.0p25.${DATE}${HOUR}.f000.grib2"

  if [ -f "$OUT" ] && [ "$(stat -c%s "$OUT" 2>/dev/null || echo 0)" -gt 100000000 ]; then
    echo "[$YEAR] already present ($(du -h "$OUT" | cut -f1)) — skipping"
    continue
  fi
  echo "[$YEAR] downloading..."
  curl -s -k -b "$COOKIES" -o "$OUT" "$URL" || { echo "  FAILED for $YEAR"; continue; }
  echo "  saved $OUT ($(du -h "$OUT" 2>/dev/null | cut -f1))"
done

echo
echo "Files in $OUTDIR:"
ls -lh "$OUTDIR"/*.grib2 2>/dev/null || echo " (none — check RDA credentials / download manually from d084.1)"
echo
echo " Next: Step 2 — docker exec mpas8 bash /opt/july_v5/step2_make_intermediates.sh"
