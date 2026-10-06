<?php
require_once __DIR__ . '/../config/database.php';

// Authentication validates token format, expiry, user status, and database hash.
authenticatedUserId();
$headers = function_exists('getallheaders') ? getallheaders() : [];
$authorization = $headers['Authorization'] ?? $headers['authorization'] ?? ($_SERVER['HTTP_AUTHORIZATION'] ?? '');
preg_match('/^Bearer\s+([a-f0-9]{64})$/i', trim($authorization), $match);
db()->prepare('DELETE FROM api_sessions WHERE token_hash = ?')
    ->execute([hash('sha256', strtolower($match[1]))]);
respond(true, 'SIGNED_OUT');
