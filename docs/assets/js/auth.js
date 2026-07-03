// Dental Compare — Owner Auth
// Magic-link (OTP) flow via Supabase Auth REST API
(function (window) {
  const URL$  = 'https://ankyjpgcocsvvtyyymys.supabase.co/auth/v1';
  const KEY   = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFua3lqcGdjb2NzdnZ0eXl5bXlzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM4MTM1MTQsImV4cCI6MjA4OTM4OTUxNH0.SXxTLBdiNVSEDXy95yU0x0ctYFOjIby8hZbJ7B1LPK8';
  const H     = { 'Content-Type': 'application/json', apikey: KEY };
  const LS    = 'dc_owner_session';

  const DCAuth = {

    // Send magic-link email. redirectTo must be in Supabase "Allowed redirect URLs".
    async sendMagicLink(email, redirectTo) {
      const body = { email, create_user: false };
      if (redirectTo) body.options = { emailRedirectTo: redirectTo };
      const r = await fetch(`${URL$}/otp`, {
        method: 'POST', headers: H, body: JSON.stringify(body)
      });
      return { ok: r.ok, status: r.status };
    },

    // Parse Supabase hash fragment after magic-link redirect.
    parseHash() {
      const params = {};
      window.location.hash.slice(1).split('&').forEach(pair => {
        const eq = pair.indexOf('=');
        if (eq < 0) return;
        params[decodeURIComponent(pair.slice(0, eq))] = decodeURIComponent(pair.slice(eq + 1));
      });
      return params;
    },

    // Persist a Supabase token response to localStorage.
    saveSession(data) {
      const s = {
        access_token:  data.access_token,
        refresh_token: data.refresh_token,
        expires_at:    Math.floor(Date.now() / 1000) + parseInt(data.expires_in || 3600),
        user:          data.user || null,
      };
      try { localStorage.setItem(LS, JSON.stringify(s)); } catch {}
      return s;
    },

    getSession() {
      try { return JSON.parse(localStorage.getItem(LS)); } catch { return null; }
    },

    clearSession() {
      try { localStorage.removeItem(LS); } catch {}
    },

    _isExpired(s) {
      return !s || (Date.now() / 1000) > (s.expires_at - 60);
    },

    async _refresh() {
      const s = this.getSession();
      if (!s?.refresh_token) return null;
      const r = await fetch(`${URL$}/token?grant_type=refresh_token`, {
        method: 'POST', headers: H,
        body: JSON.stringify({ refresh_token: s.refresh_token })
      });
      if (!r.ok) { this.clearSession(); return null; }
      return this.saveSession(await r.json());
    },

    // Returns a valid session (refreshing if needed), or null.
    async getValidSession() {
      const s = this.getSession();
      if (!s) return null;
      if (!this._isExpired(s)) return s;
      return this._refresh();
    },

    async getUser() {
      const s = await this.getValidSession();
      if (!s) return null;
      const r = await fetch(`${URL$}/user`, {
        headers: { ...H, Authorization: `Bearer ${s.access_token}` }
      });
      return r.ok ? r.json() : null;
    },

    async signOut() {
      const s = this.getSession();
      if (s?.access_token) {
        await fetch(`${URL$}/logout`, {
          method: 'POST',
          headers: { ...H, Authorization: `Bearer ${s.access_token}` }
        }).catch(() => {});
      }
      this.clearSession();
    },

    // Redirect to loginUrl if not authenticated. Returns session or null.
    async requireAuth(loginUrl) {
      loginUrl = loginUrl || 'login.html';
      const s = await this.getValidSession();
      if (!s) {
        window.location.href = `${loginUrl}?next=${encodeURIComponent(window.location.href)}`;
        return null;
      }
      return s;
    },
  };

  window.DCAuth = DCAuth;
})(window);
