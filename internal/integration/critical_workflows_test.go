//go:build integration
// +build integration

package integration

import (
	"fmt"
	"net/http"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/arx-os/arxos/pkg/models"
)

// TestCriticalWorkflows tests the most critical workflows in the system
func TestCriticalWorkflows(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	// Setup test environment
	config := setupTestEnvironment(t)
	defer config.cleanupTestEnvironment()

	// Get test users
	users := config.getTestUsers(t)

	t.Run("AuthenticationWorkflow", func(t *testing.T) {
		testAuthenticationWorkflow(t, config, users)
	})

	t.Run("BuildingManagementWorkflow", func(t *testing.T) {
		testBuildingManagementWorkflow(t, config, users)
	})

	t.Run("EquipmentManagementWorkflow", func(t *testing.T) {
		testEquipmentManagementWorkflow(t, config, users)
	})

	t.Run("SpatialQueryWorkflow", func(t *testing.T) {
		testSpatialQueryWorkflow(t, config, users)
	})

	t.Run("FileImportExportWorkflow", func(t *testing.T) {
		testFileImportExportWorkflow(t, config, users)
	})

	t.Run("RoleBasedAccessControl", func(t *testing.T) {
		testRoleBasedAccessControl(t, config, users)
	})

	t.Run("ConcurrentOperations", func(t *testing.T) {
		testConcurrentOperations(t, config, users)
	})
}

// testAuthenticationWorkflow tests the complete authentication flow
func testAuthenticationWorkflow(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	t.Run("UserRegistration", func(t *testing.T) {
		// Test user registration
		registerReq := map[string]string{
			"email":    "newuser@arxos.io",
			"password": "new_password",
			"name":     "New User",
		}

		resp, err := config.makeRequest("POST", "/api/auth/register", registerReq, "")
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var registerResp map[string]interface{}
		err = config.parseJSONResponse(resp, &registerResp)
		require.NoError(t, err)
		assert.NotEmpty(t, registerResp["token"])
		assert.NotEmpty(t, registerResp["user"])
	})

	t.Run("UserLogin", func(t *testing.T) {
		// Test user login
		loginReq := map[string]string{
			"email":    "test@arxos.io",
			"password": "test_password",
		}

		resp, err := config.makeRequest("POST", "/api/auth/login", loginReq, "")
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var loginResp map[string]interface{}
		err = config.parseJSONResponse(resp, &loginResp)
		require.NoError(t, err)
		assert.NotEmpty(t, loginResp["token"])
		assert.NotEmpty(t, loginResp["expires_at"])
		assert.NotNil(t, loginResp["user"])
	})

	t.Run("InvalidCredentials", func(t *testing.T) {
		// Test invalid credentials
		loginReq := map[string]string{
			"email":    "test@arxos.io",
			"password": "wrong_password",
		}

		resp, err := config.makeRequest("POST", "/api/auth/login", loginReq, "")
		require.NoError(t, err)
		require.Equal(t, http.StatusUnauthorized, resp.StatusCode)
	})

	t.Run("PasswordReset", func(t *testing.T) {
		// Test password reset request
		forgotReq := map[string]string{
			"email": "test@arxos.io",
		}

		resp, err := config.makeRequest("POST", "/api/auth/forgot-password", forgotReq, "")
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var forgotResp map[string]interface{}
		err = config.parseJSONResponse(resp, &forgotResp)
		require.NoError(t, err)
		assert.Contains(t, forgotResp["message"], "password reset link has been sent")
	})

	t.Run("UserLogout", func(t *testing.T) {
		// Test user logout
		resp, err := config.makeRequest("POST", "/api/auth/logout", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusNoContent, resp.StatusCode)
	})
}

// testBuildingManagementWorkflow tests building creation and management
func testBuildingManagementWorkflow(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	var buildingID string

	t.Run("CreateBuilding", func(t *testing.T) {
		building := &models.Building{
			Name:         "Test Building",
			Address:      "123 Test Street",
			City:         "Test City",
			Country:      "Test Country",
			PostalCode:   "12345",
			BuildingType: "office",
			Floors:       5,
			GrossArea:    10000.0,
		}

		resp, err := config.makeRequest("POST", "/api/buildings", building, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusCreated, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)

		if data, ok := result["data"].(map[string]interface{}); ok {
			buildingID = data["id"].(string)
		}
		assert.NotEmpty(t, buildingID)
	})

	t.Run("GetBuilding", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/buildings/"+buildingID, nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)
		assert.Equal(t, "Test Building", result["name"])
	})

	t.Run("UpdateBuilding", func(t *testing.T) {
		updateReq := map[string]interface{}{
			"name":       "Updated Test Building",
			"floors":     6,
			"gross_area": 12000.0,
		}

		resp, err := config.makeRequest("PUT", "/api/buildings/"+buildingID, updateReq, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)
		assert.Equal(t, "Updated Test Building", result["name"])
	})

	t.Run("ListBuildings", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/buildings", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)
		assert.NotNil(t, result["buildings"])
	})

	t.Run("DeleteBuilding", func(t *testing.T) {
		resp, err := config.makeRequest("DELETE", "/api/buildings/"+buildingID, nil, users["admin"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusNoContent, resp.StatusCode)
	})
}

// testEquipmentManagementWorkflow tests equipment management
func testEquipmentManagementWorkflow(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	// First create a building
	building := &models.Building{
		Name:         "Equipment Test Building",
		Address:      "456 Equipment Street",
		City:         "Test City",
		Country:      "Test Country",
		PostalCode:   "54321",
		BuildingType: "office",
		Floors:       3,
		GrossArea:    5000.0,
	}

	resp, err := config.makeRequest("POST", "/api/buildings", building, users["user"].Token)
	require.NoError(t, err)
	require.Equal(t, http.StatusCreated, resp.StatusCode)

	var buildingResult map[string]interface{}
	err = config.parseJSONResponse(resp, &buildingResult)
	require.NoError(t, err)

	buildingID := buildingResult["data"].(map[string]interface{})["id"].(string)

	t.Run("CreateEquipment", func(t *testing.T) {
		equipment := &models.Equipment{
			Name:     "Test HVAC Unit",
			Type:     "HVAC",
			Location: &models.Point3D{X: 10.0, Y: 20.0, Z: 0.0},
			Status:   models.StatusOperational,
		}

		resp, err := config.makeRequest("POST", "/api/equipment", equipment, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusCreated, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)
		assert.Equal(t, "Test HVAC Unit", result["name"])
	})

	t.Run("ListEquipment", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/equipment", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)
		assert.NotNil(t, result["equipment"])
	})
}

// testSpatialQueryWorkflow tests spatial queries
func testSpatialQueryWorkflow(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	t.Run("SpatialQuery", func(t *testing.T) {
		queryReq := map[string]interface{}{
			"query_type": "proximity",
			"center": map[string]float64{
				"x": 10.0,
				"y": 20.0,
			},
			"radius": 100.0,
		}

		resp, err := config.makeRequest("POST", "/api/spatial/query", queryReq, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)
		assert.NotNil(t, result["results"])
	})

	t.Run("ProximitySearch", func(t *testing.T) {
		params := "?x=10&y=20&radius=100"
		resp, err := config.makeRequest("GET", "/api/spatial/proximity"+params, nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)
		assert.NotNil(t, result["results"])
	})
}

// testFileImportExportWorkflow tests file import/export
func testFileImportExportWorkflow(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	t.Run("ExportBIM", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/export/bim", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		// Check that we get a file response
		assert.Equal(t, "application/octet-stream", resp.Header.Get("Content-Type"))
		assert.NotEmpty(t, resp.Header.Get("Content-Disposition"))
	})
}

// testRoleBasedAccessControl tests role-based access control
func testRoleBasedAccessControl(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	t.Run("UserCannotAccessAdminRoutes", func(t *testing.T) {
		// Try to access admin-only route with user token
		resp, err := config.makeRequest("GET", "/api/admin/users", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusForbidden, resp.StatusCode)
	})

	t.Run("AdminCanAccessAdminRoutes", func(t *testing.T) {
		// Try to access admin-only route with admin token
		resp, err := config.makeRequest("GET", "/api/admin/users", nil, users["admin"].Token)
		require.NoError(t, err)
		// This might return 404 if the route doesn't exist, but not 403
		assert.NotEqual(t, http.StatusForbidden, resp.StatusCode)
	})

	t.Run("ManagerCanAccessManagerRoutes", func(t *testing.T) {
		// Try to access manager routes with manager token
		resp, err := config.makeRequest("GET", "/api/buildings", nil, users["manager"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)
	})
}

// testConcurrentOperations tests concurrent operations
func testConcurrentOperations(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	t.Run("ConcurrentBuildingCreation", func(t *testing.T) {
		const numConcurrent = 10
		results := make(chan error, numConcurrent)

		for i := 0; i < numConcurrent; i++ {
			go func(i int) {
				building := &models.Building{
					Name:         fmt.Sprintf("Concurrent Building %d", i),
					Address:      fmt.Sprintf("Address %d", i),
					City:         "Test City",
					Country:      "Test Country",
					PostalCode:   "12345",
					BuildingType: "office",
					Floors:       1,
					GrossArea:    1000.0,
				}

				resp, err := config.makeRequest("POST", "/api/buildings", building, users["user"].Token)
				if err != nil {
					results <- err
					return
				}

				if resp.StatusCode != http.StatusCreated {
					results <- fmt.Errorf("expected status 201, got %d", resp.StatusCode)
					return
				}

				results <- nil
			}(i)
		}

		// Wait for all operations to complete
		for i := 0; i < numConcurrent; i++ {
			select {
			case err := <-results:
				require.NoError(t, err)
			case <-time.After(30 * time.Second):
				t.Fatal("Concurrent operations timed out")
			}
		}
	})
}
