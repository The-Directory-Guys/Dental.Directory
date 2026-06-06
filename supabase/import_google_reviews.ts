/**
 * Import christchurch_reviews.json into the google_reviews table.
 *
 * Prerequisites:
 *   1. Run supabase/create_google_reviews.sql in the Supabase dashboard SQL editor
 *   2. Ensure dental_clinics rows exist (run import.ts first if needed)
 *
 * Usage:
 *   node --use-system-ca node_modules/.bin/tsx supabase/import_google_reviews.ts
 *   (run from project root)
 */

import { createClient } from "@supabase/supabase-js";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";

function loadEnv() {
  const root = process.cwd();
  const envPath = [path.join(root, ".env"), path.join(root, ".env.txt")].find(
    (p) => fs.existsSync(p)
  );
  if (!envPath) return;
  for (const line of fs.readFileSync(envPath, "utf-8").split(/\r?\n/)) {
    const t = line.trim();
    if (!t || t.startsWith("#")) continue;
    const eq = t.indexOf("=");
    if (eq === -1) continue;
    const key = t.slice(0, eq).trim();
    let val = t.slice(eq + 1).trim();
    if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'")))
      val = val.slice(1, -1);
    if (!process.env[key]) process.env[key] = val;
  }
}

loadEnv();

const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY!;

if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
  console.error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY");
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const reviewsPath = path.join(__dirname, "..", "christchurch_reviews.json");
const reviewsData = JSON.parse(fs.readFileSync(reviewsPath, "utf-8"));

async function main() {
  // Fetch all clinic IDs keyed by name
  // Fetch all clinics with pagination (Supabase default limit is 1000)
  const allClinics: { id: number; name: string }[] = [];
  const PAGE = 1000;
  for (let from = 0; ; from += PAGE) {
    const { data, error } = await supabase
      .from("dental_clinics")
      .select("id, name")
      .range(from, from + PAGE - 1);
    if (error) throw new Error(error.message);
    if (!data?.length) break;
    allClinics.push(...data);
    if (data.length < PAGE) break;
  }
  console.log(`Loaded ${allClinics.length} clinics from Supabase`);

  const clinicByName = new Map(allClinics.map((c) => [c.name, c.id]));

  // Clear existing google_reviews for Christchurch clinics
  const christchurchIds = Object.keys(reviewsData)
    .map((name) => clinicByName.get(name))
    .filter((id): id is number => id !== undefined);

  if (christchurchIds.length) {
    const { error: delErr } = await supabase
      .from("google_reviews")
      .delete()
      .in("clinic_id", christchurchIds);
    if (delErr) throw new Error(`Delete failed: ${delErr.message}`);
    console.log(`Cleared existing reviews for ${christchurchIds.length} clinics`);
  }

  let totalInserted = 0;
  let skipped = 0;

  for (const [clinicName, data] of Object.entries(reviewsData) as [string, any][]) {
    const clinicId = clinicByName.get(clinicName);
    if (!clinicId) {
      console.warn(`  Skipping — not found in DB: ${clinicName}`);
      skipped++;
      continue;
    }

    const reviews = data.reviews ?? [];
    if (!reviews.length) continue;

    const rows = reviews.map((rv: any) => ({
      clinic_id: clinicId,
      author: rv.author ?? null,
      rating: rv.rating ?? null,
      date_text: rv.date ?? null,
      snippet: rv.snippet ?? null,
    }));

    const CHUNK = 100;
    for (let i = 0; i < rows.length; i += CHUNK) {
      const { error } = await supabase
        .from("google_reviews")
        .insert(rows.slice(i, i + CHUNK));
      if (error) throw new Error(`Insert failed for ${clinicName}: ${error.message}`);
    }

    totalInserted += rows.length;
    console.log(`  ${clinicName}: ${reviews.length} reviews`);
  }

  console.log(`\nDone. ${totalInserted} reviews imported, ${skipped} clinics skipped.`);
}

main().catch((e) => {
  console.error(e.message);
  process.exit(1);
});
