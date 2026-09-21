# Starts phpMyAdmin (PHP built-in web server) at http://127.0.0.1:8080
# Requires: PHP (winget install PHP.PHP.8.4) and the tools\phpmyadmin folder.

$root = Split-Path -Parent $PSScriptRoot
$bat = Join-Path $root 'tools\start_pma.cmd'
if (-not (Test-Path $bat)) {
    Write-Error "Launcher not found: $bat"
    exit 1
}

if (Test-NetConnection -ComputerName 127.0.0.1 -Port 8080 -WarningAction SilentlyContinue -InformationLevel Quiet) {
    Write-Host 'phpMyAdmin is already running.' -ForegroundColor Green
} else {
    Start-Process -FilePath $bat -WindowStyle Hidden
    Start-Sleep -Seconds 5
}

if (Test-NetConnection -ComputerName 127.0.0.1 -Port 8080 -WarningAction SilentlyContinue -InformationLevel Quiet) {
    Write-Host 'phpMyAdmin is running at http://127.0.0.1:8080/' -ForegroundColor Green
    Write-Host 'Log in with: root  /  (empty password)' -ForegroundColor Green
    Start-Process 'http://127.0.0.1:8080/'
} else {
    Write-Warning ("phpMyAdmin did not start. Check logs: " + (Join-Path $root 'tools\pma-server.err'))
}