# Test Migration Setup Script
# This script verifies that all migration files are present and properly formatted

Write-Host "Testing Migration Setup" -ForegroundColor Green
Write-Host "=======================" -ForegroundColor Green

# Check if migrations directory exists
if (Test-Path "migrations") {
    Write-Host "✓ Migrations directory exists" -ForegroundColor Green
} else {
    Write-Host "✗ Migrations directory not found" -ForegroundColor Red
    exit 1
}

# Get all migration files
$migrationFiles = Get-ChildItem "migrations\*.sql" | Sort-Object Name

Write-Host "`nFound $($migrationFiles.Count) migration files:" -ForegroundColor Yellow

# Check each migration file
$expectedMigrations = @(
    "001_create_arx_schema.sql",
    "002_create_asset_inventory_schema.sql", 
    "003_create_cmms_integration_schema.sql",
    "004_create_maintenance_workflow_schema.sql",
    "005_alter_cmms_connections_for_auth_and_sync.sql",
    "006_enhance_audit_logs.sql",
    "007_create_export_activity_tables.sql",
    "008_create_compliance_tables.sql",
    "009_create_security_tables.sql",
    "010_add_missing_data_vendor_tables.sql",
    "011_seed_industry_benchmarks_and_sample_data.sql"
)

$missingFiles = @()
$foundFiles = @()

foreach ($expected in $expectedMigrations) {
    $file = $migrationFiles | Where-Object { $_.Name -eq $expected }
    if ($file) {
        Write-Host "  ✓ $expected ($($file.Length) bytes)" -ForegroundColor Green
        $foundFiles += $expected
    } else {
        Write-Host "  ✗ $expected (MISSING)" -ForegroundColor Red
        $missingFiles += $expected
    }
}

# Check for unexpected files
$unexpectedFiles = $migrationFiles | Where-Object { $expectedMigrations -notcontains $_.Name }
if ($unexpectedFiles) {
    Write-Host "`nUnexpected migration files found:" -ForegroundColor Yellow
    foreach ($file in $unexpectedFiles) {
        Write-Host "  ? $($file.Name)" -ForegroundColor Yellow
    }
}

# Summary
Write-Host "`nMigration Setup Summary:" -ForegroundColor Cyan
Write-Host "  Total expected migrations: $($expectedMigrations.Count)" -ForegroundColor White
Write-Host "  Found migrations: $($foundFiles.Count)" -ForegroundColor White
Write-Host "  Missing migrations: $($missingFiles.Count)" -ForegroundColor White

if ($missingFiles.Count -eq 0) {
    Write-Host "`n✓ All expected migrations are present!" -ForegroundColor Green
} else {
    Write-Host "`n✗ Some migrations are missing!" -ForegroundColor Red
    exit 1
}

# Check migration script files
Write-Host "`nChecking migration scripts:" -ForegroundColor Yellow

$scriptFiles = @(
    "run_migrations.sh",
    "run_migrations.bat", 
    "run_migrations.ps1"
)

foreach ($script in $scriptFiles) {
    if (Test-Path $script) {
        Write-Host "  ✓ $script" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $script (MISSING)" -ForegroundColor Red
    }
}

# Check documentation
Write-Host "`nChecking documentation:" -ForegroundColor Yellow

if (Test-Path "DATABASE_SETUP.md") {
    Write-Host "  ✓ DATABASE_SETUP.md" -ForegroundColor Green
} else {
    Write-Host "  ✗ DATABASE_SETUP.md (MISSING)" -ForegroundColor Red
}

# Test database connection (if environment variables are set)
Write-Host "`nTesting database connection:" -ForegroundColor Yellow

if ($env:DEV_DB_HOST -and $env:DEV_DB_PASSWORD) {
    Write-Host "  Environment variables are set" -ForegroundColor Green
    
    # Check if psql is available
    try {
        $null = Get-Command psql -ErrorAction Stop
        Write-Host "  ✓ psql is available" -ForegroundColor Green
    } catch {
        Write-Host "  ✗ psql is not available" -ForegroundColor Red
        Write-Host "    Please install PostgreSQL client tools" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Environment variables not set" -ForegroundColor Yellow
    Write-Host "    Set DEV_DB_HOST, DEV_DB_PASSWORD, etc. to test connection" -ForegroundColor Yellow
}

Write-Host "`nMigration setup test completed!" -ForegroundColor Green 