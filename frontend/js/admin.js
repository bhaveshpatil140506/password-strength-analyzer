/* ============================================================
   PASSWORD STRENGTH ANALYZER - ADMIN DASHBOARD
   ============================================================ */

const PSA_Admin = {

  loadOverview() {
    if (!PSA.session || !PSA.session.is_admin) { window.location.href = 'dashboard.html'; return; }
    try {
      PSA.api('admin.php', 'POST', { action: 'overview', admin_id: PSA.session.user.id }).then(res => {
        if (!res.success) throw new Error(res.message || 'failed');
        const d = res.data;
        this.animateNumber('users-total', d.total_users);
        this.animateNumber('passwords-total', d.total_passwords);
        this.animateNumber('common-total', d.common_passwords);
        this.animateNumber('breaches-total', d.total_breaches);
        this.animateNumber('reports-total', d.total_reports);
        this.animateNumber('active-today', d.active_today);
        document.getElementById('admin-stats-text').textContent =
          'TOTAL USERS :: ' + d.total_users + ' | ACTIVE TODAY :: ' + d.active_today + ' | RECENT LOGINS :: ' + d.recent_logins;
        this.loadUsers();
        this.loadActivity();
        if (d.week_daily && d.week_daily.length) this.renderWeekChart(d.week_daily);
      }).catch(() => {
        const status = document.getElementById('admin-stats-text');
        if (status) status.textContent = 'Admin data unavailable. Check the server connection and refresh.';
        PSA.toast('Could not load admin data.', 'error');
      });
    } catch (e) {
      PSA.toast('Could not load admin data.', 'error');
    }
  },

  animateNumber(id, target) {
    const el = document.getElementById(id);
    if (!el) return;
    const dur = 1100;
    const start = performance.now();
    const step = now => {
      const p = Math.min((now - start) / dur, 1);
      el.textContent = Math.floor(target * (1 - Math.pow(1 - p, 3)));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  },

  loadUsers() {
    const tbody = document.getElementById('users-tbody');
    if (!tbody) return;
    PSA.api('admin.php', 'POST', { action: 'users', admin_id: PSA.session.user.id }).then(res => {
      this.renderUsers(res.success ? res.data : []);
    }).catch(() => {
      tbody.innerHTML = '<tr><td colspan="9" class="empty-state">Could not load users. Refresh to retry.</td></tr>';
    });
  },

  renderUsers(rows) {
    const tbody = document.getElementById('users-tbody');
    if (!tbody) return;
    tbody.innerHTML = rows.map(u => {
      const actions = u.is_admin ? '' :
        '<button class="action-btn" onclick="PSA_Admin.toggleBan(' + u.id + ',' + (u.is_active ? 0 : 1) + ')">' + (u.is_active ? 'BAN' : 'UNBAN') + '</button>' +
        '<button class="action-btn danger-btn" onclick="PSA_Admin.deleteUser(' + u.id + ')">DELETE</button>';
      return '<tr class="' + (u.is_active ? '' : 'user-row-inactive') + '">' +
        '<td>' + u.id + '</td>' +
        '<td class="terminal-text">' + PSA.escapeHtml(u.username) + '</td>' +
        '<td>' + PSA.escapeHtml(u.fullname) + '</td>' +
        '<td>' + PSA.escapeHtml(u.email) + '</td>' +
        '<td>' + (u.is_admin ? '<span class="badge badge-excellent">ROOT</span>' : '<span class="badge badge-strong">USER</span>') + '</td>' +
        '<td>' + (u.is_active ? '<span class="badge badge-strong">ACTIVE</span>' : '<span class="badge badge-weak">BANNED</span>') + '</td>' +
        '<td class="muted">' + (u.analyses || 0) + '</td>' +
        '<td class="muted nowrap">' + (u.last_login || '-') + '</td>' +
        '<td>' + actions + '</td></tr>';
    }).join('') || '<tr><td colspan="9" class="empty-state">NO USERS</td></tr>';
  },

  toggleBan(id, state) {
    PSA.api('admin.php', 'POST', { action: 'toggle_ban', admin_id: PSA.session.user.id, target_id: id, state: state }).then(res => {
      PSA.toast(res.message || 'Status updated', res.success ? 'success' : 'error');
      this.loadUsers();
    });
  },

  deleteUser(id) {
    if (!confirm('Delete user #' + id + '? This removes their analyses and reports.')) return;
    PSA.api('admin.php', 'POST', { action: 'delete_user', admin_id: PSA.session.user.id, target_id: id }).then(res => {
      PSA.toast(res.message || 'User removed', res.success ? 'success' : 'error');
      this.loadUsers();
    });
  },

  loadActivity() {
    const feed = document.getElementById('admin-feed');
    if (!feed) return;
    PSA.api('admin.php', 'POST', { action: 'activity', admin_id: PSA.session.user.id }).then(res => {
      this.renderFeed(res.success ? res.data : []);
    }).catch(() => { feed.textContent = 'Could not load activity. Refresh to retry.'; });
  },

  renderFeed(lines) {
    const feed = document.getElementById('admin-feed');
    if (!feed) return;
    feed.innerHTML = lines.map(l => {
      return '<div class="log-line log-' + (l.type || 'info') + '">' +
        '<span class="log-time">' + (l.time || '') + '</span>' + PSA.escapeHtml(l.text || '') + '</div>';
    }).join('') || '<div class="log-line">NO ACTIVITY RECORDED</div>';
  },

  renderWeekChart(week) {
    const canvas = document.getElementById('week-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const labels = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN'];
    const max = Math.max.apply(null, week.concat([1]));
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const t = 30, b = 40, l = 40, r = 20;
    const bw = ((canvas.width - l - r) / 7) * 0.55;
    week.forEach((v, i) => {
      const bh = (v / max) * (canvas.height - t - b);
      const x = l + i * ((canvas.width - l - r) / 7);
      const y = canvas.height - b - bh;
      const grad = ctx.createLinearGradient(0, y, 0, canvas.height - b);
      grad.addColorStop(0, '#00ff88');
      grad.addColorStop(1, '#00cc6a33');
      ctx.fillStyle = grad;
      ctx.shadowColor = '#00ff88';
      ctx.shadowBlur = 8;
      ctx.fillRect(x, y, bw, bh);
      ctx.shadowBlur = 0;
      ctx.fillStyle = '#d7ffe9';
      ctx.font = 'bold 13px Courier New';
      ctx.textAlign = 'center';
      ctx.fillText(v, x + bw / 2, y - 8);
      ctx.fillStyle = '#7cc79a';
      ctx.font = '11px Courier New';
      ctx.fillText(labels[i], x + bw / 2, canvas.height - 18);
    });
  },

  bind() {
    if (!PSA.session) { window.location.href = 'login.html'; return; }
    if (!PSA.session.is_admin) {
      PSA.toast('Access denied - admin only', 'error');
      setTimeout(() => (window.location.href = 'dashboard.html'), 900);
      return;
    }
    document.getElementById('admin-name').textContent = PSA.session.user.username.toUpperCase();
    this.loadOverview();
  }
};

document.addEventListener('DOMContentLoaded', function () { PSA_Admin.bind(); });
