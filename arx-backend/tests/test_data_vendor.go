package tests

import (
	"context"
	"arx/db"
	"arx/handlers"
	"arx/models"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/stretchr/testify/assert"
)

func TestDataVendorAPI(t *testing.T) {
	os.Setenv("JWT_SECRET", "test-secret-key")
	os.Setenv("DB_HOST", "localhost")
	os.Setenv("DB_PORT", "5432")
	os.Setenv("DB_USER", "arxos_user")
	os.Setenv("DB_PASSWORD", "arxos_password")
	os.Setenv("DB_NAME", "arxos_test")

	db.Connect()
	defer db.DB.Migrator().DropTable(&models.DataVendorAPIKey{}, &models.BuildingAsset{}, &models.Building{}, &models.User{})

	t.Run("API Key Generation", testAPIKeyGeneration)
	t.Run("API Key Authentication", testAPIKeyAuthentication)
	t.Run("Rate Limiting", testRateLimiting)
	t.Run("Data Access", testDataAccess)
	t.Run("Building Inventory Access", testBuildingInventoryAccess)
	t.Run("Building Summary Access", testBuildingSummaryAccess)
	t.Run("Invalid API Key", testInvalidAPIKey)
	t.Run("Expired API Key", testExpiredAPIKey)
	t.Run("Rate Limit Exceeded", testRateLimitExceeded)
	t.Run("Access Level Restrictions", testAccessLevelRestrictions)
}

func testAPIKeyGeneration(t *testing.T) {
	apiKey := CreateTestAPIKey(t, "Vendor1", "vendor1@example.com", "basic")
	assert.NotEmpty(t, apiKey.Key)
	assert.Equal(t, "Vendor1", apiKey.VendorName)
	assert.Equal(t, "basic", apiKey.AccessLevel)
	assert.True(t, apiKey.IsActive)
	assert.True(t, apiKey.ExpiresAt.After(time.Now()))
}

func testAPIKeyAuthentication(t *testing.T) {
	apiKey := CreateTestAPIKey(t, "Vendor2", "vendor2@example.com", "premium")

	req := httptest.NewRequest("GET", "/api/vendor/buildings", nil)
	req.Header.Set("Authorization", "Bearer "+apiKey.Key)

	w := httptest.NewRecorder()
	
	// Create chi router context
	rctx := chi.NewRouteContext()
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	
	handlers.GetAvailableBuildings(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Header().Get("Content-Type"), "application/json")
	
	// Verify response contains buildings data
	responseBody := w.Body.String()
	assert.Contains(t, responseBody, "buildings")
	assert.Contains(t, responseBody, "total")
}

func testRateLimiting(t *testing.T) {
	apiKey := CreateTestAPIKey(t, "Vendor3", "vendor3@example.com", "basic")
	apiKey.RateLimit = 5 // Set low rate limit for testing
	db.DB.Save(&apiKey)

	// Make requests up to the rate limit
	for i := 0; i < 5; i++ {
		req := httptest.NewRequest("GET", "/api/vendor/buildings", nil)
		req.Header.Set("Authorization", "Bearer "+apiKey.Key)
		w := httptest.NewRecorder()
		
		// Create chi router context
		rctx := chi.NewRouteContext()
		req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
		
		handlers.GetAvailableBuildings(w, req)
		
		if i < 4 {
			assert.Equal(t, http.StatusOK, w.Code)
		} else {
			// Last request should hit rate limit
			assert.Equal(t, http.StatusTooManyRequests, w.Code)
		}
	}
}

func testDataAccess(t *testing.T) {
	apiKey := CreateTestAPIKey(t, "Vendor4", "vendor4@example.com", "enterprise")
	user := CreateTestUser(t, "vendor4user@example.com", "vendor4user", "vendor")
	building := CreateTestBuilding(t, user.ID)
	CreateTestAsset(t, building.ID)

	req := httptest.NewRequest("GET", fmt.Sprintf("/api/vendor/buildings/%d/inventory", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+apiKey.Key)

	w := httptest.NewRecorder()
	
	// Create chi router context
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("id", fmt.Sprintf("%d", building.ID))
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	
	handlers.GetBuildingInventory(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Header().Get("Content-Type"), "application/json")
	
	// Verify response contains inventory data
	responseBody := w.Body.String()
	assert.Contains(t, responseBody, "assets")
	assert.Contains(t, responseBody, "total")
}

func testBuildingInventoryAccess(t *testing.T) {
	apiKey := CreateTestAPIKey(t, "Vendor5", "vendor5@example.com", "premium")
	user := CreateTestUser(t, "vendor5user@example.com", "vendor5user", "vendor")
	building := CreateTestBuilding(t, user.ID)
	
	// Create multiple assets
	asset1 := CreateTestAsset(t, building.ID)
	asset1.System = "HVAC"
	asset1.AssetType = "Chiller"
	db.DB.Save(&asset1)
	
	asset2 := CreateTestAsset(t, building.ID)
	asset2.System = "Electrical"
	asset2.AssetType = "Panel"
	db.DB.Save(&asset2)

	req := httptest.NewRequest("GET", fmt.Sprintf("/api/vendor/buildings/%d/inventory?format=json", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+apiKey.Key)

	w := httptest.NewRecorder()
	
	// Create chi router context
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("id", fmt.Sprintf("%d", building.ID))
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	
	handlers.GetBuildingInventory(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Header().Get("Content-Type"), "application/json")
	
	// Verify response contains both assets
	responseBody := w.Body.String()
	assert.Contains(t, responseBody, "HVAC")
	assert.Contains(t, responseBody, "Electrical")
	assert.Contains(t, responseBody, "Chiller")
	assert.Contains(t, responseBody, "Panel")
}

func testBuildingSummaryAccess(t *testing.T) {
	apiKey := CreateTestAPIKey(t, "Vendor6", "vendor6@example.com", "enterprise")
	user := CreateTestUser(t, "vendor6user@example.com", "vendor6user", "vendor")
	building := CreateTestBuilding(t, user.ID)
	CreateTestAsset(t, building.ID)

	req := httptest.NewRequest("GET", fmt.Sprintf("/api/vendor/buildings/%d/summary", building.ID), nil)
	req.Header.Set("Authorization", "Bearer "+apiKey.Key)

	w := httptest.NewRecorder()
	
	// Create chi router context
	rctx := chi.NewRouteContext()
	rctx.URLParams.Add("id", fmt.Sprintf("%d", building.ID))
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	
	handlers.GetBuildingSummary(w, req)

	assert.Equal(t, http.StatusOK, w.Code)
	assert.Contains(t, w.Header().Get("Content-Type"), "application/json")
	
	// Verify response contains summary data
	responseBody := w.Body.String()
	assert.Contains(t, responseBody, "building")
	assert.Contains(t, responseBody, "summary")
}

func testInvalidAPIKey(t *testing.T) {
	req := httptest.NewRequest("GET", "/api/vendor/buildings", nil)
	req.Header.Set("Authorization", "Bearer invalid-key")

	w := httptest.NewRecorder()
	
	// Create chi router context
	rctx := chi.NewRouteContext()
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	
	handlers.GetAvailableBuildings(w, req)

	assert.Equal(t, http.StatusUnauthorized, w.Code)
	assert.Contains(t, w.Body.String(), "Invalid API key")
}

func testExpiredAPIKey(t *testing.T) {
	// Create expired API key
	apiKey := models.DataVendorAPIKey{
		Key:         "expired-key",
		VendorName:  "ExpiredVendor",
		Email:       "expired@example.com",
		AccessLevel: "basic",
		RateLimit:   1000,
		IsActive:    true,
		ExpiresAt:   time.Now().Add(-24 * time.Hour), // Expired yesterday
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}
	db.DB.Create(&apiKey)

	req := httptest.NewRequest("GET", "/api/vendor/buildings", nil)
	req.Header.Set("Authorization", "Bearer "+apiKey.Key)

	w := httptest.NewRecorder()
	
	// Create chi router context
	rctx := chi.NewRouteContext()
	req = req.WithContext(context.WithValue(req.Context(), chi.RouteCtxKey, rctx))
	
	handlers.GetAvailableBuildings(w, req)

	assert.Equal(t, http.StatusUnauthorized, w.Code)
}

func testRateLimitExceeded(t *testing.T) {
	apiKey := CreateTestAPIKey(t, "Vendor7", "vendor7@example.com", "basic")
	apiKey.RateLimit = 1 // Very low rate limit
	db.DB.Save(&apiKey)

	// First request should succeed
	req1 := httptest.NewRequest("GET", "/api/vendor/buildings", nil)
	req1.Header.Set("Authorization", "Bearer "+apiKey.Key)
	w1 := httptest.NewRecorder()
	
	rctx1 := chi.NewRouteContext()
	req1 = req1.WithContext(context.WithValue(req1.Context(), chi.RouteCtxKey, rctx1))
	
	handlers.GetAvailableBuildings(w1, req1)
	assert.Equal(t, http.StatusOK, w1.Code)

	// Second request should fail
	req2 := httptest.NewRequest("GET", "/api/vendor/buildings", nil)
	req2.Header.Set("Authorization", "Bearer "+apiKey.Key)
	w2 := httptest.NewRecorder()
	
	rctx2 := chi.NewRouteContext()
	req2 = req2.WithContext(context.WithValue(req2.Context(), chi.RouteCtxKey, rctx2))
	
	handlers.GetAvailableBuildings(w2, req2)
	assert.Equal(t, http.StatusTooManyRequests, w2.Code)
}

func testAccessLevelRestrictions(t *testing.T) {
	// Test basic access level restrictions
	basicAPIKey := CreateTestAPIKey(t, "BasicVendor", "basic@example.com", "basic")
	premiumAPIKey := CreateTestAPIKey(t, "PremiumVendor", "premium@example.com", "premium")
	
	user := CreateTestUser(t, "accessuser@example.com", "accessuser", "vendor")
	building := CreateTestBuilding(t, user.ID)
	asset := CreateTestAsset(t, building.ID)
	
	// Set sensitive data for basic access testing
	asset.EstimatedValue = 10000.0
	asset.ReplacementCost = 15000.0
	db.DB.Save(&asset)

	// Test basic access - should not include sensitive data
	req1 := httptest.NewRequest("GET", fmt.Sprintf("/api/vendor/buildings/%d/inventory", building.ID), nil)
	req1.Header.Set("Authorization", "Bearer "+basicAPIKey.Key)
	w1 := httptest.NewRecorder()
	
	rctx1 := chi.NewRouteContext()
	rctx1.URLParams.Add("id", fmt.Sprintf("%d", building.ID))
	req1 = req1.WithContext(context.WithValue(req1.Context(), chi.RouteCtxKey, rctx1))
	
	handlers.GetBuildingInventory(w1, req1)
	
	assert.Equal(t, http.StatusOK, w1.Code)
	responseBody1 := w1.Body.String()
	// Basic access should not include sensitive financial data
	assert.NotContains(t, responseBody1, "10000")
	assert.NotContains(t, responseBody1, "15000")

	// Test premium access - should include more data
	req2 := httptest.NewRequest("GET", fmt.Sprintf("/api/vendor/buildings/%d/inventory", building.ID), nil)
	req2.Header.Set("Authorization", "Bearer "+premiumAPIKey.Key)
	w2 := httptest.NewRecorder()
	
	rctx2 := chi.NewRouteContext()
	rctx2.URLParams.Add("id", fmt.Sprintf("%d", building.ID))
	req2 = req2.WithContext(context.WithValue(req2.Context(), chi.RouteCtxKey, rctx2))
	
	handlers.GetBuildingInventory(w2, req2)
	
	assert.Equal(t, http.StatusOK, w2.Code)
	responseBody2 := w2.Body.String()
	// Premium access should include more detailed data
	assert.Contains(t, responseBody2, "asset_type")
	assert.Contains(t, responseBody2, "system")
}
