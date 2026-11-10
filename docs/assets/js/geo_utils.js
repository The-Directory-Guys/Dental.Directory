// Shared geo helpers used by both the region/city listing pages (app.js) and nearby.html.
// Kept in one place so a fix here (e.g. to how a suburb name resolves to coordinates)
// doesn't have to be duplicated and re-applied in both files.

function haversineKm(lat1, lng1, lat2, lng2) {
  const R = 6371;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLng = (lng2 - lng1) * Math.PI / 180;
  const a = Math.sin(dLat / 2) ** 2 +
            Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * Math.sin(dLng / 2) ** 2;
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

function normalizeRegionName(s) {
  return (s || '').toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').trim();
}

// Resolves a typed suburb/town name to its known coordinates via SUBURB_COORDS
// (defined in suburb_coords.js, which must be loaded before this is called —
// not before this file, since the lookup only happens inside the function body).
//
// A handful of suburb/town names exist in more than one NZ region (e.g.
// "Richmond" is both a Nelson & Tasman town and a Christchurch suburb), so
// SUBURB_COORDS stores those as a list of [lat, lng, region] candidates
// instead of a single [lat, lng] pair. `regionHint` (the page's own region,
// e.g. from #dentist-grid's data-region) picks the right candidate; without
// a hint, or without a match, the first candidate is used.
function resolveSuburbRadiusInput(val, regionHint) {
  const q = (val || '').trim();
  if (!q) return null;
  const coords = typeof SUBURB_COORDS !== 'undefined' ? SUBURB_COORDS : {};
  const key = Object.keys(coords).find(k => k.toLowerCase() === q.toLowerCase());
  if (!key) return null;

  const entry = coords[key];
  if (typeof entry[0] === 'number') {
    return { name: key, lat: entry[0], lng: entry[1] };
  }

  // Ambiguous name: entry is a list of [lat, lng, region] candidates.
  const hint = normalizeRegionName(regionHint);
  const match = (hint && entry.find(c => {
    const region = normalizeRegionName(c[2]);
    return region === hint || region.includes(hint) || hint.includes(region);
  })) || entry[0];
  return { name: key, lat: match[0], lng: match[1] };
}
