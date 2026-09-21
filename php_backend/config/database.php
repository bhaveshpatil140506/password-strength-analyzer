<?php
/**
 * PASSWORD STRENGTH ANALYZER - DATABASE CONFIGURATION
 * PDO / MySQL (phpMyAdmin)
 */

declare(strict_types=1);
mb_internal_encoding('UTF-8');
date_default_timezone_set('UTC');

const DB_HOST = '127.0.0.1';
const DB_NAME = 'password_analyzer';
const DB_USER = 'root';
const DB_PASS = '';

const APP_NAME  = 'PASSWORD_STRENGTH_ANALYZER';
const APP_DEBUG = true;   // false in production

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
    header('Access-Control-Allow-Headers: Content-Type');
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

/** Boot API */
apiHeaders();