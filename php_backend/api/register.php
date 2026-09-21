<?php
/**
 * PASSWORD STRENGTH ANALYZER - USER REGISTRATION API
 * POST methods: register.php
 */

require_once __DIR__ . '/../config/database.php';

$input = jsonBody();

$fullName  = trim($input['fullname'] ?? '');
$username  = trim($input['username'] ?? '');
$email     = trim($input['email'] ?? '');
$password  = $input['password'] ?? '';
$secQ      = trim($input['security_question'] ?? '');
$secA      = trim($input['security_answer'] ?? '');

$errors = [];

// ---------- VALIDATIONS ----------
if ($fullName === '' || mb_strlen($fullName) < 3 || mb_strlen($fullName) > 80) {
    $errors['fullname'] = 'Full name must be 3-80 characters.';
} elseif (!preg_match("/^[a-zA-Z\s.'-]+$/", $fullName)) {
    $errors['fullname'] = 'Full name contains invalid characters.';
}

if ($username === '' || mb_strlen($username) < 4 || mb_strlen($username) > 30) {
    $errors['username'] = 'Username must be 4-30 characters.';
} elseif (!preg_match('/^[a-zA-Z0-9_]+$/', $username)) {
    $errors['username'] = 'Username: letters, numbers, underscores only.';
}

if (!filter_var($email, FILTER_VALIDATE_EMAIL)) {
    $errors['email'] = 'A valid email address is required.';
}

$pwLen = mb_strlen($password);
if ($pwLen < 8) {
    $errors['password'] = 'Password must be at least 8 characters.';
} else {
    $complex = 0;
    if (preg_match('/[a-z]/', $password)) $complex++;
    if (preg_match('/[A-Z]/', $password)) $complex++;
    if (preg_match('/[0-9]/', $password)) $complex++;
    if (preg_match('/[^A-Za-z0-9]/', $password)) $complex++;
    if ($complex < 3) {
        $errors['password'] = 'Password needs 3+ of: lower, upper, numbers, symbols.';
    }
    if (preg_match('/(.)\1{2,}/', $password)) {
        $errors['password'] = 'Password must not contain triple repeats.';
    }
    if (preg_match('/(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|012|123|234|345|456|567|678|789)/i', $password)) {
        $errors['password'] = 'Password must not contain sequential patterns.';
    }
}

if ($secQ !== '' && $secA === '') {
    $errors['security_answer'] = 'Security answer is required when a question is set.';
}

$common = require __DIR__ . '/../config/common_list.php';
if (in_array(strtolower($password), array_map('strtolower', $common), true)) {
    $errors['password'] = 'This is a widely-used common password. Choose something unique.';
}

// ---------- DUPLICATE CHECKS ----------
if (!$errors) {
    $st = db()->prepare('SELECT id FROM users WHERE username = ? OR email = ?');
    $st->execute([$username, $email]);
    if ($st->fetch()) {
        $errors['username'] = 'Username or email is already registered.';
    }
}

if ($errors) {
    respond(false, 'VALIDATION_FAILED', ['errors' => $errors]);
}

// ---------- CREATE USER ----------
$hash = password_hash($password, PASSWORD_DEFAULT);
$answerHash = $secA !== '' ? password_hash($secA, PASSWORD_DEFAULT) : null;

try {
    $st = db()->prepare(
        'INSERT INTO users (fullname, username, email, password_hash, security_question, security_answer_hash)
         VALUES (?, ?, ?, ?, ?, ?)'
    );
    $st->execute([$fullName, $username, $email, $hash, $secQ, $answerHash]);

    $userId = (int) db()->lastInsertId();

    db()->prepare('INSERT INTO admin_activity_log (admin_id, action, details) VALUES (?, ?, ?)')
        ->execute([null, 'USER_REGISTERED', "New user #{$userId} ({$username})"]);

    respond(true, 'ACCOUNT_CREATED', ['user_id' => $userId]);
} catch (PDOException $e) {
    if ($e->getCode() === '23000') {
        respond(false, 'Username or email already exists.');
    }
    respond(false, 'REGISTRATION_FAILED :: ' . (APP_DEBUG ? $e->getMessage() : 'server error'));
}