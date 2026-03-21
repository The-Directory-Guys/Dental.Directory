/**
 * Import dental_clinics_all.csv into Supabase.
 *
 * Usage:
 *   SUPABASE_URL=... SUPABASE_SERVICE_KEY=... npx ts-node --esm supabase/import.ts
 *
 * Requires: npm install (see package.json devDependencies)
 */

import { createClient } from "@supabase/supabase-js";
import { parse } from "csv-parse/sync";
import * as fs from "fs";
import * as path from "path";

const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY!;

if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
  console.error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY");
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

async function main() {
  const csvPath = path.join(new URL("..", import.meta.url).pathname, "dental_clinics_all.csv");
  const raw = fs.readFileSync(csvPath, "utf-8");

  const records = parse(raw, { columns: true, skip_empty_lines: true });

  const rows = (records as Record<string, string>[]).map((r) => ({
    name: r.name,
    address: r.address,
    phone: r.phone_national,
    website: r.website || null,
    rating: r.rating ? parseFloat(r.rating) : null,
    total_ratings: r.total_ratings ? parseInt(r.total_ratings) : null,
    business_status: r.business_status,
    google_maps_url: r.google_maps_url,
    opening_hours: r.opening_hours,
    category: r.category,
    region: r.region,
    town: r.town,
    price: r.price !== "no_prices" ? r.price : null,
  }));

  console.log(`Importing ${rows.length} clinics...`);

  // Insert in batches of 500
  for (let i = 0; i < rows.length; i += 500) {
    const batch = rows.slice(i, i + 500);
    const { error } = await supabase
      .from("clinics")
      .upsert(batch, { onConflict: "google_maps_url" });
    if (error) {
      console.error(`Batch ${i / 500 + 1} failed:`, error.message);
    } else {
      console.log(`Batch ${i / 500 + 1} done (${i + batch.length}/${rows.length})`);
    }
  }

  console.log("Import complete.");
}

main();
