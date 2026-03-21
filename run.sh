#!/usr/bin/env bash
# End-to-end script: scrape all NZ dental clinic data, merge into a single CSV,
# then import into Supabase.
#
# Required env vars:
#   GOOGLE_PLACES_API_KEY  – Google Places API key for scraping
#   SUPABASE_URL           – Your Supabase project URL
#   SUPABASE_SERVICE_KEY   – Supabase service role key (not anon key)

set -euo pipefail

# ── Validate env vars ────────────────────────────────────────────────────────
if [ -z "${GOOGLE_PLACES_API_KEY:-}" ]; then
    echo "ERROR: GOOGLE_PLACES_API_KEY environment variable is not set."
    exit 1
fi

if [ -z "${SUPABASE_URL:-}" ]; then
    echo "ERROR: SUPABASE_URL environment variable is not set."
    exit 1
fi

if [ -z "${SUPABASE_SERVICE_KEY:-}" ]; then
    echo "ERROR: SUPABASE_SERVICE_KEY environment variable is not set."
    exit 1
fi

# ── Scrape each region ───────────────────────────────────────────────────────
SCRAPERS=(
    scrape_auckland.py
    scrape_bay_of_plenty.py
    scrape_canterbury.py
    scrape_dental_clinics.py
    scrape_gisborne.py
    scrape_hawkes_bay.py
    scrape_manawatu_whanganui.py
    scrape_northland.py
    scrape_taranaki.py
    scrape_waikato.py
    scrape_wellington.py
)

for script in "${SCRAPERS[@]}"; do
    echo "Running $script..."
    python3 "$script"
    echo "Done: $script"
    echo "---"
done

echo "All scrapers completed."

# ── Merge regional CSVs into dental_clinics_all.csv ─────────────────────────
echo "Merging regional CSVs into dental_clinics_all.csv..."

HEADER_WRITTEN=false
OUTPUT="dental_clinics_all.csv"
> "$OUTPUT"

for csv in dental_clinics_auckland.csv \
           dental_clinics_bay_of_plenty.csv \
           dental_clinics_canterbury.csv \
           dental_clinics_christchurch.csv \
           dental_clinics_gisborne.csv \
           dental_clinics_hawkes_bay.csv \
           dental_clinics_manawatu_whanganui.csv \
           dental_clinics_marlborough.csv \
           dental_clinics_nelson_tasman.csv \
           dental_clinics_northland.csv \
           dental_clinics_otago.csv \
           dental_clinics_southland.csv \
           dental_clinics_taranaki.csv \
           dental_clinics_waikato.csv \
           dental_clinics_wellington.csv \
           dental_clinics_west_coast.csv; do
    if [ ! -f "$csv" ]; then
        echo "  Skipping missing file: $csv"
        continue
    fi
    if [ "$HEADER_WRITTEN" = false ]; then
        cat "$csv" >> "$OUTPUT"
        HEADER_WRITTEN=true
    else
        tail -n +2 "$csv" >> "$OUTPUT"
    fi
    echo "  Merged: $csv"
done

echo "Merge complete: $OUTPUT"

# ── Import into Supabase ─────────────────────────────────────────────────────
echo "Importing data into Supabase..."
npm install --silent
SUPABASE_URL="$SUPABASE_URL" SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY" \
    npx ts-node --esm supabase/import.ts
echo "Import complete."
