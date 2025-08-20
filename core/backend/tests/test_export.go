package tests

import (
	"arxos/db"
	"arxos/handlers"
	"arxos/models"
	"context"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/stretchr/testify/assert"
)

func TestExportEndpoints(t *testing.T) {
	os.Setenv("JWT_SECRET", "test-secret-key")
	os.Setenv("DB_HOST", "localhost")
	os.Setenv("DB_PORT", "5432")
	os.Setenv("DB_USER", "arxos_user")
	os.Setenv("DB_PASSWORD", "arxos_password")
	os.Setenv("DB_NAME", "arxos_test")

	db.Connect()
	defer db.DB.Migrator().DropTable(&models.BuildingAsset{}, &models.Building{}, &models.User{})

	t.Run("Export CSV", testExportCSV)
	t.Run("Export JSON", testExportJSON)
	t.Run("Export With Filters", testExportWithFilters)
	t.Run("Export With History", testExportWithHistory)
	t.Run("Export With Maintenance", testExportWithMaintenance)
	t.Run("Export With Valuations", testExportWithValuations)
	t.Run("Export Unauthorized", testExportUnauthorized)
	t.Run("Export Invalid Building", testExportInvalidBuilding)
	t.Run("Export Unsupported Format", testExportUnsupportedFormat)
}

func testExportCSV(t *testing.T) {
	user := CreateTestUser(t, "csv@example.com", "csvuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	CreateTestAsset(t, building.ID)

	req := httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/inventory/export?format=csv", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w := httptest.NewRecorder()

	// Create chi router context
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("buildingId", fmt.Sprintf("%d", building.ID))
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))

	handlers.ExportBuildingInventory(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Header().Get("Content-Type"), "text/csv")
	assert.Contains(t, w.Header().Get("Content-Disposition"), "attachment")
	assert.Contains(t, w.Body.String(), "Asset Type,System,Subsystem")
}

func testExportJSON(t *testing.T) {
	user := CreateTestUser(t, "json@example.com", "jsonuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	CreateTestAsset(t, building.ID)

	req := httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/inventory/export?format=json", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w := httptest.NewRecorder()

	// Create chi router context
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("buildingId", fmt.Sprintf("%d", building.ID))
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))

	handlers.ExportBuildingInventory(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Header().Get("Content-Type"), "application/json")

	// Verify JSON response contains asset data
	responseBody := w.Body.String()
	assert.Contains(t, responseBody, "asset_type")
	assert.Contains(t, responseBody, "system")
}

func testExportWithFilters(t *testing.T) {
	user := CreateTestUser(t, "filter@example.com", "filteruser", "editor")
	building := CreateTestBuilding(t, user.ID)

	// Create assets with different systems
	asset1 := CreateTestAsset(t, building.ID)
	asset1.System = "HVAC"
	db.DB.Save(&asset1)

	asset2 := CreateTestAsset(t, building.ID)
	asset2.System = "Electrical"
	db.DB.Save(&asset2)

	req := httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/inventory/export?format=csv&system=HVAC", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w := httptest.NewRecorder()

	// Create chi router context
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("buildingId", fmt.Sprintf("%d", building.ID))
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))

	handlers.ExportBuildingInventory(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Header().Get("Content-Type"), "text/csv")

	// Verify only HVAC assets are exported
	responseBody := w.Body.String()
	assert.Contains(t, responseBody, "HVAC")
	assert.NotContains(t, responseBody, "Electrical")
}

func testExportWithHistory(t *testing.T) {
	user := CreateTestUser(t, "history@example.com", "historyuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	asset := CreateTestAsset(t, building.ID)

	// Add history to asset
	history := models.AssetHistory{
		AssetID:     asset.ID,
		Action:      "maintenance",
		Details:     "Regular maintenance performed",
		PerformedBy: "technician",
		CreatedAt:   time.Now(),
	}
	db.DB.Create(&history)

	req := httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/inventory/export?format=json&includeHistory=true", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w := httptest.NewRecorder()

	// Create chi router context
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("buildingId", fmt.Sprintf("%d", building.ID))
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))

	handlers.ExportBuildingInventory(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Header().Get("Content-Type"), "application/json")

	// Verify history is included
	responseBody := w.Body.String()
	assert.Contains(t, responseBody, "history")
	assert.Contains(t, responseBody, "maintenance")
}

func testExportWithMaintenance(t *testing.T) {
	user := CreateTestUser(t, "maintenance@example.com", "maintenanceuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	asset := CreateTestAsset(t, building.ID)

	// Add maintenance record
	maintenance := models.AssetMaintenance{
		AssetID:         asset.ID,
		MaintenanceType: "preventive",
		Description:     "Scheduled maintenance",
		Cost:            500.0,
		PerformedBy:     "technician",
		CreatedAt:       time.Now(),
	}
	db.DB.Create(&maintenance)

	req := httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/inventory/export?format=json&includeMaintenance=true", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w := httptest.NewRecorder()

	// Create chi router context
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("buildingId", fmt.Sprintf("%d", building.ID))
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))

	handlers.ExportBuildingInventory(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Header().Get("Content-Type"), "application/json")

	// Verify maintenance is included
	responseBody := w.Body.String()
	assert.Contains(t, responseBody, "maintenance")
	assert.Contains(t, responseBody, "preventive")
}

func testExportWithValuations(t *testing.T) {
	user := CreateTestUser(t, "valuation@example.com", "valuationuser", "editor")
	building := CreateTestBuilding(t, user.ID)
	asset := CreateTestAsset(t, building.ID)

	// Add valuation
	valuation := models.AssetValuation{
		AssetID:       asset.ID,
		Value:         10000.0,
		Currency:      "USD",
		ValuationDate: time.Now(),
		ValuationType: "market",
		AppraisedBy:   "appraiser",
		CreatedAt:     time.Now(),
	}
	db.DB.Create(&valuation)

	req := httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/inventory/export?format=json&includeValuations=true", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w := httptest.NewRecorder()

	// Create chi router context
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("buildingId", fmt.Sprintf("%d", building.ID))
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))

	handlers.ExportBuildingInventory(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Header().Get("Content-Type"), "application/json")

	// Verify valuations are included
	responseBody := w.Body.String()
	assert.Contains(t, responseBody, "valuations")
	assert.Contains(t, responseBody, "10000")
}

func testExportUnauthorized(t *testing.T) {
	user := CreateTestUser(t, "unauth@example.com", "unauthuser", "viewer")
	building := CreateTestBuilding(t, user.ID)

	req := httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/inventory/export?format=csv", building.ID), nil)
	// No authorization header

	w := httptest.NewRecorder()

	// Create chi router context
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("buildingId", fmt.Sprintf("%d", building.ID))
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))

	handlers.ExportBuildingInventory(w, req)

	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

func testExportInvalidBuilding(t *testing.T) {
	user := CreateTestUser(t, "invalid@example.com", "invaliduser", "editor")

	req := httptest.NewRequest("GET", "/api/buildings/99999/inventory/export?format=csv", nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w := httptest.NewRecorder()

	// Create chi router context
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("buildingId", "99999")
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))

	handlers.ExportBuildingInventory(w, req)

	assert.Equal(t, http.StatusOK, w.Code) // Should return empty result, not error
}

func testExportUnsupportedFormat(t *testing.T) {
	user := CreateTestUser(t, "unsupported@example.com", "unsupporteduser", "editor")
	building := CreateTestBuilding(t, user.ID)

	req := httptest.NewRequest("GET", fmt.Sprintf("/api/buildings/%d/inventory/export?format=xml", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+GenerateTestToken(user.ID, user.Role))

	w := httptest.NewRecorder()

	// Create chi router context
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("buildingId", fmt.Sprintf("%d", building.ID))
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))

	handlers.ExportBuildingInventory(w, req)

	assert.Equal(t, http.StatusBadRequest, w.Code)
	assert.Contains(t, w.Body.String(), "Unsupported format")
}
