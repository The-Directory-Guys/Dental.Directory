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
  // Hygienist
  'hygienist':            { service: 'Hygienist', priceType: 'hygienist' },
  'hygienists':           { service: 'Hygienist', priceType: 'hygienist' },
  'hygiene':              { service: 'Hygienist', priceType: 'hygienist' },
  'clean':                { service: 'Hygienist', priceType: 'hygienist' },
  'cleaning':             { service: 'Hygienist', priceType: 'hygienist' },
  'dental clean':         { service: 'Hygienist', priceType: 'hygienist' },
  'dental cleaning':      { service: 'Hygienist', priceType: 'hygienist' },
  'scale and polish':     { service: 'Hygienist', priceType: 'hygienist' },
  'scale and clean':      { service: 'Hygienist', priceType: 'hygienist' },
  'scale & polish':       { service: 'Hygienist', priceType: 'hygienist' },
  'scale & clean':        { service: 'Hygienist', priceType: 'hygienist' },
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
    const full = Math.floor(rating);
    const half = rating % 1 >= 0.5 ? 1 : 0;
    const empty = 5 - full - half;
    let html = '';
    for (let i = 0; i < full; i++) html += '<span>★</span>';
    if (half) html += '<span>★</span>';
    for (let i = 0; i < empty; i++) html += '<span class="empty">★</span>';
    return html;
  }

  function getCheckupPrice(d) {
    if (!d.pricing || d.pricing.length === 0) return null;
    const checkup = d.pricing.find(p => {
      const s = p.service.toLowerCase();
      return s.includes('checkup') || s.includes('check-up') || s.includes('exam') || s.includes('consult');
    });
    if (!checkup) return null;
    const match = checkup.price.replace(/,/g, '').match(/\$(\d+)/);
    return match ? parseInt(match[1], 10) : null;
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

    // Read region from data attribute (defaults to Canterbury)
    const region = dentistGrid.dataset.region || 'Canterbury';

    // Try Supabase first, fall back to static data
    if (typeof fetchClinics === 'function') {
      allDentists = await fetchClinics(region);
    }

    // Fall back to static data if Supabase returned nothing
    if (allDentists.length === 0 && typeof dentists !== 'undefined') {
      allDentists = dentists;
    }

    // Apply suburb filter if page specifies one
    const suburbFilterKey = dentistGrid.dataset.suburbFilter;
    if (suburbFilterKey && SUBURB_FILTERS[suburbFilterKey]) {
      const allowed = SUBURB_FILTERS[suburbFilterKey];
      allDentists = allDentists.filter(d => allowed.has(d.suburb));
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

    // Build dynamic suburb filters from data
    buildSuburbFilters(allDentists);

    // Setup filtering & rendering
    let activeSuburbs = [];
    let activeServices = ['General Dentistry'];
    let minRating = 0;
    let searchQuery = '';
    let sortBy = 'name';
    let maxPrice = Infinity;
    let maxHygienistPrice = Infinity;
    let activeTreatmentPriceType = null;

    function cardHTML(d) {
      const initials = d.name.split(' ').filter(w => w.length > 0).map(w => w[0]).join('').slice(0, 2).toUpperCase();
      const servicePills = d.services.slice(0, 4).map(s =>
        `<span class="pill pill--sm">${s}</span>`
      ).join('');

      let pricingPreview = '';
      if (d.pricing && d.pricing.length > 0) {
        const previewItems = d.pricing.slice(0, 3).map(p =>
          `<div class="pricing-preview__row"><span>${p.service}</span><span class="pricing-preview__price">${p.price}</span></div>`
        ).join('');
        const moreCount = d.pricing.length > 3 ? `<div class="pricing-preview__more">+ ${d.pricing.length - 3} more services</div>` : '';
        pricingPreview = `<div class="pricing-preview">${previewItems}${moreCount}</div>`;
      }

      const ratingDisplay = d.rating ? `<span class="stars">${starsHTML(d.rating)}</span> <strong>${d.rating}</strong>` : '<span style="color:var(--clr-gray-400)">No rating yet</span>';
      const reviewText = d.reviewCount ? `💬 ${d.reviewCount} review${d.reviewCount === 1 ? '' : 's'}` : '';
      const descText = d.description || '';
      const phoneText = d.phone ? `<a href="tel:${d.phone.replace(/\\s/g, '')}" style="text-decoration:none; color:inherit;">📞 ${d.phone}</a>` : '';
      const emailText = d.email ? `<a href="mailto:${d.email}" style="text-decoration:none; color:inherit; margin-left:1rem;">✉️ Email</a>` : '';

      // Use id for Supabase records, slug for static
      const profileLink = d.id ? `dentist.html?id=${d.id}&region=${encodeURIComponent(d.region || '')}` : `dentist.html?slug=${d.slug}&region=${encodeURIComponent(d.region || '')}`;

      return `
        <article class="dentist-card" data-suburb="${d.suburb}" data-rating="${d.rating || 0}" data-name="${d.name}">
          <div class="dentist-card__avatar">${initials}</div>
          <div class="dentist-card__body">
            <h3 class="dentist-card__name">
              <a href="${profileLink}">${d.name}</a>
            </h3>
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
      let filtered = allDentists.filter(d => {
        if (activeSuburbs.length && !activeSuburbs.includes(d.suburb)) return false;
        if (activeServices.length && !activeServices.every(s => d.services.includes(s))) return false;
        if (d.rating < minRating) return false;
        if (searchQuery) {
          const q = searchQuery.toLowerCase();
          const matchesName = d.name.toLowerCase().includes(q);
          const matchesService = d.services.some(s => s.toLowerCase().includes(q));
          if (!matchesName && !matchesService) return false;
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
      }

      if (filtered.length === 0) {
        dentistGrid.innerHTML = `
          <div class="no-results">
            <div class="no-results__icon">🔍</div>
            <h3>No dentists found</h3>
            <p>Try adjusting your filters or search query.</p>
          </div>
        `;
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
        const totalFiltered = allDentists.filter(d => {
          if (activeSuburbs.length && !activeSuburbs.includes(d.suburb)) return false;
          if (activeServices.length && !activeServices.every(s => d.services.includes(s))) return false;
          if (d.rating < minRating) return false;
          if (searchQuery) {
          const q = searchQuery.toLowerCase();
          const matchesName = d.name.toLowerCase().includes(q);
          const matchesService = d.services.some(s => s.toLowerCase().includes(q));
          if (!matchesName && !matchesService) return false;
        }
          const price = getCheckupPrice(d);
          if (price !== null && maxPrice !== Infinity && price > maxPrice) return false;
          const hygPrice = getHygienistPrice(d);
          if (hygPrice !== null && maxHygienistPrice !== Infinity && hygPrice > maxHygienistPrice) return false;
          return true;
        }).length;
        const showingCount = Math.min(visibleCount, totalFiltered);
        if (showingCount < totalFiltered) {
          resultsCount.textContent = `Showing ${showingCount} of ${totalFiltered} dentists in ${region}`;
        } else {
          resultsCount.textContent = `Showing ${totalFiltered} dentist${totalFiltered !== 1 ? 's' : ''} in ${region}`;
        }
      }
    }

    // Reset pagination when filters change
    function renderWithReset() {
      visibleCount = ITEMS_PER_PAGE;
      render();
    }

    // Suburb filters
    document.querySelectorAll('.filter-suburb').forEach(cb => {
      cb.addEventListener('change', () => {
        activeSuburbs = Array.from(document.querySelectorAll('.filter-suburb:checked')).map(el => el.value);
        renderWithReset();
      });
    });

    // Service filters
    document.querySelectorAll('.filter-service').forEach(cb => {
      cb.addEventListener('change', () => {
        // Sync paired mobile/desktop checkbox to the same state
        document.querySelectorAll(`.filter-service[value="${cb.value}"]`).forEach(paired => {
          paired.checked = cb.checked;
        });
        activeServices = [...new Set(Array.from(document.querySelectorAll('.filter-service:checked')).map(el => el.value))];
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
        const treatment = TREATMENT_MAP[raw.trim().toLowerCase()];
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
        const treatment = TREATMENT_MAP[qLower];
        if (treatment) {
          document.querySelectorAll(`.filter-service[value="${treatment.service}"]`).forEach(cb => { cb.checked = true; });
          activeServices = [treatment.service];
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

    // Initial render
    render();
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

    // Update desktop sidebar — find by data-filter attribute, independent of DOM order
    const desktopSuburbItems = document.querySelector('.sidebar [data-filter="suburb"] .filter-group__items');
    if (desktopSuburbItems) desktopSuburbItems.innerHTML = checkboxHtml;

    // Update mobile drawer
    const mobileSuburbItems = document.querySelector('.filter-drawer [data-filter="suburb"] .filter-group__items');
    if (mobileSuburbItems) mobileSuburbItems.innerHTML = checkboxHtml;
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

  async function initProfile() {
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    const slug = params.get('slug');
    const regionParam = params.get('region');
    let dentist = null;

    // Set back button immediately from URL param so it works before async fetch completes
    if (regionParam) setBackButton(regionParam);

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

    // Update hero
    const heroName = document.getElementById('profile-name');
    const heroMeta = document.getElementById('profile-meta');
    if (heroName) heroName.textContent = dentist.name;
    if (heroMeta) {
      const ratingHtml = dentist.rating
        ? `<span class="stars stars--lg">${starsHTML(dentist.rating)}</span> <strong style="color:#fff">${dentist.rating}</strong> <span>(${dentist.reviewCount} review${dentist.reviewCount === 1 ? '' : 's'})</span>`
        : '<span style="color:var(--clr-gray-300)">No rating yet</span>';
      heroMeta.innerHTML = `
        <span class="profile-hero__meta-item">${ratingHtml}</span>
        <span class="profile-hero__meta-item">📍 ${dentist.address}</span>
      `;
    }

    // Update Back button with confirmed region from loaded data
    if (dentist.region) setBackButton(dentist.region);

    document.title = `${dentist.name} | Dental Compare`;

    const serviceIcons = {
      'General Dentistry': '🦷', 'Cosmetic': '✨', 'Teeth Whitening': '💎',
      'Implants': '🔩', 'Orthodontics': '😁', 'Emergency': '🚨'
    };

    const servicesHTML = dentist.services.map(s => `
      <div class="service-item">
        <div class="service-item__icon">${serviceIcons[s] || '🦷'}</div>
        <div class="service-item__content">
          <div class="service-item__name">${s}</div>
          <div class="service-item__desc">Professional ${s.toLowerCase()} services tailored to your needs.</div>
        </div>
      </div>
    `).join('');

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

    // Reviews
    const reviewsHTML = (dentist.reviews || []).map(r => {
      const initials = r.name.split(' ').map(w => w[0]).join('');
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
        </div>
      `;
    }).join('');

    // Pricing table — always show, with empty state if no data
    let pricingHTML = '';
    if (dentist.pricing && dentist.pricing.length > 0) {
      const rows = dentist.pricing.map(p => {
        const notesHtml = p.notes ? `<div class="pricing-note">${p.notes}</div>` : '';
        return `<tr><td>${p.service}${notesHtml}</td><td>${p.price}</td></tr>`;
      }).join('');
      pricingHTML = `
        <div class="profile-section">
          <h2 class="profile-section__title">Pricing</h2>
          <p style="font-size:.875rem;color:var(--clr-gray-500);margin-bottom:1rem;">Prices are indicative and may vary. Contact the practice for an exact quote.</p>
          <div style="overflow-x: auto;">
            <table class="pricing-table">
              <thead><tr><th>Service</th><th>Price (NZD)</th></tr></thead>
              <tbody>${rows}</tbody>
            </table>
          </div>
        </div>
      `;
    } else {
      // Empty pricing state — placeholder for when we don't have data yet
      pricingHTML = `
        <div class="profile-section">
          <h2 class="profile-section__title">Pricing</h2>
          <div class="pricing-empty">
            <div class="pricing-empty__icon">💰</div>
            <h4 class="pricing-empty__title">Pricing Coming Soon</h4>
            <p class="pricing-empty__text">We're working on getting pricing information for this practice. In the meantime, contact them directly for a quote.</p>
            ${dentist.phone ? `<a href="tel:${dentist.phone.replace(/\s/g, '')}" class="btn btn--outline btn--sm pricing-empty__btn">📞 Call for Pricing</a>` : ''}
            ${dentist.website ? `<a href="${dentist.website}" target="_blank" class="btn btn--outline btn--sm pricing-empty__btn">🌐 Check Website</a>` : ''}
          </div>
        </div>
      `;
    }

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

    profileContainer.innerHTML = `
      <div class="profile-main">
        ${dentist.description ? `
        <div class="profile-section">
          <h2 class="profile-section__title">About</h2>
          <p>${dentist.description}</p>
        </div>` : ''}

        <div class="profile-section">
          <h2 class="profile-section__title">Services</h2>
          <div class="service-list">${servicesHTML}</div>
        </div>

        ${pricingHTML}

        ${hoursHTML ? `
        <div class="profile-section">
          <h2 class="profile-section__title">Opening Hours</h2>
          <div class="hours-table-wrap"><table class="hours-table">${hoursHTML}</table></div>
        </div>` : ''}

        <div class="profile-section">
          <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.5rem;margin-bottom:1rem;">
            <h2 class="profile-section__title" style="margin-bottom:0;">Reviews${dentist.reviewCount ? ` (${dentist.reviewCount})` : ''}</h2>
            ${dentist.googleMapsUrl ? `<a href="${dentist.googleMapsUrl}" target="_blank" rel="noopener" style="font-size:.8rem;color:#4285F4;text-decoration:none;font-weight:500;">★ Write a Google Review →</a>` : ''}
          </div>
          ${reviewsHTML
            ? `<div class="review-list">${reviewsHTML}</div>`
            : `<p style="color:var(--clr-gray-400);font-size:.9rem;">No reviews yet. Be the first to leave one!</p>`
          }
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
          ${websiteBtn}
          ${mapEmbed}
          ${mapLink}
          ${writeReviewBtn}
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
      ].filter(Boolean).join('');
    }
  }

  // ===== Hero Search =====
  const heroSearchBtn = document.getElementById('hero-search-btn');
  const heroSearchInput = document.querySelector('.hero-search__input');

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

    // No GPS — try treating full query as a location
    if (q) {
      let coord = resolveLocation(q);
      if (!coord) {
        if (heroSearchBtn) { heroSearchBtn.textContent = 'Searching…'; heroSearchBtn.disabled = true; }
        try { coord = await geocodeFallback(q); } catch (e) {}
        if (heroSearchBtn) { heroSearchBtn.textContent = 'Search'; heroSearchBtn.disabled = false; }
      }
      if (coord) {
        window.location.href = `nearby.html?lat=${coord.lat}&lng=${coord.lng}&q=${encodeURIComponent(q)}`;
        return;
      }
    }

    if (nearMeBtn) nearMeBtn.classList.add('hero-nearby__btn--nudge');
    nearMeStatus.textContent = q ? 'Location not found. Try "Dentures in Wellington".' : 'Enter a suburb, or use your location.';
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
          card.title = `${cardName}: ${towns.join(', ')}`;
        } else {
          total = counts[dbRegion] || 0;

          if (TOOLTIP_TOWN_OVERRIDES[dbRegion]) {
            card.title = `${cardName} region: includes ${TOOLTIP_TOWN_OVERRIDES[dbRegion].join(', ')}`;
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
              card.title = `${cardName} region: includes ${list}${more}`;
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
