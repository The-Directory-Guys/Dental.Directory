-- One-off: remove Lumino national promo rows from scraped_prices (run in SQL Editor).
delete from scraped_prices
where source = 'lumino_pricing_pages';
