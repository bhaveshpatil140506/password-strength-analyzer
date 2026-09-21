/* ============================================================
   PASSWORD STRENGTH ANALYZER - FORM VALIDATIONS
   ============================================================ */

const PSA_Validator = {

  /* ---------- Generic field validation ---------- */
  validateField(input, rules) {
    const val = input.value.trim();
    const errEl = document.getElementById(`${input.id}-error`);
    let msg = '';

    if (rules.required && !val) msg = rules.customMsgRequired || 'This field is required.';
    else if (rules.minLength && val.length < rules.minLength) msg = `Minimum ${rules.minLength} characters required.`;
    else if (rules.maxLength && val.length > rules.maxLength) msg = `Maximum ${rules.maxLength} characters allowed.`;
    else if (rules.pattern && !rules.pattern.test(val)) msg = rules.patternMsg || 'Invalid format.';
    else if (rules.custom && !rules.custom(val)) msg = rules.customMsg || 'Invalid value.';

    if (errEl) {
      errEl.textContent = msg;
      errEl.classList.toggle('show', !!msg);
    }
    input.classList.toggle('invalid', !!msg);
    input.classList.toggle('valid', !msg && val.length > 0);
    return !msg;
  },

  /* ---------- Registration form ---------- */
  validateRegister() {
    const fullName = document.getElementById('fullname');
    const username = document.getElementById('username');
    const email = document.getElementById('email');
    const pw = document.getElementById('password');
    const pwConfirm = document.getElementById('password_confirm');
    const sq = document.getElementById('security_question');
    const sa = document.getElementById('security_answer');

    const validFullName = this.validateField(fullName, {
      required: true,
      minLength: 3,
      maxLength: 80,
      pattern: /^[a-zA-Z\s.'-]+$/,
      patternMsg: 'Enter a valid name (letters, spaces, . - \' only).',
    });

    const validUsername = this.validateField(username, {
      required: true,
      minLength: 4,
      maxLength: 30,
      pattern: /^[a-zA-Z0-9_]+$/,
      patternMsg: 'Username: letters, numbers, and underscores only.',
    });

    const validEmail = this.validateField(email, {
      required: true,
      pattern: /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/,
      patternMsg: 'Enter a valid email address.',
    });

    const validPw = this.validatePassword(pw);
    const validPwConfirm = this.validateField(pwConfirm, {
      required: true,
      custom: v => v === pw.value,
      customMsg: 'Passwords do not match.',
    });

    let validSa = true;
    if (sq && sq.value && sa) {
      validSa = this.validateField(sa, {
        required: true,
        minLength: 2,
        customMsg: 'Security answer is required if question is set.',
      });
    }

    return validFullName && validUsername && validEmail && validPw && validPwConfirm && validSa;
  },

  /* ---------- Login form ---------- */
  validateLogin() {
    const uname = document.getElementById('username');
    const pw = document.getElementById('password');

    const v1 = this.validateField(uname, { required: true, minLength: 3 });
    const v2 = this.validateField(pw, { required: true, minLength: 4 });
    return v1 && v2;
  },

  /* ---------- Password input ---------- */
  validatePassword(input) {
    const pw = input ? input.value : '';
    let score = 0;
    let msg = '';

    if (!pw) { msg = 'Password is required.'; }
    else {
      if (pw.length >= 8) score++;
      if (pw.length >= 12) score++;
      if (pw.length >= 16) score++;
      if (/[a-z]/.test(pw)) score++;
      if (/[A-Z]/.test(pw)) score++;
      if (/[0-9]/.test(pw)) score++;
      if (/[^A-Za-z0-9]/.test(pw)) score++;
      if (!/(.)\1{2,}/.test(pw)) score++;

      if (score < 4) msg = 'Password is too weak.';
      else if (pw.length < 8) msg = 'Password must be at least 8 characters.';
    }

    if (input) {
      const errEl = document.getElementById('password-error');
      if (errEl) {
        errEl.textContent = msg;
        errEl.classList.toggle('show', !!msg);
      }
      input.classList.toggle('invalid', !!msg);
      input.classList.toggle('valid', !msg && pw.length >= 8);
    }
    return score >= 4 && pw.length >= 8;
  },

  /* ---------- Password strength analysis (inline on keyup) ---------- */
  analyzePasswordStrength(pw) {
    if (!pw) return { score: 0, label: 'None', color: 'var(--text-muted)', pct: 0 };

    let score = 0;
    const checks = {
      length8: pw.length >= 8,
      length12: pw.length >= 12,
      lowercase: /[a-z]/.test(pw),
      uppercase: /[A-Z]/.test(pw),
      numbers: /[0-9]/.test(pw),
      special: /[^A-Za-z0-9]/.test(pw),
      noRepeat: !/(.)\1{2,}/.test(pw),
      noSequential: !/(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|012|123|234|345|456|567|678|789)/i.test(pw),
    };

    Object.values(checks).forEach(c => { if (c) score++; });

    let label, color, pct;
    if (score <= 2) { label = 'WEAK'; color = 'var(--toxic-red)'; pct = 20; }
    else if (score <= 4) { label = 'FAIR'; color = 'var(--warning-amber)'; pct = 45; }
    else if (score <= 6) { label = 'STRONG'; color = 'var(--matrix-green)'; pct = 75; }
    else { label = 'EXCELLENT'; color = 'var(--neon-cyan)'; pct = 100; }

    return { score, label, color, pct, checks };
  },

  /* ---------- Realtime inline strength meter ---------- */
  bindStrengthMeter(pwInputId, meterId, labelId, criteriaId) {
    const input = document.getElementById(pwInputId);
    const meter = document.getElementById(meterId);
    const label = document.getElementById(labelId);
    const list = document.getElementById(criteriaId);
    if (!input || !meter) return;

    const labels = ['length8', 'lowercase', 'uppercase', 'numbers', 'special', 'noRepeat', 'noSequential'];
    const display = {
      length8: '8+ characters', lowercase: 'Lowercase letters', uppercase: 'Uppercase letters',
      numbers: 'Numbers (0-9)', special: 'Special characters', noRepeat: 'No repeated characters',
      noSequential: 'No sequential patterns'
    };

    input.addEventListener('input', () => {
      const r = this.analyzePasswordStrength(input.value);
      meter.style.width = r.pct + '%';
      meter.style.background = r.color;
      meter.style.boxShadow = `0 0 12px ${r.color}`;
      if (label) { label.textContent = r.label; label.style.color = r.color; }

      if (list) {
        list.innerHTML = '';
        labels.forEach(k => {
          const li = document.createElement('li');
          li.className = r.checks[k] ? 'pass' : (input.value ? 'fail' : '');
          li.innerHTML = `<span class="crit-icon">${r.checks[k] ? '&#10003;' : '&#10007;'}</span> ${display[k]}`;
          list.appendChild(li);
        });
      }
    });
  }
};