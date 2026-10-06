/* ============================================================
   PASSWORD STRENGTH ANALYZER - AUTH (Login / Register)
   ============================================================ */

const PSA_Auth = {

  /* ---------- Registration ---------- */
  async register(e) {
    e.preventDefault();
    if (!PSA_Validator.validateRegister()) return;

    const payload = {
      fullname: document.getElementById('fullname').value.trim(),
      username: document.getElementById('username').value.trim(),
      email: document.getElementById('email').value.trim(),
      password: document.getElementById('password').value,
    };

    const btn = document.getElementById('register-btn');
    btn.textContent = 'PROCESSING...';
    btn.disabled = true;

    try {
      const res = await PSA.api('register.php', 'POST', payload);
      if (res.success) {
        PSA.toast('Registration successful! Please log in.', 'success');
        setTimeout(() => (window.location.href = 'login.html'), 1400);
      } else {
        PSA.toast(res.message || 'Registration failed.', 'error');
        if (res.errors) {
          for (const [field, msg] of Object.entries(res.errors)) {
            const el = document.getElementById(field);
            const err = document.getElementById(`${field}-error`);
            if (el) el.classList.add('invalid');
            if (err) { err.textContent = msg; err.classList.add('show'); }
          }
        }
      }
    } catch (err) {
      PSA.toast('Network error. Please try again.', 'error');
    } finally {
      btn.textContent = 'CREATE ACCOUNT';
      btn.disabled = false;
    }
  },

  /* ---------- Login ---------- */
  async login(e) {
    e.preventDefault();
    if (!PSA_Validator.validateLogin()) return;

    const payload = {
      username: document.getElementById('username').value.trim(),
      password: document.getElementById('password').value,
    };

    const btn = document.getElementById('login-btn');
    btn.textContent = 'AUTHENTICATING...';
    btn.disabled = true;

    try {
      const res = await PSA.api('login.php', 'POST', payload);
      if (res.success) {
        PSA.session = res.session;
        PSA.toast('Authentication successful', 'success');
        setTimeout(() => {
          window.location.href = res.session.is_admin ? 'admin_dashboard.html' : 'dashboard.html';
        }, 800);
      } else {
        PSA.toast(res.message || 'Login failed.', 'error');
        document.getElementById('password').classList.add('invalid');
      }
    } catch (err) {
      PSA.toast('Connection refused. Please check server.', 'error');
    } finally {
      btn.textContent = 'ACCESS SYSTEM';
      btn.disabled = false;
    }
  },

  /* ---------- Init ---------- */
  bind() {
    const regForm = document.getElementById('register-form');
    const loginForm = document.getElementById('login-form');
    if (regForm) regForm.addEventListener('submit', e => PSA_Auth.register(e));
    if (loginForm) loginForm.addEventListener('submit', e => PSA_Auth.login(e));

    PSA_Validator.bindStrengthMeter('password', 'password-meter', 'password-label', 'password-criteria');
  }
};

document.addEventListener('DOMContentLoaded', () => PSA_Auth.bind());
