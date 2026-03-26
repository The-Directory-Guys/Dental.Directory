-- Run in Supabase SQL Editor if reviews.price_reports use int8 clinic_id
-- and dental_clinics has name as primary key but no numeric id yet.
--
-- Adds a unique bigserial `id` on dental_clinics (name stays the PK).
-- Rewires reviews / price_reports to reference dental_clinics(id).

-- 1) Numeric id for foreign keys (fills automatically for existing rows)
alter table dental_clinics add column if not exists id bigserial unique;

-- 2) Drop old FKs (names may differ — check Table Editor → constraints if this fails)
alter table reviews drop constraint if exists reviews_clinic_id_fkey;
alter table price_reports drop constraint if exists price_reports_clinic_id_fkey;

-- 3) Point clinic_id at dental_clinics.id
alter table reviews
  add constraint reviews_clinic_id_fkey
  foreign key (clinic_id) references dental_clinics (id) on delete cascade;

alter table price_reports
  add constraint price_reports_clinic_id_fkey
  foreign key (clinic_id) references dental_clinics (id) on delete cascade;
