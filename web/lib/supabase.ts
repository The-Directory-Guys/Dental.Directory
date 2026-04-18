import { createClient } from "@supabase/supabase-js";

export type Clinic = {
  id: number;
  name: string;
  address: string;
  phone_national: string | null;
  phone_international: string | null;
  website: string | null;
  rating: number | null;
  total_ratings: number | null;
  business_status: string;
  google_maps_url: string;
  opening_hours: string | null;
  category: string | null;
  region: string;
  /** Present when DB column is `suburb_town` */
  suburb_town?: string | null;
  /** Present when DB column is still `town` (legacy) */
  town?: string | null;
  /** Main city label, e.g. Auckland, or NA (optional until DB migrated) */
  city?: string | null;
  price: string | null;
  prices_last_updated: string | null;
};

export type Review = {
  id: number;
  clinic_id: number;
  user_id: string;
  rating: number;
  body: string;
  created_at: string;
};

export type PriceReport = {
  id: number;
  clinic_id: number;
  user_id: string;
  treatment: string;
  price_nzd: number;
  notes: string | null;
  created_at: string;
};

/** Automated website scrape (see scraped_prices table); clinic_id null = chain-wide */
export type ScrapedPrice = {
  id: number;
  clinic_id: number | null;
  source: string;
  treatment: string;
  price_nzd: number | null;
  price_label: string;
  source_url: string;
  scraped_at: string;
  notes: string | null;
};

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);
