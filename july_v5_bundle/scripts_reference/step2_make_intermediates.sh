#!/bin/bash
# Step 2 — GFS GRIB2 -> WPS intermediate format (the "FILE:" files MPAS reads).
# Runs INSIDE the container:
#   docker exec mpas8 bash /opt/july_v5/step2_make_intermediates.sh
#
# ungrib.exe and Vtable.GFS are baked into the image at /opt/july_v5/wps/.
# Reads  /host/v5_july/gfs/*.grib2
# Writes /host/v5_july/intermediates/FILE:YYYY-07-12_00
# ---------------------------------------------------------------------------
set -e

YEARS="2021 2022 2023 2024 2025"
MONTHDAY="0712"
HOUR="00"

UNGRIB=/opt/july_v5/wps/ungrib.exe
VTABLE=/opt/july_v5/wps/Vtable.GFS
GFSDIR=/host/v5_july/gfs
INTDIR=/host/v5_july/intermediates
mkdir -p "$INTDIR"

echo "=================================================================="
echo " Step 2 — ungrib: GRIB2 -> WPS intermediate"
echo "=================================================================="

[ -x "$UNGRIB" ] || { echo "ERROR: ungrib.exe missing at $UNGRIB"; exit 1; }

WORK=$(mktemp -d); trap 'rm -rf "$WORK"' EXIT
cd "$WORK"
ln -sf "$VTABLE" Vtable

for YEAR in $YEARS; do
  DATE="${YEAR}${MONTHDAY}"
  GRIB="${GFSDIR}/gfs.0p25.${DATE}${HOUR}.f000.grib2"
  [ -f "$GRIB" ] || { echo "[$YEAR] GRIB2 missing: $GRIB — run Step 1 first"; exit 1; }

  echo "[$YEAR] ungrib $GRIB"
  rm -f GRIBFILE.* FILE:* namelist.wps
  ln -sf "$GRIB" GRIBFILE.AAA
  cat > namelist.wps <<EOF
&share
 wrf_core = 'ARW',
 max_dom  = 1,
 start_date = '${YEAR}-07-12_00:00:00',
 end_date   = '${YEAR}-07-12_00:00:00',
 interval_seconds = 21600,
/
&ungrib
 out_format = 'WPS',
 prefix = 'FILE',
/
EOF
  "$UNGRIB" > "ungrib.${YEAR}.log" 2>&1 || { echo "  ungrib failed:"; tail -25 "ungrib.${YEAR}.log"; exit 1; }
  OUT="FILE:${YEAR}-07-12_00"
  [ -f "$OUT" ] || { echo "  $OUT not produced:"; tail -25 "ungrib.${YEAR}.log"; exit 1; }
  cp "$OUT" "${INTDIR}/"
  echo "  -> ${INTDIR}/${OUT}  ($(du -h "${INTDIR}/${OUT}" | cut -f1))"
done

echo
echo "Intermediates in $INTDIR:"
ls -lh "$INTDIR"
echo
echo " Next: Step 3 — docker exec mpas8 bash /opt/july_v5/step3_make_july_init.sh"
