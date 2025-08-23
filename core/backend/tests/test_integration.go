package tests

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/arxos/arxos/core/backend/db"
	"github.com/arxos/arxos/core/backend/handlers"
	"github.com/arxos/arxos/core/backend/middleware/auth"
	"github.com/arxos/arxos/core/backend/models"

	"github.com/go-chi/chi/v5"
	"github.com/stretchr/testify/assert"
	"golang.org/x/crypto/bcrypt"
)

func setupTestServer(t *testing.T) *httptest.Server {
	// Setup test database
	db.Connect()
	db.Migrate()

	// Create test router
	r := chi.NewRouter()

	// Add middleware (commented out until middleware is properly implemented)
	// r.Use(middleware.Logger)
	// r.Use(middleware.SecurityHeadersMiddleware)
	// r.Use(middleware.AuditLoggingMiddleware)
	// r.Use(middleware.RateLimitMiddleware(100, 200))

	// Setup routes
	setupTestRoutes(r)

	return httptest.NewServer(r)
}

func setupTestRoutes(r chi.Router) {
	// Initialize handlers
	exportActivityHandler := handlers.NewExportActivityHandler(db.DB)
	complianceHandler := handlers.NewComplianceReportingHandler(db.DB)
	securityHandler := handlers.NewSecurityHandler()

	// API routes
	r.Route("/api", func(r chi.Router) {
		// Public routes
		r.Post("/register", handlers.Register)
		r.Post("/login", handlers.Login)

		// Protected routes
		r.Group(func(r chi.Router) {
			// r.Use(auth.RequireAuth)
			// r.Use(middleware.RateLimitMiddleware(50, 100))

			// Export Activity endpoints
			r.Post("/export-activities", exportActivityHandler.CreateExportActivity)
			r.Get("/export-activities", exportActivityHandler.GetExportActivities)
			r.Get("/export-analytics/dashboard", exportActivityHandler.GetExportDashboard)

			// Compliance endpoints
			r.Get("/compliance/data-access-logs", complianceHandler.GetDataAccessLogs)
			r.Get("/compliance/export-activity-summary", complianceHandler.GetExportActivitySummary)
			r.Get("/compliance/data-retention-policies", complianceHandler.GetDataRetentionPolicies)
			r.Post("/compliance/data-retention-policies", complianceHandler.CreateDataRetentionPolicy)

			// Security endpoints (admin only)
			r.Group(func(r chi.Router) {
				// r.Use(auth.RequireRole("admin", "security"))
				securityHandler.RegisterSecurityRoutes(r)
			})
		})
	})
}

func createTestUser(t *testing.T, email, username, role string) (models.User, string) {
	// Hash password
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte("testpassword"), bcrypt.DefaultCost)
	assert.NoError(t, err)

	user := models.User{
		Email:    email,
		Username: username,
		Password: string(hashedPassword),
		Role:     role,
	}

	err = db.DB.Create(&user).Error
	assert.NoError(t, err)

	// Generate JWT token with role parameter
	token, err := auth.GenerateJWT(user.ID, user.Role)
	assert.NoError(t, err)

	return user, token
}

func TestSecurityAPIEndpoints(t *testing.T) {
	server := setupTestServer(t)
	defer server.Close()

	// Create test admin user
	admin, adminToken := createTestUser(t, "admin@test.com", "admin", "admin")

	t.Run("Generate API Key", func(t *testing.T) {
		payload := map[string]interface{}{
			"vendor_name":  "Test Vendor",
			"email":        "vendor@test.com",
			"access_level": "premium",
			"rate_limit":   1000,
		}

		jsonData, _ := json.Marshal(payload)
		req := httptest.NewRequest("POST", "/api/security/api-keys", bytes.NewBuffer(jsonData))
		req.Header.Set("Authorization", "Bearer "+adminToken)
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Contains(t, response, "api_key")
		assert.Contains(t, response, "id")
	})

	t.Run("List API Keys", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/security/api-keys", nil)
		req.Header.Set("Authorization", "Bearer "+adminToken)

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response []models.DataVendorAPIKey
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.GreaterOrEqual(t, len(response), 1)
	})

	t.Run("Get Security Dashboard", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/security/dashboard", nil)
		req.Header.Set("Authorization", "Bearer "+adminToken)

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Contains(t, response, "alerts")
		assert.Contains(t, response, "api_usage")
	})
}

func TestExportActivityAPIEndpoints(t *testing.T) {
	server := setupTestServer(t)
	defer server.Close()

	// Create test user and building
	user, userToken := createTestUser(t, "user@test.com", "testuser", "user")
	building := models.Building{
		Name:    "Test Building",
		Address: "123 Test St",
		OwnerID: user.ID,
	}
	db.DB.Create(&building)

	t.Run("Create Export Activity", func(t *testing.T) {
		payload := map[string]interface{}{
			"building_id": building.ID,
			"export_type": "asset_inventory",
			"format":      "csv",
			"filters":     `{"system": "electrical"}`,
			"ip_address":  "192.168.1.100",
			"user_agent":  "Test Client/1.0",
		}

		jsonData, _ := json.Marshal(payload)
		req := httptest.NewRequest("POST", "/api/export-activities", bytes.NewBuffer(jsonData))
		req.Header.Set("Authorization", "Bearer "+userToken)
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response models.ExportActivity
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Equal(t, "asset_inventory", response.ExportType)
		assert.Equal(t, "requested", response.Status)
	})

	t.Run("Get Export Activities", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/export-activities", nil)
		req.Header.Set("Authorization", "Bearer "+userToken)

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response []models.ExportActivity
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.GreaterOrEqual(t, len(response), 1)
	})

	t.Run("Get Export Dashboard", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/export-analytics/dashboard", nil)
		req.Header.Set("Authorization", "Bearer "+userToken)

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Contains(t, response, "today_exports")
		assert.Contains(t, response, "week_exports")
		assert.Contains(t, response, "month_exports")
	})
}

func TestComplianceAPIEndpoints(t *testing.T) {
	server := setupTestServer(t)
	defer server.Close()

	// Create test user
	user, userToken := createTestUser(t, "auditor@test.com", "auditor", "auditor")

	t.Run("Get Data Access Logs", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/compliance/data-access-logs", nil)
		req.Header.Set("Authorization", "Bearer "+userToken)

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response []models.DataAccessLog
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		// Response should be an array (even if empty)
		assert.IsType(t, []models.DataAccessLog{}, response)
	})

	t.Run("Get Export Activity Summary", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/compliance/export-activity-summary", nil)
		req.Header.Set("Authorization", "Bearer "+userToken)

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response []map[string]interface{}
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		// Response should be an array
		assert.IsType(t, []map[string]interface{}{}, response)
	})

	t.Run("Get Data Retention Policies", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/compliance/data-retention-policies", nil)
		req.Header.Set("Authorization", "Bearer "+userToken)

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response []models.DataRetentionPolicy
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.IsType(t, []models.DataRetentionPolicy{}, response)
	})

	t.Run("Create Data Retention Policy", func(t *testing.T) {
		payload := map[string]interface{}{
			"object_type":      "test_logs",
			"retention_period": 365,
			"archive_after":    30,
			"delete_after":     365,
			"description":      "Test retention policy",
		}

		jsonData, _ := json.Marshal(payload)
		req := httptest.NewRequest("POST", "/api/compliance/data-retention-policies", bytes.NewBuffer(jsonData))
		req.Header.Set("Authorization", "Bearer "+userToken)
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)

		var response models.DataRetentionPolicy
		err := json.Unmarshal(w.Body.Bytes(), &response)
		assert.NoError(t, err)
		assert.Equal(t, "test_logs", response.ObjectType)
		assert.Equal(t, 365, response.RetentionPeriod)
	})
}

func TestAuthenticationAndAuthorization(t *testing.T) {
	server := setupTestServer(t)
	defer server.Close()

	t.Run("Unauthenticated Access", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/export-activities", nil)
		// No Authorization header

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusUnauthorized, w.Code)
	})

	t.Run("Invalid Token", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/export-activities", nil)
		req.Header.Set("Authorization", "Bearer invalid_token")

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusUnauthorized, w.Code)
	})

	t.Run("Insufficient Role", func(t *testing.T) {
		// Create user with insufficient role
		user, userToken := createTestUser(t, "user@test.com", "user", "user")

		req := httptest.NewRequest("GET", "/api/security/api-keys", nil)
		req.Header.Set("Authorization", "Bearer "+userToken)

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusForbidden, w.Code)
	})
}

func TestRateLimiting(t *testing.T) {
	server := setupTestServer(t)
	defer server.Close()

	user, userToken := createTestUser(t, "ratelimit@test.com", "ratelimit", "user")

	t.Run("Rate Limit Enforcement", func(t *testing.T) {
		// Make multiple requests quickly to trigger rate limiting
		for i := 0; i < 60; i++ { // Exceed the rate limit
			req := httptest.NewRequest("GET", "/api/export-activities", nil)
			req.Header.Set("Authorization", "Bearer "+userToken)

			w := httptest.NewRecorder()
			server.Config.Handler.ServeHTTP(w, req)

			if i < 50 { // Should succeed within rate limit
				assert.Equal(t, http.StatusOK, w.Code)
			} else { // Should be rate limited
				assert.Equal(t, http.StatusTooManyRequests, w.Code)
			}
		}
	})

	t.Run("Rate Limit Headers", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/export-activities", nil)
		req.Header.Set("Authorization", "Bearer "+userToken)

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		// Check for rate limit headers
		assert.NotEmpty(t, w.Header().Get("X-RateLimit-Limit"))
		assert.NotEmpty(t, w.Header().Get("X-RateLimit-Remaining"))
		assert.NotEmpty(t, w.Header().Get("X-RateLimit-Reset"))
	})
}

func TestSecurityHeaders(t *testing.T) {
	server := setupTestServer(t)
	defer server.Close()

	req := httptest.NewRequest("GET", "/api/export-activities", nil)
	w := httptest.NewRecorder()

	server.Config.Handler.ServeHTTP(w, req)

	// Check for security headers
	securityHeaders := []string{
		"X-Content-Type-Options",
		"X-Frame-Options",
		"X-XSS-Protection",
		"Strict-Transport-Security",
		"Content-Security-Policy",
		"Referrer-Policy",
		"Permissions-Policy",
	}

	for _, header := range securityHeaders {
		assert.NotEmpty(t, w.Header().Get(header), "Missing security header: %s", header)
	}
}

func TestDataObfuscation(t *testing.T) {
	server := setupTestServer(t)
	defer server.Close()

	user, userToken := createTestUser(t, "obfuscate@test.com", "obfuscate", "user")

	t.Run("Data Obfuscation Query Parameter", func(t *testing.T) {
		req := httptest.NewRequest("GET", "/api/export-activities?obfuscate=true", nil)
		req.Header.Set("Authorization", "Bearer "+userToken)

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusOK, w.Code)
		// Note: The actual obfuscation would be tested in the middleware tests
	})
}

func TestErrorHandling(t *testing.T) {
	server := setupTestServer(t)
	defer server.Close()

	user, userToken := createTestUser(t, "error@test.com", "error", "user")

	t.Run("Invalid JSON Payload", func(t *testing.T) {
		req := httptest.NewRequest("POST", "/api/export-activities", bytes.NewBufferString("invalid json"))
		req.Header.Set("Authorization", "Bearer "+userToken)
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})

	t.Run("Missing Required Fields", func(t *testing.T) {
		payload := map[string]interface{}{
			"export_type": "asset_inventory",
			// Missing required fields
		}

		jsonData, _ := json.Marshal(payload)
		req := httptest.NewRequest("POST", "/api/export-activities", bytes.NewBuffer(jsonData))
		req.Header.Set("Authorization", "Bearer "+userToken)
		req.Header.Set("Content-Type", "application/json")

		w := httptest.NewRecorder()
		server.Config.Handler.ServeHTTP(w, req)

		assert.Equal(t, http.StatusBadRequest, w.Code)
	})
}

func TestDatabaseCleanup(t *testing.T) {
	// This test ensures proper cleanup after all tests
	t.Run("Cleanup Test Data", func(t *testing.T) {
		db := db.DB

		// Clean up all test data
		db.Exec("DELETE FROM security_alerts")
		db.Exec("DELETE FROM api_key_usage")
		db.Exec("DELETE FROM data_vendor_api_keys")
		db.Exec("DELETE FROM data_vendor_requests")
		db.Exec("DELETE FROM export_activities")
		db.Exec("DELETE FROM audit_logs")
		db.Exec("DELETE FROM data_access_logs")
		db.Exec("DELETE FROM compliance_reports")
		db.Exec("DELETE FROM data_retention_policies")
		db.Exec("DELETE FROM archived_audit_logs")
		db.Exec("DELETE FROM users")
		db.Exec("DELETE FROM buildings")

		// Verify cleanup
		var count int64
		db.Model(&models.User{}).Count(&count)
		assert.Equal(t, int64(0), count)

		db.Model(&models.SecurityAlert{}).Count(&count)
		assert.Equal(t, int64(0), count)
	})
}
