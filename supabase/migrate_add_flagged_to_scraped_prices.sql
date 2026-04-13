-- Add flagged column to scraped_prices for marking low-confidence/suspicious scrape results.
alter table scraped_prices
  add column if not exists flagged boolean not null default false;
