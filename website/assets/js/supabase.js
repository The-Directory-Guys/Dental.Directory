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
    .replace(/\u2013/g, '–');  // en dash
  
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
    suburb: clinic.town || 'Unknown',
    address: clinic.address || '',
    phone: clinic.phone || '',
    email: '',
    website: clinic.website || '',
    rating: clinic.rating || 0,
    reviewCount: clinic.total_ratings || 0,
    services: ['General Dentistry'],  // Default — DB doesn't have services yet
    pricing: (clinic.price && !isNaN(parseFloat(clinic.price))) ? [{ service: 'General Checkup', price: `$${clinic.price}` }] : [],
    description: '',
    hours: parseOpeningHours(clinic.opening_hours),
    reviews: [],
    googleMapsUrl: clinic.google_maps_url || '',
    businessStatus: clinic.business_status || 'OPERATIONAL'
  };
}

// Fetch clinics from Supabase for a given region
async function fetchClinics(region) {
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
    return data.map(transformClinic);
  } catch (error) {
    console.error('Failed to fetch clinics from Supabase:', error);
    // Fall back to static data if available
    if (typeof dentists !== 'undefined') {
      console.warn('⚠️ Falling back to static dentist data (Christchurch only)');
      return dentists;
    }
    return [];
  }
}

// Fetch a single clinic by ID
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
    return transformClinic(clinics[0]);
  } catch (error) {
    console.error('Failed to fetch clinic:', error);
    return null;
  }
}

// Fetch all clinics (for homepage stats, etc.)
async function fetchAllClinics() {
  try {
    const url = `${SUPABASE_URL}/rest/v1/dental_clinics?select=id,region,town&business_status=eq.OPERATIONAL&limit=2000`;
    
    const response = await fetch(url, {
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_ANON_KEY}`
      }
    });

    if (!response.ok) {
      throw new Error(`Supabase error: ${response.status}`);
    }

    return await response.json();
  } catch (error) {
    console.error('Failed to fetch all clinics:', error);
    return [];
  }
}
