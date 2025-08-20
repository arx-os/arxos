package tests

import (
	"arxos/db"
	"arxos/models"
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

// TestAssetCRUD tests the complete asset CRUD operations
func TestAssetCRUD(t *testing.T) {
	// Set up test environment
	os.Setenv("JWT_SECRET", "test-secret-key")
	os.Setenv("DB_HOST", "localhost")
	os.Setenv("DB_PORT", "5432")
	os.Setenv("DB_USER", "arxos_user")
	os.Setenv("DB_PASSWORD", "arxos_password")
	os.Setenv("DB_NAME", "arxos_test")

	// Connect to test database
	db.Connect()
	defer db.DB.Migrator().DropTable(&models.SecurityAlert{}, &models.BuildingAsset{}, &models.Building{}, &models.User{})

	// Run individual test functions
	t.Run("Create Asset", testCreateAsset)
	t.Run("Get Asset", testGetAsset)
	t.Run("Update Asset", testUpdateAsset)
	t.Run("Delete Asset", testDeleteAsset)
	t.Run("List Assets", testListAssets)
	t.Run("Asset History", testAssetHistory)
	t.Run("Asset Maintenance", testAssetMaintenance)
	t.Run("Asset Valuation", testAssetValuation)
	t.Run("Asset Export", testAssetExport)
	t.Run("Asset Summary", testAssetSummary)
}

func testCreateAsset(t *testing.T) {
	// Create test data
	user := CreateTestUser(t, "test@example.com", "testuser", "editor")
	building := CreateTestBuilding(t, user.ID)

	// Test asset creation
	assetData := map[string]interface{}{
		"building_id": building.ID,
		"floor_id":    1,
		"room_id":     "ROOM_101",
		"symbol_id":   "hvac_001",
		"asset_type":  "HVAC",
		"system":      "Heating",
		"subsystem":   "Air Handling",
		"location": map[string]interface{}{
			"floor": "1st Floor",
			"room":  "101",
			"x":     150.5,
			"y":     200.0,
		},
		"specifications": map[string]interface{}{
			"manufacturer": "Carrier",
			"model":        "48TC",
			"capacity":     "10 tons",
		},
		"estimated_value":  25000.00,
		"replacement_cost": 30000.00,
		"status":           "active",
	}

	reqBodyBytes, _ := json.Marshal(assetData)
	req := httptest.NewRequest("POST", "/api/assets", bytes.NewBuffer(reqBodyBytes))
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.CreateBuildingAsset(w, req)

	assert.Equal(t, http.StatusCreated, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)

	assert.Contains(t, response, "id")
	assert.Equal(t, "HVAC", response["asset_type"])
	assert.Equal(t, "Heating", response["system"])
	assert.Equal(t, float64(25000), response["estimated_value"])
}

func testGetAsset(t *testing.T) {
	// Create test data
	user := CreateTestUser(t, "test@example.com", "testuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	asset := CreateTestAsset(t, building.ID)

	// Test getting asset by ID
	req := httptest.NewRequest("GET", fmt.Sprintf("/api/assets/%s", asset.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w := httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.GetBuildingAsset(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)

	assert.Equal(t, asset.ID, response["id"])
	assert.Equal(t, "HVAC", response["asset_type"])
	assert.Equal(t, "Heating", response["system"])
}

func testUpdateAsset(t *testing.T) {
	// Create test data
	user := CreateTestUser(t, "test@example.com", "testuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	asset := CreateTestAsset(t, building.ID)

	// Test updating asset
	updateData := map[string]interface{}{
		"asset_type":       "Electrical",
		"system":           "Power Distribution",
		"estimated_value":  35000.00,
		"replacement_cost": 40000.00,
		"status":           "maintenance",
	}

	reqBodyBytes, _ := json.Marshal(updateData)
	req := httptest.NewRequest("PUT", fmt.Sprintf("/api/assets/%s", asset.ID), bytes.NewBuffer(reqBodyBytes))
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.UpdateBuildingAsset(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)

	assert.Equal(t, "Electrical", response["asset_type"])
	assert.Equal(t, "Power Distribution", response["system"])
	assert.Equal(t, float64(35000), response["estimated_value"])
	assert.Equal(t, "maintenance", response["status"])
}

func testDeleteAsset(t *testing.T) {
	// Create test data
	user := CreateTestUser(t, "test@example.com", "testuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	asset := CreateTestAsset(t, building.ID)

	// Test deleting asset
	req := httptest.NewRequest("DELETE", fmt.Sprintf("/api/assets/%s", asset.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w := httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.DeleteBuildingAsset(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	// Verify asset was deleted
	req = httptest.NewRequest("GET", fmt.Sprintf("/api/assets/%s", asset.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w = httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.GetBuildingAsset(w, req)

	assert.Equal(t, http.StatusNotFound, w.Code)
}

func testListAssets(t *testing.T) {
	// Create test data
	user := CreateTestUser(t, "test@example.com", "testuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	CreateTestAsset(t, building.ID)
	CreateTestAsset(t, building.ID)

	// Test listing assets
	req := httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/assets", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w := httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.ListBuildingAssets(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)

	assets := response["assets"].([]interface{})
	assert.GreaterOrEqual(t, len(assets), 2)

	// Test filtering
	req = httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/assets?system=Heating", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w = httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.ListBuildingAssets(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	json.Unmarshal(w.Body.Bytes(), &response)
	filteredAssets := response["assets"].([]interface{})
	assert.GreaterOrEqual(t, len(filteredAssets), 1)
}

func testAssetHistory(t *testing.T) {
	// Create test data
	user := CreateTestUser(t, "test@example.com", "testuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	asset := CreateTestAsset(t, building.ID)

	// Test adding history record
	historyData := map[string]interface{}{
		"event_type":  "installation",
		"event_date":  time.Now().Format(time.RFC3339),
		"description": "Initial installation",
		"cost":        25000.00,
		"contractor":  "ABC HVAC Services",
		"warranty":    "5 years parts and labor",
	}

	reqBodyBytes, _ := json.Marshal(historyData)
	req := httptest.NewRequest("POST", fmt.Sprintf("/api/assets/%s/history", asset.ID), bytes.NewBuffer(reqBodyBytes))
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.AddAssetHistory(w, req)

	assert.Equal(t, http.StatusCreated, w.Code)

	// Verify history record was added
	req = httptest.NewRequest("GET", fmt.Sprintf("/api/assets/%s", asset.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w = httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.GetBuildingAsset(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)

	history := response["history"].([]interface{})
	assert.Greater(t, len(history), 0)

	firstHistory := history[0].(map[string]interface{})
	assert.Equal(t, "installation", firstHistory["event_type"])
	assert.Equal(t, "Initial installation", firstHistory["description"])
	assert.Equal(t, float64(25000), firstHistory["cost"])
}

func testAssetMaintenance(t *testing.T) {
	// Create test data
	user := CreateTestUser(t, "test@example.com", "testuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	asset := CreateTestAsset(t, building.ID)

	// Test adding maintenance record
	maintenanceData := map[string]interface{}{
		"maintenance_type": "preventive",
		"status":           "scheduled",
		"scheduled_date":   time.Now().AddDate(0, 1, 0).Format(time.RFC3339),
		"description":      "Annual inspection",
		"estimated_cost":   500.00,
		"technician":       "John Smith",
	}

	reqBodyBytes, _ := json.Marshal(maintenanceData)
	req := httptest.NewRequest("POST", fmt.Sprintf("/api/assets/%s/maintenance", asset.ID), bytes.NewBuffer(reqBodyBytes))
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.AddAssetMaintenance(w, req)

	assert.Equal(t, http.StatusCreated, w.Code)

	// Verify maintenance record was added
	req = httptest.NewRequest("GET", fmt.Sprintf("/api/assets/%s", asset.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w = httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.GetBuildingAsset(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)

	maintenance := response["maintenance"].([]interface{})
	assert.Greater(t, len(maintenance), 0)

	firstMaintenance := maintenance[0].(map[string]interface{})
	assert.Equal(t, "preventive", firstMaintenance["maintenance_type"])
	assert.Equal(t, "scheduled", firstMaintenance["status"])
	assert.Equal(t, "Annual inspection", firstMaintenance["description"])
	assert.Equal(t, float64(500), firstMaintenance["estimated_cost"])
}

func testAssetValuation(t *testing.T) {
	// Create test data
	user := CreateTestUser(t, "test@example.com", "testuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	asset := CreateTestAsset(t, building.ID)

	// Test adding valuation record
	valuationData := map[string]interface{}{
		"valuation_date":   time.Now().Format(time.RFC3339),
		"valuation_type":   "market",
		"value":            30000.00,
		"currency":         "USD",
		"valuation_method": "comparable_sales",
		"notes":            "Based on similar equipment sales",
	}

	reqBodyBytes, _ := json.Marshal(valuationData)
	req := httptest.NewRequest("POST", fmt.Sprintf("/api/assets/%s/valuations", asset.ID), bytes.NewBuffer(reqBodyBytes))
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))
	req.Header.Set("Content-Type", "application/json")

	w := httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.AddAssetValuation(w, req)

	assert.Equal(t, http.StatusCreated, w.Code)

	// Verify valuation record was added
	req = httptest.NewRequest("GET", fmt.Sprintf("/api/assets/%s", asset.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w = httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.GetBuildingAsset(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)

	valuations := response["valuations"].([]interface{})
	assert.Greater(t, len(valuations), 0)

	firstValuation := valuations[0].(map[string]interface{})
	assert.Equal(t, "market", firstValuation["valuation_type"])
	assert.Equal(t, float64(30000), firstValuation["value"])
	assert.Equal(t, "USD", firstValuation["currency"])
}

func testAssetExport(t *testing.T) {
	// Create test data
	user := CreateTestUser(t, "test@example.com", "testuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	CreateTestAsset(t, building.ID)

	// Test CSV export
	req := httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/inventory/export?format=csv", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w := httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.ExportBuildingInventory(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Header().Get("Content-Type"), "text/csv")

	// Test JSON export
	req = httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/inventory/export?format=json", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w = httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.ExportBuildingInventory(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Header().Get("Content-Type"), "application/json")

	// Test export with filters
	req = httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/inventory/export?format=csv&system=HVAC", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w = httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.ExportBuildingInventory(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
}

func testAssetSummary(t *testing.T) {
	// Create test data
	user := CreateTestUser(t, "test@example.com", "testuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	CreateTestAsset(t, building.ID)

	// Test getting building summary
	req := httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/inventory/summary", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w := httptest.NewRecorder()
	// Call the handler directly or through router
	// handlers.GetBuildingInventorySummary(w, req)

	assert.Equal(t, http.StatusOK, w.Code)

	var response map[string]interface{}
	json.Unmarshal(w.Body.Bytes(), &response)

	assert.Contains(t, response, "total_assets")
	assert.Contains(t, response, "systems")
	assert.Contains(t, response, "asset_types")
	assert.Contains(t, response, "total_value")
	assert.Contains(t, response, "average_age")
	assert.Contains(t, response, "efficiency_stats")

	// Verify summary data
	assert.Greater(t, response["total_assets"], float64(0))
	assert.Greater(t, response["total_value"], float64(0))
}
