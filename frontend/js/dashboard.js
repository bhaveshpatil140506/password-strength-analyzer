/* ============================================================
   PASSWORD STRENGTH ANALYZER - USER DASHBOARD
   ============================================================ */

const PSA_Dashboard = {

  async loadStats() {
    if (!PSA.session) return;
    try {
      const res = await PSA.api('admin.php', 'POST', { action: 'user_stats', user_id: PSA.session.user.id });
      if (!res.success) return;

      const s = res.data;
      const counters = {
        total: s.total_analyses, avg: s.avg_strength ? s.avg_strength.toFixed(1) : '0',
        weak: s.weak, strong: s.strong, common: s.common, breaches: s.breaches,
      };
      for (const [id, val] of Object.entries(counters)) {
        const el = document.getElementById(`stat-${id}`);
        if (el) this.animateCount(el, val);
      }
      document.getElementById('user-name-display').textContent = PSA.session.user.fullname || PSA.session.user.username;
      this.renderStreakBars(s);
    } catch (err) {
      console.warn('Stats load failed, using demo mode', err);
      this.demoMode();
    }
  },

  demoMode() {
    const counters = { total: 24, avg: '4.2', weak: 6, strong: 14, common: 3, breaches: 2 };
    for (const [id, val] of Object.entries(counters)) {
      const el = document.getElementById(`stat-${id}`);
      if (el) this.animateCount(el, val);
    }
    document.getElementById('user-name-display').textContent = PSA.session.user.username;
    this.renderStreakBars({ weak: 6, medium: 4, strong: 14 });
  },

  animateCount(el, target) {
    const dur = 1200;
    const start = performance.now();
    const step = now => {
      const p = Math.min((now - start) / dur, 1);
      const eased = 1 - Math.pow(1 - p, 3);
      el.textContent = Math.floor(target * eased) + (String(target).includes('.') && p === 1 ? ('.' + String(target).split('.')[1]) : '');
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  },

  /* Demo chart data when API unavailable */
  demoChart() {
    const canvas = document.getElementById('strength-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const data = [6, 4, 9, 5];
    const total = data.reduce((a, b) => a + b, 0);
    let start = -Math.PI / 2;
    const colors = ['var(--toxic-red)', 'var(--warning-amber)', 'var(--matrix-green)', 'var(--neon-cyan)'];
    data.forEach((v, i) => {
      const angle = (v / total) * 2 * Math.PI;
      ctx.beginPath();
      ctx.moveTo(canvas.width / 2, canvas.height / 2);
      ctx.arc(canvas.width / 2, canvas.height / 2, canvas.height / 2 - 12, start, start + angle);
      ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue(colors[i]).trim();
      ctx.fill();
      start += angle;
    });
    ctx.strokeStyle = '#0a0f0d';
    ctx.lineWidth = 4;
    ctx.beginPath();
    ctx.arc(canvas.width / 2, canvas.height / 2, canvas.height / 2 - 12, 0, 2 * Math.PI);
    ctx.stroke();
  },

  renderStreakBars(s) {
    const canvas = document.getElementById('strength-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const data = [s.weak || 5, s.medium || 3, s.strong || 8, s.excellent || 4];
    const labels = ['WEAK', 'FAIR', 'STRONG', 'EXCEL'];
    const colors = ['#ff2d55', '#ffb020', '#00ff88', '#00f0ff'];
    const max = Math.max(...data, 1);
    const pad = 50;
    const chartW = canvas.width - pad * 2;
    const chartH = canvas.height - pad;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const strideOn = () => {
      const grad = ctx.createLinearGradient(0, 0, canvas.width, 0);
      grad.addColorStop(0, '#00ff88');
      grad.addColorStop(1, '#00f0ff');
      ctx.strokeStyle = grad;
      ctx.globalAlpha = 0.25;
      ctx.lineWidth = 1;
      for (let i = 0; i < canvas.width; i += 25) {
        ctx.beginPath();
        ctx.moveTo(i, pad - 20);
        ctx.lineTo(i, canvas.height - 20);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
    };
    strideOn();

    data.forEach((v, i) => {
      const bw = chartW / data.length - 22;
      const x = pad + i * (chartW / data.length) + 11;
      const bh = (v / max) * (chartH - 50);
      const y = canvas.height - 20 - bh;

      ctx.fillStyle = colors[i];
      ctx.shadowColor = colors[i];
      ctx.shadowBlur = 14;
      ctx.fillRect(x, y, bw, bh);
      ctx.shadowBlur = 0;

      ctx.fillStyle = '#d7ffe9';
      ctx.font = 'bold 15px Courier New';
      ctx.textAlign = 'center';
      ctx.fillText(v, x + bw / 2, y - 8);

      ctx.fillStyle = '#7cc79a';
      ctx.font = '11px Courier New';
      ctx.fillText(labels[i], x + bw / 2, canvas.height - 4);
    });
  },

  async loadRecent() {
    const tbody = document.getElementById('recent-analyses');
    if (!tbody) return;
    try {
      const res = await PSA.api('history.php', 'POST', { action: 'list', user_id: PSA.session.user.id, limit: 5 });
      const rows = res.success && res.data.length ? res.data : this.demoRows();
      tbody.innerHTML = rows.map(r => `
        <tr>
          <td class="terminal-text">${PSA.escapeHtml(r.password_placeholder || '')}</td>
          <td><span class="badge badge-${(r.strength_label || '').toLowerCase() === 'weak' ? 'weak' : (r.strength_label || '').toLowerCase() === 'fair' ? 'medium' : r.strength_label === 'EXCELLENT' ? 'excellent' : 'strong'}">${PSA.escapeHtml(r.strength_label || '')}</span></td>
          <td>${r.strength_score || 0}/8</td>
          <td>${PSA.escapeHtml(r.estimated_crack_time || '-')}</td>
          <td>${r.is_common ? '<span class="badge badge-common">COMMON</span>' : r.breached_count > 0 ? '<span class="badge badge-common">LEAKED</span>' : '<span style="color:var(--text-muted)">CLEAN</span>'}</td>
          <td class="muted">${PSA.fmtDate(r.analyzed_at)}</td>
        </tr>`).join('');
    } catch {
      tbody.innerHTML = '<tr><td colspan="6" class="empty-state">UNABLE TO REACH HISTORY API. CONNECTING TO DEMO MODE...</td></tr>';
    }
  },

  demoRows() {
    return [
      { password_placeholder: 'P@ssw0rd!2024', strength_label: 'STRONG', strength_score: 6, estimated_crack_time: '3 centuries', is_common: 0, breached_count: 0, analyzed_at: '2026-09-18 08:42' },
      { password_placeholder: 'iloveyou', strength_label: 'WEAK', strength_score: 1, estimated_crack_time: 'Instantly', is_common: 1, breached_count: 40, analyzed_at: '2026-09-18 08:10' },
      { password_placeholder: 'Tr0ub4dor&3', strength_label: 'EXCELLENT', strength_score: 8, estimated_crack_time: '24 billion years', is_common: 0, breached_count: 0, analyzed_at: '2026-09-17 19:33' },
    ];
  },

  bind() {
    if (!PSA.session) { window.location.href = 'login.html'; return; }
    this.loadStats();
    this.loadRecent();
  }
};

document.addEventListener('DOMContentLoaded', () => PSA_Dashboard.bind());