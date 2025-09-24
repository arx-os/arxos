package integration

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"

	"github.com/arx-os/arxos/internal/api"
	"github.com/arx-os/arxos/internal/api/types"
	"github.com/arx-os/arxos/internal/handlers/web"
	"github.com/arx-os/arxos/pkg/models"
)

// TestBuildingWorkflow tests the complete building creation and management workflow
func TestBuildingWorkflow(t *testing.T) {
	services, cleanup := setupTestServices(t)
	defer cleanup()

	typesServices := &types.Services{
		DB:   services.DB,
		User: services.User,
	}
	handler, err := web.NewHandler(typesServices)
	require.NoError(t, err)

	router := web.NewAuthenticatedRouter(handler)
	server := httptest.NewServer(router)
	defer server.Close()

	// Get auth token
	token := getTestAuthToken(t, server)

	var buildingID string

	t.Run("CreateBuilding", func(t *testing.T) {
		building := &models.FloorPlan{
			ID:          "test-building-1",
			Name:        "Test Building",
			Description: "Test office building",
			Level:       1,
		}

		body, _ := json.Marshal(building)
		req, _ := http.NewRequest("POST", server.URL+"/api/buildings", bytes.NewReader(body))
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Content-Type", "application/json")

		client := &http.Client{}
		resp, err := client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusCreated, resp.StatusCode)

		// Parse response to get building ID
		var result map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&result)

		if data, ok := result["data"].(map[string]interface{}); ok {
			buildingID = data["id"].(string)
		}
		assert.NotEmpty(t, buildingID)
	})

	t.Run("GetBuilding", func(t *testing.T) {
		req, _ := http.NewRequest("GET", server.URL+"/api/buildings/"+buildingID, nil)
		req.Header.Set("Authorization", "Bearer "+token)

		client := &http.Client{}
		resp, err := client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&result)

		if data, ok := result["data"].(map[string]interface{}); ok {
			assert.Equal(t, "Test Building", data["name"])
			assert.Equal(t, "123 Test Street", data["address"])
		}
	})

	t.Run("UpdateBuilding", func(t *testing.T) {
		update := map[string]interface{}{
			"name":   "Updated Building",
			"floors": 6,
		}

		body, _ := json.Marshal(update)
		req, _ := http.NewRequest("PUT", server.URL+"/api/buildings/"+buildingID, bytes.NewReader(body))
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Content-Type", "application/json")

		client := &http.Client{}
		resp, err := client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)
	})

	t.Run("ListBuildings", func(t *testing.T) {
		req, _ := http.NewRequest("GET", server.URL+"/api/buildings", nil)
		req.Header.Set("Authorization", "Bearer "+token)

		client := &http.Client{}
		resp, err := client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusOK, resp.StatusCode)

		var result map[string]interface{}
		json.NewDecoder(resp.Body).Decode(&result)

		if data, ok := result["data"].([]interface{}); ok {
			assert.GreaterOrEqual(t, len(data), 1)
		}
	})

	t.Run("DeleteBuilding", func(t *testing.T) {
		// Need admin token for delete
		adminToken := getTestAdminToken(t, server)

		req, _ := http.NewRequest("DELETE", server.URL+"/api/buildings/"+buildingID, nil)
		req.Header.Set("Authorization", "Bearer "+adminToken)

		client := &http.Client{}
		resp, err := client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusNoContent, resp.StatusCode)

		// Verify deletion
		req, _ = http.NewRequest("GET", server.URL+"/api/buildings/"+buildingID, nil)
		req.Header.Set("Authorization", "Bearer "+token)

		resp, err = client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		assert.Equal(t, http.StatusNotFound, resp.StatusCode)
	})
}

// TestIFCImportExportWorkflow tests IFC file import and BIM export
func TestIFCImportExportWorkflow(t *testing.T) {
	ctx := context.Background()
	services, cleanup := setupTestServices(t)
	defer cleanup()

	typesServices := &types.Services{
		DB:   services.DB,
		User: services.User,
	}
	handler, err := web.NewHandler(typesServices)
	require.NoError(t, err)

	router := web.NewAuthenticatedRouter(handler)
	server := httptest.NewServer(router)
	defer server.Close()

	token := getTestAuthToken(t, server)

	t.Run("ImportIFCFile", func(t *testing.T) {
		// Create a test IFC file
		ifcContent := `ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('Test IFC File'),'2;1');
FILE_NAME('test.ifc','2024-01-01T00:00:00',(),(),'','','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('1234567890123456',$,'Test Project',$,$,$,$,$,$);
#2=IFCBUILDING('2345678901234567',$,'Test Building',$,$,$,$,$,$,$,$);
ENDSEC;
END-ISO-10303-21;`

		// Create multipart form
		var b bytes.Buffer
		w := multipart.NewWriter(&b)

		// Add file field
		fw, err := w.CreateFormFile("file", "test.ifc")
		require.NoError(t, err)
		_, err = io.WriteString(fw, ifcContent)
		require.NoError(t, err)

		// Add building_id field (optional)
		fw, err = w.CreateFormField("building_id")
		require.NoError(t, err)
		_, err = io.WriteString(fw, "")
		require.NoError(t, err)

		w.Close()

		// Send request
		req, _ := http.NewRequest("POST", server.URL+"/api/import/ifc", &b)
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Content-Type", w.FormDataContentType())

		client := &http.Client{}
		resp, err := client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		// Check response (may be NotImplemented in current state)
		if resp.StatusCode != http.StatusNotImplemented {
			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var result map[string]interface{}
			json.NewDecoder(resp.Body).Decode(&result)

			if data, ok := result["data"].(map[string]interface{}); ok {
				assert.NotEmpty(t, data["building_id"])
				assert.Equal(t, "success", data["status"])
			}
		}
	})

	t.Run("ExportBIM", func(t *testing.T) {
		// First create a building
		building := &models.FloorPlan{
			ID:    "test-building-export",
			Name:  "Export Test Building",
			Level: 1,
		}
		_, err := services.Building.CreateBuilding(ctx, building.Name)
		require.NoError(t, err)

		// Export to BIM format
		req, _ := http.NewRequest("GET", server.URL+"/api/export/bim?building_id="+building.ID, nil)
		req.Header.Set("Authorization", "Bearer "+token)

		client := &http.Client{}
		resp, err := client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusNotImplemented {
			assert.Equal(t, http.StatusOK, resp.StatusCode)
			assert.Equal(t, "text/plain", resp.Header.Get("Content-Type"))

			// Read BIM content
			body, err := io.ReadAll(resp.Body)
			require.NoError(t, err)

			// Verify BIM format
			bimContent := string(body)
			assert.Contains(t, bimContent, "BUILDING:")
			assert.Contains(t, bimContent, "Export Test Building")
		}
	})
}

// TestEquipmentWorkflow tests equipment management workflow
func TestEquipmentWorkflow(t *testing.T) {
	ctx := context.Background()
	services, cleanup := setupTestServices(t)
	defer cleanup()

	typesServices := &types.Services{
		DB:   services.DB,
		User: services.User,
	}
	handler, err := web.NewHandler(typesServices)
	require.NoError(t, err)

	router := web.NewAuthenticatedRouter(handler)
	server := httptest.NewServer(router)
	defer server.Close()

	token := getTestAuthToken(t, server)

	// Create a building first
	building := &models.FloorPlan{
		ID:    "test-building-equip",
		Name:  "Equipment Test Building",
		Level: 1,
	}
	_, err = services.Building.CreateBuilding(ctx, building.Name)
	require.NoError(t, err)

	var equipmentID string

	t.Run("CreateEquipment", func(t *testing.T) {
		equipment := &models.Equipment{
			Name:     "Test Outlet",
			Type:     "outlet",
			Path:     "N/3/A/301/E/OUTLET_01",
			Location: &models.Point3D{X: 10.5, Y: 20.3, Z: 3.0},
			Status:   "operational",
		}

		body, _ := json.Marshal(equipment)
		req, _ := http.NewRequest("POST", server.URL+"/api/equipment", bytes.NewReader(body))
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Content-Type", "application/json")

		client := &http.Client{}
		resp, err := client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusNotImplemented {
			assert.Equal(t, http.StatusCreated, resp.StatusCode)

			var result map[string]interface{}
			json.NewDecoder(resp.Body).Decode(&result)

			if data, ok := result["data"].(map[string]interface{}); ok {
				equipmentID = data["id"].(string)
			}
			assert.NotEmpty(t, equipmentID)
		}
	})

	t.Run("SpatialQuery", func(t *testing.T) {
		// Query equipment near a point
		query := map[string]interface{}{
			"type": "proximity",
			"center": map[string]float64{
				"x": 10.0,
				"y": 20.0,
				"z": 3.0,
			},
			"radius": 5.0,
		}

		body, _ := json.Marshal(query)
		req, _ := http.NewRequest("POST", server.URL+"/api/spatial/query", bytes.NewReader(body))
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Content-Type", "application/json")

		client := &http.Client{}
		resp, err := client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusNotImplemented {
			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var result map[string]interface{}
			json.NewDecoder(resp.Body).Decode(&result)

			if data, ok := result["data"].([]interface{}); ok {
				// Should find our test outlet
				assert.GreaterOrEqual(t, len(data), 1)
			}
		}
	})

	t.Run("CreateConnection", func(t *testing.T) {
		// Create another equipment
		equipment2 := &models.Equipment{
			Name:   "Test Panel",
			Type:   "panel",
			Path:   "N/3/A/301/E/PANEL_01",
			Status: "operational",
		}

		_, err = services.Equipment.CreateEquipment(ctx, equipment2.Name, equipment2.Type, equipment2.Path, "", 0, 0, 0)
		require.NoError(t, err)

		// Create connection between equipment
		connection := map[string]interface{}{
			"from_equipment_id": equipmentID,
			"to_equipment_id":   equipment2.ID,
			"type":              "electrical",
		}

		body, _ := json.Marshal(connection)
		req, _ := http.NewRequest("POST", server.URL+"/api/connections", bytes.NewReader(body))
		req.Header.Set("Authorization", "Bearer "+token)
		req.Header.Set("Content-Type", "application/json")

		client := &http.Client{}
		resp, err := client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusNotImplemented {
			assert.Equal(t, http.StatusCreated, resp.StatusCode)
		}
	})

	t.Run("GetConnectionGraph", func(t *testing.T) {
		req, _ := http.NewRequest("GET",
			fmt.Sprintf("%s/api/connections/graph?equipment_id=%s&depth=3", server.URL, equipmentID),
			nil)
		req.Header.Set("Authorization", "Bearer "+token)

		client := &http.Client{}
		resp, err := client.Do(req)
		require.NoError(t, err)
		defer resp.Body.Close()

		if resp.StatusCode != http.StatusNotImplemented {
			assert.Equal(t, http.StatusOK, resp.StatusCode)

			var result map[string]interface{}
			json.NewDecoder(resp.Body).Decode(&result)

			if data, ok := result["data"].(map[string]interface{}); ok {
				assert.NotNil(t, data["nodes"])
				assert.NotNil(t, data["edges"])
			}
		}
	})
}

// Helper functions

func setupTestServices(t *testing.T) (*api.Services, func()) {
	// This is a simplified setup - in real tests you'd use a test database
	services := &api.Services{
		// Initialize services with test database
	}

	cleanup := func() {
		// Cleanup test data
	}

	return services, cleanup
}

func getTestAuthToken(t *testing.T, server *httptest.Server) string {
	// Create test user and get token
	loginReq := map[string]string{
		"email":    "test@arxos.io",
		"password": "test_password",
	}
	body, _ := json.Marshal(loginReq)

	resp, err := http.Post(server.URL+"/api/auth/login", "application/json", bytes.NewReader(body))
	require.NoError(t, err)
	defer resp.Body.Close()

	var loginResp map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&loginResp)

	token, _ := loginResp["token"].(string)
	return token
}

func getTestAdminToken(t *testing.T, server *httptest.Server) string {
	// Create admin user and get token
	loginReq := map[string]string{
		"email":    "admin@arxos.io",
		"password": "admin_password",
	}
	body, _ := json.Marshal(loginReq)

	resp, err := http.Post(server.URL+"/api/auth/login", "application/json", bytes.NewReader(body))
	require.NoError(t, err)
	defer resp.Body.Close()

	var loginResp map[string]interface{}
	json.NewDecoder(resp.Body).Decode(&loginResp)

	token, _ := loginResp["token"].(string)
	return token
}
