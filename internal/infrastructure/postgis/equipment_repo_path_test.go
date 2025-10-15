package postgis

import (
	"context"
	"database/sql"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestEquipmentRepository_GetByPath(t *testing.T) {
	// Setup test database
	db := setupTestDB(t)
	defer cleanupTestDB(t, db)

	repo := NewEquipmentRepository(db)
	ctx := context.Background()

	// Create test equipment with path
	equipment := &domain.Equipment{
		ID:         types.NewID(),
		BuildingID: types.NewID(),
		FloorID:    types.NewID(),
		RoomID:     types.NewID(),
		Name:       "Test VAV Box",
		Path:       "/B1/3/301/HVAC/VAV-301",
		Type:       "hvac",
		Status:     "active",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err := repo.Create(ctx, equipment)
	require.NoError(t, err, "should create equipment")

	// Test: Get by exact path
	t.Run("Get by exact path", func(t *testing.T) {
		retrieved, err := repo.GetByPath(ctx, "/B1/3/301/HVAC/VAV-301")
		require.NoError(t, err, "should retrieve equipment by path")
		assert.Equal(t, equipment.ID.String(), retrieved.ID.String())
		assert.Equal(t, equipment.Name, retrieved.Name)
		assert.Equal(t, equipment.Path, retrieved.Path)
	})

	// Test: Path not found
	t.Run("Path not found", func(t *testing.T) {
		_, err := repo.GetByPath(ctx, "/B1/3/302/HVAC/VAV-302")
		assert.Error(t, err, "should return error for non-existent path")
		assert.Contains(t, err.Error(), "not found")
	})

	// Test: Case sensitivity
	t.Run("Case sensitivity", func(t *testing.T) {
		_, err := repo.GetByPath(ctx, "/b1/3/301/hvac/vav-301")
		assert.Error(t, err, "path queries should be case-sensitive")
	})
}

func TestEquipmentRepository_FindByPath(t *testing.T) {
	// Setup test database
	db := setupTestDB(t)
	defer cleanupTestDB(t, db)

	repo := NewEquipmentRepository(db)
	ctx := context.Background()

	// Create test equipment with paths
	testEquipment := []*domain.Equipment{
		{
			ID:         types.NewID(),
			BuildingID: types.NewID(),
			Name:       "VAV-301",
			Path:       "/B1/3/301/HVAC/VAV-301",
			Type:       "hvac",
			Status:     "active",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		},
		{
			ID:         types.NewID(),
			BuildingID: types.NewID(),
			Name:       "VAV-302",
			Path:       "/B1/3/302/HVAC/VAV-302",
			Type:       "hvac",
			Status:     "active",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		},
		{
			ID:         types.NewID(),
			BuildingID: types.NewID(),
			Name:       "SW-01",
			Path:       "/B1/2/IDF-2A/NETWORK/SW-01",
			Type:       "network",
			Status:     "active",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		},
		{
			ID:         types.NewID(),
			BuildingID: types.NewID(),
			Name:       "EXTING-01",
			Path:       "/B1/2/HALL-2A/SAFETY/EXTING-01",
			Type:       "safety",
			Status:     "active",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		},
	}

	// Create all test equipment
	for _, eq := range testEquipment {
		err := repo.Create(ctx, eq)
		require.NoError(t, err, "should create test equipment")
	}

	// Test: Find all HVAC on floor 3
	t.Run("Find all HVAC on floor 3", func(t *testing.T) {
		results, err := repo.FindByPath(ctx, "/B1/3/*/HVAC/*")
		require.NoError(t, err, "should find equipment")
		assert.Len(t, results, 2, "should find 2 HVAC equipment on floor 3")
		
		// Verify results are sorted by path
		assert.Equal(t, "/B1/3/301/HVAC/VAV-301", results[0].Path)
		assert.Equal(t, "/B1/3/302/HVAC/VAV-302", results[1].Path)
	})

	// Test: Find all network equipment
	t.Run("Find all network equipment", func(t *testing.T) {
		results, err := repo.FindByPath(ctx, "/B1/*/NETWORK/*")
		require.NoError(t, err, "should find equipment")
		assert.Len(t, results, 1, "should find 1 network equipment")
		assert.Equal(t, "SW-01", results[0].Name)
	})

	// Test: Find equipment in specific room
	t.Run("Find equipment in specific room", func(t *testing.T) {
		results, err := repo.FindByPath(ctx, "/B1/3/301/*")
		require.NoError(t, err, "should find equipment")
		assert.Len(t, results, 1, "should find 1 equipment in room 301")
		assert.Equal(t, "VAV-301", results[0].Name)
	})

	// Test: Find by equipment type prefix
	t.Run("Find by equipment name pattern", func(t *testing.T) {
		results, err := repo.FindByPath(ctx, "/B1/*/HVAC/VAV-*")
		require.NoError(t, err, "should find equipment")
		assert.Len(t, results, 2, "should find 2 VAV boxes")
	})

	// Test: Find all safety equipment
	t.Run("Find all safety equipment", func(t *testing.T) {
		results, err := repo.FindByPath(ctx, "/*/*/SAFETY/*")
		require.NoError(t, err, "should find equipment")
		assert.Len(t, results, 1, "should find 1 safety equipment")
		assert.Equal(t, "EXTING-01", results[0].Name)
	})

	// Test: No matches found
	t.Run("No matches found", func(t *testing.T) {
		results, err := repo.FindByPath(ctx, "/B1/4/*/HVAC/*")
		require.NoError(t, err, "should not error on no results")
		assert.Len(t, results, 0, "should find 0 equipment on non-existent floor")
	})

	// Test: Pattern too broad (should error)
	t.Run("Pattern too broad", func(t *testing.T) {
		_, err := repo.FindByPath(ctx, "%")
		assert.Error(t, err, "should reject overly broad pattern")
		assert.Contains(t, err.Error(), "too broad")
	})

	// Test: Multiple wildcards
	t.Run("Multiple wildcards", func(t *testing.T) {
		results, err := repo.FindByPath(ctx, "/B1/*/*/HVAC/*")
		require.NoError(t, err, "should handle multiple wildcards")
		assert.Len(t, results, 2, "should find 2 HVAC equipment")
	})
}

func TestEquipmentRepository_PathWithNullValues(t *testing.T) {
	// Setup test database
	db := setupTestDB(t)
	defer cleanupTestDB(t, db)

	repo := NewEquipmentRepository(db)
	ctx := context.Background()

	// Create equipment without path (legacy data scenario)
	equipment := &domain.Equipment{
		ID:         types.NewID(),
		BuildingID: types.NewID(),
		Name:       "Legacy Equipment",
		Path:       "", // No path
		Type:       "electrical",
		Status:     "active",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err := repo.Create(ctx, equipment)
	require.NoError(t, err, "should create equipment without path")

	// Test: Get by ID should still work
	t.Run("Get by ID works without path", func(t *testing.T) {
		retrieved, err := repo.GetByID(ctx, equipment.ID.String())
		require.NoError(t, err, "should retrieve equipment by ID")
		assert.Equal(t, "", retrieved.Path, "path should be empty")
	})

	// Test: FindByPath should not return equipment without paths
	t.Run("Path query excludes equipment without paths", func(t *testing.T) {
		results, err := repo.FindByPath(ctx, "/B1/*")
		require.NoError(t, err, "should not error")
		assert.Len(t, results, 0, "should not find equipment without path")
	})
}

// Test helper functions

func setupTestDB(t *testing.T) *sql.DB {
	// This is a placeholder - in real tests, you'd connect to a test database
	// For now, we'll skip these tests if no test database is configured
	t.Skip("Test database not configured - implement test database setup")
	var db *sql.DB
	return db
}

func cleanupTestDB(t *testing.T, db *sql.DB) {
	// Cleanup test data
	if db != nil {
		db.Close()
	}
}

