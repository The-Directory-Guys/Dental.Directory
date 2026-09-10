-- Enabling RLS on clinic_practitioners (in add_practitioner_photo_policy.sql)
-- may have left signed-in owners unable to see their own practitioners, if
-- the existing "public can view" policy was scoped only to the anon role.
-- google_reviews already had RLS enabled before this project touched it and
-- was set up the same ad hoc way, so it's at risk of the identical bug -
-- fixing both here as a precaution. This adds explicit read access for
-- authenticated users without touching whatever the original policies say.
-- Run once in the Supabase SQL Editor.

create policy "Authenticated users can also view practitioners"
on clinic_practitioners for select
to authenticated
using (true);

create policy "Authenticated users can also view reviews"
on google_reviews for select
to authenticated
using (true);
