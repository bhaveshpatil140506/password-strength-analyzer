"""
Password Strength Analyzer - pure-Python analysis engine.
Mirrors the client-side JavaScript logic so Django can return authoritative results.
"""

import math
import re

COMMON = [
    '123456', 'password', '123456789', '12345678', '12345',
    'qwerty', 'abc123', 'password1', '111111', '1234567',
    'iloveyou', 'admin', 'welcome', 'monkey', 'login',
    'dragon', 'master', 'letmein', 'hello', 'freedom',
    'whatever', 'trustno1', 'sunshine', 'qwerty123', '123123',
    'passw0rd', '654321', 'qazwsx', 'princess', 'football',
    'ashley', 'batman', 'superman', 'soccer', 'jordan',
    'michael', 'shadow', '1234', '000000', 'qwertyuiop',
    'p@ssw0rd', 'Pa55w0rd', 'password123', 'letmein123',
    'admin123', 'welcome123', 'qwerty12345', '1q2w3e4r',
    'zaq12wsx', 'asdfgh', 'zxcvbn', 'Password1', 'Passw0rd!',
]

SEQUENCE_RE = re.compile(
    r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz|012|123|234|345|456|567|678|789)',
    re.IGNORECASE,
)
REPEAT_RE = re.compile(r'(.)\1{2,}')


def calculate_entropy(password: str) -> float:
    pool = 0
    if re.search(r'[a-z]', password):
        pool += 26
    if re.search(r'[A-Z]', password):
        pool += 26
    if re.search(r'[0-9]', password):
        pool += 10
    if re.search(r'[^A-Za-z0-9]', password):
        pool += 33
    if pool == 0:
        return 0.0
    return len(password) * math.log2(pool)


def estimate_crack_time(entropy: float) -> str:
    secs = (2 ** entropy) / 1e10
    if secs < 1:
        return 'Instantly'
    if secs < 60:
        return f'{int(secs)} seconds'
    if secs < 3600:
        return f'{int(secs / 60)} minutes'
    if secs < 86400:
        return f'{int(secs / 3600)} hours'
    if secs < 86400 * 365:
        return f'{int(secs / 86400)} days'
    if secs < 86400 * 365 * 100:
        return f'{int(secs / (86400 * 365))} years'
    if secs < 86400 * 365 * 100000:
        return f'{int(secs / (86400 * 365 * 100))} centuries'
    return 'Billions of years (practically unbreakable)'


def link_speed(entropy: float) -> tuple:
    if entropy < 28:
        return 'Cracked instantly', '1 in 1'
    if entropy < 36:
        return 'Cracked within minutes', '1 in 10'
    if entropy < 60:
        return 'Cracked within months', '1 in 100'
    if entropy < 80:
        return 'Safe for decades', '1 in 10,000,000'
    return 'Effectively unbreakable', '1 in 10^20'


def is_common(password: str) -> bool:
    return password.lower() in [c.lower() for c in COMMON]


def inspect(password: str) -> dict:
    length = len(password)
    checks = {
        'length8': length >= 8,
        'length12': length >= 12,
        'lowercase': bool(re.search(r'[a-z]', password)),
        'uppercase': bool(re.search(r'[A-Z]', password)),
        'numbers': bool(re.search(r'[0-9]', password)),
        'special': bool(re.search(r'[^A-Za-z0-9]', password)),
        'noRepeat': not REPEAT_RE.search(password),
        'noSequential': not SEQUENCE_RE.search(password),
    }
    score = sum(checks.values())

    if score <= 2:
        label, cls = 'WEAK', 'weak'
    elif score <= 4:
        label, cls = 'FAIR', 'medium'
    elif score <= 6:
        label, cls = 'STRONG', 'strong'
    else:
        label, cls = 'EXCELLENT', 'excellent'

    entropy = calculate_entropy(password)
    speed, odds = link_speed(entropy)

    return {
        'password_placeholder': password[:2] + '********' + password[-1],
        'score': score,
        'strength_score': score,
        'label': label,
        'strength_label': label,
        'strength_class': cls,
        'length': length,
        'has_uppercase': checks['uppercase'],
        'has_lowercase': checks['lowercase'],
        'has_numbers': checks['numbers'],
        'has_special': checks['special'],
        'character_count': round(entropy, 2),
        'entropy': round(entropy, 2),
        'link_speed': speed,
        'estimated_crack_time': estimate_crack_time(entropy),
        'is_common': is_common(password),
        'breached_count': 0,
        'checks': checks,
    }


def recommendations(result: dict) -> list:
    checks = result['checks']
    recs = []
    if not checks['length8']:
        recs.append({'severity': 'high', 'title': 'Increase password length',
                     'desc': 'Your password is shorter than 8 characters. Longer passwords are exponentially harder to brute-force.'})
    if not checks['uppercase']:
        recs.append({'severity': 'medium', 'title': 'Add uppercase letters',
                     'desc': 'Mixed-case passwords dramatically expand the search space.'})
    if not checks['lowercase']:
        recs.append({'severity': 'medium', 'title': 'Add lowercase letters',
                     'desc': 'Include lowercase letters to increase entropy and resist dictionary attacks.'})
    if not checks['numbers']:
        recs.append({'severity': 'medium', 'title': 'Include numbers',
                     'desc': 'Numbers expand character variety. Avoid common sequences like 1234.'})
    if not checks['special']:
        recs.append({'severity': 'medium', 'title': 'Use special characters',
                     'desc': 'Symbols like @ # $ % add significant strength.'})
    if not checks['noRepeat']:
        recs.append({'severity': 'high', 'title': 'Remove repeated characters',
                     'desc': 'A character repeated 3+ times in a row weakens the password.'})
    if not checks['noSequential']:
        recs.append({'severity': 'high', 'title': 'Avoid sequential patterns',
                     'desc': 'Sequences like abc or 123 are among the first things attackers try.'})
    if result['is_common']:
        recs.insert(0, {'severity': 'critical', 'title': 'Dangerously common password',
                        'desc': 'This password appears in the world\'s most-used lists. Change it immediately.'})
    if not recs:
        recs.append({'severity': 'low', 'title': 'Password looks solid',
                     'desc': 'Great job! Consider a passphrase and enabling 2FA everywhere.'})
    return recs