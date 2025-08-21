# ARXOS ArxObject Pipeline Testing Guide

## 🎯 **Overview**

This guide walks you through testing the complete ArxObject creation and storage pipeline. We'll validate each component systematically to ensure everything works correctly before moving to the next development phase.

## 🚀 **Quick Start**

### **Option 1: SQLite Testing (Recommended for Company PCs)**
**No PostgreSQL installation required! Perfect for restricted Windows environments.**

```cmd
# Navigate to backend directory
cd core\backend

# Download dependencies (including SQLite driver)
go mod tidy

# Start the server
go run main.go

# In another Command Prompt/PowerShell, run the SQLite test script
test_sqlite_windows.bat
```

### **Option 2: PostgreSQL Testing (Full Production Setup)**
**Requires PostgreSQL installation - use if you have admin access.**

```cmd
# Navigate to backend directory
cd core\backend

# Start the server
go run main.go

# In another Command Prompt/PowerShell, run the PostgreSQL test script
test_arxobject_pipeline.bat
```

### **macOS/Linux Users**
```bash
# Navigate to backend directory
cd core/backend

# Start the server
go run main.go

# Make the script executable and run
chmod +x test_arxobject_pipeline.sh
./test_arxobject_pipeline.sh
```

The server will start on `http://localhost:8080`

### **2. Run the Test Script**
```bash
# Make the script executable
chmod +x test_arxobject_pipeline.sh

# Run the comprehensive test suite
./test_arxobject_pipeline.sh
```

## 📋 **Manual Testing Steps**

If you prefer to test manually or want to understand each step:

### **Step 1: Health Check**
```bash
curl http://localhost:8080/api/health
```
**Expected**: HTTP 200 with basic health information

### **Step 2: Database Connection Test**
```bash
curl http://localhost:8080/api/test/db
```
**Expected**: HTTP 200 with database status and table information

### **Step 3: ArxObject Pipeline Test**
```bash
curl http://localhost:8080/api/test/arxobject-pipeline
```
**Expected**: HTTP 200 with comprehensive test results including:
- Table existence verification
- ArxObject creation and storage
- Data integrity validation
- Cleanup confirmation

### **Step 4: AI Service Integration Test (Mock)**
```bash
curl http://localhost:8080/api/test/ai-integration
```
**Expected**: HTTP 200 with mock AI service response processing

## 🔍 **What Each Test Validates**

### **Database Connection Test (`/api/test/db`)**
- ✅ PostgreSQL connection established
- ✅ Required tables exist (`arx_objects`, `pdf_buildings`)
- ✅ Basic database queries work
- ✅ Schema is properly set up

### **ArxObject Pipeline Test (`/api/test/arxobject-pipeline`)**
- ✅ Building creation works
- ✅ ArxObject creation from structured data
- ✅ Database storage with nanometer precision
- ✅ Coordinate conversion (mm → nm → mm)
- ✅ System classification mapping
- ✅ Data retrieval and verification
- ✅ Cleanup operations

### **AI Service Integration Test (`/api/test/ai-integration`)**
- ✅ Mock AI response processing
- ✅ ArxObject creation from AI data format
- ✅ Coordinate extraction and conversion
- ✅ System classification from object types
- ✅ Confidence score handling
- ✅ Database storage of processed objects

## 📊 **Expected Test Results**

### **Successful Test Response Example**
```json
{
  "success": true,
  "message": "ArxObject pipeline test completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "tests": {
    "database_schema": {
      "pdf_buildings": {
        "exists": true,
        "count": 0
      },
      "arx_objects": {
        "exists": true,
        "count": 0
      }
    },
    "pipeline_tests": {
      "building_creation": {
        "success": true,
        "building_id": "test_building_1705312200"
      },
      "arxobject_storage": {
        "success": true,
        "arxobject_id": "test_arx_1705312200123456789"
      },
      "data_verification": {
        "success": true,
        "coordinates": {
          "x_nano": 1000000000,
          "y_nano": 2000000000,
          "x_meters": 1.0,
          "y_meters": 2.0
        }
      }
    }
  },
  "summary": {
    "tables_exist": true,
    "pipeline_working": true,
    "data_integrity": true
  }
}
```

## ⚠️ **Common Issues and Solutions**

### **Issue: Database Connection Failed**
**Symptoms**: HTTP 500 error with "Database connection failed"
**Solutions**:
1. Check if PostgreSQL is running
2. Verify `DATABASE_URL` environment variable
3. Ensure database `arxos` exists
4. Check user permissions

### **Issue: Tables Don't Exist**
**Symptoms**: Tables show `"exists": false`
**Solutions**:
1. Run database migrations: `db.Migrate()`
2. Check if migration file exists
3. Verify database user has CREATE permissions

### **Issue: ArxObject Storage Failed**
**Symptoms**: Storage test shows `"success": false`
**Solutions**:
1. Check database schema matches expected structure
2. Verify all required fields are present
3. Check for constraint violations

## 🎯 **Success Criteria**

Your ArxObject pipeline is working correctly when:

1. ✅ **Database Connection**: All database tests pass
2. ✅ **Schema Validation**: Required tables exist and are accessible
3. ✅ **ArxObject Creation**: Test objects can be created and stored
4. ✅ **Data Integrity**: Coordinates are stored and retrieved correctly
5. ✅ **System Classification**: Objects are properly categorized
6. ✅ **Cleanup**: Test data is properly removed

## 🚀 **Next Steps After Successful Testing**

Once all tests pass:

1. **Test with Real PDF**: Upload an actual floor plan PDF
2. **Validate Coordinates**: Ensure walls appear in correct positions
3. **Check System Classification**: Verify objects are tagged correctly
4. **Monitor Performance**: Check database query performance
5. **Move to Phase 2**: Begin 3D viewer development

## 🔧 **Troubleshooting Commands**

### **Check Database Tables**
```sql
-- Connect to PostgreSQL
psql -U your_user -d arxos

-- List tables
\dt

-- Check table structure
\d arx_objects
\d pdf_buildings

-- Check if tables have data
SELECT COUNT(*) FROM arx_objects;
SELECT COUNT(*) FROM pdf_buildings;
```

### **Check Backend Logs**
```bash
# Watch backend logs
tail -f backend.log

# Check for specific errors
grep -i "error\|failed" backend.log
```

### **Test Database Connection**
```bash
# Test PostgreSQL connection
psql -h localhost -U your_user -d arxos -c "SELECT version();"
```

## 📚 **Additional Resources**

- **Database Schema**: `migrations/100_create_arxobjects_table.sql`
- **ArxObject Structure**: `handlers/pdf_upload.go` (SimpleArxObject)
- **API Endpoints**: `main.go` routing configuration
- **Error Handling**: `handlers/helpers.go` (respondWithError)

---

**Happy Testing! 🚀**

If you encounter any issues, check the error messages carefully and refer to the troubleshooting section above.
