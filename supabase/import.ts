/**
 * Import dental_clinics_all.csv into Supabase.
 *
 * Primary key on dental_clinics is `id` (bigserial). Rows are matched by
 * `google_maps_url` (must be unique in DB). Duplicate URLs in the CSV keep the last row.
 *
 * Usage:
 *   .env: SUPABASE_URL, SUPABASE_SERVICE_KEY
 *   npm run import-supabase
 *
 * Set SKIP_ORPHAN_DELETE=1 to skip removing DB rows whose URL is not in the CSV.
 * Set CLINICS_ID_COLUMN if the PK column is not `id` (unusual).
 *
 * CSV uses `suburb_town`. Default DB column is `suburb_town` (see schema.sql / after migration).
 * If your table still has `town` only, set in .env: CLINICS_SUBURB_COLUMN=town
 */

import { createClient } from "@supabase/supabase-js";
import { parse } from "csv-parse/sync";
import * as fs from "fs";
import * as path from "path";
import { fileURLToPath } from "url";

function loadEnvFromDotEnv() {
  const root = process.cwd();
  const envPath = [path.join(root, ".env"), path.join(root, ".env.txt")].find(
    (p) => fs.existsSync(p)
  );
  if (!envPath) return;
  const text = fs.readFileSync(envPath, "utf-8");
  for (const line of text.split(/\r?\n/)) {
    const t = line.trim();
    if (!t || t.startsWith("#")) continue;
    const eq = t.indexOf("=");
    if (eq === -1) continue;
    const key = t.slice(0, eq).trim();
    let val = t.slice(eq + 1).trim();
    if (
      (val.startsWith('"') && val.endsWith('"')) ||
      (val.startsWith("'") && val.endsWith("'"))
    ) {
      val = val.slice(1, -1);
    }
    if (!process.env[key]) process.env[key] = val;
  }
}

loadEnvFromDotEnv();

const SUPABASE_URL = process.env.SUPABASE_URL!;
const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY!;

if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
  console.error("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY");
  process.exit(1);
}

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_KEY);

const CLINICS_TABLE = "dental_clinics";

/** Primary key column (default `id`) */
const CLINICS_PK = (process.env.CLINICS_ID_COLUMN || "id").trim();

/** DB column for suburb/town (default `suburb_town`; use env `town` for unmigrated DBs) */
const SUBURB_DB_COL = (process.env.CLINICS_SUBURB_COLUMN || "suburb_town").trim();

const DELETE_BATCH = 200;

/** Supabase/Cloudflare sometimes returns HTML 502 pages — retry these */
function isTransientGatewayError(message: string | undefined | null): boolean {
  if (!message) return false;
  if (message.includes("<!DOCTYPE html>") || message.includes("Bad gateway")) return true;
  return /\b502\b|\b503\b|\b504\b|timeout|ECONNRESET|ETIMEDOUT|Service Unavailable/i.test(
    message
  );
}

function shortenErrorMessage(message: string): string {
  if (message.includes("<!DOCTYPE html>")) {
    return "Supabase gateway error (502/503). Wait a minute and run the import again.";
  }
  return message.length > 400 ? `${message.slice(0, 400)}…` : message;
}

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms));
}

async function withPostgrestRetry<T>(
  label: string,
  run: () => Promise<{ data: T; error: { message: string } | null }>,
  maxAttempts = 5
): Promise<{ data: T; error: null }> {
  let lastMsg = "";
  for (let attempt = 1; attempt <= maxAttempts; attempt++) {
    const { data, error } = await run();
    if (!error) return { data, error: null };
    lastMsg = error.message;
    if (!isTransientGatewayError(error.message) || attempt === maxAttempts) {
      throw new Error(shortenErrorMessage(error.message));
    }
    const waitMs = 2000 * attempt;
    console.warn(
      `${label}: transient error (attempt ${attempt}/${maxAttempts}), retry in ${waitMs}ms…`
    );
    await sleep(waitMs);
  }
  throw new Error(shortenErrorMessage(lastMsg));
}

type Pk = string | number;

type ClinicRow = {
  name: string;
  address: string;
  phone_national: string | null;
  phone_international: string | null;
  website: string | null;
  rating: number | null;
  total_ratings: number | null;
  business_status: string;
  google_maps_url: string;
  opening_hours: string;
  category: string;
  region: string;
  suburb_town: string;
  city: string;
  price: string | null;
  description: string | null;
};

/** Map CSV row to PostgREST payload (suburb_town → town or suburb_town column). */
function clinicRowToDb(row: ClinicRow): Record<string, unknown> {
  return {
    name: row.name,
    address: row.address,
    phone_national: row.phone_national,
    phone_international: row.phone_international,
    website: row.website,
    rating: row.rating,
    total_ratings: row.total_ratings,
    business_status: row.business_status,
    google_maps_url: row.google_maps_url,
    opening_hours: row.opening_hours,
    category: row.category,
    region: row.region,
    [SUBURB_DB_COL]: row.suburb_town,
    city: row.city || "NA",
    price: row.price,
    description: row.description || null,
  };
}

/** Last row wins per google_maps_url (required for unique url in DB). Rows without URL are kept. */
function dedupeRowsByGoogleMapsUrl(rows: ClinicRow[]): {
  rows: ClinicRow[];
  duplicateUrls: number;
} {
  const byUrl = new Map<string, ClinicRow>();
  const noUrl: ClinicRow[] = [];
  for (const r of rows) {
    const u = (r.google_maps_url || "").trim();
    if (!u) {
      noUrl.push(r);
      continue;
    }
    byUrl.set(u, r);
  }
  const deduped = [...byUrl.values(), ...noUrl];
  return {
    rows: deduped,
    duplicateUrls: rows.length - deduped.length,
  };
}

function dedupeInsertsByUrl(ins: ClinicRow[]): ClinicRow[] {
  const byUrl = new Map<string, ClinicRow>();
  const noUrl: ClinicRow[] = [];
  for (const r of ins) {
    const u = (r.google_maps_url || "").trim();
    if (!u) {
      noUrl.push(r);
      continue;
    }
    byUrl.set(u, r);
  }
  return [...byUrl.values(), ...noUrl];
}

function dedupeUpdatesByPk(
  toUpdate: { pk: Pk; row: ClinicRow }[]
): { pk: Pk; row: ClinicRow }[] {
  const map = new Map<string, { pk: Pk; row: ClinicRow }>();
  for (const u of toUpdate) {
    map.set(String(u.pk), u);
  }
  return [...map.values()];
}

async function flushInsertsAndUpdates(
  toInsert: ClinicRow[],
  toUpdate: { pk: Pk; row: ClinicRow }[]
) {
  const toInsertDeduped = dedupeInsertsByUrl(toInsert);
  const toUpdateDeduped = dedupeUpdatesByPk(toUpdate);

  const INSERT_CHUNK = 200;
  for (let k = 0; k < toInsertDeduped.length; k += INSERT_CHUNK) {
    const chunk = toInsertDeduped
      .slice(k, k + INSERT_CHUNK)
      .map(clinicRowToDb);
    await withPostgrestRetry(
      `insert ${k + 1}-${k + chunk.length}`,
      () => supabase.from(CLINICS_TABLE).insert(chunk)
    );
  }

  const UPDATE_PARALLEL = 25;
  for (let k = 0; k < toUpdateDeduped.length; k += UPDATE_PARALLEL) {
    const chunk = toUpdateDeduped.slice(k, k + UPDATE_PARALLEL);
    const maxAttempts = 5;
    for (let attempt = 1; attempt <= maxAttempts; attempt++) {
      const results = await Promise.all(
        chunk.map(({ pk, row }) =>
          supabase
            .from(CLINICS_TABLE)
            .update(clinicRowToDb(row))
            .eq(CLINICS_PK, pk)
        )
      );
      const firstErr = results.find((r) => r.error);
      if (!firstErr?.error) break;
      const msg = firstErr.error.message;
      if (!isTransientGatewayError(msg) || attempt === maxAttempts) {
        throw new Error(shortenErrorMessage(msg));
      }
      const waitMs = 2000 * attempt;
      console.warn(
        `update batch: transient error (attempt ${attempt}/${maxAttempts}), retry in ${waitMs}ms…`
      );
      await sleep(waitMs);
    }
  }
}

/** Match existing rows by google_maps_url; `id` is PK */
async function upsertBatchByGoogleMapsUrl(batch: ClinicRow[]) {
  const urls = [
    ...new Set(
      batch.map((r) => r.google_maps_url).filter((u) => Boolean(u && String(u).trim()))
    ),
  ];
  const idByUrl = new Map<string, Pk>();
  const URL_IN_CHUNK = 40;
  for (let j = 0; j < urls.length; j += URL_IN_CHUNK) {
    const slice = urls.slice(j, j + URL_IN_CHUNK);
    const { data } = await withPostgrestRetry(
      `select by google_maps_url (${j + 1}-${j + slice.length})`,
      () =>
        supabase
          .from(CLINICS_TABLE)
          .select(`${CLINICS_PK}, google_maps_url`)
          .in("google_maps_url", slice)
    );
    for (const e of data ?? []) {
      const rec = e as Record<string, unknown>;
      const url = rec.google_maps_url as string | undefined;
      const pkVal = rec[CLINICS_PK] as Pk | undefined;
      if (url && pkVal !== undefined && pkVal !== null) idByUrl.set(url, pkVal);
    }
  }

  const toInsert: ClinicRow[] = [];
  const toUpdate: { pk: Pk; row: ClinicRow }[] = [];
  for (const row of batch) {
    const u = row.google_maps_url;
    if (!u || !String(u).trim()) {
      toInsert.push(row);
      continue;
    }
    const pkVal = idByUrl.get(u);
    if (pkVal !== undefined) toUpdate.push({ pk: pkVal, row });
    else toInsert.push(row);
  }

  await flushInsertsAndUpdates(toInsert, toUpdate);
}

async function deleteClinicsNotInCsv(csvUrls: Set<string>) {
  const orphanPks: Pk[] = [];
  const PAGE = 1000;
  let from = 0;

  for (;;) {
    const { data } = await withPostgrestRetry(
      `select orphans page offset ${from}`,
      () =>
        supabase
          .from(CLINICS_TABLE)
          .select(`${CLINICS_PK}, google_maps_url`)
          .range(from, from + PAGE - 1)
    );
    if (!data?.length) break;

    for (const raw of data) {
      const row = raw as Record<string, unknown>;
      const url = row.google_maps_url as string | null | undefined;
      const pkVal = row[CLINICS_PK] as Pk | undefined;
      if (pkVal === undefined || pkVal === null) continue;
      if (!url || !csvUrls.has(url)) {
        orphanPks.push(pkVal);
      }
    }

    if (data.length < PAGE) break;
    from += PAGE;
  }

  if (!orphanPks.length) {
    console.log("Sync: no extra rows to remove (already matches CSV).");
    return;
  }

  for (let i = 0; i < orphanPks.length; i += DELETE_BATCH) {
    const batch = orphanPks.slice(i, i + DELETE_BATCH);
    await withPostgrestRetry(`delete orphans ${i + 1}-${i + batch.length}`, () =>
      supabase.from(CLINICS_TABLE).delete().in(CLINICS_PK, batch)
    );
  }

  console.log(`Sync: removed ${orphanPks.length} clinic(s) not present in CSV.`);
}

async function main() {
  const __dirname = path.dirname(fileURLToPath(import.meta.url));
  const csvPath = path.join(__dirname, "..", "dental_clinics_all.csv");
  const raw = fs.readFileSync(csvPath, "utf-8");

  const records = parse(raw, { columns: true, skip_empty_lines: true });

  const parsed: ClinicRow[] = (records as Record<string, string>[]).map((r) => ({
    name: r.name,
    address: r.address,
    phone_national: r.phone_national || null,
    phone_international: r.phone_international || null,
    website: r.website || null,
    rating: r.rating ? parseFloat(r.rating) : null,
    total_ratings: r.total_ratings ? parseInt(r.total_ratings) : null,
    business_status: r.business_status,
    google_maps_url: r.google_maps_url,
    opening_hours: r.opening_hours,
    category: r.category,
    region: r.region,
    suburb_town:
      (r as Record<string, string>)["suburb_town"] ??
      (r as Record<string, string>)["town"] ??
      "",
    city: ((r as Record<string, string>)["city"] || "NA").trim() || "NA",
    price: r.price !== "no_prices" ? r.price : null,
    description: (r as Record<string, string>)["description"] || null,
  }));

  const { rows, duplicateUrls } = dedupeRowsByGoogleMapsUrl(parsed);
  if (duplicateUrls > 0) {
    console.warn(
      `Duplicate google_maps_url in CSV: merged ${duplicateUrls} row(s); last row per URL wins.`
    );
  }

  const csvUrls = new Set(
    rows.map((r) => r.google_maps_url).filter((u): u is string => Boolean(u && String(u).trim()))
  );

  console.log(
    `Importing ${rows.length} rows (pk: ${CLINICS_PK}, suburb DB column: ${SUBURB_DB_COL}, match on google_maps_url)...`
  );

  let hadError = false;
  for (let i = 0; i < rows.length; i += 500) {
    const batch = rows.slice(i, i + 500);
    try {
      await upsertBatchByGoogleMapsUrl(batch);
      console.log(`Batch ${Math.floor(i / 500) + 1} done (${i + batch.length}/${rows.length})`);
    } catch (e) {
      hadError = true;
      console.error(
        `Batch ${Math.floor(i / 500) + 1} failed:`,
        e instanceof Error ? e.message : e
      );
    }
  }

  if (hadError) {
    console.error("Import aborted before sync: fix errors above, then re-run.");
    process.exit(1);
  }

  if (process.env.SKIP_ORPHAN_DELETE === "1") {
    console.log("SKIP_ORPHAN_DELETE=1: leaving rows that are not in the CSV.");
  } else {
    await deleteClinicsNotInCsv(csvUrls);
  }

  console.log("Import complete.");
}

main();
