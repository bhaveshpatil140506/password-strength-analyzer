<?php
/**
 * PASSWORD STRENGTH ANALYZER - INSTALLER
 *
 * 1. Creates the database schema (database/schema.sql)
 * 2. Creates the default admin account  admin / Admin@123
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
$pass  = 'Admin@123';
$hash  = password_hash($pass, PASSWORD_DEFAULT);

$st = db()->prepare('SELECT id FROM users WHERE username = ?');
$st->execute([$uname]);

if ($st->fetch()) {
    echo "[INFO] Admin account 'admin' already exists - skipping.\n";
} else {
    db()->prepare(
        'INSERT INTO users (fullname, username, email, password_hash, is_admin, is_active)
         VALUES (?, ?, ?, ?, 1, 1)'
    )->execute(['System Administrator', $uname, $email, $hash]);
    echo "[OK] Admin account created: admin / Admin@123\n";
}

// ---------- 3) VERIFY TABLES ----------
echo "\n== VERIFICATION ==\n";
$tables = ['users', 'analyzed_passwords', 'common_passwords', 'recommendations', 'reports', 'login_attempts', 'admin_activity_log'];
foreach ($tables as $t) {
    $r = db()->query("SHOW TABLES LIKE '{$t}'")->rowCount();
    echo "  " . ($r ? '[OK]' : '[MISSING!]') . " table: {$t}\n";
}

echo "\n== INSTALLATION COMPLETE ==\n";
echo "Delete this file (install.php) before going live.\n";