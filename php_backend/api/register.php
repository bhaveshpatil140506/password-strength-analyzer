<?php
/**
 * PASSWORD STRENGTH ANALYZER - USER REGISTRATION API
 * POST methods: register.php
 */

require_once __DIR__ . '/../config/database.php';

$input = jsonBody();

$fullName  = is_string($input['fullname'] ?? null) ? trim($input['fullname']) : '';
$username  = is_string($input['username'] ?? null) ? trim($input['username']) : '';
$email     = is_string($input['email'] ?? null) ? trim($input['email']) : '';
$password  = is_string($input['password'] ?? null) ? $input['password'] : '';
$secQ      = is_string($input['security_question'] ?? null) ? trim($input['security_question']) : '';
$secA      = is_string($input['security_answer'] ?? null) ? trim($input['security_answer']) : '';

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
if ($pwLen === 0) {
    $errors['password'] = 'Password is required.';
} elseif ($pwLen > 8) {
    $errors['password'] = 'Use no more than 8 characters.';
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
$hash = appPasswordHash($password);
$answerHash = $secA !== '' ? appPasswordHash($secA) : null;

try {
    $st = db()->prepare(
        'INSERT INTO users (fullname, username, email, password_hash, security_question, security_answer_hash,
                            is_admin, is_active, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, 0, 1, UTC_TIMESTAMP(), UTC_TIMESTAMP())'
    );
    $st->execute([$fullName, $username, $email, $hash, $secQ, $answerHash]);

    $userId = (int) db()->lastInsertId();

    db()->prepare('INSERT INTO admin_activity_log (admin_id, action, details, created_at) VALUES (?, ?, ?, UTC_TIMESTAMP())')
        ->execute([null, 'USER_REGISTERED', "New user #{$userId} ({$username})"]);

    respond(true, 'ACCOUNT_CREATED', ['user_id' => $userId]);
} catch (PDOException $e) {
    if ($e->getCode() === '23000') {
        respond(false, 'Username or email already exists.');
    }
    respond(false, 'REGISTRATION_FAILED :: ' . (APP_DEBUG ? $e->getMessage() : 'server error'));
}
