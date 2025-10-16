/**
 * Enhanced API Integration Tests
 * Comprehensive tests for HTTP API endpoints using proper router configuration
 * Tests authentication, authorization, CRUD operations, and error handling
 */

package integration

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/config"
	httpRouter "github.com/arx-os/arxos/internal/interfaces/http"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/pkg/auth"
	"github.com/arx-os/arxos/test/helpers"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// EnhancedAPITestSuite provides comprehensive API testing with proper authentication
type EnhancedAPITestSuite struct {
	app        *app.Container
	config     *config.Config
	server     *httptest.Server
	httpClient *http.Client
	jwtManager *auth.JWTManager
	testUser   *TestUser
}

// TestUser represents a test user for authentication
type TestUser struct {
	ID       string
	Email    string
	Name     string
	Password string
	Token    string
	Role     string
}

// NewEnhancedAPITestSuite creates a new enhanced API test suite
func NewEnhancedAPITestSuite(t *testing.T) *EnhancedAPITestSuite {
	// Load test configuration
	cfg := helpers.LoadTestConfig(t)

	// Create application container
	container := app.NewContainer()
	ctx := context.Background()
	err := container.Initialize(ctx, cfg)
	if err != nil {
		t.Skipf("Cannot initialize container (database may not be available): %v", err)
		return nil
	}

	// Create JWT manager
	jwtConfig := &auth.JWTConfig{
		SecretKey:          cfg.Security.JWTSecret,
		AccessTokenExpiry:  cfg.Security.JWTExpiry,
		RefreshTokenExpiry: 7 * 24 * time.Hour, // 7 days
		Issuer:             "arxos-test",
		Audience:           "arxos-api-test",
		Algorithm:          "HS256",
	}
	jwtManager, err := auth.NewJWTManager(jwtConfig)
	if err != nil {
		t.Skipf("Cannot create JWT manager: %v", err)
		return nil
	}

	// Create HTTP client
	httpClient := &http.Client{
		Timeout: 30 * time.Second,
	}

	// Create test user
	testUser := &TestUser{
		ID:       "test-user-1",
		Email:    "test@arxos.com",
		Name:     "Test User",
		Password: "testpassword123",
		Role:     "admin",
	}

	return &EnhancedAPITestSuite{
		app:        container,
		config:     cfg,
		httpClient: httpClient,
		jwtManager: jwtManager,
		testUser:   testUser,
	}
}

// SetupTestEnvironment prepares the enhanced API test environment
func (suite *EnhancedAPITestSuite) SetupTestEnvironment(t *testing.T) {
	// Create router configuration
	routerConfig := &httpRouter.RouterConfig{
		Server:     &types.Server{},
		Container:  suite.app,
		JWTManager: suite.jwtManager,
	}

	// Create router with full configuration
	router := httpRouter.NewRouter(routerConfig)

	// Create test server
	suite.server = httptest.NewServer(router)

	// Create test user and get token
	suite.createTestUser(t)
	suite.authenticateTestUser(t)
}

// TeardownTestEnvironment cleans up the enhanced API test environment
func (suite *EnhancedAPITestSuite) TeardownTestEnvironment(t *testing.T) {
	if suite.server != nil {
		suite.server.Close()
	}
}

// createTestUser creates a test user in the system
func (suite *EnhancedAPITestSuite) createTestUser(t *testing.T) {
	// This would typically create a user via the user use case
	// For now, we'll simulate this by creating a token directly
	suite.testUser.Token = suite.generateTestToken(t)
}

// authenticateTestUser authenticates the test user and gets a token
func (suite *EnhancedAPITestSuite) authenticateTestUser(t *testing.T) {
	// Generate a test token for the user
	suite.testUser.Token = suite.generateTestToken(t)
}

// generateTestToken generates a JWT token for testing
func (suite *EnhancedAPITestSuite) generateTestToken(t *testing.T) string {
	tokenPair, err := suite.jwtManager.GenerateTokenPair(
		suite.testUser.ID,
		suite.testUser.Email,
		suite.testUser.Name,
		suite.testUser.Role,
		"",                               // organizationID
		[]string{"read", "write"},        // permissions
		"test-session",                   // sessionID
		map[string]any{"device": "test"}, // deviceInfo
	)
	require.NoError(t, err)
	return tokenPair.AccessToken
}

// makeAuthenticatedRequest makes an authenticated HTTP request
func (suite *EnhancedAPITestSuite) makeAuthenticatedRequest(method, url string, body []byte) (*http.Response, error) {
	req, err := http.NewRequest(method, url, bytes.NewBuffer(body))
	if err != nil {
		return nil, err
	}

	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+suite.testUser.Token)

	return suite.httpClient.Do(req)
}

// TestBuildingAPI tests building-related API endpoints
func TestBuildingAPI(t *testing.T) {
	suite := NewEnhancedAPITestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("CreateBuilding", func(t *testing.T) {
		reqBody := map[string]any{
			"name":          "API Test Building",
			"address":       "123 API Street",
			"city":          "Test City",
			"state":         "TS",
			"zip_code":      "12345",
			"country":       "Test Country",
			"building_type": "office",
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		resp, err := suite.makeAuthenticatedRequest("POST", suite.server.URL+"/api/v1/buildings", jsonBody)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusCreated, resp.StatusCode)

		var response map[string]any
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.NotNil(t, response["id"])
		assert.Equal(t, "API Test Building", response["name"])
		assert.Equal(t, "123 API Street", response["address"])
	})

	t.Run("GetBuilding", func(t *testing.T) {
		// First create a building
		reqBody := map[string]any{
			"name":          "Get Test Building",
			"address":       "456 Get Street",
			"city":          "Test City",
			"state":         "TS",
			"zip_code":      "12345",
			"country":       "Test Country",
			"building_type": "office",
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		createResp, err := suite.makeAuthenticatedRequest("POST", suite.server.URL+"/api/v1/buildings", jsonBody)
		require.NoError(t, err)
		defer createResp.Body.Close()

		var createResponse map[string]any
		err = json.NewDecoder(createResp.Body).Decode(&createResponse)
		require.NoError(t, err)

		buildingID := createResponse["id"].(string)

		// Now get the building
		resp, err := suite.makeAuthenticatedRequest("GET", suite.server.URL+"/api/v1/buildings/"+buildingID, nil)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]any
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.Equal(t, buildingID, response["id"])
		assert.Equal(t, "Get Test Building", response["name"])
	})

	t.Run("ListBuildings", func(t *testing.T) {
		// Create multiple buildings
		for i := 0; i < 3; i++ {
			reqBody := map[string]any{
				"name":          fmt.Sprintf("List Test Building %d", i+1),
				"address":       fmt.Sprintf("%d List Street", 100+i),
				"city":          "Test City",
				"state":         "TS",
				"zip_code":      "12345",
				"country":       "Test Country",
				"building_type": "office",
			}

			jsonBody, err := json.Marshal(reqBody)
			require.NoError(t, err)

			resp, err := suite.makeAuthenticatedRequest("POST", suite.server.URL+"/api/v1/buildings", jsonBody)
			require.NoError(t, err)
			resp.Body.Close()
		}

		// List buildings
		resp, err := suite.makeAuthenticatedRequest("GET", suite.server.URL+"/api/v1/buildings", nil)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]any
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		buildings := response["buildings"].([]any)
		assert.GreaterOrEqual(t, len(buildings), 3)
	})

	t.Run("UpdateBuilding", func(t *testing.T) {
		// First create a building
		reqBody := map[string]any{
			"name":          "Update Test Building",
			"address":       "789 Update Street",
			"city":          "Test City",
			"state":         "TS",
			"zip_code":      "12345",
			"country":       "Test Country",
			"building_type": "office",
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		createResp, err := suite.makeAuthenticatedRequest("POST", suite.server.URL+"/api/v1/buildings", jsonBody)
		require.NoError(t, err)
		defer createResp.Body.Close()

		var createResponse map[string]any
		err = json.NewDecoder(createResp.Body).Decode(&createResponse)
		require.NoError(t, err)

		buildingID := createResponse["id"].(string)

		// Update the building
		updateBody := map[string]any{
			"name":    "Updated Test Building",
			"address": "999 Updated Street",
		}

		updateJsonBody, err := json.Marshal(updateBody)
		require.NoError(t, err)

		resp, err := suite.makeAuthenticatedRequest("PUT", suite.server.URL+"/api/v1/buildings/"+buildingID, updateJsonBody)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]any
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.Equal(t, "Updated Test Building", response["name"])
		assert.Equal(t, "999 Updated Street", response["address"])
	})

	t.Run("DeleteBuilding", func(t *testing.T) {
		// First create a building
		reqBody := map[string]any{
			"name":          "Delete Test Building",
			"address":       "111 Delete Street",
			"city":          "Test City",
			"state":         "TS",
			"zip_code":      "12345",
			"country":       "Test Country",
			"building_type": "office",
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		createResp, err := suite.makeAuthenticatedRequest("POST", suite.server.URL+"/api/v1/buildings", jsonBody)
		require.NoError(t, err)
		defer createResp.Body.Close()

		var createResponse map[string]any
		err = json.NewDecoder(createResp.Body).Decode(&createResponse)
		require.NoError(t, err)

		buildingID := createResponse["id"].(string)

		// Delete the building
		resp, err := suite.makeAuthenticatedRequest("DELETE", suite.server.URL+"/api/v1/buildings/"+buildingID, nil)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		// Verify building is deleted
		getResp, err := suite.makeAuthenticatedRequest("GET", suite.server.URL+"/api/v1/buildings/"+buildingID, nil)
		require.NoError(t, err)
		defer getResp.Body.Close()

		assert.Equal(t, http.StatusNotFound, getResp.StatusCode)
	})
}

// TestEquipmentAPI tests equipment-related API endpoints
func TestEquipmentAPI(t *testing.T) {
	suite := NewEnhancedAPITestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	var buildingID string

	// Setup: Create a building first
	t.Run("SetupBuilding", func(t *testing.T) {
		reqBody := map[string]any{
			"name":          "Equipment Test Building",
			"address":       "123 Equipment Street",
			"city":          "Test City",
			"state":         "TS",
			"zip_code":      "12345",
			"country":       "Test Country",
			"building_type": "office",
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		resp, err := suite.makeAuthenticatedRequest("POST", suite.server.URL+"/api/v1/buildings", jsonBody)
		require.NoError(t, err)
		defer resp.Body.Close()

		var response map[string]any
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		buildingID = response["id"].(string)
	})

	t.Run("CreateEquipment", func(t *testing.T) {
		reqBody := map[string]any{
			"building_id": buildingID,
			"name":        "API Test Equipment",
			"type":        "HVAC",
			"model":       "Test Model 3000",
			"location": map[string]float64{
				"x": 40.7128,
				"y": -74.0060,
				"z": 5,
			},
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		resp, err := suite.makeAuthenticatedRequest("POST", suite.server.URL+"/api/v1/equipment", jsonBody)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusCreated, resp.StatusCode)

		var response map[string]any
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.NotNil(t, response["id"])
		assert.Equal(t, "API Test Equipment", response["name"])
		assert.Equal(t, "HVAC", response["type"])
		assert.Equal(t, buildingID, response["building_id"])
	})

	t.Run("GetEquipmentByPath", func(t *testing.T) {
		// Test path-based equipment query
		path := "/B1/F1/R1/HVAC/EQUIP-01"

		resp, err := suite.makeAuthenticatedRequest("GET", suite.server.URL+"/api/v1/equipment/path/"+path, nil)
		require.NoError(t, err)
		defer resp.Body.Close()

		// Should return 404 for non-existent path or 200 with equipment data
		assert.True(t, resp.StatusCode == http.StatusOK || resp.StatusCode == http.StatusNotFound)
	})

	t.Run("FindEquipmentByPathPattern", func(t *testing.T) {
		// Test wildcard path query
		pattern := "/B1/F1/*/HVAC/*"

		resp, err := suite.makeAuthenticatedRequest("GET", suite.server.URL+"/api/v1/equipment/path-pattern?pattern="+pattern, nil)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]any
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.NotNil(t, response["equipment"])
	})
}

// TestBASAPI tests BAS (Building Automation System) API endpoints
func TestBASAPI(t *testing.T) {
	suite := NewEnhancedAPITestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("ListBASSystems", func(t *testing.T) {
		resp, err := suite.makeAuthenticatedRequest("GET", suite.server.URL+"/api/v1/bas/systems", nil)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]any
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.NotNil(t, response["systems"])
	})

	t.Run("ListBASPoints", func(t *testing.T) {
		resp, err := suite.makeAuthenticatedRequest("GET", suite.server.URL+"/api/v1/bas/points", nil)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]any
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.NotNil(t, response["points"])
	})

	t.Run("GetBASPointByPath", func(t *testing.T) {
		path := "/B1/F1/R1/HVAC/TEMP-01"

		resp, err := suite.makeAuthenticatedRequest("GET", suite.server.URL+"/api/v1/bas/points/path/"+path, nil)
		require.NoError(t, err)
		defer resp.Body.Close()

		// Should return 404 for non-existent path or 200 with point data
		assert.True(t, resp.StatusCode == http.StatusOK || resp.StatusCode == http.StatusNotFound)
	})
}

// TestAuthenticationAndAuthorization tests authentication and authorization
func TestAuthenticationAndAuthorization(t *testing.T) {
	suite := NewEnhancedAPITestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("UnauthorizedAccess", func(t *testing.T) {
		// Make request without authentication
		resp, err := suite.httpClient.Get(suite.server.URL + "/api/v1/buildings")
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusUnauthorized, resp.StatusCode)
	})

	t.Run("InvalidToken", func(t *testing.T) {
		// Make request with invalid token
		req, err := http.NewRequest("GET", suite.server.URL+"/api/v1/buildings", nil)
		require.NoError(t, err)
		req.Header.Set("Authorization", "Bearer invalid-token")

		resp, err := suite.httpClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusUnauthorized, resp.StatusCode)
	})

	t.Run("ValidToken", func(t *testing.T) {
		// Make request with valid token
		resp, err := suite.makeAuthenticatedRequest("GET", suite.server.URL+"/api/v1/buildings", nil)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)
	})
}

// TestErrorHandling tests API error handling
func TestErrorHandling(t *testing.T) {
	suite := NewEnhancedAPITestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("InvalidJSON", func(t *testing.T) {
		resp, err := suite.makeAuthenticatedRequest("POST", suite.server.URL+"/api/v1/buildings", []byte("invalid json"))
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
	})

	t.Run("MissingRequiredFields", func(t *testing.T) {
		reqBody := map[string]any{
			"address": "Missing Name Street",
		}

		jsonBody, err := json.Marshal(reqBody)
		require.NoError(t, err)

		resp, err := suite.makeAuthenticatedRequest("POST", suite.server.URL+"/api/v1/buildings", jsonBody)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
	})

	t.Run("NonExistentResource", func(t *testing.T) {
		resp, err := suite.makeAuthenticatedRequest("GET", suite.server.URL+"/api/v1/buildings/non-existent-id", nil)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusNotFound, resp.StatusCode)
	})

	t.Run("InvalidResourceID", func(t *testing.T) {
		resp, err := suite.makeAuthenticatedRequest("GET", suite.server.URL+"/api/v1/buildings/invalid-id", nil)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
	})
}

// TestHealthEndpoint tests the health endpoint
func TestHealthEndpoint(t *testing.T) {
	suite := NewEnhancedAPITestSuite(t)
	if suite == nil {
		t.Skip("Test suite initialization failed")
		return
	}

	suite.SetupTestEnvironment(t)
	defer suite.TeardownTestEnvironment(t)

	t.Run("HealthCheck", func(t *testing.T) {
		resp, err := suite.httpClient.Get(suite.server.URL + "/health")
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var response map[string]any
		err = json.NewDecoder(resp.Body).Decode(&response)
		require.NoError(t, err)

		assert.Equal(t, "healthy", response["status"])
		assert.NotNil(t, response["version"])
		assert.NotNil(t, response["timestamp"])
	})
}
