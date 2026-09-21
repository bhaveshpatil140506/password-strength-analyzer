/* ============================================================
   PASSWORD STRENGTH ANALYZER - PASSWORD HISTORY MODULE
   ============================================================ */

const PSA_History = {

  async load() {
    if (!PSA.session) return;
    const tbody = document.getElementById('history-tbody');
    const tbodyAll = document.getElementById('history-all-tbody');
    const countEl = document.getElementById('history-count');
    if (!tbody) return;

    try {
      const res = await PSA.api('history.php', 'POST', { user_id: PSA.session.user.id });
      const rows = res.success ? res.data : [];
      countEl.textContent = `[ ${rows.length} RECORDS ]`;

      const render = rows.map(r => `
        <tr>
          <td class="terminal-text">${PSA.escapeHtml(r.id || '')}</td>
          <td class="terminal-text">${PSA.escapeHtml(r.password_placeholder || '')}</td>
          <td><span class="badge badge-${(r.strength_label || '').toLowerCase() === 'weak' ? 'weak' : (r.strength_label || '').toLowerCase() === 'fair' ? 'medium' : r.strength_label === 'EXCELLENT' ? 'excellent' : 'strong'}">${PSA.escapeHtml(r.strength_label || '')}</span></td>
          <td>${r.strength_score || 0}/8</td>
          <td>${r.entropy || 0} bits</td>
          <td nowrap>${PSA.escapeHtml(r.estimated_crack_time || '-')}</td>
          <td>${r.is_common ? '<span class="badge badge-common">COMMON</span>' : '<span style="color:var(--matrix-green)">SAFE</span>'}</td>
          <td>${r.breached_count > 0 ? `<span class="badge badge-common">${r.breached_count}×</span>` : '<span style="color:var(--text-muted)">-</span>'}</td>
          <td class="muted nowrap">${PSA.fmtDate(r.analyzed_at)}</td>
          <td>
            <button class="action-btn" onclick="PSA_History.detail(${r.id})">VIEW</button>
            <button class="action-btn danger-btn" onclick="PSA_History.deleteRow(${r.id})">DELETE</button>
          </td>
        </tr>`).join('');

      const empty = `<tr><td colspan="10" class="empty-state">NO ANALYSES FOUND. RUN YOUR FIRST ANALYSIS.</td></tr>`;
      tbody.innerHTML = rows.length ? render : empty;
      if (tbodyAll) tbodyAll.innerHTML = rows.length ? render : empty;

      const feed = document.getElementById('history-feed');
      if (feed) {
        feed.innerHTML = rows.slice().reverse().slice(0, 12).map(r => `
          <div class="log-line ${(r.strength_label||'')==='WEAK'?'log-danger':(r.strength_label||'')==='FAIR'?'log-warn':'log-success'}">
            <span class="log-time">${PSA.fmtDate(r.analyzed_at)}</span>
            analysis :: ${PSA.escapeHtml(r.password_placeholder)} -> ${r.strength_label} (${r.strength_score}/8)${r.is_common ? ' :: FLAGGED COMMON' : ''}
          </div>`).join('') || '<div class="log-line">NO DATA IN FEED</div>';
      }
    } catch {
      tbody.innerHTML = `<tr><td colspan="10" class="empty-state">UNABLE TO REACH HISTORY API. CONNECTING TO DEMO DATA...</td></tr>`;
    }
  },

  async detail(id) {
    const res = await PSA.api('history.php', 'POST', { action: 'detail', user_id: PSA.session.user.id, id });
    const modal = document.getElementById('detail-modal');
    if (!modal || !res.success) { PSA.toast('Detail unavailable', 'error'); return; }
    const d = res.data;
    modal.querySelector('.modal-body').innerHTML = `
      <div class="stats-grid" style="grid-template-columns:repeat(3,1fr);">
        <div class="stat-box"><div class="stat-value">${d.strength_score}/8</div><div class="stat-label">Score</div></div>
        <div class="stat-box"><div class="stat-value">${d.entropy}</div><div class="stat-label">Entropy</div></div>
        <div class="stat-box"><div class="stat-value">${d.length}</div><div class="stat-label">Length</div></div>
      </div>
      <p class="muted" style="margin-top:14px;">Crack time: <b class="cyan-text">${PSA.escapeHtml(d.estimated_crack_time || '-')}</b></p>
      <p class="muted">Common flagged: <b>${d.is_common ? 'YES' : 'NO'}</b> | Breaches: <b>${d.breached_count || 0}</b></p>
      <p class="muted">Composition: UPPER[${d.has_uppercase?'✓':'✗'}] lower[${d.has_lowercase?'✓':'✗'}] num[${d.has_numbers?'✓':'✗'}] sym[${d.has_special?'✓':'✗'}]</p>
      <p class="muted">Notes: ${PSA.escapeHtml(d.analysis_notes || 'N/A')}</p>
    `;
    modal.classList.add('open');
  },

  async deleteRow(id) {
    if (!confirm(`Delete analysis record #${id}?`)) return;
    const res = await PSA.api('history.php', 'POST', { action: 'delete', user_id: PSA.session.user.id, id });
    PSA.toast(res.message || 'Record deleted', res.success ? 'success' : 'error');
    this.load();
  },

  bind() {
    if (!PSA.session) { window.location.href = 'login.html'; return; }
    this.load();
    const close = document.getElementById('modal-close');
    if (close) close.addEventListener('click', () => document.getElementById('detail-modal')?.classList.remove('open'));
  }
};

document.addEventListener('DOMContentLoaded', () => PSA_History.bind());