# Starts the user-level MySQL 8.4 instance used by the Django backend.
# Idempotent: does nothing if mysqld is already listening on 127.0.0.1:3306.

$mysqld = 'C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe'
$datadir = Join-Path $env:LOCALAPPDATA 'MySQL\data'
$logdir = Join-Path $env:LOCALAPPDATA 'MySQL\logs'

if (-not (Test-Path $mysqld)) {
    Write-Error "mysqld.exe not found at $mysqld. Install MySQL 8.4 first (winget install Oracle.MySQL)."
    exit 1
}

$listening = Test-NetConnection -ComputerName 127.0.0.1 -Port 3306 -WarningAction SilentlyContinue -InformationLevel Quiet
if ($listening) {
    Write-Host 'MySQL is already running on 127.0.0.1:3306.' -ForegroundColor Green
    exit 0
}

if (-not (Test-Path $datadir)) {
    Write-Host 'Initializing MySQL data directory (root, no password)...'
    New-Item -ItemType Directory -Force -Path $datadir, $logdir | Out-Null
    & $mysqld --initialize-insecure --basedir='C:\Program Files\MySQL\MySQL Server 8.4' --datadir=$datadir
    if ($LASTEXITCODE -ne 0) { Write-Error 'mysqld --initialize-insecure failed.'; exit 1 }
}

New-Item -ItemType Directory -Force -Path $logdir | Out-Null
$args = '"--basedir=C:\Program Files\MySQL\MySQL Server 8.4" "--datadir=' + $datadir + '" --port=3306 --bind-address=127.0.0.1'
Start-Process -FilePath $mysqld -ArgumentList $args `
    -RedirectStandardOutput (Join-Path $logdir 'mysql.out.log') `
    -RedirectStandardError (Join-Path $logdir 'mysql.err.log') -WindowStyle Hidden

Start-Sleep -Seconds 10
if (Test-NetConnection -ComputerName 127.0.0.1 -Port 3306 -WarningAction SilentlyContinue -InformationLevel Quiet) {
    Write-Host 'MySQL started.' -ForegroundColor Green
} else {
    Write-Warning 'MySQL did not report listening yet. Check logs: '
    Write-Host (Join-Path $logdir 'mysql.err.log')
}