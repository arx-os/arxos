//go:build integration
// +build integration

package integration

import (
	"bytes"
	"fmt"
	"net/http"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/arx-os/arxos/pkg/models"
)

// TestAPIIntegration tests the complete API integration
func TestAPIIntegration(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	// Setup test environment
	config := setupTestEnvironment(t)
	defer config.cleanupTestEnvironment()

	// Get test users
	users := config.getTestUsers(t)

	t.Run("APIAuthentication", func(t *testing.T) {
		testAPIAuthentication(t, config, users)
	})

	t.Run("APIBuildingCRUD", func(t *testing.T) {
		testAPIBuildingCRUD(t, config, users)
	})

	t.Run("APIEquipmentCRUD", func(t *testing.T) {
		testAPIEquipmentCRUD(t, config, users)
	})

	t.Run("APISpatialQueries", func(t *testing.T) {
		testAPISpatialQueries(t, config, users)
	})

	t.Run("APIErrorHandling", func(t *testing.T) {
		testAPIErrorHandling(t, config, users)
	})

	t.Run("APIVersioning", func(t *testing.T) {
		testAPIVersioning(t, config, users)
	})
}

// testAPIAuthentication tests API authentication
func testAPIAuthentication(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	t.Run("ValidToken", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/buildings", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)
	})

	t.Run("InvalidToken", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/buildings", nil, "invalid_token")
		require.NoError(t, err)
		require.Equal(t, http.StatusUnauthorized, resp.StatusCode)
	})

	t.Run("ExpiredToken", func(t *testing.T) {
		// Create an expired token (this would need to be implemented in the auth service)
		// For now, we'll test with an invalid token
		resp, err := config.makeRequest("GET", "/api/buildings", nil, "expired_token")
		require.NoError(t, err)
		require.Equal(t, http.StatusUnauthorized, resp.StatusCode)
	})

	t.Run("NoToken", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/buildings", nil, "")
		require.NoError(t, err)
		require.Equal(t, http.StatusUnauthorized, resp.StatusCode)
	})
}

// testAPIBuildingCRUD tests building CRUD operations
func testAPIBuildingCRUD(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	var buildingID string

	t.Run("CreateBuilding", func(t *testing.T) {
		building := &models.Building{
			Name:         "API Test Building",
			Address:      "123 API Street",
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

		assert.Equal(t, "API Test Building", result["name"])
		assert.Equal(t, "123 API Street", result["address"])
		assert.Equal(t, "office", result["building_type"])
		assert.Equal(t, float64(5), result["floors"])
		assert.Equal(t, float64(10000.0), result["gross_area"])

		buildingID = result["id"].(string)
		assert.NotEmpty(t, buildingID)
	})

	t.Run("GetBuilding", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/buildings/"+buildingID, nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)

		assert.Equal(t, "API Test Building", result["name"])
		assert.Equal(t, buildingID, result["id"])
	})

	t.Run("UpdateBuilding", func(t *testing.T) {
		updateReq := map[string]interface{}{
			"name":       "Updated API Test Building",
			"floors":     6,
			"gross_area": 12000.0,
		}

		resp, err := config.makeRequest("PUT", "/api/buildings/"+buildingID, updateReq, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)

		assert.Equal(t, "Updated API Test Building", result["name"])
		assert.Equal(t, float64(6), result["floors"])
		assert.Equal(t, float64(12000.0), result["gross_area"])
	})

	t.Run("ListBuildings", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/buildings", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)

		buildings, ok := result["buildings"].([]interface{})
		require.True(t, ok)
		assert.GreaterOrEqual(t, len(buildings), 1)
	})

	t.Run("DeleteBuilding", func(t *testing.T) {
		resp, err := config.makeRequest("DELETE", "/api/buildings/"+buildingID, nil, users["admin"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusNoContent, resp.StatusCode)

		// Verify building is deleted
		resp, err = config.makeRequest("GET", "/api/buildings/"+buildingID, nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusNotFound, resp.StatusCode)
	})
}

// testAPIEquipmentCRUD tests equipment CRUD operations
func testAPIEquipmentCRUD(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	var equipmentID string

	t.Run("CreateEquipment", func(t *testing.T) {
		equipment := &models.Equipment{
			Name:     "API Test HVAC",
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

		assert.Equal(t, "API Test HVAC", result["name"])
		assert.Equal(t, "HVAC", result["type"])
		assert.Equal(t, string(models.StatusOperational), result["status"])

		equipmentID = result["id"].(string)
		assert.NotEmpty(t, equipmentID)
	})

	t.Run("GetEquipment", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/equipment/"+equipmentID, nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)

		assert.Equal(t, "API Test HVAC", result["name"])
		assert.Equal(t, equipmentID, result["id"])
	})

	t.Run("UpdateEquipment", func(t *testing.T) {
		updateReq := map[string]interface{}{
			"name":   "Updated API Test HVAC",
			"status": string(models.StatusFailed),
		}

		resp, err := config.makeRequest("PUT", "/api/equipment/"+equipmentID, updateReq, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)

		assert.Equal(t, "Updated API Test HVAC", result["name"])
		assert.Equal(t, string(models.StatusFailed), result["status"])
	})

	t.Run("ListEquipment", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/equipment", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)

		equipment, ok := result["equipment"].([]interface{})
		require.True(t, ok)
		assert.GreaterOrEqual(t, len(equipment), 1)
	})

	t.Run("DeleteEquipment", func(t *testing.T) {
		resp, err := config.makeRequest("DELETE", "/api/equipment/"+equipmentID, nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusNoContent, resp.StatusCode)

		// Verify equipment is deleted
		resp, err = config.makeRequest("GET", "/api/equipment/"+equipmentID, nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusNotFound, resp.StatusCode)
	})
}

// testAPISpatialQueries tests spatial query endpoints
func testAPISpatialQueries(t *testing.T, config *TestConfig, users map[string]*TestUser) {
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
		assert.NotNil(t, result["query_info"])
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

// testAPIErrorHandling tests API error handling
func testAPIErrorHandling(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	t.Run("NotFound", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/buildings/nonexistent", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusNotFound, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)
		assert.Contains(t, result["error"], "not found")
	})

	t.Run("BadRequest", func(t *testing.T) {
		// Send invalid JSON
		req, err := http.NewRequest("POST", config.Server.URL+"/api/buildings", bytes.NewReader([]byte("invalid json")))
		require.NoError(t, err)
		req.Header.Set("Authorization", "Bearer "+users["user"].Token)
		req.Header.Set("Content-Type", "application/json")

		client := &http.Client{}
		resp, err := client.Do(req)
		require.NoError(t, err)
		require.Equal(t, http.StatusBadRequest, resp.StatusCode)
	})

	t.Run("Unauthorized", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/buildings", nil, "")
		require.NoError(t, err)
		require.Equal(t, http.StatusUnauthorized, resp.StatusCode)
	})

	t.Run("Forbidden", func(t *testing.T) {
		// Try to access admin route with user token
		resp, err := config.makeRequest("GET", "/api/admin/users", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusForbidden, resp.StatusCode)
	})
}

// testAPIVersioning tests API versioning
func testAPIVersioning(t *testing.T, config *TestConfig, users map[string]*TestUser) {
	t.Run("VersionHeader", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/buildings", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		// Check for API version header
		version := resp.Header.Get("X-API-Version")
		assert.NotEmpty(t, version)
	})

	t.Run("VersionInResponse", func(t *testing.T) {
		resp, err := config.makeRequest("GET", "/api/buildings", nil, users["user"].Token)
		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		err = config.parseJSONResponse(resp, &result)
		require.NoError(t, err)

		// Check for version in response metadata
		if meta, ok := result["meta"].(map[string]interface{}); ok {
			assert.NotNil(t, meta["version"])
		}
	})
}

// TestAPIPerformance tests API performance
func TestAPIPerformance(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping performance test in short mode")
	}

	config := setupTestEnvironment(t)
	defer config.cleanupTestEnvironment()

	users := config.getTestUsers(t)

	t.Run("ConcurrentAPIRequests", func(t *testing.T) {
		const numConcurrent = 100
		results := make(chan error, numConcurrent)

		for i := 0; i < numConcurrent; i++ {
			go func(i int) {
				resp, err := config.makeRequest("GET", "/api/buildings", nil, users["user"].Token)
				if err != nil {
					results <- err
					return
				}

				if resp.StatusCode != http.StatusOK {
					results <- fmt.Errorf("expected status 200, got %d", resp.StatusCode)
					return
				}

				results <- nil
			}(i)
		}

		// Wait for all requests to complete
		for i := 0; i < numConcurrent; i++ {
			select {
			case err := <-results:
				require.NoError(t, err)
			case <-time.After(60 * time.Second):
				t.Fatal("Concurrent API requests timed out")
			}
		}
	})

	t.Run("ResponseTime", func(t *testing.T) {
		start := time.Now()
		resp, err := config.makeRequest("GET", "/api/buildings", nil, users["user"].Token)
		duration := time.Since(start)

		require.NoError(t, err)
		require.Equal(t, http.StatusOK, resp.StatusCode)

		// API response should be fast (less than 500ms)
		assert.Less(t, duration, 500*time.Millisecond)
	})
}
