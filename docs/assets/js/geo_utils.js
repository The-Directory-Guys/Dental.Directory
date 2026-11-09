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

// Resolves a typed suburb/town name to its known coordinates via SUBURB_COORDS
// (defined in suburb_coords.js, which must be loaded before this is called —
// not before this file, since the lookup only happens inside the function body).
function resolveSuburbRadiusInput(val) {
  const q = (val || '').trim();
  if (!q) return null;
  const coords = typeof SUBURB_COORDS !== 'undefined' ? SUBURB_COORDS : {};
  const key = Object.keys(coords).find(k => k.toLowerCase() === q.toLowerCase());
  return key ? { name: key, lat: coords[key][0], lng: coords[key][1] } : null;
}
