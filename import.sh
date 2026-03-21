#!/usr/bin/env bash
# Import dental_clinics_all.csv into Supabase.
#
# Required env vars:
#   SUPABASE_URL         – Your Supabase project URL
#   SUPABASE_SERVICE_KEY – Supabase service role key (not anon key)

set -euo pipefail

if [ -z "${SUPABASE_URL:-}" ]; then
    echo "ERROR: SUPABASE_URL environment variable is not set."
    exit 1
fi

if [ -z "${SUPABASE_SERVICE_KEY:-}" ]; then
    echo "ERROR: SUPABASE_SERVICE_KEY environment variable is not set."
    exit 1
fi

if [ ! -f "dental_clinics_all.csv" ]; then
    echo "ERROR: dental_clinics_all.csv not found. Run run.sh first to scrape and merge data."
    exit 1
fi

echo "Importing dental_clinics_all.csv into Supabase..."
npm install --silent
SUPABASE_URL="$SUPABASE_URL" SUPABASE_SERVICE_KEY="$SUPABASE_SERVICE_KEY" \
    npx ts-node --esm supabase/import.ts
echo "Done."
