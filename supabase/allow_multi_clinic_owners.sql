-- Allows one account to own more than one clinic (e.g. a multi-branch chain
-- where each branch keeps its own listing/email, but one person manages all
-- of them). Previously clinic_owners.user_id had a hard UNIQUE constraint -
-- one login could only ever own exactly one clinic.
--
-- The auto-link-on-email-confirm trigger is unaffected: it still only ever
-- links the ONE clinic whose email matches the signup email. Linking a
-- single account to additional clinics (e.g. other branches with different
-- listed emails) still has to be done manually, the same as any other
-- manual claim approval - this just makes it POSSIBLE for that account to
-- hold more than one link afterward.
-- Run once in the Supabase SQL Editor.

ALTER TABLE clinic_owners DROP CONSTRAINT IF EXISTS clinic_owners_user_id_key;

-- Still prevent the same (user, clinic) pair being linked twice by accident.
ALTER TABLE clinic_owners DROP CONSTRAINT IF EXISTS clinic_owners_user_clinic_unique;
ALTER TABLE clinic_owners ADD CONSTRAINT clinic_owners_user_clinic_unique UNIQUE (user_id, clinic_id);
