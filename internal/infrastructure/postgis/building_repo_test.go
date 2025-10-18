package postgis_test

import (
	"context"
	"database/sql"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	_ "github.com/lib/pq"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// setupTestDB creates a test database connection
func setupTestDB(t *testing.T) *sql.DB {
	t.Helper()

	// Use test database credentials
	dsn := "host=localhost port=5432 user=arxos_test password=test_password dbname=arxos_test sslmode=disable"
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Skipf("Cannot connect to test database: %v", err)
		return nil
	}

	// Verify connection
	if err := db.Ping(); err != nil {
		t.Skipf("Cannot ping test database: %v", err)
		return nil
	}

	return db
}

// cleanupBuildings removes all buildings from the test database
func cleanupBuildings(t *testing.T, db *sql.DB) {
	t.Helper()
	_, _ = db.Exec("DELETE FROM equipment")
	_, _ = db.Exec("DELETE FROM floors")
	_, _ = db.Exec("DELETE FROM buildings")
}

func TestBuildingRepository_Create(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	defer cleanupBuildings(t, db)

	repo := postgis.NewBuildingRepository(db)
	ctx := context.Background()

	building := &domain.Building{
		ID:      types.FromString("test-building-1"),
		Name:    "Test Building",
		Address: "123 Test Street",
		Coordinates: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err := repo.Create(ctx, building)
	require.NoError(t, err)

	// Verify it was created
	retrieved, err := repo.GetByID(ctx, building.ID.String())
	require.NoError(t, err)
	assert.Equal(t, building.Name, retrieved.Name)
	assert.Equal(t, building.Address, retrieved.Address)
	assert.NotNil(t, retrieved.Coordinates)
}

func TestBuildingRepository_GetByID(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	defer cleanupBuildings(t, db)

	repo := postgis.NewBuildingRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-2"),
		Name:    "Test Building 2",
		Address: "456 Test Avenue",
		Coordinates: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err := repo.Create(ctx, building)
	require.NoError(t, err)

	// Test GetByID
	retrieved, err := repo.GetByID(ctx, building.ID.String())
	require.NoError(t, err)
	assert.Equal(t, building.ID.String(), retrieved.ID.String())
	assert.Equal(t, building.Name, retrieved.Name)
	assert.Equal(t, building.Address, retrieved.Address)

	// Test non-existent ID
	_, err = repo.GetByID(ctx, "non-existent-id")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "not found")
}

func TestBuildingRepository_GetByAddress(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	defer cleanupBuildings(t, db)

	repo := postgis.NewBuildingRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-3"),
		Name:    "Test Building 3",
		Address: "789 Unique Address",
		Coordinates: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err := repo.Create(ctx, building)
	require.NoError(t, err)

	// Test GetByAddress
	retrieved, err := repo.GetByAddress(ctx, building.Address)
	require.NoError(t, err)
	assert.Equal(t, building.ID.String(), retrieved.ID.String())
	assert.Equal(t, building.Name, retrieved.Name)

	// Test non-existent address
	_, err = repo.GetByAddress(ctx, "non-existent-address")
	assert.Error(t, err)
}

func TestBuildingRepository_Update(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	defer cleanupBuildings(t, db)

	repo := postgis.NewBuildingRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-4"),
		Name:    "Original Name",
		Address: "Original Address",
		Coordinates: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err := repo.Create(ctx, building)
	require.NoError(t, err)

	// Update the building
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
}

func TestBuildingRepository_Delete(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	defer cleanupBuildings(t, db)

	repo := postgis.NewBuildingRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-5"),
		Name:    "To Be Deleted",
		Address: "Delete Address",
		Coordinates: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err := repo.Create(ctx, building)
	require.NoError(t, err)

	// Delete the building
	err = repo.Delete(ctx, building.ID.String())
	require.NoError(t, err)

	// Verify deletion
	_, err = repo.GetByID(ctx, building.ID.String())
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "not found")
}

func TestBuildingRepository_List(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	defer cleanupBuildings(t, db)

	repo := postgis.NewBuildingRepository(db)
	ctx := context.Background()

	// Create multiple buildings
	for i := 1; i <= 5; i++ {
		building := &domain.Building{
			ID:      types.FromString("test-building-list-" + string(rune(i))),
			Name:    "List Building " + string(rune(i)),
			Address: "List Address " + string(rune(i)),
			Coordinates: &domain.Location{
				X: -122.4194,
				Y: 37.7749,
				Z: 0,
			},
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}
		err := repo.Create(ctx, building)
		require.NoError(t, err)
		time.Sleep(10 * time.Millisecond) // Ensure different timestamps
	}

	// Test List without filter
	buildings, err := repo.List(ctx, nil)
	require.NoError(t, err)
	assert.GreaterOrEqual(t, len(buildings), 5)

	// Test List with pagination
	filter := &domain.BuildingFilter{
		Limit:  2,
		Offset: 0,
	}
	buildings, err = repo.List(ctx, filter)
	require.NoError(t, err)
	assert.Len(t, buildings, 2)

	// Test List with name filter
	nameFilter := "List Building"
	filter = &domain.BuildingFilter{
		Name: &nameFilter,
	}
	buildings, err = repo.List(ctx, filter)
	require.NoError(t, err)
	assert.GreaterOrEqual(t, len(buildings), 5)
}

func TestBuildingRepository_GetFloors(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	defer cleanupBuildings(t, db)

	repo := postgis.NewBuildingRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-floors"),
		Name:    "Building with Floors",
		Address: "Floors Address",
		Coordinates: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 0,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err := repo.Create(ctx, building)
	require.NoError(t, err)

	// Create some floors
	for i := 1; i <= 3; i++ {
		_, err := db.Exec(`
			INSERT INTO floors (id, building_id, name, level, created_at, updated_at)
			VALUES ($1, $2, $3, $4, $5, $6)
		`,
			"floor-"+building.ID.String()+"-"+string(rune(i)),
			building.ID.String(),
			"Floor "+string(rune(i)),
			i,
			time.Now(),
			time.Now(),
		)
		require.NoError(t, err)
	}

	// Test GetFloors
	floors, err := repo.GetFloors(ctx, building.ID.String())
	require.NoError(t, err)
	assert.Len(t, floors, 3)
	assert.Equal(t, 1, floors[0].Level)
	assert.Equal(t, 2, floors[1].Level)
	assert.Equal(t, 3, floors[2].Level)
}

func TestBuildingRepository_CoordinateParsing(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	defer cleanupBuildings(t, db)

	repo := postgis.NewBuildingRepository(db)
	ctx := context.Background()

	testCases := []struct {
		name   string
		coords *domain.Location
	}{
		{
			name: "2D Coordinates",
			coords: &domain.Location{
				X: -122.4194,
				Y: 37.7749,
				Z: 0,
			},
		},
		{
			name: "3D Coordinates",
			coords: &domain.Location{
				X: -122.4194,
				Y: 37.7749,
				Z: 150.5,
			},
		},
	}

	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			building := &domain.Building{
				ID:          types.FromString("test-coords-" + tc.name),
				Name:        "Coords Test " + tc.name,
				Address:     "Coords Address " + tc.name,
				Coordinates: tc.coords,
				CreatedAt:   time.Now(),
				UpdatedAt:   time.Now(),
			}

			err := repo.Create(ctx, building)
			require.NoError(t, err)

			// Retrieve and verify coordinates
			retrieved, err := repo.GetByID(ctx, building.ID.String())
			require.NoError(t, err)
			require.NotNil(t, retrieved.Coordinates)
			assert.InDelta(t, tc.coords.X, retrieved.Coordinates.X, 0.0001)
			assert.InDelta(t, tc.coords.Y, retrieved.Coordinates.Y, 0.0001)
			// Note: Buildings table only stores lat/lon (2D), Z coordinate is not persisted
			// This is expected - buildings use geographic coordinates, not full 3D
			if tc.name != "3D Coordinates" {
				assert.InDelta(t, tc.coords.Z, retrieved.Coordinates.Z, 0.0001)
			} else {
				assert.Equal(t, 0.0, retrieved.Coordinates.Z, "Z coordinate not stored in buildings table (2D only)")
			}
		})
	}
}
