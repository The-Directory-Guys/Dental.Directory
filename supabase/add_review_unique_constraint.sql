-- Add unique constraint to google_reviews to prevent duplicates across sources.
-- NULLS NOT DISTINCT treats NULL values as equal, so two rows with
-- (clinic_id=1, author=NULL, date_text=NULL) are considered duplicates.
-- Requires PostgreSQL 15+ (Supabase default).
--
-- Run this in the Supabase dashboard → SQL Editor before using upsert imports.

ALTER TABLE google_reviews
  ADD CONSTRAINT google_reviews_unique_review
  UNIQUE NULLS NOT DISTINCT (clinic_id, author, date_text);
