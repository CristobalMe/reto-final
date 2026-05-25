# PowerShell script to load talos_tecmty database
# Works on Windows with Docker Desktop

param(
    [string]$Container = "talos-tecmty-mysql",
    [string]$User = "root",
    [string]$Password = "root",
    [string]$Database = "talos_tecmty",
    [string]$SeedPath = ".\data\talos_tecmty"
)

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Loading talos_tecmty Database" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if container is running
Write-Host "[1/4] Checking if container is running..." -ForegroundColor Yellow
$containerStatus = docker ps -q -f name=$Container
if (-not $containerStatus) {
    Write-Host "ERROR: Container '$Container' is not running!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Container is running" -ForegroundColor Green
Write-Host ""

# Create database
Write-Host "[2/4] Creating database..." -ForegroundColor Yellow
$createDb = @"
CREATE DATABASE IF NOT EXISTS ``$Database`` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
"@

docker exec $Container sh -c "mysql -u$User -p$Password -e '$createDb'" 2>&1 | Where-Object { $_ -notmatch "Warning" }
Write-Host "✓ Database created" -ForegroundColor Green
Write-Host ""

# Load structure
Write-Host "[3/4] Loading schema..." -ForegroundColor Yellow
docker exec $Container sh -c "cat /seed/talos_tecmty\ _structure.sql | mysql -u$User -p$Password $Database" 2>&1 | Where-Object { $_ -notmatch "Warning" }
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Schema loaded" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to load schema" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Load data (this will take several minutes)
Write-Host "[4/4] Loading data (this may take 5-15 minutes)..." -ForegroundColor Yellow
Write-Host "      Progress: watch with: docker logs $Container --follow" -ForegroundColor Gray
docker exec $Container sh -c "cat /seed/talos_tecmty_data.sql | mysql -u$User -p$Password $Database" 2>&1 | Where-Object { $_ -notmatch "Warning" }
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Data loaded" -ForegroundColor Green
} else {
    Write-Host "ERROR: Failed to load data" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Validate
Write-Host "[5/5] Validating..." -ForegroundColor Yellow
$validation = @"
SELECT COUNT(*) as unidadmedida FROM unidadmedida;
SELECT COUNT(*) as categoria FROM categoria;
SELECT COUNT(*) as almacen FROM almacen;
SELECT COUNT(*) as producto FROM producto;
SELECT COUNT(*) as productotalos FROM productotalos;
SELECT COUNT(*) as inventariomes FROM inventariomes;
SELECT COUNT(*) as inventariomesdetalle FROM inventariomesdetalle;
"@

docker exec $Container sh -c "mysql -u$User -p$Password $Database -e '$validation'" 2>&1 | Where-Object { $_ -notmatch "Warning" }
Write-Host "✓ Validation complete" -ForegroundColor Green
Write-Host ""

Write-Host "================================" -ForegroundColor Green
Write-Host "Database load complete!" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green
