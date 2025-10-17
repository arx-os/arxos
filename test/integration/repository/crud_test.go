package integration

import (
	"context"
	"fmt"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestBuildingRepositoryCRUD tests core building repository operations
func TestBuildingRepositoryCRUD(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	container := setupTestContainer(t)
	if container == nil {
		t.Skip("Test container not available - requires database")
	}

	repo := container.GetBuildingRepository()

	// Test Create
	t.Run("Create", func(t *testing.T) {
		building := &domain.Building{
			ID:      types.NewID(),
			Name:    "Test Building",
			Address: "123 Test St",
			Coordinates: &domain.Location{
				X: 37.7749,
				Y: -122.4194,
				Z: 0,
			},
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		err := repo.Create(ctx, building)
		require.NoError(t, err, "Should create building")
		assert.NotEmpty(t, building.ID, "Should have ID")
	})

	// Test GetByID
	t.Run("GetByID", func(t *testing.T) {
		// Create test building
		building := &domain.Building{
			ID:        types.NewID(),
			Name:      "Get Test Building",
			Address:   "456 Get St",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}
		err := repo.Create(ctx, building)
		require.NoError(t, err)

		// Get by ID
		retrieved, err := repo.GetByID(ctx, building.ID.String())
		require.NoError(t, err, "Should get building by ID")
		assert.Equal(t, building.ID, retrieved.ID, "Should match ID")
		assert.Equal(t, building.Name, retrieved.Name, "Should match name")
		assert.Equal(t, building.Address, retrieved.Address, "Should match address")
	})

	// Test Update
	t.Run("Update", func(t *testing.T) {
		// Create test building
		building := &domain.Building{
			ID:        types.NewID(),
			Name:      "Update Test Building",
			Address:   "789 Update St",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}
		err := repo.Create(ctx, building)
		require.NoError(t, err)

		// Update
		building.Name = "Updated Building Name"
		building.Address = "999 Updated Ave"
		building.UpdatedAt = time.Now()

		err = repo.Update(ctx, building)
		require.NoError(t, err, "Should update building")

		// Verify update
		retrieved, err := repo.GetByID(ctx, building.ID.String())
		require.NoError(t, err)
		assert.Equal(t, "Updated Building Name", retrieved.Name)
		assert.Equal(t, "999 Updated Ave", retrieved.Address)
	})

	// Test List
	t.Run("List", func(t *testing.T) {
		// Create multiple buildings
		for i := 0; i < 3; i++ {
			building := &domain.Building{
				ID:        types.NewID(),
				Name:      fmt.Sprintf("List Test Building %d", i),
				Address:   fmt.Sprintf("%d List St", i),
				CreatedAt: time.Now(),
				UpdatedAt: time.Now(),
			}
			err := repo.Create(ctx, building)
			require.NoError(t, err)
		}

		// List buildings
		buildings, err := repo.List(ctx, &domain.BuildingFilter{Limit: 10})
		require.NoError(t, err, "Should list buildings")
		assert.GreaterOrEqual(t, len(buildings), 3, "Should have at least 3 buildings")
	})

	// Test Delete
	t.Run("Delete", func(t *testing.T) {
		// Create test building
		building := &domain.Building{
			ID:        types.NewID(),
			Name:      "Delete Test Building",
			Address:   "Delete St",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}
		err := repo.Create(ctx, building)
		require.NoError(t, err)

		// Delete
		err = repo.Delete(ctx, building.ID.String())
		require.NoError(t, err, "Should delete building")

		// Verify deleted
		_, err = repo.GetByID(ctx, building.ID.String())
		assert.Error(t, err, "Should not find deleted building")
	})
}

// TestEquipmentRepositoryCRUD tests equipment repository operations
func TestEquipmentRepositoryCRUD(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	container := setupTestContainer(t)
	if container == nil {
		t.Skip("Test container not available")
	}

	equipmentRepo := container.GetEquipmentRepository()
	buildingRepo := container.GetBuildingRepository()

	// Create test building
	building := &domain.Building{
		ID:        types.NewID(),
		Name:      "Equipment Test Building",
		Address:   "Equipment St",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	err := buildingRepo.Create(ctx, building)
	require.NoError(t, err)

	// Test Create Equipment
	t.Run("Create", func(t *testing.T) {
		equipment := &domain.Equipment{
			ID:         types.NewID(),
			BuildingID: building.ID,
			Name:       "Test Equipment",
			Type:       "hvac",
			Category:   "hvac",
			Status:     "operational",
			Path:       "/TEST/1/101/HVAC/TEST-001",
			Location: &domain.Location{
				X: 10.5,
				Y: 20.3,
				Z: 3.0,
			},
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		err := equipmentRepo.Create(ctx, equipment)
		require.NoError(t, err, "Should create equipment")
		assert.NotEmpty(t, equipment.ID)
	})

	// Test GetByPath (exact match)
	t.Run("GetByPath", func(t *testing.T) {
		path := "/TEST/1/102/HVAC/PATH-TEST-001"
		equipment := &domain.Equipment{
			ID:         types.NewID(),
			BuildingID: building.ID,
			Name:       "Path Test Equipment",
			Type:       "hvac",
			Category:   "hvac",
			Status:     "operational",
			Path:       path,
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		err := equipmentRepo.Create(ctx, equipment)
		require.NoError(t, err)

		// Get by exact path
		retrieved, err := equipmentRepo.GetByPath(ctx, path)
		require.NoError(t, err, "Should get equipment by path")
		assert.Equal(t, equipment.ID, retrieved.ID)
		assert.Equal(t, path, retrieved.Path)
	})

	// Test FindByPath (wildcard patterns)
	t.Run("FindByPath", func(t *testing.T) {
		// Create test equipment with known paths
		paths := []string{
			"/TEST/1/201/HVAC/VAV-201",
			"/TEST/1/202/HVAC/VAV-202",
			"/TEST/2/203/HVAC/VAV-203",
			"/TEST/1/201/NETWORK/SW-201",
		}

		for _, path := range paths {
			equipment := &domain.Equipment{
				ID:         types.NewID(),
				BuildingID: building.ID,
				Name:       "Wildcard Test",
				Type:       "hvac",
				Category:   "hvac",
				Status:     "operational",
				Path:       path,
				CreatedAt:  time.Now(),
				UpdatedAt:  time.Now(),
			}
			err := equipmentRepo.Create(ctx, equipment)
			require.NoError(t, err)
		}

		// Test various wildcard patterns
		tests := []struct {
			pattern     string
			expectedMin int
			description string
		}{
			{"/TEST/1/*/HVAC/*", 2, "All HVAC on floor 1"},
			{"/TEST/*/HVAC/VAV-*", 3, "All VAV boxes"},
			{"/TEST/1/201/*/*", 2, "All equipment in room 201"},
			{"/TEST/*/NETWORK/*", 1, "All network equipment"},
		}

		for _, tt := range tests {
			t.Run(tt.description, func(t *testing.T) {
				equipment, err := equipmentRepo.FindByPath(ctx, tt.pattern)
				require.NoError(t, err, "Pattern should work: %s", tt.pattern)
				assert.GreaterOrEqual(t, len(equipment), tt.expectedMin,
					"Should find at least %d equipment for pattern: %s", tt.expectedMin, tt.pattern)
			})
		}
	})

	// Test GetByBuilding
	t.Run("GetByBuilding", func(t *testing.T) {
		equipment, err := equipmentRepo.GetByBuilding(ctx, building.ID.String())
		require.NoError(t, err, "Should get equipment by building")
		assert.NotEmpty(t, equipment, "Should have equipment")
	})

	// Test Update
	t.Run("Update", func(t *testing.T) {
		equipment := &domain.Equipment{
			ID:         types.NewID(),
			BuildingID: building.ID,
			Name:       "Update Test",
			Type:       "hvac",
			Category:   "hvac",
			Status:     "operational",
			Path:       "/TEST/1/301/HVAC/UPDATE-001",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		err := equipmentRepo.Create(ctx, equipment)
		require.NoError(t, err)

		// Update
		equipment.Status = "maintenance"
		equipment.UpdatedAt = time.Now()
		err = equipmentRepo.Update(ctx, equipment)
		require.NoError(t, err, "Should update equipment")

		// Verify
		retrieved, err := equipmentRepo.GetByID(ctx, equipment.ID.String())
		require.NoError(t, err)
		assert.Equal(t, "maintenance", retrieved.Status)
	})

	// Test Delete
	t.Run("Delete", func(t *testing.T) {
		equipment := &domain.Equipment{
			ID:         types.NewID(),
			BuildingID: building.ID,
			Name:       "Delete Test",
			Type:       "hvac",
			Category:   "hvac",
			Path:       "/TEST/1/401/HVAC/DELETE-001",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		err := equipmentRepo.Create(ctx, equipment)
		require.NoError(t, err)

		// Delete
		err = equipmentRepo.Delete(ctx, equipment.ID.String())
		require.NoError(t, err, "Should delete equipment")

		// Verify
		_, err = equipmentRepo.GetByID(ctx, equipment.ID.String())
		assert.Error(t, err, "Should not find deleted equipment")
	})
}

// TestFloorRepositoryCRUD tests floor repository operations
func TestFloorRepositoryCRUD(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	container := setupTestContainer(t)
	if container == nil {
		t.Skip("Test container not available")
	}

	floorRepo := container.GetFloorRepository()
	buildingRepo := container.GetBuildingRepository()

	// Create test building
	building := &domain.Building{
		ID:        types.NewID(),
		Name:      "Floor Test Building",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	err := buildingRepo.Create(ctx, building)
	require.NoError(t, err)

	t.Run("CreateAndGetByBuilding", func(t *testing.T) {
		// Create floors
		for i := 1; i <= 3; i++ {
			floor := &domain.Floor{
				ID:         types.NewID(),
				BuildingID: building.ID,
				Name:       fmt.Sprintf("Floor %d", i),
				Level:      i,
				CreatedAt:  time.Now(),
				UpdatedAt:  time.Now(),
			}
			err := floorRepo.Create(ctx, floor)
			require.NoError(t, err, "Should create floor %d", i)
		}

		// Get floors by building
		floors, err := floorRepo.GetByBuilding(ctx, building.ID.String())
		require.NoError(t, err, "Should get floors by building")
		assert.Len(t, floors, 3, "Should have 3 floors")

		// Verify ordering by level
		for i, floor := range floors {
			assert.Equal(t, i+1, floor.Level, "Floors should be ordered by level")
		}
	})
}

// TestRoomRepositoryCRUD tests room repository operations
func TestRoomRepositoryCRUD(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	container := setupTestContainer(t)
	if container == nil {
		t.Skip("Test container not available")
	}

	roomRepo := container.GetRoomRepository()
	floorRepo := container.GetFloorRepository()
	buildingRepo := container.GetBuildingRepository()

	// Create test structure
	building := &domain.Building{
		ID:        types.NewID(),
		Name:      "Room Test Building",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	err := buildingRepo.Create(ctx, building)
	require.NoError(t, err)

	floor := &domain.Floor{
		ID:         types.NewID(),
		BuildingID: building.ID,
		Name:       "Test Floor",
		Level:      1,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
	err = floorRepo.Create(ctx, floor)
	require.NoError(t, err)

	t.Run("CreateWithGeometry", func(t *testing.T) {
		room := &domain.Room{
			ID:      types.NewID(),
			FloorID: floor.ID,
			Name:    "Conference Room",
			Number:  "101",
			Location: &domain.Location{
				X: 10.0,
				Y: 20.0,
				Z: 0.0,
			},
			Width:     5.5,
			Height:    4.0,
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		err := roomRepo.Create(ctx, room)
		require.NoError(t, err, "Should create room with geometry")

		// Verify geometry preserved
		retrieved, err := roomRepo.GetByID(ctx, room.ID.String())
		require.NoError(t, err)
		assert.NotNil(t, retrieved.Location)
		assert.Equal(t, 10.0, retrieved.Location.X)
		assert.Equal(t, 5.5, retrieved.Width)
	})

	t.Run("GetByFloor", func(t *testing.T) {
		// Create multiple rooms
		for i := 0; i < 3; i++ {
			room := &domain.Room{
				ID:        types.NewID(),
				FloorID:   floor.ID,
				Name:      fmt.Sprintf("Room %d", i),
				Number:    fmt.Sprintf("10%d", i),
				CreatedAt: time.Now(),
				UpdatedAt: time.Now(),
			}
			err := roomRepo.Create(ctx, room)
			require.NoError(t, err)
		}

		rooms, err := roomRepo.GetByFloor(ctx, floor.ID.String())
		require.NoError(t, err, "Should get rooms by floor")
		assert.GreaterOrEqual(t, len(rooms), 3, "Should have at least 3 rooms")
	})
}
