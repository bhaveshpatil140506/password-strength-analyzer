# 🔐 PassGuard — Password Strength Analyzer

A full-stack cybersecurity web application that audits passwords, detects breached/common credentials,
computes entropy and crack-times, and produces pentest-grade reports.

**Frontend:** HTML · CSS · JavaScript (hacking/Matrix theme, animations, matrix-rain canvas, glitch effects)

**Backend:** Django (Python REST API) **+** PHP (PDO REST API)

**Database:** MySQL via phpMyAdmin — database name: `password_analyzer`

---

## 📁 Project Structure

```
Password Strength analyzer/
├── frontend/
│   ├── index.html           (landing page)
│   ├── register.html        (registration)
│   ├── login.html           (login)
│   ├── analyzer.html        (password input + strength analysis)
│   ├── dashboard.html       (user dashboard)
│   ├── history.html         (password history)
│   ├── recommendations.html (security recommendations)
│   ├── report.html          (report generation)
│   ├── admin_dashboard.html (admin dashboard)
│   ├── css/style.css        (hacking theme + animations)
│   └── js/
│       ├── common.js        (session, toasts, matrix bg, API router)
│       ├── validations.js   (form + password validations)
│       ├── analyzer.js      (analysis engine)
│       ├── analyzer_page.js
│       ├── auth.js
│       ├── dashboard.js
│       ├── history.js
│       ├── recommendations.js
│       ├── report.js
│       └── admin.js
├── django_backend/          (complete Django project + REST API)
│   ├── manage.py
│   ├── config/              (settings, urls, wsgi, asgi)
│   └── analyzer/            (models, views, serializers, services, admin)
├── php_backend/             (PHP REST API + installer)
│   ├── install.php          (imports schema + creates admin)
│   ├── config/database.php  (PDO connection)
│   ├── config/common_list.php
│   └── api/                 (register/login/history/report/admin/common_passwords)
└── database/
    └── schema.sql           (phpMyAdmin-compatible MySQL schema + seed data)
```

---

## 🚀 Setup — XAMPP / PHP / phpMyAdmin (recommended, both backends work)

1. **Install XAMPP**, start **Apache** and **MySQL**.
2. Open **phpMyAdmin** → create an empty database named `password_analyzer`.
   (Or just run the installer — it creates everything.)
3. Copy the entire project folder into `C:\xampp\htdocs\`.
4. Open in browser:
   ```
   http://localhost/Password-Strength-Analyzer/php_backend/install.php
   ```
   This imports `database/schema.sql`, creates all tables and the default admin.
5. Save the one-time admin password printed by the installer, then **delete `install.php`** (security).
6. Open the app:
   ```
   http://localhost/Password-Strength-Analyzer/frontend/index.html
   ```

> The PHP API path is derived from the served project location. For a custom
> deployment, define `window.PSA_API_BASE` before loading `js/common.js`.

### Initial admin
- username: `admin`
- password: generated once by the installer; set `PSA_ADMIN_PASSWORD` before installation or seeding to choose/reset it.

---

## 🚀 Setup — Django backend (verified on Windows 10/11)

```bash
# 0) One-time installs (if not present)
winget install -e --id Python.Python.3.12
winget install -e --id Oracle.MySQL

# 1) Start MySQL, then create the database (root, empty password by default)
powershell -ExecutionPolicy Bypass -File scripts\start_mysql.ps1
mysql -u root -e "CREATE DATABASE IF NOT EXISTS password_analyzer CHARACTER SET utf8mb4"

# 2) Create venv + install packages
cd django_backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# 3) Create tables (PyMySQL driver used on Windows — no C compiler needed)
python manage.py makemigrations analyzer
python manage.py migrate

# 4) Seed admin, demo user + common-passwords table (prints one-time generated passwords)
python manage.py seed

# 5) Run
python manage.py runserver
```

Now the *whole site* (pages + API) runs at: **http://127.0.0.1:8000/**

**Quick start (one command), also usable in VS Code terminal:**
```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_django.ps1
```

The frontend JS automatically falls back to the Django API (`/api/...`)
when the PHP backend is unreachable — so either backend can drive the UI.

### ▶️ Run inside VS Code
1. Open the project folder **`Password Strength analyzer`** in VS Code.
2. Install the **Python** extension (ms-python.python).
3. **Option A (recommended):** run task `Ctrl+Shift+P → "Tasks: Run Task" →
   "Run Django server (localhost:8000)"` — starts MySQL (if needed), runs
   migrate + seed, then serves the app.
4. **Option B (debugger):** open **Run and Debug** (`Ctrl+Shift+D`) and choose
   **"Django: runserver (Option C)"**, then press F5.
5. Open http://127.0.0.1:8000/ — *index.html*, login, analyzer, history,
   report, and admin_dashboard are all served by Django.

> **Note:** MySQL runs as a **user-level process** on this setup (no admin
> service). Use `scripts\start_mysql.ps1` / `scripts\stop_mysql.ps1` to
> control it after a reboot.

### 🐬 phpMyAdmin (browse the database in a GUI)

```powershell
# One-time: install PHP
winget install -e --id PHP.PHP.8.4

# Start phpMyAdmin (opens http://127.0.0.1:8080/)
powershell -ExecutionPolicy Bypass -File scripts\start_phpmyadmin.ps1
```

- Login: username **root**, **empty** password.
- Database `password_analyzer` → click tables to browse rows.
- Also available as a VS Code task: `Terminal → Run Task… → Start phpMyAdmin`.
- Stops with `scripts\stop_phpmyadmin.ps1`.

### Default accounts
| Role | Username | Password |
|---|---|---|
| Admin | `admin` | Printed once when a new account is created |
| Demo user | `demo` | Printed once when a new account is created by Django seeding |
| phpMyAdmin | `root` | *(empty)* |

> **Two-backend note:** both backends share one MySQL database, so they stay in sync
> automatically. If you prefer Django to own a separate fresh schema, change the
> database name in `config/settings.py` (e.g. `password_analyzer_django`) and run
> `python manage.py migrate` normally.

---

## 🔌 API Reference

**PHP** (`php_backend/api/`) and **Django** (`/api/`) expose the same contract:

| Endpoint | Method | Body | Purpose |
|---|---|---|---|
| `register.php` / `api/register` | POST | fullname, username, email, password | Create account |
| `login.php` / `api/login` | POST | username, password | Authenticate (lockout after 5 fails / 15 min) |
| `history.php` / `api/history` | POST | action: `list`|`save`|`detail`|`delete`, user_id, ... | History CRUD |
| `report.php` / `api/report` | POST | action: `generate`|`full`, user_id, result_data? | Generate report |
| `admin.php` / `api/admin` | POST | action: `overview`|`users`|`toggle_ban`|`delete_user`|`activity`|`user_stats` | Administration |
| `common_passwords.php` / `api/common-check` | POST | password | Common password check |

---

## 🔍 Strength Analysis Engine

Computed **client-side** (JS) and **server-side** (Django `services.py`):

- Entropy: `length × log2(character_pool)`
- 8 complexity checks: length≥8, length≥12, lowercase, uppercase, numbers, symbols, no repeats, no sequences
- Crack-time estimate at 10 billion guesses/second
- Link-speed risk table
- HaveIBeenPwned **k-anonymity** breach lookup (`checkBreached`)
- Analyzer mode accepts passwords of any nonzero length. Account registration and login currently allow up to 8 characters and reject common passwords.

---

## 🛡️ Security Notes

- Analyzed passwords are stored only as masked placeholders; account passwords use salted bcrypt hashes over a SHA-256 pre-digest so both APIs can verify long passwords consistently.
- Login attempts are audited with IP + user-agent; accounts lock after repeated failures.
- Protected API requests use expiring bearer sessions stored as token hashes; admin actions also check `is_admin` server-side.
- Before deployment, set `PSA_DEBUG=0`, `PSA_DJANGO_SECRET_KEY`, `PSA_ALLOWED_HOSTS`, and the `PSA_DB_*` connection variables. Keep secrets out of Git.
- `.htaccess` sets security headers on the PHP API.

---

## Offline use

The standalone analyzer page can run without an application server, but breach
checks need an internet connection. Accounts, saved history, reports, and admin
features require a configured PHP or Django API and database. Account pages show
a connection message instead of presenting sample data as real account data.
