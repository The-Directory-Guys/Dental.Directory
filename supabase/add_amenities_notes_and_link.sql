-- Adds an optional note to each amenity toggle (matching the existing
-- online_booking_note pattern) plus a dedicated online booking link field.
-- Run once in the Supabase SQL Editor.

ALTER TABLE clinic_amenities ADD COLUMN IF NOT EXISTS wheelchair_accessible_note text;
ALTER TABLE clinic_amenities ADD COLUMN IF NOT EXISTS dental_anxiety_friendly_note text;
ALTER TABLE clinic_amenities ADD COLUMN IF NOT EXISTS kids_family_friendly_note text;
ALTER TABLE clinic_amenities ADD COLUMN IF NOT EXISTS same_day_emergency_note text;
ALTER TABLE clinic_amenities ADD COLUMN IF NOT EXISTS online_booking_link text;
