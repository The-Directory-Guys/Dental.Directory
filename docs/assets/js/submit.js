(function () {
  'use strict';

  if (!document.getElementById('profile-content')) return;
  if (typeof window.supabase === 'undefined') return;

  const SUPABASE_URL = 'https://ankyjpgcocsvvtyyymys.supabase.co';
  const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFua3lqcGdjb2NzdnZ0eXl5bXlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4MTM1MTQsImV4cCI6MjA4OTM4OTUxNH0.SXxTLBdiNVSEDXy95yU0x0ctYFOjIby8hZbJ7B1LPK8';
  const PENDING_KEY = 'dc_pending_submit';

  const db = window.supabase.createClient(SUPABASE_URL, ANON_KEY);

  const TYPES = [
    { value: 'checkup',     label: 'Checkup price',       isPrice: true,  ph: '' },
    { value: 'scale_clean', label: 'Scale & clean price', isPrice: true,  ph: '' },
    { value: 'hygienist',   label: 'Hygienist price',     isPrice: true,  ph: '' },
    { value: 'hours',       label: 'Opening hours',       isPrice: false, ph: 'e.g. Mon–Fri 8am–5pm, Sat 9am–1pm' },
    { value: 'phone',       label: 'Phone number',        isPrice: false, ph: 'e.g. 04 123 4567' },
    { value: 'other',       label: 'Other correction',    isPrice: false, ph: 'Describe what needs updating' },
  ];

  const CSS = `
    #sub-overlay {
      display:none; position:fixed; inset:0; background:rgba(0,0,0,.5);
      z-index:900; align-items:center; justify-content:center; padding:1rem;
    }
    #sub-modal {
      background:#fff; border-radius:16px; padding:2rem;
      width:min(460px,100%); max-height:90vh; overflow-y:auto;
      box-shadow:0 12px 48px rgba(0,0,0,.22); position:relative;
    }
    #sub-close {
      position:absolute; top:1rem; right:1rem; background:none; border:none;
      font-size:1.125rem; cursor:pointer; color:#94a3b8; padding:.25rem; line-height:1;
    }
    #sub-close:hover { color:#475569; }
    .sub-h3 { margin:0 0 .375rem; font-size:1.125rem; font-weight:700; color:var(--clr-navy,#0f2a4a); }
    .sub-lead { font-size:.875rem; color:#64748b; margin:0 0 1.25rem; line-height:1.55; }
    .sub-lead a { color:var(--clr-teal,#0ea5e9); }
    .sub-label { display:block; font-size:.8125rem; font-weight:600; color:#374151; margin-bottom:.35rem; }
    .sub-optional { font-weight:400; color:#94a3b8; }
    .sub-input,.sub-select,.sub-textarea {
      width:100%; box-sizing:border-box; padding:.625rem .875rem;
      border:1.5px solid #e2e8f0; border-radius:8px; font-size:.9375rem;
      font-family:inherit; color:#1e293b; background:#fff; outline:none; transition:border-color .15s;
    }
    .sub-input:focus,.sub-select:focus,.sub-textarea:focus { border-color:var(--clr-teal,#0ea5e9); }
    .sub-textarea { resize:vertical; }
    .sub-field { margin-bottom:1rem; }
    .sub-err { font-size:.8125rem; color:#dc2626; margin:.35rem 0 0; display:none; }
    .sub-btn {
      display:block; width:100%; margin-top:1rem; padding:.75rem; border:none;
      border-radius:8px; font-size:.9375rem; font-weight:600; cursor:pointer;
      font-family:inherit; transition:background .15s;
    }
    .sub-btn--primary { background:var(--clr-teal,#0ea5e9); color:#fff; }
    .sub-btn--primary:hover { background:#0284c7; }
    .sub-btn--primary:disabled { opacity:.6; cursor:default; }
    .sub-center { text-align:center; padding:1.25rem 0 .5rem; }
    .sub-center-icon { font-size:2.5rem; margin-bottom:.75rem; }
    .sub-center h3 { color:var(--clr-navy,#0f2a4a); margin:0 0 .5rem; font-size:1.1rem; }
    .sub-center p { color:#64748b; font-size:.9rem; margin:0; line-height:1.6; }
    .sub-email-strong { font-weight:700; color:#1e293b; }
    .sub-done-link {
      display:inline-block; margin-top:1.25rem; background:var(--clr-navy,#0f2a4a);
      color:#fff; text-decoration:none; border-radius:8px; padding:.625rem 1.25rem;
      font-weight:600; font-size:.9375rem; transition:opacity .15s;
    }
    .sub-done-link:hover { opacity:.85; }
    @media (max-width:480px) { #sub-modal { padding:1.5rem; } }
  `;

  function buildModal() {
    if (document.getElementById('sub-overlay')) return;
    const style = document.createElement('style');
    style.textContent = CSS;
    document.head.appendChild(style);

    const typeOpts = TYPES.map(t =>
      `<option value="${t.value}" data-is-price="${t.isPrice}" data-ph="${t.ph}">${t.label}</option>`
    ).join('');

    const el = document.createElement('div');
    el.id = 'sub-overlay';
    el.innerHTML = `
      <div id="sub-modal" role="dialog" aria-modal="true">
        <button id="sub-close" aria-label="Close">&#x2715;</button>

        <div id="sub-step-email">
          <h3 class="sub-h3">Verify your email</h3>
          <p class="sub-lead">We'll send a one-click magic link — no password needed. Your name will appear on the <a href="leaderboard.html" target="_blank">contributor leaderboard</a> and follows you across all your devices.</p>
          <div class="sub-field">
            <label class="sub-label" for="sub-email-input">Email address</label>
            <input id="sub-email-input" class="sub-input" type="email" placeholder="you@example.com" autocomplete="email">
            <p class="sub-err" id="sub-email-err"></p>
          </div>
          <button class="sub-btn sub-btn--primary" id="sub-email-btn">Send magic link &rarr;</button>
        </div>

        <div id="sub-step-sent" style="display:none;">
          <div class="sub-center">
            <div class="sub-center-icon">📬</div>
            <h3>Check your inbox</h3>
            <p>We sent a link to <span class="sub-email-strong" id="sub-sent-addr"></span>.<br>Click it and you'll come straight back here to complete your submission.</p>
          </div>
        </div>

        <div id="sub-step-name" style="display:none;">
          <h3 class="sub-h3">Choose a display name</h3>
          <p class="sub-lead">This is how you'll appear on the leaderboard — saved to your account so it works everywhere.</p>
          <div class="sub-field">
            <label class="sub-label" for="sub-name-input">Display name</label>
            <input id="sub-name-input" class="sub-input" type="text" maxlength="30" placeholder="e.g. Wellington Wanderer" autocomplete="off">
            <p class="sub-err" id="sub-name-err"></p>
          </div>
          <button class="sub-btn sub-btn--primary" id="sub-name-btn">Continue &rarr;</button>
        </div>

        <div id="sub-step-form" style="display:none;">
          <h3 class="sub-h3">Submit information</h3>
          <p class="sub-lead" id="sub-clinic-label"></p>
          <div class="sub-field">
            <label class="sub-label" for="sub-type">What are you submitting?</label>
            <select id="sub-type" class="sub-select">${typeOpts}</select>
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
          <button class="sub-btn sub-btn--primary" id="sub-submit-btn">Submit</button>
        </div>

        <div id="sub-step-done" style="display:none;">
          <div class="sub-center">
            <div class="sub-center-icon">&#127881;</div>
            <h3>Thanks, <span id="sub-done-name"></span>!</h3>
            <p>Your submission is under review. Once approved it will help others find better prices.</p>
            <a href="leaderboard.html" class="sub-done-link">See the leaderboard &rarr;</a>
          </div>
        </div>
      </div>`;
    document.body.appendChild(el);

    el.addEventListener('click', e => { if (e.target === el) closeModal(); });
    document.getElementById('sub-close').addEventListener('click', closeModal);
    document.getElementById('sub-type').addEventListener('change', syncFields);
    document.getElementById('sub-email-btn').addEventListener('click', onEmailNext);
    document.getElementById('sub-name-btn').addEventListener('click', onNameNext);
    document.getElementById('sub-submit-btn').addEventListener('click', onSubmit);
  }

  const STEPS = ['email', 'sent', 'name', 'form', 'done'];
  function showStep(name) {
    STEPS.forEach(s => {
      document.getElementById(`sub-step-${s}`).style.display = s === name ? '' : 'none';
    });
  }

  function syncFields() {
    const sel = document.getElementById('sub-type');
    const opt = sel.options[sel.selectedIndex];
    const isPrice = opt.dataset.isPrice === 'true';
    document.getElementById('sub-price-row').style.display = isPrice ? '' : 'none';
    document.getElementById('sub-value-row').style.display = isPrice ? 'none' : '';
    document.getElementById('sub-value').placeholder = opt.dataset.ph || '';
  }

  async function openModal() {
    buildModal();
    document.getElementById('sub-overlay').style.display = 'flex';
    document.getElementById('sub-clinic-label').textContent =
      document.getElementById('profile-name')?.textContent || '';

    const { data: { session } } = await db.auth.getSession();
    if (!session) { showStep('email'); return; }

    const name = session.user.user_metadata?.display_name;
    if (!name) { showStep('name'); return; }

    showStep('form');
    syncFields();
  }

  function closeModal() {
    const el = document.getElementById('sub-overlay');
    if (el) el.style.display = 'none';
  }

  async function onEmailNext() {
    const email = document.getElementById('sub-email-input').value.trim();
    const err = document.getElementById('sub-email-err');
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      err.textContent = 'Please enter a valid email address.';
      err.style.display = 'block';
      return;
    }
    err.style.display = 'none';
    const btn = document.getElementById('sub-email-btn');
    btn.textContent = 'Sending…'; btn.disabled = true;

    sessionStorage.setItem(PENDING_KEY, '1');
    const redirectTo = window.location.origin + window.location.pathname + window.location.search;
    const { error } = await db.auth.signInWithOtp({ email, options: { emailRedirectTo: redirectTo, shouldCreateUser: true } });

    if (error) {
      err.textContent = 'Could not send link. Please try again.';
      err.style.display = 'block';
      btn.textContent = 'Send magic link →'; btn.disabled = false;
      sessionStorage.removeItem(PENDING_KEY);
      return;
    }
    document.getElementById('sub-sent-addr').textContent = email;
    showStep('sent');
  }

  async function onNameNext() {
    const name = document.getElementById('sub-name-input').value.trim();
    const err = document.getElementById('sub-name-err');
    if (!name) { err.textContent = 'Please enter a display name.'; err.style.display = 'block'; return; }
    err.style.display = 'none';
    const btn = document.getElementById('sub-name-btn');
    btn.textContent = 'Saving…'; btn.disabled = true;

    const { error } = await db.auth.updateUser({ data: { display_name: name } });
    if (error) {
      err.textContent = 'Could not save name. Please try again.';
      err.style.display = 'block';
      btn.textContent = 'Continue →'; btn.disabled = false;
      return;
    }
    showStep('form'); syncFields();
  }

  async function onSubmit() {
    const sel = document.getElementById('sub-type');
    const opt = sel.options[sel.selectedIndex];
    const isPrice = opt.dataset.isPrice === 'true';
    const price = document.getElementById('sub-price').value;
    const valueText = document.getElementById('sub-value').value.trim();
    const err = document.getElementById('sub-form-err');

    if (isPrice && !price)    { err.textContent = 'Please enter a price.'; err.style.display = 'block'; return; }
    if (!isPrice && !valueText) { err.textContent = 'Please enter a value.'; err.style.display = 'block'; return; }
    err.style.display = 'none';

    const { data: { session } } = await db.auth.getSession();
    if (!session) { showStep('email'); return; }

    const displayName = session.user.user_metadata?.display_name || 'Anonymous';
    const params = new URLSearchParams(window.location.search);
    const clinicId = params.get('id') ? parseInt(params.get('id'), 10) : null;
    const clinicName = document.getElementById('profile-name')?.textContent || null;

    const btn = document.getElementById('sub-submit-btn');
    btn.textContent = 'Submitting…'; btn.disabled = true;

    try {
      const res = await fetch(`${SUPABASE_URL}/rest/v1/price_submissions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'apikey': ANON_KEY,
          'Authorization': `Bearer ${session.access_token}`,
          'Prefer': 'return=minimal',
        },
        body: JSON.stringify({
          clinic_id: clinicId,
          clinic_name: clinicName,
          user_id: session.user.id,
          user_handle: displayName,
          submission_type: sel.value,
          price: isPrice ? parseInt(price, 10) : null,
          value_text: isPrice ? null : valueText,
          notes: document.getElementById('sub-notes').value.trim() || null,
          user_agent: navigator.userAgent,
        }),
      });
      if (!res.ok) throw new Error(res.status);
      document.getElementById('sub-done-name').textContent = displayName;
      showStep('done');
    } catch {
      err.textContent = 'Something went wrong. Please try again.';
      err.style.display = 'block';
      btn.textContent = 'Submit'; btn.disabled = false;
    }
  }

  // Re-open modal after magic link redirect
  db.auth.onAuthStateChange((event, session) => {
    if (event === 'SIGNED_IN' && session && sessionStorage.getItem(PENDING_KEY)) {
      sessionStorage.removeItem(PENDING_KEY);
      setTimeout(openModal, 600);
    }
  });

  document.addEventListener('click', e => {
    if (e.target.closest('[data-action="submit-info"]')) openModal();
  });
  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') closeModal();
  });
})();
