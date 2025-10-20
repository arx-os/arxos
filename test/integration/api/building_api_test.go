package integration

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
)

func TestBuildingAPI_EndToEnd(t *testing.T) {
	WithTestServer(t, func(t *testing.T, server *httptest.Server, auth *TestAuthHelper, container *app.Container) {
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

			resp := auth.POST(t, "/api/v1/buildings", createReq)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusCreated, resp.StatusCode)

			var building domain.Building
			auth.DecodeJSON(t, resp, &building)

			assert.Equal(t, createReq.Name, building.Name)
			assert.Equal(t, createReq.Address, building.Address)
			assert.NotEmpty(t, building.ID)
		})

		// Test 2: List buildings
		t.Run("ListBuildings", func(t *testing.T) {
			resp := auth.GET(t, "/api/v1/buildings?limit=10&offset=0")
			defer resp.Body.Close()

			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var result map[string]any
			auth.DecodeJSON(t, resp, &result)

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

			createResp := auth.POST(t, "/api/v1/buildings", createReq)
			defer createResp.Body.Close()

			var createdBuilding domain.Building
			auth.DecodeJSON(t, createResp, &createdBuilding)

			// Now get it
			getResp := auth.GET(t, "/api/v1/buildings/"+createdBuilding.ID.String())
			defer getResp.Body.Close()

			assert.Equal(t, http.StatusOK, getResp.StatusCode)

			var building domain.Building
			auth.DecodeJSON(t, getResp, &building)

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

			createResp := auth.POST(t, "/api/v1/buildings", createReq)
			defer createResp.Body.Close()

			var createdBuilding domain.Building
			auth.DecodeJSON(t, createResp, &createdBuilding)

			// Now update it
			updatedName := "Updated Building Name"
			updateReq := domain.UpdateBuildingRequest{
				ID:   types.FromString(createdBuilding.ID.String()),
				Name: &updatedName,
			}

			putResp := auth.PUT(t, "/api/v1/buildings/"+createdBuilding.ID.String(), updateReq)
			defer putResp.Body.Close()

			assert.Equal(t, http.StatusOK, putResp.StatusCode)

			var updatedBuilding domain.Building
			auth.DecodeJSON(t, putResp, &updatedBuilding)

			assert.Equal(t, updatedName, updatedBuilding.Name)
		})

		// Test 5: Delete building
		t.Run("DeleteBuilding", func(t *testing.T) {
			// First create a building
			createReq := domain.CreateBuildingRequest{
				Name:    "Test Building Delete",
				Address: "999 Delete Test Street",
			}

			createResp := auth.POST(t, "/api/v1/buildings", createReq)
			defer createResp.Body.Close()

			var createdBuilding domain.Building
			auth.DecodeJSON(t, createResp, &createdBuilding)

			// Now delete it
			deleteResp := auth.DELETE(t, "/api/v1/buildings/"+createdBuilding.ID.String())
			defer deleteResp.Body.Close()

			assert.Equal(t, http.StatusNoContent, deleteResp.StatusCode)

			// Verify it's deleted
			getResp := auth.GET(t, "/api/v1/buildings/"+createdBuilding.ID.String())
			defer getResp.Body.Close()

			assert.Equal(t, http.StatusNotFound, getResp.StatusCode) // Should return 404 after delete
		})
	})
}

func TestBuildingAPI_Validation(t *testing.T) {
	WithTestServer(t, func(t *testing.T, server *httptest.Server, auth *TestAuthHelper, container *app.Container) {
		t.Run("CreateBuilding_MissingName", func(t *testing.T) {
			createReq := domain.CreateBuildingRequest{
				Address: "Missing Name Street",
			}

			resp := auth.POST(t, "/api/v1/buildings", createReq)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
		})

		t.Run("CreateBuilding_MissingAddress", func(t *testing.T) {
			createReq := domain.CreateBuildingRequest{
				Name: "No Address Building",
			}

			resp := auth.POST(t, "/api/v1/buildings", createReq)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
		})
	})
}

func TestBuildingAPI_ErrorCases(t *testing.T) {
	WithTestServer(t, func(t *testing.T, server *httptest.Server, auth *TestAuthHelper, container *app.Container) {
		t.Run("GetBuilding_NotFound", func(t *testing.T) {
			// Use a valid UUID that doesn't exist
			resp := auth.GET(t, "/api/v1/buildings/00000000-0000-0000-0000-000000000001")
			defer resp.Body.Close()

			assert.Equal(t, http.StatusNotFound, resp.StatusCode) // Should return 404 for not found
		})

		t.Run("UpdateBuilding_NotFound", func(t *testing.T) {
			updatedName := "Updated Name"
			updateReq := domain.UpdateBuildingRequest{
				ID:   types.FromString("00000000-0000-0000-0000-000000000002"),
				Name: &updatedName,
			}

			resp := auth.PUT(t, "/api/v1/buildings/00000000-0000-0000-0000-000000000002", updateReq)
			defer resp.Body.Close()

			// Update should fail with appropriate error status
			assert.True(t, resp.StatusCode >= 400, "Expected error status code")
		})
	})
}
