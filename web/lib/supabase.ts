import { createClient } from "@supabase/supabase-js";

export type Clinic = {
  id: number;
  name: string;
  address: string;
  phone: string | null;
  website: string | null;
  rating: number | null;
  total_ratings: number | null;
  business_status: string;
  google_maps_url: string;
  opening_hours: string | null;
  category: string | null;
  region: string;
  town: string | null;
  price: string | null;
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

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
);
