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

func TestEquipmentAPI_EndToEnd(t *testing.T) {
	WithTestServer(t, func(t *testing.T, server *httptest.Server, auth *TestAuthHelper, container *app.Container) {
		// Shared variables across subtests
		var buildingID string
		var equipmentID string

		t.Run("Setup_CreateBuilding", func(t *testing.T) {
			createReq := domain.CreateBuildingRequest{
				Name:    "Equipment Test Building",
				Address: "Equipment Test Address",
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
			buildingID = building.ID.String()
		})

		// Test 1: Create equipment
		t.Run("CreateEquipment", func(t *testing.T) {
			createReq := domain.CreateEquipmentRequest{
				BuildingID: types.FromString(buildingID),
				Name:       "HVAC Unit 01",
				Type:       "hvac",
				Model:      "Model-ABC123",
				Location: &domain.Location{
					X: -122.4194,
					Y: 37.7749,
					Z: 10.5,
				},
			}

			resp := auth.POST(t, "/api/v1/equipment", createReq)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusCreated, resp.StatusCode)

			var equipment domain.Equipment
			auth.DecodeJSON(t, resp, &equipment)
			equipmentID = equipment.ID.String()

			assert.Equal(t, createReq.Name, equipment.Name)
			assert.Equal(t, createReq.Type, equipment.Type)
			assert.NotEmpty(t, equipmentID)
		})

		// Test 2: Get equipment
		t.Run("GetEquipment", func(t *testing.T) {
			resp := auth.GET(t, "/api/v1/equipment/"+equipmentID)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var equipment domain.Equipment
			auth.DecodeJSON(t, resp, &equipment)

			assert.Equal(t, equipmentID, equipment.ID.String())
			assert.Equal(t, "HVAC Unit 01", equipment.Name)
		})

		// Test 3: List equipment
		t.Run("ListEquipment", func(t *testing.T) {
			resp := auth.GET(t, "/api/v1/equipment?limit=10&offset=0")
			defer resp.Body.Close()

			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var result map[string]any
			auth.DecodeJSON(t, resp, &result)

			assert.Contains(t, result, "equipment")
		})

		// Test 4: Filter equipment by building
		t.Run("FilterEquipmentByBuilding", func(t *testing.T) {
			resp := auth.GET(t, "/api/v1/equipment?building_id="+buildingID)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var result map[string]any
			auth.DecodeJSON(t, resp, &result)

			assert.Contains(t, result, "equipment")
		})

		// Test 5: Update equipment
		t.Run("UpdateEquipment", func(t *testing.T) {
			updatedName := "HVAC Unit 01 - Updated"
			updateReq := domain.UpdateEquipmentRequest{
				ID:   types.FromString(equipmentID),
				Name: &updatedName,
			}

			resp := auth.PUT(t, "/api/v1/equipment/"+equipmentID, updateReq)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var equipment domain.Equipment
			auth.DecodeJSON(t, resp, &equipment)

			assert.Equal(t, updatedName, equipment.Name)
		})

		// Test 6: Delete equipment
		t.Run("DeleteEquipment", func(t *testing.T) {
			// Ensure equipment was created
			if equipmentID == "" {
				t.Fatal("equipmentID is empty - CreateEquipment test may have failed")
			}

			// First, set equipment to inactive status (business rule: can't delete active equipment)
			inactiveStatus := "inactive"
			updateReq := domain.UpdateEquipmentRequest{
				ID:     types.FromString(equipmentID),
				Status: &inactiveStatus,
			}

			updateResp := auth.PUT(t, "/api/v1/equipment/"+equipmentID, updateReq)
			defer updateResp.Body.Close()

			assert.Equal(t, http.StatusOK, updateResp.StatusCode)

			// Now delete the equipment
			resp := auth.DELETE(t, "/api/v1/equipment/"+equipmentID)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusNoContent, resp.StatusCode)

			// Verify deletion
			getResp := auth.GET(t, "/api/v1/equipment/"+equipmentID)
			defer getResp.Body.Close()

			assert.Equal(t, http.StatusNotFound, getResp.StatusCode)
		})
	})
}

func TestEquipmentAPI_Validation(t *testing.T) {
	WithTestServer(t, func(t *testing.T, server *httptest.Server, auth *TestAuthHelper, container *app.Container) {
		// Create a building first
		buildingID := auth.CreateTestBuilding(t, "Validation Test Building", "Validation Test Address")

		t.Run("CreateEquipment_MissingName", func(t *testing.T) {
			createReq := domain.CreateEquipmentRequest{
				BuildingID: types.FromString(buildingID),
				Type:       "hvac",
			}

			resp := auth.POST(t, "/api/v1/equipment", createReq)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
		})

		t.Run("CreateEquipment_InvalidType", func(t *testing.T) {
			createReq := domain.CreateEquipmentRequest{
				BuildingID: types.FromString(buildingID),
				Name:       "Test Equipment",
				Type:       "", // Empty type
			}

			resp := auth.POST(t, "/api/v1/equipment", createReq)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
		})
	})
}

func TestEquipmentAPI_LocationTracking(t *testing.T) {
	WithTestServer(t, func(t *testing.T, server *httptest.Server, auth *TestAuthHelper, container *app.Container) {
		// Create a building first (not as subtest to ensure buildingID is set)
		buildingID := auth.CreateTestBuilding(t, "Location Test Building", "Location Test Address")

		t.Run("CreateEquipmentWith3DLocation", func(t *testing.T) {
			createReq := domain.CreateEquipmentRequest{
				BuildingID: types.FromString(buildingID),
				Name:       "Sensor 3D",
				Type:       "sensor",
				Location: &domain.Location{
					X: -122.4194,
					Y: 37.7749,
					Z: 25.5,
				},
			}

			resp := auth.POST(t, "/api/v1/equipment", createReq)
			defer resp.Body.Close()

			assert.Equal(t, http.StatusCreated, resp.StatusCode)

			var equipment domain.Equipment
			auth.DecodeJSON(t, resp, &equipment)

			assert.NotNil(t, equipment.Location)
			assert.Equal(t, 25.5, equipment.Location.Z)
		})
	})
}
