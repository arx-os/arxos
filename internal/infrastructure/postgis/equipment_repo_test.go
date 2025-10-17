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

// cleanupEquipment removes all equipment from the test database
func cleanupEquipment(t *testing.T, db *sql.DB) {
	t.Helper()
	_, _ = db.Exec("DELETE FROM equipment")
}

func TestEquipmentRepository_Create(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupEquipment(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupEquipment(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	equipRepo := postgis.NewEquipmentRepository(db)
	ctx := context.Background()

	// Create a building first
	building := &domain.Building{
		ID:      types.FromString("test-building-eq"),
		Name:    "Equipment Test Building",
		Address: "Equipment Test Address",
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

	// Create equipment
	equipment := &domain.Equipment{
		ID:         types.FromString("test-equipment-1"),
		BuildingID: building.ID,
		Name:       "HVAC Unit 01",
		Type:       "hvac",
		Model:      "Model-ABC",
		Status:     "operational",
		Location: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 10.5,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err = equipRepo.Create(ctx, equipment)
	require.NoError(t, err)

	// Verify it was created
	retrieved, err := equipRepo.GetByID(ctx, equipment.ID.String())
	require.NoError(t, err)
	assert.Equal(t, equipment.Name, retrieved.Name)
	assert.Equal(t, equipment.Type, retrieved.Type)
	assert.Equal(t, equipment.Model, retrieved.Model)
	assert.Equal(t, equipment.Status, retrieved.Status)
}

func TestEquipmentRepository_GetByID(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupEquipment(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupEquipment(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	equipRepo := postgis.NewEquipmentRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-eq-2"),
		Name:    "Test Building 2",
		Address: "Test Address 2",
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

	// Create equipment
	equipment := &domain.Equipment{
		ID:         types.FromString("test-equipment-2"),
		BuildingID: building.ID,
		Name:       "Lighting Unit 01",
		Type:       "lighting",
		Status:     "operational",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err = equipRepo.Create(ctx, equipment)
	require.NoError(t, err)

	// Test GetByID
	retrieved, err := equipRepo.GetByID(ctx, equipment.ID.String())
	require.NoError(t, err)
	assert.Equal(t, equipment.ID.String(), retrieved.ID.String())
	assert.Equal(t, equipment.Name, retrieved.Name)
	assert.Equal(t, equipment.Type, retrieved.Type)

	// Test non-existent ID
	_, err = equipRepo.GetByID(ctx, "non-existent-id")
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "not found")
}

func TestEquipmentRepository_GetByBuilding(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupEquipment(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupEquipment(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	equipRepo := postgis.NewEquipmentRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-eq-3"),
		Name:    "Test Building 3",
		Address: "Test Address 3",
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

	// Create multiple equipment items
	for i := 1; i <= 3; i++ {
		equipment := &domain.Equipment{
			ID:         types.FromString("test-equipment-building-" + string(rune(i))),
			BuildingID: building.ID,
			Name:       "Equipment " + string(rune(i)),
			Type:       "hvac",
			Status:     "operational",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		err := equipRepo.Create(ctx, equipment)
		require.NoError(t, err)
		time.Sleep(10 * time.Millisecond)
	}

	// Test GetByBuilding
	equipment, err := equipRepo.GetByBuilding(ctx, building.ID.String())
	require.NoError(t, err)
	assert.Len(t, equipment, 3)
}

func TestEquipmentRepository_GetByType(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupEquipment(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupEquipment(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	equipRepo := postgis.NewEquipmentRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-eq-4"),
		Name:    "Test Building 4",
		Address: "Test Address 4",
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

	// Create equipment of different types
	types_list := []string{"hvac", "hvac", "lighting", "security"}
	for i, eqType := range types_list {
		equipment := &domain.Equipment{
			ID:         types.FromString(fmt.Sprintf("test-equipment-type-%d", i)),
			BuildingID: building.ID,
			Name:       fmt.Sprintf("Equipment %d", i),
			Type:       eqType,
			Status:     "operational",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		err := equipRepo.Create(ctx, equipment)
		require.NoError(t, err)
	}

	// Test GetByType for HVAC
	equipment, err := equipRepo.GetByType(ctx, "hvac")
	require.NoError(t, err)
	assert.Len(t, equipment, 2)

	// Test GetByType for lighting
	equipment, err = equipRepo.GetByType(ctx, "lighting")
	require.NoError(t, err)
	assert.Len(t, equipment, 1)
}

func TestEquipmentRepository_Update(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupEquipment(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupEquipment(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	equipRepo := postgis.NewEquipmentRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-eq-5"),
		Name:    "Test Building 5",
		Address: "Test Address 5",
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

	// Create equipment
	equipment := &domain.Equipment{
		ID:         types.FromString("test-equipment-update"),
		BuildingID: building.ID,
		Name:       "Original Name",
		Type:       "hvac",
		Status:     "operational",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err = equipRepo.Create(ctx, equipment)
	require.NoError(t, err)

	// Update the equipment
	equipment.Name = "Updated Name"
	equipment.Status = "maintenance"
	equipment.UpdatedAt = time.Now()

	err = equipRepo.Update(ctx, equipment)
	require.NoError(t, err)

	// Verify update
	retrieved, err := equipRepo.GetByID(ctx, equipment.ID.String())
	require.NoError(t, err)
	assert.Equal(t, "Updated Name", retrieved.Name)
	assert.Equal(t, "maintenance", retrieved.Status)
}

func TestEquipmentRepository_Delete(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupEquipment(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupEquipment(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	equipRepo := postgis.NewEquipmentRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-eq-6"),
		Name:    "Test Building 6",
		Address: "Test Address 6",
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

	// Create equipment
	equipment := &domain.Equipment{
		ID:         types.FromString("test-equipment-delete"),
		BuildingID: building.ID,
		Name:       "To Be Deleted",
		Type:       "hvac",
		Status:     "operational",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err = equipRepo.Create(ctx, equipment)
	require.NoError(t, err)

	// Delete the equipment
	err = equipRepo.Delete(ctx, equipment.ID.String())
	require.NoError(t, err)

	// Verify deletion
	_, err = equipRepo.GetByID(ctx, equipment.ID.String())
	assert.Error(t, err)
	assert.Contains(t, err.Error(), "not found")
}

func TestEquipmentRepository_List(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupEquipment(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupEquipment(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	equipRepo := postgis.NewEquipmentRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-eq-list"),
		Name:    "Test Building List",
		Address: "Test Address List",
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

	// Create multiple equipment items
	for i := 1; i <= 5; i++ {
		equipment := &domain.Equipment{
			ID:         types.FromString("test-equipment-list-" + string(rune(i))),
			BuildingID: building.ID,
			Name:       "List Equipment " + string(rune(i)),
			Type:       "hvac",
			Status:     "operational",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		err := equipRepo.Create(ctx, equipment)
		require.NoError(t, err)
		time.Sleep(10 * time.Millisecond)
	}

	// Test List without filter
	equipment, err := equipRepo.List(ctx, nil)
	require.NoError(t, err)
	assert.GreaterOrEqual(t, len(equipment), 5)

	// Test List with pagination
	filter := &domain.EquipmentFilter{
		Limit:  2,
		Offset: 0,
	}
	equipment, err = equipRepo.List(ctx, filter)
	require.NoError(t, err)
	assert.Len(t, equipment, 2)

	// Test List with building filter
	filter = &domain.EquipmentFilter{
		BuildingID: &building.ID,
	}
	equipment, err = equipRepo.List(ctx, filter)
	require.NoError(t, err)
	assert.Len(t, equipment, 5)

	// Test List with type filter
	eqType := "hvac"
	filter = &domain.EquipmentFilter{
		Type: &eqType,
	}
	equipment, err = equipRepo.List(ctx, filter)
	require.NoError(t, err)
	assert.GreaterOrEqual(t, len(equipment), 5)
}

func TestEquipmentRepository_LocationParsing(t *testing.T) {
	db := setupTestDB(t)
	if db == nil {
		return
	}
	defer db.Close()

	cleanupBuildings(t, db)
	cleanupEquipment(t, db)
	defer cleanupBuildings(t, db)
	defer cleanupEquipment(t, db)

	buildingRepo := postgis.NewBuildingRepository(db)
	equipRepo := postgis.NewEquipmentRepository(db)
	ctx := context.Background()

	// Create a building
	building := &domain.Building{
		ID:      types.FromString("test-building-eq-loc"),
		Name:    "Test Building Location",
		Address: "Test Address Location",
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

	// Create equipment with 3D location
	equipment := &domain.Equipment{
		ID:         types.FromString("test-equipment-loc"),
		BuildingID: building.ID,
		Name:       "Location Equipment",
		Type:       "hvac",
		Status:     "operational",
		Location: &domain.Location{
			X: -122.4194,
			Y: 37.7749,
			Z: 25.5,
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err = equipRepo.Create(ctx, equipment)
	require.NoError(t, err)

	// Retrieve and verify location
	retrieved, err := equipRepo.GetByID(ctx, equipment.ID.String())
	require.NoError(t, err)
	require.NotNil(t, retrieved.Location)
	assert.InDelta(t, equipment.Location.X, retrieved.Location.X, 0.0001)
	assert.InDelta(t, equipment.Location.Y, retrieved.Location.Y, 0.0001)
	assert.InDelta(t, equipment.Location.Z, retrieved.Location.Z, 0.0001)
}
