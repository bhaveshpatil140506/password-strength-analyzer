<?php
/**
 * PASSWORD STRENGTH ANALYZER - LOGIN API
 * POST methods: login.php
 *
 * - 5 failed attempts / 15 min => temporary lockout (brute-force protection)
 * - records login_attempts audit
 */

require_once __DIR__ . '/../config/database.php';

$input  = jsonBody();
$uname  = trim($input['username'] ?? '');
$pass   = $input['password'] ?? '';

if ($uname === '' || $pass === '') {
    respond(false, 'Username and password are required.');
}

$lockoutWindow = time() - 900; // 15 minutes
$failed = db()->prepare(
    'SELECT COUNT(*) FROM login_attempts
     WHERE username = ? AND success = 0 AND attempted_at > FROM_UNIXTIME(?)'
);
$failed->execute([$uname, $lockoutWindow]);

if ($failed->fetchColumn() >= 5) {
    respond(false, 'ACCOUNT_LOCKED :: too many failures, retry in 15 minutes.');
}

$st = db()->prepare('SELECT * FROM users WHERE username = ? OR email = ? LIMIT 1');
$st->execute([$uname, $uname]);
$user = $st->fetch();

$loginOk = $user && password_verify($pass, $user['password_hash']) && (int) $user['is_active'] === 1;

// ---------- AUDIT ----------
db()->prepare(
    'INSERT INTO login_attempts (user_id, username, ip_address, user_agent, success) VALUES (?, ?, ?, ?, ?)'
)->execute([
    $user ? (int) $user['id'] : null,
    $uname,
    clientIp(),
    substr($_SERVER['HTTP_USER_AGENT'] ?? '', 0, 250),
    $loginOk ? 1 : 0,
]);

if (!$loginOk) {
    respond(false, $user && (int) $user['is_active'] === 0
        ? 'ACCOUNT_BANNED :: contact administrator.'
        : 'INVALID_CREDENTIALS :: username or password is incorrect.');
}

// ---------- SUCCESS ----------
db()->prepare('UPDATE users SET last_login = NOW() WHERE id = ?')->execute([$user['id']]);

$session = [
    'user' => [
        'id'         => (int) $user['id'],
        'fullname'   => $user['fullname'],
        'username'   => $user['username'],
        'email'      => $user['email'],
    ],
    'is_admin'   => (bool) $user['is_admin'],
    'logged_in'  => true,
    'token'      => bin2hex(random_bytes(24)),
    'expires_at' => date('Y-m-d H:i:s', time() + 3600 * 4),
];

db()->prepare('INSERT INTO admin_activity_log (admin_id, action, details) VALUES (?, ?, ?)')
    ->execute([null, 'USER_LOGIN', "{$user['username']} logged in from " . clientIp()]);

respond(true, 'AUTHENTICATION_SUCCESS', ['session' => $session]);