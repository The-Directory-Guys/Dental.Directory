-- Rename column town -> suburb_town on dental_clinics (run once in SQL Editor)

alter table dental_clinics rename column town to suburb_town;

-- After this, set in .env for imports: CLINICS_SUBURB_COLUMN=suburb_town
-- (or remove CLINICS_SUBURB_COLUMN if your import defaults to suburb_town — check import.ts)
