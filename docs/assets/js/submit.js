(function () {
  'use strict';

  if (!document.getElementById('profile-content')) return;

  const SUPABASE_URL = 'https://ankyjpgcocsvvtyyymys.supabase.co';
  const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFua3lqcGdjb2NzdnZ0eXl5bXlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4MTM1MTQsImV4cCI6MjA4OTM4OTUxNH0.SXxTLBdiNVSEDXy95yU0x0ctYFOjIby8hZbJ7B1LPK8';
  const USERNAME_KEY = 'dc_username';

  const TYPES = [
    { value: 'checkup',     label: 'Checkup price',        isPrice: true,  placeholder: null },
    { value: 'scale_clean', label: 'Scale & clean price',  isPrice: true,  placeholder: null },
    { value: 'hygienist',   label: 'Hygienist price',      isPrice: true,  placeholder: null },
    { value: 'hours',       label: 'Opening hours',        isPrice: false, placeholder: 'e.g. Mon–Fri 8am–5pm, Sat 9am–1pm' },
    { value: 'phone',       label: 'Phone number',         isPrice: false, placeholder: 'e.g. 04 123 4567' },
    { value: 'other',       label: 'Other correction',     isPrice: false, placeholder: 'e.g. New website is dentalclinic.co.nz' },
  ];

  const CSS = `
    #sub-overlay {
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,.5);
      z-index: 900;
      align-items: center;
      justify-content: center;
      padding: 1rem;
    }
    #sub-modal {
      background: #fff;
      border-radius: 16px;
      padding: 2rem;
      width: min(460px, 100%);
      max-height: 90vh;
      overflow-y: auto;
      box-shadow: 0 12px 48px rgba(0,0,0,.22);
      position: relative;
    }
    #sub-close {
      position: absolute;
      top: 1rem;
      right: 1rem;
      background: none;
      border: none;
      font-size: 1.125rem;
      cursor: pointer;
      color: #94a3b8;
      line-height: 1;
      padding: .25rem;
    }
    #sub-close:hover { color: #475569; }
    .sub-h3 {
      margin: 0 0 .375rem;
      font-size: 1.125rem;
      font-weight: 700;
      color: var(--clr-navy, #0f2a4a);
    }
    .sub-lead {
      font-size: .875rem;
      color: #64748b;
      margin: 0 0 1.25rem;
    }
    .sub-label {
      display: block;
      font-size: .8125rem;
      font-weight: 600;
      color: #374151;
      margin-bottom: .35rem;
    }
    .sub-label .sub-optional {
      font-weight: 400;
      color: #94a3b8;
    }
    .sub-input, .sub-select, .sub-textarea {
      width: 100%;
      box-sizing: border-box;
      padding: .625rem .875rem;
      border: 1.5px solid #e2e8f0;
      border-radius: 8px;
      font-size: .9375rem;
      font-family: inherit;
      color: #1e293b;
      background: #fff;
      outline: none;
      transition: border-color .15s;
    }
    .sub-input:focus, .sub-select:focus, .sub-textarea:focus {
      border-color: var(--clr-teal, #0ea5e9);
    }
    .sub-textarea { resize: vertical; }
    .sub-field { margin-bottom: 1rem; }
    .sub-err {
      font-size: .8125rem;
      color: #dc2626;
      margin: .35rem 0 0;
      display: none;
    }
    .sub-btn-primary {
      display: block;
      width: 100%;
      margin-top: 1rem;
      padding: .75rem;
      background: var(--clr-teal, #0ea5e9);
      color: #fff;
      border: none;
      border-radius: 8px;
      font-size: .9375rem;
      font-weight: 600;
      cursor: pointer;
      font-family: inherit;
      transition: background .15s;
    }
    .sub-btn-primary:hover { background: #0284c7; }
    .sub-btn-primary:disabled { opacity: .6; cursor: default; }
    .sub-done-wrap {
      text-align: center;
      padding: 1rem 0 .5rem;
    }
    .sub-done-emoji { font-size: 2.75rem; margin-bottom: .75rem; }
    .sub-done-wrap h3 { color: var(--clr-navy, #0f2a4a); margin: 0 0 .5rem; }
    .sub-done-wrap p { color: #64748b; font-size: .9375rem; margin: 0 0 1.25rem; }
    .sub-done-link {
      display: inline-block;
      background: var(--clr-navy, #0f2a4a);
      color: #fff;
      text-decoration: none;
      border-radius: 8px;
      padding: .625rem 1.25rem;
      font-weight: 600;
      font-size: .9375rem;
      transition: opacity .15s;
    }
    .sub-done-link:hover { opacity: .85; }
    @media (max-width: 480px) {
      #sub-modal { padding: 1.5rem; }
    }
  `;

  function injectStyles() {
    if (document.getElementById('sub-styles')) return;
    const style = document.createElement('style');
    style.id = 'sub-styles';
    style.textContent = CSS;
    document.head.appendChild(style);
  }

  function buildModal() {
    if (document.getElementById('sub-overlay')) return;
    injectStyles();

    const typeOptions = TYPES.map(t =>
      `<option value="${t.value}" data-is-price="${t.isPrice}" data-placeholder="${t.placeholder || ''}">${t.label}</option>`
    ).join('');

    const el = document.createElement('div');
    el.id = 'sub-overlay';
    el.setAttribute('role', 'dialog');
    el.setAttribute('aria-modal', 'true');
    el.innerHTML = `
      <div id="sub-modal">
        <button id="sub-close" aria-label="Close">&#x2715;</button>

        <div id="sub-step-username">
          <h3 class="sub-h3">Choose a display name</h3>
          <p class="sub-lead">This appears on the <a href="leaderboard.html" target="_blank" style="color:var(--clr-teal,#0ea5e9);">contributor leaderboard</a> so others can recognise your help.</p>
          <div class="sub-field">
            <label class="sub-label" for="sub-username-input">Display name</label>
            <input id="sub-username-input" class="sub-input" type="text" maxlength="30" placeholder="e.g. Wellington Wanderer" autocomplete="off">
            <p class="sub-err" id="sub-username-err">Please enter a display name.</p>
          </div>
          <button class="sub-btn-primary" id="sub-username-next">Continue &rarr;</button>
        </div>

        <div id="sub-step-form" style="display:none;">
          <h3 class="sub-h3">Submit information</h3>
          <p class="sub-lead" id="sub-clinic-name"></p>
          <div class="sub-field">
            <label class="sub-label" for="sub-type">What are you submitting?</label>
            <select id="sub-type" class="sub-select">${typeOptions}</select>
          </div>
          <div class="sub-field" id="sub-price-row">
            <label class="sub-label" for="sub-price">Price (NZD $)</label>
            <input id="sub-price" class="sub-input" type="number" min="0" max="9999" placeholder="e.g. 95">
          </div>
          <div class="sub-field" id="sub-value-row" style="display:none;">
            <label class="sub-label" for="sub-value">Value</label>
            <input id="sub-value" class="sub-input" type="text">
          </div>
          <div class="sub-field">
            <label class="sub-label" for="sub-notes">Notes <span class="sub-optional">(optional)</span></label>
            <textarea id="sub-notes" class="sub-textarea" rows="2" placeholder="e.g. Quoted over the phone in June 2025"></textarea>
          </div>
          <p class="sub-err" id="sub-form-err"></p>
          <button class="sub-btn-primary" id="sub-submit">Submit</button>
        </div>

        <div id="sub-step-done" style="display:none;">
          <div class="sub-done-wrap">
            <div class="sub-done-emoji">&#127881;</div>
            <h3>Thanks, <span id="sub-done-name"></span>!</h3>
            <p>Your submission is under review. Once approved it will help others find better prices.</p>
            <a href="leaderboard.html" class="sub-done-link">See the leaderboard &rarr;</a>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(el);

    el.addEventListener('click', e => { if (e.target === el) closeModal(); });
    document.getElementById('sub-close').addEventListener('click', closeModal);
    document.getElementById('sub-type').addEventListener('change', syncTypeFields);
    document.getElementById('sub-username-next').addEventListener('click', onUsernameNext);
    document.getElementById('sub-submit').addEventListener('click', onSubmit);
  }

  function syncTypeFields() {
    const sel = document.getElementById('sub-type');
    const opt = sel.options[sel.selectedIndex];
    const isPrice = opt.dataset.isPrice === 'true';
    document.getElementById('sub-price-row').style.display = isPrice ? '' : 'none';
    document.getElementById('sub-value-row').style.display = isPrice ? 'none' : '';
    document.getElementById('sub-value').placeholder = opt.dataset.placeholder;
  }

  function showStep(name) {
    ['username', 'form', 'done'].forEach(s => {
      document.getElementById(`sub-step-${s}`).style.display = s === name ? '' : 'none';
    });
  }

  function openModal() {
    buildModal();
    document.getElementById('sub-overlay').style.display = 'flex';
    const clinicName = document.getElementById('profile-name')?.textContent || '';
    document.getElementById('sub-clinic-name').textContent = clinicName;
    const username = localStorage.getItem(USERNAME_KEY);
    showStep(username ? 'form' : 'username');
    syncTypeFields();
  }

  function closeModal() {
    const el = document.getElementById('sub-overlay');
    if (el) el.style.display = 'none';
  }

  function onUsernameNext() {
    const val = document.getElementById('sub-username-input').value.trim();
    const err = document.getElementById('sub-username-err');
    if (!val) { err.style.display = 'block'; return; }
    err.style.display = 'none';
    localStorage.setItem(USERNAME_KEY, val);
    showStep('form');
  }

  async function onSubmit() {
    const sel = document.getElementById('sub-type');
    const opt = sel.options[sel.selectedIndex];
    const isPrice = opt.dataset.isPrice === 'true';
    const price = document.getElementById('sub-price').value;
    const valueText = document.getElementById('sub-value').value.trim();
    const err = document.getElementById('sub-form-err');

    if (isPrice && !price) {
      err.textContent = 'Please enter a price.';
      err.style.display = 'block';
      return;
    }
    if (!isPrice && !valueText) {
      err.textContent = 'Please enter a value.';
      err.style.display = 'block';
      return;
    }
    err.style.display = 'none';

    const username = localStorage.getItem(USERNAME_KEY);
    const params = new URLSearchParams(window.location.search);
    const clinicId = params.get('id') ? parseInt(params.get('id'), 10) : null;
    const clinicName = document.getElementById('profile-name')?.textContent || null;

    const btn = document.getElementById('sub-submit');
    btn.textContent = 'Submitting…';
    btn.disabled = true;

    try {
      const res = await fetch(`${SUPABASE_URL}/rest/v1/price_submissions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'apikey': ANON_KEY,
          'Authorization': `Bearer ${ANON_KEY}`,
          'Prefer': 'return=minimal',
        },
        body: JSON.stringify({
          clinic_id: clinicId,
          clinic_name: clinicName,
          user_handle: username,
          submission_type: sel.value,
          price: isPrice ? parseInt(price, 10) : null,
          value_text: isPrice ? null : valueText,
          notes: document.getElementById('sub-notes').value.trim() || null,
          user_agent: navigator.userAgent,
        }),
      });
      if (!res.ok) throw new Error(res.status);
      document.getElementById('sub-done-name').textContent = username;
      showStep('done');
    } catch {
      err.textContent = 'Something went wrong. Please try again.';
      err.style.display = 'block';
      btn.textContent = 'Submit';
      btn.disabled = false;
    }
  }

  document.addEventListener('click', e => {
    if (e.target.closest('[data-action="submit-info"]')) openModal();
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });
})();
