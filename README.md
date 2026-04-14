# Dental Directory NZ

The codebase behind [dentalcompare.co.nz](https://dentalcompare.co.nz) — a directory of dental clinics across all 15 New Zealand regions, with ratings, opening hours, pricing data, and user reviews. Built on Supabase and Next.js.

## Structure

```
.
├── dental_clinics_all.csv      # Source of truth for all clinic data
├── scrape_*.py                 # Google Places scrapers, one per region
├── scrape_lumino_prices.py     # Price scraper for Lumino chain
├── scrape_region_prices.py     # Price scraper for regional clinic websites
├── filter_private_price_directory.py
├── remove_false_listings.py    # Removes non-dental entries from CSV
├── run.sh                      # Scrape all regions → merge into CSV
├── import.sh                   # Import CSV → Supabase
├── requirements.txt            # Python dependencies
├── supabase/
│   ├── schema.sql              # Full database schema
│   ├── import.ts               # TypeScript import script
│   └── *.sql                   # Utility SQL (deduplication, seeds)
└── web/                        # Next.js frontend
    ├── app/
    │   ├── page.tsx            # Homepage — search and browse clinics
    │   └── clinics/[id]/       # Clinic detail page
    ├── components/
    │   ├── ReviewForm.tsx       # User review submission
    │   └── PriceForm.tsx        # User price report submission
    └── lib/supabase.ts         # Supabase client and types
```

## Data Pipeline

Clinic data is sourced from the Google Places API, cleaned manually, and imported into Supabase.

**To re-scrape and rebuild the CSV:**
```bash
export GOOGLE_PLACES_API_KEY=your_key_here
./run.sh
```

**To import the CSV into Supabase:**
```bash
# Set these in a .env file or export them
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_SERVICE_KEY=your_service_role_key

./import.sh
```

## Web App

Built with Next.js 16, React 19, and Tailwind CSS. Connects to Supabase via the public anon key.

**To run locally:**
```bash
cd web
cp .env.local.example .env.local  # Add your Supabase URL and anon key
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

**Environment variables** (`web/.env.local`):
```
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

## Database

The schema is defined in [supabase/schema.sql](supabase/schema.sql). Key tables:

| Table | Description |
|---|---|
| `dental_clinics` | Core clinic data — name, address, region, category, ratings |
| `reviews` | User-submitted star ratings and review text |
| `price_reports` | User-submitted treatment prices |
| `scraped_prices` | Prices scraped from clinic and chain websites |

Clinic categories: `dentist`, `orthodontist`, `dentures`, `dentist_and_orthodontist`, `dentist_and_dentures`, `hygienist`, `whitening`.

## Python Dependencies

```bash
pip install -r requirements.txt
```

Requires Python 3.9+.
