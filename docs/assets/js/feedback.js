(function () {
  'use strict';

  const SUPABASE_URL = 'https://ankyjpgcocsvvtyyymys.supabase.co';
  const ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFua3lqcGdjb2NzdnZ0eXl5bXlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4MTM1MTQsImV4cCI6MjA4OTM4OTUxNH0.SXxTLBdiNVSEDXy95yU0x0ctYFOjIby8hZbJ7B1LPK8';

  function init() {
    const wrapper = document.createElement('div');
    wrapper.id = 'fb-widget';
    wrapper.innerHTML = `
      <button id="fb-tab" aria-label="Give feedback" aria-expanded="false">
        <span>Feedback</span>
      </button>
      <div id="fb-panel" hidden role="dialog" aria-label="Feedback">
        <div class="fb-header">
          <span class="fb-header-title">Share feedback</span>
          <button class="fb-close" aria-label="Close">✕</button>
        </div>
        <div class="fb-body">
          <div id="fb-s1" class="fb-step">
            <p class="fb-question">Did you find what you were looking for?</p>
            <div class="fb-yn-row">
              <button class="fb-yn fb-yn--yes" data-found="true">✓&nbsp; Yes</button>
              <button class="fb-yn fb-yn--no"  data-found="false">✗&nbsp; No</button>
            </div>
          </div>

          <div id="fb-s2" class="fb-step" hidden>
            <p id="fb-msg" class="fb-msg"></p>

            <div class="fb-field">
              <label class="fb-label">Tell us more <span class="fb-opt">(optional)</span></label>
              <textarea id="fb-comment" class="fb-textarea" rows="3"
                placeholder="What were you looking for? Any suggestions?"></textarea>
            </div>

            <div class="fb-field">
              <label class="fb-label">Overall rating <span class="fb-opt">(optional)</span></label>
              <div class="fb-stars" id="fb-overall" data-field="overall"></div>
            </div>

            <details class="fb-aspects-wrap">
              <summary class="fb-aspects-toggle">
                Rate specific aspects <span class="fb-opt">(optional)</span>
              </summary>
              <div class="fb-aspects">
                <div class="fb-aspect">
                  <span>Search &amp; Filters</span>
                  <div class="fb-stars" data-field="search"></div>
                </div>
                <div class="fb-aspect">
                  <span>Clinic Information</span>
                  <div class="fb-stars" data-field="clinic_info"></div>
                </div>
                <div class="fb-aspect">
                  <span>Pricing Data</span>
                  <div class="fb-stars" data-field="pricing"></div>
                </div>
                <div class="fb-aspect">
                  <span>Reviews</span>
                  <div class="fb-stars" data-field="reviews"></div>
                </div>
              </div>
            </details>

            <button id="fb-submit" class="fb-submit">Submit feedback</button>
          </div>

          <div id="fb-s3" class="fb-step fb-thanks" hidden>
            <div class="fb-thanks-icon">🙏</div>
            <p class="fb-thanks-title">Thanks for your feedback!</p>
            <p class="fb-thanks-sub">It helps us improve the site.</p>
          </div>
        </div>
      </div>
    `;
    document.body.appendChild(wrapper);

    const tab      = document.getElementById('fb-tab');
    const panel    = document.getElementById('fb-panel');
    const closeBtn = wrapper.querySelector('.fb-close');
    const s1       = document.getElementById('fb-s1');
    const s2       = document.getElementById('fb-s2');
    const s3       = document.getElementById('fb-s3');
    const msg      = document.getElementById('fb-msg');
    const comment  = document.getElementById('fb-comment');
    const submit   = document.getElementById('fb-submit');

    let foundIt = null;

    wrapper.querySelectorAll('.fb-stars').forEach(initStars);

    tab.addEventListener('click', () => {
      const open = panel.hidden;
      panel.hidden = !open;
      tab.setAttribute('aria-expanded', open);
    });

    closeBtn.addEventListener('click', close);

    // Close on outside click
    document.addEventListener('click', (e) => {
      if (!panel.hidden && !wrapper.contains(e.target)) close();
    });

    wrapper.querySelectorAll('.fb-yn').forEach(btn => {
      btn.addEventListener('click', () => {
        foundIt = btn.dataset.found === 'true';
        msg.textContent = foundIt
          ? 'Glad to hear it! Anything to add?'
          : 'Sorry to hear that. What were you looking for?';
        s1.hidden = true;
        s2.hidden = false;
      });
    });

    submit.addEventListener('click', async () => {
      submit.disabled = true;
      submit.textContent = 'Submitting…';

      const overall = parseInt(document.getElementById('fb-overall').dataset.value || '0') || null;
      const aspects = {};
      wrapper.querySelectorAll('.fb-stars[data-field]').forEach(el => {
        const v = parseInt(el.dataset.value || '0');
        if (v > 0 && el.dataset.field !== 'overall') aspects[el.dataset.field] = v;
      });

      try {
        await fetch(`${SUPABASE_URL}/rest/v1/feedback`, {
          method: 'POST',
          headers: {
            'apikey': ANON_KEY,
            'Authorization': `Bearer ${ANON_KEY}`,
            'Content-Type': 'application/json',
            'Prefer': 'return=minimal',
          },
          body: JSON.stringify({
            page_url: window.location.pathname,
            found_it: foundIt,
            comment: comment.value.trim() || null,
            overall_rating: overall,
            aspect_ratings: Object.keys(aspects).length ? aspects : null,
            user_agent: navigator.userAgent,
          }),
        });
      } catch (_) { /* fail silently */ }

      s2.hidden = true;
      s3.hidden = false;

      setTimeout(() => {
        close();
        setTimeout(reset, 350);
      }, 2500);
    });

    function close() {
      panel.hidden = true;
      tab.setAttribute('aria-expanded', 'false');
    }

    function reset() {
      foundIt = null;
      s1.hidden = false;
      s2.hidden = true;
      s3.hidden = true;
      comment.value = '';
      wrapper.querySelectorAll('.fb-stars').forEach(el => {
        el.dataset.value = '0';
        el.querySelectorAll('.fb-star').forEach(s => s.classList.remove('active', 'hover'));
      });
      submit.disabled = false;
      submit.textContent = 'Submit feedback';
    }
  }

  function initStars(container) {
    container.dataset.value = '0';
    for (let i = 1; i <= 5; i++) {
      const s = document.createElement('button');
      s.type = 'button';
      s.className = 'fb-star';
      s.textContent = '★';
      s.dataset.val = i;
      s.setAttribute('aria-label', `${i} star${i > 1 ? 's' : ''}`);

      s.addEventListener('mouseenter', () => {
        container.querySelectorAll('.fb-star').forEach(x =>
          x.classList.toggle('hover', +x.dataset.val <= i)
        );
      });
      s.addEventListener('mouseleave', () => {
        const cur = +container.dataset.value;
        container.querySelectorAll('.fb-star').forEach(x => {
          x.classList.remove('hover');
          x.classList.toggle('active', +x.dataset.val <= cur);
        });
      });
      s.addEventListener('click', () => {
        container.dataset.value = i;
        container.querySelectorAll('.fb-star').forEach(x => {
          x.classList.toggle('active', +x.dataset.val <= i);
          x.classList.remove('hover');
        });
      });
      container.appendChild(s);
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
