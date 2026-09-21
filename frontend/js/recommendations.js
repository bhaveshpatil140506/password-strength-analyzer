/* ============================================================
   PASSWORD STRENGTH ANALYZER - RECOMMENDATIONS MODULE
   ============================================================ */

const PSA_Recommendations = {

  masterTips() {
    return [
      { sev: 'critical', icon: '☠', title: 'Never reuse passwords', desc: 'Each account needs its own unique password. A breach on one service must not cascade to your email, banking, or social accounts.' },
      { sev: 'high', icon: '⚔', title: 'Use a passphrase', desc: 'Combine 4-5 unrelated words with symbols and numbers, e.g. "Blue#Monkey$Train2026". Easy to remember, brutal to crack.' },
      { sev: 'high', icon: '🔐', title: 'Enable 2-Factor Authentication', desc: 'Even a stolen password becomes useless with 2FA. Prefer authenticator apps over SMS.' },
      { sev: 'medium', icon: '🗝', title: 'Use a password manager', desc: 'Generate and store strong random passwords per site. You only need to remember one master password.' },
      { sev: 'medium', icon: '🔄', title: 'Rotate critical passwords regularly', desc: 'Changing passwords for email and banking every 90 days drastically shrinks your exposure window.' },
      { sev: 'medium', icon: '🧹', title: 'Audit old accounts & data breaches', desc: 'Periodically check haveibeenpwned.com. Delete accounts you no longer use.' },
      { sev: 'low', icon: '🛡', title: 'Avoid personal data in passwords', desc: 'Birthdays, names, city names, and pet names are obtainable from social media. Keep them out of your passwords.' },
      { sev: 'low', icon: '💠', title: 'Beware of phishing', desc: 'Always verify the URL before entering credentials. Password managers help by auto-filling only on the real domain.' },
    ];
  },

  render() {
    const box = document.getElementById('rec-list');
    if (!box) return;
    const wide = box.dataset.wide === 'true';
    const tips = wide ? this.masterTips() : this.masterTips().slice(0, 4);
    box.innerHTML = tips.map(t => `
      <div class="rec-item severity-${t.sev}">
        <span class="rec-icon">${t.icon}</span>
        <div>
          <div class="rec-title">${t.title}</div>
          <div class="rec-desc">${t.desc}</div>
        </div>
      </div>`).join('');
  },

  /* Password history (analysis-based) recommendations */
  async loadFromHistory() {
    const box = document.getElementById('rec-history');
    if (!box || !PSA.session) return;
    try {
      const res = await PSA.api('history.php', 'POST', { user_id: PSA.session.user.id });
      const rows = (res.success ? res.data : []);
      if (!rows.length) {
        box.innerHTML = '<div class="empty-state">NO ANALYSIS DATA YET — RUN AN ANALYSIS TO GET PERSONALIZED TIPS.</div>';
        return;
      }
      const tips = [];
      rows.forEach(r => {
        const masked = PSA.escapeHtml(r.password_placeholder || '');
        if (r.is_common) tips.push({ sev: 'critical', icon: '&#9760;', title: 'Common password flagged', desc: '"' + masked + '" was detected as a widely-used weak password. Change it immediately.' });
        if (r.strength_score <= 4) tips.push({ sev: 'high', icon: '&#9876;', title: 'Weak score (' + r.strength_score + '/8)', desc: 'Analysis #' + r.id + ' shows weak protection. Re-run through the analyzer and follow strengthening tips.' });
        if (r.breached_count > 0) tips.push({ sev: 'high', icon: '&#128272;', title: 'Found in ' + r.breached_count + ' breaches', desc: 'The analyzed value (#' + r.id + ') matches known breach data. Stop using it across all sites.' });
        if (r.has_uppercase && r.has_numbers && r.has_special && r.strength_score >= 6) tips.push({ sev: 'low', icon: '&#9989;', title: 'Healthy password detected', desc: 'Analysis #' + r.id + ' scores well. Maintain this standard everywhere.' });
      });
      box.innerHTML = tips.slice(0, 8).map(t => `
        <div class="rec-item severity-${t.sev}">
          <span class="rec-icon">${t.icon}</span>
          <div><div class="rec-title">${t.title}</div><div class="rec-desc">${t.desc}</div></div>
        </div>`).join('') || '<div class="empty-state">NO PERSONALIZED TIPS AVAILABLE.</div>';
    } catch {
      box.innerHTML = '<div class="empty-state">UNABLE TO LOAD PERSONALIZED RECOMMENDATIONS.</div>';
    }
  },

  bind() {
    if (window.location.pathname.includes('recommendations')) {
      this.render();
      this.loadFromHistory();
    }
  }
};

document.addEventListener('DOMContentLoaded', () => PSA_Recommendations.bind());