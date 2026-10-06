<?php
/**
 * PASSWORD STRENGTH ANALYZER - ADMIN DASHBOARD API
 * Actions:
 *   admin.php?action=overview      => platform stats + weekly activity
 *   admin.php?action=users         => list users with analysis counts
 *   admin.php?action=toggle_ban    => ban / unban user
 *   admin.php?action=delete_user   => delete user (cascade)
 *   admin.php?action=activity      => latest audit log entries
 *   admin.php?action=user_stats    => per-user stats (dashboard)
 *
 * Every action requires admin token check (is_admin).
 */

require_once __DIR__ . '/../config/database.php';

$input  = jsonBody();
$action = $input['action'] ?? $_GET['action'] ?? 'overview';
$authenticatedId = authenticatedUserId();
$adminId = $authenticatedId;

$db = db();

// ---------- ADMIN ONLY (except user_stats, which serves the user dashboard) ----------
if ($action === 'user_stats') {
    if ((int) ($input['user_id'] ?? 0) !== $authenticatedId) {
        http_response_code(403);
        respond(false, 'FORBIDDEN');
    }
} elseif (!isAdmin($adminId)) {
    http_response_code(403);
    respond(false, 'FORBIDDEN :: admin privileges required.');
}

switch ($action) {

    case 'user_stats':
        $uid = (int) ($input['user_id'] ?? 0);
        if ($uid <= 0) respond(false, 'USER_ID_REQUIRED');

        $rows = $db->prepare('SELECT strength_score, strength_label, is_common, breached_count FROM analyzed_passwords WHERE user_id = ?');
        $rows->execute([$uid]);
        $all = $rows->fetchAll();

        $total = count($all);
        $scoreSum = 0; $weak = 0; $strong = 0; $common = 0; $breaches = 0;
        foreach ($all as $a) {
            $scoreSum += (int) $a['strength_score'];
            $label = strtoupper((string) $a['strength_label']);
            if (in_array($label, ['WEAK', 'FAIR'], true)) $weak++;
            if (in_array($label, ['STRONG', 'EXCELLENT'], true)) $strong++;
            if ((int) $a['is_common'] === 1) $common++;
            $breaches += (int) $a['breached_count'];
        }

        respond(true, 'OK', ['data' => [
            'total_analyses' => $total,
            'avg_strength'   => $total ? round($scoreSum / $total, 2) : 0,
            'weak'           => $weak,
            'medium'         => 0,
            'strong'         => $strong,
            'excellent'      => 0,
            'common'         => $common,
            'breaches'       => $breaches,
        ]]);
        break;

    case 'overview':
        $totalUsers    = (int) $db->query('SELECT COUNT(*) FROM users')->fetchColumn();
        $totalPw       = (int) $db->query('SELECT COUNT(*) FROM analyzed_passwords')->fetchColumn();
        $commonPw      = (int) $db->query('SELECT COUNT(*) FROM analyzed_passwords WHERE is_common = 1')->fetchColumn();
        $totalBreaches = (int) $db->query('SELECT COALESCE(SUM(breached_count),0) FROM analyzed_passwords')->fetchColumn();
        $totalReports  = (int) $db->query('SELECT COUNT(*) FROM reports')->fetchColumn();
        $activeToday   = (int) $db->query('SELECT COUNT(*) FROM users WHERE DATEDIFF(NOW(), last_login) = 0')->fetchColumn();
        $recentLogins  = (int) $db->query('SELECT COUNT(*) FROM login_attempts WHERE success = 1 AND DATEDIFF(NOW(), attempted_at) = 0')->fetchColumn();

        $week = [];
        $weekSql = $db->prepare('SELECT COUNT(*) FROM analyzed_passwords WHERE DATE(analyzed_at) = DATE_SUB(CURDATE(), INTERVAL ? DAY)');
        for ($i = 6; $i >= 0; $i--) {
            $weekSql->execute([$i]);
            $week[] = (int) $weekSql->fetchColumn();
        }

        respond(true, 'OK', ['data' => [
            'total_users'      => $totalUsers,
            'total_passwords'  => $totalPw,
            'common_passwords' => $commonPw,
            'total_breaches'   => $totalBreaches,
            'total_reports'    => $totalReports,
            'active_today'     => $activeToday,
            'recent_logins'    => $recentLogins,
            'week_daily'       => $week,
        ]]);
        break;

    case 'users':
        $rows = $db->query(
            'SELECT u.id, u.fullname, u.username, u.email, u.is_admin, u.is_active, u.last_login,
                    (SELECT COUNT(*) FROM analyzed_passwords p WHERE p.user_id = u.id) AS analyses
             FROM users u ORDER BY u.id ASC'
        )->fetchAll();
        respond(true, 'OK', ['data' => $rows]);
        break;

    case 'toggle_ban':
        $target = (int) ($input['target_id'] ?? 0);
        $state  = (int) ($input['state'] ?? 0) === 1 ? 1 : 0;
        if ($target <= 0) respond(false, 'TARGET_ID_REQUIRED');

        $chk = $db->prepare('SELECT is_admin FROM users WHERE id = ?');
        $chk->execute([$target]);
        if ((int) ($chk->fetchColumn() ?: 0) === 1) {
            respond(false, 'CANNOT_MODIFY_ADMIN_ACCOUNT');
        }

        $db->prepare('UPDATE users SET is_active = ? WHERE id = ?')->execute([$state, $target]);
        $db->prepare('INSERT INTO admin_activity_log (admin_id, action, target_user_id, details, created_at) VALUES (?,?,?,?,UTC_TIMESTAMP())')
            ->execute([$adminId, $state ? 'USER_UNBANNED' : 'USER_BANNED', $target, "admin #{$adminId} toggled user #{$target}"]);
        respond(true, $state ? 'USER_UNBANNED' : 'USER_BANNED');
        break;

    case 'delete_user':
        $target = (int) ($input['target_id'] ?? 0);
        if ($target <= 0) respond(false, 'TARGET_ID_REQUIRED');

        $chk = $db->prepare('SELECT is_admin FROM users WHERE id = ?');
        $chk->execute([$target]);
        if ((int) ($chk->fetchColumn() ?: 0) === 1) {
            respond(false, 'CANNOT_DELETE_ADMIN_ACCOUNT');
        }

        $db->prepare('DELETE FROM users WHERE id = ?')->execute([$target]);
        $db->prepare('INSERT INTO admin_activity_log (admin_id, action, target_user_id, details, created_at) VALUES (?,?,?,?,UTC_TIMESTAMP())')
            ->execute([$adminId, 'USER_DELETED', $target, "admin #{$adminId} deleted user #{$target}"]);
        respond(true, 'USER_DELETED');
        break;

    case 'activity':
        $rows = $db->query('SELECT * FROM admin_activity_log ORDER BY created_at DESC LIMIT 30')->fetchAll();
        $fn = static function (array $r) {
            $actionUpper = strtoupper((string) $r['action']);
            if (in_array($actionUpper, ['USER_BANNED', 'USER_DELETED', 'LOGIN_FAILED'], true)) {
                $type = 'danger';
            } elseif (in_array($actionUpper, ['USER_REGISTERED', 'REPORT_GENERATED', 'USER_LOGIN'], true)) {
                $type = 'success';
            } elseif (strpos($actionUpper, 'FAILED') !== false) {
                $type = 'warn';
            } else {
                $type = 'info';
            }
            return [
                'time' => date('H:i:s', strtotime($r['created_at'])),
                'type' => $type,
                'text' => $r['action'] . ' :: ' . ($r['details'] ?? ''),
            ];
        };
        respond(true, 'OK', ['data' => array_map($fn, $rows)]);
        break;

    default:
        respond(false, 'UNKNOWN_ACTION');
}
