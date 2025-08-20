package tests

import (
	"arxos/db"
	"arxos/handlers"
	"arxos/middleware"
	"arxos/models"
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestSecurityFeatures(t *testing.T) {
	os.Setenv("JWT_SECRET", "test-secret-key")
	os.Setenv("DB_HOST", "localhost")
	os.Setenv("DB_PORT", "5432")
	os.Setenv("DB_USER", "arxos_user")
	os.Setenv("DB_PASSWORD", "arxos_password")
	os.Setenv("DB_NAME", "arxos_test")

	db.Connect()
	defer db.DB.Migrator().DropTable(&models.DataVendorAPIKey{}, &models.BuildingAsset{}, &models.Building{}, &models.User{})

	t.Run("Access Controls", testAccessControls)
	t.Run("API Key Security", testAPIKeySecurity)
	t.Run("Data Obfuscation", testDataObfuscation)
	t.Run("Rate Limiting", testRateLimiting)
	t.Run("Security Headers", testSecurityHeaders)
}

func testAccessControls(t *testing.T) {
	// Create test users with different roles
	adminUser := CreateTestUser(t, "admin@test.com", "admin", "admin")
	editorUser := CreateTestUser(t, "editor@test.com", "editor", "editor")
	maintenanceUser := CreateTestUser(t, "maintenance@test.com", "maintenance", "maintenance")
	viewerUser := CreateTestUser(t, "viewer@test.com", "viewer", "viewer")

	// Create test building and asset
	building := CreateTestBuilding(t, adminUser.ID)
	asset := CreateTestAsset(t, building.ID)

	// Test 1: Admin can modify any asset
	t.Run("Admin Asset Modification", func(t *testing.T) {
		updateData := map[string]interface{}{
			"asset_type": "Modified by Admin",
			"system":     "Admin System",
		}

		reqBodyBytes, _ := json.Marshal(updateData)
		req := httptest.NewRequest("PUT", fmt.Sprintf("/api/assets/%s", asset.ID), bytes.NewBuffer(reqBodyBytes))
		req.Header.Set("Authorization", "Bearer "+GenerateTestToken(adminUser.ID, adminUser.Role))
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		handlers.UpdateBuildingAsset(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
	})

	// Test 2: Editor can modify assets in accessible buildings
	t.Run("Editor Asset Modification", func(t *testing.T) {
		updateData := map[string]interface{}{
			"asset_type": "Modified by Editor",
			"system":     "Editor System",
		}

		reqBodyBytes, _ := json.Marshal(updateData)
		req := httptest.NewRequest("PUT", fmt.Sprintf("/api/assets/%s", asset.ID), bytes.NewBuffer(reqBodyBytes))
		req.Header.Set("Authorization", "Bearer "+GenerateTestToken(editorUser.ID, editorUser.Role))
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		handlers.UpdateBuildingAsset(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
	})

	// Test 3: Maintenance user cannot modify assets they're not assigned to
	t.Run("Maintenance User Restricted Access", func(t *testing.T) {
		updateData := map[string]interface{}{
			"asset_type": "Modified by Maintenance",
			"system":     "Maintenance System",
		}

		reqBodyBytes, _ := json.Marshal(updateData)
		req := httptest.NewRequest("PUT", fmt.Sprintf("/api/assets/%s", asset.ID), bytes.NewBuffer(reqBodyBytes))
		req.Header.Set("Authorization", "Bearer "+GenerateTestToken(maintenanceUser.ID, maintenanceUser.Role))
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		handlers.UpdateBuildingAsset(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})

	// Test 4: Only admins and asset owners can delete assets
	t.Run("Asset Deletion Permissions", func(t *testing.T) {
		// Test admin can delete
		req1 := httptest.NewRequest("DELETE", fmt.Sprintf("/api/assets/%s", asset.ID), nil)
		req1.Header.Set("Authorization", "Bearer "+GenerateTestToken(adminUser.ID, adminUser.Role))

		w1 := httptest.NewRecorder()
		handlers.DeleteBuildingAsset(w1, req1)
		assert.Equal(t, http.StatusOK, w1.Code)

		// Create new asset for viewer test
		newAsset := CreateTestAsset(t, building.ID)

		// Test viewer cannot delete
		req2 := httptest.NewRequest("DELETE", fmt.Sprintf("/api/assets/%s", newAsset.ID), nil)
		req2.Header.Set("Authorization", "Bearer "+GenerateTestToken(viewerUser.ID, viewerUser.Role))

		w2 := httptest.NewRecorder()
		handlers.DeleteBuildingAsset(w2, req2)
		assert.Equal(t, http.StatusForbidden, w2.Code)
	})
}

func testAPIKeySecurity(t *testing.T) {
	// Test 1: API key generation is cryptographically secure
	t.Run("Secure API Key Generation", func(t *testing.T) {
		key1 := handlers.GenerateAPIKey()
		key2 := handlers.GenerateAPIKey()

		// Keys should be different
		assert.NotEqual(t, key1, key2)

		// Keys should have proper format
		assert.True(t, strings.HasPrefix(key1, "arx_"))
		assert.True(t, strings.HasPrefix(key2, "arx_"))

		// Keys should be reasonably long
		assert.Greater(t, len(key1), 32)
		assert.Greater(t, len(key2), 32)
	})

	// Test 2: API key validation
	t.Run("API Key Validation", func(t *testing.T) {
		// Create valid API key
		apiKey := CreateTestAPIKey(t, "TestVendor", "test@vendor.com", "basic")

		// Test valid key
		req := httptest.NewRequest("GET", "/api/vendor/buildings", nil)
		req.Header.Set("Authorization", "Bearer "+apiKey.Key)

		w := httptest.NewRecorder()
		handlers.GetAvailableBuildings(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		// Test invalid key
		req2 := httptest.NewRequest("GET", "/api/vendor/buildings", nil)
		req2.Header.Set("Authorization", "Bearer invalid_key")

		w2 := httptest.NewRecorder()
		handlers.GetAvailableBuildings(w2, req2)

		assert.Equal(t, http.StatusUnauthorized, w2.Code)
	})

	// Test 3: API key expiration
	t.Run("API Key Expiration", func(t *testing.T) {
		// Create expired API key
		expiredKey := models.DataVendorAPIKey{
			Key:         "expired_test_key",
			VendorName:  "ExpiredVendor",
			Email:       "expired@vendor.com",
			AccessLevel: "basic",
			RateLimit:   1000,
			IsActive:    true,
			ExpiresAt:   time.Now().Add(-24 * time.Hour), // Expired yesterday
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		}
		db.DB.Create(&expiredKey)

		req := httptest.NewRequest("GET", "/api/vendor/buildings", nil)
		req.Header.Set("Authorization", "Bearer "+expiredKey.Key)

		w := httptest.NewRecorder()
		handlers.GetAvailableBuildings(w, req)

		assert.Equal(t, http.StatusUnauthorized, w.Code)
	})

	// Test 4: API key rotation
	t.Run("API Key Rotation", func(t *testing.T) {
		// Create API key to rotate
		originalKey := CreateTestAPIKey(t, "RotateVendor", "rotate@vendor.com", "basic")

		// Simulate rotation by creating new key and deactivating old one
		newKey := models.DataVendorAPIKey{
			Key:         handlers.GenerateAPIKey(),
			VendorName:  originalKey.VendorName,
			Email:       originalKey.Email,
			AccessLevel: originalKey.AccessLevel,
			RateLimit:   originalKey.RateLimit,
			IsActive:    true,
			ExpiresAt:   originalKey.ExpiresAt,
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		}
		db.DB.Create(&newKey)

		// Deactivate old key
		db.DB.Model(&originalKey).Update("is_active", false)

		// Test old key is no longer valid
		req1 := httptest.NewRequest("GET", "/api/vendor/buildings", nil)
		req1.Header.Set("Authorization", "Bearer "+originalKey.Key)

		w1 := httptest.NewRecorder()
		handlers.GetAvailableBuildings(w1, req1)

		assert.Equal(t, http.StatusUnauthorized, w1.Code)

		// Test new key is valid
		req2 := httptest.NewRequest("GET", "/api/vendor/buildings", nil)
		req2.Header.Set("Authorization", "Bearer "+newKey.Key)

		w2 := httptest.NewRecorder()
		handlers.GetAvailableBuildings(w2, req2)

		assert.Equal(t, http.StatusOK, w2.Code)
	})
}

func testDataObfuscation(t *testing.T) {
	// Test 1: Basic data obfuscation
	t.Run("Basic Data Obfuscation", func(t *testing.T) {
		handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.Write([]byte(`{"email":"test@example.com","phone":"123-456-7890","name":"John Doe"}`))
		})

		obfuscatedHandler := middleware.DataObfuscationMiddleware(handler)

		// Test without obfuscation
		req := httptest.NewRequest("GET", "/test", nil)
		w := httptest.NewRecorder()

		obfuscatedHandler.ServeHTTP(w, req)

		response := w.Body.String()
		assert.Contains(t, response, "test@example.com")
		assert.Contains(t, response, "123-456-7890")

		// Test with obfuscation
		req = httptest.NewRequest("GET", "/test?obfuscate=true", nil)
		w = httptest.NewRecorder()

		obfuscatedHandler.ServeHTTP(w, req)

		response = w.Body.String()
		assert.NotContains(t, response, "test@example.com")
		assert.NotContains(t, response, "123-456-7890")
		assert.Contains(t, response, "***")
	})

	// Test 2: Address anonymization
	t.Run("Address Anonymization", func(t *testing.T) {
		handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.Write([]byte(`{"building_address":"123 Main St, New York, NY 10001","location":"40.7128,-74.0060"}`))
		})

		obfuscatedHandler := middleware.DataObfuscationMiddleware(handler)

		// Test with anonymization
		req := httptest.NewRequest("GET", "/test?anonymize=true", nil)
		w := httptest.NewRecorder()

		obfuscatedHandler.ServeHTTP(w, req)

		response := w.Body.String()
		assert.Contains(t, response, "***, New York, NY 10001")
		assert.Contains(t, response, "40.7")
		assert.Contains(t, response, "-74.0")
	})

	// Test 3: Financial data obfuscation
	t.Run("Financial Data Obfuscation", func(t *testing.T) {
		handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Header().Set("Content-Type", "application/json")
			w.Write([]byte(`{"estimated_value":50000,"replacement_cost":75000,"asset_type":"HVAC"}`))
		})

		obfuscatedHandler := middleware.DataObfuscationMiddleware(handler)

		// Test with obfuscation
		req := httptest.NewRequest("GET", "/test?obfuscate=true", nil)
		w := httptest.NewRecorder()

		obfuscatedHandler.ServeHTTP(w, req)

		response := w.Body.String()
		assert.NotContains(t, response, "50000")
		assert.NotContains(t, response, "75000")
		assert.Contains(t, response, "***")
		assert.Contains(t, response, "HVAC") // Non-sensitive data should remain
	})
}

func testRateLimiting(t *testing.T) {
	// Test 1: Rate limiting middleware
	t.Run("Rate Limiting Middleware", func(t *testing.T) {
		handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("success"))
		})

		rateLimitedHandler := middleware.RateLimitMiddleware(1.0, 2)(handler) // 1 request per second, burst of 2

		// First two requests should succeed
		for i := 0; i < 2; i++ {
			req := httptest.NewRequest("GET", "/test", nil)
			req.RemoteAddr = "192.168.1.1:12345"
			w := httptest.NewRecorder()

			rateLimitedHandler.ServeHTTP(w, req)
			assert.Equal(t, http.StatusOK, w.Code)
		}

		// Third request should be rate limited
		req := httptest.NewRequest("GET", "/test", nil)
		req.RemoteAddr = "192.168.1.1:12345"
		w := httptest.NewRecorder()

		rateLimitedHandler.ServeHTTP(w, req)
		assert.Equal(t, http.StatusTooManyRequests, w.Code)
	})

	// Test 2: API key rate limiting
	t.Run("API Key Rate Limiting", func(t *testing.T) {
		apiKey := CreateTestAPIKey(t, "RateLimitVendor", "ratelimit@vendor.com", "basic")
		apiKey.RateLimit = 1 // Very low rate limit
		db.DB.Save(&apiKey)

		// First request should succeed
		req1 := httptest.NewRequest("GET", "/api/vendor/buildings", nil)
		req1.Header.Set("Authorization", "Bearer "+apiKey.Key)

		w1 := httptest.NewRecorder()
		handlers.GetAvailableBuildings(w1, req1)
		assert.Equal(t, http.StatusOK, w1.Code)

		// Second request should fail
		req2 := httptest.NewRequest("GET", "/api/vendor/buildings", nil)
		req2.Header.Set("Authorization", "Bearer "+apiKey.Key)

		w2 := httptest.NewRecorder()
		handlers.GetAvailableBuildings(w2, req2)
		assert.Equal(t, http.StatusTooManyRequests, w2.Code)
	})
}

func testSecurityHeaders(t *testing.T) {
	// Test security headers middleware
	t.Run("Security Headers", func(t *testing.T) {
		handler := http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			w.Write([]byte("success"))
		})

		secureHandler := middleware.SecurityHeadersMiddleware(handler)

		req := httptest.NewRequest("GET", "/test", nil)
		w := httptest.NewRecorder()

		secureHandler.ServeHTTP(w, req)

		// Check security headers
		assert.Equal(t, "nosniff", w.Header().Get("X-Content-Type-Options"))
		assert.Equal(t, "DENY", w.Header().Get("X-Frame-Options"))
		assert.Equal(t, "1; mode=block", w.Header().Get("X-XSS-Protection"))
		assert.Contains(t, w.Header().Get("Strict-Transport-Security"), "max-age=31536000")
		assert.Contains(t, w.Header().Get("Content-Security-Policy"), "default-src 'self'")
		assert.Equal(t, "strict-origin-when-cross-origin", w.Header().Get("Referrer-Policy"))
	})
}

// Helper function to generate test JWT token
func GenerateTestToken(userID uint, role string) string {
	// This is a simplified token generation for testing
	// In production, use the proper JWT generation function
	return fmt.Sprintf("test_token_%d_%s", userID, role)
}
