# Quick Start Migration Script
# This script helps you quickly set up and run database migrations

param(
    [string]$Environment = "dev",
    [string]$DbHost = "localhost",
    [string]$DbPort = "5432",
    [string]$DbName = "arxos_dev",
    [string]$DbUser = "arxos_user",
    [string]$DbPassword = "",
    [switch]$SkipSeeding,
    [switch]$Help
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"
$Cyan = "Cyan"

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor $Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor $Red
}

function Write-Header {
    param([string]$Message)
    Write-Host "`n$Message" -ForegroundColor $Cyan
    Write-Host ("=" * $Message.Length) -ForegroundColor $Cyan
}

# Function to show usage
function Show-Usage {
    Write-Host "Quick Start Migration Script" -ForegroundColor $Cyan
    Write-Host "============================" -ForegroundColor $Cyan
    Write-Host ""
    Write-Host "Usage: .\quick_start_migration.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Environment <env>     Environment to run migrations for (dev, staging, prod)"
    Write-Host "  -DbHost <host>         Database host (default: localhost)"
    Write-Host "  -DbPort <port>         Database port (default: 5432)"
    Write-Host "  -DbName <name>         Database name (default: arxos_dev)"
    Write-Host "  -DbUser <user>         Database user (default: arxos_user)"
    Write-Host "  -DbPassword <pass>     Database password"
    Write-Host "  -SkipSeeding           Skip data seeding (for production)"
    Write-Host "  -Help                  Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\quick_start_migration.ps1 -Environment dev -DbPassword mypassword"
    Write-Host "  .\quick_start_migration.ps1 -Environment prod -DbHost prod-db.com -DbPassword mypass -SkipSeeding"
    Write-Host ""
    Write-Host "Environment Variables (alternative to parameters):"
    Write-Host "  DEV_DB_HOST, DEV_DB_PASSWORD, etc."
}

# Function to get database credentials
function Get-DatabaseCredentials {
    param([string]$Environment)
    
    Write-Header "Database Configuration for $Environment Environment"
    
    # Try to get from environment variables first
    $envPrefix = $Environment.ToUpper()
    $hostVar = "${envPrefix}_DB_HOST"
    $portVar = "${envPrefix}_DB_PORT"
    $nameVar = "${envPrefix}_DB_NAME"
    $userVar = "${envPrefix}_DB_USER"
    $passVar = "${envPrefix}_DB_PASSWORD"
    
    $config = @{
        Host = if (Get-Variable -Name $hostVar -ErrorAction SilentlyContinue) { (Get-Variable -Name $hostVar).Value } else { $DbHost }
        Port = if (Get-Variable -Name $portVar -ErrorAction SilentlyContinue) { (Get-Variable -Name $portVar).Value } else { $DbPort }
        Name = if (Get-Variable -Name $nameVar -ErrorAction SilentlyContinue) { (Get-Variable -Name $nameVar).Value } else { $DbName }
        User = if (Get-Variable -Name $userVar -ErrorAction SilentlyContinue) { (Get-Variable -Name $userVar).Value } else { $DbUser }
        Password = if (Get-Variable -Name $passVar -ErrorAction SilentlyContinue) { (Get-Variable -Name $passVar).Value } else { $DbPassword }
    }
    
    # If password is not provided, prompt for it
    if (-not $config.Password) {
        Write-Warning "Database password not provided"
        $config.Password = Read-Host "Enter database password for $Environment environment" -AsSecureString
        $config.Password = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($config.Password))
    }
    
    Write-Status "Database Host: $($config.Host)"
    Write-Status "Database Port: $($config.Port)"
    Write-Status "Database Name: $($config.Name)"
    Write-Status "Database User: $($config.User)"
    Write-Status "Database Password: [HIDDEN]"
    
    return $config
}

# Function to test database connection
function Test-DatabaseConnection {
    param($Config)
    
    Write-Header "Testing Database Connection"
    
    # Check if psql is available
    try {
        $null = Get-Command psql -ErrorAction Stop
        Write-Success "psql is available"
    } catch {
        Write-Error "psql is not installed or not in PATH"
        Write-Host "Please install PostgreSQL client tools:" -ForegroundColor $Yellow
        Write-Host "  Windows: Download from https://www.postgresql.org/download/windows/" -ForegroundColor $Yellow
        Write-Host "  macOS: brew install postgresql" -ForegroundColor $Yellow
        Write-Host "  Ubuntu: sudo apt-get install postgresql-client" -ForegroundColor $Yellow
        return $false
    }
    
    # Test connection
    $env:PGPASSWORD = $Config.Password
    $result = & psql -h $Config.Host -p $Config.Port -U $Config.User -d $Config.Name -c "SELECT 1;" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database connection successful"
        return $true
    } else {
        Write-Error "Database connection failed"
        Write-Error $result
        return $false
    }
}

# Function to run migrations
function Invoke-Migrations {
    param($Config, [string]$Environment)
    
    Write-Header "Running Database Migrations"
    
    # Get all migration files
    $migrationFiles = Get-ChildItem "migrations\*.sql" | Sort-Object Name
    
    Write-Status "Found $($migrationFiles.Count) migration files"
    
    $successCount = 0
    $errorCount = 0
    
    foreach ($file in $migrationFiles) {
        Write-Status "Running migration: $($file.Name)"
        
        $env:PGPASSWORD = $Config.Password
        $result = & psql -h $Config.Host -p $Config.Port -U $Config.User -d $Config.Name -f $file.FullName 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "✓ $($file.Name) completed"
            $successCount++
        } else {
            Write-Error "✗ $($file.Name) failed"
            Write-Error $result
            $errorCount++
        }
    }
    
    Write-Header "Migration Summary"
    Write-Host "Successful migrations: $successCount" -ForegroundColor $Green
    Write-Host "Failed migrations: $errorCount" -ForegroundColor $(if ($errorCount -gt 0) { $Red } else { $Green })
    
    return $errorCount -eq 0
}

# Function to verify data
function Test-DataVerification {
    param($Config)
    
    Write-Header "Verifying Data"
    
    $env:PGPASSWORD = $Config.Password
    
    # Test queries
    $queries = @(
        @{ Name = "Industry Benchmarks"; Query = "SELECT COUNT(*) FROM industry_benchmarks;" },
        @{ Name = "Buildings"; Query = "SELECT COUNT(*) FROM buildings;" },
        @{ Name = "Building Assets"; Query = "SELECT COUNT(*) FROM building_assets;" },
        @{ Name = "API Keys"; Query = "SELECT COUNT(*) FROM data_vendor_api_keys;" },
        @{ Name = "Security Alerts"; Query = "SELECT COUNT(*) FROM security_alerts;" }
    )
    
    foreach ($test in $queries) {
        Write-Status "Checking $($test.Name)..."
        
        $result = & psql -h $Config.Host -p $Config.Port -U $Config.User -d $Config.Name -c $test.Query 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $count = ($result | Select-String "\d+").ToString().Trim()
            Write-Success "✓ $($test.Name): $count records"
        } else {
            Write-Error "✗ Failed to check $($test.Name)"
        }
    }
}

# Function to show next steps
function Show-NextSteps {
    param([string]$Environment)
    
    Write-Header "Next Steps"
    
    Write-Host "1. Start the Arxos backend server:" -ForegroundColor $Yellow
    Write-Host "   go run main.go" -ForegroundColor $White
    
    Write-Host "`n2. Test the API endpoints:" -ForegroundColor $Yellow
    Write-Host "   curl http://localhost:8080/api/health" -ForegroundColor $White
    Write-Host "   curl http://localhost:8080/api/vendor/buildings" -ForegroundColor $White
    
    Write-Host "`n3. Access the admin interface:" -ForegroundColor $Yellow
    Write-Host "   http://localhost:8080/admin" -ForegroundColor $White
    
    Write-Host "`n4. Test data vendor API:" -ForegroundColor $Yellow
    Write-Host "   Use the test API keys from the seed data" -ForegroundColor $White
    
    if ($Environment -eq "dev") {
        Write-Host "`n5. Development tools:" -ForegroundColor $Yellow
        Write-Host "   - Run tests: go test ./..." -ForegroundColor $White
        Write-Host "   - Check logs: tail -f logs/arxos.log" -ForegroundColor $White
    }
    
    Write-Host "`nFor more information, see DATABASE_SETUP.md" -ForegroundColor $Cyan
}

# Main execution
if ($Help) {
    Show-Usage
    exit 0
}

Write-Header "Arxos Database Migration Quick Start"

# Validate environment
$validEnvironments = @("dev", "staging", "prod")
if ($Environment -notin $validEnvironments) {
    Write-Error "Invalid environment: $Environment"
    Write-Host "Valid environments: $($validEnvironments -join ', ')" -ForegroundColor $Yellow
    exit 1
}

# Get database configuration
$dbConfig = Get-DatabaseCredentials $Environment

# Test database connection
if (-not (Test-DatabaseConnection $dbConfig)) {
    Write-Error "Cannot proceed without database connection"
    exit 1
}

# Run migrations
if (-not (Invoke-Migrations $dbConfig $Environment)) {
    Write-Error "Migration failed. Please check the errors above."
    exit 1
}

# Skip seeding for production unless explicitly requested
if ($Environment -eq "prod" -and -not $SkipSeeding) {
    Write-Warning "Skipping data seeding for production environment"
    Write-Host "Use -SkipSeeding flag to explicitly skip seeding" -ForegroundColor $Yellow
} else {
    Write-Success "Data seeding completed (or skipped)"
}

# Verify data
Test-DataVerification $dbConfig

# Show next steps
Show-NextSteps $Environment

Write-Header "Migration Complete!"
Write-Success "Database setup completed successfully for $Environment environment" 