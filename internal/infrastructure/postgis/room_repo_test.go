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

// cleanupRooms removes all rooms from the test database
func cleanupRooms(t *testing.T, db *sql.DB) {
	t.Helper()
	_, _ = db.Exec("DELETE FROM rooms")
}

func TestRoomRepository_Create(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupFloors(t, db)
	cleanupRooms(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupFloors(t, db)
	defer cleanupRooms(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	floorRepo := postgis.NewFloorRepository(db)
	roomRepo := postgis.NewRoomRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-room"),
		Name:    "Room Test Building",
		Address: "Room Test Address",
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
		Name:       "Test Floor",
		Level:      1,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err = floorRepo.Create(ctx, floor)
	require.NoError(t, err)

	// Create a room
	room := &domain.Room{
		ID:        types.NewID(),
		FloorID:   floor.ID,
		Name:      "Conference Room A",
		Number:    "101",
		Width:     5.0, // 5 meters
		Height:    3.0, // 3 meters
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err = roomRepo.Create(ctx, room)
	require.NoError(t, err)

	// Verify it was created
	retrieved, err := roomRepo.GetByID(ctx, room.ID.String())
	require.NoError(t, err)
	assert.Equal(t, room.Name, retrieved.Name)
	assert.Equal(t, room.Number, retrieved.Number)
}

func TestRoomRepository_GetByFloor(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupFloors(t, db)
	cleanupRooms(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupFloors(t, db)
	defer cleanupRooms(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	floorRepo := postgis.NewFloorRepository(db)
	roomRepo := postgis.NewRoomRepository(db)
	ctx := context.Background()

	// Create building and floor
	building := &domain.Building{
		ID:      types.FromString("test-building-rooms"),
		Name:    "Multi-Room Building",
		Address: "Multi-Room Address",
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

	floor := &domain.Floor{
		ID:         types.NewID(),
		BuildingID: building.ID,
		Name:       "First Floor",
		Level:      1,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err = floorRepo.Create(ctx, floor)
	require.NoError(t, err)

	// Create multiple rooms
	for i := 1; i <= 5; i++ {
		room := &domain.Room{
			ID:        types.NewID(),
			FloorID:   floor.ID,
			Name:      fmt.Sprintf("Room %d", i),
			Number:    fmt.Sprintf("10%d", i),
			Width:     float64(4 + i), // Varying widths 5-9 meters
			Height:    3.0,            // 3 meters
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}
		err := roomRepo.Create(ctx, room)
		require.NoError(t, err)
		time.Sleep(10 * time.Millisecond)
	}

	// Test GetByFloor
	rooms, err := roomRepo.GetByFloor(ctx, floor.ID.String())
	require.NoError(t, err)
	assert.Len(t, rooms, 5)

	// Verify they're sorted by number
	assert.Equal(t, "101", rooms[0].Number)
	assert.Equal(t, "102", rooms[1].Number)
}

func TestRoomRepository_GetByNumber(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupFloors(t, db)
	cleanupRooms(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupFloors(t, db)
	defer cleanupRooms(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	floorRepo := postgis.NewFloorRepository(db)
	roomRepo := postgis.NewRoomRepository(db)
	ctx := context.Background()

	// Create building and floor
	building := &domain.Building{
		ID:      types.FromString("test-building-room-num"),
		Name:    "Room Number Test",
		Address: "Room Number Address",
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

	// Create a room with specific number
	room := &domain.Room{
		ID:        types.NewID(),
		FloorID:   floor.ID,
		Name:      "Room 205",
		Number:    "205",
		Width:     6.0, // 6 meters
		Height:    3.0, // 3 meters
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err = roomRepo.Create(ctx, room)
	require.NoError(t, err)

	// Test GetByNumber
	retrieved, err := roomRepo.GetByNumber(ctx, floor.ID.String(), "205")
	require.NoError(t, err)
	assert.Equal(t, room.Name, retrieved.Name)
	assert.Equal(t, room.Number, retrieved.Number)

	// Test non-existent room number
	_, err = roomRepo.GetByNumber(ctx, floor.ID.String(), "999")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "not found")
}

func TestRoomRepository_Update(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupFloors(t, db)
	cleanupRooms(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupFloors(t, db)
	defer cleanupRooms(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	floorRepo := postgis.NewFloorRepository(db)
	roomRepo := postgis.NewRoomRepository(db)
	ctx := context.Background()

	// Create building and floor
	building := &domain.Building{
		ID:      types.FromString("test-building-room-update"),
		Name:    "Update Test",
		Address: "Update Address",
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

	// Create a room
	room := &domain.Room{
		ID:        types.NewID(),
		FloorID:   floor.ID,
		Name:      "Original Name",
		Number:    "100",
		Width:     4.5, // 4.5 meters
		Height:    3.0, // 3 meters
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err = roomRepo.Create(ctx, room)
	require.NoError(t, err)

	// Update the room
	room.Name = "Updated Room Name"
	room.Number = "101"
	room.UpdatedAt = time.Now()

	err = roomRepo.Update(ctx, room)
	require.NoError(t, err)

	// Verify update
	retrieved, err := roomRepo.GetByID(ctx, room.ID.String())
	require.NoError(t, err)
	assert.Equal(t, "Updated Room Name", retrieved.Name)
	assert.Equal(t, "101", retrieved.Number)
}

func TestRoomRepository_Delete(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupFloors(t, db)
	cleanupRooms(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupFloors(t, db)
	defer cleanupRooms(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	floorRepo := postgis.NewFloorRepository(db)
	roomRepo := postgis.NewRoomRepository(db)
	ctx := context.Background()

	// Create building and floor
	building := &domain.Building{
		ID:      types.FromString("test-building-room-delete"),
		Name:    "Delete Test",
		Address: "Delete Address",
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

	// Create a room
	room := &domain.Room{
		ID:        types.NewID(),
		FloorID:   floor.ID,
		Name:      "To Be Deleted",
		Number:    "999",
		Width:     5.5, // 5.5 meters
		Height:    3.0, // 3 meters
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err = roomRepo.Create(ctx, room)
	require.NoError(t, err)

	// Delete the room
	err = roomRepo.Delete(ctx, room.ID.String())
	require.NoError(t, err)

	// Verify deletion
	_, err = roomRepo.GetByID(ctx, room.ID.String())
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "not found")
}
