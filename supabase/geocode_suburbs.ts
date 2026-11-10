/**
 * One-time script to geocode all suburb/town names from the CSV and output
 * a static JS lookup table for use in app.js.
 *
 * Some suburb/town names exist in more than one NZ region (e.g. "Richmond"
 * is both a Nelson & Tasman town and a Christchurch suburb). For those, a
 * plain name-only Nominatim query can only ever return one of them — so
 * this script detects any name used under more than one region in the CSV
 * and geocodes each region variant separately, with a region-qualified
 * query. The output stores those as a list of [lat, lng, region] candidates
 * instead of a single [lat, lng] pair; resolveSuburbRadiusInput (geo_utils.js)
 * picks the right one using the current page's region.
 *
 * Also guards against picking a wrong-type top hit (e.g. a river or road
 * sharing the suburb's name) by preferring a result whose Nominatim `type`
 * is an actual settlement (city/town/suburb/village/hamlet/...), falling
 * back to the top result — flagged in the output — only when none qualify.
 *
 * Respects Nominatim's 1 req/sec policy.
 * Usage: $env:NODE_OPTIONS="--use-system-ca"; web\node_modules\.bin\tsx.cmd supabase\geocode_suburbs.ts
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { parse } from 'csv-parse/sync';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const SETTLEMENT_TYPES = new Set([
  'city', 'town', 'suburb', 'village', 'hamlet', 'neighbourhood', 'borough', 'quarter',
]);

function sleep(ms: number) { return new Promise(r => setTimeout(r, ms)); }

interface GeocodeResult { lat: number; lng: number; isSettlement: boolean; displayName: string; }

async function geocode(query: string): Promise<GeocodeResult | null> {
  const url = `https://nominatim.openstreetmap.org/search?${new URLSearchParams({
    q: query, format: 'jsonv2', limit: '5', countrycodes: 'nz',
  })}`;
  try {
    const res = await fetch(url, { headers: { 'User-Agent': 'DentalCompareNZ/1.0' } });
    const data = await res.json() as Array<{ lat: string; lon: string; type: string; display_name: string }>;
    if (!data.length) return null;
    const best = data.find(d => SETTLEMENT_TYPES.has(d.type)) || data[0];
    return {
      lat: parseFloat(parseFloat(best.lat).toFixed(5)),
      lng: parseFloat(parseFloat(best.lon).toFixed(5)),
      isSettlement: SETTLEMENT_TYPES.has(best.type),
      displayName: best.display_name,
    };
  } catch (e) {
    console.error(`  Error geocoding "${query}":`, e);
  }
  return null;
}

async function main() {
  const csvPath = path.join(__dirname, '..', 'dental_clinics_all.csv');
  const raw = fs.readFileSync(csvPath, 'utf-8');
  const records = parse(raw, { columns: true, skip_empty_lines: true }) as Record<string, string>[];

  // suburb name -> set of regions it appears under
  const regionsByName = new Map<string, Set<string>>();
  for (const row of records) {
    const suburb = (row['suburb_town'] ?? '').trim();
    const region = (row['region'] ?? '').trim();
    if (!suburb || !region) continue;
    if (!regionsByName.has(suburb)) regionsByName.set(suburb, new Set());
    regionsByName.get(suburb)!.add(region);
  }

  // Build the flat list of (name, region|null) geocode jobs — null region
  // means "unambiguous, use a plain name query"; one job per region otherwise.
  const jobs: Array<{ name: string; region: string | null }> = [];
  for (const [name, regions] of regionsByName) {
    if (regions.size <= 1) jobs.push({ name, region: null });
    else for (const region of regions) jobs.push({ name, region });
  }
  jobs.sort((a, b) => a.name.localeCompare(b.name) || (a.region || '').localeCompare(b.region || ''));

  console.log(`Geocoding ${jobs.length} suburb/region jobs (1/sec)…`);

  // Unambiguous names -> single [lat,lng]; ambiguous names -> list of [lat,lng,region]
  const singleResults: Record<string, [number, number]> = {};
  const multiResults: Record<string, Array<[number, number, string]>> = {};
  const failed: string[] = [];
  const lowConfidence: string[] = [];

  for (let i = 0; i < jobs.length; i++) {
    const { name, region } = jobs[i];
    const query = region ? `${name}, ${region}, New Zealand` : `${name}, New Zealand`;
    process.stdout.write(`[${i + 1}/${jobs.length}] ${query}… `);
    const r = await geocode(query);
    if (!r) {
      failed.push(query);
      console.log('NOT FOUND');
    } else {
      if (!r.isSettlement) lowConfidence.push(`${query} -> ${r.displayName}`);
      if (region) {
        if (!multiResults[name]) multiResults[name] = [];
        multiResults[name].push([r.lat, r.lng, region]);
      } else {
        singleResults[name] = [r.lat, r.lng];
      }
      console.log(`${r.lat}, ${r.lng}${r.isSettlement ? '' : '  (NOT a settlement type — check manually)'}`);
    }
    if (i < jobs.length - 1) await sleep(1100);
  }

  // Write JS lookup table
  const singleLines = Object.entries(singleResults)
    .map(([name, [lat, lng]]) => ({ name, line: `  ${JSON.stringify(name)}: [${lat}, ${lng}]` }));
  const multiLines = Object.entries(multiResults)
    .map(([name, candidates]) => ({
      name,
      line: `  ${JSON.stringify(name)}: [${candidates.map(([lat, lng, region]) => `[${lat}, ${lng}, ${JSON.stringify(region)}]`).join(', ')}]`,
    }));
  const lines = [...singleLines, ...multiLines]
    .sort((a, b) => a.name.localeCompare(b.name))
    .map(e => e.line);
  const results = { ...singleResults, ...multiResults };

  const output = `// Auto-generated by geocode_suburbs.ts — do not edit manually
const SUBURB_COORDS = {
${lines.join(',\n')}
};
`;

  const outPath = path.join(__dirname, '..', 'docs', 'assets', 'js', 'suburb_coords.js');
  fs.writeFileSync(outPath, output, 'utf-8');
  console.log(`\nWritten to ${outPath}`);
  console.log(`Geocoded: ${Object.keys(results).length} names (${jobs.length} queries), Failed: ${failed.length}`);
  if (failed.length) console.log('Failed:', failed.join(', '));
  if (lowConfidence.length) {
    console.log(`\n${lowConfidence.length} result(s) were not a settlement type — verify manually:`);
    lowConfidence.forEach(l => console.log('  ' + l));
  }
}

main();
