#!/usr/bin/env bash
# Run all dental clinic scrapers for New Zealand regions.
# Requires: GOOGLE_PLACES_API_KEY environment variable to be set.

set -euo pipefail

if [ -z "${GOOGLE_PLACES_API_KEY:-}" ]; then
    echo "ERROR: GOOGLE_PLACES_API_KEY environment variable is not set."
    exit 1
fi

SCRAPERS=(
    scrape_dental_clinics.py
    scrape_bay_of_plenty.py
    scrape_canterbury.py
    scrape_gisborne.py
    scrape_hawkes_bay.py
    scrape_manawatu_whanganui.py
    scrape_northland.py
    scrape_taranaki.py
)

for script in "${SCRAPERS[@]}"; do
    echo "Running $script..."
    python3 "$script"
    echo "Done: $script"
    echo "---"
done

echo "All scrapers completed."
