<?php
/**
 * PASSWORD STRENGTH ANALYZER - PHP BACKEND INDEX / ROUTER
 * Public endpoint list for the API.
 */

require_once __DIR__ . '/config/database.php';

$endpoints = [
    'POST api/register.php'           => 'Create a new user account (validations + bcrypt)',
    'POST api/login.php'              => 'Authenticate (attempt lockout + audit trail)',
    'POST api/history.php'            => 'Save / list analysis history',
    'POST api/history.php?action=detail' => 'Fetch one history record',
    'POST api/history.php?action=delete' => 'Delete a history record',
    'POST api/report.php'             => 'Generate & persist a security report',
    'POST api/report.php?action=full' => 'Compile full report from history',
    'POST api/admin.php?action=overview'      => 'Platform-wide admin stats',
    'POST api/admin.php?action=users'         => 'List users (admin)',
    'POST api/admin.php?action=toggle_ban'    => 'Ban / unban user (admin)',
    'POST api/admin.php?action=delete_user'   => 'Delete user (admin)',
    'POST api/admin.php?action=activity'      => 'Audit log feed (admin)',
    'POST api/common_passwords.php'   => 'Common password detection',
];

respond(true, APP_NAME . ' :: API READY', [
    'version'   => '1.0.0',
    'database'  => DB_NAME,
    'endpoints' => $endpoints,
]);