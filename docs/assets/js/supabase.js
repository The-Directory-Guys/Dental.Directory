// Supabase Configuration & Data Fetching
const SUPABASE_URL = 'https://ankyjpgcocsvvtyyymys.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFua3lqcGdjb2NzdnZ0eXl5bXlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4MTM1MTQsImV4cCI6MjA4OTM4OTUxNH0.SXxTLBdiNVSEDXy95yU0x0ctYFOjIby8hZbJ7B1LPK8';

// Parse opening hours from "Monday: 8:00 AM – 5:00 PM; Tuesday: ..." string into object
function parseOpeningHours(hoursStr) {
  if (!hoursStr) return null;
  const hours = {};
  // Normalize unicode characters from Google Maps
  const cleaned = hoursStr
    .replace(/\u202f/g, ' ')   // narrow no-break space
    .replace(/\u2009/g, '')    // thin space
    .replace(/[‐‑‒–—―−]/g, "-");  // all dashes -> hyphen
  
  cleaned.split(';').forEach(part => {
    const trimmed = part.trim();
    const colonIdx = trimmed.indexOf(':');
    if (colonIdx === -1) return;
    const day = trimmed.substring(0, colonIdx).trim();
    const time = trimmed.substring(colonIdx + 1).trim();
    if (day && time) {
      hours[day] = time;
    }
  });
  return Object.keys(hours).length > 0 ? hours : null;
}

// Convert parsed hours object {DayName: "8:00 AM – 5:00 PM"} into compact numeric format
// {dayNum: [openMinutes, closeMinutes] | null}  where 0=Sunday … 6=Saturday
function compactHours(hoursObj) {
  if (!hoursObj) return null;
  const DAY_MAP = { Sunday: 0, Monday: 1, Tuesday: 2, Wednesday: 3, Thursday: 4, Friday: 5, Saturday: 6 };
  const result = {};
  const toMin = (h, mn, ampm) => {
    let hour = parseInt(h, 10);
    if (ampm.toUpperCase() === 'PM' && hour !== 12) hour += 12;
    if (ampm.toUpperCase() === 'AM' && hour === 12) hour = 0;
    return hour * 60 + parseInt(mn, 10);
  };
  for (const [day, range] of Object.entries(hoursObj)) {
    const dayNum = DAY_MAP[day];
    if (dayNum === undefined) continue;
    if (!range || /closed/i.test(range)) { result[dayNum] = null; continue; }
    const m = range.match(/(\d+):(\d+)\s*(AM|PM)\s*[-]\s*(\d+):(\d+)\s*(AM|PM)/i);
    if (m) result[dayNum] = [toMin(m[1], m[2], m[3]), toMin(m[4], m[5], m[6])];
  }
  return Object.keys(result).length > 0 ? result : null;
}

// Generate a URL-friendly slug from a name
function generateSlug(name) {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim();
}

// Transform Supabase clinic data to match the format used by app.js
function transformClinic(clinic) {
  return {
    id: clinic.id,
    name: clinic.name || 'Unknown Clinic',
    slug: generateSlug(clinic.name || 'unknown'),
    suburb: clinic.suburb_town || clinic.town || '',
    city: clinic.city && clinic.city !== 'NA' ? clinic.city : '',
    region: clinic.region || '',
    address: clinic.address || '',
    phone: clinic.phone_national || clinic.phone_international || clinic.phone || '',
    email: clinic.email || '',
    website: clinic.website || '',
    rating: clinic.rating || 0,
    reviewCount: clinic.total_ratings || 0,
    services: clinic.services ? clinic.services.split(',').map(s => s.trim()) : ['General Dentistry'],
    pricing: [],  // Will be populated from scraped_prices table
    hasPricingFlag: clinic.price || null,  // 'full_prices', 'some_prices', or null
    pricesLastUpdated: clinic.prices_last_updated || null,
    description: clinic.description || '',
    hours: parseOpeningHours(clinic.opening_hours),
    hrs: compactHours(parseOpeningHours(clinic.opening_hours)),
    reviews: [],
    googleMapsUrl: clinic.google_maps_url || '',
    businessStatus: clinic.business_status || 'OPERATIONAL',
    photoUrl: clinic.photo_url || '',
    clinicPhotoUrl: clinic.clinic_photo_url || '',
    foundedYear: clinic.founded_year || null,
    facebookUrl: clinic.facebook_url || ''
  };
}

// Fetch pricing data for a list of clinic IDs from the scraped_prices table
// Handles batching (to avoid URL length limits) and pagination (Supabase 1000-row cap)
async function fetchClinicPricing(clinicIds) {
  if (!clinicIds || clinicIds.length === 0) return {};

  const pricingMap = {};
  const BATCH_SIZE = 50; // IDs per request to keep URLs manageable

  try {
    // Process clinic IDs in batches
    for (let i = 0; i < clinicIds.length; i += BATCH_SIZE) {
      const batch = clinicIds.slice(i, i + BATCH_SIZE);
      const idsParam = batch.map(id => `clinic_id.eq.${id}`).join(',');

      // Paginate within each batch (handle > 1000 pricing rows per batch)
      let offset = 0;
      let hasMore = true;

      while (hasMore) {
        const url = `${SUPABASE_URL}/rest/v1/scraped_prices?or=(${idsParam})&select=clinic_id,treatment,price_label,notes&order=clinic_id,id&limit=1000&offset=${offset}`;

        const response = await fetch(url, {
          headers: {
            'apikey': SUPABASE_ANON_KEY,
            'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
          }
        });

        if (!response.ok) {
          console.warn('Failed to fetch pricing batch:', response.status);
          break;
        }

        const data = await response.json();
        if (!Array.isArray(data) || data.length === 0) {
          hasMore = false;
          break;
        }

        // Group pricing by clinic_id
        data.forEach(row => {
          if (row.treatment === 'Scrape error' || row.price_label === 'Website could not be fetched') return;
          
          if (!pricingMap[row.clinic_id]) {
            pricingMap[row.clinic_id] = [];
          }
          pricingMap[row.clinic_id].push({
            service: row.treatment || 'Other',
            price: row.price_label || '—',
            notes: row.notes || ''
          });
        });

        // If we got fewer than 1000 rows, we've reached the end for this batch
        if (data.length < 1000) {
          hasMore = false;
        } else {
          offset += 1000;
        }
      }
    }

    console.log(`Fetched pricing for ${Object.keys(pricingMap).length} clinics`);
    return pricingMap;
  } catch (error) {
    console.error('Failed to fetch pricing:', error);
    return pricingMap; // Return whatever we collected so far
  }
}

// Fetch pricing for a single clinic (with pagination)
async function fetchSingleClinicPricing(clinicId) {
  try {
    const allPricing = [];
    let offset = 0;
    let hasMore = true;

    while (hasMore) {
      const url = `${SUPABASE_URL}/rest/v1/scraped_prices?clinic_id=eq.${clinicId}&select=treatment,price_label,notes&order=id&limit=1000&offset=${offset}`;
      
      const response = await fetch(url, {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
        }
      });

      if (!response.ok) return allPricing;

      const data = await response.json();
      if (!Array.isArray(data) || data.length === 0) break;

      data.forEach(row => {
        if (row.treatment === 'Scrape error' || row.price_label === 'Website could not be fetched') return;
        
        allPricing.push({
          service: row.treatment || 'Other',
          price: row.price_label || '—',
          notes: row.notes || ''
        });
      });

      hasMore = data.length === 1000;
      offset += 1000;
    }

    return allPricing;
  } catch (error) {
    console.error('Failed to fetch single clinic pricing:', error);
    return [];
  }
}

// Fetch clinics from Supabase for a given region
async function fetchClinics(region) {
  // Use build-time pre-fetched data if available (injected by build/prerender.py).
  // This skips the Supabase round-trip entirely, making the initial render
  // instant and ensuring Googlebot sees clinic names without needing JS execution.
  if (window.__DC_PREFETCH__) {
    const prefetch = window.__DC_PREFETCH__;
    const data = prefetch.clinics || [];
    const pricingById = prefetch.pricing || {};
    const clinics = data.map(transformClinic);
    clinics.forEach(clinic => {
      const rows = pricingById[String(clinic.id)];
      if (rows) clinic.pricing = rows;
    });
    return clinics;
  }

  try {
    const url = `${SUPABASE_URL}/rest/v1/dental_clinics?region=eq.${encodeURIComponent(region)}&business_status=eq.OPERATIONAL&order=total_ratings.desc.nullslast&limit=1000`;
    console.log('Fetching clinics from:', url, 'for region:', region);

    const response = await fetch(url, {
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
      }
    });

    if (!response.ok) {
      throw new Error(`Supabase error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();

    // Check if response is an error object instead of an array
    if (!Array.isArray(data)) {
      console.error('Supabase returned non-array response:', data);
      throw new Error('Invalid response from Supabase');
    }

    console.log(`Fetched ${data.length} clinics for ${region}`);
    const clinics = data.map(transformClinic);

    // Fetch pricing for ALL clinics in this region (not just flagged ones)
    const allClinicIds = data.map(c => c.id);
    if (allClinicIds.length > 0) {
      const pricingMap = await fetchClinicPricing(allClinicIds);
      clinics.forEach(clinic => {
        if (pricingMap[clinic.id]) {
          clinic.pricing = pricingMap[clinic.id];
        }
      });
      console.log(`Attached pricing to ${Object.keys(pricingMap).length} of ${clinics.length} clinics in ${region}`);
    }

    return clinics;
  } catch (error) {
    console.error('Failed to fetch clinics from Supabase:', error);
    // Fall back to static data if available
    if (typeof dentists !== 'undefined') {
      console.warn('⚠️ Falling back to static dentist data (Canterbury only)');
      return dentists;
    }
    return [];
  }
}

// Fetch amenity flags for a batch of clinic IDs, returns map of clinic_id → {flag: bool}
async function fetchAmenitiesForClinics(clinicIds) {
  if (!clinicIds || clinicIds.length === 0) return {};
  const map = {};
  const BATCH = 100;
  const FIELDS = 'clinic_id,dental_anxiety_friendly,wheelchair_accessible,online_booking,online_booking_note,saturday_evening_hours,same_day_emergency';
  try {
    for (let i = 0; i < clinicIds.length; i += BATCH) {
      const batch = clinicIds.slice(i, i + BATCH);
      const idsParam = batch.map(id => `clinic_id.eq.${id}`).join(',');
      const url = `${SUPABASE_URL}/rest/v1/clinic_amenities?or=(${idsParam})&select=${FIELDS}&limit=1000`;
      const response = await fetch(url, {
        headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` }
      });
      if (!response.ok) continue;
      const data = await response.json();
      data.forEach(row => { map[row.clinic_id] = row; });
    }
  } catch (e) {}
  return map;
}

// Normalise free-text language strings into canonical language names
const LANG_PATTERNS = [
  { key: 'Mandarin',     re: /mandarin|chinese/i },
  { key: 'Cantonese',    re: /cantonese/i },
  { key: 'Korean',       re: /korean/i },
  { key: 'Hindi',        re: /hindi/i },
  { key: 'Malay',        re: /malay|bahasa/i },
  { key: 'Arabic',       re: /arabic/i },
  { key: 'Japanese',     re: /japanese/i },
  { key: 'Spanish',      re: /spanish/i },
  { key: 'Filipino',     re: /tagalog|filipino/i },
  { key: 'Vietnamese',   re: /vietnamese/i },
  { key: 'Punjabi',      re: /punjabi/i },
  { key: 'Gujarati',     re: /gujarati/i },
  { key: 'Tamil',        re: /tamil/i },
  { key: 'Afrikaans',    re: /afrikaans/i },
  { key: 'Tongan',       re: /tongan/i },
  { key: 'Samoan',       re: /samoan/i },
  { key: 'Thai',         re: /thai/i },
  { key: 'Portuguese',   re: /portuguese/i },
  { key: 'French',       re: /french/i },
  { key: 'German',       re: /german/i },
  { key: 'Sign Language',re: /sign language/i },
];

function normaliseLangs(raw) {
  if (!raw) return [];
  const found = [];
  for (const { key, re } of LANG_PATTERNS) {
    if (re.test(raw) && !found.includes(key)) found.push(key);
  }
  return found;
}

// Fetch practitioners for a batch of clinic IDs, returns map of clinic_id → { specialties, names, languages, hasPhoto, hasBio, hasFemalePractitioner, hasMalePractitioner }
async function fetchPractitionersForClinics(clinicIds) {
  if (!clinicIds || clinicIds.length === 0) return {};
  const map = {};
  const BATCH = 100;
  try {
    for (let i = 0; i < clinicIds.length; i += BATCH) {
      const batch = clinicIds.slice(i, i + BATCH);
      const idsParam = batch.map(id => `clinic_id.eq.${id}`).join(',');
      const url = `${SUPABASE_URL}/rest/v1/clinic_practitioners?or=(${idsParam})&select=clinic_id,name,specialties,languages,photo_url,bio,gender&limit=1000`;
      const response = await fetch(url, {
        headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` }
      });
      if (!response.ok) continue;
      const data = await response.json();
      data.forEach(row => {
        if (!map[row.clinic_id]) map[row.clinic_id] = { specialties: [], names: [], languages: [], hasPhoto: false, hasBio: false, hasFemalePractitioner: false, hasMalePractitioner: false };
        if (row.name) {
          const cleanName = row.name.replace(/^Dr\.?\s*/i, '').trim();
          if (cleanName && !map[row.clinic_id].names.includes(cleanName)) {
            map[row.clinic_id].names.push(cleanName);
          }
        }
        if (row.specialties) {
          (Array.isArray(row.specialties) ? row.specialties : (() => { try { const p = JSON.parse(row.specialties); return Array.isArray(p) ? p : row.specialties.split(','); } catch(e) { return row.specialties.split(','); } })()).forEach(s => {
            const norm = String(s).trim().toLowerCase();
            if (norm && !map[row.clinic_id].specialties.includes(norm)) map[row.clinic_id].specialties.push(norm);
          });
        }
        normaliseLangs(row.languages).forEach(lang => {
          if (!map[row.clinic_id].languages.includes(lang)) map[row.clinic_id].languages.push(lang);
        });
        if (row.photo_url) map[row.clinic_id].hasPhoto = true;
        if (row.bio) map[row.clinic_id].hasBio = true;
        if (row.gender === 'F') map[row.clinic_id].hasFemalePractitioner = true;
        if (row.gender === 'M') map[row.clinic_id].hasMalePractitioner = true;
      });
    }
  } catch (e) {}
  return map;
}

// Fetch practitioners for a single clinic
async function fetchClinicPractitioners(clinicId) {
  try {
    const url = `${SUPABASE_URL}/rest/v1/clinic_practitioners?clinic_id=eq.${clinicId}&select=name,experience,specialties,bio,languages,photo_url&order=id`;
    const response = await fetch(url, {
      headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` }
    });
    if (!response.ok) return [];
    return await response.json();
  } catch (e) {
    return [];
  }
}

// Fetch amenities row for a single clinic
async function fetchClinicAmenities(clinicId) {
  try {
    const url = `${SUPABASE_URL}/rest/v1/clinic_amenities?clinic_id=eq.${clinicId}&select=parking_access,wheelchair_accessible,same_day_emergency,saturday_evening_hours,in_house_specialists,sedation_options,calming_amenities,dental_anxiety_friendly,online_booking,online_booking_note,payment_partners,membership_plans,kids_family_friendly,special_offers`;
    const response = await fetch(url, {
      headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` }
    });
    if (!response.ok) return null;
    const data = await response.json();
    return data.length > 0 ? data[0] : null;
  } catch (e) {
    return null;
  }
}

// Fetch a single clinic by ID (including its pricing)
async function fetchClinicById(id) {
  try {
    const url = `${SUPABASE_URL}/rest/v1/dental_clinics?id=eq.${id}`;
    
    const response = await fetch(url, {
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
      }
    });

    if (!response.ok) {
      throw new Error(`Supabase error: ${response.status}`);
    }

    const clinics = await response.json();
    if (clinics.length === 0) return null;
    const clinic = transformClinic(clinics[0]);

    // Fetch pricing for this specific clinic
    const pricing = await fetchSingleClinicPricing(id);
    clinic.pricing = pricing;

    // Fetch reviews for this specific clinic
    const reviews = await fetchSingleClinicReviews(id);
    clinic.reviews = reviews;

    // Fetch amenities for this specific clinic
    const amenities = await fetchClinicAmenities(id);
    clinic.amenities = amenities;

    // Fetch practitioners for this specific clinic
    const practitioners = await fetchClinicPractitioners(id);
    clinic.practitioners = practitioners;

    return clinic;
  } catch (error) {
    console.error('Failed to fetch clinic:', error);
    return null;
  }
}

// Parse "X days/weeks/months/years ago" into a comparable number (lower = more recent)
function parseDateTextToDaysAgo(s) {
  if (!s) return 9999;
  s = s.toLowerCase().trim();
  if (s === 'just now' || s === 'today') return 0;
  if (s === 'a day ago' || s === 'yesterday') return 1;
  if (s === 'a week ago') return 7;
  if (s === 'a month ago') return 30;
  if (s === 'a year ago') return 365;
  if (s === 'an hour ago' || s === 'a minute ago' || s === 'a second ago') return 0;
  const m = s.match(/^(\d+)\s+(second|minute|hour|day|week|month|year)s?\s+ago$/);
  if (!m) return 9999;
  const n = parseInt(m[1]);
  const mult = { second: 0, minute: 0, hour: 0, day: 1, week: 7, month: 30, year: 365 };
  return n * (mult[m[2]] ?? 1);
}

// Fetch reviews for a single clinic from Supabase google_reviews table
async function fetchSingleClinicReviews(clinicId) {
  try {
    const url = `${SUPABASE_URL}/rest/v1/google_reviews?clinic_id=eq.${clinicId}&order=id.desc`;
    const response = await fetch(url, {
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
      }
    });

    if (!response.ok) {
      console.warn('Failed to fetch reviews:', response.status);
      return [];
    }

    const data = await response.json();
    if (!Array.isArray(data)) return [];

    return data
      .map(r => ({
        name: r.author || 'Verified Patient',
        date: r.date_text || 'Recently',
        rating: r.rating || 5,
        text: r.snippet || '',
        daysAgo: parseDateTextToDaysAgo(r.date_text),
        curated: r.is_curated || false,
        curatedRating: r.is_curated_rating || false
      }))
      .sort((a, b) => a.daysAgo - b.daysAgo);
  } catch (error) {
    console.error('Failed to fetch single clinic reviews:', error);
    return [];
  }
}

// Fetch a specific set of clinics by ID array (used by the saved clinics page)
async function fetchClinicsByIds(ids) {
  if (!ids || ids.length === 0) return [];
  try {
    const url = `${SUPABASE_URL}/rest/v1/dental_clinics?id=in.(${ids.join(',')})&business_status=eq.OPERATIONAL`;
    const response = await fetch(url, {
      headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` }
    });
    if (!response.ok) throw new Error(`Supabase error: ${response.status}`);
    const data = await response.json();
    const clinics = data.map(transformClinic);
    const pricingMap = await fetchClinicPricing(data.map(c => c.id));
    clinics.forEach(clinic => { if (pricingMap[clinic.id]) clinic.pricing = pricingMap[clinic.id]; });
    return clinics;
  } catch (error) {
    console.error('Failed to fetch clinics by IDs:', error);
    return [];
  }
}

// Fetch all clinics (for homepage stats, etc.)
async function fetchAllClinics() {
  const PAGE = 1000;
  const all = [];
  try {
    for (let offset = 0; ; offset += PAGE) {
      const url = `${SUPABASE_URL}/rest/v1/dental_clinics?select=id,region,suburb_town,city&business_status=eq.OPERATIONAL&limit=${PAGE}&offset=${offset}`;
      const response = await fetch(url, {
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
        }
      });
      if (!response.ok) throw new Error(`Supabase error: ${response.status}`);
      const page = await response.json();
      all.push(...page);
      if (page.length < PAGE) break;
    }
    return all;
  } catch (error) {
    console.error('Failed to fetch all clinics:', error);
    return [];
  }
}
