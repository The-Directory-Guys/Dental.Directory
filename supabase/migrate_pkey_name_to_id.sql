-- Migrate dental_clinics from PRIMARY KEY (name) to PRIMARY KEY (id).
-- Run in Supabase SQL Editor (backup first). Safe if reviews/price_reports empty.
--
-- Prerequisites: column `id` exists (bigint/bigserial). If not, run migrate_clinic_id_int8.sql first.

begin;

alter table reviews drop constraint if exists reviews_clinic_id_fkey;
alter table price_reports drop constraint if exists price_reports_clinic_id_fkey;

-- Ensure every row has a numeric id
alter table dental_clinics add column if not exists id bigserial unique;

alter table dental_clinics drop constraint if exists dental_clinics_pkey;

alter table dental_clinics add primary key (id);

-- Allow duplicate names across rows
create unique index if not exists dental_clinics_google_maps_url_uidx
  on dental_clinics (google_maps_url)
  where google_maps_url is not null and btrim(google_maps_url) <> '';

alter table reviews
  add constraint reviews_clinic_id_fkey
  foreign key (clinic_id) references dental_clinics (id) on delete cascade;

alter table price_reports
  add constraint price_reports_clinic_id_fkey
  foreign key (clinic_id) references dental_clinics (id) on delete cascade;

commit;
