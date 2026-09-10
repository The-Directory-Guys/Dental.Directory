-- Lets a signed-in clinic owner create/edit their own clinic_amenities row
-- (Miscellaneous + Payment Options sections). clinic_id is the primary key,
-- so a clinic either has exactly one row or none yet - owners need INSERT
-- for the "none yet" case and UPDATE for editing an existing row.
-- Run once in the Supabase SQL Editor.

grant insert, update on clinic_amenities to authenticated;

create policy "Clinic owners can manage their own amenities"
on clinic_amenities for all
to authenticated
using (clinic_id in (select clinic_id from clinic_owners where user_id = auth.uid()))
with check (clinic_id in (select clinic_id from clinic_owners where user_id = auth.uid()));
