@echo off
REM Database Migration and Seeding Script for Windows
REM This script runs all migrations and seeds data for all environments

setlocal enabledelayedexpansion

REM Colors for output (Windows doesn't support ANSI colors in batch, but we can use echo)
set "RED=[ERROR]"
set "GREEN=[SUCCESS]"
set "YELLOW=[WARNING]"
set "BLUE=[INFO]"

REM Function to print colored output
:print_status
echo %BLUE% %~1
goto :eof

:print_success
echo %GREEN% %~1
goto :eof

:print_warning
echo %YELLOW% %~1
goto :eof

:print_error
echo %RED% %~1
goto :eof

REM Function to run migration for a specific environment
:run_migrations_for_env
set env=%~1
set db_host=%~2
set db_port=%~3
set db_name=%~4
set db_user=%~5
set db_password=%~6

call :print_status "Running migrations for environment: %env%"

REM Create migrations directory if it doesn't exist
if not exist "migrations" mkdir migrations

REM Run each migration file in order
for %%f in (migrations\*.sql) do (
    if exist "%%f" (
        call :print_status "Running migration: %%~nxf"
        
        REM Use psql to run the migration
        set PGPASSWORD=%db_password%
        psql -h %db_host% -p %db_port% -U %db_user% -d %db_name% -f "%%f"
        
        if !errorlevel! equ 0 (
            call :print_success "Migration %%~nxf completed successfully"
        ) else (
            call :print_error "Migration %%~nxf failed"
            exit /b 1
        )
    )
)

call :print_success "All migrations completed for environment: %env%"
goto :eof

REM Function to seed data for a specific environment
:seed_data_for_env
set env=%~1
set db_host=%~2
set db_port=%~3
set db_name=%~4
set db_user=%~5
set db_password=%~6

call :print_status "Seeding data for environment: %env%"

REM Run the seed migration
if exist "migrations\011_seed_industry_benchmarks_and_sample_data.sql" (
    call :print_status "Running seed data migration"
    
    set PGPASSWORD=%db_password%
    psql -h %db_host% -p %db_port% -U %db_user% -d %db_name% -f "migrations\011_seed_industry_benchmarks_and_sample_data.sql"
    
    if !errorlevel! equ 0 (
        call :print_success "Seed data migration completed successfully"
    ) else (
        call :print_error "Seed data migration failed"
        exit /b 1
    )
) else (
    call :print_warning "Seed data migration file not found"
)

call :print_success "Data seeding completed for environment: %env%"
goto :eof

REM Function to verify database connection
:verify_db_connection
set db_host=%~1
set db_port=%~2
set db_name=%~3
set db_user=%~4
set db_password=%~5

call :print_status "Verifying database connection..."

set PGPASSWORD=%db_password%
psql -h %db_host% -p %db_port% -U %db_user% -d %db_name% -c "SELECT 1;" >nul 2>&1

if !errorlevel! equ 0 (
    call :print_success "Database connection verified"
    exit /b 0
) else (
    call :print_error "Database connection failed"
    exit /b 1
)

REM Function to check if migrations table exists
:check_migrations_table
set db_host=%~1
set db_port=%~2
set db_name=%~3
set db_user=%~4
set db_password=%~5

call :print_status "Checking if migrations tracking table exists..."

set PGPASSWORD=%db_password%
psql -h %db_host% -p %db_port% -U %db_user% -d %db_name% -c "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'migrations');" | findstr "t" >nul

if !errorlevel! equ 0 (
    call :print_success "Migrations table exists"
    exit /b 0
) else (
    call :print_warning "Migrations table does not exist, creating it..."
    
    set PGPASSWORD=%db_password%
    psql -h %db_host% -p %db_port% -U %db_user% -d %db_name% -c "CREATE TABLE IF NOT EXISTS migrations (id SERIAL PRIMARY KEY, filename VARCHAR(255) NOT NULL UNIQUE, executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, checksum VARCHAR(64), execution_time_ms INTEGER);"
    
    if !errorlevel! equ 0 (
        call :print_success "Migrations table created"
        exit /b 0
    ) else (
        call :print_error "Failed to create migrations table"
        exit /b 1
    )
)

REM Main execution
:main
call :print_status "Starting database migration and seeding process"

REM Environment configurations
REM Development
set DEV_HOST=%DEV_DB_HOST%
if "%DEV_HOST%"=="" set DEV_HOST=localhost
set DEV_PORT=%DEV_DB_PORT%
if "%DEV_PORT%"=="" set DEV_PORT=5432
set DEV_NAME=%DEV_DB_NAME%
if "%DEV_NAME%"=="" set DEV_NAME=arxos_dev
set DEV_USER=%DEV_DB_USER%
if "%DEV_USER%"=="" set DEV_USER=arxos_user
set DEV_PASSWORD=%DEV_DB_PASSWORD%
if "%DEV_PASSWORD%"=="" set DEV_PASSWORD=arxos_password

REM Staging
set STAGING_HOST=%STAGING_DB_HOST%
if "%STAGING_HOST%"=="" set STAGING_HOST=staging-db.example.com
set STAGING_PORT=%STAGING_DB_PORT%
if "%STAGING_PORT%"=="" set STAGING_PORT=5432
set STAGING_NAME=%STAGING_DB_NAME%
if "%STAGING_NAME%"=="" set STAGING_NAME=arxos_staging
set STAGING_USER=%STAGING_DB_USER%
if "%STAGING_USER%"=="" set STAGING_USER=arxos_user
set STAGING_PASSWORD=%STAGING_DB_PASSWORD%
if "%STAGING_PASSWORD%"=="" set STAGING_PASSWORD=arxos_password

REM Production
set PROD_HOST=%PROD_DB_HOST%
if "%PROD_HOST%"=="" set PROD_HOST=prod-db.example.com
set PROD_PORT=%PROD_DB_PORT%
if "%PROD_PORT%"=="" set PROD_PORT=5432
set PROD_NAME=%PROD_DB_NAME%
if "%PROD_NAME%"=="" set PROD_NAME=arxos_prod
set PROD_USER=%PROD_DB_USER%
if "%PROD_USER%"=="" set PROD_USER=arxos_user
set PROD_PASSWORD=%PROD_DB_PASSWORD%
if "%PROD_PASSWORD%"=="" set PROD_PASSWORD=arxos_password

REM Check command line arguments
if "%1"=="dev" (
    set ENVIRONMENTS=dev
) else if "%1"=="staging" (
    set ENVIRONMENTS=staging
) else if "%1"=="prod" (
    set ENVIRONMENTS=prod
) else if "%1"=="all" (
    set ENVIRONMENTS=dev staging prod
) else if "%1"=="" (
    set ENVIRONMENTS=dev staging prod
) else (
    call :print_error "Invalid environment. Use: dev, staging, prod, or all"
    exit /b 1
)

REM Process each environment
for %%e in (%ENVIRONMENTS%) do (
    call :print_status "Processing environment: %%e"
    
    REM Set environment-specific variables
    if "%%e"=="dev" (
        set DB_HOST=%DEV_HOST%
        set DB_PORT=%DEV_PORT%
        set DB_NAME=%DEV_NAME%
        set DB_USER=%DEV_USER%
        set DB_PASSWORD=%DEV_PASSWORD%
    ) else if "%%e"=="staging" (
        set DB_HOST=%STAGING_HOST%
        set DB_PORT=%STAGING_PORT%
        set DB_NAME=%STAGING_NAME%
        set DB_USER=%STAGING_USER%
        set DB_PASSWORD=%STAGING_PASSWORD%
    ) else if "%%e"=="prod" (
        set DB_HOST=%PROD_HOST%
        set DB_PORT=%PROD_PORT%
        set DB_NAME=%PROD_NAME%
        set DB_USER=%PROD_USER%
        set DB_PASSWORD=%PROD_PASSWORD%
    )
    
    REM Verify database connection
    call :verify_db_connection %DB_HOST% %DB_PORT% %DB_NAME% %DB_USER% %DB_PASSWORD%
    if !errorlevel! neq 0 (
        call :print_error "Cannot connect to %%e database. Skipping..."
        goto :continue
    )
    
    REM Check/create migrations table
    call :check_migrations_table %DB_HOST% %DB_PORT% %DB_NAME% %DB_USER% %DB_PASSWORD%
    if !errorlevel! neq 0 (
        call :print_error "Failed to setup migrations tracking for %%e. Skipping..."
        goto :continue
    )
    
    REM Run migrations
    call :run_migrations_for_env %%e %DB_HOST% %DB_PORT% %DB_NAME% %DB_USER% %DB_PASSWORD%
    
    REM Seed data (only for dev and staging)
    if not "%%e"=="prod" (
        call :seed_data_for_env %%e %DB_HOST% %DB_PORT% %DB_NAME% %DB_USER% %DB_PASSWORD%
    ) else (
        call :print_warning "Skipping data seeding for production environment"
    )
    
    call :print_success "Environment %%e completed successfully"
    echo.
    
    :continue
)

call :print_success "All environments processed successfully!"
goto :eof

REM Check if required tools are available
:check_requirements
call :print_status "Checking requirements..."

where psql >nul 2>&1
if !errorlevel! neq 0 (
    call :print_error "psql is not installed or not in PATH. Please install PostgreSQL client."
    exit /b 1
)

call :print_success "Requirements check passed"
goto :eof

REM Show usage
:show_usage
echo Usage: %~nx0 [dev^|staging^|prod^|all]
echo.
echo Environments:
echo   dev      - Run migrations and seed data for development
echo   staging  - Run migrations and seed data for staging
echo   prod     - Run migrations only for production (no seeding)
echo   all      - Run migrations and seed data for all environments
echo.
echo Environment Variables:
echo   DEV_DB_HOST, DEV_DB_PORT, DEV_DB_NAME, DEV_DB_USER, DEV_DB_PASSWORD
echo   STAGING_DB_HOST, STAGING_DB_PORT, STAGING_DB_NAME, STAGING_DB_USER, STAGING_DB_PASSWORD
echo   PROD_DB_HOST, PROD_DB_PORT, PROD_DB_NAME, PROD_DB_USER, PROD_DB_PASSWORD
echo.
echo Example:
echo   set DEV_DB_PASSWORD=mypassword
echo   %~nx0 dev
goto :eof

REM Check for help flag
if "%1"=="-h" (
    call :show_usage
    exit /b 0
)
if "%1"=="--help" (
    call :show_usage
    exit /b 0
)

REM Check requirements and run main function
call :check_requirements
call :main %* 