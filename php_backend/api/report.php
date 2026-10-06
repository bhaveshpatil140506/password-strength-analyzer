<?php
/**
 * PASSWORD STRENGTH ANALYZER - REPORT GENERATION API
 * POST:  report.php              => generate + persist report
 * POST?: report.php?action=full  => compile full report from history
 */

require_once __DIR__ . '/../config/database.php';

$input  = jsonBody();
$action = $input['action'] ?? $_GET['action'] ?? 'generate';
$userId = (int) ($input['user_id'] ?? 0);
$authenticatedId = authenticatedUserId();

if ($userId <= 0 || $userId !== $authenticatedId) {
    http_response_code($userId <= 0 ? 400 : 403);
    if ($userId > 0) respond(false, 'FORBIDDEN');
    respond(false, 'USER_ID_REQUIRED');
}

$db = db();

function compileReport(int $userId): array
{
    $db = db();

    $rows = $db->prepare('SELECT * FROM analyzed_passwords WHERE user_id = ? ORDER BY analyzed_at DESC');
    $rows->execute([$userId]);
    $analyses = $rows->fetchAll();

    $total    = count($analyses);
    $scoreSum = 0;
    $buckets  = ['weak' => 0, 'medium' => 0, 'strong' => 0, 'excellent' => 0];
    $common   = 0;
    $breaches = 0;

    foreach ($analyses as $a) {
        $scoreSum += (int) $a['strength_score'];
        $label = strtoupper((string) $a['strength_label']);
        if (in_array($label, ['WEAK', 'FAIR'], true)) $buckets['weak']++;
        elseif ($label === 'STRONG') $buckets['strong']++;
        else $buckets['excellent']++;
        if ((int) $a['is_common'] === 1) $common++;
        if ((int) $a['breached_count'] > 0) $breaches += (int) $a['breached_count'];
    }

    $avg = $total ? round($scoreSum / $total, 2) : 0;

    $recommendations = [];
    if ($common > 0) {
        $recommendations[] = ['severity' => 'critical', 'title' => 'CRITICAL: Common passwords in use',
            'desc' => "{$common} analyzed values are on global breach lists. Change these immediately and never reuse them."];
    }
    if ($buckets['weak'] > 0) {
        $recommendations[] = ['severity' => 'high', 'title' => 'Improve password strength',
            'desc' => "{$buckets['weak']} entries score weakly. Choose longer, unique passphrases or manager-generated passwords."];
    }
    if ($breaches > 0) {
        $recommendations[] = ['severity' => 'high', 'title' => 'Stop using leaked passwords',
            'desc' => "Your history contains passwords found in {$breaches} real-world breaches. Change those passwords now."];
    }
    if ($avg >= 5) {
        $recommendations[] = ['severity' => 'low', 'title' => 'Maintain current hygiene',
            'desc' => 'Average strength is solid. Keep using unique passwords and change any password that is exposed or compromised.'];
    } else {
        $recommendations[] = ['severity' => 'medium', 'title' => 'Raise your average score',
            'desc' => "Your average is {$avg}/8. A passphrase strategy will lift this substantially."];
    }

    return [
        'user_id'              => $userId,
        'total_analyses'       => $total,
        'avg_strength'         => $avg,
        'weak_passwords'       => $buckets['weak'],
        'medium_passwords'     => 0,
        'strong_passwords'     => $buckets['strong'] + $buckets['excellent'],
        'excellent_passwords'  => $buckets['excellent'],
        'common_detected'      => $common,
        'breach_hits'          => $breaches,
        'analyses'             => $analyses,
        'recommendations'      => $recommendations,
    ];
}

switch ($action) {

    case 'full':
        respond(true, 'OK', ['data' => compileReport($userId)]);
        break;

    default:
        // single-analysis result saved as a report snapshot
        $resultData = $input['result_data'] ?? null;
        if (!is_array($resultData)) {
            respond(false, 'RESULT_DATA_REQUIRED');
        }

        // Save the analysis to history automatically if it isn't duplicate
        $savedId = null;
        $pwMask = (string) ($resultData['placeholder'] ?? 'NA');
        $check = $db->prepare('SELECT id FROM analyzed_passwords WHERE user_id = ? AND password_placeholder = ? ORDER BY analyzed_at DESC LIMIT 1');
        $check->execute([$userId, $pwMask]);
        if (!$check->fetch()) {
            $db->prepare(
                'INSERT INTO analyzed_passwords
                 (user_id, password_placeholder, strength_score, strength_label, length,
                  has_uppercase, has_lowercase, has_numbers, has_special, character_count,
                  link_speed, estimated_crack_time, is_common, breached_count, entropy, analysis_notes, analyzed_at)
                 VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,UTC_TIMESTAMP())'
            )->execute([
                $userId,
                $pwMask,
                (int) ($resultData['score'] ?? 0),
                (string) ($resultData['label'] ?? 'NONE'),
                (int) ($resultData['length'] ?? 0),
                (int) ($resultData['has_uppercase'] ?? 0),
                (int) ($resultData['has_lowercase'] ?? 0),
                (int) ($resultData['has_numbers'] ?? 0),
                (int) ($resultData['has_special'] ?? 0),
                (float) ($resultData['entropy'] ?? 0),
                (string) ($resultData['linkLabel'] ?? '-'),
                (string) ($resultData['crackTime'] ?? '-'),
                (int) ($resultData['isCommon'] ?? 0),
                (int) ($resultData['breached'] ?? 0),
                (float) ($resultData['entropy'] ?? 0),
                isset($resultData['recommendations']) ? implode('; ', array_column($resultData['recommendations'], 'title')) : '',
            ]);
            $savedId = (int) $db->lastInsertId();
        }

        $report = compileReport($userId);
        $db->prepare(
            'INSERT INTO reports (user_id, report_type, report_format, total_analyses, avg_strength, weak_passwords, medium_passwords, strong_passwords, common_detected, recommendations_count, report_data, generated_at)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,UTC_TIMESTAMP())'
        )->execute([
            $userId,
            'single',
            'json',
            $report['total_analyses'],
            $report['avg_strength'],
            $report['weak_passwords'],
            $report['medium_passwords'],
            $report['strong_passwords'],
            $report['common_detected'],
            count($report['recommendations']),
            json_encode($report),
        ]);

        respond(true, 'REPORT_GENERATED', ['report_id' => (int) $db->lastInsertId(), 'saved_analysis_id' => $savedId]);
}
