# Stops the phpMyAdmin PHP web server (anything bound to port 8080).

$pids = (Get-NetTCPConnection -LocalPort 8080 -State Listen -ErrorAction SilentlyContinue) | Select-Object -ExpandProperty OwningProcess
if (-not $pids) {
    Write-Host 'phpMyAdmin server is not running.' -ForegroundColor Yellow
    exit 0
}
foreach ($pid in $pids) {
    Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
}
Write-Host 'phpMyAdmin stopped.' -ForegroundColor Green