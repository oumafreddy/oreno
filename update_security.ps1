# Security Update Script for Oreno GRC
# Run this from the project root with .venv activated

Write-Host "=== Security Update Script ===" -ForegroundColor Cyan
Write-Host ""

# Backup requirements.txt
Write-Host "1. Backing up requirements.txt..." -ForegroundColor Yellow
Copy-Item requirements.txt requirements.txt.backup
Write-Host "   Backup created: requirements.txt.backup" -ForegroundColor Green

# Phase 1: Critical Security Updates
Write-Host ""
Write-Host "2. Updating CRITICAL security packages..." -ForegroundColor Yellow
Write-Host "   This may take a few minutes..." -ForegroundColor Gray

pip install --upgrade `
    Django==5.1.14 `
    djangorestframework==3.15.2 `
    djangorestframework-simplejwt==5.5.1 `
    requests==2.32.4 `
    urllib3==2.5.0 `
    protobuf==5.29.5 `
    setuptools==78.1.1

if ($LASTEXITCODE -eq 0) {
    Write-Host "   Critical packages updated successfully!" -ForegroundColor Green
} else {
    Write-Host "   ERROR: Some packages failed to update" -ForegroundColor Red
    exit 1
}

# Phase 2: High Priority Updates
Write-Host ""
Write-Host "3. Updating HIGH PRIORITY packages..." -ForegroundColor Yellow

pip install --upgrade `
    brotli==1.2.0 `
    pdfminer-six==20251107

# Note: pypdf is a major version jump - update separately after testing
Write-Host "   Note: pypdf update (5.4.0 -> 6.1.3) skipped - major version jump" -ForegroundColor Yellow
Write-Host "   Update manually after testing: pip install --upgrade pypdf==6.1.3" -ForegroundColor Yellow

if ($LASTEXITCODE -eq 0) {
    Write-Host "   High priority packages updated successfully!" -ForegroundColor Green
} else {
    Write-Host "   WARNING: Some packages failed to update" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Update Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Update requirements.txt with new versions:" -ForegroundColor White
Write-Host "   pip freeze > requirements_new.txt" -ForegroundColor Gray
Write-Host "   (Then manually merge critical updates into requirements.txt)" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Test your application thoroughly:" -ForegroundColor White
Write-Host "   python manage.py check" -ForegroundColor Gray
Write-Host "   python manage.py migrate --check" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Verify fixes:" -ForegroundColor White
Write-Host "   pip-audit -r requirements.txt" -ForegroundColor Gray
Write-Host ""
Write-Host "4. If everything works, update pypdf:" -ForegroundColor White
Write-Host "   pip install --upgrade pypdf==6.1.3" -ForegroundColor Gray
Write-Host ""

