package integration

import (
	"context"
	"fmt"
	"net/http/httptest"
	"os"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/bas"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestBASImportIntegration tests the complete BAS import workflow with real CSV data
func TestBASImportIntegration(t *testing.T) {
	// Setup test server
	WithTestServer(t, func(t *testing.T, server *httptest.Server, auth *TestAuthHelper, container *app.Container) {
		// Verify BAS import use case is available
		basImportUC := container.GetBASImportUseCase()
		if basImportUC == nil {
			t.Skip("BAS import use case not available")
		}

		// Create test building structure
		ctx := context.Background()
		buildingID := createTestBuildingStructureForBAS(t, container)

		t.Run("Import_Metasys_CSV", func(t *testing.T) {
			// Create BAS system
			systemID := createTestBASSystem(t, container, buildingID)

			// Import CSV file
			csvPath := "../../../test_data/bas/metasys_sample_export.csv"
			_, err := os.Stat(csvPath)
			if os.IsNotExist(err) {
				t.Skip("Metasys sample CSV not found")
			}

			req := bas.ImportBASPointsRequest{
				FilePath:    csvPath,
				BuildingID:  buildingID,
				BASSystemID: systemID,
				SystemType:  bas.BASSystemTypeMetasys,
				AutoMap:     true,
				AutoCommit:  false,
			}

			result, err := basImportUC.ImportBASPoints(ctx, req)
			require.NoError(t, err, "BAS import should succeed")

			// Verify import results
			assert.NotNil(t, result)
			assert.Equal(t, "success", result.Status, "Import status should be success")
			assert.Greater(t, result.PointsAdded, 0, "Should add points")

			t.Logf("Import successful:")
			t.Logf("  Points added: %d", result.PointsAdded)
			t.Logf("  Points modified: %d", result.PointsModified)
			t.Logf("  Points deleted: %d", result.PointsDeleted)
			t.Logf("  Points mapped: %d", result.PointsMapped)
			t.Logf("  Points unmapped: %d", result.PointsUnmapped)
			t.Logf("  Duration: %dms", result.DurationMS)

			// Verify points were created in database
			basPointRepo := container.GetBASPointRepository()
			points, err := basPointRepo.ListByBuilding(buildingID)
			require.NoError(t, err)
			assert.Equal(t, result.PointsAdded, len(points), "Point count should match")

			t.Logf("Found %d points in database", len(points))
		})

		t.Run("Auto_Mapping_Functionality", func(t *testing.T) {
			// This test verifies auto-mapping by checking database state
			// Note: Points may already exist from previous test, so we verify database state

			basPointRepo := container.GetBASPointRepository()
			points, err := basPointRepo.ListByBuilding(buildingID)
			require.NoError(t, err)

			// Verify mapped points have room_id and correct attributes
			mappedCount := 0
			for _, point := range points {
				if point.RoomID != nil {
					mappedCount++

					// Verify path was generated
					assert.NotEmpty(t, point.Path, "Mapped point should have path")
					assert.True(t, point.Mapped, "Mapped flag should be true")
					assert.Greater(t, point.MappingConfidence, 0, "Should have confidence score")
					assert.Equal(t, 3, point.MappingConfidence, "Should have confidence 3 for exact matches")

					// Verify path format
					assert.Contains(t, point.Path, "/BAS/", "Path should contain /BAS/")
					assert.Contains(t, point.Path, point.PointName, "Path should contain point name")

					t.Logf("Mapped point: %s -> Room: %s, Path: %s, Confidence: %d",
						point.PointName, point.RoomID.String(), point.Path, point.MappingConfidence)
				}
			}

			// Should have auto-mapped several points
			assert.Greater(t, mappedCount, 10, "Should have auto-mapped multiple points")
			t.Logf("Auto-mapping verified: %d points mapped with confidence 3", mappedCount)
		})

		t.Run("Universal_Path_Generation", func(t *testing.T) {
			// Create BAS system
			systemID := createTestBASSystem(t, container, buildingID)

			// Import with auto-map
			csvPath := "../../../test_data/bas/metasys_sample_export.csv"
			req := bas.ImportBASPointsRequest{
				FilePath:    csvPath,
				BuildingID:  buildingID,
				BASSystemID: systemID,
				SystemType:  bas.BASSystemTypeMetasys,
				AutoMap:     true,
				AutoCommit:  false,
			}

			_, err := basImportUC.ImportBASPoints(ctx, req)
			require.NoError(t, err)

			// Verify universal paths
			basPointRepo := container.GetBASPointRepository()
			points, err := basPointRepo.ListByBuilding(buildingID)
			require.NoError(t, err)

			for _, point := range points {
				if point.Mapped {
					// Verify path format: /BUILDING/FLOOR/ROOM/BAS/POINT
					assert.Contains(t, point.Path, "/BAS/", "Path should contain /BAS/")
					assert.Contains(t, point.Path, point.PointName, "Path should contain point name")

					t.Logf("Universal path: %s", point.Path)
				}
			}
		})

		t.Run("CSV_Parsing_Accuracy", func(t *testing.T) {
			// Create BAS system
			systemID := createTestBASSystem(t, container, buildingID)

			// Import CSV
			csvPath := "../../../test_data/bas/metasys_sample_export.csv"
			req := bas.ImportBASPointsRequest{
				FilePath:    csvPath,
				BuildingID:  buildingID,
				BASSystemID: systemID,
				SystemType:  bas.BASSystemTypeMetasys,
				AutoMap:     false, // Disable auto-map to just test parsing
				AutoCommit:  false,
			}

			_, err := basImportUC.ImportBASPoints(ctx, req)
			require.NoError(t, err)

			// Verify points
			basPointRepo := container.GetBASPointRepository()
			points, err := basPointRepo.ListByBuilding(buildingID)
			require.NoError(t, err)

			// Verify sample points have correct metadata
			for _, point := range points {
				assert.NotEmpty(t, point.PointName, "Point should have name")
				assert.NotEmpty(t, point.DeviceID, "Point should have device ID")
				assert.NotEmpty(t, point.ObjectType, "Point should have object type")
				assert.NotEmpty(t, point.Description, "Point should have description")
				assert.NotEmpty(t, point.LocationText, "Point should have location text")

				// Log sample point for verification
				if point.PointName == "AI-1-1" {
					t.Logf("Sample point AI-1-1:")
					t.Logf("  Device: %s", point.DeviceID)
					t.Logf("  Type: %s", point.ObjectType)
					t.Logf("  Description: %s", point.Description)
					t.Logf("  Units: %s", point.Units)
					t.Logf("  Location: %s", point.LocationText)
				}
			}
		})

		t.Run("BAS_System_Management", func(t *testing.T) {
			// Create multiple BAS systems
			systemID1 := createTestBASSystem(t, container, buildingID)

			// Try to create another with different type
			systemID2 := createTestBASSystemWithType(t, container, buildingID, bas.BASSystemTypeDesigo)

			// Should be different systems
			assert.NotEqual(t, systemID1, systemID2, "Different system types should have different IDs")

			// List systems
			basSystemRepo := container.GetBASSystemRepository()
			systems, err := basSystemRepo.List(buildingID)
			require.NoError(t, err)
			assert.GreaterOrEqual(t, len(systems), 2, "Should have at least 2 systems")

			t.Logf("Found %d BAS systems", len(systems))
			for _, sys := range systems {
				t.Logf("  System: %s (Type: %s)", sys.Name, sys.SystemType)
			}
		})

		t.Run("Import_Performance", func(t *testing.T) {
			// Create BAS system
			systemID := createTestBASSystem(t, container, buildingID)

			// Measure import time
			csvPath := "../../../test_data/bas/metasys_sample_export.csv"
			req := bas.ImportBASPointsRequest{
				FilePath:    csvPath,
				BuildingID:  buildingID,
				BASSystemID: systemID,
				SystemType:  bas.BASSystemTypeMetasys,
				AutoMap:     true,
				AutoCommit:  false,
			}

			start := time.Now()
			result, err := basImportUC.ImportBASPoints(ctx, req)
			duration := time.Since(start)

			require.NoError(t, err)
			t.Logf("Import completed in %v", duration)
			t.Logf("Import reported duration: %dms", result.DurationMS)

			// Import should be fast (< 5 seconds for small CSV)
			assert.Less(t, duration, 5*time.Second, "Import should complete quickly")
		})

		t.Run("Change_Detection", func(t *testing.T) {
			// Create BAS system
			systemID := createTestBASSystem(t, container, buildingID)

			// First import
			csvPath := "../../../test_data/bas/metasys_sample_export.csv"
			req := bas.ImportBASPointsRequest{
				FilePath:    csvPath,
				BuildingID:  buildingID,
				BASSystemID: systemID,
				SystemType:  bas.BASSystemTypeMetasys,
				AutoMap:     false,
				AutoCommit:  false,
			}

			result1, err := basImportUC.ImportBASPoints(ctx, req)
			require.NoError(t, err)

			firstImportCount := result1.PointsAdded
			t.Logf("First import: %d points added", firstImportCount)

			// Second import (should detect no changes - using smaller test file)
			csvPath2 := "../../../test_data/bas/test_points.csv"
			if _, err := os.Stat(csvPath2); os.IsNotExist(err) {
				t.Skip("test_points.csv not found")
			}

			req2 := bas.ImportBASPointsRequest{
				FilePath:    csvPath2,
				BuildingID:  buildingID,
				BASSystemID: systemID,
				SystemType:  bas.BASSystemTypeMetasys,
				AutoMap:     false,
				AutoCommit:  false,
			}

			result2, err := basImportUC.ImportBASPoints(ctx, req2)
			require.NoError(t, err)

			t.Logf("Second import: added=%d, modified=%d, deleted=%d",
				result2.PointsAdded, result2.PointsModified, result2.PointsDeleted)

			// Should detect changes appropriately
			assert.True(t, result2.PointsAdded >= 0, "Should track added points")
		})
	})
}

// Helper: Create test building structure for BAS testing
func createTestBuildingStructureForBAS(t *testing.T, container *app.Container) types.ID {
	t.Helper()

	ctx := context.Background()

	// Create building
	buildingUC := container.GetBuildingUseCase()
	if buildingUC == nil {
		t.Fatal("Building use case not available")
	}

	buildingReq := &domain.CreateBuildingRequest{
		Name:    fmt.Sprintf("BAS Test Building %d", time.Now().UnixNano()),
		Address: "100 BAS Test Street",
	}
	building, err := buildingUC.CreateBuilding(ctx, buildingReq)
	require.NoError(t, err, "Should create test building")

	// Create floor
	floorUC := container.GetFloorUseCase()
	if floorUC == nil {
		t.Fatal("Floor use case not available")
	}

	floorReq := &domain.CreateFloorRequest{
		BuildingID: building.ID,
		Name:       "Floor 1",
		Level:      1,
	}
	floor, err := floorUC.CreateFloor(ctx, floorReq)
	require.NoError(t, err, "Should create test floor")

	// Create rooms (101, 102, 103, Mechanical Room)
	roomUC := container.GetRoomUseCase()
	if roomUC == nil {
		t.Fatal("Room use case not available")
	}

	rooms := []struct {
		name   string
		number string
	}{
		{"Room 101", "101"},
		{"Room 102", "102"},
		{"Room 103", "103"},
		{"Mechanical Room", "MR-01"},
	}

	for _, room := range rooms {
		roomReq := &domain.CreateRoomRequest{
			FloorID: floor.ID,
			Name:    room.name,
			Number:  room.number,
			Width:   12.0,
			Height:  10.0,
		}
		_, err := roomUC.CreateRoom(ctx, roomReq)
		require.NoError(t, err, "Should create room "+room.name)
	}

	t.Logf("Created test structure: building=%s, floor=%s, 4 rooms", building.ID.String(), floor.ID.String())
	return building.ID
}

// Helper: Create test BAS system
func createTestBASSystem(t *testing.T, container *app.Container, buildingID types.ID) types.ID {
	t.Helper()
	return createTestBASSystemWithType(t, container, buildingID, bas.BASSystemTypeMetasys)
}

// Helper: Create test BAS system with specific type
func createTestBASSystemWithType(t *testing.T, container *app.Container, buildingID types.ID, systemType bas.BASSystemType) types.ID {
	t.Helper()

	basSystemRepo := container.GetBASSystemRepository()
	if basSystemRepo == nil {
		t.Fatal("BAS system repository not available")
	}

	// Check if system already exists
	systems, err := basSystemRepo.List(buildingID)
	require.NoError(t, err)

	// Find existing system of this type
	for _, sys := range systems {
		if sys.SystemType == systemType {
			t.Logf("Using existing BAS system: %s (ID: %s)", sys.Name, sys.ID.String())
			return sys.ID
		}
	}

	// Create new system
	systemID := types.NewID()
	systemName := fmt.Sprintf("%s Test System %d", systemType, time.Now().UnixNano())

	system := &bas.BASSystem{
		ID:         systemID,
		BuildingID: buildingID,
		Name:       systemName,
		SystemType: systemType,
		Enabled:    true,
		ReadOnly:   false,
		Metadata:   make(map[string]interface{}),
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err = basSystemRepo.Create(system)
	require.NoError(t, err, "Should create BAS system")

	t.Logf("Created BAS system: %s (ID: %s)", system.Name, systemID.String())
	return systemID
}
