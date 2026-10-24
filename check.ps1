# AMLIS local validation runner (PowerShell equivalent to `make check`)
$ErrorActionPreference = "Stop"

Write-Host "==> Checking Lint & Formatting (Ruff)..." -ForegroundColor Cyan
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\ruff.exe format --check .

Write-Host "==> Checking Types (Mypy)..." -ForegroundColor Cyan
.\.venv\Scripts\mypy.exe

Write-Host "==> Checking Service Boundaries (Import Linter)..." -ForegroundColor Cyan
.\.venv\Scripts\lint-imports.exe

Write-Host "==> Running Leakage Test Suite..." -ForegroundColor Cyan
.\.venv\Scripts\pytest.exe tests/leakage

Write-Host "==> Running Full Test Suite..." -ForegroundColor Cyan
.\.venv\Scripts\pytest.exe

Write-Host "`n[PASS] All checks passed successfully!" -ForegroundColor Green
