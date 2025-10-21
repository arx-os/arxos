package integration

import (
	"context"
	"fmt"
	"os"
	"testing"
	"time"

	"database/sql"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure/logging"
	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	"github.com/jmoiron/sqlx"
	_ "github.com/lib/pq"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestVersionControl_CompleteWorkflow tests the entire version control workflow
// This is an end-to-end integration test that exercises all version control components
func TestVersionControl_CompleteWorkflow(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()

	// Setup database
	db, cleanup := setupVersionControlDB(t)
	defer cleanup()

	// Setup object storage
	tempDir, err := os.MkdirTemp("", "arxos-test-vc-*")
	require.NoError(t, err)
	defer os.RemoveAll(tempDir)

	// Create logger
	testLogger := logging.NewLogger(logging.INFO)

	// Create repositories
	buildingRepo := postgis.NewBuildingRepository(db)
	equipmentRepo := postgis.NewEquipmentRepository(db)
	floorRepo := postgis.NewFloorRepository(db)

	// Wrap db for repositories that need sqlx.DB
	dbx := sqlx.NewDb(db, "postgres")
	objectRepo := postgis.NewObjectRepository(dbx, tempDir)
	snapshotRepo := postgis.NewSnapshotRepository(dbx)
	treeRepo := postgis.NewTreeRepository(objectRepo)

	// Create services
	snapshotService := usecase.NewSnapshotService(
		buildingRepo,
		equipmentRepo,
		floorRepo,
		objectRepo,
		snapshotRepo,
		treeRepo,
		testLogger,
	)

	diffService := usecase.NewDiffService(
		snapshotRepo,
		objectRepo,
		treeRepo,
		testLogger,
	)

	// Step 1: Create a building with initial data
	t.Log("Step 1: Creating building with initial data")

	buildingID := types.NewID()
	initialBuilding := &domain.Building{
		ID:        buildingID,
		Name:      "Test Building for Version Control",
		Address:   "123 Test Street",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}

	err = buildingRepo.Create(ctx, initialBuilding)
	require.NoError(t, err, "Failed to create building")

	// Add initial floors
	floor1 := &domain.Floor{
		ID:         types.NewID(),
		BuildingID: buildingID,
		Name:       "Ground Floor",
		Level:      0,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
	floor2 := &domain.Floor{
		ID:         types.NewID(),
		BuildingID: buildingID,
		Name:       "First Floor",
		Level:      1,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err = floorRepo.Create(ctx, floor1)
	require.NoError(t, err, "Failed to create floor 1")
	err = floorRepo.Create(ctx, floor2)
	require.NoError(t, err, "Failed to create floor 2")

	// Add initial equipment
	eq1 := &domain.Equipment{
		ID:         types.NewID(),
		BuildingID: buildingID,
		FloorID:    floor1.ID,
		Name:       "AHU-101",
		Type:       "HVAC",
		Status:     "operational",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
	eq2 := &domain.Equipment{
		ID:         types.NewID(),
		BuildingID: buildingID,
		FloorID:    floor2.ID,
		Name:       "AHU-201",
		Type:       "HVAC",
		Status:     "operational",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err = equipmentRepo.Create(ctx, eq1)
	require.NoError(t, err, "Failed to create equipment 1")
	err = equipmentRepo.Create(ctx, eq2)
	require.NoError(t, err, "Failed to create equipment 2")

	// Step 2: Capture first snapshot (v1.0.0)
	t.Log("Step 2: Capturing first snapshot (v1.0.0)")

	snapshot1, err := snapshotService.CaptureSnapshot(ctx, buildingID.String())
	require.NoError(t, err, "Failed to capture first snapshot")
	assert.NotEmpty(t, snapshot1.Hash, "Snapshot hash should not be empty")
	assert.Equal(t, 2, snapshot1.Metadata.FloorCount, "Should have 2 floors")
	assert.Equal(t, 2, snapshot1.Metadata.EquipmentCount, "Should have 2 equipment items")

	t.Logf("  Snapshot captured: %s", snapshot1.Hash[:12])
	t.Logf("  Floors: %d, Equipment: %d", snapshot1.Metadata.FloorCount, snapshot1.Metadata.EquipmentCount)

	// Step 3: Modify building (add more equipment)
	t.Log("Step 3: Adding more equipment")

	eq3 := &domain.Equipment{
		ID:         types.NewID(),
		BuildingID: buildingID,
		FloorID:    floor1.ID,
		Name:       "AHU-102",
		Type:       "HVAC",
		Status:     "operational",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
	eq4 := &domain.Equipment{
		ID:         types.NewID(),
		BuildingID: buildingID,
		FloorID:    floor2.ID,
		Name:       "VAV-301",
		Type:       "HVAC",
		Status:     "operational",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	err = equipmentRepo.Create(ctx, eq3)
	require.NoError(t, err, "Failed to create equipment 3")
	err = equipmentRepo.Create(ctx, eq4)
	require.NoError(t, err, "Failed to create equipment 4")

	// Step 4: Capture second snapshot (v1.1.0)
	t.Log("Step 4: Capturing second snapshot (v1.1.0)")

	snapshot2, err := snapshotService.CaptureSnapshot(ctx, buildingID.String())
	require.NoError(t, err, "Failed to capture second snapshot")
	assert.NotEmpty(t, snapshot2.Hash, "Snapshot hash should not be empty")
	assert.Equal(t, 2, snapshot2.Metadata.FloorCount, "Should still have 2 floors")
	assert.Equal(t, 4, snapshot2.Metadata.EquipmentCount, "Should now have 4 equipment items")

	// Snapshots should be different
	assert.NotEqual(t, snapshot1.Hash, snapshot2.Hash, "Snapshots should be different")

	t.Logf("  Snapshot captured: %s", snapshot2.Hash[:12])
	t.Logf("  Equipment increased: %d → %d", snapshot1.Metadata.EquipmentCount, snapshot2.Metadata.EquipmentCount)

	// Step 5: Create mock versions for diff testing
	t.Log("Step 5: Testing diff between snapshots")

	version1 := &building.Version{
		ID:       "v1",
		Tag:      "v1.0.0",
		Snapshot: snapshot1.Hash,
		Hash:     "version-hash-1",
		Author: building.Author{
			Name:  "test-user",
			Email: "test@example.com",
		},
	}

	version2 := &building.Version{
		ID:       "v2",
		Tag:      "v1.1.0",
		Snapshot: snapshot2.Hash,
		Hash:     "version-hash-2",
		Parent:   version1.Hash,
		Author: building.Author{
			Name:  "test-user",
			Email: "test@example.com",
		},
	}

	// Calculate diff
	diff, err := diffService.DiffVersions(ctx, version1, version2)
	require.NoError(t, err, "Failed to calculate diff")

	// Verify diff results
	assert.Equal(t, "v1.0.0", diff.FromVersion)
	assert.Equal(t, "v1.1.0", diff.ToVersion)
	assert.True(t, diff.Summary.EquipmentAdded >= 2, "Should show at least 2 equipment added")

	t.Logf("  Diff calculated: %d total changes", diff.Summary.TotalChanges)
	t.Logf("  Equipment added: %d", diff.Summary.EquipmentAdded)

	// Step 6: Test diff output formats
	t.Log("Step 6: Testing diff output formats")

	formats := []building.DiffOutputFormat{
		building.DiffFormatUnified,
		building.DiffFormatJSON,
		building.DiffFormatSemantic,
		building.DiffFormatSummary,
	}

	for _, format := range formats {
		output, err := building.FormatDiff(diff, format)
		require.NoError(t, err, "Failed to format diff as %s", format)
		assert.NotEmpty(t, output, "Diff output should not be empty for format %s", format)
		t.Logf("  Format %s: %d bytes", format, len(output))
	}

	// Step 7: Test content deduplication
	t.Log("Step 7: Testing content deduplication")

	// Capture snapshot again without changes
	snapshot3, err := snapshotService.CaptureSnapshot(ctx, buildingID.String())
	require.NoError(t, err, "Failed to capture third snapshot")

	// Snapshot hashes should be identical (no changes)
	assert.Equal(t, snapshot2.Hash, snapshot3.Hash, "Snapshots should be identical (content deduplication)")
	t.Logf("  Deduplication working: snapshot2 == snapshot3")

	// Step 8: Test tree-level diff optimization
	t.Log("Step 8: Testing tree-level diff optimization")

	// Space tree should be the same in snapshot2 and snapshot3
	assert.Equal(t, snapshot2.SpaceTree, snapshot3.SpaceTree, "Space tree should be identical")
	assert.Equal(t, snapshot2.ItemTree, snapshot3.ItemTree, "Item tree should be identical")

	t.Logf("  Tree-level optimization working: identical trees share hashes")

	// Success!
	t.Log("✅ Complete workflow test passed!")
	t.Logf("   Created 2 floors, 4 equipment items")
	t.Logf("   Captured 3 snapshots (2 unique)")
	t.Logf("   Calculated diffs between versions")
	t.Logf("   Verified deduplication and tree optimization")
}

// TestVersionControl_SnapshotPerformance benchmarks snapshot creation
func TestVersionControl_SnapshotPerformance(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping performance test in short mode")
	}

	ctx := context.Background()

	// Setup
	db, cleanup := setupVersionControlDB(t)
	defer cleanup()

	tempDir, err := os.MkdirTemp("", "arxos-test-vc-perf-*")
	require.NoError(t, err)
	defer os.RemoveAll(tempDir)

	testLogger := logging.NewLogger(logging.INFO)

	buildingRepo := postgis.NewBuildingRepository(db)
	equipmentRepo := postgis.NewEquipmentRepository(db)
	floorRepo := postgis.NewFloorRepository(db)

	// Wrap db for repositories that need sqlx.DB
	dbx := sqlx.NewDb(db, "postgres")
	objectRepo := postgis.NewObjectRepository(dbx, tempDir)
	snapshotRepo := postgis.NewSnapshotRepository(dbx)
	treeRepo := postgis.NewTreeRepository(objectRepo)

	snapshotService := usecase.NewSnapshotService(
		buildingRepo,
		equipmentRepo,
		floorRepo,
		objectRepo,
		snapshotRepo,
		treeRepo,
		testLogger,
	)

	// Create test building
	buildingID := types.NewID()
	testBuilding := &domain.Building{
		ID:        buildingID,
		Name:      "Performance Test Building",
		Address:   "Performance Test",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	err = buildingRepo.Create(ctx, testBuilding)
	require.NoError(t, err)

	// Create 10 floors
	for i := 0; i < 10; i++ {
		floor := &domain.Floor{
			ID:         types.NewID(),
			BuildingID: buildingID,
			Name:       fmt.Sprintf("Floor %d", i),
			Level:      i,
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		err = floorRepo.Create(ctx, floor)
		require.NoError(t, err)
	}

	// Create 100 equipment items
	for i := 0; i < 100; i++ {
		eq := &domain.Equipment{
			ID:         types.NewID(),
			BuildingID: buildingID,
			Name:       fmt.Sprintf("Equipment-%d", i),
			Type:       "HVAC",
			Status:     "operational",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		err = equipmentRepo.Create(ctx, eq)
		require.NoError(t, err)
	}

	// Benchmark snapshot creation
	t.Log("Benchmarking snapshot creation (10 floors, 100 equipment items)...")

	start := time.Now()
	snapshot, err := snapshotService.CaptureSnapshot(ctx, buildingID.String())
	duration := time.Since(start)

	require.NoError(t, err)
	assert.NotNil(t, snapshot)

	t.Logf("Snapshot created in %v", duration)
	t.Logf("  Hash: %s", snapshot.Hash[:12])
	t.Logf("  Floors: %d", snapshot.Metadata.FloorCount)
	t.Logf("  Equipment: %d", snapshot.Metadata.EquipmentCount)

	// Performance assertion: should be under 5 seconds for 100 items
	assert.Less(t, duration, 5*time.Second, "Snapshot creation should be under 5 seconds")

	// Benchmark second snapshot (should be faster due to deduplication)
	start2 := time.Now()
	snapshot2, err := snapshotService.CaptureSnapshot(ctx, buildingID.String())
	duration2 := time.Since(start2)

	require.NoError(t, err)
	assert.Equal(t, snapshot.Hash, snapshot2.Hash, "Snapshots should be identical")

	t.Logf("Second snapshot (identical) created in %v", duration2)
	t.Logf("  Deduplication speedup: %.2fx", float64(duration)/float64(duration2))
}

// TestVersionControl_DiffPerformance benchmarks diff calculation
func TestVersionControl_DiffPerformance(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping performance test in short mode")
	}

	ctx := context.Background()

	// Setup
	db, cleanup := setupVersionControlDB(t)
	defer cleanup()

	tempDir, err := os.MkdirTemp("", "arxos-test-vc-diff-*")
	require.NoError(t, err)
	defer os.RemoveAll(tempDir)

	testLogger := logging.NewLogger(logging.INFO)

	buildingRepo := postgis.NewBuildingRepository(db)
	equipmentRepo := postgis.NewEquipmentRepository(db)
	floorRepo := postgis.NewFloorRepository(db)

	// Wrap db for repositories that need sqlx.DB
	dbx := sqlx.NewDb(db, "postgres")
	objectRepo := postgis.NewObjectRepository(dbx, tempDir)
	snapshotRepo := postgis.NewSnapshotRepository(dbx)
	treeRepo := postgis.NewTreeRepository(objectRepo)

	snapshotService := usecase.NewSnapshotService(
		buildingRepo,
		equipmentRepo,
		floorRepo,
		objectRepo,
		snapshotRepo,
		treeRepo,
		testLogger,
	)

	diffService := usecase.NewDiffService(
		snapshotRepo,
		objectRepo,
		treeRepo,
		testLogger,
	)

	// Create building
	buildingID := types.NewID()
	testBuilding := &domain.Building{
		ID:        buildingID,
		Name:      "Diff Performance Test",
		Address:   "Test",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	err = buildingRepo.Create(ctx, testBuilding)
	require.NoError(t, err)

	// Create 50 equipment items
	for i := 0; i < 50; i++ {
		eq := &domain.Equipment{
			ID:         types.NewID(),
			BuildingID: buildingID,
			Name:       fmt.Sprintf("Equipment-%d", i),
			Type:       "HVAC",
			Status:     "operational",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		err = equipmentRepo.Create(ctx, eq)
		require.NoError(t, err)
	}

	// Capture first snapshot
	snapshot1, err := snapshotService.CaptureSnapshot(ctx, buildingID.String())
	require.NoError(t, err)

	// Add 5 more equipment items
	for i := 50; i < 55; i++ {
		eq := &domain.Equipment{
			ID:         types.NewID(),
			BuildingID: buildingID,
			Name:       fmt.Sprintf("Equipment-%d", i),
			Type:       "HVAC",
			Status:     "operational",
			CreatedAt:  time.Now(),
			UpdatedAt:  time.Now(),
		}
		err = equipmentRepo.Create(ctx, eq)
		require.NoError(t, err)
	}

	// Capture second snapshot
	snapshot2, err := snapshotService.CaptureSnapshot(ctx, buildingID.String())
	require.NoError(t, err)

	// Benchmark diff calculation
	t.Log("Benchmarking diff calculation (50 → 55 equipment items)...")

	diffVersion1 := &building.Version{Tag: "v1.0.0", Snapshot: snapshot1.Hash, Hash: "hash1"}
	diffVersion2 := &building.Version{Tag: "v1.1.0", Snapshot: snapshot2.Hash, Hash: "hash2"}

	start := time.Now()
	diff, err := diffService.DiffVersions(ctx, diffVersion1, diffVersion2)
	duration := time.Since(start)

	require.NoError(t, err)
	assert.NotNil(t, diff)

	t.Logf("Diff calculated in %v", duration)
	t.Logf("  Total changes: %d", diff.Summary.TotalChanges)
	t.Logf("  Equipment added: %d", diff.Summary.EquipmentAdded)

	// Performance assertion: diff should be under 2 seconds
	assert.Less(t, duration, 2*time.Second, "Diff calculation should be under 2 seconds")

	// Verify diff correctness
	assert.True(t, diff.Summary.EquipmentAdded >= 5, "Should detect at least 5 equipment added")
}

// TestVersionControl_ContentDeduplication tests deduplication across snapshots
func TestVersionControl_ContentDeduplication(t *testing.T) {
	if testing.Short() {
		t.Skip("Skipping integration test in short mode")
	}

	ctx := context.Background()

	// Setup
	db, cleanup := setupVersionControlDB(t)
	defer cleanup()

	tempDir, err := os.MkdirTemp("", "arxos-test-vc-dedup-*")
	require.NoError(t, err)
	defer os.RemoveAll(tempDir)

	testLogger := logging.NewLogger(logging.INFO)

	buildingRepo := postgis.NewBuildingRepository(db)
	equipmentRepo := postgis.NewEquipmentRepository(db)
	floorRepo := postgis.NewFloorRepository(db)

	// Wrap db for repositories that need sqlx.DB
	dbx := sqlx.NewDb(db, "postgres")
	objectRepo := postgis.NewObjectRepository(dbx, tempDir)
	snapshotRepo := postgis.NewSnapshotRepository(dbx)
	treeRepo := postgis.NewTreeRepository(objectRepo)

	snapshotService := usecase.NewSnapshotService(
		buildingRepo,
		equipmentRepo,
		floorRepo,
		objectRepo,
		snapshotRepo,
		treeRepo,
		testLogger,
	)

	// Create building with floors (won't change)
	buildingID := types.NewID()
	testBuilding := &domain.Building{
		ID:        buildingID,
		Name:      "Dedup Test Building",
		Address:   "Test",
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
	err = buildingRepo.Create(ctx, testBuilding)
	require.NoError(t, err)

	floor1 := &domain.Floor{
		ID:         types.NewID(),
		BuildingID: buildingID,
		Name:       "Floor 1",
		Level:      1,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
	err = floorRepo.Create(ctx, floor1)
	require.NoError(t, err)

	// Capture snapshot 1
	snapshot1, err := snapshotService.CaptureSnapshot(ctx, buildingID.String())
	require.NoError(t, err)

	// Add equipment (building and floors unchanged)
	eq1 := &domain.Equipment{
		ID:         types.NewID(),
		BuildingID: buildingID,
		Name:       "New Equipment",
		Type:       "HVAC",
		Status:     "operational",
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}
	err = equipmentRepo.Create(ctx, eq1)
	require.NoError(t, err)

	// Capture snapshot 2
	snapshot2, err := snapshotService.CaptureSnapshot(ctx, buildingID.String())
	require.NoError(t, err)

	// Verify deduplication: Space tree should be identical
	assert.Equal(t, snapshot1.SpaceTree, snapshot2.SpaceTree,
		"Space tree should be identical (deduplication)")

	// Item tree should be different
	assert.NotEqual(t, snapshot1.ItemTree, snapshot2.ItemTree,
		"Item tree should be different")

	t.Log("✅ Content deduplication verified")
	t.Logf("   Space tree shared: %s", snapshot1.SpaceTree[:12])
	t.Logf("   Item trees differ: %s vs %s",
		snapshot1.ItemTree[:12],
		snapshot2.ItemTree[:12])
}

// setupVersionControlDB sets up database for version control tests
func setupVersionControlDB(t *testing.T) (*sql.DB, func()) {
	t.Helper()

	dsn := "host=localhost port=5432 user=arxos_test password=test_password dbname=arxos_test sslmode=disable"
	db, err := sql.Open("postgres", dsn)
	if err != nil {
		t.Skipf("Cannot connect to test database: %v", err)
		return nil, func() {}
	}

	if err := db.Ping(); err != nil {
		db.Close()
		t.Skipf("Cannot ping test database: %v", err)
		return nil, func() {}
	}

	// Check if version control tables exist
	var exists bool
	err = db.QueryRow("SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'version_objects')").Scan(&exists)
	if err != nil || !exists {
		db.Close()
		t.Skipf("Version control tables not found. Run migrations: make migrate-up")
		return nil, func() {}
	}

	// Cleanup function
	cleanup := func() {
		// Clean up test data
		db.Exec("DELETE FROM equipment")
		db.Exec("DELETE FROM floors")
		db.Exec("DELETE FROM buildings")
		db.Exec("DELETE FROM versions")
		db.Exec("DELETE FROM version_snapshots")
		db.Exec("DELETE FROM version_objects WHERE created_at > NOW() - INTERVAL '1 hour'")
		db.Close()
	}

	return db, cleanup
}
