<?php
/**
 * PASSWORD STRENGTH ANALYZER - INSTALLER
 *
 * 1. Creates the database schema (database/schema.sql)
 * 2. Creates the admin account with a generated or environment-provided password
 *
 * Usage:  http://localhost/Password-Strength-Analyzer/php_backend/install.php
 * Afterwards DELETE or rename this file for security.
 */

header('Content-Type: text/plain; charset=utf-8');

define('PSA_BYPASS_HEADERS', true);
require_once __DIR__ . '/config/database.php';

echo "== PASSWORD STRENGTH ANALYZER INSTALLER ==\n\n";

// ---------- 1) SCHEMA ----------
$schemaFile = realpath(__DIR__ . '/../database/schema.sql');
if (!$schemaFile || !is_readable($schemaFile)) {
    echo "ERROR :: schema.sql not found at database/schema.sql\n";
    exit(1);
}

$sql = file_get_contents($schemaFile);

try {
    $pdo = db();
    $pdo->exec($sql);
    echo "[OK] Schema executed successfully.\n";
} catch (PDOException $e) {
    // Some statements may already exist; verify tables instead
    echo "[WARN] Schema import produced an error (likely already imported).\n";
    if (APP_DEBUG) {
        echo "      " . $e->getMessage() . "\n";
    }
}

// ---------- 2) DEFAULT ADMIN ----------
$uname = 'admin';
$email = 'admin@psa.local';
$configuredPassword = getenv('PSA_ADMIN_PASSWORD');
$pass  = $configuredPassword ?: bin2hex(random_bytes(4));
if (mb_strlen($pass) > 8) {
    exit("[ERROR] PSA_ADMIN_PASSWORD must be no more than 8 characters.\n");
}
$hash  = appPasswordHash($pass);

$st = db()->prepare('SELECT id FROM users WHERE username = ?');
$st->execute([$uname]);

if ($st->fetch()) {
    if ($configuredPassword !== false && $configuredPassword !== '') {
        db()->prepare('UPDATE users SET password_hash = ? WHERE username = ?')
            ->execute([appPasswordHash($pass), $uname]);
        echo "[OK] Admin password reset. Username: admin. Initial password: {$pass}\n";
    } else {
        echo "[INFO] Admin account 'admin' already exists - skipping. Set PSA_ADMIN_PASSWORD to reset it.\n";
    }
} else {
    db()->prepare(
        'INSERT INTO users (fullname, username, email, password_hash, is_admin, is_active, created_at, updated_at)
         VALUES (?, ?, ?, ?, 1, 1, UTC_TIMESTAMP(), UTC_TIMESTAMP())'
    )->execute(['System Administrator', $uname, $email, $hash]);
    echo "[OK] Admin account created for username 'admin'. Initial password: {$pass}\n";
}

// ---------- 3) VERIFY TABLES ----------
echo "\n== VERIFICATION ==\n";
$tables = ['users', 'api_sessions', 'analyzed_passwords', 'common_passwords', 'recommendations', 'reports', 'login_attempts', 'admin_activity_log'];
foreach ($tables as $t) {
    $r = db()->query("SHOW TABLES LIKE '{$t}'")->rowCount();
    echo "  " . ($r ? '[OK]' : '[MISSING!]') . " table: {$t}\n";
}

echo "\n== INSTALLATION COMPLETE ==\n";
echo "Delete this file (install.php) before going live.\n";
