package integration

import (
	"context"
	"os"
	"path/filepath"
	"testing"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestIFCImportE2E validates complete IFC import workflow
// Tests: IFC parsing → entity extraction → database persistence → path generation
func TestIFCImportE2E(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	// Setup test environment
	ctx := context.Background()
	container := setupTestContainer(t)
	if container == nil {
		t.Skip("Test container not available - requires database")
	}

	// Get use cases and repositories
	ifcUC := container.GetIFCUseCase()
	buildingRepo := container.GetBuildingRepository()
	floorRepo := container.GetFloorRepository()
	roomRepo := container.GetRoomRepository()
	equipmentRepo := container.GetEquipmentRepository()

	// Test cases with different IFC files
	testCases := []struct {
		name              string
		ifcFile           string
		skipIfNotFound    bool
		expectedBuildings int
		expectedMinFloors int
		expectedMinRooms  int
		expectedMinEquip  int
	}{
		{
			name:              "FZK Haus Sample",
			ifcFile:           "AC20-FZK-Haus.ifc",
			skipIfNotFound:    true,
			expectedBuildings: 1,
			expectedMinFloors: 1,
			expectedMinRooms:  1,
			expectedMinEquip:  1,
		},
		{
			name:              "Duplex Sample",
			ifcFile:           "Duplex_A_20110907.ifc",
			skipIfNotFound:    true,
			expectedBuildings: 1,
			expectedMinFloors: 2,
			expectedMinRooms:  5,
			expectedMinEquip:  0, // May not have equipment
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			// Load IFC file
			ifcPath := filepath.Join("../../test_data/inputs", tc.ifcFile)
			ifcData, err := os.ReadFile(ifcPath)
			if err != nil {
				if tc.skipIfNotFound && os.IsNotExist(err) {
					t.Skipf("IFC file not found: %s (place sample files in test_data/inputs/)", tc.ifcFile)
				}
				require.NoError(t, err, "Failed to read IFC file")
			}

			t.Logf("Loaded IFC file: %s (%d bytes)", tc.ifcFile, len(ifcData))

			// Create test repository
			repoID := "test-repo-" + tc.name

			// Import IFC
			result, err := ifcUC.ImportIFC(ctx, repoID, ifcData)
			require.NoError(t, err, "IFC import should succeed")
			require.NotNil(t, result, "Import result should not be nil")

			t.Logf("Import complete: %d buildings, %d floors, %d rooms, %d equipment",
				result.BuildingsCreated, result.FloorsCreated, result.RoomsCreated, result.EquipmentCreated)

			// Validate import statistics
			assert.GreaterOrEqual(t, result.BuildingsCreated, tc.expectedBuildings,
				"Should create expected number of buildings")
			assert.GreaterOrEqual(t, result.FloorsCreated, tc.expectedMinFloors,
				"Should create minimum expected floors")
			assert.GreaterOrEqual(t, result.RoomsCreated, tc.expectedMinRooms,
				"Should create minimum expected rooms")
			assert.GreaterOrEqual(t, result.EquipmentCreated, tc.expectedMinEquip,
				"Should create minimum expected equipment")

			// Verify buildings created in database
			buildings, err := buildingRepo.List(ctx, &domain.BuildingFilter{Limit: 100})
			require.NoError(t, err, "Should list buildings")
			assert.GreaterOrEqual(t, len(buildings), tc.expectedBuildings,
				"Buildings should exist in database")

			if len(buildings) == 0 {
				t.Fatal("No buildings found in database after import")
			}

			building := buildings[0]
			t.Logf("First building: ID=%s, Name=%s, Address=%s",
				building.ID, building.Name, building.Address)

			// Verify building has required fields
			assert.NotEmpty(t, building.ID, "Building should have ID")
			assert.NotEmpty(t, building.Name, "Building should have name")

			// Verify floors created
			floors, err := floorRepo.GetByBuilding(ctx, building.ID.String())
			require.NoError(t, err, "Should get floors by building")
			assert.GreaterOrEqual(t, len(floors), tc.expectedMinFloors,
				"Floors should exist for building")

			if len(floors) > 0 {
				floor := floors[0]
				t.Logf("First floor: ID=%s, Name=%s, Level=%d",
					floor.ID, floor.Name, floor.Level)
				assert.NotEmpty(t, floor.ID, "Floor should have ID")
				assert.NotEmpty(t, floor.Name, "Floor should have name")
				assert.Equal(t, building.ID, floor.BuildingID, "Floor should link to building")

				// Verify rooms created for floor
				rooms, err := roomRepo.GetByFloor(ctx, floor.ID.String())
				require.NoError(t, err, "Should get rooms by floor")

				if len(rooms) > 0 {
					room := rooms[0]
					t.Logf("First room: ID=%s, Name=%s, Number=%s",
						room.ID, room.Name, room.Number)
					assert.NotEmpty(t, room.ID, "Room should have ID")
					assert.NotEmpty(t, room.Name, "Room should have name")
					assert.Equal(t, floor.ID, room.FloorID, "Room should link to floor")

					// Verify room has geometry if extracted from IFC
					if room.Location != nil {
						t.Logf("Room location: (%.2f, %.2f, %.2f)",
							room.Location.X, room.Location.Y, room.Location.Z)
					}
					if room.Width > 0 && room.Height > 0 {
						t.Logf("Room dimensions: %.2fm x %.2fm", room.Width, room.Height)
					}
				}
			}

			// Verify equipment created
			equipment, err := equipmentRepo.GetByBuilding(ctx, building.ID.String())
			require.NoError(t, err, "Should get equipment by building")
			assert.GreaterOrEqual(t, len(equipment), tc.expectedMinEquip,
				"Equipment should exist for building")

			if len(equipment) > 0 {
				// Verify equipment has required fields
				eq := equipment[0]
				t.Logf("First equipment: ID=%s, Name=%s, Type=%s, Category=%s, Path=%s",
					eq.ID, eq.Name, eq.Type, eq.Category, eq.Path)

				assert.NotEmpty(t, eq.ID, "Equipment should have ID")
				assert.NotEmpty(t, eq.Name, "Equipment should have name")
				assert.Equal(t, building.ID, eq.BuildingID, "Equipment should link to building")

				// Verify universal naming path generated
				assert.NotEmpty(t, eq.Path, "Equipment should have universal naming path")
				assert.Contains(t, eq.Path, "/", "Path should be hierarchical")

				// Verify equipment category mapped from IFC type
				validCategories := []string{"electrical", "hvac", "plumbing", "safety", "lighting", "network", "other"}
				assert.Contains(t, validCategories, eq.Category,
					"Equipment category should be valid: %s", eq.Category)

				// Verify equipment has location if extracted
				if eq.Location != nil {
					t.Logf("Equipment location: (%.2f, %.2f, %.2f)",
						eq.Location.X, eq.Location.Y, eq.Location.Z)
					assert.NotZero(t, eq.Location.X+eq.Location.Y+eq.Location.Z,
						"Location should have coordinates")
				}

				// Test path-based query on imported equipment
				t.Run("QueryImportedEquipmentByPath", func(t *testing.T) {
					// Test exact path query
					equipByPath, err := equipmentRepo.GetByPath(ctx, eq.Path)
					require.NoError(t, err, "Should get equipment by exact path")
					assert.Equal(t, eq.ID, equipByPath.ID, "Should find same equipment")

					// Test wildcard path query
					pathPattern := "/" + building.Name[:1] + "*/*/*/" + eq.Category + "/*"
					equipByPattern, err := equipmentRepo.FindByPath(ctx, pathPattern)
					require.NoError(t, err, "Should find equipment by pattern")
					assert.NotEmpty(t, equipByPattern, "Should find equipment matching pattern")

					t.Logf("Found %d equipment matching pattern: %s",
						len(equipByPattern), pathPattern)
				})
			}

			// Validate spatial hierarchy
			t.Run("ValidateSpatialHierarchy", func(t *testing.T) {
				// Building → Floors → Rooms → Equipment
				for _, floor := range floors {
					assert.Equal(t, building.ID, floor.BuildingID,
						"Floor %s should link to building", floor.Name)

					rooms, _ := roomRepo.GetByFloor(ctx, floor.ID.String())
					for _, room := range rooms {
						assert.Equal(t, floor.ID, room.FloorID,
							"Room %s should link to floor", room.Name)

						// Check if any equipment links to this room
						roomEquip, _ := equipmentRepo.GetByRoom(ctx, room.ID.String())
						for _, eq := range roomEquip {
							assert.Equal(t, room.ID, eq.RoomID,
								"Equipment %s should link to room", eq.Name)
							assert.Equal(t, building.ID, eq.BuildingID,
								"Equipment %s should link to building", eq.Name)
						}
					}
				}
			})
		})
	}
}

// TestIFCImportEdgeCases tests edge cases in IFC import
func TestIFCImportEdgeCases(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	container := setupTestContainer(t)
	if container == nil {
		t.Skip("Test container not available")
	}

	ifcUC := container.GetIFCUseCase()

	t.Run("InvalidIFCData", func(t *testing.T) {
		// Test with invalid IFC data
		invalidData := []byte("This is not an IFC file")
		result, err := ifcUC.ImportIFC(ctx, "test-repo", invalidData)

		// Should handle gracefully
		if err != nil {
			t.Logf("Invalid IFC handled with error: %v", err)
		} else if result != nil {
			t.Logf("Invalid IFC resulted in: %+v", result)
		}
	})

	t.Run("EmptyIFCData", func(t *testing.T) {
		// Test with empty data
		result, err := ifcUC.ImportIFC(ctx, "test-repo", []byte{})

		// Should handle gracefully
		if err != nil {
			t.Logf("Empty IFC handled with error: %v", err)
		} else if result != nil {
			t.Logf("Empty IFC resulted in: %+v", result)
		}
	})
}

// TestIFCImportPerformance tests import performance with large files
func TestIFCImportPerformance(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping performance test in short mode")
	}

	// TODO: Add performance benchmarks
	// - Measure time to import various file sizes
	// - Track memory usage during import
	// - Verify performance is acceptable (< 5s for small files)
	t.Skip("Performance tests - to be implemented")
}
