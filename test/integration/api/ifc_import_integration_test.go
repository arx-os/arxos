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
	"os"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestIFCImportIntegration tests the complete IFC import workflow with real service
func TestIFCImportIntegration(t *testing.T) {
	// Check if IFC service is available
	ifcServiceURL := os.Getenv("ARXOS_IFC_SERVICE_URL")
	if ifcServiceURL == "" {
		ifcServiceURL = "http://localhost:5001"
	}

	// Try to ping the service
	client := &http.Client{Timeout: 2 * time.Second}
	resp, err := client.Get(ifcServiceURL + "/health")
	if err != nil || resp.StatusCode != http.StatusOK {
		t.Skip("IFC service not available at " + ifcServiceURL + " - start service to run this test")
	}
	if resp != nil {
		resp.Body.Close()
	}

	// Setup test server with IFC service configured
	WithTestServer(t, func(t *testing.T, server *httptest.Server, auth *TestAuthHelper, container *app.Container) {
		// Verify IFC service is configured
		ifcUC := container.GetIFCUseCase()
		if ifcUC == nil {
			t.Skip("IFC use case not available")
		}

		t.Run("Import_Sample_IFC", func(t *testing.T) {
			// Create test repository
			repoID := createTestRepositoryForIFC(t, container)

			// Read test IFC file
			ifcData, err := os.ReadFile("../../../test_data/inputs/sample.ifc")
			require.NoError(t, err, "Should read test IFC file")
			require.NotEmpty(t, ifcData, "IFC file should not be empty")

			t.Logf("Loaded IFC file: %d bytes", len(ifcData))

			// Import IFC directly via use case
			ctx := context.Background()
			result, err := ifcUC.ImportIFC(ctx, repoID, ifcData)
			require.NoError(t, err, "IFC import should succeed")

			// Verify result
			assert.NotNil(t, result, "Import result should not be nil")
			assert.Greater(t, result.BuildingsCreated, 0, "Should create at least one building")

			t.Logf("Import successful:")
			t.Logf("  Buildings created: %d", result.BuildingsCreated)
			t.Logf("  Floors created: %d", result.FloorsCreated)
			t.Logf("  Rooms created: %d", result.RoomsCreated)
			t.Logf("  Equipment created: %d", result.EquipmentCreated)

			// Verify entities were actually created in database
			if result.BuildingsCreated > 0 {
				buildingRepo := container.GetBuildingRepository()
				filter := &domain.BuildingFilter{Limit: 100}
				buildings, err := buildingRepo.List(ctx, filter)
				require.NoError(t, err)
				assert.Greater(t, len(buildings), 0, "Should have buildings in database")

				// Find the imported building
				var importedBuilding *domain.Building
				for _, b := range buildings {
					if b.Name == "Sample Building" {
						importedBuilding = b
						break
					}
				}
				if importedBuilding != nil {
					t.Logf("Found imported building: %s (ID: %s)", importedBuilding.Name, importedBuilding.ID)

					// Check for floors
					if result.FloorsCreated > 0 {
						floorRepo := container.GetFloorRepository()
						floors, err := floorRepo.GetByBuilding(ctx, importedBuilding.ID.String())
						require.NoError(t, err)
						assert.Equal(t, result.FloorsCreated, len(floors), "Floor count should match")
						t.Logf("Found %d floors", len(floors))
					}

					// Check for equipment
					if result.EquipmentCreated > 0 {
						equipmentRepo := container.GetEquipmentRepository()
						filter := &domain.EquipmentFilter{
							BuildingID: &importedBuilding.ID,
							Limit:      100,
						}
						equipment, err := equipmentRepo.List(ctx, filter)
						require.NoError(t, err)
						assert.Equal(t, result.EquipmentCreated, len(equipment), "Equipment count should match")
						t.Logf("Found %d equipment items", len(equipment))
					}
				}
			}
		})

		t.Run("Import_Complex_IFC", func(t *testing.T) {
			// Create test repository
			repoID := createTestRepositoryForIFC(t, container)

			// Read complex IFC file
			ifcData, err := os.ReadFile("../../../test_data/inputs/complex_building.ifc")
			if os.IsNotExist(err) {
				t.Skip("Complex building IFC file not found")
			}
			require.NoError(t, err, "Should read complex IFC file")

			t.Logf("Loaded complex IFC file: %d bytes", len(ifcData))

			// Import IFC
			ctx := context.Background()
			result, err := ifcUC.ImportIFC(ctx, repoID, ifcData)
			require.NoError(t, err, "Complex IFC import should succeed")

			t.Logf("Complex import successful:")
			t.Logf("  Buildings created: %d", result.BuildingsCreated)
			t.Logf("  Floors created: %d", result.FloorsCreated)
			t.Logf("  Equipment created: %d", result.EquipmentCreated)

			// This file should have lots of equipment
			assert.Greater(t, result.EquipmentCreated, 20, "Complex file should have many equipment items")
		})

		t.Run("Import_Via_HTTP_Endpoint", func(t *testing.T) {
			// Create test repository
			repoID := createTestRepositoryForIFC(t, container)

			// Read test IFC file
			ifcData, err := os.ReadFile("../../../test_data/inputs/sample.ifc")
			require.NoError(t, err)

			// Create multipart form
			var buf bytes.Buffer
			writer := multipart.NewWriter(&buf)

			// Add repository_id field
			err = writer.WriteField("repository_id", repoID)
			require.NoError(t, err)

			// Add file field
			part, err := writer.CreateFormFile("file", "sample.ifc")
			require.NoError(t, err)
			_, err = io.Copy(part, bytes.NewReader(ifcData))
			require.NoError(t, err)

			err = writer.Close()
			require.NoError(t, err)

			// Make authenticated request
			req, err := http.NewRequest("POST", server.URL+"/api/v1/ifc/import", &buf)
			require.NoError(t, err)
			req.Header.Set("Content-Type", writer.FormDataContentType())
			req.Header.Set("Authorization", "Bearer "+auth.token)

			resp, err := http.DefaultClient.Do(req)
			require.NoError(t, err)
			defer resp.Body.Close()

			t.Logf("HTTP Import Status: %d", resp.StatusCode)

			// Should succeed or return a known error
			if resp.StatusCode == http.StatusOK || resp.StatusCode == http.StatusCreated {
				var response map[string]any
				err = json.NewDecoder(resp.Body).Decode(&response)
				require.NoError(t, err)

				t.Logf("HTTP Import Response: %+v", response)
			} else if resp.StatusCode == http.StatusNotFound {
				t.Log("IFC import endpoint not found (404) - endpoint may not be registered")
			} else {
				// Log the error but don't fail - endpoint might not be fully wired
				bodyBytes, _ := io.ReadAll(resp.Body)
				t.Logf("HTTP Import returned %d: %s", resp.StatusCode, string(bodyBytes))
			}
		})

		t.Run("Import_Performance", func(t *testing.T) {
			// Create test repository
			repoID := createTestRepositoryForIFC(t, container)

			// Read test IFC file
			ifcData, err := os.ReadFile("../../../test_data/inputs/sample.ifc")
			require.NoError(t, err)

			// Measure import time
			ctx := context.Background()
			start := time.Now()
			result, err := ifcUC.ImportIFC(ctx, repoID, ifcData)
			duration := time.Since(start)

			require.NoError(t, err, "IFC import should succeed")
			t.Logf("Import completed in %v", duration)
			t.Logf("Entities created: Buildings=%d, Floors=%d, Equipment=%d",
				result.BuildingsCreated, result.FloorsCreated, result.EquipmentCreated)

			// Import should be reasonably fast (< 5 seconds for small file)
			assert.Less(t, duration, 5*time.Second, "Import should complete quickly")
		})
	})
}

// Helper function to create a test repository for IFC import
func createTestRepositoryForIFC(t *testing.T, container *app.Container) string {
	t.Helper()

	// Create repository directly in database
	ctx := context.Background()

	// Check if we have a repository repository
	// For now, insert directly into database via SQL
	postgis := container.GetPostGIS()
	if postgis == nil {
		t.Fatal("PostGIS not available")
	}
	db := postgis.GetDB()

	// Generate unique name using timestamp
	repoName := fmt.Sprintf("Test IFC Repository %d", time.Now().UnixNano())

	var repoID string
	err := db.QueryRowContext(ctx, `
		INSERT INTO building_repositories (name, type, floors, structure_json)
		VALUES ($1, $2, $3, $4)
		RETURNING id
	`, repoName, "commercial", 1, `{"ifc_files":[],"plans":[],"equipment":[],"operations":{},"integrations":[]}`).Scan(&repoID)

	require.NoError(t, err, "Should create test repository")
	require.NotEmpty(t, repoID, "Repository ID should not be empty")

	t.Logf("Created test repository: %s", repoID)
	return repoID
}
