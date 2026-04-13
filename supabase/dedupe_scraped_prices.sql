-- Remove duplicate scraped_prices rows for the same clinic + source + price.
-- Keeps the row with the smallest id in each group. Run in Supabase SQL Editor.
--
-- Note: We do NOT include `treatment` in the partition. Duplicate pushes often
-- differ only in treatment text (e.g. name prefix, scrape wording), so the old
-- (clinic_id, source, treatment, price_nzd) dedupe left pairs intact.

-- Optional: see groups that still have more than one row before deleting
-- select clinic_id, source, price_nzd, count(*) as n
-- from scraped_prices
-- group by clinic_id, source, price_nzd
-- having count(*) > 1;

delete from scraped_prices
where id in (
  select id
  from (
    select
      id,
      row_number() over (
        partition by
          clinic_id,
          source,
          price_nzd
        order by id
      ) as rn
    from scraped_prices
    where clinic_id is not null
  ) sub
  where rn > 1
);

-- If you ever have rows with clinic_id null and want to dedupe those too, run separately:
-- delete from scraped_prices
-- where id in (
--   select id from (
--     select id,
--       row_number() over (
--         partition by source, treatment, price_nzd, coalesce(source_url, '')
--         order by id
--       ) as rn
--     from scraped_prices
--     where clinic_id is null
--   ) s where rn > 1
-- );
