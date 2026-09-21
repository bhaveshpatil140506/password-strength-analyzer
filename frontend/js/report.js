/* ============================================================
   PASSWORD STRENGTH ANALYZER - REPORT GENERATION MODULE
   ============================================================ */

const PSA_Report = {

  /* ---------- Generate a full report from history data ---------- */
  async generateFromResult(result) {
    if (!PSA.session) { PSA.toast('Login required', 'error'); return; }
    try {
      const res = await PSA.api('report.php', 'POST', {
        user_id: PSA.session.user.id,
        report_type: 'single',
        result_data: result,
      });
      if (res.success) {
        PSA.toast('Report generated', 'success');
        window.location.href = 'report.html';
      } else {
        PSA.toast(res.message || 'Report failed', 'error');
      }
    } catch { PSA.toast('Report API unreachable', 'error'); }
  },

  /* ---------- Full report (uses history data) ---------- */
  async loadFullReport() {
    const content = document.getElementById('report-content');
    if (!content) return;
    if (!PSA.session) { window.location.href = 'login.html'; return; }

    const stamp = document.getElementById('report-timestamp');
    const username = document.getElementById('report-username');
    if (stamp) stamp.textContent = new Date().toLocaleString();
    if (username) username.textContent = PSA.session.user.username;

    content.innerHTML = '<div class="loading show"><div class="typing-indicator">COMPILING REPORT <span>.</span><span>.</span><span>.</span></div></div>';

    try {
      const res = await PSA.api('report.php', 'POST', { action: 'full', user_id: PSA.session.user.id });
      if (!res.success) { content.innerHTML = `<div class="empty-state">${PSA.escapeHtml(res.message || 'REPORT FAILED')}</div>`; return; }
      this.renderFull(res.data);
    } catch {
      this.renderDemo();
    }
  },

  renderFull(d) {
    const content = document.getElementById('report-content');
    if (!content || !d) return;

    content.innerHTML = `
      <div class="card" style="margin-bottom:22px;">
        <h3 style="color:var(--neon-cyan)">▌EXECUTIVE SUMMARY</h3>
        <div class="stats-grid">
          <div class="stat-box"><div class="stat-value">${d.total_analyses}</div><div class="stat-label">Total Analyses</div></div>
          <div class="stat-box"><div class="stat-value">${d.avg_strength ?? 0}</div><div class="stat-label">Avg Score /8</div></div>
          <div class="stat-box"><div class="stat-value" style="color:var(--toxic-red)">${d.weak_passwords ?? 0}</div><div class="stat-label">Weak</div></div>
          <div class="stat-box"><div class="stat-value" style="color:var(--warning-amber)">${d.medium_passwords ?? 0}</div><div class="stat-label">Fair</div></div>
          <div class="stat-box"><div class="stat-value" style="color:var(--matrix-green)">${d.strong_passwords ?? 0}</div><div class="stat-label">Strong+</div></div>
          <div class="stat-box"><div class="stat-value" style="color:var(--toxic-red)">${d.common_detected ?? 0}</div><div class="stat-label">Common Flags</div></div>
        </div>
        <p class="muted" style="margin-top:14px;">
          Your password hygiene is <b>${this.healthLabel(d.avg_strength ?? 3)}</b>.
          ${(d.common_detected ?? 0) > 0 ? `<span class="danger">⚠ ${d.common_detected} analyzed values appear on global breach lists — prioritize changing these.</span>` : 'No analyzed values matched global common-password lists.'}
          ${(d.weak_passwords ?? 0) > 0 ? ` ${d.weak_passwords} weak entries bring your average down.` : ' The majority of your entries score well.'}
        </p>
      </div>

      <div class="chart-container">
        <h3>▌STRENGTH DISTRIBUTION</h3>
        <canvas id="report-chart" width="560" height="220" style="display:block; margin:0 auto;"></canvas>
      </div>

      <div class="chart-container" style="margin-top:22px;">
        <h3>▌PARTICULARS PER ANALYSIS</h3>
        <div class="table-wrapper" style="margin-top:14px;">
          <table>
            <thead><tr><th>#</th><th>Password</th><th>Score</th><th>Label</th><th>Entropy</th><th>Crack Time</th><th>Status</th></tr></thead>
            <tbody>
              ${(d.analyses || []).map(a => `<tr>
                <td>${a.id}</td>
                <td class="terminal-text">${PSA.escapeHtml(a.password_placeholder)}</td>
                <td>${a.strength_score}/8</td>
                <td><span class="badge badge-${(a.strength_label||'').toLowerCase()==='weak'?'weak':(a.strength_label||'').toLowerCase()==='fair'?'medium':a.strength_label==='EXCELLENT'?'excellent':'strong'}">${PSA.escapeHtml(a.strength_label || '')}</span></td>
                <td>${a.entropy} bits</td>
                <td>${PSA.escapeHtml(a.estimated_crack_time || '-')}</td>
                <td>${a.is_common ? '<span class="badge badge-common">COMMON</span>' : (a.breached_count||0) > 0 ? '<span class="badge badge-common">LEAKED</span>' : '<span style="color:var(--matrix-green)">OK</span>'}</td>
              </tr>`).join('')}
            </tbody>
          </table>
        </div>
      </div>

      <div class="chart-container" style="margin-top:22px;">
        <h3>▌RECOMMENDATIONS PACKAGE</h3>
        <div style="margin-top:14px;">
          ${(d.recommendations || []).map(r => `<div class="rec-item severity-${r.severity}"><span class="rec-icon">●</span><div><div class="rec-title">${PSA.escapeHtml(r.title)}</div><div class="rec-desc">${PSA.escapeHtml(r.desc)}</div></div></div>`).join('')}
        </div>
      </div>

      <div style="margin-top:22px; display:flex; gap:12px; flex-wrap:wrap;">
        <button class="btn btn-solid" onclick="window.print()">Download / Print Report</button>
        <button class="btn btn-cyan" onclick="PSA_Report.exportCSV()">Export CSV</button>
        <button class="btn" onclick="PSA_Report.exportJSON()">Export JSON</button>
      </div>
    `;

    this.renderReportChart(d);
    PSA_Report._data = d;
  },

  renderReportChart(d) {
    const canvas = document.getElementById('report-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const dist = [d.weak_passwords || 0, d.medium_passwords || 0, d.strong_passwords || 0, d.excellent_passwords || 0];
    const labels = ['WEAK', 'FAIR', 'STRONG', 'EXCELLENT'];
    const colors = ['#ff2d55', '#ffb020', '#00ff88', '#00f0ff'];
    const max = Math.max(...dist, 1);

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const top = 30, bottom = 40, left = 40, right = 20;
    const bw = ((canvas.width - left - right) / dist.length) * 0.6;

    dist.forEach((v, i) => {
      const bh = (v / max) * (canvas.height - top - bottom);
      const x = left + i * ((canvas.width - left - right) / dist.length);
      const y = canvas.height - bottom - bh;

      const grad = ctx.createLinearGradient(0, y, 0, canvas.height - bottom);
      grad.addColorStop(0, colors[i]);
      grad.addColorStop(1, colors[i] + '33');
      ctx.fillStyle = grad;
      ctx.shadowColor = colors[i];
      ctx.shadowBlur = 10;
      ctx.fillRect(x, y, bw, bh);
      ctx.shadowBlur = 0;

      ctx.fillStyle = '#d7ffe9';
      ctx.font = 'bold 14px Courier New';
      ctx.textAlign = 'center';
      ctx.fillText(v, x + bw / 2, y - 8);

      ctx.fillStyle = '#7cc79a';
      ctx.font = '12px Courier New';
      ctx.fillText(labels[i], x + bw / 2, canvas.height - 18);
    });
  },

  renderDemo() {
    const d = {
      total_analyses: 24, avg_strength: 4.2, weak_passwords: 6, medium_passwords: 4,
      strong_passwords: 14, excellent_passwords: 0, common_detected: 3, analyses: [],
      recommendations: [{ severity: 'low', title: 'DEMO DATA', desc: 'Backend report API unreachable — showing sample figures. Start the XAMPP/PHP server to persist reports.' }]
    };
    this.renderFull(d);
    PSA.toast('Displaying demo report (PHP API offline)', 'info');
  },

  healthLabel(avg) {
    if (avg >= 6.5) return 'EXCELLENT';
    if (avg >= 5) return 'GOOD';
    if (avg >= 4) return 'AVERAGE';
    return 'POOR — IMPROVEMENT REQUIRED';
  },

  exportCSV() {
    const d = PSA_Report._data;
    if (!d || !d.analyses.length) { PSA.toast('Nothing to export', 'error'); return; }
    const header = ['ID', 'Password', 'Score', 'Label', 'Entropy', 'CrackTime', 'Common', 'Breaches'];
    const rows = d.analyses.map(a => [a.id, `"${a.password_placeholder}"`, a.strength_score, a.strength_label, a.entropy, `"${a.estimated_crack_time}"`, a.is_common, a.breached_count]);
    const csv = [header, ...rows].map(r => r.join(',')).join('\n');
    this.download(`PassGuard_Report_${Date.now()}.csv`, csv, 'text/csv');
  },

  exportJSON() {
    const d = PSA_Report._data;
    if (!d) { PSA.toast('Nothing to export', 'error'); return; }
    this.download(`PassGuard_Report_${Date.now()}.json`, JSON.stringify(d, null, 2), 'application/json');
  },

  download(name, content, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = name;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
    PSA.toast(`${name} downloaded`, 'success');
  },

  bind() {
    if (window.location.pathname.includes('report')) this.loadFullReport();
  }
};

document.addEventListener('DOMContentLoaded', () => PSA_Report.bind());