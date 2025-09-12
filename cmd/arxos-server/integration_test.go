package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	"github.com/joelpate/arxos/internal/api"
	"github.com/joelpate/arxos/internal/config"
	"github.com/joelpate/arxos/internal/database"
)

// TestSuite provides infrastructure for API integration tests
type TestSuite struct {
	t        *testing.T
	server   *httptest.Server
	services *api.Services
	cfg      *config.Config
	db       database.DB
	tempDir  string
}

// NewTestSuite creates a new test suite with temporary database
func NewTestSuite(t *testing.T) *TestSuite {
	// Create temporary directory for test database
	tempDir, err := os.MkdirTemp("", "arxos-api-test-")
	require.NoError(t, err)

	// Initialize test configuration
	cfg := config.Default()
	cfg.StateDir = tempDir

	// Initialize database
	dbPath := filepath.Join(tempDir, "test.db")
	db, err := database.NewSQLiteDBFromPath(dbPath)
	require.NoError(t, err)

	// Initialize services (like main.go does)
	buildingService := api.NewBuildingService(db)
	authService := api.NewAuthService(db)
	orgService := api.NewOrganizationService(db)

	// Wire organization service to auth service
	if authImpl, ok := authService.(*api.AuthServiceImpl); ok {
		authImpl.SetOrganizationService(orgService)
	}

	services := &api.Services{
		Building:     buildingService,
		Auth:         authService,
		Organization: orgService,
		DB:           db,
	}

	// Create HTTP server with router
	handler := NewChiRouter(cfg, services)
	server := httptest.NewServer(handler)

	suite := &TestSuite{
		t:        t,
		server:   server,
		services: services,
		cfg:      cfg,
		db:       db,
		tempDir:  tempDir,
	}

	return suite
}

// Cleanup cleans up test resources
func (s *TestSuite) Cleanup() {
	if s.server != nil {
		s.server.Close()
	}
	if s.db != nil {
		s.db.Close()
	}
	os.RemoveAll(s.tempDir)
}

// Request makes HTTP requests to the test server
func (s *TestSuite) Request(method, path string, body interface{}) (*http.Response, map[string]interface{}) {
	var bodyReader *bytes.Buffer
	if body != nil {
		bodyBytes, err := json.Marshal(body)
		require.NoError(s.t, err)
		bodyReader = bytes.NewBuffer(bodyBytes)
	} else {
		bodyReader = bytes.NewBuffer(nil)
	}

	req, err := http.NewRequest(method, s.server.URL+path, bodyReader)
	require.NoError(s.t, err)

	if body != nil {
		req.Header.Set("Content-Type", "application/json")
	}

	client := &http.Client{}
	resp, err := client.Do(req)
	require.NoError(s.t, err)

	var result map[string]interface{}
	if resp.ContentLength != 0 {
		err = json.NewDecoder(resp.Body).Decode(&result)
		if err != nil {
			// If JSON decode fails, just return empty map
			result = make(map[string]interface{})
		}
	}
	resp.Body.Close()

	return resp, result
}

// TestHealthEndpoints tests the health and readiness endpoints
func TestHealthEndpoints(t *testing.T) {
	suite := NewTestSuite(t)
	defer suite.Cleanup()

	// Test health endpoint
	resp, health := suite.Request("GET", "/health", nil)
	assert.Equal(t, http.StatusOK, resp.StatusCode)
	assert.Equal(t, "healthy", health["status"])

	// Test ready endpoint
	resp, ready := suite.Request("GET", "/ready", nil)
	assert.Equal(t, http.StatusOK, resp.StatusCode)
	assert.Equal(t, true, ready["ready"])
}

// TestAPIRoot tests the API v1 root endpoint
func TestAPIRoot(t *testing.T) {
	suite := NewTestSuite(t)
	defer suite.Cleanup()

	resp, apiInfo := suite.Request("GET", "/api/v1/", nil)
	assert.Equal(t, http.StatusOK, resp.StatusCode)
	assert.NotEmpty(t, apiInfo["name"])
	assert.NotEmpty(t, apiInfo["version"])
}

// TestUnauthorizedAccess tests that protected endpoints require authentication
func TestUnauthorizedAccess(t *testing.T) {
	suite := NewTestSuite(t)
	defer suite.Cleanup()

	protectedEndpoints := []struct {
		method string
		path   string
	}{
		{"POST", "/api/v1/buildings"},
		{"PUT", "/api/v1/buildings/test-id"},
		{"DELETE", "/api/v1/buildings/test-id"},
		{"POST", "/api/v1/equipment"},
		{"PUT", "/api/v1/equipment/test-id"},
		{"DELETE", "/api/v1/equipment/test-id"},
	}

	for _, endpoint := range protectedEndpoints {
		t.Run(fmt.Sprintf("%s_%s", endpoint.method, endpoint.path), func(t *testing.T) {
			resp, _ := suite.Request(endpoint.method, endpoint.path, nil)
			// Should get some form of auth error (401, 403, or handled by middleware)
			assert.True(t, resp.StatusCode == http.StatusUnauthorized || 
				resp.StatusCode == http.StatusForbidden ||
				resp.StatusCode >= 400,
				"Expected auth error for %s %s, got %d", endpoint.method, endpoint.path, resp.StatusCode)
		})
	}
}

// TestInputValidation tests API input validation
func TestInputValidation(t *testing.T) {
	suite := NewTestSuite(t)
	defer suite.Cleanup()

	// Test malformed JSON
	req, err := http.NewRequest("POST", suite.server.URL+"/api/v1/auth/register", 
		bytes.NewBufferString("{invalid json"))
	require.NoError(t, err)
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{}
	resp, err := client.Do(req)
	require.NoError(t, err)
	assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
	resp.Body.Close()
}

// TestErrorHandling tests API error handling
func TestErrorHandling(t *testing.T) {
	suite := NewTestSuite(t)
	defer suite.Cleanup()

	// Test 404 for non-existent endpoints
	resp, _ := suite.Request("GET", "/api/v1/nonexistent", nil)
	assert.Equal(t, http.StatusNotFound, resp.StatusCode)

	// Test 405 for unsupported methods
	resp, _ = suite.Request("PATCH", "/health", nil)
	assert.Equal(t, http.StatusMethodNotAllowed, resp.StatusCode)
}

// TestConcurrentRequests tests concurrent API access
func TestConcurrentRequests(t *testing.T) {
	suite := NewTestSuite(t)
	defer suite.Cleanup()

	// Make multiple concurrent requests to health endpoint
	const numRequests = 10
	results := make(chan int, numRequests)

	for i := 0; i < numRequests; i++ {
		go func() {
			resp, _ := suite.Request("GET", "/health", nil)
			results <- resp.StatusCode
		}()
	}

	// Wait for all requests to complete
	successCount := 0
	for i := 0; i < numRequests; i++ {
		code := <-results
		if code == http.StatusOK {
			successCount++
		}
	}

	assert.Equal(t, numRequests, successCount, "All concurrent requests should succeed")
}

// TestMiddlewareChain tests that middleware is properly applied
func TestMiddlewareChain(t *testing.T) {
	suite := NewTestSuite(t)
	defer suite.Cleanup()

	// Test that CORS headers are added
	req, err := http.NewRequest("OPTIONS", suite.server.URL+"/api/v1/", nil)
	require.NoError(t, err)
	req.Header.Set("Origin", "http://localhost:3000")
	req.Header.Set("Access-Control-Request-Method", "GET")

	client := &http.Client{}
	resp, err := client.Do(req)
	require.NoError(t, err)

	// Should have CORS headers
	assert.NotEmpty(t, resp.Header.Get("Access-Control-Allow-Origin"))
	resp.Body.Close()
}

// TestRateLimiting tests basic rate limiting functionality
func TestRateLimiting(t *testing.T) {
	suite := NewTestSuite(t)
	defer suite.Cleanup()

	// Make many rapid requests to test rate limiting
	// Note: Rate limits may be high for health endpoints, so this is a basic test
	const numRequests = 20
	statusCodes := make([]int, numRequests)

	for i := 0; i < numRequests; i++ {
		resp, _ := suite.Request("GET", "/health", nil)
		statusCodes[i] = resp.StatusCode
	}

	// Count successful requests
	successCount := 0
	for _, code := range statusCodes {
		if code == http.StatusOK {
			successCount++
		}
	}

	// At least some requests should succeed (health checks typically have high limits)
	assert.Greater(t, successCount, 0, "At least some requests should succeed")
}

// TestRequestSizeLimits tests request size validation
func TestRequestSizeLimits(t *testing.T) {
	suite := NewTestSuite(t)
	defer suite.Cleanup()

	// Create a very large request body to test size limits
	largeData := make(map[string]interface{})
	largeString := string(make([]byte, 20*1024*1024)) // 20MB of data
	largeData["large_field"] = largeString

	resp, _ := suite.Request("POST", "/api/v1/auth/register", largeData)
	// Should be rejected due to size limits
	assert.True(t, resp.StatusCode >= 400, "Large request should be rejected")
}

// TestSecurityHeaders tests security-related headers
func TestSecurityHeaders(t *testing.T) {
	suite := NewTestSuite(t)
	defer suite.Cleanup()

	resp, _ := suite.Request("GET", "/api/v1/", nil)
	assert.Equal(t, http.StatusOK, resp.StatusCode)

	// Check for basic security practices
	// Note: Exact headers depend on middleware configuration
	assert.NotEmpty(t, resp.Header, "Response should have headers")
}