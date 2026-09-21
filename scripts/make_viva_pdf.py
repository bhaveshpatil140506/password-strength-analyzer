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
         'the security of user-chosen passwords. It assigns a strength score from 0 to 10 '
         'based on entropy (length x log2 of the character pool) and eight complexity '
         'checks, estimates password crack time at ten billion guesses per second, and '
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
         'with validations such as bcrypt hashing and brute-force lockout, then types any '
         'password into the analyzer. It returns a score out of 10, its entropy, and an '
         'estimated crack time - for example, how many centuries it would take to guess. '
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
         'strength on a 0-10 scale, estimates entropy and crack time, detects common and '
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
         'Two components: (1) Shannon entropy = length x log2(character pool size), and '
         '(2) an 8-point checklist - length >= 8, length >= 12, lowercase, uppercase, '
         'digits, symbols, no repeated characters, and no sequential patterns. The score '
         '0-10 maps to labels: WEAK, FAIR, GOOD, STRONG, EXCELLENT.'),
        ('What is "estimated crack time"?',
         'The number of guesses needed divided by a hypothetical 10 billion guesses per '
         'second, presented as a human label such as "180 centuries". When the search '
         'space is too large it displays "Safe for decades".'),
        ('Which passwords does registration reject?',
         'Passwords under 8 characters, passwords using fewer than 3 character classes '
         '(lowercase, uppercase, digits, symbols), passwords with triple repeats such as '
         '"aaa", passwords with sequential patterns such as "123" or "abc", and any '
         'password found in the common passwords list.'),
    ]),
    ('5. SECURITY - IMPLEMENTATION', [
        ('Is the actual password ever stored?',
         'No. Only a masked placeholder such as "Tr********3" is stored in the history '
         'table. For login verification only the bcrypt (PBKDF2) hash is stored.'),
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
         'Type "Tr0ub4dor&3" - it jumps to 7/10 with roughly 72 bits of entropy and an '
         'estimated crack time far beyond centuries. The meter, checklist and analytics '
         'react instantly.'),
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
]

story = []
story.append(Paragraph('Password Strength Analyzer', title_style))
story.append(Paragraph('Viva / Invigilator Preparation  -  Question Bank with Model Answers', sub_style))

for name, items in SECTIONS:
    story.append(Paragraph(esc(name), section_style))
    for qtext, atext in items:
        story.extend(qa(qtext, atext))

story.append(Spacer(1, 10))
foot = Table([[Paragraph(esc('Default logins:  admin / Admin@123   |   demo / Demo@123'
                             '   |   phpMyAdmin: root / (empty)'), a_style)]],
             colWidths=[176 * mm])
foot.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#eef7f1')),
    ('BOX', (0, 0), (-1, -1), 0.75, ACCENT),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
story.append(foot)

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=17 * mm, rightMargin=17 * mm,
                        topMargin=15 * mm, bottomMargin=15 * mm,
                        title='Password Strength Analyzer - Viva Q&A',
                        author='Password Strength Analyzer Project')
doc.build(story)
print('PDF written:', OUT)
