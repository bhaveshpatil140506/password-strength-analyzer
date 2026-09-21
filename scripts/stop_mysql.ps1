# Stops the user-level MySQL 8.4 instance (if running).
Get-Process mysqld -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2
if (Get-Process mysqld -ErrorAction SilentlyContinue) {
    Write-Warning 'Some mysqld processes are still running.'
} else {
    Write-Host 'MySQL stopped.' -ForegroundColor Green
}