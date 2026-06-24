-- Tables for the clinic "amenities" data scraped by scrape_amenities_claude.py
-- (parking, accessibility, sedation, practitioners, etc.) -- the 19-field
-- schema piloted nationally and recorded in amenities_*.json / amenities_scrape_errors.csv.
--
-- Run this once in the Supabase SQL Editor (Dashboard -> SQL Editor -> New query).

-- One row per clinic. Scalar/boolean fields only -- practitioners are
-- one-to-many and live in clinic_practitioners below.
CREATE TABLE clinic_amenities (
  clinic_id                 bigint PRIMARY KEY REFERENCES dental_clinics(id) ON DELETE CASCADE,
  parking_access            text,
  wheelchair_accessible     boolean,
  same_day_emergency        boolean,
  saturday_evening_hours    boolean,
  in_house_specialists      text,
  practice_size             text,
  sedation_options          text,
  calming_amenities         text,
  dental_anxiety_friendly   boolean,
  years_open                text,
  awards                    text[],
  professional_memberships  text[],
  before_after_gallery      boolean,
  online_booking            boolean,
  new_patient_forms_online  boolean,
  payment_partners          text,
  membership_plans          text,
  kids_family_friendly      text,
  source                    text,        -- e.g. 'scraper:clinicwebsite.co.nz'
  source_url                text,
  scraped_at                date DEFAULT CURRENT_DATE
);

-- One row per named dentist/practitioner found on a clinic's site.
CREATE TABLE clinic_practitioners (
  id           bigserial PRIMARY KEY,
  clinic_id    bigint NOT NULL REFERENCES dental_clinics(id) ON DELETE CASCADE,
  name         text NOT NULL,
  photo_url    text,
  experience   text,
  specialties  text,
  bio          text,
  languages    text,
  source_url   text,
  scraped_at   date DEFAULT CURRENT_DATE
);

CREATE INDEX idx_clinic_practitioners_clinic_id ON clinic_practitioners(clinic_id);

-- Public can read (same as dental_clinics/google_reviews/scraped_prices, which
-- the live site already queries with the anon key). Writes only happen via
-- the service-role key (used by the scraper scripts), which bypasses RLS
-- entirely, so no insert/update/delete policy is needed for anon/authenticated.
ALTER TABLE clinic_amenities ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinic_practitioners ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read access" ON clinic_amenities
  FOR SELECT USING (true);

CREATE POLICY "Public read access" ON clinic_practitioners
  FOR SELECT USING (true);
