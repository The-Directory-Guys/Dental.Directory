-- Add city column (run once in Supabase SQL Editor if table already exists)

alter table dental_clinics add column if not exists city text;

update dental_clinics set city = 'NA' where city is null;
