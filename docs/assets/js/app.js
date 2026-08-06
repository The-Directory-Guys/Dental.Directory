// Dental Compare — App Logic

// Treatment synonym map — keys are user search terms, values are { service, priceType }
// priceType: 'checkup' | 'hygienist' | null (null = no price-boost sort)
const TREATMENT_MAP = {
  // General Dentistry / checkup
  'checkup':              { service: 'General Dentistry', priceType: 'checkup' },
  'checkups':             { service: 'General Dentistry', priceType: 'checkup' },
  'check-up':             { service: 'General Dentistry', priceType: 'checkup' },
  'check up':             { service: 'General Dentistry', priceType: 'checkup' },
  'exam':                 { service: 'General Dentistry', priceType: 'checkup' },
  'examination':          { service: 'General Dentistry', priceType: 'checkup' },
  'dental exam':          { service: 'General Dentistry', priceType: 'checkup' },
  'consult':              { service: 'General Dentistry', priceType: 'checkup' },
  'consultation':         { service: 'General Dentistry', priceType: 'checkup' },
  'general':              { service: 'General Dentistry', priceType: null },
  'general dentist':      { service: 'General Dentistry', priceType: null },
  'general dentistry':    { service: 'General Dentistry', priceType: null },
  'filling':              { service: 'General Dentistry', priceType: null },
  'fillings':             { service: 'General Dentistry', priceType: null },
  'crown':                { service: 'General Dentistry', priceType: null },
  'crowns':               { service: 'General Dentistry', priceType: null },
  'extraction':           { service: 'General Dentistry', priceType: null },
  'extractions':          { service: 'General Dentistry', priceType: null },
  'tooth extraction':     { service: 'General Dentistry', priceType: null },
  'wisdom tooth':         { service: 'General Dentistry', priceType: null },
  'wisdom teeth':         { service: 'General Dentistry', priceType: null },
  // Hygienist — no service filter; sort all clinics by scale & clean price
  'hygienist':            { service: null, priceType: 'hygienist' },
  'hygienists':           { service: null, priceType: 'hygienist' },
  'hygiene':              { service: null, priceType: 'hygienist' },
  'clean':                { service: null, priceType: 'hygienist' },
  'cleaning':             { service: null, priceType: 'hygienist' },
  'dental clean':         { service: null, priceType: 'hygienist' },
  'dental cleaning':      { service: null, priceType: 'hygienist' },
  'scale and polish':     { service: null, priceType: 'hygienist' },
  'scale and clean':      { service: null, priceType: 'hygienist' },
  'scale & polish':       { service: null, priceType: 'hygienist' },
  'scale & clean':        { service: null, priceType: 'hygienist' },
  // Orthodontics
  'braces':               { service: 'Orthodontics', priceType: null },
  'brace':                { service: 'Orthodontics', priceType: null },
  'aligners':             { service: 'Orthodontics', priceType: null },
  'aligner':              { service: 'Orthodontics', priceType: null },
  'invisalign':           { service: 'Orthodontics', priceType: null },
  'orthodontist':         { service: 'Orthodontics', priceType: null },
  'orthodontists':        { service: 'Orthodontics', priceType: null },
  'orthodontic':          { service: 'Orthodontics', priceType: null },
  'orthodontics':         { service: 'Orthodontics', priceType: null },
  // Dental Implants
  'implant':              { service: 'Dental Implants', priceType: null },
  'implants':             { service: 'Dental Implants', priceType: null },
  'dental implant':       { service: 'Dental Implants', priceType: null },
  'dental implants':      { service: 'Dental Implants', priceType: null },
  // Teeth Whitening
  'whitening':            { service: 'Teeth Whitening', priceType: null },
  'teeth whitening':      { service: 'Teeth Whitening', priceType: null },
  'tooth whitening':      { service: 'Teeth Whitening', priceType: null },
  'bleaching':            { service: 'Teeth Whitening', priceType: null },
  // Emergency
  'emergency':            { service: 'Emergency', priceType: null },
  'emergency dentist':    { service: 'Emergency', priceType: null },
  'emergency dentistry':  { service: 'Emergency', priceType: null },
  'urgent':               { service: 'Emergency', priceType: null },
  // Dentures
  'denture':              { service: 'Dentures', priceType: null },
  'dentures':             { service: 'Dentures', priceType: null },
  // Endodontics
  'root canal':           { service: 'Endodontics', priceType: null },
  'root canals':          { service: 'Endodontics', priceType: null },
  'endodontics':          { service: 'Endodontics', priceType: null },
  'endodontist':          { service: 'Endodontics', priceType: null },
  // Oral Surgery
  'oral surgery':         { service: 'Oral Surgery', priceType: null },
  'oral surgeon':         { service: 'Oral Surgery', priceType: null },
  'oral surgeons':        { service: 'Oral Surgery', priceType: null },
  'maxillofacial':        { service: 'Oral Surgery', priceType: null },
  // Periodontal Care
  'gum disease':          { service: 'Periodontal Care', priceType: null },
  'gum treatment':        { service: 'Periodontal Care', priceType: null },
  'periodontist':         { service: 'Periodontal Care', priceType: null },
  'periodontics':         { service: 'Periodontal Care', priceType: null },
  'periodontal':          { service: 'Periodontal Care', priceType: null },
  // Cosmetic
  'cosmetic':             { service: 'Cosmetic', priceType: null },
  'veneers':              { service: 'Cosmetic', priceType: null },
  'veneer':               { service: 'Cosmetic', priceType: null },
  'cosmetic dentist':     { service: 'Cosmetic', priceType: null },
  'cosmetic dentistry':   { service: 'Cosmetic', priceType: null },
};

// Exact match first; fall back to prefix match on any key (min 3 chars typed)
function matchTreatment(raw) {
  const q = raw.trim().toLowerCase();
  if (!q) return null;
  if (TREATMENT_MAP[q]) return TREATMENT_MAP[q];
  if (q.length >= 3) {
    const key = Object.keys(TREATMENT_MAP).find(k => k.startsWith(q));
    if (key) return TREATMENT_MAP[key];
  }
  return null;
}

(function () {
  'use strict';

  // ===== Mobile Nav Toggle =====
  const menuToggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.nav');
  if (menuToggle && nav) {
    menuToggle.addEventListener('click', () => {
      nav.classList.toggle('active');
    });
  }

  // ===== Shared Helpers =====
  function starsHTML(rating) {
    if (!rating) return '<span class="empty">★</span>'.repeat(5);
    const full = Math.round(rating);
    const empty = 5 - full;
    let html = '';
    for (let i = 0; i < full; i++) html += '<span>★</span>';
    for (let i = 0; i < empty; i++) html += '<span class="empty">★</span>';
    return html;
  }

  function getCheckupPrice(d) {
    if (!d.pricing || d.pricing.length === 0) return null;
    const checkup = d.pricing.find(p => {
      const s = p.service.toLowerCase();
      return s.includes('checkup') || s.includes('check-up') || s.includes('exam') ||
             s.includes('consult') || s.includes('assessment') || s.includes('new patient') ||
             s.includes('initial') || s.includes('comprehensive') || s.includes('oral health');
    });
    if (!checkup) return null;
    const match = checkup.price.replace(/,/g, '').match(/\$(\d+)/);
    return match ? parseInt(match[1], 10) : null;
  }

  // Checkup price averages loaded lazily from price-averages.json
  let _cityAverages = null;
  let _cityAveragesPromise = null;
  function loadCityAverages() {
    if (_cityAverages) return Promise.resolve(_cityAverages);
    if (!_cityAveragesPromise) {
      _cityAveragesPromise = fetch('assets/data/price-averages.json')
        .then(r => r.json())
        .then(data => { _cityAverages = data; return data; })
        .catch(() => { _cityAverages = {}; return {}; });
    }
    return _cityAveragesPromise;
  }

  // Clinic experience map loaded lazily from clinic-experience.json
  let _experienceMap = null;
  let _experienceMapPromise = null;
  function loadExperienceMap() {
    if (_experienceMap) return Promise.resolve(_experienceMap);
    if (!_experienceMapPromise) {
      _experienceMapPromise = fetch('assets/data/clinic-experience.json')
        .then(r => r.json())
        .then(data => { _experienceMap = data; return data; })
        .catch(() => { _experienceMap = {}; return {}; });
    }
    return _experienceMapPromise;
  }

  // Hygienist price averages loaded lazily from hygienist-averages.json
  let _hygienistAverages = null;
  let _hygienistAveragesPromise = null;
  function loadHygienistAverages() {
    if (_hygienistAverages) return Promise.resolve(_hygienistAverages);
    if (!_hygienistAveragesPromise) {
      _hygienistAveragesPromise = fetch('assets/data/hygienist-averages.json')
        .then(r => r.json())
        .then(data => { _hygienistAverages = data; return data; })
        .catch(() => { _hygienistAverages = {}; return {}; });
    }
    return _hygienistAveragesPromise;
  }

  function _cmpEntry(price, entry, label) {
    if (!entry || entry.clinics < 2) return null;
    const diff = price - entry.avg;
    const pct = Math.round(Math.abs(diff) / entry.avg * 100);
    if (pct < 5) return null;
    const dir = diff < 0 ? 'below' : 'above';
    return { dir, text: `${pct}% ${dir} ${label} avg (${entry.clinics} clinics)` };
  }

  function getPriceComparisons(price, city, region) {
    if (!_cityAverages || !price) return { city: null, region: null };
    const cityEntry = city ? (_cityAverages.cities || {})[city] : null;
    const regionEntry = region ? (_cityAverages.regions || {})[region] : null;
    return {
      city: _cmpEntry(price, cityEntry, city),
      region: _cmpEntry(price, regionEntry, region),
    };
  }

  function getHygienistComparisons(price, city, region) {
    if (!_hygienistAverages || !price) return { city: null, region: null };
    const cityEntry = city ? (_hygienistAverages.cities || {})[city] : null;
    const regionEntry = region ? (_hygienistAverages.regions || {})[region] : null;
    return {
      city: _cmpEntry(price, cityEntry, city),
      region: _cmpEntry(price, regionEntry, region),
    };
  }


  function getHygienistPrice(d) {
    if (!d.pricing || d.pricing.length === 0) return null;
    const match = d.pricing.find(p => {
      const s = p.service.toLowerCase();
      return s.includes('hygienist') || s.includes('hygiene') ||
             (s.includes('scale') && (s.includes('polish') || s.includes('clean')));
    });
    if (!match) return null;
    const m = match.price.replace(/,/g, '').match(/\$(\d+)/);
    return m ? parseInt(m[1], 10) : null;
  }

  const AMENITY_CHECKS = {
    saturday_hours: d => !!(d.hrs && Array.isArray(d.hrs['6'])),
    sunday_hours:   d => !!(d.hrs && Array.isArray(d.hrs['0'])),
    evening_hours:  d => !!(d.hrs && Object.values(d.hrs).some(v => Array.isArray(v) && v[1] > 1020)),
  };

  function checkAmenity(key, d) {
    if (AMENITY_CHECKS[key]) return AMENITY_CHECKS[key](d);
    return !!(d.amenityFlags && d.amenityFlags[key] === true);
  }

  function isOpenNow(d) {
    if (!d.hrs) return null;
    const now = new Date(new Date().toLocaleString('en-US', { timeZone: 'Pacific/Auckland' }));
    const range = d.hrs[String(now.getDay())];
    if (range === undefined) return null;
    if (range === null) return false;
    const cur = now.getHours() * 60 + now.getMinutes();
    return cur >= range[0] && cur < range[1];
  }

  function getFavourites() {
    try { return new Set(JSON.parse(localStorage.getItem('dc_favourites') || '[]')); }
    catch { return new Set(); }
  }
  function saveFavourites(favSet) {
    try { localStorage.setItem('dc_favourites', JSON.stringify([...favSet])); }
    catch {}
  }

  // ===== Compare feature =====
  const COMPARE_MAX = 4;
  function getCompare() {
    try { return JSON.parse(localStorage.getItem('dc_compare') || '[]'); }
    catch { return []; }
  }
  function saveCompare(list) {
    try { localStorage.setItem('dc_compare', JSON.stringify(list)); } catch {}
  }
  function compareIds() { return new Set(getCompare().map(c => c.id)); }

  function renderCompareTray() {
    const list = getCompare();
    let tray = document.getElementById('compare-tray');
    if (list.length === 0) {
      if (tray) tray.remove();
      document.body.classList.remove('compare-tray-open');
      return;
    }
    document.body.classList.add('compare-tray-open');
    if (!tray) {
      tray = document.createElement('div');
      tray.id = 'compare-tray';
      tray.className = 'compare-tray';
      document.body.appendChild(tray);
    }
    tray.innerHTML = `
      <div class="compare-tray__inner">
        <div class="compare-tray__info">
          <span class="compare-tray__count">${list.length} of ${COMPARE_MAX} selected</span>
          <span class="compare-tray__names">${list.map(c => c.name).join('  ·  ')}</span>
        </div>
        <div class="compare-tray__actions">
          <button class="compare-tray__clear" id="compare-clear">Clear</button>
          <a href="compare.html" class="btn btn--primary">Compare now →</a>
        </div>
      </div>`;
    tray.querySelector('#compare-clear').addEventListener('click', () => {
      saveCompare([]);
      document.querySelectorAll('.cmp-btn--active').forEach(b => {
        b.classList.remove('cmp-btn--active');
        b.innerHTML = '⚖ Compare';
        b.title = 'Add to comparison';
      });
      renderCompareTray();
    });
  }
  renderCompareTray();

  // ===== Listings Page Logic =====
  const dentistGrid = document.getElementById('dentist-grid');
  const resultsCount = document.getElementById('results-count');

  if (dentistGrid) {
    // Show loading state
    dentistGrid.innerHTML = `
      <div class="no-results">
        <div class="no-results__icon">⏳</div>
        <h3>Loading dentists...</h3>
        <p>Fetching the latest data.</p>
      </div>
    `;

    // Determine data source and initialize
    initListings();
  }

  const SUBURB_FILTERS = {
    'christchurch-city': new Set([
      'Christchurch Central','Papanui','Riccarton','Strowan','Merivale','St Albans',
      'Sydenham','Bishopdale','Linwood','Shirley','Spreydon','Hornby','Burnside',
      'Woolston','Avonhead','Hillmorton','Cashmere','Sockburn','Halswell',
      'Bryndwr','Richmond','Redwood','Riccarton (Upper)','Somerfield','Hoon Hay',
      'Phillipstown','Ferrymead','Casebrook','Northcote','Ilam','Waltham','Addington',
      'North New Brighton','Redcliffs','Fendalton','Yaldhurst',
      'Kaiapoi','Prebbleton','Rangiora','Rolleston','Lincoln'
    ]),
    'wider-canterbury': new Set([
      'Ashburton','Timaru','Darfield','Geraldine','Kaikōura','Oxford'
    ]),
    'hamilton-city': new Set([
      'Hamilton Central','Hamilton East','Claudelands','Chartwell','Hillcrest','Pukete',
      'Nawton','Fairfield','Whitiora','Hamilton Lake','Te Rapa','Rototuna North','Rototuna',
      'Frankton','Dinsdale','Beerescourt','Parkwood','Melville','Flagstaff'
    ]),
    'wider-waikato': new Set([
      'Cambridge','Taupo','Thames','Te Awamutu','Morrinsville','Tokoroa','Waihi',
      'Pirongia','Leamington','Paeroa','Huntly','Coromandel Town','Matamata',
      'Raglan','Te Aroha','Turangi','Whitianga'
    ]),
    'tauranga-city': new Set([
      'Tauranga','Papamoa Beach','Tauranga South','Gate Pa','Bethlehem','Greerton',
      'Pyes Pa','Otūmoetai','Papamoa','Mount Maunganui','Tauriko','Hairini'
    ]),
    'wider-bop': new Set([
      'Rotorua','Whakatāne','Kawerau','Ōpōtiki','Katikati','Omokoroa','Te Puke'
    ]),
    'dunedin-city': new Set([
      'Dunedin Central','Dunedin North','Mosgiel','Green Island','Roslyn','Wakari',
      'Musselburgh','North East Valley','Kaikorai','Mornington','South Dunedin','Maori Hill'
    ]),
    'wider-otago': new Set([
      'Queenstown','Frankton','Wānaka','Alexandra','Oamaru','Cromwell',
      'Balclutha','Ranfurly','Milton','Palmerston'
    ])
  };

  // Shorter curated town list for the hover tooltip, used when a card's
  // full SUBURB_FILTERS set is too long to display nicely. Filtering and
  // counts still use the full set above — this only affects tooltip text.
  const TOOLTIP_TOWN_OVERRIDES = {
    'christchurch-city': ['Christchurch', 'Kaiapoi', 'Lincoln', 'Prebbleton', 'Rangiora', 'Rolleston'],
    'dunedin-city': ['Dunedin', 'Mosgiel'],
    'hamilton-city': ['Hamilton'],
    'Wellington': ['Wellington', 'Lower Hutt', 'Upper Hutt', 'Porirua', 'Paraparaumu', 'Waikanae'],
    'tauranga-city': ['Tauranga', 'Mount Maunganui', 'Papamoa']
  };

  async function initListings() {
    let allDentists = [];
    const savedMode = dentistGrid.dataset.mode === 'saved';
    const region = dentistGrid.dataset.region || 'Canterbury';
    const displayLocation = dentistGrid.dataset.city || region;

    if (savedMode) {
      const ids = [...getFavourites()];
      if (ids.length === 0) {
        dentistGrid.innerHTML = `
          <div class="no-results">
            <div class="no-results__icon">♥</div>
            <p class="no-results__desc">No saved clinics yet. Browse a region and click ♥ on any card to save a clinic.</p>
            <a href="/" class="btn btn--primary" style="margin-top:1rem;">Browse regions</a>
          </div>
        `;
        if (resultsCount) resultsCount.textContent = '';
        return;
      }
      if (typeof fetchClinicsByIds === 'function') {
        allDentists = await fetchClinicsByIds(ids);
      }
    } else {
      // Try Supabase first, fall back to static data
      if (typeof fetchClinics === 'function') {
        allDentists = await fetchClinics(region);
      }
      if (allDentists.length === 0 && typeof dentists !== 'undefined') {
        allDentists = dentists;
      }
      // Apply suburb filter if page specifies one
      const suburbFilterKey = dentistGrid.dataset.suburbFilter;
      if (suburbFilterKey && SUBURB_FILTERS[suburbFilterKey]) {
        const allowed = SUBURB_FILTERS[suburbFilterKey];
        allDentists = allDentists.filter(d => allowed.has(d.suburb));
      }
    }

    if (allDentists.length === 0) {
      dentistGrid.innerHTML = `
        <div class="no-results">
          <div class="no-results__icon">😕</div>
          <h3>Could not load dentists</h3>
          <p>Please check your connection and try again.</p>
        </div>
      `;
      return;
    }

    // Load price averages in parallel with other fetches
    loadCityAverages();
    loadHygienistAverages();

    // Fetch and attach practitioner specialties + amenity flags for the whole region
    if (!savedMode) {
      const ids = allDentists.map(d => d.id).filter(Boolean);
      const [specMap, amenMap, expMap] = await Promise.all([
        fetchPractitionersForClinics(ids),
        fetchAmenitiesForClinics(ids),
        loadExperienceMap(),
      ]);
      allDentists.forEach(d => {
        if (d.id && specMap[d.id]) {
          d.practitionerSpecialties = specMap[d.id].specialties;
          d.practitionerNames = specMap[d.id].names;
          d.practitionerLanguages = specMap[d.id].languages;
        }
        if (d.id && amenMap[d.id]) d.amenityFlags = amenMap[d.id];
        if (d.id && expMap[d.id]) d.maxExperience = expMap[d.id];
      });
    }

    // Setup filtering & rendering
    let activeSuburbs = [];
    let activeLanguages = [];
    let activeServices = [];
    let minRating = 0;
    let searchQuery = '';
    let sortBy = 'reviews';
    let maxPrice = Infinity;
    let maxHygienistPrice = Infinity;
    let activeTreatmentPriceType = null;
    let activeSpecialties = [];
    let activeAmenities = [];
    let minExperience = 0;
    let showFavouritesOnly = false;
    let showOpenOnly = false;
    let _favs = getFavourites();
    let _cmpIds = compareIds();

    function cardHTML(d) {
      const initials = d.name.split(' ').filter(w => w.length > 0).map(w => w[0]).join('').slice(0, 2).toUpperCase();
      const orderedServices = d.services.includes('Teen Dental')
        ? ['Teen Dental', ...d.services.filter(s => s !== 'Teen Dental')]
        : d.services;
      const servicePills = orderedServices.slice(0, 4).map(s =>
        `<span class="pill pill--sm" data-service="${s}" role="button" tabindex="0" style="cursor:pointer;">${s === 'Hygienist' ? 'Hygienist: Scale & clean' : s}</span>`
      ).join('');

      let pricingPreview = '';
      if (d.pricing && d.pricing.length > 0) {
        const checkupPrice = getCheckupPrice(d);
        const hygPrice = getHygienistPrice(d);
        const parts = [];
        if (checkupPrice) {
          const cmps = getPriceComparisons(checkupPrice, d.city, d.region);
          const cmp = cmps.city || cmps.region;
          const cmpBadge = cmp
            ? ` <span class="price-cmp price-cmp--${cmp.dir}">${cmp.text}</span>`
            : '';
          parts.push(`Checkup from $${checkupPrice}${cmpBadge}`);
        }
        if (hygPrice) {
          const hCmps = getHygienistComparisons(hygPrice, d.city, d.region);
          const hCmp = hCmps.city || hCmps.region;
          const hBadge = hCmp ? ` <span class="price-cmp price-cmp--${hCmp.dir}">${hCmp.text}</span>` : '';
          parts.push(`Hygienist: scale &amp; clean from $${hygPrice}${hBadge}`);
        }
        if (parts.length > 0) {
          pricingPreview = `<div class="pricing-summary">${parts.map(p => `<div class="pricing-line">💰 ${p}</div>`).join('')}</div>`;
        } else if (d.pricing.some(p => /\$\d/.test(p.price))) {
          pricingPreview = `<div class="pricing-summary pricing-summary--muted">💰 Pricing available</div>`;
        } else {
          pricingPreview = `<div class="pricing-summary pricing-summary--muted">No prices listed</div>`;
        }
      } else {
        pricingPreview = `<div class="pricing-summary pricing-summary--muted">No prices listed</div>`;
      }

      const ratingDisplay = d.rating ? `<span class="stars">${starsHTML(d.rating)}</span> <strong>${d.rating}</strong>` : '<span style="color:var(--clr-gray-400)">No rating yet</span>';
      const reviewText = d.reviewCount ? `💬 ${d.reviewCount} review${d.reviewCount === 1 ? '' : 's'}` : '';
      const descText = d.description
        ? d.description.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim().slice(0, 200)
        : '';
      const phoneText = d.phone ? `<a href="tel:${d.phone.replace(/\\s/g, '')}" style="text-decoration:none; color:inherit;">📞 ${d.phone}</a>` : '';
      const emailText = d.email ? `<a href="mailto:${d.email}" style="text-decoration:none; color:inherit; margin-left:1rem;">✉️ Email</a>` : '';

      const openStatus = isOpenNow(d);
      const openBadge = openStatus === true
        ? '<span class="badge badge--open">🟢 Open now</span>'
        : openStatus === false
        ? '<span class="badge badge--closed">🔴 Closed</span>'
        : '';

      const isFav = !!d.id && _favs.has(d.id);
      const favBtn = d.id ? `<button class="fav-btn${isFav ? ' fav-btn--active' : ''}" data-fav-id="${d.id}" aria-label="${isFav ? 'Remove from saved' : 'Save clinic'}" title="${isFav ? 'Remove from saved' : 'Save clinic'}">♥</button>` : '';
      const inCmp = !!d.id && _cmpIds.has(d.id);
      const cmpBtn = d.id ? `<button class="cmp-btn${inCmp ? ' cmp-btn--active' : ''}" data-cmp-id="${d.id}" aria-label="${inCmp ? 'Remove from comparison' : 'Add to comparison'}" title="${inCmp ? 'Remove from comparison' : 'Add to comparison'}">${inCmp ? '✓ Added' : '⚖ Compare'}</button>` : '';

      // Use id for Supabase records, slug for static
      const profileLink = d.id ? `dentist.html?id=${d.id}&region=${encodeURIComponent(d.region || '')}` : `dentist.html?slug=${d.slug}&region=${encodeURIComponent(d.region || '')}`;

      return `
        <article class="dentist-card" data-suburb="${d.suburb}" data-rating="${d.rating || 0}" data-name="${d.name}">
          ${favBtn}
          ${cmpBtn}
          <div class="dentist-card__avatar">${d.photoUrl ? `<img src="${d.photoUrl}" alt="${d.name}" class="dentist-card__avatar-img" loading="lazy" onerror="this.parentElement.innerHTML='${initials}'">` : initials}</div>
          <div class="dentist-card__body">
            <h3 class="dentist-card__name">
              <a href="${profileLink}">${d.name}</a>
            </h3>
            ${openBadge}
            <div class="dentist-card__meta">
              <span class="dentist-card__meta-item">${ratingDisplay}</span>
              <span class="dentist-card__meta-item">📍 ${d.suburb && d.suburb !== d.city ? `${d.suburb}, ${d.city}` : (d.city || d.suburb || 'Unknown')}</span>
              ${reviewText ? `<span class="dentist-card__meta-item">${reviewText}</span>` : ''}
            </div>
            ${descText ? `<p class="dentist-card__desc">${descText}</p>` : ''}
            ${servicePills ? `<div class="dentist-card__services">${servicePills}</div>` : ''}
            ${pricingPreview}
            <div class="dentist-card__footer">
              <div>
                ${phoneText ? `<span class="dentist-card__phone">${phoneText}</span>` : ''}
                ${emailText ? `<span class="dentist-card__email">${emailText}</span>` : ''}
              </div>
              <a href="${profileLink}" class="btn btn--primary">View Profile</a>
            </div>
          </div>
        </article>
      `;
    }

    // Pagination
    const ITEMS_PER_PAGE = 50;
    let visibleCount = ITEMS_PER_PAGE;

    function render() {
      _favs = getFavourites();
      _cmpIds = compareIds();
      let filtered = allDentists.filter(d => {
        if (showFavouritesOnly && !_favs.has(d.id)) return false;
        if (showOpenOnly && isOpenNow(d) !== true) return false;
        if (activeSpecialties.length) {
          const specs = d.practitionerSpecialties || [];
          if (!activeSpecialties.every(kw => specs.some(s => s.includes(kw)))) return false;
        }
        if (activeLanguages.length) {
          const langs = d.practitionerLanguages || [];
          if (!activeLanguages.some(l => langs.includes(l))) return false;
        }
        if (activeAmenities.length) {
          if (!activeAmenities.every(key => checkAmenity(key, d))) return false;
        }
        if (minExperience > 0 && (d.maxExperience == null || d.maxExperience < minExperience)) return false;
        if (activeSuburbs.length && !activeSuburbs.includes(d.suburb)) return false;
        if (activeServices.length && !searchQuery && !activeServices.every(s => {
          if (s === 'Hygienist') return getHygienistPrice(d) !== null;
          return (SERVICE_ALIASES[s] || [s]).some(a => d.services.includes(a));
        })) return false;
        if (minRating > 0 && (d.rating == null || d.rating < minRating)) return false;
        if (searchQuery) {
          const q = searchQuery.toLowerCase();
          const matchesName = d.name.toLowerCase().includes(q);
          const matchesService = d.services.some(s => s.toLowerCase().includes(q));
          const matchesPractitioner = (d.practitionerNames || []).some(n => n.toLowerCase().includes(q));
          if (!matchesName && !matchesService && !matchesPractitioner) return false;
        }
        const price = getCheckupPrice(d);
        if (price !== null && maxPrice !== Infinity && price > maxPrice) return false;
        const hygPrice = getHygienistPrice(d);
        if (hygPrice !== null && maxHygienistPrice !== Infinity && hygPrice > maxHygienistPrice) return false;
        return true;
      });
      if (activeTreatmentPriceType === 'checkup') {
        filtered.sort((a, b) => {
          const pa = getCheckupPrice(a), pb = getCheckupPrice(b);
          if (pa !== null && pb !== null) return pa - pb;
          if (pa !== null) return -1;
          if (pb !== null) return 1;
          return (b.rating || 0) - (a.rating || 0);
        });
      } else if (activeTreatmentPriceType === 'hygienist') {
        filtered.sort((a, b) => {
          const pa = getHygienistPrice(a), pb = getHygienistPrice(b);
          if (pa !== null && pb !== null) return pa - pb;
          if (pa !== null) return -1;
          if (pb !== null) return 1;
          return (b.rating || 0) - (a.rating || 0);
        });
      } else if (sortBy === 'rating') {
        filtered.sort((a, b) => (b.rating || 0) - (a.rating || 0));
      } else if (sortBy === 'name') {
        filtered.sort((a, b) => a.name.localeCompare(b.name));
      } else if (sortBy === 'reviews') {
        filtered.sort((a, b) => (b.reviewCount || 0) - (a.reviewCount || 0));
      } else if (sortBy === 'price') {
        filtered.sort((a, b) => (getCheckupPrice(a) || 999) - (getCheckupPrice(b) || 999));
      } else if (sortBy === 'price-desc') {
        filtered.sort((a, b) => (getCheckupPrice(b) || 0) - (getCheckupPrice(a) || 0));
      } else if (sortBy === 'rating-asc') {
        filtered.sort((a, b) => (a.rating || 0) - (b.rating || 0));
      }

      if (filtered.length === 0) {
        if (showFavouritesOnly && _favs.size === 0) {
          dentistGrid.innerHTML = `
            <div class="no-results">
              <div class="no-results__icon">♥</div>
              <p class="no-results__desc">No saved clinics yet. Click ♥ on any card to save a clinic.</p>
              <button class="btn btn--outline clear-filters-btn">Clear all filters</button>
            </div>
          `;
        } else {
          const activeLabels = [];
          if (showFavouritesOnly) activeLabels.push('Saved');
          if (showOpenOnly) activeLabels.push('Open now');
          activeSpecialties.forEach(s => activeLabels.push(s));
          activeAmenities.forEach(a => activeLabels.push(a.replace(/_/g, ' ')));
          if (searchQuery) activeLabels.push(`"${searchQuery}"`);
          activeServices.forEach(s => activeLabels.push(s));
          activeLanguages.forEach(l => activeLabels.push(l));
          activeSuburbs.forEach(s => activeLabels.push(s));
          if (minRating > 0) activeLabels.push(`★ ${minRating.toFixed(1)}+`);
          if (maxPrice !== Infinity) activeLabels.push(`under $${maxPrice}`);
          if (maxHygienistPrice !== Infinity) activeLabels.push(`hygienist under $${maxHygienistPrice}`);

          const filtersDesc = activeLabels.length
            ? `No results for <strong>${activeLabels.join(' + ')}</strong>.`
            : 'No dentists found.';

          dentistGrid.innerHTML = `
            <div class="no-results">
              <div class="no-results__icon">🔍</div>
              <p class="no-results__desc">${filtersDesc}</p>
              <button class="btn btn--outline clear-filters-btn">Clear all filters</button>
            </div>
          `;
        }
      } else {
        const showing = filtered.slice(0, visibleCount);
        const remaining = filtered.length - showing.length;

        let html = showing.map(cardHTML).join('');

        // Load More button
        if (remaining > 0) {
          html += `
            <div class="load-more-container">
              <button class="btn btn--primary btn--lg load-more-btn" id="load-more-btn">
                Load More (${remaining} remaining)
              </button>
            </div>
          `;
        }

        dentistGrid.innerHTML = html;

        // Attach load more handler
        const loadMoreBtn = document.getElementById('load-more-btn');
        if (loadMoreBtn) {
          loadMoreBtn.addEventListener('click', () => {
            visibleCount += ITEMS_PER_PAGE;
            render();
          });
        }
      }

      if (resultsCount) {
        const totalFiltered = filtered.length;
        const showingCount = Math.min(visibleCount, totalFiltered);
        if (showingCount < totalFiltered) {
          resultsCount.textContent = `Showing ${showingCount} of ${totalFiltered} ${savedMode ? 'saved clinics' : `dentists in ${displayLocation}`}`;
        } else {
          resultsCount.textContent = `Showing ${totalFiltered} ${savedMode ? `saved clinic${totalFiltered !== 1 ? 's' : ''}` : `dentist${totalFiltered !== 1 ? 's' : ''} in ${displayLocation}`}`;
        }
      }

      // Keep apply-button count in sync
      const n = filtered.length;
      document.querySelectorAll('.filter-apply-btn').forEach(btn => {
        btn.textContent = `Show ${n} result${n !== 1 ? 's' : ''} →`;
      });
    }

    // Reset pagination when filters change
    function renderWithReset() {
      visibleCount = ITEMS_PER_PAGE;
      render();
    }

    function updateFavToggle() {
      const btn = document.getElementById('fav-toggle');
      if (!btn) return;
      const count = getFavourites().size;
      btn.textContent = count > 0 ? `♥ Saved (${count})` : '♥ Saved';
      btn.classList.toggle('fav-toggle--active', showFavouritesOnly);
    }

    function updateOpenToggle() {
      const btn = document.getElementById('open-toggle');
      if (!btn) return;
      btn.classList.toggle('fav-toggle--active', showOpenOnly);
    }

    function clearAllFilters() {
      activeSuburbs = [];
      activeLanguages = [];
      activeServices = [];
      minRating = 0;
      searchQuery = '';
      maxPrice = Infinity;
      maxHygienistPrice = Infinity;
      activeTreatmentPriceType = null;
      activeSpecialties = [];
      activeAmenities = [];
      minExperience = 0;
      showFavouritesOnly = false;
      showOpenOnly = false;
      updateFavToggle();
      updateOpenToggle();

      document.querySelectorAll('.filter-suburb, .filter-service, .filter-specialty, .filter-amenity, .filter-language').forEach(cb => { cb.checked = false; });
      document.querySelectorAll('.filter-exp-slider').forEach(s => {
        s.value = '0';
        const val = s.closest('[data-filter="experience"]')?.querySelector('.filter-exp-val');
        if (val) val.textContent = 'Any';
      });
      if (searchInput) searchInput.value = '';

      // Reset sliders + labels without triggering extra renders
      const ratingLabel = 'Any';
      [document.getElementById('desktop-rating-range'), document.getElementById('mobile-rating-range')].forEach(el => { if (el) el.value = 0; });
      [document.getElementById('desktop-rating-value'), document.getElementById('mobile-rating-value')].forEach(el => { if (el) el.textContent = ratingLabel; });

      [document.getElementById('desktop-price-range'), document.getElementById('mobile-price-range')].forEach(el => { if (el) el.value = 300; });
      [document.getElementById('desktop-price-value'), document.getElementById('mobile-price-value')].forEach(el => { if (el) el.textContent = 'Any'; });

      [document.getElementById('desktop-hygienist-range'), document.getElementById('mobile-hygienist-range')].forEach(el => { if (el) el.value = 200; });
      [document.getElementById('desktop-hygienist-value'), document.getElementById('mobile-hygienist-value')].forEach(el => { if (el) el.textContent = 'Any'; });

      renderWithReset();
    }

    // Card interaction: favourite toggle + clear-filters (event delegation)
    dentistGrid.addEventListener('click', (e) => {
      if (e.target.closest('.clear-filters-btn')) { clearAllFilters(); return; }

      const favBtnEl = e.target.closest('.fav-btn');
      if (favBtnEl) {
        e.preventDefault();
        e.stopPropagation();
        const id = parseInt(favBtnEl.dataset.favId, 10);
        const favs = getFavourites();
        if (favs.has(id)) favs.delete(id); else favs.add(id);
        saveFavourites(favs);
        _favs = favs;
        const isFav = favs.has(id);
        favBtnEl.classList.toggle('fav-btn--active', isFav);
        favBtnEl.setAttribute('aria-label', isFav ? 'Remove from saved' : 'Save clinic');
        favBtnEl.title = isFav ? 'Remove from saved' : 'Save clinic';
        updateFavToggle();
        if (showFavouritesOnly) renderWithReset();
        return;
      }

      const servicePillEl = e.target.closest('.pill[data-service]');
      if (servicePillEl) {
        e.preventDefault();
        e.stopPropagation();
        const svc = servicePillEl.dataset.service;
        const desc = FILTER_DESCS[svc];
        if (!desc) return;
        let tt = document.getElementById('filter-info-tooltip');
        if (!tt) {
          tt = document.createElement('div');
          tt.id = 'filter-info-tooltip';
          tt.style.cssText = 'position:fixed;z-index:9999;max-width:220px;background:var(--clr-navy,#1a3c5e);color:#fff;font-size:.78rem;line-height:1.5;padding:.5rem .75rem;border-radius:7px;box-shadow:0 4px 14px rgba(0,0,0,.25);display:none;pointer-events:none;';
          document.body.appendChild(tt);
        }
        if (tt.style.display === 'block' && tt._src === servicePillEl) {
          tt.style.display = 'none'; tt._src = null; return;
        }
        tt.innerHTML = `<strong style="display:block;margin-bottom:.2rem;">${svc === 'Hygienist' ? 'Hygienist: Scale & clean' : svc}</strong>${desc}`;
        tt.style.display = 'block';
        tt._src = servicePillEl;
        const r = servicePillEl.getBoundingClientRect();
        let left = r.left;
        if (left + 224 > window.innerWidth - 8) left = window.innerWidth - 232;
        let top = r.bottom + 6;
        if (top + 100 > window.innerHeight) top = r.top - 106;
        tt.style.left = `${Math.max(8, left)}px`;
        tt.style.top = `${top}px`;
        return;
      }

      const cmpBtnEl = e.target.closest('.cmp-btn');
      if (cmpBtnEl) {
        e.preventDefault();
        e.stopPropagation();
        const id = parseInt(cmpBtnEl.dataset.cmpId, 10);
        let list = getCompare();
        const idx = list.findIndex(c => c.id === id);
        if (idx >= 0) {
          list.splice(idx, 1);
        } else {
          if (list.length >= COMPARE_MAX) {
            alert(`You can compare up to ${COMPARE_MAX} clinics at a time. Remove one first.`);
            return;
          }
          const d = allDentists.find(x => x.id === id);
          if (!d) return;
          // Snapshot the fields compare.html needs so it renders without refetching
          list.push({
            id: d.id, name: d.name, slug: d.slug, suburb: d.suburb, city: d.city,
            address: d.address || '', phone: d.phone || '', website: d.website || '',
            rating: d.rating || 0, reviewCount: d.reviewCount || 0,
            services: d.services || [], pricing: d.pricing || [],
            photoUrl: d.photoUrl || ''
          });
          if (typeof gtag === 'function') {
            gtag('event', 'add_to_compare', { dentist_id: d.id, dentist_name: d.name });
          }
        }
        saveCompare(list);
        _cmpIds = compareIds();
        const nowIn = idx < 0;
        cmpBtnEl.classList.toggle('cmp-btn--active', nowIn);
        cmpBtnEl.innerHTML = nowIn ? '✓ Added' : '⚖ Compare';
        cmpBtnEl.setAttribute('aria-label', nowIn ? 'Remove from comparison' : 'Add to comparison');
        cmpBtnEl.title = nowIn ? 'Remove from comparison' : 'Add to comparison';
        renderCompareTray();
      }
    });

    // Service filters
    document.querySelectorAll('.filter-service').forEach(cb => {
      cb.addEventListener('change', () => {
        // Sync paired mobile/desktop checkbox to the same state
        document.querySelectorAll(`.filter-service[value="${cb.value}"]`).forEach(paired => {
          paired.checked = cb.checked;
        });
        activeServices = [...new Set(Array.from(document.querySelectorAll('.filter-service:checked')).map(el => el.value))];
        if (activeServices.includes('Hygienist')) {
          activeTreatmentPriceType = 'hygienist';
        } else if (activeTreatmentPriceType === 'hygienist') {
          activeTreatmentPriceType = null;
        }
        renderWithReset();
      });
    });

    // Rating slider (sync desktop & mobile)
    const desktopRatingSlider = document.getElementById('desktop-rating-range');
    const mobileRatingSlider = document.getElementById('mobile-rating-range');
    const desktopRatingLabel = document.getElementById('desktop-rating-value');
    const mobileRatingLabel = document.getElementById('mobile-rating-value');

    function updateRatingSlider(value) {
      minRating = parseFloat(value);
      const label = minRating === 0 ? 'Any' : `★ ${minRating.toFixed(1)}+`;
      if (desktopRatingSlider) desktopRatingSlider.value = minRating;
      if (mobileRatingSlider) mobileRatingSlider.value = minRating;
      if (desktopRatingLabel) desktopRatingLabel.textContent = label;
      if (mobileRatingLabel) mobileRatingLabel.textContent = label;
      renderWithReset();
    }

    if (desktopRatingSlider) desktopRatingSlider.addEventListener('input', (e) => updateRatingSlider(e.target.value));
    if (mobileRatingSlider) mobileRatingSlider.addEventListener('input', (e) => updateRatingSlider(e.target.value));

    // Search
    const searchInput = document.getElementById('listings-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        const raw = e.target.value;
        const treatment = matchTreatment(raw);
        if (treatment) {
          document.querySelectorAll(`.filter-service[value="${treatment.service}"]`).forEach(cb => { cb.checked = true; });
          activeServices = [...new Set(Array.from(document.querySelectorAll('.filter-service:checked')).map(el => el.value))];
          activeTreatmentPriceType = treatment.priceType;
          searchQuery = '';
        } else {
          activeTreatmentPriceType = null;
          searchQuery = raw;
        }
        renderWithReset();
      });
      // Pre-fill from ?q= URL param (passed by home page search)
      const urlQ = new URLSearchParams(window.location.search).get('q');
      if (urlQ) {
        const qLower = urlQ.trim().toLowerCase();
        const treatment = matchTreatment(urlQ);
        if (treatment) {
          if (treatment.service) {
            document.querySelectorAll(`.filter-service[value="${treatment.service}"]`).forEach(cb => { cb.checked = true; });
            activeServices = [treatment.service];
          }
          activeTreatmentPriceType = treatment.priceType;
        } else {
          // Fall back to direct service checkbox match
          const matchingService = Array.from(document.querySelectorAll('.filter-service'))
            .find(cb => cb.value.toLowerCase() === qLower);
          if (matchingService) {
            document.querySelectorAll(`.filter-service[value="${matchingService.value}"]`).forEach(cb => { cb.checked = true; });
            activeServices = [matchingService.value];
          } else {
            activeServices = [];
            searchInput.value = urlQ;
            searchQuery = urlQ;
          }
        }
      }
    }

    // Sort
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        sortBy = e.target.value;
        renderWithReset();
      });
    }

    // Favourites toggle — injected next to sort select
    const listingsHeader = document.querySelector('.listings-header');
    if (listingsHeader && sortSelect) {
      const openToggleBtn = document.createElement('button');
      openToggleBtn.id = 'open-toggle';
      openToggleBtn.className = 'fav-toggle';
      openToggleBtn.textContent = '🟢 Open now';
      listingsHeader.insertBefore(openToggleBtn, sortSelect);
      openToggleBtn.addEventListener('click', () => {
        showOpenOnly = !showOpenOnly;
        updateOpenToggle();
        renderWithReset();
      });

      const favToggleBtn = document.createElement('button');
      favToggleBtn.id = 'fav-toggle';
      favToggleBtn.className = 'fav-toggle';
      listingsHeader.insertBefore(favToggleBtn, sortSelect);
      updateFavToggle();
      favToggleBtn.addEventListener('click', () => {
        showFavouritesOnly = !showFavouritesOnly;
        updateFavToggle();
        renderWithReset();
      });

      // Ensure mobile filter button is first in the row (before Open now)
      // Works for both cached HTML (button may be outside listingsHeader) and fresh HTML
      const mobileFilterBtn = document.getElementById('mobile-filter-btn');
      if (mobileFilterBtn) {
        mobileFilterBtn.remove();
        listingsHeader.insertBefore(mobileFilterBtn, openToggleBtn);
      }
    }

    // Price slider (sync desktop & mobile)
    const desktopSlider = document.getElementById('desktop-price-range');
    const mobileSlider = document.getElementById('mobile-price-range');
    const desktopLabel = document.getElementById('desktop-price-value');
    const mobileLabel = document.getElementById('mobile-price-value');

    function updatePriceSlider(value) {
      maxPrice = parseInt(value, 10) >= 300 ? Infinity : parseInt(value, 10);
      const label = maxPrice === Infinity ? 'Any' : `Up to $${maxPrice}`;
      const sliderVal = maxPrice === Infinity ? 300 : maxPrice;
      if (desktopSlider) desktopSlider.value = sliderVal;
      if (mobileSlider) mobileSlider.value = sliderVal;
      if (desktopLabel) desktopLabel.textContent = label;
      if (mobileLabel) mobileLabel.textContent = label;
      renderWithReset();
    }

    if (desktopSlider) {
      desktopSlider.addEventListener('input', (e) => updatePriceSlider(e.target.value));
    }
    if (mobileSlider) {
      mobileSlider.addEventListener('input', (e) => updatePriceSlider(e.target.value));
    }

    // Hygienist price slider (sync desktop & mobile)
    const desktopHygienistSlider = document.getElementById('desktop-hygienist-range');
    const mobileHygienistSlider = document.getElementById('mobile-hygienist-range');
    const desktopHygienistLabel = document.getElementById('desktop-hygienist-value');
    const mobileHygienistLabel = document.getElementById('mobile-hygienist-value');

    function updateHygienistSlider(value) {
      maxHygienistPrice = parseInt(value, 10) >= 200 ? Infinity : parseInt(value, 10);
      const label = maxHygienistPrice === Infinity ? 'Any' : `Up to $${maxHygienistPrice}`;
      const sliderVal = maxHygienistPrice === Infinity ? 200 : maxHygienistPrice;
      if (desktopHygienistSlider) desktopHygienistSlider.value = sliderVal;
      if (mobileHygienistSlider) mobileHygienistSlider.value = sliderVal;
      if (desktopHygienistLabel) desktopHygienistLabel.textContent = label;
      if (mobileHygienistLabel) mobileHygienistLabel.textContent = label;
      renderWithReset();
    }

    if (desktopHygienistSlider) {
      desktopHygienistSlider.addEventListener('input', (e) => updateHygienistSlider(e.target.value));
    }
    if (mobileHygienistSlider) {
      mobileHygienistSlider.addEventListener('input', (e) => updateHygienistSlider(e.target.value));
    }

    // Reflect default activeServices in checkboxes before first render
    document.querySelectorAll('.filter-service[value="General Dentistry"]').forEach(cb => {
      cb.checked = activeServices.includes('General Dentistry');
    });

    // Build dynamic suburb + specialty + amenity + experience + language filters
    buildSuburbFilters(allDentists);
    buildSpecialtyFilters(allDentists);
    buildAmenitiesFilter(allDentists);
    buildExperienceFilter(allDentists);
    buildLanguageFilters(allDentists);
    addFilterInfoButtons();
    addApplyFilterButton();

    // Suburb filters (injected dynamically by buildSuburbFilters)
    document.querySelectorAll('.filter-suburb').forEach(cb => {
      cb.addEventListener('change', () => {
        activeSuburbs = Array.from(document.querySelectorAll('.filter-suburb:checked')).map(el => el.value);
        renderWithReset();
      });
    });

    // Specialty filters (injected dynamically by buildSpecialtyFilters)
    document.querySelectorAll('.filter-specialty').forEach(cb => {
      cb.addEventListener('change', () => {
        document.querySelectorAll(`.filter-specialty[value="${cb.value}"]`).forEach(p => { p.checked = cb.checked; });
        activeSpecialties = [...new Set(Array.from(document.querySelectorAll('.filter-specialty:checked')).map(el => el.value))];
        renderWithReset();
      });
    });

    // Amenity filters (injected dynamically by buildAmenitiesFilter)
    document.querySelectorAll('.filter-amenity').forEach(cb => {
      cb.addEventListener('change', () => {
        document.querySelectorAll(`.filter-amenity[value="${cb.value}"]`).forEach(p => { p.checked = cb.checked; });
        activeAmenities = [...new Set(Array.from(document.querySelectorAll('.filter-amenity:checked')).map(el => el.value))];
        renderWithReset();
      });
    });

    // Language filters (injected dynamically by buildLanguageFilters)
    document.querySelectorAll('.filter-language').forEach(cb => {
      cb.addEventListener('change', () => {
        document.querySelectorAll(`.filter-language[value="${cb.value}"]`).forEach(p => { p.checked = cb.checked; });
        activeLanguages = [...new Set(Array.from(document.querySelectorAll('.filter-language:checked')).map(el => el.value))];
        renderWithReset();
      });
    });

    // Experience filter (injected dynamically by buildExperienceFilter)
    document.querySelectorAll('.filter-exp-slider').forEach(slider => {
      slider.addEventListener('input', () => {
        minExperience = parseInt(slider.value, 10);
        document.querySelectorAll('.filter-exp-slider').forEach(s => {
          s.value = slider.value;
          s.closest('[data-filter="experience"]').querySelector('.filter-exp-val').textContent =
            slider.value === '0' ? 'Any' : slider.value + '+ yrs';
        });
        renderWithReset();
      });
    });

    // Initial render
    render();
  }

  // Merged filter aliases — one checkbox value matches multiple raw service strings
  const SERVICE_ALIASES = {
    'Oral Surgery': ['Oral Surgery', 'Oral and Maxillofacial Surgery'],
    'Cosmetic':     ['Cosmetic', 'Teeth Whitening'],
  };

  const AMENITY_FILTERS = [
    { key: 'dental_anxiety_friendly', label: 'Dental anxiety friendly' },
    { key: 'wheelchair_accessible',   label: 'Wheelchair accessible' },
    { key: 'online_booking',          label: 'Online booking' },
    { key: 'saturday_hours',          label: 'Open Saturdays' },
    { key: 'sunday_hours',            label: 'Open Sundays' },
    { key: 'evening_hours',           label: 'Open evenings (after 5 PM)' },
    { key: 'same_day_emergency',      label: 'Same-day emergencies' },
  ];

  function buildAmenitiesFilter(allDentists) {
    const available = AMENITY_FILTERS.filter(af =>
      allDentists.some(d => checkAmenity(af.key, d))
    );
    if (available.length === 0) return;

    const html = available.map(af => `
      <label class="filter-check">
        <input type="checkbox" class="filter-amenity" value="${af.key}">
        <span>${af.label}</span>
      </label>`).join('');

    const groupHTML = `
      <div class="filter-group" data-filter="amenity">
        <div class="filter-group__label">Amenities</div>
        <div class="filter-group__items">${html}</div>
      </div>`;

    document.querySelectorAll('.sidebar, .filter-drawer').forEach(container => {
      if (container.querySelector('[data-filter="amenity"]')) return;
      container.insertAdjacentHTML('beforeend', groupHTML);
    });
  }

  function buildExperienceFilter(allDentists) {
    if (!allDentists.some(d => d.maxExperience != null)) return;

    const groupHTML = `
      <div class="filter-group" data-filter="experience">
        <div class="filter-group__label">Practitioner Experience (Years) <span class="filter-exp-val">Any</span></div>
        <input type="range" class="filter-exp-slider" min="0" max="10" step="1" value="0">
        <div class="filter-exp-ticks"><span>Any</span><span>5+</span><span>10+</span></div>
      </div>`;

    document.querySelectorAll('.sidebar, .filter-drawer').forEach(container => {
      if (container.querySelector('[data-filter="experience"]')) return;
      container.insertAdjacentHTML('beforeend', groupHTML);
    });
  }

  // Specialty filter definitions — only show specialties not already covered by service filters
  const SPECIALTY_FILTERS = [
    { label: 'IV Sedation',         keyword: 'sedation' },
    { label: 'Oral Health Therapy', keyword: 'oral health therap' },
  ];

  function buildSpecialtyFilters(allDentists) {
    // Only show specialties that at least one clinic in this region has
    const available = SPECIALTY_FILTERS.filter(sf =>
      allDentists.some(d => (d.practitionerSpecialties || []).some(s => s.includes(sf.keyword)))
    );
    if (available.length === 0) return;

    const html = available.map(sf => `
      <label class="filter-check">
        <input type="checkbox" class="filter-specialty" value="${sf.keyword}">
        <span>${sf.label}</span>
      </label>`).join('');

    const groupHTML = `
      <div class="filter-group" data-filter="specialty">
        <div class="filter-group__label">Specialist Skills</div>
        <div class="filter-group__items">${html}</div>
      </div>`;

    document.querySelectorAll('.sidebar, .filter-drawer').forEach(container => {
      if (container.querySelector('[data-filter="specialty"]')) return;
      container.insertAdjacentHTML('beforeend', groupHTML);
    });
  }

  // Info buttons on filter labels
  const FILTER_DESCS = {
    'General Dentistry':  'Checkups, fillings, extractions, and routine dental care for the whole family.',
    'Cosmetic':           'Smile makeovers including veneers, teeth whitening, bonding, and aesthetic restorations.',
    'Dental Implants':    'Permanent tooth replacements surgically placed in the jaw — look, feel, and function like natural teeth.',
    'Dentures':           'Custom-made full or partial dentures to replace missing teeth.',
    'Endodontics':        'Root canal treatment to save infected or damaged teeth from extraction.',
    'Hygienist':          'Professional scale and clean, stain removal, and personalised oral hygiene advice.',
    'Oral Surgery':       'Tooth extractions, wisdom teeth removal, and minor surgical procedures.',
    'Orthodontics':       'Braces and clear aligners (including Invisalign) to straighten teeth and correct bite issues.',
    'Periodontal Care':   'Treatment for gum disease, including deep cleaning and ongoing gum health management.',
    'Teen Dental':        'Subsidised dental care for eligible patients aged 18 and under.',
    'sedation':           'Intravenous sedation for patients with dental anxiety or for complex procedures — you remain conscious but deeply relaxed.',
    'oral health therap': 'Oral health therapists provide preventive care, hygiene treatments, and dental treatment for children and adolescents.',
  };

  function addFilterInfoButtons() {
    let tooltip = document.getElementById('filter-info-tooltip');
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.id = 'filter-info-tooltip';
      tooltip.style.cssText = 'position:fixed;z-index:9999;max-width:220px;background:var(--clr-navy,#1a3c5e);color:#fff;font-size:.78rem;line-height:1.5;padding:.5rem .75rem;border-radius:7px;box-shadow:0 4px 14px rgba(0,0,0,.25);display:none;pointer-events:none;';
      document.body.appendChild(tooltip);
    }

    document.querySelectorAll('.filter-check').forEach(label => {
      const cb = label.querySelector('.filter-service, .filter-specialty');
      if (!cb || label.querySelector('.filter-info-btn')) return;
      const desc = FILTER_DESCS[cb.value];
      if (!desc) return;

      const btn = document.createElement('button');
      btn.className = 'filter-info-btn';
      btn.type = 'button';
      btn.setAttribute('aria-label', `About ${cb.value}`);
      btn.innerHTML = 'i';
      btn.style.cssText = 'width:1rem;height:1rem;border-radius:50%;border:1.5px solid var(--clr-gray-300,#d1d5db);background:transparent;color:var(--clr-gray-400,#9ca3af);font-size:.6rem;font-weight:700;font-style:italic;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;line-height:1;margin-left:.35rem;flex-shrink:0;vertical-align:middle;padding:0;';
      btn.addEventListener('click', e => {
        e.preventDefault();
        e.stopPropagation();
        if (tooltip.style.display === 'block' && tooltip._src === btn) {
          tooltip.style.display = 'none';
          tooltip._src = null;
          return;
        }
        tooltip.textContent = desc;
        tooltip.style.display = 'block';
        tooltip._src = btn;
        const r = btn.getBoundingClientRect();
        let left = r.left;
        if (left + 224 > window.innerWidth - 8) left = window.innerWidth - 232;
        let top = r.bottom + 6;
        if (top + 100 > window.innerHeight) top = r.top - 106;
        tooltip.style.left = `${Math.max(8, left)}px`;
        tooltip.style.top = `${top}px`;
      });
      label.appendChild(btn);
    });

    document.addEventListener('click', e => {
      if (!e.target.closest('.filter-info-btn')) {
        tooltip.style.display = 'none';
        tooltip._src = null;
      }
    });
  }

  function addApplyFilterButton() {
    const drawer = document.querySelector('.filter-drawer');
    const overlay = document.querySelector('.filter-overlay');

    document.querySelectorAll('.sidebar, .filter-drawer').forEach(container => {
      if (container.querySelector('.filter-apply-btn')) return;
      const btn = document.createElement('button');
      btn.className = 'btn btn--primary filter-apply-btn';
      btn.type = 'button';
      btn.style.cssText = 'width:100%;margin-top:1.25rem;font-size:.9rem;padding:.6rem 1rem;';
      btn.textContent = 'Show results';
      btn.addEventListener('click', () => {
        if (drawer && drawer.classList.contains('active')) {
          drawer.classList.remove('active');
          overlay && overlay.classList.remove('active');
        }
        const grid = document.getElementById('dentist-grid');
        if (grid) grid.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      container.appendChild(btn);
    });
  }

  // Build suburb filter checkboxes dynamically from data
  function buildSuburbFilters(allDentists) {
    // Count dentists per suburb
    const suburbCounts = {};
    allDentists.forEach(d => {
      if (d.suburb) {
        suburbCounts[d.suburb] = (suburbCounts[d.suburb] || 0) + 1;
      }
    });

    const sortedSuburbs = Object.entries(suburbCounts)
      .sort((a, b) => a[0].localeCompare(b[0]));

    // Helper to build checkbox HTML
    function buildCheckboxes(suburbs) {
      return suburbs.map(([suburb, count]) => `
        <label class="filter-check">
          <input type="checkbox" class="filter-suburb" value="${suburb}">
          <span>${suburb} <span class="filter-check__count">${count}</span></span>
        </label>
      `).join('');
    }

    const checkboxHtml = buildCheckboxes(sortedSuburbs);

    const desktopSuburbItems = document.querySelector('.sidebar [data-filter="suburb"] .filter-group__items');
    if (desktopSuburbItems) desktopSuburbItems.innerHTML = checkboxHtml;

    const mobileSuburbItems = document.querySelector('.filter-drawer [data-filter="suburb"] .filter-group__items');
    if (mobileSuburbItems) mobileSuburbItems.innerHTML = checkboxHtml;
  }

  function buildLanguageFilters(allDentists) {
    // Count clinics per language
    const counts = {};
    allDentists.forEach(d => {
      (d.practitionerLanguages || []).forEach(lang => {
        counts[lang] = (counts[lang] || 0) + 1;
      });
    });
    const available = Object.entries(counts)
      .filter(([, n]) => n >= 1)
      .sort((a, b) => b[1] - a[1]);
    if (available.length === 0) return;

    const html = available.map(([lang, count]) => `
      <label class="filter-check">
        <input type="checkbox" class="filter-language" value="${lang}">
        <span>${lang} <span class="filter-check__count">${count}</span></span>
      </label>`).join('');

    const groupHTML = `
      <div class="filter-group" data-filter="language">
        <div class="filter-group__label">Language</div>
        <div class="filter-group__items">${html}</div>
      </div>`;

    document.querySelectorAll('.sidebar, .filter-drawer').forEach(container => {
      if (container.querySelector('[data-filter="language"]')) return;
      container.insertAdjacentHTML('beforeend', groupHTML);
    });
  }

  // ===== Mobile Filter Drawer =====
  const filterBtn = document.querySelector('.mobile-filter-btn');
  const filterOverlay = document.querySelector('.filter-overlay');
  const filterDrawer = document.querySelector('.filter-drawer');
  const filterClose = document.querySelector('.filter-drawer__close');

  if (filterBtn && filterOverlay && filterDrawer) {
    filterBtn.addEventListener('click', () => {
      filterOverlay.classList.add('active');
      filterDrawer.classList.add('active');
    });

    const closeDrawer = () => {
      filterOverlay.classList.remove('active');
      filterDrawer.classList.remove('active');
    };

    filterClose?.addEventListener('click', closeDrawer);
    filterOverlay.addEventListener('click', closeDrawer);
  }

  // ===== Dentist Profile Page =====
  const REGION_FILES = {
    'Auckland': 'auckland.html',
    'Bay of Plenty': 'tauranga.html',
    'Canterbury': 'christchurch.html',
    'Gisborne': 'gisborne.html',
    'Hawke\'s Bay': 'hawkes-bay.html',
    'Manawatū-Whanganui': 'manawatu-whanganui.html',
    'Marlborough': 'marlborough.html',
    'Nelson': 'nelson-tasman.html',
    'Nelson & Tasman': 'nelson-tasman.html',
    'Northland': 'northland.html',
    'Otago': 'dunedin.html',
    'Southland': 'southland.html',
    'Taranaki': 'taranaki.html',
    'Waikato': 'hamilton.html',
    'Wellington': 'wellington.html',
    'Wairarapa': 'wairarapa.html',
    'West Coast': 'west-coast.html'
  };

  function setBackButton(region) {
    const backBtn = document.querySelector('.profile-hero__back');
    if (!backBtn || !region) return;
    const fileName = REGION_FILES[region] || 'index.html';
    backBtn.href = fileName;
    const displayName = region === 'Nelson' ? 'Nelson/Tasman' : region;
    backBtn.textContent = `← Back to ${displayName} listings`;
  }

  const profileContainer = document.getElementById('profile-content');
  if (profileContainer) {
    // Show loading
    profileContainer.innerHTML = `
      <div class="no-results">
        <div class="no-results__icon">⏳</div>
        <h3>Loading profile...</h3>
      </div>
    `;
    initProfile();
  }

  async function initProfile() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    const slug = params.get('slug');
    const regionParam = params.get('region');
    let dentist = null;

    // Set back button immediately from URL param so it works before async fetch completes
    if (regionParam) setBackButton(regionParam);

    // Load price averages in parallel with clinic fetch
    loadCityAverages();
    loadHygienistAverages();

    // Try Supabase first (by id)
    if (id && typeof fetchClinicById === 'function') {
      dentist = await fetchClinicById(id);
    }

    // Fall back to static data (by slug)
    if (!dentist && slug && typeof dentists !== 'undefined') {
      dentist = dentists.find(d => d.slug === slug);
    }

    if (!dentist) {
      profileContainer.innerHTML = `
        <div class="no-results">
          <div class="no-results__icon">😕</div>
          <h3>Dentist not found</h3>
          <p>The profile you're looking for doesn't exist. <a href="/" style="color: var(--clr-teal);">Go back to listings</a>.</p>
        </div>
      `;
      return;
    }

    // Track the profile view in GA4 (clinic name + id + region).
    // Register dentist_name / dentist_id / dentist_region as event-scoped
    // custom dimensions in GA4 Admin to report on them.
    if (typeof gtag === 'function') {
      gtag('event', 'view_dentist', {
        dentist_id: dentist.id,
        dentist_name: dentist.name,
        dentist_region: dentist.region || '(not set)'
      });
    }

    // Update hero
    const heroName = document.getElementById('profile-name');
    const heroMeta = document.getElementById('profile-meta');
    if (heroName) heroName.textContent = dentist.name;
    if (heroMeta) {
      const ratingHtml = dentist.rating
        ? `<span class="stars stars--lg">${starsHTML(dentist.rating)}</span> <strong style="color:#fff">${dentist.rating}</strong> <span>(${dentist.reviewCount} review${dentist.reviewCount === 1 ? '' : 's'})</span>`
        : '<span style="color:var(--clr-gray-300)">No rating yet</span>';
      const foundedHtml = dentist.foundedYear ? `<span class="profile-hero__meta-item">Est. ${dentist.foundedYear}</span>` : '';
      heroMeta.innerHTML = `
        <span class="profile-hero__meta-item">${ratingHtml}</span>
        <span class="profile-hero__meta-item">📍 ${dentist.address}</span>
        ${foundedHtml}
      `;
    }

    // Update Back button with confirmed region from loaded data
    if (dentist.region) setBackButton(dentist.region);

    document.title = `${dentist.name} | Dental Compare`;

    const serviceIcons = {
      'General Dentistry': '🦷', 'Cosmetic': '✨', 'Teeth Whitening': '💎',
      'Dental Implants': '🔩', 'Implants': '🔩', 'Orthodontics': '😁', 'Emergency': '🚨',
      'Dentures': '🦷', 'Oral Surgery': '🩺', 'Endodontics': '🔬',
      'Periodontal Care': '🦠', 'Oral and Maxillofacial Surgery': '🩺',
      'Hygienist': '🪥', 'Scale & clean': '🪥', 'Teen Dental': '🧒',
    };

    const serviceDescs = {
      'General Dentistry':              'Checkups, fillings, extractions, and all routine dental care for the whole family.',
      'Cosmetic':                       'Smile makeovers including veneers, bonding, and aesthetic restorations.',
      'Teeth Whitening':                'In-chair and take-home whitening treatments to brighten your smile.',
      'Dental Implants':                'Permanent tooth replacements that look, feel, and function like natural teeth.',
      'Implants':                       'Permanent tooth replacements that look, feel, and function like natural teeth.',
      'Orthodontics':                   'Braces and clear aligners to straighten teeth and correct bite issues.',
      'Emergency':                      'Same-day appointments for toothache, broken teeth, lost fillings, and dental trauma.',
      'Dentures':                       'Custom-made full and partial dentures to replace missing teeth.',
      'Oral Surgery':                   'Tooth extractions, wisdom teeth removal, and minor surgical procedures.',
      'Endodontics':                    'Root canal treatment to save infected or damaged teeth.',
      'Periodontal Care':               'Treatment for gum disease, including deep cleaning and ongoing gum health management.',
      'Oral and Maxillofacial Surgery': 'Surgical treatment of conditions affecting the mouth, jaw, and face.',
      'Hygienist':                      'Professional scale and clean, stain removal, and personalised oral hygiene advice.',
      'Scale & clean':                  'Professional scale and clean, stain removal, and personalised oral hygiene advice.',
      'Teen Dental':                    'Subsidised dental care for eligible patients aged 18 and under.',
    };

    const servicesHTML = dentist.services.map(s => {
      const displayName = s === 'Hygienist' ? 'Hygienist: Scale & clean' : s;
      return `
      <div class="service-item">
        <div class="service-item__icon">${serviceIcons[s] || '🦷'}</div>
        <div class="service-item__content">
          <div class="service-item__name">${displayName}</div>
          <div class="service-item__desc">${serviceDescs[s] || `${s} provided by qualified dental professionals.`}</div>
        </div>
      </div>
    `;
    }).join('');

    // Opening hours
    let hoursHTML = '';
    if (dentist.hours) {
      const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
      const today = days[new Date().getDay() === 0 ? 6 : new Date().getDay() - 1];
      hoursHTML = days.map(day => `
        <tr class="${day === today ? 'today' : ''}">
          <td>${day}</td>
          <td>${dentist.hours[day] || 'Closed'}</td>
        </tr>
      `).join('');
    }

    // Reviews rendered dynamically after profile HTML is set (supports sorting)

    // Pricing table — always show, with empty state if no data
    let pricingHTML = '';
    const PAYMENT_KEYWORDS = [
      'q card','afterpay','zip','laybuy','winz','work and income','southern cross',
      'acc','gem visa','gem finance','farmers','credit card','visa','mastercard',
      'eftpos','cash','payment plan','instalment','installment','interest-free',
      'supergold','gold card','humm','genoapay','partpay','flexicare',
    ];
    const isPaymentMethod = p => {
      const s = (p.service || '').toLowerCase();
      return PAYMENT_KEYWORDS.some(k => s.includes(k));
    };
    const pricingRows = (dentist.pricing || []).filter(p => /\$\d/.test(p.price));
    const paymentRows = (dentist.pricing || []).filter(p => !(/\$\d/.test(p.price)) && isPaymentMethod(p));
    if (pricingRows.length > 0) {
      const checkupPrice = getCheckupPrice(dentist);
      const cmps = getPriceComparisons(checkupPrice, dentist.city, dentist.region);
      const hygPrice = getHygienistPrice(dentist);
      const hygCmps = getHygienistComparisons(hygPrice, dentist.city, dentist.region);
      const rows = pricingRows.map(p => {
        const notesHtml = p.notes ? `<div class="pricing-note">${p.notes}</div>` : '';
        const s = p.service.toLowerCase();
        const isCheckup = s.includes('checkup') || s.includes('check-up') || s.includes('exam') ||
          s.includes('consult') || s.includes('assessment') || s.includes('new patient') ||
          s.includes('initial') || s.includes('comprehensive') || s.includes('oral health');
        const isHygienist = s.includes('hygienist') || s.includes('hygiene') ||
          (s.includes('scale') && (s.includes('polish') || s.includes('clean')));
        let cmpHtml = '';
        if (isCheckup) {
          if (cmps.city) cmpHtml += ` <span class="price-cmp price-cmp--${cmps.city.dir}">${cmps.city.text}</span>`;
          if (cmps.region) cmpHtml += ` <span class="price-cmp price-cmp--${cmps.region.dir}">${cmps.region.text}</span>`;
        }
        if (isHygienist) {
          if (hygCmps.city) cmpHtml += ` <span class="price-cmp price-cmp--${hygCmps.city.dir}">${hygCmps.city.text}</span>`;
          if (hygCmps.region) cmpHtml += ` <span class="price-cmp price-cmp--${hygCmps.region.dir}">${hygCmps.region.text}</span>`;
        }
        const displayService = isHygienist ? 'Hygienist: Scale & clean' : p.service;
        return `<tr><td>${displayService}${notesHtml}</td><td>${p.price}${cmpHtml}</td></tr>`;
      }).join('');
      pricingHTML = `
        <div class="profile-section profile-section--pricing">
          <h2 class="profile-section__title">Pricing</h2>
          <p style="font-size:.875rem;color:var(--clr-gray-500);margin-bottom:1rem;">Prices are indicative and may vary. Contact the practice for an exact quote.${dentist.pricesLastUpdated ? ` <span style="white-space:nowrap;">Last updated: ${new Date(dentist.pricesLastUpdated).toLocaleDateString('en-NZ', {month:'long',year:'numeric'})}</span>` : ''}</p>
          <div style="overflow-x: auto;">
            <table class="pricing-table">
              <thead><tr><th>Service</th><th>Price (NZD)</th></tr></thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
          <div class="submit-nudge">
            <span class="submit-nudge__text">Know a different price?</span>
            <button data-action="submit-info" class="submit-nudge__btn">Help the community &rarr;</button>
          </div>
        </div>
      `;
    } else {
      // Empty pricing state — placeholder for when we don't have data yet
      pricingHTML = `
        <div class="profile-section profile-section--pricing">
          <h2 class="profile-section__title">Pricing</h2>
          <div class="pricing-empty">
            <div class="pricing-empty__icon">💰</div>
            <h4 class="pricing-empty__title">No prices listed on website</h4>
            <p class="pricing-empty__text">This practice hasn't published prices on their website. Contact them directly for a quote.</p>
            ${dentist.phone ? `<a href="tel:${dentist.phone.replace(/\s/g, '')}" class="btn btn--outline btn--sm pricing-empty__btn">📞 Call for Pricing</a>` : ''}
            ${dentist.website ? `<a href="${dentist.website}" target="_blank" class="btn btn--outline btn--sm pricing-empty__btn">🌐 Check Website</a>` : ''}
          </div>
          <div class="submit-nudge">
            <span class="submit-nudge__text">Do you know the price?</span>
            <button data-action="submit-info" class="submit-nudge__btn">Help the community &rarr;</button>
          </div>
        </div>
      `;
    }

    // Collect payment pills from scraped_prices (merged with amenity data below)
    const scrapedPaymentPills = paymentRows.map(p => {
      const tip = p.price && p.price !== p.service ? ` title="${p.price}${p.notes ? ' — ' + p.notes : ''}"` : '';
      return `<span class="payment-pill"${tip}>${p.service}</span>`;
    });

    // Embedded map
    const encodedAddress = encodeURIComponent(dentist.address || dentist.name + ', New Zealand');
    const mapEmbed = `
      <div class="map-embed">
        <iframe
          src="https://maps.google.com/maps?q=${encodedAddress}&t=&z=15&ie=UTF8&iwloc=&output=embed"
          width="100%"
          height="250"
          style="border:0; border-radius: 12px;"
          allowfullscreen=""
          loading="lazy"
          referrerpolicy="no-referrer-when-downgrade">
        </iframe>
      </div>
    `;

    // Google Maps directions link
    const mapLink = dentist.googleMapsUrl
      ? `<a href="${dentist.googleMapsUrl}" target="_blank" class="btn btn--outline btn--block" style="margin-top:.5rem;">📍 Get Directions</a>`
      : '';

    // Write a Google Review button
    const writeReviewBtn = dentist.googleMapsUrl
      ? `<a href="${dentist.googleMapsUrl}" target="_blank" rel="noopener" class="btn btn--block" style="margin-top:.5rem;background:#fff;border:1.5px solid #dadce0;color:#3c4043;display:flex;align-items:center;justify-content:center;gap:.5rem;font-weight:500;"><svg width="16" height="16" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/><path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/><path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l3.66-2.84z" fill="#FBBC05"/><path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/></svg>Write a Google Review</a>`
      : '';

    // Website button
    const websiteBtn = dentist.website
      ? `<a href="${dentist.website}" target="_blank" class="btn btn--primary btn--block">Visit Website ↗</a>`
      : '';

    // Availability
    const availabilityHTML = (() => {
      const parts = [];
      if (dentist.acceptingNewPatients === true) {
        parts.push(`<div class="avail-badge avail-badge--yes">✓ Accepting new patients</div>`);
      } else if (dentist.acceptingNewPatients === false) {
        parts.push(`<div class="avail-badge avail-badge--no">✗ Not currently accepting new patients</div>`);
      }
      if (dentist.bookingUrl) {
        parts.push(`<a href="${dentist.bookingUrl}" target="_blank" rel="noopener" class="btn btn--primary btn--block">📅 Book Online</a>`);
      }
      return parts.join('');
    })();

    // Save button
    const profileIsFav = dentist.id && getFavourites().has(dentist.id);
    const saveBtn = dentist.id
      ? `<button id="profile-save-btn" class="btn btn--outline btn--block profile-save-btn${profileIsFav ? ' profile-save-btn--active' : ''}" style="margin-top:.5rem;">${profileIsFav ? '♥ Saved' : '♥ Save clinic'}</button>`
      : '';

    // Meet the Team section
    let teamHTML = '';
    if (dentist.practitioners && dentist.practitioners.length > 0) {
      const cards = dentist.practitioners.map(p => {
        const initials = p.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
        const specialtyPills = p.specialties
          ? p.specialties.split(',').map(s => `<span class="pill pill--sm">${s.trim()}</span>`).join(' ')
          : '';
        const languageNote = p.languages ? `<div class="team-card__languages">🌐 ${p.languages}</div>` : '';
        const avatar = p.photo_url
          ? `<button class="team-card__photo-btn" data-src="${p.photo_url}" data-name="${p.name}" aria-label="View photo of ${p.name}"><img class="team-card__photo" src="${p.photo_url}" alt="${p.name}" loading="lazy" onerror="this.closest('.team-card__photo-btn').style.display='none';this.closest('.team-card__avatar-wrap').querySelector('.team-card__avatar').style.display='flex'"></button>`
          : '';
        const initialsEl = `<div class="team-card__avatar"${p.photo_url ? ' style="display:none"' : ''}>${initials}</div>`;
        const cardSlug = p.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
        return `
          <div class="team-card" id="team-card-${cardSlug}">
            <div class="team-card__avatar-wrap">${avatar}${initialsEl}</div>
            <div class="team-card__body">
              <div class="team-card__name">${p.name}</div>
              ${p.experience ? `<div class="team-card__experience">${p.experience}</div>` : ''}
              ${specialtyPills ? `<div class="team-card__specialties">${specialtyPills}</div>` : ''}
              ${p.bio ? `<div class="team-card__bio-wrap"><p class="team-card__bio">${p.bio}</p><button class="team-card__read-more" onclick="var w=this.previousElementSibling;var expanded=w.classList.toggle('team-card__bio--expanded');this.textContent=expanded?'Read less ▲':'Read more ▼'">Read more ▼</button></div>` : ''}
              ${languageNote}
            </div>
          </div>`;
      }).join('');
      teamHTML = `
        <div class="profile-section profile-section--team">
          <h2 class="profile-section__title">Meet the Team</h2>
          <div class="team-list">${cards}</div>
        </div>`;
    }

    // Merge scraped payment methods + amenity payment_partners into one section
    let paymentHTML = '';
    const am = dentist.amenities;
    {
      const rawPartners = am && am.payment_partners;
      const rawPlans = am && am.membership_plans;
      let amenityChips = [];
      if (rawPartners) {
        try { amenityChips = JSON.parse(rawPartners).map(s => String(s).trim()).filter(Boolean); }
        // Split on commas not inside parentheses
        catch { amenityChips = rawPartners.split(/,(?![^(]*\))/).map(s => s.trim()).filter(Boolean); }
      }
      // Filter amenity chips that are already covered by a scraped payment (containment match)
      const scrapedLabels = paymentRows.map(p => p.service.toLowerCase().trim());
      const uniqueAmenityChips = amenityChips.filter(c => {
        const cLower = c.toLowerCase().trim();
        return !scrapedLabels.some(s => cLower === s || cLower.includes(s) || s.includes(cLower));
      });
      const amenityPills = uniqueAmenityChips.map(c => `<span class="payment-pill">${c}</span>`);
      const allPills = [...scrapedPaymentPills, ...amenityPills];
      const plansHTML = rawPlans ? `<p class="payment-plans">${rawPlans}</p>` : '';
      if (allPills.length > 0 || plansHTML) {
        paymentHTML = `
        <div class="profile-section profile-section--payment">
          <h2 class="profile-section__title">Payment Options</h2>
          ${allPills.length > 0 ? `<div class="payment-pills">${allPills.join('')}</div>` : ''}
          ${plansHTML}
        </div>`;
      }
    }

    // Miscellaneous section from amenities
    let miscHTML = '';
    if (am) {
      const TEXT_FIELDS = [
        ['in_house_specialists', 'In-house specialists'],
        ['sedation_options', 'Sedation options'],
        ['calming_amenities', 'Comfort amenities'],
        ['parking_access', 'Parking'],
        ['special_offers', 'Special offers'],
      ];
      const BOOL_FIELDS = [
        ['wheelchair_accessible', 'Wheelchair accessible'],
        ['dental_anxiety_friendly', 'Dental anxiety friendly'],
        ['kids_family_friendly', 'Kids & family friendly'],
        ['online_booking', 'Online booking available'],
        ['same_day_emergency', 'Same-day emergencies'],
      ];
      const items = [];
      TEXT_FIELDS.forEach(([key, label]) => {
        if (am[key]) items.push(`<div class="misc-item"><span class="misc-item__label">${label}</span><span class="misc-item__value">${am[key]}</span></div>`);
      });
      BOOL_FIELDS.forEach(([key, label]) => {
        if (am[key] === true) items.push(`<div class="misc-item"><span class="misc-item__label">${label}</span><span class="misc-item__value misc-item__value--yes">✓ Yes</span></div>`);
        else if (am[key] === false) items.push(`<div class="misc-item"><span class="misc-item__label">${label}</span><span class="misc-item__value misc-item__value--no">✗ No</span></div>`);
      });
      if (items.length > 0) {
        miscHTML = `
        <div class="profile-section profile-section--misc">
          <h2 class="profile-section__title">Miscellaneous</h2>
          <div class="misc-list">${items.join('')}</div>
        </div>`;
      }
    }

    profileContainer.innerHTML = `
      <div class="profile-main">
        ${dentist.description ? `
        <div class="profile-section profile-section--about">
          <h2 class="profile-section__title">About</h2>
          <div class="profile-desc">${dentist.description}</div>
        </div>` : ''}

        <div class="profile-section profile-section--services">
          <h2 class="profile-section__title">Services</h2>
          <div class="service-list">${servicesHTML}</div>
        </div>

        ${pricingHTML}

        ${paymentHTML}

        ${hoursHTML ? `
        <div class="profile-section profile-section--hours">
          <h2 class="profile-section__title">Opening Hours</h2>
          <div class="hours-table-wrap"><table class="hours-table">${hoursHTML}</table></div>
        </div>` : ''}

        ${teamHTML}

        ${miscHTML}

        <div class="profile-section profile-section--reviews">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.5rem;margin-bottom:1rem;">
            <h2 class="profile-section__title" style="margin-bottom:0;">Reviews${dentist.reviewCount ? ` (${dentist.reviewCount})` : ''}</h2>
            <div style="display:flex;align-items:center;gap:.75rem;flex-wrap:wrap;">
              ${(dentist.reviews || []).length > 1 ? `
              <div style="display:flex;align-items:center;gap:.4rem;">
                <div style="display:flex;gap:2px;background:var(--clr-gray-100);border-radius:6px;padding:2px;flex-shrink:0;" role="group" aria-label="Review filter">
                  <button id="review-tab-curated" style="font-size:.8rem;padding:.25rem .65rem;border-radius:4px;border:none;cursor:pointer;background:var(--clr-navy);color:#fff;font-weight:500;">Curated</button>
                  <button id="review-tab-all" style="font-size:.8rem;padding:.25rem .65rem;border-radius:4px;border:none;cursor:pointer;background:transparent;color:var(--clr-gray-500);">All reviews</button>
                </div>
                <button id="curated-info-btn" aria-label="What are curated reviews?" style="width:1.2rem;height:1.2rem;border-radius:50%;border:1.5px solid var(--clr-gray-300);background:transparent;color:var(--clr-gray-400);font-size:.7rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0;line-height:1;">ℹ</button>
              </div>
              <input id="review-search" type="search" placeholder="Search reviews…" style="font-size:.8rem;border:1px solid var(--clr-gray-200);border-radius:6px;padding:.3rem .6rem;color:var(--clr-gray-600);width:160px;">
              <select id="review-sort" style="font-size:.8rem;border:1px solid var(--clr-gray-200);border-radius:6px;padding:.3rem .6rem;color:var(--clr-gray-600);background:#fff;cursor:pointer;">
                <option value="newest">Newest first</option>
                <option value="oldest">Oldest first</option>
                <option value="highest">Highest rated</option>
                <option value="lowest">Lowest rated</option>
              </select>` : ''}
              ${dentist.googleMapsUrl ? `<a href="${dentist.googleMapsUrl}" target="_blank" rel="noopener" style="font-size:.8rem;color:#4285F4;text-decoration:none;font-weight:500;">★ Write a Google Review →</a>` : ''}
            </div>
          </div>
          <div id="curated-info-box" style="display:none;background:var(--clr-sky-50,#f0f7ff);border:1px solid var(--clr-sky-200,#bfdbfe);border-radius:8px;padding:.75rem 1rem;margin-bottom:.75rem;font-size:.82rem;color:var(--clr-gray-600);line-height:1.55;">
            <strong style="display:block;margin-bottom:.35rem;color:var(--clr-navy);">What are curated reviews?</strong>
            Curated reviews are a filtered selection of Google reviews designed to give a clearer picture of the genuine patient experience. We automatically remove:
            <ul style="margin:.4rem 0 0 1.1rem;padding:0;">
              <li>Reviews with no written text</li>
              <li>Very short reviews under 20 characters</li>
              <li>Duplicate reviews from the same person</li>
              <li>Identical reviews posted across multiple clinics</li>
            </ul>
            <span style="display:block;margin-top:.4rem;">Individual reviews may also be manually removed if they appear suspicious or off-topic. Switch to <em>All reviews</em> to see everything on file.</span>
          </div>
          <p id="curated-rating-note" style="font-size:.8rem;color:var(--clr-gray-400);margin-bottom:var(--sp-4);display:none;"></p>
          <div id="review-list-container"></div>
        </div>
      </div>

      <aside>
        <div class="contact-box">
          <h3 class="contact-box__title">Contact</h3>
          ${dentist.phone ? `
          <div class="contact-item">
            <div class="contact-item__icon">📞</div>
            <div class="contact-item__content">
              <a href="tel:${dentist.phone.replace(/\\s/g, '')}" style="font-weight:600;color:var(--clr-navy);text-decoration:none;">${dentist.phone}</a>
              <div style="font-size:.75rem;color:var(--clr-gray-400)">Phone</div>
            </div>
          </div>` : ''}
          ${dentist.email ? `
          <div class="contact-item">
            <div class="contact-item__icon">✉️</div>
            <div class="contact-item__content">
              <a href="mailto:${dentist.email}" style="font-weight:600;color:var(--clr-navy);text-decoration:none;">${dentist.email}</a>
              <div style="font-size:.75rem;color:var(--clr-gray-400)">Email</div>
            </div>
          </div>` : ''}
          <div class="contact-item">
            <div class="contact-item__icon">📍</div>
            <div class="contact-item__content">
              <div style="font-weight:600;color:var(--clr-navy)">${dentist.address}</div>
              <div style="font-size:.75rem;color:var(--clr-gray-400)">Address</div>
            </div>
          </div>
          ${availabilityHTML}
          ${websiteBtn}
          ${saveBtn}
          ${mapEmbed}
          ${mapLink}
          ${writeReviewBtn}
        </div>

        <div class="claim-nudge">
          <div class="claim-nudge__question">Are you the owner?</div>
          <a href="claim.html?id=${dentist.id || ''}&name=${encodeURIComponent(dentist.name)}" class="claim-nudge__link">Claim this listing →</a>
          <div class="claim-nudge__sub">Update your hours, pricing, services and availability.</div>
        </div>
      </aside>
    `;

    // Populate sticky mobile action bar in footer
    const stickyActions = document.getElementById('sticky-actions');
    if (stickyActions) {
      stickyActions.innerHTML = [
        dentist.phone ? `<a href="tel:${dentist.phone.replace(/\s/g, '')}" class="sticky-actions__btn sticky-actions__btn--call">📞 Call</a>` : '',
        dentist.website ? `<a href="${dentist.website}" target="_blank" class="sticky-actions__btn sticky-actions__btn--website">🌐 Visit Website</a>` : '',
        dentist.googleMapsUrl ? `<a href="${dentist.googleMapsUrl}" target="_blank" class="sticky-actions__btn sticky-actions__btn--directions">📍 Directions</a>` : '',
        dentist.id ? `<button id="sticky-save-btn" class="sticky-actions__btn sticky-actions__btn--save${profileIsFav ? ' sticky-actions__btn--save--active' : ''}">${profileIsFav ? '♥ Saved' : '♥ Save'}</button>` : '',
      ].filter(Boolean).join('');
    }

    // Wire up save buttons
    if (dentist.id) {
      function syncSaveBtns() {
        const isFav = getFavourites().has(dentist.id);
        const b1 = document.getElementById('profile-save-btn');
        const b2 = document.getElementById('sticky-save-btn');
        if (b1) { b1.textContent = isFav ? '♥ Saved' : '♥ Save clinic'; b1.classList.toggle('profile-save-btn--active', isFav); }
        if (b2) { b2.textContent = isFav ? '♥ Saved' : '♥ Save'; b2.classList.toggle('sticky-actions__btn--save--active', isFav); }
      }
      function onProfileSaveClick() {
        const favs = getFavourites();
        if (favs.has(dentist.id)) favs.delete(dentist.id); else favs.add(dentist.id);
        saveFavourites(favs);
        syncSaveBtns();
      }
      const b1 = document.getElementById('profile-save-btn');
      const b2 = document.getElementById('sticky-save-btn');
      if (b1) b1.addEventListener('click', onProfileSaveClick);
      if (b2) b2.addEventListener('click', onProfileSaveClick);
    }

    // Reviews — dynamic render with sort + curated/all toggle
    const allReviews = dentist.reviews || [];
    const curatedReviews = allReviews.filter(r => r.curated);
    const curatedRatingReviews = allReviews.filter(r => r.curatedRating);
    const curatedAvg = curatedRatingReviews.length
      ? (curatedRatingReviews.reduce((s, r) => s + (r.rating || 0), 0) / curatedRatingReviews.length).toFixed(1)
      : null;
    let reviewMode = 'curated';
    function parseRelDate(s) {
      if (!s) return 0;
      const m = s.match(/(\d+|a|an)\s+(day|week|month|year)/i);
      if (!m) return 0;
      const n = (m[1] === 'a' || m[1] === 'an') ? 1 : parseInt(m[1]);
      const mult = { day: 1, week: 7, month: 30, year: 365 }[m[2].toLowerCase()] || 1;
      return -(n * mult);
    }
    // Build practitioner name patterns for review → team card linking
    const _practPatterns = [];
    (dentist.practitioners || []).forEach(p => {
      const slug = p.name.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
      const cardId = `team-card-${slug}`;
      const add = pat => _practPatterns.push({ pat: pat.toLowerCase(), cardId, displayName: p.name });
      add(p.name);
      const noDr = p.name.replace(/^Dr\.?\s+/i, '');
      if (noDr !== p.name) {
        add(noDr);
        const parts = noDr.split(' ');
        if (parts.length >= 2) { add('Dr ' + parts[parts.length - 1]); add('Dr. ' + parts[parts.length - 1]); }
      }
    });
    _practPatterns.sort((a, b) => b.pat.length - a.pat.length);
    function findMentions(text) {
      const low = (text || '').toLowerCase();
      const found = [], seen = new Set();
      for (const { pat, cardId, displayName } of _practPatterns) {
        if (!seen.has(cardId) && low.includes(pat)) { found.push({ cardId, displayName }); seen.add(cardId); }
      }
      return found;
    }

    function renderReviews(order, query) {
      const container = document.getElementById('review-list-container');
      if (!container) return;
      const activeSet = reviewMode === 'curated' ? curatedReviews : allReviews;
      if (!activeSet.length) {
        container.innerHTML = `<p style="color:var(--clr-gray-400);font-size:.9rem;">No reviews yet. Be the first to leave one!</p>`;
        return;
      }
      const q = (query || '').trim().toLowerCase();
      const filtered = q
        ? activeSet.filter(r => (r.text || '').toLowerCase().includes(q) || (r.name || '').toLowerCase().includes(q))
        : activeSet;
      if (!filtered.length) {
        container.innerHTML = `<p style="color:var(--clr-gray-400);font-size:.9rem;">No reviews match "${query}".</p>`;
        return;
      }
      const sorted = [...filtered].sort((a, b) => {
        if (order === 'highest') return (b.rating || 0) - (a.rating || 0);
        if (order === 'lowest')  return (a.rating || 0) - (b.rating || 0);
        if (order === 'oldest')  return parseRelDate(a.date) - parseRelDate(b.date);
        return parseRelDate(b.date) - parseRelDate(a.date); // newest
      });
      const cards = sorted.map(r => {
        const initials = r.name.split(' ').map(w => w[0]).join('');
        const mentions = findMentions(r.text);
        const mentionHTML = mentions.length
          ? `<div class="review-card__mentions">${mentions.map(m => `<a href="#${m.cardId}" class="review-card__mention">👤 ${m.displayName}</a>`).join('')}</div>`
          : '';
        return `
          <div class="review-card">
            <div class="review-card__header">
              <div class="review-card__avatar">${initials}</div>
              <div class="review-card__info">
                <div class="review-card__name">${r.name}</div>
                <div class="review-card__date">${r.date}</div>
              </div>
              <div class="stars" style="margin-left:auto">${starsHTML(r.rating)}</div>
            </div>
            <p class="review-card__text">${r.text}</p>
            ${mentionHTML}
          </div>`;
      }).join('');
      const filterNote = q && filtered.length < activeSet.length
        ? `<p style="font-size:.8rem;color:var(--clr-sky);margin-bottom:var(--sp-4);">Showing ${filtered.length} of ${activeSet.length} reviews matching "${query}"</p>`
        : '';
      const showingNote = dentist.reviewCount > allReviews.length
        ? `<p style="font-size:.8rem;color:var(--clr-gray-400);margin-top:var(--sp-4);">Showing ${allReviews.length} of ${dentist.reviewCount} reviews.${dentist.googleMapsUrl ? ` <a href="${dentist.googleMapsUrl}" target="_blank" rel="noopener" style="color:#4285F4;text-decoration:none;">See all on Google →</a>` : ''}</p>`
        : '';
      container.innerHTML = `${filterNote}<div class="review-list">${cards}</div>${showingNote}`;
    }
    const curatedInfoBtn = document.getElementById('curated-info-btn');
    const curatedInfoBox = document.getElementById('curated-info-box');
    if (curatedInfoBtn && curatedInfoBox) {
      curatedInfoBtn.addEventListener('click', () => {
        const open = curatedInfoBox.style.display !== 'none';
        curatedInfoBox.style.display = open ? 'none' : 'block';
        curatedInfoBtn.style.background = open ? 'transparent' : 'var(--clr-sky-50,#f0f7ff)';
        curatedInfoBtn.style.borderColor = open ? 'var(--clr-gray-300)' : 'var(--clr-sky-200,#bfdbfe)';
        curatedInfoBtn.style.color = open ? 'var(--clr-gray-400)' : 'var(--clr-navy)';
      });
    }
    const ratingNote = document.getElementById('curated-rating-note');
    if (ratingNote && curatedAvg) {
      ratingNote.innerHTML = `Curated average: <strong style="color:var(--clr-navy)">${curatedAvg} ★</strong> based on ${curatedRatingReviews.length} verified reviews`;
      ratingNote.style.display = '';
    }
    renderReviews('newest', '');
    const reviewSortEl = document.getElementById('review-sort');
    const reviewSearchEl = document.getElementById('review-search');
    const tabCurated = document.getElementById('review-tab-curated');
    const tabAll = document.getElementById('review-tab-all');
    function refreshReviews() {
      renderReviews(reviewSortEl ? reviewSortEl.value : 'newest', reviewSearchEl ? reviewSearchEl.value : '');
    }
    function setReviewTab(mode) {
      reviewMode = mode;
      if (tabCurated) {
        tabCurated.style.background = mode === 'curated' ? 'var(--clr-navy)' : 'transparent';
        tabCurated.style.color = mode === 'curated' ? '#fff' : 'var(--clr-gray-500)';
        tabCurated.style.fontWeight = mode === 'curated' ? '500' : 'normal';
      }
      if (tabAll) {
        tabAll.style.background = mode === 'all' ? 'var(--clr-navy)' : 'transparent';
        tabAll.style.color = mode === 'all' ? '#fff' : 'var(--clr-gray-500)';
        tabAll.style.fontWeight = mode === 'all' ? '500' : 'normal';
      }
      const ratingNote = document.getElementById('curated-rating-note');
      if (ratingNote) ratingNote.style.display = mode === 'curated' ? '' : 'none';
      if (reviewSearchEl) reviewSearchEl.value = '';
      refreshReviews();
    }
    if (tabCurated) tabCurated.addEventListener('click', () => setReviewTab('curated'));
    if (tabAll) tabAll.addEventListener('click', () => setReviewTab('all'));
    if (reviewSortEl) reviewSortEl.addEventListener('change', refreshReviews);
    if (reviewSearchEl) {
      reviewSearchEl.addEventListener('input', refreshReviews);
      reviewSearchEl.addEventListener('search', refreshReviews); // fires when × is clicked
      reviewSearchEl.addEventListener('keyup', refreshReviews);  // fallback for any missed input events
    }

    // Photo lightbox
    const teamList = document.querySelector('.team-list');
    if (teamList) {
      if (!document.getElementById('photo-lightbox')) {
        const lb = document.createElement('div');
        lb.id = 'photo-lightbox';
        lb.innerHTML = '<div class="photo-lightbox__backdrop"></div><figure class="photo-lightbox__frame"><img class="photo-lightbox__img" alt=""><figcaption class="photo-lightbox__caption"></figcaption></figure>';
        document.body.appendChild(lb);
        lb.querySelector('.photo-lightbox__backdrop').addEventListener('click', () => lb.classList.remove('photo-lightbox--open'));
        document.addEventListener('keydown', e => { if (e.key === 'Escape') lb.classList.remove('photo-lightbox--open'); });
      }
      teamList.addEventListener('click', e => {
        const btn = e.target.closest('.team-card__photo-btn');
        if (!btn) return;
        const lb = document.getElementById('photo-lightbox');
        lb.querySelector('.photo-lightbox__img').src = btn.dataset.src;
        lb.querySelector('.photo-lightbox__img').alt = btn.dataset.name;
        lb.querySelector('.photo-lightbox__caption').textContent = btn.dataset.name;
        lb.classList.add('photo-lightbox--open');
      });

      // Hide "Read more" buttons where the bio text isn't actually clipped
      requestAnimationFrame(() => {
        teamList.querySelectorAll('.team-card__bio').forEach(bio => {
          if (bio.scrollHeight <= bio.clientHeight) {
            const btn = bio.nextElementSibling;
            if (btn && btn.classList.contains('team-card__read-more')) btn.style.display = 'none';
          }
        });
      });
    }
  }

  // ===== Hero Search =====
  const heroSearchBtn = document.getElementById('hero-search-btn');
  const heroSearchInput = document.querySelector('.hero-search__input');
  const searchSuggestions = document.getElementById('search-suggestions');

  async function fetchClinicSuggestions(q) {
    if (!q || q.length < 2) return [];
    const url = `${SUPABASE_URL}/rest/v1/dental_clinics?name=ilike.*${encodeURIComponent(q)}*&select=id,name,city,suburb_town,region&order=total_ratings.desc.nullslast&limit=7`;
    try {
      const res = await fetch(url, { headers: { 'apikey': SUPABASE_ANON_KEY, 'Authorization': `Bearer ${SUPABASE_ANON_KEY}` } });
      return res.ok ? await res.json() : [];
    } catch { return []; }
  }

  function showSuggestions(clinics) {
    if (!searchSuggestions || !clinics.length) { hideSuggestions(); return; }
    searchSuggestions.innerHTML = clinics.map(c =>
      `<div class="hero-search__suggestion" data-id="${c.id}" data-region="${encodeURIComponent(c.region)}">
        <span class="hero-search__suggestion-name">${c.name}</span>
        <span class="hero-search__suggestion-loc">${c.suburb_town ? c.suburb_town + ', ' : ''}${c.city}</span>
      </div>`
    ).join('');
    searchSuggestions.hidden = false;
    searchSuggestions.querySelectorAll('.hero-search__suggestion').forEach(el => {
      el.addEventListener('mousedown', e => {
        e.preventDefault();
        window.location.href = `dentist.html?id=${el.dataset.id}&region=${el.dataset.region}`;
      });
    });
  }

  function hideSuggestions() {
    if (searchSuggestions) searchSuggestions.hidden = true;
  }

  // ===== Homepage: Near Me Toggle + Search =====
  const nearMeBtn = document.getElementById('near-me-btn');
  const nearMeStatus = document.getElementById('near-me-status');
  const locationModalOverlay = document.getElementById('location-modal-overlay');
  const locationModalAllow = document.getElementById('location-modal-allow');
  const locationModalDeny = document.getElementById('location-modal-deny');

  let savedLat = null, savedLng = null;

  function setLocationActive(lat, lng) {
    savedLat = lat; savedLng = lng;
    if (nearMeBtn) nearMeBtn.classList.add('hero-nearby__btn--active');
    if (nearMeStatus) nearMeStatus.textContent = '';
  }

  function clearLocation() {
    savedLat = null; savedLng = null;
    if (nearMeBtn) nearMeBtn.classList.remove('hero-nearby__btn--active');
    if (nearMeStatus) nearMeStatus.textContent = '';
  }

  function requestLocation() {
    if (!navigator.geolocation) {
      nearMeStatus.textContent = 'Geolocation not supported by your browser.';
      return;
    }
    nearMeStatus.textContent = 'Getting your location...';
    navigator.geolocation.getCurrentPosition(
      pos => {
        setLocationActive(pos.coords.latitude, pos.coords.longitude);
      },
      () => {
        nearMeStatus.textContent = 'Location access denied. Please allow location in your browser.';
      }
    );
  }

  // Animated placeholder typewriter
  if (heroSearchInput) {
    const examples = [
      "Try 'Dentures in Wellington'…",
      "Try 'Orthodontics near Riccarton'…",
      "Try 'Christchurch'…",
      "Or use 'Use my location' below…",
    ];
    let exIdx = 0, charIdx = 0, erasing = false;
    function typePlaceholder() {
      if (document.activeElement === heroSearchInput || heroSearchInput.value) return;
      const target = examples[exIdx];
      if (!erasing) {
        heroSearchInput.placeholder = target.slice(0, ++charIdx);
        if (charIdx === target.length) { erasing = true; setTimeout(typePlaceholder, 2000); return; }
        setTimeout(typePlaceholder, 55);
      } else {
        heroSearchInput.placeholder = target.slice(0, --charIdx);
        if (charIdx === 0) { erasing = false; exIdx = (exIdx + 1) % examples.length; setTimeout(typePlaceholder, 400); return; }
        setTimeout(typePlaceholder, 30);
      }
    }
    setTimeout(typePlaceholder, 800);
  }

  // Autocomplete: show clinic name suggestions as user types
  let suggestTimer;
  if (heroSearchInput) {
    heroSearchInput.addEventListener('input', () => {
      clearTimeout(suggestTimer);
      const q = heroSearchInput.value.trim();
      if (q.length < 2) { hideSuggestions(); return; }
      suggestTimer = setTimeout(async () => showSuggestions(await fetchClinicSuggestions(q)), 260);
    });
    heroSearchInput.addEventListener('blur', () => setTimeout(hideSuggestions, 160));
    heroSearchInput.addEventListener('focus', () => {
      const q = heroSearchInput.value.trim();
      if (q.length >= 2) fetchClinicSuggestions(q).then(showSuggestions);
    });
  }

  function resolveLocation(locationStr) {
    const coords = typeof SUBURB_COORDS !== 'undefined' ? SUBURB_COORDS : {};
    const lower = locationStr.toLowerCase().trim();
    const entry = Object.entries(coords).find(([k]) =>
      k.toLowerCase() === lower || k.toLowerCase() === lower.split(',')[0].trim()
    );
    return entry ? { lat: entry[1][0], lng: entry[1][1], fromCache: true } : null;
  }

  async function geocodeFallback(locationStr) {
    const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(locationStr + ', New Zealand')}&format=json&limit=1&countrycodes=nz`);
    const data = await res.json();
    if (data.length > 0) return { lat: parseFloat(data[0].lat), lng: parseFloat(data[0].lon), fromCache: false };
    return null;
  }

  function normalizeService(str) {
    const t = TREATMENT_MAP[str.toLowerCase().trim()];
    return t ? t.service : str;
  }

  async function doSearch() {
    const q = heroSearchInput ? heroSearchInput.value.trim() : '';

    // Parse "service in/near location" pattern
    const locationMatch = q.match(/^(.+?)\s+(?:in|near)\s+(.+)$/i);
    const service = locationMatch ? normalizeService(locationMatch[1].trim()) : null;
    const locationStr = locationMatch ? locationMatch[2].trim() : null;

    // If explicit "X in/near Y" — geocode Y and use X as service filter
    if (locationMatch) {
      let coord = resolveLocation(locationStr);
      if (!coord) {
        if (heroSearchBtn) { heroSearchBtn.textContent = 'Searching…'; heroSearchBtn.disabled = true; }
        try { coord = await geocodeFallback(locationStr); } catch (e) {}
        if (heroSearchBtn) { heroSearchBtn.textContent = 'Search'; heroSearchBtn.disabled = false; }
      }
      if (coord) {
        window.location.href = `nearby.html?lat=${coord.lat}&lng=${coord.lng}&q=${encodeURIComponent(service)}`;
        return;
      }
    }

    // GPS active — use it
    if (savedLat !== null) {
      const qParam = q ? `&q=${encodeURIComponent(q)}` : '';
      window.location.href = `nearby.html?lat=${savedLat}&lng=${savedLng}${qParam}`;
      return;
    }

    // No GPS — try treating full query as a location or clinic name
    if (q) {
      let coord = resolveLocation(q);
      if (!coord) {
        if (heroSearchBtn) { heroSearchBtn.textContent = 'Searching…'; heroSearchBtn.disabled = true; }
        let nameResults = [];
        try {
          [coord, nameResults] = await Promise.all([
            geocodeFallback(q).catch(() => null),
            fetchClinicSuggestions(q)
          ]);
        } catch (e) {}
        if (heroSearchBtn) { heroSearchBtn.textContent = 'Search'; heroSearchBtn.disabled = false; }
        if (!coord && nameResults.length) {
          if (nameResults.length === 1) {
            window.location.href = `dentist.html?id=${nameResults[0].id}&region=${encodeURIComponent(nameResults[0].region)}`;
          } else {
            showSuggestions(nameResults);
          }
          return;
        }
      }
      if (coord) {
        window.location.href = `nearby.html?lat=${coord.lat}&lng=${coord.lng}&q=${encodeURIComponent(q)}`;
        return;
      }
    }

    if (nearMeBtn) nearMeBtn.classList.add('hero-nearby__btn--nudge');
    nearMeStatus.textContent = q ? 'No results found. Try "Dentures in Wellington".' : 'Enter a clinic name, suburb, or use your location.';
    setTimeout(() => {
      if (nearMeBtn) nearMeBtn.classList.remove('hero-nearby__btn--nudge');
      nearMeStatus.textContent = '';
    }, 3000);
  }

  // "Use my location" → show modal (if location not yet granted) or clear it (if already on)
  if (nearMeBtn) {
    nearMeBtn.addEventListener('click', () => {
      if (savedLat !== null) {
        clearLocation();
        return;
      }
      if (locationModalOverlay) {
        locationModalOverlay.style.display = 'flex';
      } else {
        requestLocation();
      }
    });
  }

  if (heroSearchBtn) heroSearchBtn.addEventListener('click', doSearch);
  if (heroSearchInput) {
    heroSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') doSearch();
    });
  }

  if (locationModalOverlay) {
    locationModalAllow.addEventListener('click', () => {
      locationModalOverlay.style.display = 'none';
      requestLocation();
    });
    locationModalDeny.addEventListener('click', () => {
      locationModalOverlay.style.display = 'none';
    });
    locationModalOverlay.addEventListener('click', (e) => {
      if (e.target === locationModalOverlay) locationModalOverlay.style.display = 'none';
    });
  }

  // ===== Homepage: Dynamic Region Counts =====
  const locationCards = document.querySelectorAll('.location-card[data-region]');
  if (locationCards.length > 0) {
    fetchAllClinics().then(clinics => {
      if (!Array.isArray(clinics) || clinics.length === 0) return;

      // Update hero stat with live clinic count
      const heroStatEl = document.querySelector('.hero-stat__number');
      if (heroStatEl) {
        heroStatEl.textContent = clinics.length.toLocaleString();
      }

      const counts = {};
      const regionCityCounts = {};
      clinics.forEach(c => {
        if (c.region) counts[c.region] = (counts[c.region] || 0) + 1;
        if (c.region && c.city) {
          if (!regionCityCounts[c.region]) regionCityCounts[c.region] = {};
          regionCityCounts[c.region][c.city] = (regionCityCounts[c.region][c.city] || 0) + 1;
        }
      });

      // Largest city per region (by clinic count) — the headline city shown
      // in "whole region" tooltips, e.g. Whangārei for Northland.
      const regionLargestCity = {};
      Object.entries(regionCityCounts).forEach(([region, cityCounts]) => {
        regionLargestCity[region] = Object.entries(cityCounts).sort((a, b) => b[1] - a[1])[0][0];
      });

      // Per-region suburb frequency, excluding the largest city's own
      // suburbs — used to sample genuinely outer towns. Without excluding
      // the main city, low-clinic-count inner suburbs of that same city
      // would wrongly show up as "outer" towns.
      const regionOuterSuburbCounts = {};
      clinics.forEach(c => {
        if (!c.region || !c.suburb_town) return;
        if (c.city === regionLargestCity[c.region]) return;
        if (!regionOuterSuburbCounts[c.region]) regionOuterSuburbCounts[c.region] = {};
        regionOuterSuburbCounts[c.region][c.suburb_town] = (regionOuterSuburbCounts[c.region][c.suburb_town] || 0) + 1;
      });

      const TOWN_SAMPLE_SIZE = 10;

      locationCards.forEach(card => {
        const dbRegion = card.getAttribute('data-region');
        const suburbFilterKey = card.getAttribute('data-suburb-filter');
        const cardName = card.querySelector('.location-card__name')?.textContent || dbRegion;
        let total;
        if (suburbFilterKey && SUBURB_FILTERS[suburbFilterKey]) {
          const allowed = SUBURB_FILTERS[suburbFilterKey];
          total = clinics.filter(c => c.region === dbRegion && allowed.has(c.suburb_town)).length;

          // Hover tooltip listing the towns this card covers
          const towns = TOOLTIP_TOWN_OVERRIDES[suburbFilterKey] || [...allowed].sort();
          card.title = `Includes ${towns.join(', ')}`;
        } else {
          total = counts[dbRegion] || 0;

          if (TOOLTIP_TOWN_OVERRIDES[dbRegion]) {
            card.title = `Includes ${TOOLTIP_TOWN_OVERRIDES[dbRegion].join(', ')}`;
          } else {
            // Hover tooltip for whole-region cards: lead with the largest
            // city, then sample the least-common remaining suburbs (a proxy
            // for outer/satellite towns) so it's clear the card covers the
            // full region, not just the main city.
            const largestCity = regionLargestCity[dbRegion];
            if (largestCity) {
              const outerCounts = regionOuterSuburbCounts[dbRegion] || {};
              const allOuterTowns = Object.keys(outerCounts);
              const sample = Object.entries(outerCounts)
                .sort((a, b) => a[1] - b[1] || a[0].localeCompare(b[0]))
                .slice(0, TOWN_SAMPLE_SIZE)
                .map(([town]) => town)
                .sort();
              const more = allOuterTowns.length > sample.length ? ' and more' : '';
              const list = sample.length > 0 ? `${largestCity}, ${sample.join(', ')}` : largestCity;
              card.title = `Includes ${list}${more}`;
            }
          }
        }
        if (total > 0) {
          const countEl = card.querySelector('.location-card__count');
          if (countEl) countEl.textContent = `${total} dentists`;
        }
      });
    });
  }

})();
