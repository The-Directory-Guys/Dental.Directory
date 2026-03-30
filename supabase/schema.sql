-- Dental Directory Schema
-- Primary key is `id` (bigserial). `name` is not unique (same brand, multiple sites).
-- `google_maps_url` is unique when present (one row per Google listing).

create table dental_clinics (
  id          bigserial primary key,
  name        text not null,
  address     text,
  phone_national text,
  phone_international text,
  website     text,
  rating      numeric(2,1),
  total_ratings integer,
  business_status text,
  google_maps_url text unique,
  opening_hours text,
  category    text,
  region      text,
  suburb_town text,
  city        text,
  price       text,
  date_scraped date
);

create index on dental_clinics (region);
create index on dental_clinics (rating desc);
create index on dental_clinics using gin (to_tsvector('english', name || ' ' || coalesce(address, '')));

create table reviews (
  id          bigserial primary key,
  clinic_id   bigint not null references dental_clinics (id) on delete cascade,
  user_id     uuid references auth.users(id) on delete cascade,
  rating      integer check (rating between 1 and 5),
  body        text,
  created_at  timestamptz default now()
);

create index on reviews (clinic_id);

create table price_reports (
  id          bigserial primary key,
  clinic_id   bigint not null references dental_clinics (id) on delete cascade,
  user_id     uuid references auth.users(id) on delete cascade,
  treatment   text not null,
  price_nzd   integer not null,
  notes       text,
  created_at  timestamptz default now()
);

create index on price_reports (clinic_id);

alter table reviews enable row level security;
alter table price_reports enable row level security;

create policy "Reviews are public" on reviews for select using (true);
create policy "Prices are public" on price_reports for select using (true);

create policy "Users insert own reviews" on reviews for insert
  with check (auth.uid() = user_id);

create policy "Users insert own prices" on price_reports for insert
  with check (auth.uid() = user_id);

create policy "Users delete own reviews" on reviews for delete
  using (auth.uid() = user_id);

create policy "Users delete own prices" on price_reports for delete
  using (auth.uid() = user_id);
