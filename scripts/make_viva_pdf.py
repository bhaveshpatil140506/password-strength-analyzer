#!/usr/bin/env python
"""Generate Viva_Prep_Questions_Answers.pdf for the Password Strength Analyzer."""

import os

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer,
                                Table, TableStyle)

OUT = os.path.join(r'C:\Users\bhave\OneDrive\Desktop',
                   'Viva_Prep_Questions_Answers.pdf')
INVIGILATOR_OUT = os.path.join(r'C:\Users\bhave\OneDrive\Desktop',
                               'Invigilator_Questions_and_Answers.pdf')

ACCENT = colors.HexColor('#0a7d32')
DARK = colors.HexColor('#14341f')

styles = getSampleStyleSheet()

title_style = ParagraphStyle('TitleX', parent=styles['Title'], fontName='Helvetica-Bold',
                             fontSize=22, leading=27, textColor=DARK, spaceAfter=2)
sub_style = ParagraphStyle('SubX', parent=styles['Normal'], fontName='Helvetica',
                           fontSize=11, leading=15, textColor=colors.HexColor('#555555'),
                           spaceAfter=10)
section_style = ParagraphStyle('SectionX', parent=styles['Heading2'], fontName='Helvetica-Bold',
                               fontSize=14, leading=18, textColor=colors.white,
                               backColor=ACCENT, borderPadding=(5, 6, 5, 6),
                               spaceBefore=14, spaceAfter=8)
q_style = ParagraphStyle('QX', parent=styles['Normal'], fontName='Helvetica-Bold',
                         fontSize=10.5, leading=14, textColor=DARK,
                         spaceBefore=6, spaceAfter=1)
a_style = ParagraphStyle('AX', parent=styles['Normal'], fontName='Helvetica',
                         fontSize=10, leading=14, textColor=colors.black,
                         leftIndent=14, spaceAfter=4)


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def qa(q, a):
    return [Paragraph('Q. ' + esc(q), q_style), Paragraph(esc(a), a_style)]


SECTIONS = [
    ('1. PROJECT ABSTRACT (FOR REPORT)', [
        ('One-paragraph abstract',
         'The Password Strength Analyzer is a full-stack web application that evaluates '
         'user-entered passwords with an eight-check strength score, a separate entropy '
         'estimate, and an estimated crack time at ten billion guesses per second. The '
         'analyzer currently accepts passwords from 4 to 8 characters, so its maximum '
         'possible checklist score is 7 because the 12-character check cannot pass. It '
         'flags weak or commonly used credentials by comparing blind SHA-256 hashes, '
         'further supported by HaveIBeenPwned k-anonymity breach lookup. The system '
         'provides user registration and login with bcrypt-hashed credentials and '
         'brute-force lockout, live analysis with a visual strength meter, personalized '
         'security recommendations, a masked password history (plaintext is never '
         'stored), and executive report generation with export options. An administrator '
         'dashboard enables user management, activity monitoring, and an audit log. '
         'Built with HTML, CSS, and JavaScript on the front end and dual Django (Python) '
         'and PHP (PDO) REST APIs backed by a seven-table MySQL database, the project '
         'demonstrates secure password handling, threat-aware validation, and complete '
         'user workflows from a single unified interface.'),
    ]),
    ('2. 1-MINUTE SPOKEN INTRO (VIVA)', [
        ('Spoken intro',
         'Good morning, Sir/Ma\'am. My project is a Password Strength Analyzer - a web '
         'application that audits how secure a password is. A user registers and logs in '
         'with a bcrypt-based password hash and brute-force lockout, then types a 4-to-8 '
         'character password into the analyzer. It returns a checklist score, its entropy, '
         'and an estimated crack time based on a fixed guessing-speed assumption. '
         'It also detects common passwords such as "password" or "123456" using blind '
         'hashing, so the server never even sees the plaintext, and checks against the '
         'HaveIBeenPwned breach database. Every analysis is saved into a history that '
         'stores only a masked version, the system gives personalized recommendations, '
         'and the user can generate a report and export it. Behind that is a seven-table '
         'MySQL database, served by both Django and PHP backends, and an admin dashboard '
         'where the administrator can manage users and watch a live audit log. The '
         'project runs end to end on this machine. Thank you.'),
    ]),
    ('3. PROJECT OVERVIEW', [
        ('Explain your project in 2 minutes.',
         'It is a cybersecurity web application that audits passwords. It scores password '
         'strength using an eight-check score, estimates entropy and crack time, detects common and '
         'breached passwords, gives personalized security recommendations, stores a masked '
         'password history, generates printable reports, and provides an admin dashboard '
         'with user management and an audit log. Frontend is HTML/CSS/JS; backends are '
         'Django and PHP; database is MySQL.'),
        ('Why do you have TWO backends (Django and PHP)?',
         'Both expose the same REST-style API contract. PHP with PDO is a lightweight '
         'alternative and Django is a full framework. The frontend JavaScript automatically '
         'detects which backend is reachable and falls back gracefully, so the same UI works '
         'under both XAMPP and Django.'),
    ]),
    ('4. STRENGTH ANALYSIS LOGIC', [
        ('How do you calculate password strength?',
         'The displayed score counts eight checks: length >= 8, length >= 12, lowercase, '
         'uppercase, digits, symbols, no triple repeated character, and no recognized '
         'sequential pattern. Scores 0-2 are WEAK, 3-4 FAIR, 5-6 STRONG, and 7-8 '
         'EXCELLENT. Entropy is calculated separately as length x log2(character pool). '
         'Because the current input limit is 8, the 12-character check cannot pass and '
         'the maximum score is 7.'),
        ('What is "estimated crack time"?',
         'The number of guesses needed divided by a hypothetical 10 billion guesses per '
         'second, presented as a human label such as "180 centuries". When the search '
         'space is too large it displays "Safe for decades".'),
        ('Which passwords does registration reject?',
         'Registration requires a non-empty password of at most 8 characters and rejects '
         'passwords found in the common-password list. Sequential patterns are not '
         'blocked, although they lose a point in the analyzer checklist.'),
    ]),
    ('5. SECURITY - IMPLEMENTATION', [
        ('Is the actual password ever stored?',
         'The analysis history stores a masked placeholder and analysis results, not the '
         'entered plaintext. Account passwords are stored as bcrypt-based hashes; the '
         'application verifies a login against the hash.'),
        ('Why bcrypt and not MD5 or plain SHA-256 for passwords?',
         'bcrypt is deliberately slow and automatically salted, which resists brute-force '
         'and rainbow-table attacks. MD5 is fast and cryptographically broken. Fast '
         'hashing functions are unsuitable for password storage.'),
        ('How do you detect common passwords without revealing the plaintext?',
         'The common password table stores only blind SHA-256 digests of the top common '
         'passwords. The server hashes the entered password and compares digests, so the '
         'database never contains the plaintext of user inputs. Breach lookup also uses '
         'HaveIBeenPwned k-anonymity: only the first 5 hex characters of the SHA-1 hash '
         'are sent, and the suffix list is compared locally.'),
        ('How do you prevent SQL injection?',
         'The PHP backend uses PDO prepared statements with ? placeholders, and the '
         'Django backend uses the ORM. No raw user input is concatenated into SQL.'),
        ('How do you prevent brute-force login attacks?',
         'Every attempt is recorded in the login_attempts table with IP address and '
         'user agent. After 5 failed attempts within 15 minutes the account is locked '
         'for 15 minutes. Admin bans also prevent login via the is_active flag.'),
        ('How is the admin area protected?',
         'The is_admin flag is checked server-side on both backends for every admin API '
         'call, and every administrative action is written to the admin_activity_log '
         'audit table.'),
        ('How are forms validated?',
         'Validation happens on both the client side (JavaScript, for instant feedback) '
         'and the server side (Django/PHP), because client checks can be bypassed.'),
    ]),
    ('6. DATABASE DESIGN', [
        ('How many tables and what are the relationships?',
         'Seven tables: users, analyzed_passwords, common_passwords, recommendations, '
         'reports, login_attempts and admin_activity_log. users is the parent table with '
         'one-to-many relationships to analyses, reports and logins; each recommendation '
         'optionally links back to an analyzed password.'),
        ('Why MySQL with phpMyAdmin?',
         'MySQL was specified for the project and phpMyAdmin provides a GUI to inspect '
         'the schema, browse rows and export data, which also helps during the demo.'),
    ]),
    ('7. PRACTICAL / LIVE DEMO', [
        ('Walk me through the user flow.',
         'Register -> login -> type a password on the analyzer -> live meter shows score, '
         'entropy, crack time and checklist -> save to history (masked only) -> get '
         'recommendations -> generate a report with export options (print, CSV, JSON) -> '
         'the admin dashboard shows totals, weekly charts and the audit log.'),
        ('How would you deploy this in production?',
         'Run Django behind a production WSGI server such as Gunicorn with nginx or '
         'Apache, MySQL as a Windows service, enable HTTPS/TLS, disable DEBUG mode, '
         'remove demo accounts/credentials, harden session handling and CSRF, and use '
         'environment variables for secrets.'),
        ('What is your future scope?',
         'Add OTP/2FA, breach-alert email notifications, a password generator, browser '
         'extension, password-manager import and machine-learning based strength '
         'prediction.'),
    ]),
    ('8. CORE CONCEPT DRILL', [
        ('Difference between encoding, hashing and encryption?',
         'Encoding is reversible without a key and is used to represent data (Base64, '
         'UTF-8). Hashing is one-way and fixed length - used to verify integrity and '
         'store passwords; it cannot be reversed. Encryption is reversible but requires '
         'a secret key, and is used for confidentiality.'),
        ('MD5 vs SHA-256 vs bcrypt?',
         'MD5 (128-bit) is broken because collisions are known. SHA-256 (256-bit) is '
         'suitable for integrity checks but is too fast for passwords. bcrypt is slow '
         'and salted, making it the correct choice for password storage.'),
        ('What is a salt and why use it?',
         'A salt is a random value added before hashing, so identical passwords produce '
         'different hashes. It defeats rainbow tables and duplicate-hash detection.'),
        ('Sessions vs cookies vs tokens?',
         'Cookies are small values stored by the browser. Sessions are server-side state '
         'identified by a session id held in a cookie. Tokens are self-contained '
         'credentials sent in headers - this project issues a token with a 4-hour '
         'expiry after login.'),
        ('HTTP vs HTTPS?',
         'HTTPS is HTTP over TLS. It encrypts traffic so passwords and data are not '
         'readable in transit (prevents man-in-the-middle attacks).'),
        ('Symmetric vs asymmetric encryption?',
         'Symmetric encryption uses one shared key (e.g., AES) and is fast. Asymmetric '
         'encryption uses a public/private key pair (e.g., RSA) and is slower - used for '
         'key exchange and digital signatures.'),
        ('XSS vs SQL injection?',
         'XSS is a client-side attack where an attacker injects a script that runs in '
         'another user\'s browser; it is prevented by output escaping. SQL injection is '
         'a server-side attack where SQL is injected through user input; it is prevented '
         'by input sanitization and parameterized queries.'),
        ('POST vs GET?',
         'GET places parameters in the URL - used for fetching, and stays in browser '
         'history. POST places parameters in the request body - used for submitting data. '
         'Passwords must never be sent via GET.'),
        ('How would you add two-factor authentication?',
         'Implement TOTP: generate a per-user secret, show it as a QR code for Google '
         'Authenticator, and verify a time-based one-time code on login.'),
        ('What happens if two users choose the same password?',
         'Because each account uses unique salts, the stored bcrypt hashes are '
         'completely different, so identical passwords cannot be detected from the '
         'database alone.'),
    ]),
    ('9. 30-SECOND DEMO SCRIPT', [
        ('Register',
         'Create an account and intentionally try the bad password "123456" - show how '
         'it gets rejected as too weak/common, then register with a strong password.'),
        ('Analyze',
         'Type an 8-character sample such as "A7#vK2!m". The meter and checklist update '
         'instantly. Explain that the score is a simple checklist, while entropy and the '
         'crack-time estimate are separate heuristic outputs.'),
        ('Common check',
         'Type "password" - the top-common list and breach lookup flag it red, proving '
         'the system never suggests or accepts such weak credentials.'),
        ('History',
         'Save the analysis, then open History - only a masked placeholder is stored, '
         'demonstrating that the real password never touches the database.'),
        ('Report',
         'Generate the executive report with charts and export options (print, CSV, JSON).'),
        ('Admin',
         'Log in as admin - user list with ban/delete, weekly activity chart and the '
         'live audit log of every recorded action.'),
    ]),
    ('10. LIKELY INVIGILATOR QUESTIONS AND MODEL ANSWERS', [
        ('What problem does your project solve?',
         'It gives users a quick assessment of password patterns, common-password risk, '
         'possible breach exposure, and password reuse risk awareness, with recommendations '
         'and a private analysis history.'),
        ('How is the password strength score calculated?',
         'The analyzer awards one point for each of eight checks: length of at least 8, '
         'length of at least 12, lowercase, uppercase, digits, symbols, no character '
         'repeated three times in a row, and no recognized sequential pattern.'),
        ('What do Weak, Fair, Strong, and Excellent mean?',
         'Weak is 0-2 checks, Fair is 3-4, Strong is 5-6, and Excellent is 7-8. With the '
         'current eight-character maximum, the 12-character check cannot pass, so the '
         'maximum reachable score is 7.'),
        ('Why does password length matter?',
         'A longer password generally creates more possible combinations and increases '
         'the search space. The analyzer currently limits input to 8 characters, which '
         'is not a recommended limit for real account security.'),
        ('How does the system check common or breached passwords?',
         'It checks known common-password entries. For breach lookup, it uses the Have I '
         'Been Pwned range method: it sends only the first five characters of the SHA-1 '
         'hash and compares the returned suffixes locally.'),
        ('Is the entered password stored in the database?',
         'No plaintext analysis password is stored. History stores a masked placeholder '
         'and analysis results. Account credentials are stored as bcrypt-based hashes.'),
        ('How are passwords protected during login?',
         'The server compares the submitted password with its stored bcrypt-based hash. '
         'The application also records failed attempts and applies a temporary lockout '
         'after repeated failures.'),
        ('What happens if a password is longer than eight characters?',
         'The interface limits typing to eight characters, and server-side validation '
         'rejects longer passwords so the rule cannot be bypassed by skipping the form.'),
        ('Are sequential passwords such as abc123 blocked?',
         'No. They can be analyzed, but a recognized sequence fails the no-sequential '
         'check and lowers the score. A common-password match can also raise a separate warning.'),
        ('What is entropy in your project?',
         'Entropy is an estimate based on password length and the character categories '
         'present. The implementation calculates length multiplied by log base 2 of the '
         'estimated character pool.'),
        ('What assumptions affect the crack-time estimate?',
         'It converts estimated entropy to a search-space size and assumes 10 billion '
         'guesses per second. It is illustrative, not a prediction of a specific attacker '
         'or hardware setup.'),
        ('Which technologies did you use?',
         'The frontend uses HTML, CSS, and JavaScript. The project includes Django and '
         'PHP APIs and uses MySQL for persistent data.'),
        ('How do you prevent users from seeing another user’s analysis history?',
         'The API authenticates the session token, identifies the logged-in user, and '
         'checks that the requested history belongs to that user before returning it.'),
        ('What are the limitations of the scoring method?',
         'It is a small heuristic checklist, not a guarantee of security. It can reward '
         'character variety without understanding context or real-world attacker behavior. '
         'The eight-character cap is also too short for strong real-world passwords.'),
        ('What would you improve next?',
         'I would allow longer passphrases, use a better calibrated strength estimator '
         'that recognizes common patterns, and make crack-time estimates explicit about '
         'online versus offline attack conditions.'),
    ]),
]

story = []
story.append(Paragraph('Password Strength Analyzer', title_style))
story.append(Paragraph('Viva / Invigilator Preparation  -  Question Bank with Model Answers', sub_style))

for name, items in SECTIONS:
    story.append(Paragraph(esc(name), section_style))
    for qtext, atext in items:
        story.extend(qa(qtext, atext))

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=17 * mm, rightMargin=17 * mm,
                        topMargin=15 * mm, bottomMargin=15 * mm,
                        title='Password Strength Analyzer - Viva Q&A',
                        author='Password Strength Analyzer Project')
doc.build(story)
print('PDF written:', OUT)

qa_story = [
    Paragraph('Password Strength Analyzer', title_style),
    Paragraph('Invigilator Questions with Model Answers', sub_style),
    Paragraph('15 Questions', section_style),
]
for qtext, atext in SECTIONS[-1][1]:
    qa_story.extend(qa(qtext, atext))

qa_doc = SimpleDocTemplate(INVIGILATOR_OUT, pagesize=A4,
                           leftMargin=17 * mm, rightMargin=17 * mm,
                           topMargin=15 * mm, bottomMargin=15 * mm,
                           title='Password Strength Analyzer - Invigilator Q&A',
                           author='Password Strength Analyzer Project')
qa_doc.build(qa_story)
print('PDF written:', INVIGILATOR_OUT)
