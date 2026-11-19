-- Captures the business owner's reply as it appears on Google itself
-- (separate from owner_reply/owner_reply_at, which is the Dental Compare
-- website's own reply feature). Run once in the Supabase SQL Editor.

ALTER TABLE google_reviews ADD COLUMN IF NOT EXISTS google_reply text;
ALTER TABLE google_reviews ADD COLUMN IF NOT EXISTS google_reply_date_text text;
