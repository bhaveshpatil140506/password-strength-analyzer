<?php
/**
 * PASSWORD STRENGTH ANALYZER - DATABASE CONFIGURATION
 * PDO / MySQL (phpMyAdmin)
 */

declare(strict_types=1);
mb_internal_encoding('UTF-8');
date_default_timezone_set('UTC');

define('DB_HOST', getenv('PSA_DB_HOST') ?: '127.0.0.1');
define('DB_NAME', getenv('PSA_DB_NAME') ?: 'password_analyzer');
define('DB_USER', getenv('PSA_DB_USER') ?: 'root');
define('DB_PASS', getenv('PSA_DB_PASSWORD') ?: '');

define('APP_NAME', 'PASSWORD_STRENGTH_ANALYZER');
define('APP_DEBUG', getenv('PSA_DEBUG') === '1');

/** Global PDO singleton */
function db(): PDO
{
    static $pdo = null;
    if ($pdo instanceof PDO) {
        return $pdo;
    }
    $dsn = 'mysql:host=' . DB_HOST . ';dbname=' . DB_NAME . ';charset=utf8mb4';
    try {
        $pdo = new PDO($dsn, DB_USER, DB_PASS, [
            PDO::ATTR_ERRMODE            => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_EMULATE_PREPARES   => false,
        ]);
        return $pdo;
    } catch (PDOException $e) {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode([
            'success' => false,
            'message' => 'DATABASE_CONNECTION_FAILED :: ' . (APP_DEBUG ? $e->getMessage() : 'Cannot reach the database.'),
        ]);
        exit;
    }
}

/** CORS + JSON headers for every API call */
function apiHeaders(): void
{
    if (defined('PSA_BYPASS_HEADERS') && PSA_BYPASS_HEADERS) {
        return;
    }
    header('Access-Control-Allow-Origin: *');
    header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, Authorization');
    header('Content-Type: application/json; charset=utf-8');
    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        http_response_code(204);
        exit;
    }
}

/** Read JSON body into associative array */
function jsonBody(): array
{
    $raw = file_get_contents('php://input');
    $data = json_decode($raw, true);
    return is_array($data) ? $data : [];
}

/** Uniform API response */
function respond(bool $ok, string $msg = '', array $extra = []): void
{
    echo json_encode(array_merge(['success' => $ok, 'message' => $msg], $extra));
    exit;
}

/** Safe client IP */
function clientIp(): string
{
    return $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
}

/** Get admin flag */
function isAdmin(int $uid): bool
{
    $st = db()->prepare('SELECT is_admin FROM users WHERE id = ?');
    $st->execute([$uid]);
    return (bool) ($st->fetchColumn() ?: 0);
}

/** Hash the SHA-256 pre-digest with bcrypt to avoid bcrypt's 72-byte input cap. */
function appPasswordHash(string $password): string
{
    $material = base64_encode(hash('sha256', $password, true));
    return password_hash($material, PASSWORD_BCRYPT);
}

/** Accept current pre-digested hashes and existing direct bcrypt hashes. */
function appPasswordVerify(string $password, string $encoded): bool
{
    $material = base64_encode(hash('sha256', $password, true));
    return password_verify($material, $encoded) || password_verify($password, $encoded);
}

/** Resolve a bearer token to an active database user. */
function authenticatedUserId(): int
{
    $headers = function_exists('getallheaders') ? getallheaders() : [];
    $authorization = $headers['Authorization'] ?? $headers['authorization'] ?? ($_SERVER['HTTP_AUTHORIZATION'] ?? '');
    if (!preg_match('/^Bearer\s+([a-f0-9]{64})$/i', trim($authorization), $match)) {
        http_response_code(401);
        respond(false, 'AUTHENTICATION_REQUIRED');
    }

    $st = db()->prepare(
        'SELECT s.user_id FROM api_sessions s JOIN users u ON u.id = s.user_id
         WHERE s.token_hash = ? AND s.expires_at > UTC_TIMESTAMP() AND u.is_active = 1 LIMIT 1'
    );
    $st->execute([hash('sha256', strtolower($match[1]))]);
    $uid = (int) ($st->fetchColumn() ?: 0);
    if (!$uid) {
        http_response_code(401);
        respond(false, 'SESSION_EXPIRED_OR_INVALID');
    }
    return $uid;
}

/** Boot API */
apiHeaders();
