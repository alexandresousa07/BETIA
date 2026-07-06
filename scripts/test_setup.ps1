# Football AI Analyst - Teste rapido do ambiente
# Uso: .\scripts\test_setup.ps1

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

Write-Host "`n=== Football AI Analyst - Diagnostico ===" -ForegroundColor Cyan

# 1. Verificar .env
$envLine = Get-Content ".env" | Where-Object { $_ -match '^API_FOOTBALL_KEY=' } | Select-Object -First 1
if ($envLine -match 'your-api-football-key') {
    Write-Host "[FALHA] API_FOOTBALL_KEY ainda e placeholder no .env" -ForegroundColor Red
    Write-Host "        Edite .env, coloque sua chave real e salve (Ctrl+S)" -ForegroundColor Yellow
    Write-Host "        Depois: docker compose up -d --force-recreate backend celery-worker celery-beat`n" -ForegroundColor Yellow
    $envOk = $false
} else {
    Write-Host "[OK] API_FOOTBALL_KEY configurada no .env" -ForegroundColor Green
    $envOk = $true
}

# 2. Containers
Write-Host "`n--- Containers ---" -ForegroundColor Cyan
docker compose ps --format "table {{.Name}}\t{{.Status}}"

# 3. Health check
Write-Host "`n--- API Health ---" -ForegroundColor Cyan
try {
    $health = Invoke-RestMethod "http://localhost:8000/api/v1/health" -TimeoutSec 5
    if ($health.success) {
        Write-Host "[OK] Backend: $($health.data.status)" -ForegroundColor Green
    }
} catch {
    Write-Host "[FALHA] Backend nao responde em http://localhost:8000" -ForegroundColor Red
}

# 4. Frontend
Write-Host "`n--- Frontend ---" -ForegroundColor Cyan
try {
    $r = Invoke-WebRequest "http://localhost:3000" -TimeoutSec 5 -UseBasicParsing
    if ($r.StatusCode -eq 200) {
        Write-Host "[OK] Frontend em http://localhost:3000" -ForegroundColor Green
    }
} catch {
    Write-Host "[FALHA] Frontend nao responde em http://localhost:3000" -ForegroundColor Red
}

if (-not $envOk) {
    Write-Host "`n=== Corrija o .env antes de continuar ===" -ForegroundColor Yellow
    exit 1
}

# 5. Migracoes
Write-Host "`n--- Migracoes ---" -ForegroundColor Cyan
docker compose exec backend python scripts/migrate_competitions.py 2>&1 | Select-Object -Last 2
docker compose exec backend python scripts/migrate_odds.py 2>&1 | Select-Object -Last 1

# 6. Sync ligas
Write-Host "`n--- Sincronizar Ligas ---" -ForegroundColor Cyan
try {
    $sync = Invoke-RestMethod -Method POST "http://localhost:8000/api/v1/competitions/sync" -TimeoutSec 120
    Write-Host "[OK] Ligas sincronizadas: $($sync.data.fetched) da API, $($sync.data.total_in_db) no banco" -ForegroundColor Green
} catch {
    Write-Host "[FALHA] Sync de ligas: $($_.ErrorDetails.Message)" -ForegroundColor Red
    Write-Host "        Verifique sua chave em https://dashboard.api-football.com/" -ForegroundColor Yellow
}

# 7. Sync partidas ao vivo
Write-Host "`n--- Sincronizar Partidas ---" -ForegroundColor Cyan
try {
    $matches = Invoke-RestMethod -Method POST "http://localhost:8000/api/v1/matches/sync" -TimeoutSec 30
    Write-Host "[OK] Partidas ao vivo sincronizadas: $($matches.data.count)" -ForegroundColor Green
} catch {
    Write-Host "[AVISO] Sync partidas: $($_.ErrorDetails.Message)" -ForegroundColor Yellow
}

# 8. Resumo
Write-Host "`n=== Pronto para testar ===" -ForegroundColor Cyan
Write-Host "  Dashboard:     http://localhost:3000"
Write-Host "  Competicoes:   http://localhost:3000/competitions"
Write-Host "  Partidas:      http://localhost:3000/matches"
Write-Host "  API Docs:      http://localhost:8000/docs"
Write-Host ""
