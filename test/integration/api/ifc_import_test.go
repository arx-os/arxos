package integration

import (
	"bytes"
	"context"
	"encoding/json"
	"io"
	"mime/multipart"
	"net/http"
	"net/http/httptest"
	"os"
	"testing"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain/types"
	httpapi "github.com/arx-os/arxos/internal/interfaces/http"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestIFCImportEndpoint tests the IFC import HTTP endpoint
func TestIFCImportEndpoint(t *testing.T) {
	t.Skip("IFC Import endpoint test - see ifc_import_integration_test.go for complete integration tests")

	// Skip if not in integration test mode
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	// Setup test environment
	cfg := &config.Config{
		Mode: "test",
		PostGIS: config.PostGISConfig{
			Host:     "localhost",
			Port:     5432,
			Database: "arxos",
			User:     "arxos",
			Password: "",
			SSLMode:  "disable",
		},
		IFC: config.IFCConfig{
			Service: config.IFCServiceConfig{
				Enabled: true,
				URL:     "http://localhost:5001",
				Timeout: "30s",
				Retries: 3,
			},
		},
	}

	// Initialize container
	container := app.NewContainer()
	ctx := context.Background()
	err := container.Initialize(ctx, cfg)
	require.NoError(t, err, "Container initialization should succeed")
	defer container.Shutdown(context.Background())

	// Create router
	routerConfig := &httpapi.RouterConfig{
		Container: container,
	}
	router := httpapi.NewRouter(routerConfig)

	// Create test repository
	repoID := types.NewID()
	createTestRepository(t, container, repoID)

	t.Run("Import IFC via multipart upload", func(t *testing.T) {
		// Read test IFC file
		ifcFilePath := "../../test_data/inputs/sample.ifc"
		ifcData, err := os.ReadFile(ifcFilePath)
		require.NoError(t, err, "Should read test IFC file")

		// Create multipart form
		body := &bytes.Buffer{}
		writer := multipart.NewWriter(body)

		// Add repository_id field
		err = writer.WriteField("repository_id", repoID.String())
		require.NoError(t, err)

		// Add file field
		part, err := writer.CreateFormFile("file", "sample.ifc")
		require.NoError(t, err)
		_, err = io.Copy(part, bytes.NewReader(ifcData))
		require.NoError(t, err)

		err = writer.Close()
		require.NoError(t, err)

		// Create request
		req := httptest.NewRequest("POST", "/api/v1/ifc/import", body)
		req.Header.Set("Content-Type", writer.FormDataContentType())

		// Record response
		rr := httptest.NewRecorder()

		// Execute request
		router.ServeHTTP(rr, req)

		// Check response (might be 401 if auth is required)
		t.Logf("Status Code: %d", rr.Code)
		t.Logf("Response: %s", rr.Body.String())

		// If successful (200) or auth required (401), both are expected
		assert.True(t, rr.Code == http.StatusOK || rr.Code == http.StatusUnauthorized,
			"Should return 200 OK or 401 Unauthorized, got %d", rr.Code)

		// If successful, validate response
		if rr.Code == http.StatusOK {
			var response map[string]any
			err = json.NewDecoder(rr.Body).Decode(&response)
			require.NoError(t, err)

			assert.True(t, response["success"].(bool), "Import should succeed")
			assert.NotNil(t, response["result"], "Should have result")

			result := response["result"].(map[string]any)
			t.Logf("Buildings Created: %.0f", result["buildings_created"])
			t.Logf("Floors Created: %.0f", result["floors_created"])
			t.Logf("Equipment Created: %.0f", result["equipment_created"])
		}
	})

	t.Run("Import IFC via JSON", func(t *testing.T) {
		// Read test IFC file
		ifcFilePath := "../../test_data/inputs/sample.ifc"
		ifcData, err := os.ReadFile(ifcFilePath)
		require.NoError(t, err, "Should read test IFC file")

		// Create JSON request
		requestBody := map[string]string{
			"repository_id": repoID.String(),
			"ifc_data":      string(ifcData),
		}
		jsonData, err := json.Marshal(requestBody)
		require.NoError(t, err)

		// Create request
		req := httptest.NewRequest("POST", "/api/v1/ifc/import", bytes.NewReader(jsonData))
		req.Header.Set("Content-Type", "application/json")

		// Record response
		rr := httptest.NewRecorder()

		// Execute request
		router.ServeHTTP(rr, req)

		// Check response
		t.Logf("Status Code: %d", rr.Code)
		t.Logf("Response: %s", rr.Body.String())

		// Should succeed or require auth
		assert.True(t, rr.Code == http.StatusOK || rr.Code == http.StatusUnauthorized,
			"Should return 200 OK or 401 Unauthorized, got %d", rr.Code)
	})
}

// Helper function to create test repository
func createTestRepository(t *testing.T, container *app.Container, repoID types.ID) {
	// This would create a test repository in the database
	// For now, using existing test repository
	t.Log("Using test repository:", repoID.String())
}
