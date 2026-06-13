// Dental Compare — App Logic
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
      'Woolston','Avonhead','Hillmorton','Seaview','Cashmere','Sockburn','Halswell',
      'Bryndwr','Richmond','Redwood','Riccarton (Upper)','Somerfield','Hoon Hay',
      'Phillipstown','Ferrymead','Casebrook','Northcote','Ilam','Waltham','Addington',
      'North New Brighton','Redcliffs','Fendalton','Yaldhurst',
      'Kaiapoi','Prebbleton','Rangiora','Rolleston','Lincoln'
    ]),
    'wider-canterbury': new Set([
      'Ashburton','Timaru','Darfield','Geraldine','Kaikōura','Oxford','Temuka'
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
      'Musselburgh','North East Valley','Kaikorai','Mornington','South Dunedin'
    ]),
    'wider-otago': new Set([
      'Queenstown','Frankton','Wānaka','Alexandra','Oamaru','Cromwell',
      'Balclutha','Ranfurly','Milton','Palmerston'
    ])
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
    let activeServices = [];
    let minRating = 0;
    let searchQuery = '';
    let sortBy = 'rating';
    let maxPrice = Infinity;

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
      const reviewText = d.reviewCount ? `💬 ${d.reviewCount} reviews` : '';
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
        return true;
      });

      if (sortBy === 'rating') {
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
        searchQuery = e.target.value;
        renderWithReset();
      });
      // Pre-fill from ?q= URL param (passed by home page search)
      const urlQ = new URLSearchParams(window.location.search).get('q');
      if (urlQ) {
        searchInput.value = urlQ;
        searchQuery = urlQ;
        // If the query matches a service checkbox exactly, tick it and clear the text search
        const matchingService = Array.from(document.querySelectorAll('.filter-service'))
          .find(cb => cb.value.toLowerCase() === urlQ.toLowerCase());
        if (matchingService) {
          matchingService.checked = true;
          // Sync the paired mobile/desktop checkbox too
          document.querySelectorAll(`.filter-service[value="${matchingService.value}"]`).forEach(cb => cb.checked = true);
          activeServices = [matchingService.value];
          searchInput.value = '';
          searchQuery = '';
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
      const label = maxPrice === Infinity ? 'Any price' : `Up to $${maxPrice}`;
      if (desktopSlider) desktopSlider.value = maxPrice;
      if (mobileSlider) mobileSlider.value = maxPrice;
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
        ? `<span class="stars stars--lg">${starsHTML(dentist.rating)}</span> <strong style="color:#fff">${dentist.rating}</strong> <span>(${dentist.reviewCount} reviews)</span>`
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
        <div>
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
            <div>
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
          <table class="hours-table">${hoursHTML}</table>
        </div>` : ''}

        ${reviewsHTML ? `
        <div class="profile-section">
          <h2 class="profile-section__title">Reviews (${dentist.reviewCount})</h2>
          <div class="review-list">${reviewsHTML}</div>
        </div>` : ''}
      </div>

      <aside>
        <div class="contact-box">
          <h3 class="contact-box__title">Contact</h3>
          ${dentist.phone ? `
          <div class="contact-item">
            <div class="contact-item__icon">📞</div>
            <div>
              <a href="tel:${dentist.phone.replace(/\\s/g, '')}" style="font-weight:600;color:var(--clr-navy);text-decoration:none;">${dentist.phone}</a>
              <div style="font-size:.75rem;color:var(--clr-gray-400)">Phone</div>
            </div>
          </div>` : ''}
          ${dentist.email ? `
          <div class="contact-item">
            <div class="contact-item__icon">✉️</div>
            <div>
              <a href="mailto:${dentist.email}" style="font-weight:600;color:var(--clr-navy);text-decoration:none;">${dentist.email}</a>
              <div style="font-size:.75rem;color:var(--clr-gray-400)">Email</div>
            </div>
          </div>` : ''}
          <div class="contact-item">
            <div class="contact-item__icon">📍</div>
            <div>
              <div style="font-weight:600;color:var(--clr-navy)">${dentist.address}</div>
              <div style="font-size:.75rem;color:var(--clr-gray-400)">Address</div>
            </div>
          </div>
          ${websiteBtn}
          ${mapEmbed}
          ${mapLink}
        </div>
      </aside>
    `;
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

  async function doSearch() {
    const q = heroSearchInput ? heroSearchInput.value.trim() : '';

    if (savedLat !== null) {
      const qParam = q ? `&q=${encodeURIComponent(q)}` : '';
      window.location.href = `nearby.html?lat=${savedLat}&lng=${savedLng}${qParam}`;
      return;
    }

    if (q) {
      if (heroSearchBtn) { heroSearchBtn.textContent = 'Searching…'; heroSearchBtn.disabled = true; }
      try {
        const res = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q + ', New Zealand')}&format=json&limit=1&countrycodes=nz`);
        const data = await res.json();
        if (data.length > 0) {
          window.location.href = `nearby.html?lat=${data[0].lat}&lng=${data[0].lon}&q=${encodeURIComponent(q)}`;
          return;
        }
      } catch (e) {}
      if (heroSearchBtn) { heroSearchBtn.textContent = 'Search'; heroSearchBtn.disabled = false; }
    }

    if (nearMeBtn) nearMeBtn.classList.add('hero-nearby__btn--nudge');
    nearMeStatus.textContent = q ? 'Location not found. Try enabling your location.' : 'Enable your location to search.';
    setTimeout(() => {
      if (nearMeBtn) nearMeBtn.classList.remove('hero-nearby__btn--nudge');
      nearMeStatus.textContent = '';
    }, 2000);
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
      if (heroStatEl && heroStatEl.textContent.includes('1,100')) {
        heroStatEl.textContent = clinics.length.toLocaleString();
      }

      const counts = {};
      clinics.forEach(c => {
        if (c.region) counts[c.region] = (counts[c.region] || 0) + 1;
      });

      locationCards.forEach(card => {
        const dbRegion = card.getAttribute('data-region');
        const suburbFilterKey = card.getAttribute('data-suburb-filter');
        let total;
        if (suburbFilterKey && SUBURB_FILTERS[suburbFilterKey]) {
          const allowed = SUBURB_FILTERS[suburbFilterKey];
          total = clinics.filter(c => c.region === dbRegion && allowed.has(c.suburb_town)).length;
        } else {
          total = counts[dbRegion] || 0;
        }
        if (total > 0) {
          const countEl = card.querySelector('.location-card__count');
          if (countEl) countEl.textContent = `${total} dentists`;
        }
      });
    });
  }

})();
