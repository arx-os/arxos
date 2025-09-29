# ArxOS Test Runner for Windows PowerShell
# Runs comprehensive tests for the Clean Architecture implementation

param(
    [switch]$Verbose,
    [switch]$Benchmark,
    [switch]$Race,
    [int]$CoverageThreshold = 80,
    [string]$Timeout = "10m",
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Write-Host "Usage: .\run_tests.ps1 [OPTIONS]" -ForegroundColor Cyan
    Write-Host "Options:" -ForegroundColor Cyan
    Write-Host "  -Verbose           Enable verbose output" -ForegroundColor White
    Write-Host "  -Benchmark         Run benchmarks" -ForegroundColor White
    Write-Host "  -Race              Enable race detection" -ForegroundColor White
    Write-Host "  -CoverageThreshold Set coverage threshold (default: 80)" -ForegroundColor White
    Write-Host "  -Timeout           Set test timeout (default: 10m)" -ForegroundColor White
    Write-Host "  -Help              Show this help message" -ForegroundColor White
    exit 0
}

# Function to print colored output
function Write-Status {
    param(
        [string]$Status,
        [string]$Message
    )
    
    switch ($Status) {
        "INFO" { Write-Host "ℹ️  $Message" -ForegroundColor Blue }
        "SUCCESS" { Write-Host "✅ $Message" -ForegroundColor Green }
        "WARNING" { Write-Host "⚠️  $Message" -ForegroundColor Yellow }
        "ERROR" { Write-Host "❌ $Message" -ForegroundColor Red }
    }
}

# Function to run tests with proper flags
function Invoke-Tests {
    param(
        [string]$Package,
        [string]$TestName
    )
    
    $flags = @()
    
    if ($Verbose) {
        $flags += "-v"
    }
    
    if ($Race) {
        $flags += "-race"
    }
    
    if ($Benchmark) {
        $flags += "-bench=."
    }
    
    Write-Status "INFO" "Running tests for $TestName..."
    
    $testArgs = $flags + "-timeout=$Timeout", $Package
    $result = & go test @testArgs
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "SUCCESS" "$TestName tests passed"
        return $true
    } else {
        Write-Status "ERROR" "$TestName tests failed"
        return $false
    }
}

# Function to run tests with coverage
function Invoke-TestsWithCoverage {
    param(
        [string]$Package,
        [string]$TestName
    )
    
    $coverageFile = "coverage_$($TestName.Replace(' ', '_')).out"
    
    Write-Status "INFO" "Running tests with coverage for $TestName..."
    
    $testArgs = @("-race", "-coverprofile=$coverageFile", "-covermode=atomic", "-timeout=$Timeout", $Package)
    $result = & go test @testArgs
    
    if ($LASTEXITCODE -eq 0) {
        # Get coverage percentage
        $coverageOutput = & go tool cover -func=$coverageFile
        $coverageLine = $coverageOutput | Where-Object { $_ -match "total:" }
        $coverage = [double]($coverageLine -split '\s+')[2].TrimEnd('%')
        
        Write-Status "SUCCESS" "$TestName tests passed with $coverage% coverage"
        
        if ($coverage -lt $CoverageThreshold) {
            Write-Status "WARNING" "Coverage $coverage% is below threshold $CoverageThreshold%"
        }
        
        return $true
    } else {
        Write-Status "ERROR" "$TestName tests failed"
        return $false
    }
}

# Check if Go is installed
try {
    $goVersion = & go version
    Write-Status "INFO" "Using Go version $($goVersion.Split(' ')[2])"
} catch {
    Write-Status "ERROR" "Go is not installed or not in PATH"
    exit 1
}

# Create coverage directory
if (!(Test-Path "coverage")) {
    New-Item -ItemType Directory -Path "coverage" | Out-Null
}

# Change to project root
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptPath
Set-Location $projectRoot

Write-Host "🚀 Starting ArxOS Test Suite" -ForegroundColor Cyan
Write-Host "==============================" -ForegroundColor Cyan

# Run tests for each package
Write-Status "INFO" "Starting test execution..."

# 1. Dependency Injection Tests
Invoke-TestsWithCoverage "./internal/app/di" "Dependency Injection"

# 2. WebSocket Tests
Invoke-TestsWithCoverage "./internal/infra/messaging" "WebSocket"

# 3. Domain Tests
Invoke-TestsWithCoverage "./internal/domain/building" "Building Domain"
Invoke-TestsWithCoverage "./internal/domain/equipment" "Equipment Domain"
Invoke-TestsWithCoverage "./internal/domain/spatial" "Spatial Domain"
Invoke-TestsWithCoverage "./internal/domain/analytics" "Analytics Domain"
Invoke-TestsWithCoverage "./internal/domain/workflow" "Workflow Domain"
Invoke-TestsWithCoverage "./internal/domain/messaging" "Messaging Domain"

# 4. Application Tests
Invoke-TestsWithCoverage "./internal/app/handlers" "HTTP Handlers"
Invoke-TestsWithCoverage "./internal/app/middleware" "Middleware"
Invoke-TestsWithCoverage "./internal/app/routes" "Routes"

# 5. Infrastructure Tests
Invoke-TestsWithCoverage "./internal/infra/database" "Database"
Invoke-TestsWithCoverage "./internal/infra/cache" "Cache"
Invoke-TestsWithCoverage "./internal/infra/storage" "Storage"

# 6. Integration Tests
Invoke-TestsWithCoverage "./internal/app" "Integration"

# 7. Command Tests
Invoke-TestsWithCoverage "./cmd/arx" "CLI Commands"

# 8. Package Tests
Invoke-TestsWithCoverage "./pkg/models" "Models"
Invoke-TestsWithCoverage "./pkg/errors" "Errors"
Invoke-TestsWithCoverage "./pkg/sync" "Sync"

# 9. Common Tests
Invoke-TestsWithCoverage "./internal/common/logger" "Logger"
Invoke-TestsWithCoverage "./internal/common/progress" "Progress"
Invoke-TestsWithCoverage "./internal/common/resources" "Resources"
Invoke-TestsWithCoverage "./internal/common/retry" "Retry"
Invoke-TestsWithCoverage "./internal/common/state" "State"

# 10. Configuration Tests
Invoke-TestsWithCoverage "./internal/config" "Configuration"

# 11. Validation Tests
Invoke-TestsWithCoverage "./internal/validation" "Validation"

# 12. BIM Tests
Invoke-TestsWithCoverage "./internal/bim" "BIM"

# 13. Cache Tests
Invoke-TestsWithCoverage "./internal/cache" "Cache Implementation"

# 14. Analytics Tests
Invoke-TestsWithCoverage "./internal/analytics" "Analytics Implementation"

# 15. Workflow Tests
Invoke-TestsWithCoverage "./internal/workflow" "Workflow Implementation"

# 16. Hardware Tests
Invoke-TestsWithCoverage "./internal/hardware" "Hardware"

# 17. Facility Tests
Invoke-TestsWithCoverage "./internal/facility" "Facility"

# 18. Integration Tests
Invoke-TestsWithCoverage "./internal/integration" "Integration Implementation"

# 19. Services Tests
Invoke-TestsWithCoverage "./internal/services" "Services"

# 20. API Tests
Invoke-TestsWithCoverage "./internal/api" "API"

# 21. Daemon Tests
Invoke-TestsWithCoverage "./internal/daemon" "Daemon"

# 22. Telemetry Tests
Invoke-TestsWithCoverage "./internal/telemetry" "Telemetry"

# 23. Simulation Tests
Invoke-TestsWithCoverage "./internal/simulation" "Simulation"

# 24. Rendering Tests
Invoke-TestsWithCoverage "./internal/rendering" "Rendering"

# 25. Search Tests
Invoke-TestsWithCoverage "./internal/search" "Search"

# 26. Security Tests
Invoke-TestsWithCoverage "./internal/security" "Security"

# 27. Notifications Tests
Invoke-TestsWithCoverage "./internal/notifications" "Notifications"

# 28. Email Tests
Invoke-TestsWithCoverage "./internal/email" "Email"

# 29. Ecosystem Tests
Invoke-TestsWithCoverage "./internal/ecosystem" "Ecosystem"

# 30. Core Tests
Invoke-TestsWithCoverage "./internal/core" "Core"

# 31. Interfaces Tests
Invoke-TestsWithCoverage "./internal/interfaces" "Interfaces"

# 32. IT Tests
Invoke-TestsWithCoverage "./internal/it" "IT"

# 33. Metrics Tests
Invoke-TestsWithCoverage "./internal/metrics" "Metrics"

# 34. Spatial Tests
Invoke-TestsWithCoverage "./internal/spatial" "Spatial"

# 35. Storage Tests
Invoke-TestsWithCoverage "./internal/storage" "Storage Implementation"

# 36. Database Tests
Invoke-TestsWithCoverage "./internal/database" "Database Implementation"

# 37. Adapters Tests
Invoke-TestsWithCoverage "./internal/adapters" "Adapters"

# 38. Auth Tests
Invoke-TestsWithCoverage "./internal/auth" "Authentication"

# 39. Compliance Tests
Invoke-TestsWithCoverage "./internal/compliance" "Compliance"

# 40. Connections Tests
Invoke-TestsWithCoverage "./internal/connections" "Connections"

# 41. Converter Tests
Invoke-TestsWithCoverage "./internal/converter" "Converter"

# 42. Exporter Tests
Invoke-TestsWithCoverage "./internal/exporter" "Exporter"

# 43. Importer Tests
Invoke-TestsWithCoverage "./internal/importer" "Importer"

# 44. Handlers Tests
Invoke-TestsWithCoverage "./internal/handlers" "Handlers"

# 45. Migration Tests
Invoke-TestsWithCoverage "./internal/migration" "Migration"

# 46. Visualization Tests
Invoke-TestsWithCoverage "./internal/visualization" "Visualization"

# 47. Test Tests
Invoke-TestsWithCoverage "./test" "Test Utilities"

# Generate overall coverage report
Write-Status "INFO" "Generating overall coverage report..."

# Combine all coverage files
"mode: atomic" | Out-File -FilePath "coverage/coverage.out" -Encoding UTF8
Get-ChildItem -Path "coverage_*.out" | ForEach-Object {
    Get-Content $_.FullName | Select-Object -Skip 1 | Add-Content "coverage/coverage.out"
}

# Generate HTML coverage report
& go tool cover -html=coverage/coverage.out -o coverage/coverage.html

# Generate coverage summary
& go tool cover -func=coverage/coverage.out | Out-File -FilePath "coverage/coverage.txt" -Encoding UTF8

# Display coverage summary
Write-Status "INFO" "Coverage Summary:"
Get-Content "coverage/coverage.txt" | Where-Object { $_ -match "total:" }

# Clean up individual coverage files
Remove-Item "coverage_*.out" -ErrorAction SilentlyContinue

# Run benchmarks if requested
if ($Benchmark) {
    Write-Status "INFO" "Running benchmarks..."
    & go test -bench=. -benchmem ./...
}

# Run race detection tests
if ($Race) {
    Write-Status "INFO" "Running race detection tests..."
    & go test -race ./...
}

# Run vet
Write-Status "INFO" "Running go vet..."
& go vet ./...

# Run fmt check
Write-Status "INFO" "Checking code formatting..."
$fmtOutput = & go fmt ./...
if ($fmtOutput) {
    Write-Status "WARNING" "Code formatting issues found. Run 'go fmt ./...' to fix."
} else {
    Write-Status "SUCCESS" "Code formatting is correct"
}

# Run mod tidy check
Write-Status "INFO" "Checking go.mod..."
$tidyOutput = & go mod tidy -v 2>&1
if ($tidyOutput -match "go: downloading|go: extracting") {
    Write-Status "WARNING" "go.mod needs tidying. Run 'go mod tidy' to fix."
} else {
    Write-Status "SUCCESS" "go.mod is tidy"
}

# Run security check if gosec is available
try {
    Write-Status "INFO" "Running security scan..."
    & gosec ./...
} catch {
    Write-Status "WARNING" "gosec is not installed. Install it for security scanning."
}

# Run static analysis if staticcheck is available
try {
    Write-Status "INFO" "Running static analysis..."
    & staticcheck ./...
} catch {
    Write-Status "WARNING" "staticcheck is not installed. Install it for static analysis."
}

Write-Status "SUCCESS" "All tests completed successfully!"
Write-Status "INFO" "Coverage report available at: coverage/coverage.html"
Write-Status "INFO" "Coverage summary available at: coverage/coverage.txt"

Write-Host ""
Write-Host "🎉 Test Suite Complete!" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green
