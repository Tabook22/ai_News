param(
    [Parameter(Position = 0)]
    [string]$Message = "Update magazine"
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "1/4  Staging local changes..." -ForegroundColor Cyan
git add .

$staged = @(git diff --cached --name-only)
if ($staged -match '(^|/)\.env$') {
    throw "Refusing to deploy: .env is staged. Remove it with: git reset .env"
}

if ($staged.Count -eq 0) {
    Write-Host "     No new local changes." -ForegroundColor DarkGray
} else {
    Write-Host "2/4  Committing..." -ForegroundColor Cyan
    git commit -m $Message
}

Write-Host "3/4  Pushing to GitHub..." -ForegroundColor Cyan
git push origin main

Write-Host "4/4  Updating the VPS and restarting the service..." -ForegroundColor Cyan
ssh root@76.13.243.173 "cd /var/www/ainews && sudo -u www-data git pull --ff-only && sudo systemctl restart ainews && sleep 1 && systemctl is-active ainews"

Write-Host ""
Write-Host "Live: https://nasserdiary.com/ainews/" -ForegroundColor Green
Write-Host "Admin: https://nasserdiary.com/ainews/login" -ForegroundColor Green
