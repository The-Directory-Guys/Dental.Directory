-- Run in Supabase SQL Editor after backup.
-- Scraped fee/promo data from clinic websites (separate from user price_reports).

create table if not exists scraped_prices (
  id bigserial primary key,
  clinic_id bigint references dental_clinics (id) on delete cascade,
  source text not null,
  treatment text not null,
  price_nzd integer,
  price_label text not null,
  source_url text not null,
  scraped_at timestamptz not null default now(),
  notes text
);

create index if not exists scraped_prices_clinic_id_idx on scraped_prices (clinic_id);
create index if not exists scraped_prices_source_idx on scraped_prices (source);

comment on table scraped_prices is 'Website-scraped offers/fees; clinic_id null = chain-wide / not tied to one practice row';
comment on column scraped_prices.source is 'e.g. lumino_pricing_pages';
comment on column scraped_prices.price_nzd is 'Whole NZ dollars when known; null for percentage-only or descriptive offers';

alter table scraped_prices enable row level security;

drop policy if exists "Scraped prices are public" on scraped_prices;
create policy "Scraped prices are public" on scraped_prices for select using (true);
