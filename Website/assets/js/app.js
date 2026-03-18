// NZ Dental — App Logic
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

  // ===== Listings Page Logic =====
  const dentistGrid = document.getElementById('dentist-grid');
  const resultsCount = document.getElementById('results-count');

  if (dentistGrid && typeof dentists !== 'undefined') {
    let activeSuburbs = [];
    let activeServices = [];
    let minRating = 0;
    let searchQuery = '';
    let sortBy = 'rating';
    let maxPrice = 200;

    // Helper: extract the first dollar amount from checkup pricing
    function getCheckupPrice(d) {
      if (!d.pricing) return null;
      const checkup = d.pricing.find(p => p.service.toLowerCase().includes('checkup'));
      if (!checkup) return null;
      const match = checkup.price.replace(/,/g, '').match(/\$(\d+)/);
      return match ? parseInt(match[1], 10) : null;
    }

    // Render star HTML
    function starsHTML(rating) {
      const full = Math.floor(rating);
      const half = rating % 1 >= 0.5 ? 1 : 0;
      const empty = 5 - full - half;
      let html = '';
      for (let i = 0; i < full; i++) html += '<span>★</span>';
      if (half) html += '<span>★</span>';
      for (let i = 0; i < empty; i++) html += '<span class="empty">★</span>';
      return html;
    }

    // Build a single card
    function cardHTML(d) {
      const initials = d.name.split(' ').map(w => w[0]).join('').slice(0, 2);
      const servicePills = d.services.slice(0, 4).map(s =>
        `<span class="pill pill--sm">${s}</span>`
      ).join('');

      // Pricing preview — show first 3 items
      let pricingPreview = '';
      if (d.pricing && d.pricing.length > 0) {
        const previewItems = d.pricing.slice(0, 3).map(p =>
          `<div class="pricing-preview__row"><span>${p.service}</span><span class="pricing-preview__price">${p.price}</span></div>`
        ).join('');
        const moreCount = d.pricing.length > 3 ? `<div class="pricing-preview__more">+ ${d.pricing.length - 3} more services</div>` : '';
        pricingPreview = `<div class="pricing-preview">${previewItems}${moreCount}</div>`;
      }

      return `
        <article class="dentist-card" data-suburb="${d.suburb}" data-services='${JSON.stringify(d.services)}' data-rating="${d.rating}" data-name="${d.name}">
          <div class="dentist-card__avatar">${initials}</div>
          <div class="dentist-card__body">
            <h3 class="dentist-card__name">
              <a href="dentist.html?slug=${d.slug}">${d.name}</a>
            </h3>
            <div class="dentist-card__meta">
              <span class="dentist-card__meta-item">
                <span class="stars">${starsHTML(d.rating)}</span>
                <strong>${d.rating}</strong>
              </span>
              <span class="dentist-card__meta-item">📍 ${d.suburb}</span>
              <span class="dentist-card__meta-item">💬 ${d.reviewCount} reviews</span>
            </div>
            <p class="dentist-card__desc">${d.description}</p>
            <div class="dentist-card__services">${servicePills}</div>
            ${pricingPreview}
            <div class="dentist-card__footer">
              <span class="dentist-card__phone">📞 ${d.phone}</span>
              <a href="dentist.html?slug=${d.slug}" class="btn btn--primary">View Profile</a>
            </div>
          </div>
        </article>
      `;
    }

    // Filter & render
    function render() {
      let filtered = dentists.filter(d => {
        if (activeSuburbs.length && !activeSuburbs.includes(d.suburb)) return false;
        if (activeServices.length && !activeServices.some(s => d.services.includes(s))) return false;
        if (d.rating < minRating) return false;
        if (searchQuery && !d.name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
        // Price filter
        const price = getCheckupPrice(d);
        if (price !== null && price > maxPrice) return false;
        return true;
      });

      // Sort
      if (sortBy === 'rating') {
        filtered.sort((a, b) => b.rating - a.rating);
      } else if (sortBy === 'name') {
        filtered.sort((a, b) => a.name.localeCompare(b.name));
      } else if (sortBy === 'reviews') {
        filtered.sort((a, b) => b.reviewCount - a.reviewCount);
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
        dentistGrid.innerHTML = filtered.map(cardHTML).join('');
      }

      if (resultsCount) {
        resultsCount.textContent = `Showing ${filtered.length} dentist${filtered.length !== 1 ? 's' : ''} in Christchurch`;
      }
    }

    // Suburb filters
    document.querySelectorAll('.filter-suburb').forEach(cb => {
      cb.addEventListener('change', () => {
        activeSuburbs = Array.from(document.querySelectorAll('.filter-suburb:checked')).map(el => el.value);
        render();
      });
    });

    // Service filters
    document.querySelectorAll('.filter-service').forEach(cb => {
      cb.addEventListener('change', () => {
        activeServices = Array.from(document.querySelectorAll('.filter-service:checked')).map(el => el.value);
        render();
      });
    });

    // Rating filter
    document.querySelectorAll('.filter-rating').forEach(cb => {
      cb.addEventListener('change', () => {
        const checked = Array.from(document.querySelectorAll('.filter-rating:checked')).map(el => parseFloat(el.value));
        minRating = checked.length ? Math.min(...checked) : 0;
        render();
      });
    });

    // Search
    const searchInput = document.getElementById('listings-search');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        searchQuery = e.target.value;
        render();
      });
    }

    // Sort
    const sortSelect = document.getElementById('sort-select');
    if (sortSelect) {
      sortSelect.addEventListener('change', (e) => {
        sortBy = e.target.value;
        render();
      });
    }

    // Price slider (sync desktop & mobile)
    const desktopSlider = document.getElementById('desktop-price-range');
    const mobileSlider = document.getElementById('mobile-price-range');
    const desktopLabel = document.getElementById('desktop-price-value');
    const mobileLabel = document.getElementById('mobile-price-value');

    function updatePriceSlider(value) {
      maxPrice = parseInt(value, 10);
      const label = maxPrice >= 200 ? 'Any price' : `Up to $${maxPrice}`;
      if (desktopSlider) desktopSlider.value = maxPrice;
      if (mobileSlider) mobileSlider.value = maxPrice;
      if (desktopLabel) desktopLabel.textContent = label;
      if (mobileLabel) mobileLabel.textContent = label;
      render();
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
  if (profileContainer && typeof dentists !== 'undefined') {
    const params = new URLSearchParams(window.location.search);
    const slug = params.get('slug');
    const dentist = dentists.find(d => d.slug === slug);

    if (!dentist) {
      profileContainer.innerHTML = `
        <div class="no-results">
          <div class="no-results__icon">😕</div>
          <h3>Dentist not found</h3>
          <p>The profile you're looking for doesn't exist. <a href="christchurch.html" style="color: var(--clr-teal);">Go back to listings</a>.</p>
        </div>
      `;
      return;
    }

    // Star HTML
    function starsHTML(rating) {
      const full = Math.floor(rating);
      const empty = 5 - full;
      let html = '';
      for (let i = 0; i < full; i++) html += '<span>★</span>';
      for (let i = 0; i < empty; i++) html += '<span class="empty">★</span>';
      return html;
    }

    // Update hero
    const heroName = document.getElementById('profile-name');
    const heroMeta = document.getElementById('profile-meta');
    if (heroName) heroName.textContent = dentist.name;
    if (heroMeta) {
      heroMeta.innerHTML = `
        <span class="profile-hero__meta-item">
          <span class="stars stars--lg">${starsHTML(dentist.rating)}</span>
          <strong style="color:#fff">${dentist.rating}</strong>
          <span>(${dentist.reviewCount} reviews)</span>
        </span>
        <span class="profile-hero__meta-item">📍 ${dentist.suburb}, Christchurch</span>
        <span class="profile-hero__meta-item">📍 ${dentist.address}</span>
      `;
    }

    // Update page title
    document.title = `${dentist.name} | NZ Dental`;

    // Service icons map
    const serviceIcons = {
      'General Dentistry': '🦷',
      'Cosmetic': '✨',
      'Teeth Whitening': '💎',
      'Implants': '🔩',
      'Orthodontics': '😁',
      'Emergency': '🚨'
    };

    // Build profile content
    const servicesHTML = dentist.services.map(s => `
      <div class="service-item">
        <div class="service-item__icon">${serviceIcons[s] || '🦷'}</div>
        <div>
          <div class="service-item__name">${s}</div>
          <div class="service-item__desc">Professional ${s.toLowerCase()} services tailored to your needs.</div>
        </div>
      </div>
    `).join('');

    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
    const today = days[new Date().getDay() === 0 ? 6 : new Date().getDay() - 1];
    const hoursHTML = days.map(day => `
      <tr class="${day === today ? 'today' : ''}">
        <td>${day}</td>
        <td>${dentist.hours[day]}</td>
      </tr>
    `).join('');

    const reviewsHTML = dentist.reviews.map(r => {
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

    // Build pricing table
    let pricingHTML = '';
    if (dentist.pricing && dentist.pricing.length > 0) {
      const rows = dentist.pricing.map(p => `
              <tr>
                <td>${p.service}</td>
                <td>${p.price}</td>
              </tr>
            `).join('');
      pricingHTML = `
              <div class="profile-section">
                <h2 class="profile-section__title">Pricing</h2>
                <p style="font-size:.875rem;color:var(--clr-gray-500);margin-bottom:1rem;">Prices are indicative and may vary. Contact the practice for an exact quote.</p>
                <table class="pricing-table">
                  <thead>
                    <tr><th>Service</th><th>Price (NZD)</th></tr>
                  </thead>
                  <tbody>${rows}</tbody>
                </table>
              </div>
            `;
    }

    profileContainer.innerHTML = `
      <div class="profile-main">
        <div class="profile-section">
          <h2 class="profile-section__title">About</h2>
          <p>${dentist.description}</p>
        </div>

        <div class="profile-section">
          <h2 class="profile-section__title">Services</h2>
          <div class="service-list">${servicesHTML}</div>
        </div>

        ${pricingHTML}

        <div class="profile-section">
          <h2 class="profile-section__title">Opening Hours</h2>
          <table class="hours-table">${hoursHTML}</table>
        </div>

        <div class="profile-section">
          <h2 class="profile-section__title">Reviews (${dentist.reviewCount})</h2>
          <div class="review-list">${reviewsHTML}</div>
        </div>
      </div>

      <aside>
        <div class="contact-box">
          <h3 class="contact-box__title">Contact</h3>
          <div class="contact-item">
            <div class="contact-item__icon">📞</div>
            <div>
              <div style="font-weight:600;color:var(--clr-navy)">${dentist.phone}</div>
              <div style="font-size:.75rem;color:var(--clr-gray-400)">Phone</div>
            </div>
          </div>
          <div class="contact-item">
            <div class="contact-item__icon">✉️</div>
            <div>
              <div style="font-weight:600;color:var(--clr-navy)">${dentist.email}</div>
              <div style="font-size:.75rem;color:var(--clr-gray-400)">Email</div>
            </div>
          </div>
          <div class="contact-item">
            <div class="contact-item__icon">📍</div>
            <div>
              <div style="font-weight:600;color:var(--clr-navy)">${dentist.address}</div>
              <div style="font-size:.75rem;color:var(--clr-gray-400)">Address</div>
            </div>
          </div>
          <a href="${dentist.website}" target="_blank" class="btn btn--primary btn--block">Visit Website ↗</a>
          <div class="map-placeholder">📍 Map — Coming Soon</div>
        </div>
      </aside>
    `;
  }

  // ===== Hero Search Redirect =====
  const heroSearchBtn = document.querySelector('.hero-search__btn');
  if (heroSearchBtn) {
    heroSearchBtn.addEventListener('click', () => {
      window.location.href = 'christchurch.html';
    });
  }

  const heroSearchInput = document.querySelector('.hero-search__input');
  if (heroSearchInput) {
    heroSearchInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        window.location.href = 'christchurch.html';
      }
    });
  }

})();
