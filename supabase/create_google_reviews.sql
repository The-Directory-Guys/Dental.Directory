-- Google Maps reviews scraped via SerpAPI
create table if not exists google_reviews (
  id         bigserial primary key,
  clinic_id  bigint not null references dental_clinics (id) on delete cascade,
  author     text,
  rating     integer check (rating between 1 and 5),
  date_text  text,
  snippet    text,
  fetched_at timestamptz default now()
);

create index if not exists google_reviews_clinic_id_idx on google_reviews (clinic_id);
create index if not exists google_reviews_rating_idx on google_reviews (rating desc);

alter table google_reviews enable row level security;

create policy "Google reviews are public"
  on google_reviews for select using (true);
