<?php
/**
 * PASSWORD STRENGTH ANALYZER - COMMON PASSWORD DETECTION API
 * POST: common_passwords.php  { password => string }
 * Returns: check result against local list + breach count (HIBP style check is client-side)
 */

require_once __DIR__ . '/../config/database.php';

$input = jsonBody();
$password = (string) ($input['password'] ?? '');

if ($password === '') {
    respond(false, 'PASSWORD_REQUIRED');
}

$commonList = require __DIR__ . '/../config/common_list.php';

$common = in_array(strtolower($password), array_map('strtolower', $commonList), true);
$rank = 0;
if ($common) {
    $rank = array_search(strtolower($password), array_map('strtolower', $commonList), true) + 1;
}

// Cross-check the common_passwords table (authoritative, blinded via SHA-256)
$hash = hash('sha256', $password);
$db = db();
$st = $db->prepare('SELECT appearance_rank FROM common_passwords WHERE password_hash = ?');
$st->execute([$hash]);
$dbRank = $st->fetchColumn();

respond(true, 'OK', [
    'is_common' => (bool) ($common || $dbRank),
    'rank'      => $dbRank ? (int) $dbRank : $rank,
    'standard'  => $common,
    'database'  => (bool) $dbRank,
]);