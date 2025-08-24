@echo off
REM ARXOS ArxObject Pipeline Testing - SQLite Version (Windows)
REM This script tests the ArxObject pipeline using SQLite (no PostgreSQL required)

echo 🚀 ARXOS ArxObject Pipeline Testing - SQLite Version
echo ====================================================
echo.
echo This version uses SQLite for testing without requiring PostgreSQL installation.
echo Perfect for company Windows PCs with restricted software installation.
echo.

REM Configuration
set BACKEND_URL=http://localhost:3000

REM Check if backend is running
echo 🔍 Checking Backend Status...
powershell -Command "try { Invoke-RestMethod -Uri '%BACKEND_URL%/api/health' -Method Get | Out-Null; Write-Host '✅ Backend is running on %BACKEND_URL%' } catch { Write-Host '❌ Backend is not running on %BACKEND_URL%' }"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Please start the backend server first:
    echo   cd core\backend
    echo   go run main.go
    echo.
    echo Note: You may need to run 'go mod tidy' first to download SQLite dependencies.
    pause
    exit /b 1
)

echo.

REM Test 1: Basic Health Check
echo 📋 Test 1: Basic Health Check
echo Testing: Health Check
echo Endpoint: %BACKEND_URL%/api/health
powershell -Command "try { $response = Invoke-RestMethod -Uri '%BACKEND_URL%/api/health' -Method Get; Write-Host '✅ HTTP 200 - Health Check'; Write-Host 'Response:' $response | ConvertTo-Json -Depth 3 } catch { Write-Host '❌ Failed - Health Check' }"
echo.

REM Test 2: SQLite Database Connection Test
echo 📋 Test 2: SQLite Database Connection Test
echo Testing: SQLite Database Connection
echo Endpoint: %BACKEND_URL%/api/test/sqlite/db
powershell -Command "try { $response = Invoke-RestMethod -Uri '%BACKEND_URL%/api/test/sqlite/db' -Method Get; Write-Host '✅ HTTP 200 - SQLite Database Connection Test'; Write-Host 'Response:' $response | ConvertTo-Json -Depth 3 } catch { Write-Host '❌ Failed - SQLite Database Connection Test' }"
echo.

REM Test 3: SQLite ArxObject Pipeline Test
echo 📋 Test 3: SQLite ArxObject Pipeline Test
echo Testing: ArxObject Pipeline with SQLite
echo Endpoint: %BACKEND_URL%/api/test/sqlite/arxobject-pipeline
powershell -Command "try { $response = Invoke-RestMethod -Uri '%BACKEND_URL%/api/test/sqlite/arxobject-pipeline' -Method Get; Write-Host '✅ HTTP 200 - SQLite ArxObject Pipeline Test'; Write-Host 'Response:' $response | ConvertTo-Json -Depth 3 } catch { Write-Host '❌ Failed - SQLite ArxObject Pipeline Test' }"
echo.

REM Test 4: SQLite PDF Upload Test (Mock)
echo 📋 Test 4: SQLite PDF Upload Test (Mock)
echo Testing: PDF Upload with SQLite (Mock Data)
echo Endpoint: %BACKEND_URL%/api/test/sqlite/pdf-upload
powershell -Command "try { $response = Invoke-RestMethod -Uri '%BACKEND_URL%/api/test/sqlite/pdf-upload' -Method Post; Write-Host '✅ HTTP 200 - SQLite PDF Upload Test'; Write-Host 'Response:' $response | ConvertTo-Json -Depth 3 } catch { Write-Host '❌ Failed - SQLite PDF Upload Test' }"
echo.

echo.
echo 🎯 Test Summary
echo ===============
echo All SQLite tests completed. Check the results above.
echo.
echo What This Tests:
echo ✅ ArxObject creation and storage with nanometer precision
echo ✅ Coordinate conversion (mm → nm → mm)
echo ✅ System classification mapping
echo ✅ Database operations with SQLite
echo ✅ Mock PDF processing pipeline
echo.
echo Database Location:
echo   ./test_data/arxos_test.db
echo.
echo Next Steps:
echo 1. If all tests pass, your ArxObject pipeline is working correctly
echo 2. The SQLite database file contains your test data
echo 3. You can examine the database file to see stored ArxObjects
echo 4. Ready to move to Phase 2: 3D viewer development
echo.
echo Happy testing! 🚀
pause
