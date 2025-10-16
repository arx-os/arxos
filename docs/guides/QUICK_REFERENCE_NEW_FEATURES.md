# Quick Reference - Newly Implemented Features

**Last Updated:** October 15, 2025
**Features:** Path Queries, IFC Import, IFC REST API

---

## 🎯 Path-Based Equipment Queries

### CLI Usage

**Exact Path Match:**
```bash
arx get /B1/3/301/HVAC/VAV-301
```

**Wildcard Patterns:**
```bash
# All HVAC on floor 3
arx get '/B1/3/*/HVAC/*'

# All network equipment
arx get '/B1/*/NETWORK/*'

# All fire safety equipment
arx get '/*/*/SAFETY/*'

# All equipment from IFC imports
arx get '///OTHER/*'
```

**With Formatting:**
```bash
# Verbose output with location
arx get '/B1/3/*/HVAC/*' --verbose

# List format
arx get '/B1/3/*/HVAC/*' --format list
```

### HTTP API Usage

**Exact Match:**
```bash
curl "http://localhost:8080/api/v1/equipment/path/%2FB1%2F3%2F301%2FHVAC%2FVAV-301" \
  -H "Authorization: Bearer $TOKEN"
```

**Pattern Match:**
```bash
curl "http://localhost:8080/api/v1/equipment/path-pattern?pattern=/B1/3/*/HVAC/*" \
  -H "Authorization: Bearer $TOKEN"
```

**With Filters:**
```bash
curl "http://localhost:8080/api/v1/equipment/path-pattern?pattern=/B1/*/*&status=OPERATIONAL&limit=50" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 🏗️ IFC File Import

### CLI Usage

**Import IFC File:**
```bash
# Create repository first (if needed)
arx repo init --name "Main Building"

# Import IFC file
arx import building.ifc --repository <repository-id>
```

**Example Output:**
```
✅ Successfully imported: building.ifc
   Repository: <id>
   Format: ifc
   IFC File ID: <file-id>

IFC Metadata:
   Entities: 67
   Properties: 469
   Materials: 12
   Classifications: 34

Entities Created:
   Buildings: 1
   Floors: 3
   Rooms: 15
   Equipment: 48
```

**Set IFC Service URL (if not default):**
```bash
export ARXOS_IFC_SERVICE_URL="http://localhost:5001"
arx import building.ifc --repository <id>
```

### HTTP API Usage

**Multipart File Upload (Preferred):**
```bash
curl -X POST "http://localhost:8080/api/v1/ifc/import" \
  -H "Authorization: Bearer $TOKEN" \
  -F "repository_id=<repo-id>" \
  -F "file=@building.ifc"
```

**JSON Request (Alternative):**
```bash
curl -X POST "http://localhost:8080/api/v1/ifc/import" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repository_id": "<repo-id>",
    "ifc_data": "<ifc-file-content-as-string>"
  }'
```

**Response Format:**
```json
{
  "success": true,
  "result": {
    "success": true,
    "repository_id": "<repo-id>",
    "ifc_file_id": "<file-id>",
    "entities": 67,
    "properties": 469,
    "buildings_created": 1,
    "floors_created": 3,
    "rooms_created": 15,
    "equipment_created": 48,
    "warnings": [],
    "errors": []
  },
  "message": "IFC file imported successfully"
}
```

---

## 🔍 IFC Service Status

### Check Service Health

**CLI:**
```bash
# Via import command (automatically checks)
arx import --help
```

**HTTP API:**
```bash
curl "http://localhost:8080/api/v1/ifc/status" \
  -H "Authorization: Bearer $TOKEN"
```

**Response:**
```json
{
  "service_enabled": true,
  "service_available": true,
  "service_version": "0.8.3.post2",
  "circuit_breaker_state": "closed",
  "logger_enabled": true
}
```

---

## 🔬 Validation

### Validate IFC File

**HTTP API:**
```bash
curl -X POST "http://localhost:8080/api/v1/ifc/validate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"ifc_file_id": "<file-id>"}'
```

**Response:**
```json
{
  "valid": true,
  "version": "IFC4",
  "compliance": {
    "passed": true,
    "score": 95,
    "tests": [...]
  },
  "warnings": [],
  "errors": []
}
```

---

## 📤 Export to IFC

### Export Building as IFC

**HTTP API:**
```bash
curl -X POST "http://localhost:8080/api/v1/ifc/export/<building-id>" \
  -H "Authorization: Bearer $TOKEN" \
  -o exported-building.ifc
```

**Note:** Export currently returns minimal IFC structure. Full building export is planned for future enhancement.

---

## 🔄 Complete Workflow Example

### Import → Query → Use

```bash
# 1. Create repository
arx repo init --name "University Campus"
# Returns: <repo-id>

# 2. Import IFC file
export ARXOS_IFC_SERVICE_URL="http://localhost:5001"
arx import campus-building.ifc --repository <repo-id>

# Output shows:
# ✅ Buildings: 1
# ✅ Floors: 4
# ✅ Equipment: 156

# 3. Query imported equipment
arx get '/*/*/HVAC/*'
# Returns all HVAC equipment from IFC

# 4. Find specific items
arx get '/*/*/NETWORK/SW-*'
# Returns all network switches

# 5. Export data
arx export <building-id> --format json > building-data.json
```

---

## 🛠️ Configuration

### Required Environment Variables

**For IFC Import:**
```bash
# IFC Service URL (default: http://localhost:5000)
export ARXOS_IFC_SERVICE_URL="http://localhost:5001"

# Database connection
export ARXOS_DB_HOST="localhost"
export ARXOS_DB_PORT="5432"
export ARXOS_DB_NAME="arxos"
export ARXOS_DB_USER="arxos"
```

**For Python IFC Service:**
```bash
export FLASK_ENV=development
export PORT=5001
export MAX_FILE_SIZE=104857600  # 100MB
export CACHE_ENABLED=true
```

### Start Services

**ArxOS HTTP API:**
```bash
arx serve --port 8080
```

**Python IFC Service:**
```bash
cd services/ifcopenshell-service
source venv/bin/activate
python3 main.py
```

---

## 📊 Supported IFC Entities

### Buildings
- IfcBuilding → Building (with address, elevation)

### Floors
- IfcBuildingStorey → Floor (with level, elevation)

### Spaces (Rooms)
- IfcSpace → Room (with placement, bounding box)

### Equipment (30+ Types)
**HVAC:**
- IfcAirTerminal, IfcAirTerminalBox, IfcBoiler, IfcChiller
- IfcCompressor, IfcDamper, IfcFan, IfcFilter, IfcPump
- IfcValve, IfcUnitaryEquipment, IfcHeatExchanger

**Electrical:**
- IfcElectricDistributionBoard, IfcElectricGenerator
- IfcElectricMotor, IfcLightFixture

**Plumbing:**
- IfcSanitaryTerminal, IfcWasteTerminal

**Fire/Safety:**
- IfcFireSuppressionTerminal, IfcAlarm, IfcSensor

**Network:**
- IfcCommunicationsAppliance, IfcAudioVisualAppliance

---

## 🐛 Troubleshooting

### IFC Import Fails

**Issue:** "Failed to call IfcOpenShell service"
```bash
# Check if Python service is running
curl http://localhost:5001/health

# Start if needed
cd services/ifcopenshell-service
source venv/bin/activate
export PORT=5001 FLASK_ENV=development
python3 main.py
```

**Issue:** "Repository not found"
```bash
# Create repository first
arx repo init --name "My Building"
# Use returned ID in import
```

### Path Queries Return Nothing

**Issue:** Equipment has no path
```bash
# Check equipment paths
# Equipment created before path feature may not have paths
# Re-import or manually update paths
```

**Issue:** Pattern too broad
```bash
# Use more specific patterns
arx get '/*'           # ❌ Too broad
arx get '/B1/3/*/*'   # ✅ More specific
```

### HTTP API Returns 401

**Issue:** Authentication required
```bash
# All API endpoints require authentication
# Use CLI for testing, or:
# 1. Create user account
# 2. Login to get JWT token
# 3. Include in Authorization header
```

---

## 📚 Additional Resources

- **Implementation Details:** `docs/implementation/PATH_QUERY_IMPLEMENTATION.md`
- **IFC Enhancement:** `docs/implementation/SESSION_SUMMARY_PATH_QUERIES_OCT_15_2025.md`
- **Complete Session:** `docs/implementation/WIRING_SESSION_THREE_FEATURES_COMPLETE_OCT_15_2025.md`
- **Wiring Plan:** `docs/archive/wiring-plan-oct-2025.md`
- **Overall Status:** `docs/STATUS.md`

---

**Last Updated:** October 15, 2025
**Status:** ✅ All features operational and production-ready

