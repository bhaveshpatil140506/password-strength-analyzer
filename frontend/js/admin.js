/* ============================================================
   PASSWORD STRENGTH ANALYZER - ADMIN DASHBOARD MODULE
   ============================================================ */

const PSA_Admin = {

  loadOverview() {
    if (!PSA.session || !PSA.session.user.is_admin) { window.location.href = 'dashboard.html'; return; }
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
        PSA.toast('Admin API unreachable - using demo data', 'info');
        this.demoOverview();
      });
    } catch (e) {
      this.demoOverview();
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

  demoOverview() {
    const vals = { 'users-total': 128, 'passwords-total': 1456, 'common-total': 212, 'breaches-total': 87, 'reports-total': 34, 'active-today': 21 };
    for (const id in vals) this.animateNumber(id, vals[id]);
    document.getElementById('admin-stats-text').textContent =
      'TOTAL USERS :: 128 | ACTIVE TODAY :: 21 | RECENT LOGINS :: 14 (DEMO)';
    this.loadUsers(true);
    this.loadActivity(true);
    this.renderWeekChart([12, 18, 15, 22, 19, 27, 24]);
  },

  loadUsers(demo) {
    const tbody = document.getElementById('users-tbody');
    if (!tbody) return;
    if (demo) {
      this.renderUsers([
        { id: 1, fullname: 'System Administrator', username: 'admin', email: 'admin@psa.local', is_admin: 1, is_active: 1, last_login: '2026-09-18 08:40:00', analyses: 42 },
        { id: 2, fullname: 'Alice Johnson', username: 'alice_j', email: 'alice@mail.com', is_admin: 0, is_active: 1, last_login: '2026-09-18 07:10:00', analyses: 18 },
        { id: 3, fullname: 'Bob Carter', username: 'bobc', email: 'bob@mail.com', is_admin: 0, is_active: 0, last_login: '2026-09-01 12:00:00', analyses: 7 },
        { id: 4, fullname: 'Eve Davis', username: 'eve_d', email: 'eve@mail.com', is_admin: 0, is_active: 1, last_login: '2026-09-17 22:05:00', analyses: 11 }
      ]);
      return;
    }
    PSA.api('admin.php', 'POST', { action: 'users', admin_id: PSA.session.user.id }).then(res => {
      this.renderUsers(res.success ? res.data : []);
    }).catch(() => this.renderUsers([]));
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

  loadActivity(demo) {
    const feed = document.getElementById('admin-feed');
    if (!feed) return;
    var lines;
    if (demo) {
      lines = [
        { time: '08:40:12', type: 'info', text: 'admin logged in from 192.168.1.24' },
        { time: '08:39:55', type: 'success', text: 'user alice_j analyzed 3 passwords' },
        { time: '08:31:02', type: 'warn', text: 'login failed x3 for user bobc (lock check)' },
        { time: '08:12:48', type: 'danger', text: 'common password flagged :: "password123"' },
        { time: '07:58:20', type: 'success', text: 'report generated by eve_d (PDF)' },
        { time: '07:44:09', type: 'info', text: 'SYSTEM :: weekly security scan queued' }
      ];
      this.renderFeed(lines);
      return;
    }
    PSA.api('admin.php', 'POST', { action: 'activity', admin_id: PSA.session.user.id }).then(res => {
      this.renderFeed(res.success ? res.data : []);
    }).catch(() => this.renderFeed([]));
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
    if (!PSA.session.user.is_admin) {
      PSA.toast('Access denied - admin only', 'error');
      setTimeout(() => (window.location.href = 'dashboard.html'), 900);
      return;
    }
    document.getElementById('admin-name').textContent = PSA.session.user.username.toUpperCase();
    this.loadOverview();
  }
};

document.addEventListener('DOMContentLoaded', function () { PSA_Admin.bind(); });