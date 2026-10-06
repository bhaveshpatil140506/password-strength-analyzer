<?php
/**
 * PASSWORD STRENGTH ANALYZER - PASSWORD HISTORY API
 * POST:  history.php                 => list / save
 * POST?: history.php?action=detail  => single record
 * POST?: history.php?action=delete  => delete record
 */

require_once __DIR__ . '/../config/database.php';

$input  = jsonBody();
$action = $input['action'] ?? $_GET['action'] ?? 'list';
$userId = (int) ($input['user_id'] ?? 0);
$authenticatedId = authenticatedUserId();

if ($userId <= 0 || $userId !== $authenticatedId) {
    http_response_code($userId <= 0 ? 400 : 403);
    if ($userId > 0) respond(false, 'FORBIDDEN');
    respond(false, 'USER_ID_REQUIRED');
}

$db = db();

switch ($action) {

    case 'detail':
        $id = (int) ($input['id'] ?? 0);
        $st = $db->prepare('SELECT * FROM analyzed_passwords WHERE id = ? AND user_id = ?');
        $st->execute([$id, $userId]);
        $row = $st->fetch();
        respond($row ? true : false, $row ? '' : 'RECORD_NOT_FOUND', ['data' => $row]);
        break;

    case 'delete':
        $id = (int) ($input['id'] ?? 0);
        $db->prepare('DELETE FROM analyzed_passwords WHERE id = ? AND user_id = ?')
            ->execute([$id, $userId]);
        respond(true, 'RECORD_DELETED');
        break;

    case 'save':
    default:
        if ($action === 'list') {
            $limit = (int) ($input['limit'] ?? (isset($_GET['limit']) ? (int) $_GET['limit'] : 0));
            $sql = 'SELECT * FROM analyzed_passwords WHERE user_id = ? ORDER BY analyzed_at DESC';
            if ($limit > 0) $sql .= ' LIMIT ' . $limit;
            $st = $db->prepare($sql);
            $st->execute([$userId]);
            respond(true, 'OK', ['data' => $st->fetchAll()]);
            break;
        }

        // ---------- SAVE ----------
        // The frontend sends analysis fields in a `result` object, matching
        // the Django API. Accept that contract while retaining flat payload
        // compatibility for older callers.
        $result = isset($input['result']) && is_array($input['result'])
            ? $input['result']
            : $input;

        if (empty($result['password_placeholder'])) {
            respond(false, 'RESULT_DATA_REQUIRED');
        }

        $clean = [
            'password_placeholder' => $result['password_placeholder'] ?? $result['placeholder'] ?? null,
            'strength_score' => $result['strength_score'] ?? $result['score'] ?? null,
            'strength_label' => $result['strength_label'] ?? $result['label'] ?? null,
            'length' => $result['length'] ?? null,
            'has_uppercase' => $result['has_uppercase'] ?? 0,
            'has_lowercase' => $result['has_lowercase'] ?? 0,
            'has_numbers' => $result['has_numbers'] ?? 0,
            'has_special' => $result['has_special'] ?? 0,
            'character_count' => $result['character_count'] ?? $result['entropy'] ?? 0,
            'link_speed' => $result['link_speed'] ?? $result['linkLabel'] ?? '',
            'estimated_crack_time' => $result['estimated_crack_time'] ?? $result['crackTime'] ?? '',
            'is_common' => $result['is_common'] ?? $result['isCommon'] ?? 0,
            'breached_count' => $result['breached_count'] ?? $result['breached'] ?? 0,
            'entropy' => $result['entropy'] ?? 0,
            'analysis_notes' => $result['analysis_notes'] ?? '',
        ];

        $db->prepare(
            'INSERT INTO analyzed_passwords
             (user_id, password_placeholder, strength_score, strength_label, length,
              has_uppercase, has_lowercase, has_numbers, has_special, character_count,
              link_speed, estimated_crack_time, is_common, breached_count, entropy, analysis_notes, analyzed_at)
             VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,UTC_TIMESTAMP())'
        )->execute([
            $userId,
            (string) $clean['password_placeholder'],
            (int) $clean['strength_score'],
            (string) $clean['strength_label'],
            (int) $clean['length'],
            (int) $clean['has_uppercase'],
            (int) $clean['has_lowercase'],
            (int) $clean['has_numbers'],
            (int) $clean['has_special'],
            (float) $clean['character_count'],
            (string) $clean['link_speed'],
            (string) $clean['estimated_crack_time'],
            (int) $clean['is_common'],
            (int) $clean['breached_count'],
            (float) $clean['entropy'],
            (string) $clean['analysis_notes'],
        ]);

        $newId = (int) $db->lastInsertId();
        respond(true, 'ANALYSIS_SAVED', ['id' => $newId]);
}
