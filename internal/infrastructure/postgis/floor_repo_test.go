package postgis_test

import (
	"context"
	"database/sql"
	"fmt"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// cleanupFloors removes all floors from the test database
func cleanupFloors(t *testing.T, db *sql.DB) {
	t.Helper()
	_, _ = db.Exec("DELETE FROM floors")
}

func TestFloorRepository_Create(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupFloors(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupFloors(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	floorRepo := postgis.NewFloorRepository(db)
	ctx := context.Background()

	// Create a building first
	building := &domain.Building{
		ID:      types.FromString("test-building-floor"),
		Name:    "Floor Test Building",
		Address: "Floor Test Address",
		Coordinates: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err := buildingRepo.Create(ctx, building)
	require.NoError(t, err)

	// Create a floor
	floor := &domain.Floor{
		ID:         types.NewID(),
		BuildingID: building.ID,
		Name:       "Ground Floor",
		Level:      0,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err = floorRepo.Create(ctx, floor)
	require.NoError(t, err)

	// Verify it was created
	retrieved, err := floorRepo.GetByID(ctx, floor.ID.String())
	require.NoError(t, err)
	assert.Equal(t, floor.Name, retrieved.Name)
	assert.Equal(t, floor.Level, retrieved.Level)
}

func TestFloorRepository_GetByBuilding(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupFloors(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupFloors(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	floorRepo := postgis.NewFloorRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-floors"),
		Name:    "Multi-Floor Building",
		Address: "Multi-Floor Address",
		Coordinates: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err := buildingRepo.Create(ctx, building)
	require.NoError(t, err)

	// Create multiple floors
	for i := 0; i < 5; i++ {
		floor := &domain.Floor{
			ID:         types.NewID(),
			BuildingID: building.ID,
			Name:       fmt.Sprintf("Floor %d", i),
			Level:      i,
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		err := floorRepo.Create(ctx, floor)
		require.NoError(t, err)
		time.Sleep(10 * time.Millisecond)
	}

	// Test GetByBuilding
	floors, err := floorRepo.GetByBuilding(ctx, building.ID.String())
	require.NoError(t, err)
	assert.Len(t, floors, 5)

	// Verify they're sorted by level
	for i, floor := range floors {
		assert.Equal(t, i, floor.Level)
	}
}

func TestFloorRepository_Update(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupFloors(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupFloors(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	floorRepo := postgis.NewFloorRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-update"),
		Name:    "Update Test Building",
		Address: "Update Test Address",
		Coordinates: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err := buildingRepo.Create(ctx, building)
	require.NoError(t, err)

	// Create a floor
	floor := &domain.Floor{
		ID:         types.NewID(),
		BuildingID: building.ID,
		Name:       "Original Name",
		Level:      1,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err = floorRepo.Create(ctx, floor)
	require.NoError(t, err)

	// Update the floor
	floor.Name = "Updated Floor Name"
	floor.Level = 2
	floor.UpdatedAt = time.Now()

	err = floorRepo.Update(ctx, floor)
	require.NoError(t, err)

	// Verify update
	retrieved, err := floorRepo.GetByID(ctx, floor.ID.String())
	require.NoError(t, err)
	assert.Equal(t, "Updated Floor Name", retrieved.Name)
	assert.Equal(t, 2, retrieved.Level)
}

func TestFloorRepository_Delete(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupFloors(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupFloors(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	floorRepo := postgis.NewFloorRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-delete"),
		Name:    "Delete Test Building",
		Address: "Delete Test Address",
		Coordinates: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err := buildingRepo.Create(ctx, building)
	require.NoError(t, err)

	// Create a floor
	floor := &domain.Floor{
		ID:         types.NewID(),
		BuildingID: building.ID,
		Name:       "To Be Deleted",
		Level:      1,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err = floorRepo.Create(ctx, floor)
	require.NoError(t, err)

	// Delete the floor
	err = floorRepo.Delete(ctx, floor.ID.String())
	require.NoError(t, err)

	// Verify deletion
	_, err = floorRepo.GetByID(ctx, floor.ID.String())
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "not found")
}
