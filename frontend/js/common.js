/* ============================================================
   PASSWORD STRENGTH ANALYZER - COMMON UTILITIES
   ============================================================ */

const PSA = {
  API_BASE: window.PSA_API_BASE || (() => {
    const path = window.location.pathname;
    const projectRoot = path.includes('/frontend/') ? path.split('/frontend/')[0] : '';
    return `${window.location.origin}${projectRoot}/php_backend/api/`;
  })(),

  /* ---------- Toast notifications ---------- */
  toast(msg, type = 'success') {
    let container = document.querySelector('.toast-container');
    if (!container) {
      container = document.createElement('div');
      container.className = 'toast-container';
      container.setAttribute('role', 'status');
      container.setAttribute('aria-live', 'polite');
      document.body.appendChild(container);
    }
    const t = document.createElement('div');
    t.className = `toast toast-${type}`;
    t.textContent = `${type === 'success' ? 'OK' : type === 'error' ? 'ERR' : 'INFO'} :: ${msg}`;
    container.appendChild(t);
    setTimeout(() => {
      t.style.opacity = '0';
      t.style.transition = 'opacity 0.4s';
      setTimeout(() => t.remove(), 400);
    }, 3200);
  },

/* ---------- Fetch wrapper (JSON API) ----------
     Detects the live backend ONCE (Django REST vs. PHP), caches the
     decision, then calls it directly — no wasted dead-request on
     every call. */
  _backendDetected: null,
  async detectBackend() {
    if (this._backendDetected) return this._backendDetected;
    const saved = sessionStorage.getItem('psa_api_backend');
    if (saved) { this._backendDetected = saved; return saved; }
    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), 1500);
    try {
      const probe = new URL('../index.php', this.API_BASE).href;
      const res = await fetch(probe, { method: 'GET', signal: ctrl.signal, cache: 'no-store' });
      this._backendDetected = (res.ok || res.type === 'opaque') ? 'php' : 'django';
    } catch {
      this._backendDetected = 'django';
    } finally {
      clearTimeout(timer);
    }
    sessionStorage.setItem('psa_api_backend', this._backendDetected);
    return this._backendDetected;
  },

  async api(endpoint, method = 'POST', data = null) {
    const opts = { method, headers: {} };
    const activeSession = this.session;
    if (activeSession && activeSession.token) {
      opts.headers.Authorization = `Bearer ${activeSession.token}`;
    }
    if (data) {
      opts.headers['Content-Type'] = 'application/json';
      opts.body = JSON.stringify(data);
    }
    const backend = await this.detectBackend();
    let url;
    if (backend === 'php') {
      url = `${this.API_BASE}${endpoint}`;
    } else {
      // Django REST: map PHP filenames to endpoint names
      const map = {
        'register.php': 'register',
        'login.php': 'login',
        'session.php': 'session',
        'history.php': 'history',
        'report.php': 'report',
        'admin.php': 'admin',
        'common_passwords.php': 'common-check',
        'analyze.php': 'analyze',
      };
      let base = '/api/';
      try { base = new URL('api/', window.location.href).href; } catch { base = '/api/'; }
      const name = endpoint.split('?')[0];
      url = `${base}${map[name] || name}`;
    }
    const res = await fetch(url, opts);
    const body = await res.json();
    if (res.status === 401 && endpoint.split('?')[0] !== 'login.php') {
      this.session = null;
      if (!location.pathname.endsWith('login.html')) location.href = 'login.html';
    }
    return body;
  },

  /* ---------- Friendly date/time ---------- */
  fmtDate(iso) {
    if (!iso) return '-';
    const d = new Date(/[zZ]$|[+-][0-9]{2}:?[0-9]{2}$/.test(iso) ? iso : iso + 'Z');
    if (isNaN(d)) return iso;
    try {
      return d.toLocaleString(undefined, {
        year: 'numeric', month: 'short', day: 'numeric',
        hour: '2-digit', minute: '2-digit',
      });
    } catch { return iso; }
  },

  /* ---------- Local session ---------- */
  get session() {
    try {
      return JSON.parse(localStorage.getItem('psa_session') || 'null');
    } catch { return null; }
  },

  set session(s) {
    if (s) localStorage.setItem('psa_session', JSON.stringify(s));
    else localStorage.removeItem('psa_session');
    this.applySessionToUI();
  },

  logout() {
    this.api('session.php', 'POST', { action: 'logout' }).catch(() => {}).finally(() => {
      this.session = null;
      window.location.href = 'login.html';
    });
  },

  applySessionToUI() {
    const s = this.session;
    document.body.classList.toggle('logged-in', !!s);
    const navAuth = document.getElementById('nav-auth-area');
    if (!navAuth) return;
    if (s) {
      navAuth.innerHTML = `
        <a href="dashboard.html" class="${location.pathname.includes('dashboard') ? 'active' : ''}">Dashboard</a>
        <a href="#" onclick="event.preventDefault(); PSA.logout()" style="color:var(--toxic-red)">Sign out</a>`;
      const adminNav = document.getElementById('nav-admin');
      if (s.is_admin && adminNav) adminNav.style.display = '';
    } else {
      navAuth.innerHTML = `
        <a href="login.html">Login</a>
        <a href="register.html" class="btn btn-sm btn-solid">Register</a>`;
      if (location.pathname.includes('dashboard')) window.location.href = 'login.html';
    }
    this.applyUserBadge();
  },

  applyUserBadge() {
    const s = this.session;
    const badge = document.getElementById('user-badge');
    if (!badge || !s) return;
    badge.textContent = `UID:${s.user.id} :: ${s.user.username}${s.is_admin ? ' [ROOT]' : ''}`;
  },

  /* ---------- Matrix rain canvas ---------- */
  initMatrix() {
    const canvas = document.getElementById('matrix-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let w, h, cols, drops;
    const resize = () => {
      w = canvas.width = window.innerWidth;
      h = canvas.height = window.innerHeight;
      cols = Math.floor(w / 18);
      drops = Array(cols).fill(1);
    };
    resize();
    const chars = '01アイウエオカキクケコサシスセソタチツテトナニヌネノABCDEF0123456789#$%&';

    function draw() {
      if (document.hidden) return;
      ctx.fillStyle = 'rgba(5, 8, 7, 0.06)';
      ctx.fillRect(0, 0, w, h);
      ctx.fillStyle = '#00ff88';
      ctx.font = '15px monospace';
      for (let i = 0; i < cols; i++) {
        const ch = chars[Math.floor(Math.random() * chars.length)];
        ctx.fillText(ch, i * 18, drops[i] * 18);
        if (drops[i] * 18 > h && Math.random() > 0.975) drops[i] = 0;
        drops[i]++;
      }
    }
    let rainTimer = setInterval(draw, 50);
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        clearInterval(rainTimer);
        rainTimer = null;
      } else if (!rainTimer) {
        rainTimer = setInterval(draw, 50);
      }
    });
    window.addEventListener('resize', resize);
  },

  /* ---------- Typing title ---------- */
  initTypewriter(element, text) {
    if (!element) return;
    element.textContent = '';
    let i = 0;
    const tw = () => {
      if (i <= text.length) {
        element.textContent = text.slice(0, i);
        i++;
        setTimeout(tw, 75);
      }
    };
    tw();
  },

  /* ---------- Password visibility toggles ---------- */
  initPasswordToggles() {
    document.querySelectorAll('.toggle-password').forEach(btn => {
      btn.setAttribute('aria-label', 'Show password');
      btn.setAttribute('aria-pressed', 'false');
      btn.addEventListener('click', () => {
        const input = document.getElementById(btn.dataset.target);
        if (!input) return;
        const isPw = input.type === 'password';
        input.type = isPw ? 'text' : 'password';
        btn.textContent = isPw ? '◎' : '●';
        btn.setAttribute('aria-label', isPw ? 'Hide password' : 'Show password');
        btn.setAttribute('aria-pressed', String(isPw));
      });
    });
  },

  initNavigation() {
    const button = document.querySelector('.burger');
    const links = document.getElementById('nav-links');
    if (!button || !links) return;
    button.removeAttribute('onclick');
    button.type = 'button';
    button.setAttribute('aria-label', 'Open navigation');
    button.setAttribute('aria-controls', 'nav-links');
    button.setAttribute('aria-expanded', 'false');
    const close = () => {
      links.classList.remove('open');
      button.setAttribute('aria-expanded', 'false');
      button.setAttribute('aria-label', 'Open navigation');
    };
    button.addEventListener('click', () => {
      const open = links.classList.toggle('open');
      button.setAttribute('aria-expanded', String(open));
      button.setAttribute('aria-label', open ? 'Close navigation' : 'Open navigation');
    });
    links.addEventListener('click', event => {
      if (event.target.closest('a')) close();
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape') close();
    });
  },

  /* ---------- Fetch and populate dynamic nav (session) ---------- */
  guard() {
    if (!this.session) {
      this.toast('Authentication required. Redirecting to login.', 'info');
      setTimeout(() => (window.location.href = 'login.html'), 900);
      return false;
    }
    return true;
  },

  escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  }
};

/* ---------- Boot helpers on DOM ready ---------- */
document.addEventListener('DOMContentLoaded', () => {
  PSA.applySessionToUI();
  PSA.initPasswordToggles();
  PSA.initNavigation();
  if (document.getElementById('matrix-canvas')) PSA.initMatrix();
  const ty = document.getElementById('typewriter-text');
  if (ty) PSA.initTypewriter(ty, ty.dataset.text || 'PASSGUARD');
});
