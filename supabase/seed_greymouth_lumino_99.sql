-- Greymouth Lumino practices: $99 new patient offer (national Lumino promo).
-- Run once in SQL Editor. Safe to re-run if you delete duplicates first.

insert into scraped_prices (clinic_id, source, treatment, price_nzd, price_label, source_url, notes)
select
  c.id,
  'lumino_new_patient_99',
  'New patient exam and x-rays (promotional offer)',
  99,
  '$99 New Patient Check-Up (Lumino national offer)',
  'https://lumino.co.nz/pricing-offers/99-new-patient-check-up/',
  'Participating Lumino practice (Greymouth); confirm availability and terms when booking.'
from dental_clinics c
where (c.google_maps_url like '%cid=12335065779227543131%'
   or c.google_maps_url like '%cid=15764414591835748325%')
  and not exists (
    select 1 from scraped_prices sp
    where sp.clinic_id = c.id
      and sp.source = 'lumino_new_patient_99'
      and sp.price_nzd = 99
  );
