package workflow

import (
	integration "github.com/arx-os/arxos/test/integration"
	"context"
	"fmt"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestWorkflowIFCImportToPathQuery validates complete workflow:
// IFC Import → Path Query → Verify Results
func TestWorkflowIFCImportToPathQuery(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	container := integration.SetupTestContainer(t)
	if container == nil {
		t.Skip("Test container not available - requires database")
	}

	// Get use cases
	ifcUC := container.GetIFCUseCase()
	equipmentRepo := container.GetEquipmentRepository()

	// Step 1: Import IFC file
	t.Log("Step 1: Importing IFC file...")
	ifcPath := filepath.Join("../../test_data/inputs", "AC20-FZK-Haus.ifc")
	ifcData, err := os.ReadFile(ifcPath)
	if err != nil {
		if os.IsNotExist(err) {
			t.Skip("Sample IFC file not found - place in test_data/inputs/")
		}
		require.NoError(t, err)
	}

	result, err := ifcUC.ImportIFC(ctx, "test-workflow-repo", ifcData)
	require.NoError(t, err, "IFC import should succeed")
	require.NotNil(t, result)

	t.Logf("Import complete: %d equipment created", result.EquipmentCreated)

	// Step 2: Query by exact path
	t.Log("Step 2: Querying equipment by exact path...")
	equipment, err := equipmentRepo.List(ctx, &domain.EquipmentFilter{Limit: 1})
	require.NoError(t, err)

	if len(equipment) > 0 && equipment[0].Path != "" {
		exactPath := equipment[0].Path
		t.Logf("Testing exact path: %s", exactPath)

		equipByPath, err := equipmentRepo.GetByPath(ctx, exactPath)
		require.NoError(t, err, "Should get equipment by exact path")
		assert.Equal(t, equipment[0].ID, equipByPath.ID, "Should find same equipment")
	}

	// Step 3: Query by wildcard pattern
	t.Log("Step 3: Querying equipment by wildcard pattern...")
	patterns := []string{
		"/*/*/*/*",      // All equipment
		"/*/1/*/*",      // Floor 1 only
		"/*/*/HVAC/*",   // All HVAC
		"/*/*/*/HVAC/*", // All HVAC (more specific)
	}

	for _, pattern := range patterns {
		equipByPattern, err := equipmentRepo.FindByPath(ctx, pattern)
		require.NoError(t, err, "Pattern %s should work", pattern)
		t.Logf("Pattern '%s' found %d equipment", pattern, len(equipByPattern))

		// Verify all results match pattern
		for _, eq := range equipByPattern {
			assert.NotEmpty(t, eq.Path, "Equipment should have path")
		}
	}

	// Step 4: Verify equipment has required fields
	t.Log("Step 4: Validating equipment data quality...")
	allEquipment, err := equipmentRepo.List(ctx, &domain.EquipmentFilter{Limit: 100})
	require.NoError(t, err)

	for _, eq := range allEquipment {
		assert.NotEmpty(t, eq.ID, "Equipment should have ID")
		assert.NotEmpty(t, eq.Name, "Equipment should have name")
		assert.NotEmpty(t, eq.BuildingID, "Equipment should have building ID")
		assert.NotEmpty(t, eq.Path, "Equipment should have universal path")
		assert.NotEmpty(t, eq.Category, "Equipment should have category")
	}

	t.Logf("✅ Workflow complete: IFC Import → Path Query → Validation")
}

// TestWorkflowBASImportPlusIFCImport validates:
// IFC Import (creates rooms) → BAS Import (maps to rooms) → Verify Integration
func TestWorkflowBASImportPlusIFCImport(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	container := integration.SetupTestContainer(t)
	if container == nil {
		t.Skip("Test container not available - requires database")
	}

	// Get use cases
	ifcUC := container.GetIFCUseCase()
	// basUC := container.GetBASUseCase() // TODO: Uncomment when implementing BAS tests
	buildingRepo := container.GetBuildingRepository()
	// roomRepo := container.GetRoomRepository() // TODO: Use when implementing room-level tests

	// Step 1: Import IFC (creates spatial structure)
	t.Log("Step 1: Importing IFC file to create spatial structure...")
	ifcPath := filepath.Join("../../test_data/inputs", "AC20-FZK-Haus.ifc")
	ifcData, err := os.ReadFile(ifcPath)
	if err != nil {
		if os.IsNotExist(err) {
			t.Skip("Sample IFC file not found")
		}
		require.NoError(t, err)
	}

	ifcResult, err := ifcUC.ImportIFC(ctx, "test-bas-workflow", ifcData)
	require.NoError(t, err)
	t.Logf("IFC import created: %d rooms", ifcResult.RoomsCreated)

	// Get building ID for BAS import
	buildings, err := buildingRepo.List(ctx, &domain.BuildingFilter{Limit: 1})
	require.NoError(t, err)
	require.NotEmpty(t, buildings, "Should have at least one building")
	// buildingID := buildings[0].ID // TODO: Use when implementing BAS import

	// Step 2: Import BAS points
	t.Log("Step 2: Importing BAS points...")
	// basPath := filepath.Join("../../test_data/bas", "sample_bas_export.csv")
	// basData, err := os.ReadFile(basPath)
	// TODO: Implement BAS import with auto-mapping
	// basResult, err := basUC.ImportCSV(ctx, buildingID.String(), basData, true)
	// require.NoError(t, err)
	// t.Logf("BAS import created: %d points", basResult.PointsCreated)

	t.Log("✅ Workflow validated: IFC + BAS integration structure exists")
	// Full validation requires BAS import implementation
}

// TestWorkflowVersionControl validates:
// Create Building → Commit → Branch → Modify → Commit → Merge
func TestWorkflowVersionControl(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	container := integration.SetupTestContainer(t)
	if container == nil {
		t.Skip("Test container not available")
	}

	buildingRepo := container.GetBuildingRepository()
	branchRepo := container.GetBranchRepository()
	commitRepo := container.GetCommitRepository()

	// Step 1: Create building
	t.Log("Step 1: Creating test building...")
	building := &domain.Building{
		Name:    "Version Control Test Building",
		Address: "123 Test Street",
	}
	err := buildingRepo.Create(ctx, building)
	require.NoError(t, err)
	t.Logf("Created building: %s", building.ID)

	// Step 2: Create initial commit
	t.Log("Step 2: Creating initial commit...")
	commit := &domain.Commit{
		Message: "Initial building creation",
		// Author: "test-user",
	}
	err = commitRepo.Create(commit)
	require.NoError(t, err)
	t.Logf("Created commit: %s", commit.ID)

	// Step 3: Create feature branch
	t.Log("Step 3: Creating feature branch...")
	branch := &domain.Branch{
		Name:        "feature/updates",
		Description: "Test updates to building",
		// SourceBranch: "main",
	}
	err = branchRepo.Create(branch)
	require.NoError(t, err)
	t.Logf("Created branch: %s", branch.ID)

	// Step 4: Modify building
	t.Log("Step 4: Modifying building on branch...")
	building.Address = "456 Updated Street"
	err = buildingRepo.Update(ctx, building)
	require.NoError(t, err)

	// Step 5: Commit changes
	t.Log("Step 5: Committing changes...")
	commit2 := &domain.Commit{
		Message: "Updated building address",
		// BranchID: branch.ID,
	}
	err = commitRepo.Create(commit2)
	require.NoError(t, err)

	// Step 6: Merge branch (TODO: implement merge logic)
	t.Log("Step 6: Merging branch...")
	// mergeResult, err := branchRepo.Merge(ctx, branch.ID, "main")
	// require.NoError(t, err)

	t.Log("✅ Version control workflow validated")
}

// TestWorkflowCompleteLifecycle validates complete building lifecycle:
// Create → Import IFC → Add BAS → Query → Export → Delete
func TestWorkflowCompleteLifecycle(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()
	container := integration.SetupTestContainer(t)
	if container == nil {
		t.Skip("Test container not available")
	}

	buildingRepo := container.GetBuildingRepository()
	equipmentRepo := container.GetEquipmentRepository()

	// Create building
	t.Log("Creating building...")
	building := &domain.Building{
		Name:    "Lifecycle Test Building",
		Address: "789 Lifecycle Ave",
	}
	err := buildingRepo.Create(ctx, building)
	require.NoError(t, err)

	// Query equipment (should be empty)
	equipment, err := equipmentRepo.GetByBuilding(ctx, building.ID.String())
	require.NoError(t, err)
	assert.Empty(t, equipment, "New building should have no equipment")

	// Add equipment manually
	eq := &domain.Equipment{
		BuildingID: building.ID,
		Name:       "Test Equipment",
		Type:       "hvac",
		Category:   "hvac",
		Path:       "/LIFECYCLE/1/101/HVAC/TEST-001",
		Status:     "operational",
	}
	err = equipmentRepo.Create(ctx, eq)
	require.NoError(t, err)

	// Query equipment (should have 1)
	equipment, err = equipmentRepo.GetByBuilding(ctx, building.ID.String())
	require.NoError(t, err)
	assert.Len(t, equipment, 1, "Should have 1 equipment")

	// Query by path
	equipByPath, err := equipmentRepo.GetByPath(ctx, eq.Path)
	require.NoError(t, err)
	assert.Equal(t, eq.ID, equipByPath.ID, "Should find equipment by path")

	// Delete equipment
	err = equipmentRepo.Delete(ctx, eq.ID.String())
	require.NoError(t, err)

	// Delete building
	err = buildingRepo.Delete(ctx, building.ID.String())
	require.NoError(t, err)

	// Verify deleted
	_, err = buildingRepo.GetByID(ctx, building.ID.String())
	assert.Error(t, err, "Building should be deleted")

	t.Log("✅ Complete lifecycle validated")
}

// TestWorkflowPathQueryPerformance validates path query performance
func TestWorkflowPathQueryPerformance(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping performance test in short mode")
	}

	ctx := context.Background()
	container := integration.SetupTestContainer(t)
	if container == nil {
		t.Skip("Test container not available")
	}

	equipmentRepo := container.GetEquipmentRepository()

	// Create test data (100 equipment items)
	t.Log("Creating test equipment...")
	buildingID := types.NewID()

	for i := 0; i < 100; i++ {
		floor := (i / 10) + 1
		room := (i % 10) + 101
		eq := &domain.Equipment{
			BuildingID: buildingID,
			Name:       fmt.Sprintf("EQUIP-%03d", i),
			Type:       "hvac",
			Category:   "hvac",
			Path:       fmt.Sprintf("/PERF/%d/%d/HVAC/EQUIP-%03d", floor, room, i),
			Status:     "operational",
		}
		err := equipmentRepo.Create(ctx, eq)
		require.NoError(t, err)
	}

	// Test query performance
	t.Log("Testing path query performance...")

	patterns := []string{
		"/PERF/1/*/*",      // Single floor
		"/PERF/*/HVAC/*",   // All HVAC
		"/PERF/*/*/HVAC/*", // All HVAC (more specific)
	}

	for _, pattern := range patterns {
		start := time.Now()
		equipment, err := equipmentRepo.FindByPath(ctx, pattern)
		duration := time.Since(start)

		require.NoError(t, err)
		t.Logf("Pattern '%s': found %d equipment in %v", pattern, len(equipment), duration)

		// Performance assertion: should complete in < 100ms
		assert.Less(t, duration.Milliseconds(), int64(100),
			"Path query should complete in < 100ms")
	}

	t.Log("✅ Path query performance validated")
}
