package integration

import (
	"bytes"
	"context"
	"encoding/json"
	"net/http"
	"testing"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestEquipmentAPI_EndToEnd(t *testing.T) {
	server, container := setupTestServerWithConfig(t)
	if server == nil {
		return
	}
	defer server.Close()
	defer container.Shutdown(context.Background())

	// First create a building to attach equipment to
	var createdBuilding domain.Building
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

		body, err := json.Marshal(createReq)
		require.NoError(t, err)

		req, err := http.NewRequest("POST", server.URL+"/api/v1/buildings", bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		require.Equal(t, http.StatusCreated, resp.StatusCode)

		err = json.NewDecoder(resp.Body).Decode(&createdBuilding)
		require.NoError(t, err)
	})

	// Test 1: Create equipment
	var createdEquipment domain.Equipment
	t.Run("CreateEquipment", func(t *testing.T) {
		createReq := domain.CreateEquipmentRequest{
			BuildingID: createdBuilding.ID,
			Name:       "HVAC Unit 01",
			Type:       "hvac",
			Model:      "Model-ABC123",
			Location: &domain.Location{
				X: -122.4194,
				Y: 37.7749,
				Z: 10.5,
			},
		}

		body, err := json.Marshal(createReq)
		require.NoError(t, err)

		req, err := http.NewRequest("POST", server.URL+"/api/v1/equipment", bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusCreated, resp.StatusCode)

		err = json.NewDecoder(resp.Body).Decode(&createdEquipment)
		require.NoError(t, err)

		assert.Equal(t, createReq.Name, createdEquipment.Name)
		assert.Equal(t, createReq.Type, createdEquipment.Type)
		assert.Equal(t, createReq.Model, createdEquipment.Model)
		assert.NotEmpty(t, createdEquipment.ID)
	})

	// Test 2: List equipment
	t.Run("ListEquipment", func(t *testing.T) {
		req, err := http.NewRequest("GET", server.URL+"/api/v1/equipment?limit=10&offset=0", nil)
		require.NoError(t, err)

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]any
		err = json.NewDecoder(resp.Body).Decode(&result)
		require.NoError(t, err)

		assert.Contains(t, result, "equipment")
		equipment := result["equipment"].([]any)
		assert.GreaterOrEqual(t, len(equipment), 1)
	})

	// Test 3: Get equipment by ID
	t.Run("GetEquipment", func(t *testing.T) {
		req, err := http.NewRequest("GET", server.URL+"/api/v1/equipment/"+createdEquipment.ID.String(), nil)
		require.NoError(t, err)

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var equipment domain.Equipment
		err = json.NewDecoder(resp.Body).Decode(&equipment)
		require.NoError(t, err)

		assert.Equal(t, createdEquipment.ID.String(), equipment.ID.String())
		assert.Equal(t, createdEquipment.Name, equipment.Name)
	})

	// Test 4: Update equipment
	t.Run("UpdateEquipment", func(t *testing.T) {
		updatedName := "Updated HVAC Unit"
		updatedStatus := "maintenance"
		updateReq := domain.UpdateEquipmentRequest{
			ID:     types.FromString(createdEquipment.ID.String()),
			Name:   &updatedName,
			Status: &updatedStatus,
		}

		body, err := json.Marshal(updateReq)
		require.NoError(t, err)

		req, err := http.NewRequest("PUT", server.URL+"/api/v1/equipment/"+createdEquipment.ID.String(), bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var updatedEquipment domain.Equipment
		err = json.NewDecoder(resp.Body).Decode(&updatedEquipment)
		require.NoError(t, err)

		assert.Equal(t, updatedName, updatedEquipment.Name)
		assert.Equal(t, updatedStatus, updatedEquipment.Status)
	})

	// Test 5: Filter equipment by building
	t.Run("FilterEquipmentByBuilding", func(t *testing.T) {
		url := server.URL + "/api/v1/equipment?building_id=" + createdBuilding.ID.String()
		req, err := http.NewRequest("GET", url, nil)
		require.NoError(t, err)

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]any
		err = json.NewDecoder(resp.Body).Decode(&result)
		require.NoError(t, err)

		assert.Contains(t, result, "equipment")
		equipment := result["equipment"].([]any)
		assert.GreaterOrEqual(t, len(equipment), 1)
	})

	// Test 6: Delete equipment
	t.Run("DeleteEquipment", func(t *testing.T) {
		// First change status to allow deletion
		inactiveStatus := "inactive"
		updateReq := domain.UpdateEquipmentRequest{
			ID:     types.FromString(createdEquipment.ID.String()),
			Status: &inactiveStatus,
		}

		body, err := json.Marshal(updateReq)
		require.NoError(t, err)

		updateReqHTTP, err := http.NewRequest("PUT", server.URL+"/api/v1/equipment/"+createdEquipment.ID.String(), bytes.NewBuffer(body))
		require.NoError(t, err)
		updateReqHTTP.Header.Set("Content-Type", "application/json")

		updateResp, err := http.DefaultClient.Do(updateReqHTTP)
		require.NoError(t, err)
		updateResp.Body.Close()

		// Now delete
		deleteReq, err := http.NewRequest("DELETE", server.URL+"/api/v1/equipment/"+createdEquipment.ID.String(), nil)
		require.NoError(t, err)

		deleteResp, err := http.DefaultClient.Do(deleteReq)
		require.NoError(t, err)
		defer deleteResp.Body.Close()

		assert.Equal(t, http.StatusNoContent, deleteResp.StatusCode)
	})
}

func TestEquipmentAPI_Validation(t *testing.T) {
	server, container := setupTestServerWithConfig(t)
	if server == nil {
		return
	}
	defer server.Close()
	defer container.Shutdown(context.Background())

	t.Run("CreateEquipment_MissingName", func(t *testing.T) {
		createReq := domain.CreateEquipmentRequest{
			BuildingID: types.FromString("some-building"),
			Type:       "hvac",
		}

		body, err := json.Marshal(createReq)
		require.NoError(t, err)

		req, err := http.NewRequest("POST", server.URL+"/api/v1/equipment", bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
	})

	t.Run("CreateEquipment_InvalidType", func(t *testing.T) {
		createReq := domain.CreateEquipmentRequest{
			BuildingID: types.FromString("some-building"),
			Name:       "Test Equipment",
			Type:       "invalid_type",
		}

		body, err := json.Marshal(createReq)
		require.NoError(t, err)

		req, err := http.NewRequest("POST", server.URL+"/api/v1/equipment", bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusBadRequest, resp.StatusCode)
	})
}

func TestEquipmentAPI_LocationTracking(t *testing.T) {
	server, container := setupTestServerWithConfig(t)
	if server == nil {
		return
	}
	defer server.Close()
	defer container.Shutdown(context.Background())

	// Create a building first
	var building domain.Building
	t.Run("Setup_CreateBuilding", func(t *testing.T) {
		createReq := domain.CreateBuildingRequest{
			Name:    "Location Test Building",
			Address: "Location Test Address",
		}

		body, err := json.Marshal(createReq)
		require.NoError(t, err)

		req, err := http.NewRequest("POST", server.URL+"/api/v1/buildings", bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		err = json.NewDecoder(resp.Body).Decode(&building)
		require.NoError(t, err)
	})

	// Test creating equipment with 3D location
	t.Run("CreateEquipmentWith3DLocation", func(t *testing.T) {
		createReq := domain.CreateEquipmentRequest{
			BuildingID: building.ID,
			Name:       "3D Location Equipment",
			Type:       "hvac",
			Location: &domain.Location{
				X: 10.5,
				Y: 20.3,
				Z: 3.2,
			},
		}

		body, err := json.Marshal(createReq)
		require.NoError(t, err)

		req, err := http.NewRequest("POST", server.URL+"/api/v1/equipment", bytes.NewBuffer(body))
		require.NoError(t, err)
		req.Header.Set("Content-Type", "application/json")

		resp, err := http.DefaultClient.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusCreated, resp.StatusCode)

		var equipment domain.Equipment
		err = json.NewDecoder(resp.Body).Decode(&equipment)
		require.NoError(t, err)

		require.NotNil(t, equipment.Location)
		assert.InDelta(t, 10.5, equipment.Location.X, 0.01)
		assert.InDelta(t, 20.3, equipment.Location.Y, 0.01)
		assert.InDelta(t, 3.2, equipment.Location.Z, 0.01)
	})
}
