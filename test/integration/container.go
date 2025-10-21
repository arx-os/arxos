package integration

import (
	"context"
	"database/sql"
	"fmt"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain/bas"
	"github.com/arx-os/arxos/internal/domain/versioncontrol"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	buildinguc "github.com/arx-os/arxos/internal/usecase/building"
	usecaseintegration "github.com/arx-os/arxos/internal/usecase/integration"
	"github.com/stretchr/testify/require"
)

// TestContainer wraps app.Container with test-specific utilities
type TestContainer struct {
	*app.Container
	DB     *sql.DB
	TX     *sql.Tx
	Logger domain.Logger
}

// SetupTestContainer initializes a full test container with all dependencies
// This is the main entry point for integration tests
func SetupTestContainer(t *testing.T) *TestContainer {
	t.Helper()

	// Setup test database
	db := SetupTestDB(t)
	if db == nil {
		return nil
	}

	// Verify migrations
	RunMigrations(t, db)

	// Create test container wrapper
	testContainer := &TestContainer{
		Container: nil, // Not using full app container for now
		DB:        db,
		TX:        nil,
		Logger:    nil, // Use Go test logger
	}

	t.Log("Test container initialized with database connection")
	return testContainer
}

// SetupTestContainerWithTransaction creates a test container with transaction isolation
// The transaction will be rolled back on cleanup, ensuring tests don't affect each other
func SetupTestContainerWithTransaction(t *testing.T) *TestContainer {
	t.Helper()

	// Setup database with transaction
	db, tx := SetupTestDBWithTransaction(t)
	if db == nil || tx == nil {
		return nil
	}

	// For transaction-based testing, we need to pass the transaction to repositories
	// This requires repositories to accept *sql.Tx instead of *sql.DB
	// For now, we'll use the non-transactional approach and rely on cleanup

	container := SetupTestContainer(t)
	if container != nil {
		container.TX = tx

		// Register cleanup to rollback
		t.Cleanup(func() {
			CleanupTestData(t, db)
		})
	}

	return container
}

// Helper methods to access repositories and use cases

func (tc *TestContainer) GetBuildingRepository() domain.BuildingRepository {
	return postgis.NewBuildingRepository(tc.DB)
}

func (tc *TestContainer) GetFloorRepository() domain.FloorRepository {
	return postgis.NewFloorRepository(tc.DB)
}

func (tc *TestContainer) GetRoomRepository() domain.RoomRepository {
	return postgis.NewRoomRepository(tc.DB)
}

func (tc *TestContainer) GetEquipmentRepository() domain.EquipmentRepository {
	return postgis.NewEquipmentRepository(tc.DB)
}

func (tc *TestContainer) GetOrganizationRepository() domain.OrganizationRepository {
	return postgis.NewOrganizationRepository(tc.DB)
}

func (tc *TestContainer) GetBASPointRepository() bas.BASPointRepository {
	return postgis.NewBASPointRepository(tc.DB)
}

func (tc *TestContainer) GetBASSystemRepository() bas.BASSystemRepository {
	return postgis.NewBASSystemRepository(tc.DB)
}

func (tc *TestContainer) GetBranchRepository() versioncontrol.BranchRepository {
	return postgis.NewBranchRepository(tc.DB)
}

func (tc *TestContainer) GetCommitRepository() versioncontrol.CommitRepository {
	return postgis.NewCommitRepository(tc.DB)
}

func (tc *TestContainer) GetBuildingUseCase() *buildinguc.BuildingUseCase {
	return buildinguc.NewBuildingUseCase(
		tc.GetBuildingRepository(),
		tc.GetEquipmentRepository(),
		nil, // logger - tests use t.Log
	)
}

func (tc *TestContainer) GetEquipmentUseCase() *buildinguc.EquipmentUseCase {
	return buildinguc.NewEquipmentUseCase(
		tc.GetEquipmentRepository(),
		tc.GetBuildingRepository(),
		tc.GetFloorRepository(),
		tc.GetRoomRepository(),
		tc.Logger,
	)
}

func (tc *TestContainer) GetIFCUseCase() *usecaseintegration.IFCUseCase {
	// Note: IFC service initialization simplified for tests
	// Full IFC import tests will skip if service is not available
	// TODO: Initialize enhanced IFC service when needed for full IFC import tests

	return usecaseintegration.NewIFCUseCase(
		nil, // repo repo - not needed for basic tests
		nil, // ifc repo - not needed for basic tests
		nil, // validator - not needed for basic tests
		nil, // enhanced service - TODO: create when needed
		tc.GetBuildingRepository(),
		tc.GetFloorRepository(),
		tc.GetRoomRepository(),
		tc.GetEquipmentRepository(),
		nil, // logger - tests use t.Log
	)
}

// CreateTestBuilding creates a test building for use in tests
func (tc *TestContainer) CreateTestBuilding(t *testing.T, name string) *domain.Building {
	t.Helper()

	buildingRepo := tc.GetBuildingRepository()
	building := &domain.Building{
		Name:      name,
		Address:   "123 Test Street",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err := buildingRepo.Create(context.Background(), building)
	require.NoError(t, err, "Failed to create test building")

	t.Logf("Created test building: %s (ID: %s)", building.Name, building.ID)
	return building
}

// CreateTestFloor creates a test floor for use in tests
func (tc *TestContainer) CreateTestFloor(t *testing.T, buildingID types.ID, level int) *domain.Floor {
	t.Helper()

	floorRepo := tc.GetFloorRepository()
	floor := &domain.Floor{
		BuildingID: buildingID,
		Name:       fmt.Sprintf("Floor %d", level),
		Level:      level,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err := floorRepo.Create(context.Background(), floor)
	require.NoError(t, err, "Failed to create test floor")

	t.Logf("Created test floor: %s (ID: %s)", floor.Name, floor.ID)
	return floor
}

// CreateTestRoom creates a test room for use in tests
func (tc *TestContainer) CreateTestRoom(t *testing.T, floorID types.ID, number string) *domain.Room {
	t.Helper()

	roomRepo := tc.GetRoomRepository()
	room := &domain.Room{
		FloorID:   floorID,
		Name:      "Test Room " + number,
		Number:    number,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err := roomRepo.Create(context.Background(), room)
	require.NoError(t, err, "Failed to create test room")

	t.Logf("Created test room: %s (ID: %s)", room.Name, room.ID)
	return room
}

// CreateTestEquipment creates test equipment for use in tests
func (tc *TestContainer) CreateTestEquipment(t *testing.T, buildingID, roomID types.ID, name, path string) *domain.Equipment {
	t.Helper()

	equipmentRepo := tc.GetEquipmentRepository()
	equipment := &domain.Equipment{
		BuildingID: buildingID,
		RoomID:     roomID,
		Name:       name,
		Type:       "hvac",
		Category:   "hvac",
		Status:     "operational",
		Path:       path,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err := equipmentRepo.Create(context.Background(), equipment)
	require.NoError(t, err, "Failed to create test equipment")

	t.Logf("Created test equipment: %s (ID: %s, Path: %s)", equipment.Name, equipment.ID, equipment.Path)
	return equipment
}
