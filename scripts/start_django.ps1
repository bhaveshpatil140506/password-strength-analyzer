# Runs the Django development server for the Password Strength Analyzer.
# USAGE: from an already-open terminal (or VS Code task), this stays open.

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$django = Join-Path $root 'django_backend'
$venvPy = Join-Path $django 'venv\Scripts\python.exe'
$pip = Join-Path $django 'venv\Scripts\pip.exe'

if (-not (Test-Path $venvPy)) {
    Write-Host 'First run: creating virtual environment and installing packages...' -ForegroundColor Yellow
    & 'C:\Users\bhave\AppData\Local\Programs\Python\Python312\python.exe' -m venv (Join-Path $django 'venv')
    & $pip install -r (Join-Path $django 'requirements.txt')
}

# Make sure the MySQL instance is up.
& (Join-Path $root 'scripts\start_mysql.ps1')

# Apply any pending migrations and keep seed data in place.
Push-Location $django
try {
    & $venvPy manage.py migrate --noinput
    & $venvPy manage.py seed
} finally {
    Pop-Location
}

Write-Host ''
Write-Host 'Django server:  http://127.0.0.1:8000' -ForegroundColor Green
Write-Host 'Use credentials printed by the seed command above.' -ForegroundColor Green
Write-Host 'Press Ctrl+C to stop.' -ForegroundColor DarkGray
Write-Host ''

Push-Location $django
try {
    & $venvPy manage.py runserver 127.0.0.1:8000
} finally {
    Pop-Location
}