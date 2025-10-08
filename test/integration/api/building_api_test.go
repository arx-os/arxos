package integration

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	httpRouter "github.com/arx-os/arxos/internal/interfaces/http"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// setupTestServer creates a test server with in-memory dependencies
func setupTestServer(t *testing.T) (*httptest.Server, *app.Container) {
	t.Helper()

	// Load test configuration
	cfg := &config.Config{
		Mode: "test",
		PostGIS: config.PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos_test",
			User:     "arxos_test",
			Password: "test_password",
			SSLMode:  "disable",
		},
		Security: config.SecurityConfig{
			JWTSecret: "test-secret-key-for-testing-only",
			JWTExpiry: 24 * time.Hour,
		},
		Database: config.DatabaseConfig{
			MaxOpenConns: 10,
			MaxIdleConns: 5,
			ConnLifetime: 5 * time.Minute,
		},
	}

	// Initialize container
	container := app.NewContainer()
	err := container.Initialize(context.Background(), cfg)
	if err != nil {
		t.Skipf("Cannot initialize container (database may not be available): %v", err)
		return nil, nil
	}

	// Create router config
	routerConfig := &httpRouter.RouterConfig{
		Container: container,
	}
	r := httpRouter.NewRouter(routerConfig)

	// Create test server
	server := httptest.NewServer(r)

	return server, container
}

func TestBuildingAPI_EndToEnd(t *testing.T) {
	server, container := setupTestServer(t)
	if server == nil {
		return
	}
	defer server.Close()
	defer container.Shutdown(context.Background())

	// Test 1: Create a building
	t.Run("CreateBuilding", func(t *testing.T) {
		createReq := domain.CreateBuildingRequest{
			Name:    "Test Building API",
			Address: "123 API Test Street",
			Coordinates: &domain.Location{
				X: -122.4194,
				Y: 37.7749,
				Z: 0,
			},
		}

		body, err := json.Marshal(createReq)
		require.NoError(t, err)

		req, err := http.NewRequest("POST", server.URL+"/api/v1/buildings", bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusCreated, resp.StatusCode)

		var building domain.Building
		err = json.NewDecoder(resp.Body).Decode(&building)
		require.NoError(t, err)

		assert.Equal(t, createReq.Name, building.Name)
		assert.Equal(t, createReq.Address, building.Address)
		assert.NotEmpty(t, building.ID)
	})

	// Test 2: List buildings
	t.Run("ListBuildings", func(t *testing.T) {
		req, err := http.NewRequest("GET", server.URL+"/api/v1/buildings?limit=10&offset=0", nil)
		require.NoError(t, err)

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]any
		err = json.NewDecoder(resp.Body).Decode(&result)
		require.NoError(t, err)

		assert.Contains(t, result, "buildings")
		buildings := result["buildings"].([]any)
		assert.GreaterOrEqual(t, len(buildings), 1)
	})

	// Test 3: Get building by ID (using a known building from list)
	t.Run("GetBuilding", func(t *testing.T) {
		// First create a building to get
		createReq := domain.CreateBuildingRequest{
			Name:    "Test Building Get",
			Address: "456 Get Test Street",
		}

		body, err := json.Marshal(createReq)
		require.NoError(t, err)

		createReqHTTP, err := http.NewRequest("POST", server.URL+"/api/v1/buildings", bytes.NewBuffer(body))
		require.NoError(t, err)
		createReqHTTP.Header.Set("Content-Type", "application/json")

		createResp, err := http.DefaultClient.Do(createReqHTTP)
		require.NoError(t, err)
		defer createResp.Body.Close()

		var createdBuilding domain.Building
		err = json.NewDecoder(createResp.Body).Decode(&createdBuilding)
		require.NoError(t, err)

		// Now get it
		getReq, err := http.NewRequest("GET", server.URL+"/api/v1/buildings/"+createdBuilding.ID.String(), nil)
		require.NoError(t, err)

		getResp, err := http.DefaultClient.Do(getReq)
		require.NoError(t, err)
		defer getResp.Body.Close()

		assert.Equal(t, http.StatusOK, getResp.StatusCode)

		var building domain.Building
		err = json.NewDecoder(getResp.Body).Decode(&building)
		require.NoError(t, err)

		assert.Equal(t, createdBuilding.ID.String(), building.ID.String())
		assert.Equal(t, createReq.Name, building.Name)
	})

	// Test 4: Update building
	t.Run("UpdateBuilding", func(t *testing.T) {
		// First create a building
		createReq := domain.CreateBuildingRequest{
			Name:    "Test Building Update",
			Address: "789 Update Test Street",
		}

		body, err := json.Marshal(createReq)
		require.NoError(t, err)

		createReqHTTP, err := http.NewRequest("POST", server.URL+"/api/v1/buildings", bytes.NewBuffer(body))
		require.NoError(t, err)
		createReqHTTP.Header.Set("Content-Type", "application/json")

		createResp, err := http.DefaultClient.Do(createReqHTTP)
		require.NoError(t, err)
		defer createResp.Body.Close()

		var createdBuilding domain.Building
		err = json.NewDecoder(createResp.Body).Decode(&createdBuilding)
		require.NoError(t, err)

		// Now update it
		updatedName := "Updated Building Name"
		updateReq := domain.UpdateBuildingRequest{
			ID:   types.FromString(createdBuilding.ID.String()),
			Name: &updatedName,
		}

		body, err = json.Marshal(updateReq)
		require.NoError(t, err)

		putReq, err := http.NewRequest("PUT", server.URL+"/api/v1/buildings/"+createdBuilding.ID.String(), bytes.NewBuffer(body))
		require.NoError(t, err)
		putReq.Header.Set("Content-Type", "application/json")

		putResp, err := http.DefaultClient.Do(putReq)
		require.NoError(t, err)
		defer putResp.Body.Close()

		assert.Equal(t, http.StatusOK, putResp.StatusCode)

		var updatedBuilding domain.Building
		err = json.NewDecoder(putResp.Body).Decode(&updatedBuilding)
		require.NoError(t, err)

		assert.Equal(t, updatedName, updatedBuilding.Name)
	})

	// Test 5: Delete building
	t.Run("DeleteBuilding", func(t *testing.T) {
		// First create a building
		createReq := domain.CreateBuildingRequest{
			Name:    "Test Building Delete",
			Address: "999 Delete Test Street",
		}

		body, err := json.Marshal(createReq)
		require.NoError(t, err)

		createReqHTTP, err := http.NewRequest("POST", server.URL+"/api/v1/buildings", bytes.NewBuffer(body))
		require.NoError(t, err)
		createReqHTTP.Header.Set("Content-Type", "application/json")

		createResp, err := http.DefaultClient.Do(createReqHTTP)
		require.NoError(t, err)
		defer createResp.Body.Close()

		var createdBuilding domain.Building
		err = json.NewDecoder(createResp.Body).Decode(&createdBuilding)
		require.NoError(t, err)

		// Now delete it
		deleteReq, err := http.NewRequest("DELETE", server.URL+"/api/v1/buildings/"+createdBuilding.ID.String(), nil)
		require.NoError(t, err)

		deleteResp, err := http.DefaultClient.Do(deleteReq)
		require.NoError(t, err)
		defer deleteResp.Body.Close()

		assert.Equal(t, http.StatusNoContent, deleteResp.StatusCode)

		// Verify it's deleted
		getReq, err := http.NewRequest("GET", server.URL+"/api/v1/buildings/"+createdBuilding.ID.String(), nil)
		require.NoError(t, err)

		getResp, err := http.DefaultClient.Do(getReq)
		require.NoError(t, err)
		defer getResp.Body.Close()

		assert.Equal(t, http.StatusInternalServerError, getResp.StatusCode) // Should fail to find
	})
}

func TestBuildingAPI_Validation(t *testing.T) {
	server, container := setupTestServer(t)
	if server == nil {
		return
	}
	defer server.Close()
	defer container.Shutdown(context.Background())

	t.Run("CreateBuilding_MissingName", func(t *testing.T) {
		createReq := domain.CreateBuildingRequest{
			Address: "Missing Name Street",
		}

		body, err := json.Marshal(createReq)
		require.NoError(t, err)

		req, err := http.NewRequest("POST", server.URL+"/api/v1/buildings", bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
	})

	t.Run("CreateBuilding_MissingAddress", func(t *testing.T) {
		createReq := domain.CreateBuildingRequest{
			Name: "No Address Building",
		}

		body, err := json.Marshal(createReq)
		require.NoError(t, err)

		req, err := http.NewRequest("POST", server.URL+"/api/v1/buildings", bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
	})
}

func TestBuildingAPI_ErrorCases(t *testing.T) {
	server, container := setupTestServer(t)
	if server == nil {
		return
	}
	defer server.Close()
	defer container.Shutdown(context.Background())

	t.Run("GetBuilding_NotFound", func(t *testing.T) {
		req, err := http.NewRequest("GET", server.URL+"/api/v1/buildings/non-existent-id", nil)
		require.NoError(t, err)

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusInternalServerError, resp.StatusCode)
	})

	t.Run("UpdateBuilding_NotFound", func(t *testing.T) {
		updatedName := "Updated Name"
		updateReq := domain.UpdateBuildingRequest{
			ID:   types.FromString("non-existent-id"),
			Name: &updatedName,
		}

		body, err := json.Marshal(updateReq)
		require.NoError(t, err)

		req, err := http.NewRequest("PUT", server.URL+"/api/v1/buildings/non-existent-id", bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusInternalServerError, resp.StatusCode)
	})
}
