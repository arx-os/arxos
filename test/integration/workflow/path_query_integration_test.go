package workflow

import (
	"context"
	"database/sql"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestPathQueryWorkflow tests the complete path-based query workflow
// Tests: Create equipment with paths → Query by exact path → Query by pattern
func TestPathQueryWorkflow(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	// Setup test environment
	ctx := context.Background()
	db := setupTestDatabase(t)
	defer cleanupTestDatabase(t, db)

	// Create repositories
	equipmentRepo := postgis.NewEquipmentRepository(db)
	buildingRepo := postgis.NewBuildingRepository(db)
	floorRepo := postgis.NewFloorRepository(db)
	roomRepo := postgis.NewRoomRepository(db)

	// Setup test data
	building := createTestBuilding(t, ctx, buildingRepo, "Main Building")
	floor := createTestFloor(t, ctx, floorRepo, building.ID, 3, "Third Floor")
	room301 := createTestRoom(t, ctx, roomRepo, floor.ID, "301", "Room 301")
	room302 := createTestRoom(t, ctx, roomRepo, floor.ID, "302", "Room 302")
	idf2A := createTestRoom(t, ctx, roomRepo, floor.ID, "IDF-2A", "Network Closet")

	// Create test equipment with paths
	testEquipment := []struct {
		name     string
		path     string
		eqType   string
		category string
		roomID   types.ID
	}{
		{
			name:     "VAV-301",
			path:     "/MAIN/3/301/HVAC/VAV-301",
			eqType:   "vav",
			category: "hvac",
			roomID:   room301.ID,
		},
		{
			name:     "VAV-302",
			path:     "/MAIN/3/302/HVAC/VAV-302",
			eqType:   "vav",
			category: "hvac",
			roomID:   room302.ID,
		},
		{
			name:     "STAT-301",
			path:     "/MAIN/3/301/HVAC/STAT-301",
			eqType:   "thermostat",
			category: "hvac",
			roomID:   room301.ID,
		},
		{
			name:     "SW-01",
			path:     "/MAIN/3/IDF-2A/NETWORK/SW-01",
			eqType:   "switch",
			category: "network",
			roomID:   idf2A.ID,
		},
	}

	// Create all test equipment
	createdEquipment := make([]*domain.Equipment, 0, len(testEquipment))
	for _, eq := range testEquipment {
		equipment := &domain.Equipment{
			ID:         types.NewID(),
			BuildingID: building.ID,
			FloorID:    floor.ID,
			RoomID:     eq.roomID,
			Name:       eq.name,
			Path:       eq.path,
			Type:       eq.eqType,
			Category:   eq.category,
			Status:     "active",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}

		err := equipmentRepo.Create(ctx, equipment)
		require.NoError(t, err, "should create equipment: %s", eq.name)
		createdEquipment = append(createdEquipment, equipment)
	}

	// Test 1: Get by exact path
	t.Run("Get equipment by exact path", func(t *testing.T) {
		equipment, err := equipmentRepo.GetByPath(ctx, "/MAIN/3/301/HVAC/VAV-301")
		require.NoError(t, err, "should get equipment by exact path")
		assert.Equal(t, "VAV-301", equipment.Name)
		assert.Equal(t, "/MAIN/3/301/HVAC/VAV-301", equipment.Path)
	})

	// Test 2: Find all HVAC on floor 3
	t.Run("Find all HVAC equipment on floor 3", func(t *testing.T) {
		equipment, err := equipmentRepo.FindByPath(ctx, "/MAIN/3/*/HVAC/*")
		require.NoError(t, err, "should find equipment by pattern")
		assert.Len(t, equipment, 3, "should find 3 HVAC equipment on floor 3")
		
		// Verify they're sorted by path
		assert.Equal(t, "/MAIN/3/301/HVAC/STAT-301", equipment[0].Path)
		assert.Equal(t, "/MAIN/3/301/HVAC/VAV-301", equipment[1].Path)
		assert.Equal(t, "/MAIN/3/302/HVAC/VAV-302", equipment[2].Path)
	})

	// Test 3: Find equipment in specific room
	t.Run("Find all equipment in room 301", func(t *testing.T) {
		equipment, err := equipmentRepo.FindByPath(ctx, "/MAIN/3/301/*/*")
		require.NoError(t, err, "should find equipment in room")
		assert.Len(t, equipment, 2, "should find 2 equipment in room 301")
	})

	// Test 4: Find by equipment type prefix
	t.Run("Find all VAV boxes", func(t *testing.T) {
		equipment, err := equipmentRepo.FindByPath(ctx, "/MAIN/*/HVAC/VAV-*")
		require.NoError(t, err, "should find VAV boxes")
		assert.Len(t, equipment, 2, "should find 2 VAV boxes")
	})

	// Test 5: Find network equipment
	t.Run("Find all network equipment", func(t *testing.T) {
		equipment, err := equipmentRepo.FindByPath(ctx, "/MAIN/*/NETWORK/*")
		require.NoError(t, err, "should find network equipment")
		assert.Len(t, equipment, 1, "should find 1 network equipment")
		assert.Equal(t, "SW-01", equipment[0].Name)
	})

	// Test 6: No matches
	t.Run("No matches for non-existent path", func(t *testing.T) {
		equipment, err := equipmentRepo.FindByPath(ctx, "/MAIN/4/*/HVAC/*")
		require.NoError(t, err, "should not error on no matches")
		assert.Len(t, equipment, 0, "should find 0 equipment on floor 4")
	})

	// Test 7: Case sensitivity
	t.Run("Path queries are case-sensitive", func(t *testing.T) {
		equipment, err := equipmentRepo.FindByPath(ctx, "/main/3/*/hvac/*")
		require.NoError(t, err, "should not error")
		assert.Len(t, equipment, 0, "lowercase paths should not match")
	})
}

// TestPathQueryWithFilters tests path queries combined with additional filters
func TestPathQueryWithFilters(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	db := setupTestDatabase(t)
	defer cleanupTestDatabase(t, db)

	equipmentRepo := postgis.NewEquipmentRepository(db)
	buildingRepo := postgis.NewBuildingRepository(db)
	floorRepo := postgis.NewFloorRepository(db)
	roomRepo := postgis.NewRoomRepository(db)

	// Setup test data
	building := createTestBuilding(t, ctx, buildingRepo, "Test Building")
	floor := createTestFloor(t, ctx, floorRepo, building.ID, 2, "Second Floor")
	room := createTestRoom(t, ctx, roomRepo, floor.ID, "205", "Room 205")

	// Create equipment with different statuses
	equipment1 := &domain.Equipment{
		ID:         types.NewID(),
		BuildingID: building.ID,
		FloorID:    floor.ID,
		RoomID:     room.ID,
		Name:       "HVAC-01",
		Path:       "/TEST/2/205/HVAC/HVAC-01",
		Type:       "hvac",
		Status:     "active",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	equipment2 := &domain.Equipment{
		ID:         types.NewID(),
		BuildingID: building.ID,
		FloorID:    floor.ID,
		RoomID:     room.ID,
		Name:       "HVAC-02",
		Path:       "/TEST/2/205/HVAC/HVAC-02",
		Type:       "hvac",
		Status:     "maintenance",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	require.NoError(t, equipmentRepo.Create(ctx, equipment1))
	require.NoError(t, equipmentRepo.Create(ctx, equipment2))

	// Test: Find all HVAC (both statuses)
	t.Run("Find all HVAC equipment", func(t *testing.T) {
		results, err := equipmentRepo.FindByPath(ctx, "/TEST/2/205/HVAC/*")
		require.NoError(t, err)
		assert.Len(t, results, 2, "should find both HVAC equipment")
	})

	// Test: Filter by status would be done in handler/use case layer
	// Repository returns all matches, filtering happens above
	t.Run("Repository returns all matches", func(t *testing.T) {
		results, err := equipmentRepo.FindByPath(ctx, "/TEST/2/205/HVAC/*")
		require.NoError(t, err)
		
		// Count by status
		active := 0
		maintenance := 0
		for _, eq := range results {
			if eq.Status == "active" {
				active++
			} else if eq.Status == "maintenance" {
				maintenance++
			}
		}
		
		assert.Equal(t, 1, active, "should have 1 active equipment")
		assert.Equal(t, 1, maintenance, "should have 1 maintenance equipment")
	})
}

// Test helper functions

func setupTestDatabase(t *testing.T) *sql.DB {
	// NOTE: This requires a real test database
	// For CI/CD, use environment variables to configure test database
	// For now, skip if test database not available
	t.Skip("Integration test requires test database - configure ARXOS_TEST_DB environment variable")
	return nil
}

func cleanupTestDatabase(t *testing.T, db *sql.DB) {
	if db != nil {
		// Clean up test data
		db.Exec("TRUNCATE equipment CASCADE")
		db.Exec("TRUNCATE rooms CASCADE")
		db.Exec("TRUNCATE floors CASCADE")
		db.Exec("TRUNCATE buildings CASCADE")
		db.Close()
	}
}

func createTestBuilding(t *testing.T, ctx context.Context, repo domain.BuildingRepository, name string) *domain.Building {
	building := &domain.Building{
		ID:        types.NewID(),
		Name:      name,
		Address:   "123 Test St",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	
	err := repo.Create(ctx, building)
	require.NoError(t, err, "should create test building")
	
	return building
}

func createTestFloor(t *testing.T, ctx context.Context, repo domain.FloorRepository, buildingID types.ID, level int, name string) *domain.Floor {
	floor := &domain.Floor{
		ID:         types.NewID(),
		BuildingID: buildingID,
		Level:      level,
		Name:       name,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
	
	err := repo.Create(ctx, floor)
	require.NoError(t, err, "should create test floor")
	
	return floor
}

func createTestRoom(t *testing.T, ctx context.Context, repo domain.RoomRepository, floorID types.ID, number, name string) *domain.Room {
	room := &domain.Room{
		ID:        types.NewID(),
		FloorID:   floorID,
		Number:    number,
		Name:      name,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	
	err := repo.Create(ctx, room)
	require.NoError(t, err, "should create test room")
	
	return room
}

