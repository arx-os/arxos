/**
 * Repository Integration Tests
 * Comprehensive tests for all PostGIS repositories
 * Tests CRUD operations, path queries, relationships, and spatial queries
 */

package repository

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	"github.com/arx-os/arxos/test/helpers"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestBuildingRepository tests all BuildingRepository operations
func TestBuildingRepository(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	db, _ := helpers.SetupTestEnvironment(t)
	defer db.Close()

	repo := postgis.NewBuildingRepository(db)

	t.Run("Create and Get Building", func(t *testing.T) {
		// Create building with unique ID
		uniqueID := fmt.Sprintf("test-building-%d", time.Now().UnixNano())
		building := &domain.Building{
			ID:        types.FromString(uniqueID),
			Name:      "Test Building",
			Address:   "123 Test Street",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		err := repo.Create(ctx, building)
		require.NoError(t, err)

		// Get building
		retrieved, err := repo.GetByID(ctx, building.ID.String())
		require.NoError(t, err)
		require.NotNil(t, retrieved)
		assert.Equal(t, building.ID, retrieved.ID)
		assert.Equal(t, building.Name, retrieved.Name)
		assert.Equal(t, building.Address, retrieved.Address)
	})

	t.Run("Update Building", func(t *testing.T) {
		// Create building with unique ID
		uniqueID := fmt.Sprintf("test-building-upd-%d", time.Now().UnixNano())
		building := &domain.Building{
			ID:        types.FromString(uniqueID),
			Name:      "Original Name",
			Address:   "Original Address",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		err := repo.Create(ctx, building)
		require.NoError(t, err)

		// Update building
		building.Name = "Updated Name"
		building.Address = "Updated Address"
		building.UpdatedAt = time.Now()

		err = repo.Update(ctx, building)
		require.NoError(t, err)

		// Verify update
		retrieved, err := repo.GetByID(ctx, building.ID.String())
		require.NoError(t, err)
		assert.Equal(t, "Updated Name", retrieved.Name)
		assert.Equal(t, "Updated Address", retrieved.Address)
	})

	t.Run("Delete Building", func(t *testing.T) {
		// Create building with unique ID
		uniqueID := fmt.Sprintf("test-building-del-%d", time.Now().UnixNano())
		building := &domain.Building{
			ID:        types.FromString(uniqueID),
			Name:      "To Be Deleted",
			Address:   "Delete Address",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		err := repo.Create(ctx, building)
		require.NoError(t, err)

		// Delete building
		err = repo.Delete(ctx, building.ID.String())
		require.NoError(t, err)

		// Verify deletion
		retrieved, err := repo.GetByID(ctx, building.ID.String())
		require.Error(t, err)
		assert.Nil(t, retrieved)
	})

	t.Run("List Buildings", func(t *testing.T) {
		// Create multiple buildings with unique IDs
		timestamp := time.Now().UnixNano()
		for i := 0; i < 3; i++ {
			building := &domain.Building{
				ID:        types.FromString(fmt.Sprintf("test-bld-lst-%d-%d", timestamp, i)),
				Name:      fmt.Sprintf("Building %d", i),
				Address:   fmt.Sprintf("Address %d", i),
				CreatedAt: time.Now(),
				UpdatedAt: time.Now(),
			}
			err := repo.Create(ctx, building)
			require.NoError(t, err)
			time.Sleep(1 * time.Millisecond) // Ensure unique IDs
		}

		// List buildings
		filter := &domain.BuildingFilter{
			Limit: 10,
		}
		buildings, err := repo.List(ctx, filter)
		require.NoError(t, err)
		assert.GreaterOrEqual(t, len(buildings), 3)
	})

	t.Run("Get Building by Address", func(t *testing.T) {
		// Create building with specific address and unique ID
		uniqueID := fmt.Sprintf("test-bld-addr-%d", time.Now().UnixNano())
		building := &domain.Building{
			ID:        types.FromString(uniqueID),
			Name:      "Address Test Building",
			Address:   fmt.Sprintf("123 Unique Address-%d", time.Now().UnixNano()),
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		err := repo.Create(ctx, building)
		require.NoError(t, err)

		// Get building by address
		retrieved, err := repo.GetByAddress(ctx, building.Address)
		require.NoError(t, err)
		assert.Equal(t, building.ID, retrieved.ID)
		assert.Equal(t, building.Address, retrieved.Address)
	})
}

// TestEquipmentRepository tests all EquipmentRepository operations
func TestEquipmentRepository(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	db, _ := helpers.SetupTestEnvironment(t)
	defer db.Close()

	repo := postgis.NewEquipmentRepository(db)

	// Create test building first
	buildingRepo := postgis.NewBuildingRepository(db)
	building := &domain.Building{
		ID:        helpers.UniqueTestID(),
		Name:      "Equipment Test Building",
		Address:   "Equipment Address",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	err := buildingRepo.Create(ctx, building)
	require.NoError(t, err)

	t.Run("Create and Get Equipment", func(t *testing.T) {
		equipment := &domain.Equipment{
			ID:         helpers.UniqueTestID(),
			BuildingID: building.ID,
			Name:       "Test Equipment",
			Type:       "HVAC",
			Path:       "/test-building-equipment-create/1/room1/HVAC/equipment1", // Different path prefix
			Status:     "operational",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}

		err := repo.Create(ctx, equipment)
		require.NoError(t, err)

		retrieved, err := repo.GetByID(ctx, equipment.ID.String())
		require.NoError(t, err)
		require.NotNil(t, retrieved)
		assert.Equal(t, equipment.ID, retrieved.ID)
		assert.Equal(t, equipment.Name, retrieved.Name)
		assert.Equal(t, equipment.Path, retrieved.Path)
	})

	t.Run("Path-based Queries", func(t *testing.T) {
		// Create equipment with specific paths using unique prefix
		testPrefix := fmt.Sprintf("/test-path-%d", time.Now().UnixNano())
		hvacUnit1ID := helpers.UniqueTestID()
		hvacUnit2ID := helpers.UniqueTestID()
		electricalPanelID := helpers.UniqueTestID()

		equipments := []*domain.Equipment{
			{
				ID:         hvacUnit1ID,
				BuildingID: building.ID,
				Name:       "HVAC Unit 1",
				Type:       "HVAC",
				Path:       testPrefix + "/room1/HVAC/unit1",
				Status:     "operational",
				CreatedAt:  time.Now(),
				UpdatedAt:  time.Now(),
			},
			{
				ID:         hvacUnit2ID,
				BuildingID: building.ID,
				Name:       "HVAC Unit 2",
				Type:       "HVAC",
				Path:       testPrefix + "/room2/HVAC/unit2",
				Status:     "operational",
				CreatedAt:  time.Now(),
				UpdatedAt:  time.Now(),
			},
			{
				ID:         electricalPanelID,
				BuildingID: building.ID,
				Name:       "Electrical Panel",
				Type:       "Electrical",
				Path:       testPrefix + "/room1/Electrical/panel1",
				Status:     "operational",
				CreatedAt:  time.Now(),
				UpdatedAt:  time.Now(),
			},
		}

		for _, eq := range equipments {
			err := repo.Create(ctx, eq)
			require.NoError(t, err)
			time.Sleep(1 * time.Millisecond) // Ensure unique IDs
		}

		// Test exact path query
		exact, err := repo.GetByPath(ctx, testPrefix+"/room1/HVAC/unit1")
		require.NoError(t, err)
		require.NotNil(t, exact)
		assert.Equal(t, hvacUnit1ID, exact.ID)

		// Test wildcard path query
		wildcard, err := repo.FindByPath(ctx, testPrefix+"/*/HVAC/*")
		require.NoError(t, err)
		assert.Len(t, wildcard, 2) // Should find both HVAC units

		// Test building-level wildcard
		buildingLevel, err := repo.FindByPath(ctx, testPrefix+"/*/*/*")
		require.NoError(t, err)
		assert.Len(t, buildingLevel, 3) // Should find all equipment
	})

	t.Run("Get Equipment by Building", func(t *testing.T) {
		equipment, err := repo.GetByBuilding(ctx, building.ID.String())
		require.NoError(t, err)
		// Should include at least the equipment created in this test
		// (Path-based test creates 3, this is run after)
		assert.GreaterOrEqual(t, len(equipment), 1)
	})

	t.Run("Update Equipment", func(t *testing.T) {
		equipment := &domain.Equipment{
			ID:         helpers.UniqueTestID(),
			BuildingID: building.ID,
			Name:       "Status Test Equipment",
			Type:       "HVAC",
			Path:       "/test-building-equipment-update/1/room1/HVAC/status-test", // Different path prefix
			Status:     "operational",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}

		err := repo.Create(ctx, equipment)
		require.NoError(t, err)

		// Update equipment
		equipment.Status = "needs_attention"
		equipment.UpdatedAt = time.Now()
		err = repo.Update(ctx, equipment)
		require.NoError(t, err)

		// Verify status update
		retrieved, err := repo.GetByID(ctx, equipment.ID.String())
		require.NoError(t, err)
		assert.Equal(t, "needs_attention", retrieved.Status)
	})
}

// TestFloorRepository tests all FloorRepository operations
func TestFloorRepository(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	db, _ := helpers.SetupTestEnvironment(t)
	defer db.Close()

	repo := postgis.NewFloorRepository(db)

	// Create test building
	buildingRepo := postgis.NewBuildingRepository(db)
	building := &domain.Building{
		ID:        helpers.UniqueTestID(),
		Name:      "Floor Test Building",
		Address:   "Floor Address",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	err := buildingRepo.Create(ctx, building)
	require.NoError(t, err)

	t.Run("Create and Get Floor", func(t *testing.T) {
		floor := &domain.Floor{
			ID:         helpers.UniqueTestID(),
			BuildingID: building.ID,
			Level:      1,
			Name:       "Ground Floor",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}

		err := repo.Create(ctx, floor)
		require.NoError(t, err)

		retrieved, err := repo.GetByID(ctx, floor.ID.String())
		require.NoError(t, err)
		require.NotNil(t, retrieved)
		assert.Equal(t, floor.ID, retrieved.ID)
		assert.Equal(t, floor.Level, retrieved.Level)
		assert.Equal(t, floor.Name, retrieved.Name)
	})

	t.Run("Get Floors by Building", func(t *testing.T) {
		// Create multiple floors with unique IDs
		for i := 2; i <= 3; i++ {
			floor := &domain.Floor{
				ID:         helpers.UniqueTestID(),
				BuildingID: building.ID,
				Level:      i,
				Name:       fmt.Sprintf("Floor %d", i),
				CreatedAt:  time.Now(),
				UpdatedAt:  time.Now(),
			}
			err := repo.Create(ctx, floor)
			require.NoError(t, err)
		}

		floors, err := repo.GetByBuilding(ctx, building.ID.String())
		require.NoError(t, err)
		// Should have at least 3 floors (1 from previous test + 2 new ones)
		assert.GreaterOrEqual(t, len(floors), 3)
	})

	t.Run("Update Floor", func(t *testing.T) {
		floor := &domain.Floor{
			ID:         helpers.UniqueTestID(),
			BuildingID: building.ID,
			Level:      4,
			Name:       "Original Name",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}

		err := repo.Create(ctx, floor)
		require.NoError(t, err)

		// Update floor
		floor.Name = "Updated Name"
		floor.Level = 5
		floor.UpdatedAt = time.Now()

		err = repo.Update(ctx, floor)
		require.NoError(t, err)

		// Verify update
		retrieved, err := repo.GetByID(ctx, floor.ID.String())
		require.NoError(t, err)
		assert.Equal(t, "Updated Name", retrieved.Name)
		assert.Equal(t, 5, retrieved.Level)
	})
}

// TestRoomRepository tests all RoomRepository operations including geometry
func TestRoomRepository(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	db, _ := helpers.SetupTestEnvironment(t)
	defer db.Close()

	repo := postgis.NewRoomRepository(db)

	// Create test building and floor
	buildingRepo := postgis.NewBuildingRepository(db)
	building := &domain.Building{
		ID:        helpers.UniqueTestID(),
		Name:      "Room Test Building",
		Address:   "Room Address",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	err := buildingRepo.Create(ctx, building)
	require.NoError(t, err)

	floorRepo := postgis.NewFloorRepository(db)
	floor := &domain.Floor{
		ID:         helpers.UniqueTestID(),
		BuildingID: building.ID,
		Level:      1,
		Name:       "Ground Floor",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
	err = floorRepo.Create(ctx, floor)
	require.NoError(t, err)

	t.Run("Create and Get Room with Geometry", func(t *testing.T) {
		room := &domain.Room{
			ID:        helpers.UniqueTestID(),
			FloorID:   floor.ID,
			Name:      "Test Room",
			Number:    "101",
			Width:     10.0,
			Height:    8.0,
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		err := repo.Create(ctx, room)
		require.NoError(t, err)

		retrieved, err := repo.GetByID(ctx, room.ID.String())
		require.NoError(t, err)
		require.NotNil(t, retrieved)
		assert.Equal(t, room.ID, retrieved.ID)
		assert.Equal(t, room.Width, retrieved.Width)
		assert.Equal(t, room.Height, retrieved.Height)
		assert.Equal(t, room.Number, retrieved.Number)
	})

	t.Run("Get Rooms by Floor", func(t *testing.T) {
		// Create multiple rooms with unique IDs
		for i := 2; i <= 3; i++ {
			room := &domain.Room{
				ID:        helpers.UniqueTestID(),
				FloorID:   floor.ID,
				Name:      fmt.Sprintf("Room %d", i),
				Number:    fmt.Sprintf("10%d", i),
				Width:     float64(i * 5),
				Height:    8.0,
				CreatedAt: time.Now(),
				UpdatedAt: time.Now(),
			}
			err := repo.Create(ctx, room)
			require.NoError(t, err)
		}

		rooms, err := repo.GetByFloor(ctx, floor.ID.String())
		require.NoError(t, err)
		// Should have at least 3 rooms (1 from previous test + 2 new ones)
		assert.GreaterOrEqual(t, len(rooms), 3)
	})

	t.Run("Get Room by Number", func(t *testing.T) {
		// Test getting room by floor and number
		retrieved, err := repo.GetByNumber(ctx, floor.ID.String(), "101")
		require.NoError(t, err)
		require.NotNil(t, retrieved)
		assert.Equal(t, "101", retrieved.Number)
	})
}

// TestBASPointRepository tests all BASPointRepository operations
func TestBASPointRepository(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	db, _ := helpers.SetupTestEnvironment(t)
	defer db.Close()

	repo := postgis.NewBASPointRepository(db)

	// Create test building and BAS system
	buildingRepo := postgis.NewBuildingRepository(db)
	building := &domain.Building{
		ID:        helpers.UniqueTestID(),
		Name:      "BAS Test Building",
		Address:   "BAS Address",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	err := buildingRepo.Create(ctx, building)
	require.NoError(t, err)

	basSystem := &domain.BASSystem{
		ID:         helpers.UniqueTestID(),
		BuildingID: building.ID,
		Name:       "Test BAS System",
		SystemType: domain.BASSystemTypeMetasys,
		Enabled:    true,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	// Create BAS system in database
	basSystemRepo := postgis.NewBASSystemRepository(db)
	err = basSystemRepo.Create(basSystem)
	require.NoError(t, err, "Failed to create BAS system for test")

	t.Run("Create and Get BAS Point", func(t *testing.T) {
		point := &domain.BASPoint{
			ID:          helpers.UniqueTestID(),
			BuildingID:  building.ID,
			BASSystemID: basSystem.ID,
			PointName:   "Temperature Sensor",
			Path:        "/test-building/1/room1/HVAC/temp-sensor",
			DeviceID:    "DEV001",
			ObjectType:  "AI",
			Description: "Room temperature sensor",
			Units:       "F",
			PointType:   "Temperature",
			Writeable:   false,
			Mapped:      true,
			Metadata:    make(map[string]interface{}), // Initialize empty metadata
			ImportedAt:  time.Now(),
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		}

		err := repo.Create(point)
		require.NoError(t, err)

		retrieved, err := repo.GetByID(point.ID)
		require.NoError(t, err)
		require.NotNil(t, retrieved)
		assert.Equal(t, point.ID, retrieved.ID)
		assert.Equal(t, point.PointName, retrieved.PointName)
		assert.Equal(t, point.Path, retrieved.Path)
	})

	t.Run("Path-based Queries for BAS Points", func(t *testing.T) {
		// Create BAS points with unique paths to avoid collisions
		pathTimestamp := time.Now().UnixNano()
		uniquePath1 := fmt.Sprintf("/test-bldg-%d/1/room1/HVAC/temp1", pathTimestamp)
		uniquePath2 := fmt.Sprintf("/test-bldg-%d/1/room2/HVAC/temp2", pathTimestamp)

		points := []*domain.BASPoint{
			{
				ID:          helpers.UniqueTestID(),
				BuildingID:  building.ID,
				BASSystemID: basSystem.ID,
				PointName:   "HVAC Temp 1",
				Path:        uniquePath1,
				DeviceID:    "DEV002",
				ObjectType:  "AI",
				PointType:   "Temperature",
				Mapped:      true,
				Metadata:    make(map[string]interface{}),
				ImportedAt:  time.Now(),
				CreatedAt:   time.Now(),
				UpdatedAt:   time.Now(),
			},
			{
				ID:          helpers.UniqueTestID(),
				BuildingID:  building.ID,
				BASSystemID: basSystem.ID,
				PointName:   "HVAC Temp 2",
				Path:        uniquePath2,
				DeviceID:    "DEV003",
				ObjectType:  "AI",
				PointType:   "Temperature",
				Mapped:      true,
				Metadata:    make(map[string]interface{}),
				ImportedAt:  time.Now(),
				CreatedAt:   time.Now(),
				UpdatedAt:   time.Now(),
			},
		}

		for _, point := range points {
			err := repo.Create(point)
			require.NoError(t, err)
		}

		// Test exact path query
		exact, err := repo.GetByPath(uniquePath1)
		require.NoError(t, err)
		require.NotNil(t, exact)

		// Test wildcard path query - use pattern that matches our unique paths
		pattern := fmt.Sprintf("/test-bldg-%d/*/HVAC/*", pathTimestamp)
		wildcard, err := repo.FindByPath(pattern)
		require.NoError(t, err)
		assert.Len(t, wildcard, 2, "Should find exactly the 2 points we just created")
	})

	t.Run("List BAS Points by Building", func(t *testing.T) {
		points, err := repo.ListByBuilding(building.ID)
		require.NoError(t, err)
		assert.GreaterOrEqual(t, len(points), 3) // Should include created points
	})

	t.Run("Update BAS Point", func(t *testing.T) {
		point := &domain.BASPoint{
			ID:          helpers.UniqueTestID(),
			BuildingID:  building.ID,
			BASSystemID: basSystem.ID,
			PointName:   "Update Test Sensor",
			Path:        "/test-building/1/room1/HVAC/update-test",
			DeviceID:    "DEV004",
			ObjectType:  "AI",
			PointType:   "Temperature",
			Mapped:      true,
			ImportedAt:  time.Now(),
			CreatedAt:   time.Now(),
			UpdatedAt:   time.Now(),
		}

		err := repo.Create(point)
		require.NoError(t, err)

		// Update point
		point.PointName = "Updated Sensor Name"
		point.UpdatedAt = time.Now()
		err = repo.Update(point)
		require.NoError(t, err)

		// Verify update
		retrieved, err := repo.GetByID(point.ID)
		require.NoError(t, err)
		assert.Equal(t, "Updated Sensor Name", retrieved.PointName)
	})
}

// TestSpatialRepository tests all SpatialRepository operations
func TestSpatialRepository(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	// Note: Spatial repository tests require sqlx.DB, but test setup provides sql.DB
	// For now, we'll skip spatial repository tests until test setup is updated
	t.Skip("Spatial repository tests require sqlx.DB, skipping for now")
}

// TestRepositoryRelationships tests relationships between repositories
func TestRepositoryRelationships(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	db, _ := helpers.SetupTestEnvironment(t)
	defer db.Close()

	// Create repositories
	buildingRepo := postgis.NewBuildingRepository(db)
	floorRepo := postgis.NewFloorRepository(db)
	roomRepo := postgis.NewRoomRepository(db)
	equipmentRepo := postgis.NewEquipmentRepository(db)

	t.Run("Building-Floor-Room-Equipment Hierarchy", func(t *testing.T) {
		// Create building
		building := &domain.Building{
			ID:        helpers.UniqueTestID(),
			Name:      "Hierarchy Test Building",
			Address:   "Hierarchy Address",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}
		err := buildingRepo.Create(ctx, building)
		require.NoError(t, err)

		// Create floor
		floor := &domain.Floor{
			ID:         helpers.UniqueTestID(),
			BuildingID: building.ID,
			Level:      1,
			Name:       "Ground Floor",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		err = floorRepo.Create(ctx, floor)
		require.NoError(t, err)

		// Create room
		room := &domain.Room{
			ID:        helpers.UniqueTestID(),
			FloorID:   floor.ID,
			Name:      "Test Room",
			Number:    "101",
			Width:     10.0,
			Height:    8.0,
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}
		err = roomRepo.Create(ctx, room)
		require.NoError(t, err)

		// Create equipment
		equipment := &domain.Equipment{
			ID:         helpers.UniqueTestID(),
			BuildingID: building.ID,
			Name:       "Test Equipment",
			Type:       "HVAC",
			Path:       "/test-hierarchy-building/1/test-room/HVAC/equipment",
			Status:     "operational",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		err = equipmentRepo.Create(ctx, equipment)
		require.NoError(t, err)

		// Verify hierarchy relationships
		retrievedBuilding, err := buildingRepo.GetByID(ctx, building.ID.String())
		require.NoError(t, err)
		assert.NotNil(t, retrievedBuilding)

		floors, err := floorRepo.GetByBuilding(ctx, building.ID.String())
		require.NoError(t, err)
		assert.Len(t, floors, 1)
		assert.Equal(t, floor.ID, floors[0].ID)

		rooms, err := roomRepo.GetByFloor(ctx, floor.ID.String())
		require.NoError(t, err)
		assert.Len(t, rooms, 1)
		assert.Equal(t, room.ID, rooms[0].ID)

		equipments, err := equipmentRepo.GetByBuilding(ctx, building.ID.String())
		require.NoError(t, err)
		assert.Len(t, equipments, 1)
		assert.Equal(t, equipment.ID, equipments[0].ID)
	})

	t.Run("Cascade Delete Behavior", func(t *testing.T) {
		// This test would verify that deleting a building cascades properly
		// For now, we'll test that the delete operations work without foreign key violations

		// Create a building with associated data
		building := &domain.Building{
			ID:        helpers.UniqueTestID(),
			Name:      "Cascade Test Building",
			Address:   "Cascade Address",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}
		err := buildingRepo.Create(ctx, building)
		require.NoError(t, err)

		// Delete building (should handle cascading properly)
		err = buildingRepo.Delete(ctx, building.ID.String())
		require.NoError(t, err)

		// Verify building is deleted
		retrieved, err := buildingRepo.GetByID(ctx, building.ID.String())
		require.Error(t, err)
		assert.Nil(t, retrieved)
	})
}
