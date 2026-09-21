/* ============================================================
   PASSWORD STRENGTH ANALYZER - CORE ANALYSIS ENGINE
   Entropy, crack-time, common list, recommendations
   ============================================================ */

const PSA_Analyzer = {

  /* Top common-ish passwords (client mirror; server has authoritative list) */
  commonList: [
    '123456','123456789','password','qwerty','abc123','111111','12345678',
    '12345','iloveyou','admin','welcome','monkey','login','dragon','master',
    'letmein','hello','freedom','whatever','trustno1','sunshine','qwerty123',
    '123123','passw0rd','654321','qazwsx','password1','000000','1234','1234567',
    'princess','football','ashley','batman','superman','soccer','jordan','michael','shadow','qwertyuiop','letmein123','p@ssw0rd','Pa55w0rd','password123'
  ].map(p => p.toLowerCase()),

  /* ---------- Character pool entropy ---------- */
  calculateEntropy(pw) {
    let pool = 0;
    if (/[a-z]/.test(pw)) pool += 26;
    if (/[A-Z]/.test(pw)) pool += 26;
    if (/[0-9]/.test(pw)) pool += 10;
    if (/[^A-Za-z0-9]/.test(pw)) pool += 33;
    if (pool === 0) return 0;
    return pw.length * Math.log2(pool);
  },

  /* ---------- Estimated crack time (@10 billion guesses/sec) ---------- */
  estimateCrackTime(entropy) {
    const secs = Math.pow(2, entropy) / 1e10;
    if (secs < 1) return 'Instantly';
    if (secs < 60) return `${Math.floor(secs)} seconds`;
    if (secs < 3600) return `${Math.floor(secs / 60)} minutes`;
    if (secs < 86400) return `${Math.floor(secs / 3600)} hours`;
    if (secs < 86400 * 365) return `${Math.floor(secs / 86400)} days`;
    if (secs < 86400 * 365 * 100) return `${Math.floor(secs / (86400 * 365))} years`;
    if (secs < 86400 * 365 * 100000) return `${Math.floor(secs / (86400 * 365 * 100))} centuries`;
    return 'Billions of years (practically unbreakable)';
  },

  /* ---------- Brute-force link speed odds ---------- */
  linkSpeed(entropy) {
    if (entropy < 28) return { label: 'Cracked instantly', odds: '1 in 1' };
    if (entropy < 36) return { label: 'Cracked within minutes', odds: '1 in 10' };
    if (entropy < 60) return { label: 'Cracked within months', odds: '1 in 100' };
    if (entropy < 80) return { label: 'Safe for decades', odds: '1 in 10,000,000' };
    return { label: 'Effectively unbreakable', odds: '1 in 10^20' };
  },

  /* ---------- Common password detection ---------- */
  isCommon(pw) {
    return this.commonList.includes(pw.toLowerCase());
  },

  /* ---------- Detect leaked password via web API (HaveIBeenPwned k-anonymity) ---------- */
  async checkBreached(pw) {
    try {
      const hash = await this.sha1(pw);
      const prefix = hash.slice(0, 5);
      const suffix = hash.slice(5).toUpperCase();
      const res = await fetch(`https://api.pwnedpasswords.com/range/${prefix}`);
      if (!res.ok) return 0;
      const text = await res.text();
      const match = text.split('\r\n').find(line => line.split(':')[0] === suffix);
      return match ? parseInt(match.split(':')[1], 10) : 0;
    } catch {
      return 0;
    }
  },

  async sha1(str) {
    const data = new TextEncoder().encode(str);
    const buf = await crypto.subtle.digest('SHA-1', data);
    return [...new Uint8Array(buf)].map(b => b.toString(16).padStart(2, '0')).join('');
  },

  /* ---------- Security recommendations building ---------- */
  buildRecommendations(result) {
    const recs = [];
    const { checks, length } = result;

    if (!checks.length8) recs.push({
      severity: 'high',
      title: 'Increase password length',
      desc: 'Your password is shorter than 8 characters. Longer passwords are exponentially harder to brute-force. Aim for 12-16+ characters.'
    });
    if (!checks.uppercase) recs.push({
      severity: 'medium',
      title: 'Add uppercase letters',
      desc: 'Mixed-case passwords dramatically expand the search space. Include letters like A-Z.'
    });
    if (!checks.lowercase) recs.push({
      severity: 'medium',
      title: 'Add lowercase letters',
      desc: 'Include lowercase letters to increase entropy and resist dictionary attacks.'
    });
    if (!checks.numbers) recs.push({
      severity: 'medium',
      title: 'Include numbers',
      desc: 'Numbers expand character variety. Avoid common sequences like 1234 or 0000.'
    });
    if (!checks.special) recs.push({
      severity: 'medium',
      title: 'Use special characters',
      desc: 'Symbols like @ # $ % ^ & * add significant strength. Combine with letters/numbers.'
    });
    if (!checks.noRepeat) recs.push({
      severity: 'high',
      title: 'Remove repeated characters',
      desc: 'Your password contains a character repeated 3+ times in a row. This weakens it.'
    });
    if (!checks.noSequential) recs.push({
      severity: 'high',
      title: 'Avoid sequential patterns',
      desc: 'Sequences like abc or 123 are the first things attackers try.'
    });
    if (result.isCommon) recs.push({
      severity: 'critical',
      title: 'Dangerously common password',
      desc: `"${result.placeholder}" appears in the world\'s most-used password lists. Change it immediately.`
    });
    if (recs.length === 0) recs.push({
      severity: 'low',
      title: 'Password looks solid',
      desc: 'Great job! Consider using a passphrase of unrelated words and enabling 2FA everywhere.'
    });
    return recs;
  },

  /* ---------- Full analysis pipeline ---------- */
  async analyze(pw) {
    const placeholder = pw.slice(0, 2) + '********' + pw.slice(-1);
    const entropy = this.calculateEntropy(pw);
    const length = pw.length;

    const checks = {
      length8: length >= 8,
      length12: length >= 12,
      lowercase: /[a-z]/.test(pw),
      uppercase: /[A-Z]/.test(pw),
      numbers: /[0-9]/.test(pw),
      special: /[^A-Za-z0-9]/.test(pw),
      noRepeat: !/(.)\1{2,}/.test(pw),
      noSequential: !/(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|012|123|234|345|456|567|678|789)/i.test(pw),
    };

    let score = Object.values(checks).filter(Boolean).length;

    let label, strengthColor;
    if (score <= 2) { label = 'WEAK'; strengthColor = 'weak'; }
    else if (score <= 4) { label = 'FAIR'; strengthColor = 'medium'; }
    else if (score <= 6) { label = 'STRONG'; strengthColor = 'strong'; }
    else { label = 'EXCELLENT'; strengthColor = 'excellent'; }

    const isCommon = this.isCommon(pw);
    const crackTime = this.estimateCrackTime(entropy);
    const link = this.linkSpeed(entropy);
    const breached = await this.checkBreached(pw);

    const result = {
      placeholder, score, entropy: Math.round(entropy * 100) / 100,
      label, strengthColor, length,
      has_uppercase: checks.uppercase, has_lowercase: checks.lowercase,
      has_numbers: checks.numbers, has_special: checks.special,
      crackTime, linkLabel: link.label, linkOdds: link.odds,
      isCommon, breached, checks,
    };
    result.recommendations = this.buildRecommendations(result);
    return result;
  },

  /* ---------- Render result into analyzer page ---------- */
  renderResult(result, containerId) {
    const box = document.getElementById(containerId || 'analysis-result');
    if (!box) return;
    box.classList.add('show');

    const commonAlert = result.isCommon
      ? '<div class="common-alert show"><span>&#9888;</span><div><strong>COMMON PASSWORD DETECTED!</strong><br>This password (or a variant) is in the world\'s top breached password list &mdash; ' + (result.breached > 0 ? 'it has appeared in <b>' + result.breached.toLocaleString() + '</b> data breaches.' : 'use it at your own risk.') + '</div></div>'
      : '';

    const breachAlert = !result.isCommon && result.breached > 0
      ? '<div class="common-alert show"><span>&#9760;</span><div><strong>LEAKED PASSWORD</strong><br>This password was found in ' + result.breached.toLocaleString() + ' real-world data breaches. Do NOT use it.</div></div>'
      : '';

    box.innerHTML = `
      <div class="result-header">
        <div class="stats-grid result-head">
          <div class="stat-box">
            <div class="stat-value score-${result.strengthColor}">${result.score}/8</div>
            <div class="stat-label">Complexity Score</div>
          </div>
          <div class="stat-box">
            <div class="stat-value" style="font-size:1.9rem; color:${result.strengthColor==='weak'?'var(--toxic-red)':result.strengthColor==='medium'?'var(--warning-amber)':result.strengthColor==='strong'?'var(--matrix-green)':'var(--neon-cyan)'}">${result.label}</div>
            <div class="stat-label">Rating</div>
          </div>
        </div>
      </div>

      ${commonAlert}
      ${breachAlert}

      <div class="stats-grid result-stats">
        <div class="stat-box"><div class="stat-value">${result.length}</div><div class="stat-label">Length</div></div>
        <div class="stat-box"><div class="stat-value">${result.entropy}</div><div class="stat-label">Entropy (bits)</div></div>
        <div class="stat-box"><div class="stat-value">${result.crackTime}</div><div class="stat-label">Est. Crack Time</div></div>
        <div class="stat-box"><div class="stat-value">${result.linkLabel}</div><div class="stat-label">Link Speed Risk</div></div>
        <div class="stat-box"><div class="stat-value">${result.isCommon ? 'YES' : 'NO'}</div><div class="stat-label">Common List</div></div>
        <div class="stat-box"><div class="stat-value">${result.breached > 0 ? result.breached.toLocaleString() : '0'}</div><div class="stat-label">Breaches Found</div></div>
      </div>

      <div class="chart-container">
        <h3><span style="color:var(--matrix-green)">▼</span> Character Analysis</h3>
        <div class="criteria-list">
          ${['length8','lowercase','uppercase','numbers','special','noRepeat','noSequential'].map(k => {
            const labels = { length8:'8+ characters', lowercase:'Lowercase (a-z)', uppercase:'Uppercase (A-Z)', numbers:'Numbers (0-9)', special:'Special symbols', noRepeat:'No repeats', noSequential:'No sequences' };
            return `<li class="${result.checks[k] ? 'pass' : 'fail'}"><span class="crit-icon">${result.checks[k] ? '&#10003;' : '&#10007;'}</span> ${labels[k]}</li>`;
          }).join('')}
        </div>
      </div>

      <div style="margin-top:22px; display:flex; gap:12px; flex-wrap:wrap;">
        <button class="btn btn-sm btn-cyan" onclick="PSA_Analyzer.saveResult(PREV_RESULT)">Save To History</button>
        <button class="btn btn-sm" onclick="PSA_Report.generateFromResult(PREV_RESULT)">Generate Report</button>
        <button class="btn btn-sm btn-red" id="generate-suggest-btn" onclick="PSA_Analyzer.generateStrongSuggestion()">Generate Strong Password</button>
      </div>

      <div id="generated-password" style="margin-top:16px; display:none;">
        <div class="alert alert-success show">Suggested strong password generated.</div>
        <div class="analyzer-panel" style="padding:18px; margin:0; background:var(--bg-deep);">
          <div id="generated-pw-value" style="font-family:var(--font-terminal); font-size:1.2rem; color:var(--neon-cyan); word-break:break-all; margin-bottom:10px;"></div>
          <div style="display:flex; gap:10px;">
            <button class="btn btn-sm btn-cyan" onclick="PSA_Analyzer.copyGenerated()">Copy to Clipboard</button>
            <button class="btn btn-sm" onclick="PSA_Analyzer.useGenerated()">Use This Password</button>
          </div>
        </div>
      </div>
    `;
  },

  generateStrongSuggestion() {
    const L = 'abcdefghjkmnpqrstuvwxyz';
    const U = L.toUpperCase();
    const N = '23456789';
    const S = '!@#$%^&*()-_=+[]{}<>?';
    const pool = L + U + N + S;
    let pw = '';
    for (let i = 0; i < 16; i++) pw += pool[Math.floor(Math.random() * pool.length)];
    pw = pw
      .replace(/./, c => U[Math.floor(Math.random() * U.length)])
      .replace(/.$/, c => N[Math.floor(Math.random() * N.length)]);
    const box = document.getElementById('generated-password');
    const val = document.getElementById('generated-pw-value');
    box.style.display = 'block';
    val.textContent = pw;
    this._generated = pw;
  },

  copyGenerated() {
    if (!this._generated) return;
    navigator.clipboard.writeText(this._generated).then(() => PSA.toast('Copied to clipboard', 'success'));
  },

  useGenerated() {
    const input = document.getElementById('password');
    if (!input || !this._generated) return;
    input.value = this._generated;
    input.dispatchEvent(new Event('input'));
    PSA.toast('Generated password loaded into analyzer', 'info');
  },

  saveResult(result) {
    if (!PSA.session) { PSA.toast('Login required to save history', 'error'); return; }
    PSA.api('history.php', 'POST', {
      action: 'save',
      user_id: PSA.session.user.id,
      result: {
        password_placeholder: result.placeholder,
        score: result.score,
        label: result.label,
        length: result.length,
        has_uppercase: result.has_uppercase ? 1 : 0,
        has_lowercase: result.has_lowercase ? 1 : 0,
        has_numbers: result.has_numbers ? 1 : 0,
        has_special: result.has_special ? 1 : 0,
        character_count: result.entropy,
        link_speed: result.linkLabel,
        estimated_crack_time: result.crackTime,
        is_common: result.isCommon ? 1 : 0,
        breached_count: result.breached,
        entropy: result.entropy,
        analysis_notes: result.recommendations.map(r => r.title).join('; ')
      }
    }).then(res => {
      if (res.success) PSA.toast('Analysis saved to history', 'success');
      else PSA.toast(res.message || 'Failed to save', 'error');
    }).catch(() => PSA.toast('Could not reach history API', 'error'));
  }
};