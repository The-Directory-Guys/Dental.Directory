-- Lets a signed-in clinic owner add new practitioners to their own clinic
-- (the earlier policy only covered updating existing ones).
-- Run once in the Supabase SQL Editor.

grant insert on clinic_practitioners to authenticated;

create policy "Clinic owners can add practitioners to their own clinic"
on clinic_practitioners for insert
to authenticated
with check (clinic_id in (select clinic_id from clinic_owners where user_id = auth.uid()));
