"""
Password Strength Analyzer - Django views.

Two responsibilities:
 1. Serve the static frontend HTML pages (frontend/*.html)
 2. Expose the REST API (/api/*) mirroring the PHP endpoints.
"""

import json
import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.db.models import Count, Sum
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import (AdminActivityLog, AnalyzedPassword, CommonPassword,
                     LoginAttempt, Report, User)
from . import services

USERNAME_RE = re.compile(r'^[a-zA-Z0-9_]+$')
NAME_RE = re.compile(r"^[a-zA-Z\s.'-]+$")
SEQUENCE_RE = re.compile(
    r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|012|123|234|345|456|567|678|789)',
    re.IGNORECASE,
)


def _body(request):
    try:
        return json.loads(request.body or b'{}')
    except json.JSONDecodeError:
        return {}


def _err(message, code=400):
    return JsonResponse({'success': False, 'message': message}, status=code)


def _ok(message='OK', data=None, **extra):
    payload = {'success': True, 'message': message}
    if data is not None:
        payload['data'] = data
    payload.update(extra)
    return JsonResponse(payload)


# ---------------------------------------------------------------------------
# PAGES (static frontend)
# ---------------------------------------------------------------------------
_FILE_CACHE = {}
_FILE_CACHE_MAX = 48
_TEXT_CT = {
    'css': 'text/css; charset=utf-8',
    'js': 'application/javascript; charset=utf-8',
    'html': 'text/html; charset=utf-8',
}
_IMAGE_CT = {
    'svg': 'image/svg+xml',
    'png': 'image/png',
    'ico': 'image/x-icon',
    'jpg': 'image/jpeg',
    'jpeg': 'image/jpeg',
    'gif': 'image/gif',
    'webp': 'image/webp',
}
_EXT_SPLIT = re.compile(r'\.([a-z0-9]+)$', re.IGNORECASE)


def _cached_file(path: Path) -> bytes:
    """Read a frontend file once, cache by (path, mtime) with a small LRU-ish cap."""
    key = (str(path), path.stat().st_mtime)
    cached = _FILE_CACHE.get(key)
    if cached is not None:
        return cached
    data = path.read_bytes()
    if len(_FILE_CACHE) >= _FILE_CACHE_MAX:
        _FILE_CACHE.clear()
    _FILE_CACHE[key] = data
    return data


def _respond_file(path: Path, kind: str):
    m = _EXT_SPLIT.search(path.name)
    ext = m.group(1) if m else ''
    if kind == 'images':
        ct = _IMAGE_CT.get(ext, 'application/octet-stream')
    else:
        ct = _TEXT_CT.get(ext, _TEXT_CT.get(kind, 'application/octet-stream'))
    resp = HttpResponse(_cached_file(path), content_type=ct)
    resp['Cache-Control'] = 'public, max-age=300'
    return resp


def page_loader(name):
    def view(request):
        path = settings.FRONTEND_DIR / name
        if not path.exists():
            return HttpResponse('PAGE_NOT_FOUND', status=404)
        return _respond_file(path, 'html')
    return view


page_index = page_loader('index.html')
page_login = page_loader('login.html')
page_register = page_loader('register.html')
page_analyzer = page_loader('analyzer.html')
page_dashboard = page_loader('dashboard.html')
page_history = page_loader('history.html')
page_recommendations = page_loader('recommendations.html')
page_report = page_loader('report.html')
page_admin = page_loader('admin_dashboard.html')


@require_http_methods(['GET'])
def page_static(request, kind, filename):
    # Guard against path traversal
    if '..' in filename or '/' in filename:
        return HttpResponse('FORBIDDEN', status=403)
    base = settings.FRONTEND_DIR / kind
    path = base / filename
    if not path.exists():
        return HttpResponse('NOT_FOUND', status=404)
    return _respond_file(path, kind)


# ---------------------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------------------
@csrf_exempt
@require_http_methods(['POST'])
def api_register(request):
    d = _body(request)
    fullname = (d.get('fullname') or '').strip()
    username = (d.get('username') or '').strip()
    email = (d.get('email') or '').strip()
    password = d.get('password') or ''
    sec_q = (d.get('security_question') or '').strip()
    sec_a = (d.get('security_answer') or '').strip()

    errors = {}
    if not (3 <= len(fullname) <= 80) or not NAME_RE.match(fullname):
        errors['fullname'] = 'Full name must be 3-80 valid characters.'
    if not (4 <= len(username) <= 30) or not USERNAME_RE.match(username):
        errors['username'] = 'Username: 4-30 chars, letters/numbers/underscores.'
    if not re.match(r'^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$', email):
        errors['email'] = 'A valid email is required.'
    if len(password) < 8:
        errors['password'] = 'Password must be at least 8 characters.'
    else:
        classes = sum([
            bool(re.search(r'[a-z]', password)),
            bool(re.search(r'[A-Z]', password)),
            bool(re.search(r'[0-9]', password)),
            bool(re.search(r'[^A-Za-z0-9]', password)),
        ])
        if classes < 3:
            errors['password'] = 'Password needs 3+ of: lower, upper, numbers, symbols.'
        if re.search(r'(.)\1{2,}', password):
            errors['password'] = 'Password must not contain triple repeats.'
        if SEQUENCE_RE.search(password):
            errors['password'] = 'Password must not contain sequential patterns.'
        if services.is_common(password):
            errors['password'] = 'This is a widely-used common password. Choose something unique.'
    if sec_q and not sec_a:
        errors['security_answer'] = 'Security answer required when a question is set.'

    if User.objects.filter(username=username).exists() or User.objects.filter(email__iexact=email).exists():
        errors['username'] = 'Username or email is already registered.'

    if errors:
        return JsonResponse({'success': False, 'message': 'VALIDATION_FAILED', 'errors': errors}, status=422)

    user = User.objects.create(
        fullname=fullname,
        username=username,
        email=email.lower(),
        password_hash=make_password(password),
        security_question=sec_q or None,
        security_answer_hash=make_password(sec_a) if sec_a else None,
    )
    AdminActivityLog.objects.create(
        action='USER_REGISTERED', details=f'New user #{user.pk} ({username})',
    )
    return _ok('ACCOUNT_CREATED', user_id=user.pk)


@csrf_exempt
@require_http_methods(['POST'])
def api_login(request):
    d = _body(request)
    uname = (d.get('username') or '').strip()
    password = d.get('password') or ''
    if not uname or not password:
        return _err('Username and password are required.')

    since = timezone.now() - timezone.timedelta(minutes=15)
    recent_fails = LoginAttempt.objects.filter(
        username=uname, success=False, attempted_at__gt=since,
    ).count()
    if recent_fails >= 5:
        return _err('ACCOUNT_LOCKED :: too many failures, retry in 15 minutes.', 423)

    try:
        user = User.objects.get(username=uname)
    except User.DoesNotExist:
        user = (User.objects.filter(email__iexact=uname).first()
                or User.objects.filter(username__iexact=uname).first())
        if user is None:
            LoginAttempt.objects.create(username=uname, ip_address=_ip(request), success=False)
            return _err('INVALID_CREDENTIALS')

    ok = check_password(password, user.password_hash) and user.is_active
    LoginAttempt.objects.create(
        user=user if ok else None,
        username=uname,
        ip_address=_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')[:250],
        success=ok,
    )
    if not ok:
        msg = 'ACCOUNT_BANNED :: contact administrator.' if not user.is_active else 'INVALID_CREDENTIALS'
        return _err(msg, 401)

    user.last_login = timezone.now()
    user.save(update_fields=['last_login'])
    AdminActivityLog.objects.create(action='USER_LOGIN', details=f'{user.username} logged in')

    session = {
        'user': {'id': user.pk, 'fullname': user.fullname,
                 'username': user.username, 'email': user.email},
        'is_admin': user.is_admin,
        'logged_in': True,
        'token': __import__('secrets').token_hex(24),
        'expires_at': (timezone.now() + timezone.timedelta(hours=4)).isoformat(),
    }
    return _ok('AUTHENTICATION_SUCCESS', session=session)


def _ip(request):
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


# ---------------------------------------------------------------------------
# ANALYSIS
# ---------------------------------------------------------------------------
@csrf_exempt
@require_http_methods(['POST'])
def api_analyze(request):
    d = _body(request)
    password = d.get('password') or ''
    if len(password) < 4:
        return _err('Minimum 4 characters for analysis.', 422)
    result = services.inspect(password)
    result['recommendations'] = services.recommendations(result)
    return _ok('ANALYSIS_COMPLETE', data=result)


@csrf_exempt
@require_http_methods(['POST'])
def api_common_check(request):
    d = _body(request)
    password = d.get('password') or ''
    if not password:
        return _err('PASSWORD_REQUIRED')
    local = services.is_common(password)
    db_hit = CommonPassword.is_common(password) if CommonPassword.objects.exists() else 0
    return _ok('OK', is_common=bool(local or db_hit), database=bool(db_hit))


# ---------------------------------------------------------------------------
# HISTORY
# ---------------------------------------------------------------------------
@csrf_exempt
@require_http_methods(['POST'])
def api_history(request):
    d = _body(request)
    action = d.get('action') or 'list'
    user_id = int(d.get('user_id') or 0)
    if not user_id:
        return _err('USER_ID_REQUIRED')

    if action == 'detail':
        pk = int(d.get('id') or 0)
        obj = AnalyzedPassword.objects.filter(pk=pk, user_id=user_id).first()
        return _ok(data=_record(obj)) if obj else _err('RECORD_NOT_FOUND', 404)

    if action == 'delete':
        pk = int(d.get('id') or 0)
        AnalyzedPassword.objects.filter(pk=pk, user_id=user_id).delete()
        return _ok('RECORD_DELETED')

    if action == 'save':
        result = d.get('result') or {}
        if not isinstance(result, dict) or not result.get('password_placeholder'):
            return _err('RESULT_DATA_REQUIRED')
        r = services.inspect('X' * max(len(str(result.get('password_placeholder', ''))), 8))
        obj = AnalyzedPassword.objects.create(
            user_id=user_id,
            password_placeholder=result.get('password_placeholder')[:250],
            strength_score=int(result.get('score', r['score'])),
            strength_label=result.get('label') or r['label'],
            length=int(result.get('length', 0)),
            has_uppercase=bool(result.get('has_uppercase')),
            has_lowercase=bool(result.get('has_lowercase')),
            has_numbers=bool(result.get('has_numbers')),
            has_special=bool(result.get('has_special')),
            character_count=float(result.get('entropy', 0)),
            link_speed=result.get('linkLabel') or result.get('link_speed') or '',
            estimated_crack_time=result.get('crackTime') or result.get('estimated_crack_time') or '',
            is_common=bool(result.get('isCommon', result.get('is_common'))),
            breached_count=int(result.get('breached', result.get('breached_count', 0))),
            entropy=float(result.get('entropy', 0)),
            analysis_notes=result.get('analysis_notes', ''),
        )
        return _ok('ANALYSIS_SAVED', id=obj.pk)

    try:
        limit = int(d.get('limit') or 0)
    except (TypeError, ValueError):
        limit = 0
    qs = AnalyzedPassword.objects.filter(user_id=user_id)
    if limit:
        qs = qs[:limit]
    return _ok('OK', data=[_record(o) for o in qs])


def _record(o):
    return {
        'id': o.pk,
        'password_placeholder': o.password_placeholder,
        'strength_score': o.strength_score,
        'strength_label': o.strength_label,
        'length': o.length,
        'has_uppercase': int(o.has_uppercase),
        'has_lowercase': int(o.has_lowercase),
        'has_numbers': int(o.has_numbers),
        'has_special': int(o.has_special),
        'entropy': float(o.entropy),
        'estimated_crack_time': o.estimated_crack_time,
        'link_speed': o.link_speed,
        'is_common': int(o.is_common),
        'breached_count': o.breached_count,
        'analysis_notes': o.analysis_notes,
        'analyzed_at': o.analyzed_at.isoformat() if o.analyzed_at else None,
    }


# ---------------------------------------------------------------------------
# REPORTS
# ---------------------------------------------------------------------------
@csrf_exempt
@require_http_methods(['POST'])
def api_report(request):
    d = _body(request)
    user_id = int(d.get('user_id') or 0)
    if not user_id:
        return _err('USER_ID_REQUIRED')

    analyses = AnalyzedPassword.objects.filter(user_id=user_id)
    total = analyses.count()
    score_sum = sum(a.strength_score for a in analyses)
    weak = analyses.filter(strength_label__in=['WEAK', 'FAIR']).count()
    strong = analyses.filter(strength_label__in=['STRONG', 'EXCELLENT']).count()
    common = analyses.filter(is_common=True).count()
    breaches = sum(a.breached_count for a in analyses)

    report = {
        'user_id': user_id,
        'total_analyses': total,
        'avg_strength': round(score_sum / total, 2) if total else 0,
        'weak_passwords': weak,
        'medium_passwords': 0,
        'strong_passwords': strong,
        'excellent_passwords': analyses.filter(strength_label='EXCELLENT').count(),
        'common_detected': common,
        'breach_hits': breaches,
        'analyses': [_record(a) for a in analyses],
        'recommendations': _report_recs(common, weak, breaches, total),
    }

    action = d.get('action') or 'generate'
    if action == 'full':
        return _ok('OK', data=report)

    Report.objects.create(
        user_id=user_id,
        report_type='single',
        report_format='json',
        total_analyses=total,
        avg_strength=report['avg_strength'],
        weak_passwords=weak,
        medium_passwords=0,
        strong_passwords=strong,
        common_detected=common,
        recommendations_count=len(report['recommendations']),
        report_data=json.dumps(report),
    )
    AdminActivityLog.objects.create(
        admin_id=user_id, action='REPORT_GENERATED', details=f'Report for user #{user_id}',
    )
    return _ok('REPORT_GENERATED', report_id=Report.objects.latest('id').pk, data=report)


def _report_recs(common, weak, breaches, total):
    recs = []
    if common:
        recs.append({'severity': 'critical', 'title': 'CRITICAL: Common passwords in use',
                     'desc': f'{common} analyzed values are on global breach lists.'})
    if weak:
        recs.append({'severity': 'high', 'title': 'Increase password complexity',
                     'desc': f'{weak} entries score weakly. Use 12+ chars with mixed classes.'})
    if breaches:
        recs.append({'severity': 'high', 'title': 'Stop using leaked passwords',
                     'desc': f'Found in {breaches} real-world breaches. Rotate now.'})
    recs.append({'severity': 'low', 'title': 'Maintain hygiene',
                 'desc': 'Keep rotating critical accounts every 90 days.'})
    return recs


# ---------------------------------------------------------------------------
# ADMIN
# ---------------------------------------------------------------------------
def _require_admin(request, d):
    admin_id = int(d.get('admin_id') or 0)
    user = User.objects.filter(pk=admin_id, is_admin=True).first()
    if not user:
        return None, _err('FORBIDDEN :: admin privileges required.', 403)
    return user, None


@csrf_exempt
@require_http_methods(['POST'])
def api_admin(request):
    d = _body(request)
    action = d.get('action') or 'overview'

    # user_stats is allowed for any logged-in user
    if action == 'user_stats':
        uid = int(d.get('user_id') or 0)
        if not uid:
            return _err('USER_ID_REQUIRED')
        analyses = AnalyzedPassword.objects.filter(user_id=uid)
        total = analyses.count()
        return _ok('OK', data={
            'total_analyses': total,
            'avg_strength': round(sum(a.strength_score for a in analyses) / total, 2) if total else 0,
            'weak': analyses.filter(strength_label__in=['WEAK', 'FAIR']).count(),
            'medium': 0,
            'strong': analyses.filter(strength_label__in=['STRONG', 'EXCELLENT']).count(),
            'excellent': analyses.filter(strength_label='EXCELLENT').count(),
            'common': analyses.filter(is_common=True).count(),
            'breaches': sum(a.breached_count for a in analyses),
        })

    admin, resp = _require_admin(request, d)
    if not admin:
        return resp

    if action == 'overview':
        today = timezone.now().date()
        week = []
        for i in range(6, -1, -1):
            day = today - timezone.timedelta(days=i)
            week.append(AnalyzedPassword.objects.filter(analyzed_at__date=day).count())
        return _ok('OK', data={
            'total_users': User.objects.count(),
            'total_passwords': AnalyzedPassword.objects.count(),
            'common_passwords': AnalyzedPassword.objects.filter(is_common=True).count(),
            'total_breaches': AnalyzedPassword.objects.aggregate(s=Sum('breached_count'))['s'] or 0,
            'total_reports': Report.objects.count(),
            'active_today': User.objects.filter(last_login__date=today).count(),
            'recent_logins': LoginAttempt.objects.filter(success=True, attempted_at__date=today).count(),
            'week_daily': week,
        })

    if action == 'users':
        users = []
        for u in User.objects.all():
            users.append({
                'id': u.pk, 'username': u.username, 'fullname': u.fullname,
                'email': u.email, 'is_admin': int(u.is_admin), 'is_active': int(u.is_active),
                'last_login': u.last_login.isoformat() if u.last_login else None,
                'analyses': u.analyses.count(),
            })
        return _ok('OK', data=users)

    if action == 'toggle_ban':
        target = int(d.get('target_id') or 0)
        state = 1 if int(d.get('state') or 0) == 1 else 0
        user = User.objects.filter(pk=target).first()
        if not user:
            return _err('TARGET_NOT_FOUND', 404)
        if user.is_admin:
            return _err('CANNOT_MODIFY_ADMIN_ACCOUNT', 403)
        user.is_active = bool(state)
        user.save(update_fields=['is_active'])
        AdminActivityLog.objects.create(admin=admin, action='USER_UNBANNED' if state else 'USER_BANNED',
                                        target_user=user)
        return _ok('USER_UNBANNED' if state else 'USER_BANNED')

    if action == 'delete_user':
        target = int(d.get('target_id') or 0)
        user = User.objects.filter(pk=target).first()
        if not user:
            return _err('TARGET_NOT_FOUND', 404)
        if user.is_admin:
            return _err('CANNOT_DELETE_ADMIN_ACCOUNT', 403)
        AdminActivityLog.objects.create(admin=admin, action='USER_DELETED', target_user=user)
        user.delete()
        return _ok('USER_DELETED')

    if action == 'activity':
        logs = []
        for log in AdminActivityLog.objects.all()[:30]:
            action_name = log.action.upper()
            if action_name in ('USER_BANNED', 'USER_DELETED'):
                level = 'danger'
            elif action_name in ('USER_REGISTERED', 'USER_LOGIN', 'REPORT_GENERATED'):
                level = 'success'
            elif 'FAILED' in action_name:
                level = 'warn'
            else:
                level = 'info'
            logs.append({
                'time': log.created_at.strftime('%H:%M:%S'),
                'type': level,
                'text': f"{log.action} :: {log.details or ''}",
            })
        return _ok('OK', data=logs)

    return _err('UNKNOWN_ACTION')