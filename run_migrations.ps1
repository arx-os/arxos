# Database Migration and Seeding Script for PowerShell
# This script runs all migrations and seeds data for all environments

param(
    [Parameter(Position=0)]
    [ValidateSet("dev", "staging", "prod", "all")]
    [string]$Environment = "all",
    
    [switch]$Help
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

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

# Function to run migration for a specific environment
function Invoke-MigrationsForEnvironment {
    param(
        [string]$Environment,
        [string]$DbHost,
        [string]$DbPort,
        [string]$DbName,
        [string]$DbUser,
        [string]$DbPassword
    )
    
    Write-Status "Running migrations for environment: $Environment"
    
    # Create migrations directory if it doesn't exist
    if (!(Test-Path "migrations")) {
        New-Item -ItemType Directory -Path "migrations" | Out-Null
    }
    
    # Get all migration files and sort them
    $migrationFiles = Get-ChildItem "migrations\*.sql" | Sort-Object Name
    
    foreach ($file in $migrationFiles) {
        Write-Status "Running migration: $($file.Name)"
        
        # Set environment variable for psql
        $env:PGPASSWORD = $DbPassword
        
        # Run the migration
        $result = & psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -f $file.FullName 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Migration $($file.Name) completed successfully"
        } else {
            Write-Error "Migration $($file.Name) failed"
            Write-Error $result
            exit 1
        }
    }
    
    Write-Success "All migrations completed for environment: $Environment"
}

# Function to seed data for a specific environment
function Invoke-SeedDataForEnvironment {
    param(
        [string]$Environment,
        [string]$DbHost,
        [string]$DbPort,
        [string]$DbName,
        [string]$DbUser,
        [string]$DbPassword
    )
    
    Write-Status "Seeding data for environment: $Environment"
    
    $seedFile = "migrations\011_seed_industry_benchmarks_and_sample_data.sql"
    
    if (Test-Path $seedFile) {
        Write-Status "Running seed data migration"
        
        # Set environment variable for psql
        $env:PGPASSWORD = $DbPassword
        
        # Run the seed migration
        $result = & psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -f $seedFile 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Seed data migration completed successfully"
        } else {
            Write-Error "Seed data migration failed"
            Write-Error $result
            exit 1
        }
    } else {
        Write-Warning "Seed data migration file not found"
    }
    
    Write-Success "Data seeding completed for environment: $Environment"
}

# Function to verify database connection
function Test-DatabaseConnection {
    param(
        [string]$DbHost,
        [string]$DbPort,
        [string]$DbName,
        [string]$DbUser,
        [string]$DbPassword
    )
    
    Write-Status "Verifying database connection..."
    
    # Set environment variable for psql
    $env:PGPASSWORD = $DbPassword
    
    # Test connection
    $result = & psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -c "SELECT 1;" 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "Database connection verified"
        return $true
    } else {
        Write-Error "Database connection failed"
        Write-Error $result
        return $false
    }
}

# Function to check if migrations table exists
function Test-MigrationsTable {
    param(
        [string]$DbHost,
        [string]$DbPort,
        [string]$DbName,
        [string]$DbUser,
        [string]$DbPassword
    )
    
    Write-Status "Checking if migrations tracking table exists..."
    
    # Set environment variable for psql
    $env:PGPASSWORD = $DbPassword
    
    # Check if migrations table exists
    $result = & psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'migrations');" 2>&1
    
    if ($LASTEXITCODE -eq 0 -and $result -match "t") {
        Write-Success "Migrations table exists"
        return $true
    } else {
        Write-Warning "Migrations table does not exist, creating it..."
        
        # Create migrations table
        $createResult = & psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -c "CREATE TABLE IF NOT EXISTS migrations (id SERIAL PRIMARY KEY, filename VARCHAR(255) NOT NULL UNIQUE, executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, checksum VARCHAR(64), execution_time_ms INTEGER);" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Migrations table created"
            return $true
        } else {
            Write-Error "Failed to create migrations table"
            Write-Error $createResult
            return $false
        }
    }
}

# Function to show usage
function Show-Usage {
    Write-Host "Usage: .\run_migrations.ps1 [dev|staging|prod|all] [-Help]"
    Write-Host ""
    Write-Host "Environments:"
    Write-Host "  dev      - Run migrations and seed data for development"
    Write-Host "  staging  - Run migrations and seed data for staging"
    Write-Host "  prod     - Run migrations only for production (no seeding)"
    Write-Host "  all      - Run migrations and seed data for all environments"
    Write-Host ""
    Write-Host "Environment Variables:"
    Write-Host "  DEV_DB_HOST, DEV_DB_PORT, DEV_DB_NAME, DEV_DB_USER, DEV_DB_PASSWORD"
    Write-Host "  STAGING_DB_HOST, STAGING_DB_PORT, STAGING_DB_NAME, STAGING_DB_USER, STAGING_DB_PASSWORD"
    Write-Host "  PROD_DB_HOST, PROD_DB_PORT, PROD_DB_NAME, PROD_DB_USER, PROD_DB_PASSWORD"
    Write-Host ""
    Write-Host "Example:"
    Write-Host "  `$env:DEV_DB_PASSWORD='mypassword'; .\run_migrations.ps1 dev"
}

# Function to check requirements
function Test-Requirements {
    Write-Status "Checking requirements..."
    
    # Check if psql is available
    try {
        $null = Get-Command psql -ErrorAction Stop
        Write-Success "psql is available"
    } catch {
        Write-Error "psql is not installed or not in PATH. Please install PostgreSQL client."
        exit 1
    }
    
    Write-Success "Requirements check passed"
}

# Main execution function
function Invoke-Main {
    param([string]$Environment)
    
    Write-Status "Starting database migration and seeding process"
    
    # Environment configurations
    # Development
    $DevHost = if ($env:DEV_DB_HOST) { $env:DEV_DB_HOST } else { "localhost" }
    $DevPort = if ($env:DEV_DB_PORT) { $env:DEV_DB_PORT } else { "5432" }
    $DevName = if ($env:DEV_DB_NAME) { $env:DEV_DB_NAME } else { "arxos_dev" }
    $DevUser = if ($env:DEV_DB_USER) { $env:DEV_DB_USER } else { "arxos_user" }
    $DevPassword = if ($env:DEV_DB_PASSWORD) { $env:DEV_DB_PASSWORD } else { "arxos_password" }
    
    # Staging
    $StagingHost = if ($env:STAGING_DB_HOST) { $env:STAGING_DB_HOST } else { "staging-db.example.com" }
    $StagingPort = if ($env:STAGING_DB_PORT) { $env:STAGING_DB_PORT } else { "5432" }
    $StagingName = if ($env:STAGING_DB_NAME) { $env:STAGING_DB_NAME } else { "arxos_staging" }
    $StagingUser = if ($env:STAGING_DB_USER) { $env:STAGING_DB_USER } else { "arxos_user" }
    $StagingPassword = if ($env:STAGING_DB_PASSWORD) { $env:STAGING_DB_PASSWORD } else { "arxos_password" }
    
    # Production
    $ProdHost = if ($env:PROD_DB_HOST) { $env:PROD_DB_HOST } else { "prod-db.example.com" }
    $ProdPort = if ($env:PROD_DB_PORT) { $env:PROD_DB_PORT } else { "5432" }
    $ProdName = if ($env:PROD_DB_NAME) { $env:PROD_DB_NAME } else { "arxos_prod" }
    $ProdUser = if ($env:PROD_DB_USER) { $env:PROD_DB_USER } else { "arxos_user" }
    $ProdPassword = if ($env:PROD_DB_PASSWORD) { $env:PROD_DB_PASSWORD } else { "arxos_password" }
    
    # Determine which environments to process
    $environments = @()
    switch ($Environment) {
        "dev" { $environments = @("dev") }
        "staging" { $environments = @("staging") }
        "prod" { $environments = @("prod") }
        "all" { $environments = @("dev", "staging", "prod") }
    }
    
    # Process each environment
    foreach ($env in $environments) {
        Write-Status "Processing environment: $env"
        
        # Set environment-specific variables
        switch ($env) {
            "dev" {
                $DbHost = $DevHost
                $DbPort = $DevPort
                $DbName = $DevName
                $DbUser = $DevUser
                $DbPassword = $DevPassword
            }
            "staging" {
                $DbHost = $StagingHost
                $DbPort = $StagingPort
                $DbName = $StagingName
                $DbUser = $StagingUser
                $DbPassword = $StagingPassword
            }
            "prod" {
                $DbHost = $ProdHost
                $DbPort = $ProdPort
                $DbName = $ProdName
                $DbUser = $ProdUser
                $DbPassword = $ProdPassword
            }
        }
        
        # Verify database connection
        if (!(Test-DatabaseConnection $DbHost $DbPort $DbName $DbUser $DbPassword)) {
            Write-Error "Cannot connect to $env database. Skipping..."
            continue
        }
        
        # Check/create migrations table
        if (!(Test-MigrationsTable $DbHost $DbPort $DbName $DbUser $DbPassword)) {
            Write-Error "Failed to setup migrations tracking for $env. Skipping..."
            continue
        }
        
        # Run migrations
        Invoke-MigrationsForEnvironment $env $DbHost $DbPort $DbName $DbUser $DbPassword
        
        # Seed data (only for dev and staging)
        if ($env -ne "prod") {
            Invoke-SeedDataForEnvironment $env $DbHost $DbPort $DbName $DbUser $DbPassword
        } else {
            Write-Warning "Skipping data seeding for production environment"
        }
        
        Write-Success "Environment $env completed successfully"
        Write-Host ""
    }
    
    Write-Success "All environments processed successfully!"
}

# Show help if requested
if ($Help) {
    Show-Usage
    exit 0
}

# Check requirements and run main function
Test-Requirements
Invoke-Main $Environment 