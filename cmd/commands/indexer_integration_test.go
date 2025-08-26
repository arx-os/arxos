package commands

import (
	"os"
	"path/filepath"
	"testing"
)

func TestIndexerIntegrationWithNavigation(t *testing.T) {
	// Create temporary building workspace
	tempDir, err := os.MkdirTemp("", "arxos-nav-test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create building structure
	buildingID := "test-building"
	if err := createTestBuildingStructure(tempDir, buildingID); err != nil {
		t.Fatalf("failed to create test building: %v", err)
	}

	// Test index building
	idx, err := BuildIndex(tempDir, buildingID)
	if err != nil {
		t.Fatalf("failed to build index: %v", err)
	}

	// Test path existence validation
	testPaths := []string{
		"/",
		"/floors",
		"/systems",
		"/floors/1",
		"/systems/hvac",
		"/zones",
		"/assets",
	}

	for _, path := range testPaths {
		if !idx.Exists(path) {
			t.Errorf("expected path '%s' to exist", path)
		}
	}

	// Test non-existent paths
	nonExistentPaths := []string{
		"/nonexistent",
		"/floors/999",
		"/systems/invalid",
	}

	for _, path := range nonExistentPaths {
		if idx.Exists(path) {
			t.Errorf("expected path '%s' to not exist", path)
		}
	}

	// Test directory listing
	rootEntries := idx.List("/")
	if len(rootEntries) < 5 {
		t.Errorf("expected at least 5 root entries, got %d", len(rootEntries))
	}

	floorEntries := idx.List("/floors")
	if len(floorEntries) != 2 {
		t.Errorf("expected 2 floor entries, got %d", len(floorEntries))
	}

	systemEntries := idx.List("/systems")
	if len(systemEntries) != 2 {
		t.Errorf("expected 2 system entries, got %d", len(systemEntries))
	}

	// Test tree building
	rootTree := idx.BuildTree("/", 0)
	if rootTree.Name != "building" {
		t.Errorf("expected root tree name 'building', got '%s'", rootTree.Name)
	}

	// Test limited depth
	limitedTree := idx.BuildTree("/", 2)
	if len(limitedTree.Children) == 0 {
		t.Error("expected limited tree to have children")
	}

	// Test specific path tree
	floorTree := idx.BuildTree("/floors", 0)
	if floorTree.Name != "floors" {
		t.Errorf("expected floor tree name 'floors', got '%s'", floorTree.Name)
	}
	if len(floorTree.Children) != 2 {
		t.Errorf("expected 2 floor children, got %d", len(floorTree.Children))
	}
}

func TestIndexerCacheIntegration(t *testing.T) {
	// Create temporary building workspace
	tempDir, err := os.MkdirTemp("", "arxos-cache-test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	buildingID := "cache-test-building"

	// Test GetOrBuildIndex creates and caches index
	idx1, err := GetOrBuildIndex(tempDir, buildingID)
	if err != nil {
		t.Fatalf("failed to build initial index: %v", err)
	}

	// Verify index was cached
	cachedIdx, err := LoadIndex(tempDir)
	if err != nil {
		t.Fatalf("failed to load cached index: %v", err)
	}
	if cachedIdx == nil {
		t.Fatal("expected cached index to exist")
	}
	if cachedIdx.BuildingID != buildingID {
		t.Errorf("expected cached building ID '%s', got '%s'", buildingID, cachedIdx.BuildingID)
	}

	// Test GetOrBuildIndex loads from cache
	idx2, err := GetOrBuildIndex(tempDir, buildingID)
	if err != nil {
		t.Fatalf("failed to load cached index: %v", err)
	}
	if idx2.BuildingID != buildingID {
		t.Errorf("expected loaded building ID '%s', got '%s'", buildingID, idx2.BuildingID)
	}

	// Test RefreshIndex forces rebuild
	refreshedIdx, err := RefreshIndex(tempDir, buildingID)
	if err != nil {
		t.Fatalf("failed to refresh index: %v", err)
	}
	if refreshedIdx.BuildingID != buildingID {
		t.Errorf("expected refreshed building ID '%s', got '%s'", buildingID, refreshedIdx.BuildingID)
	}
}

func TestIndexerWithRealFilesystem(t *testing.T) {
	// Create temporary building workspace
	tempDir, err := os.MkdirTemp("", "arxos-fs-test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	buildingID := "fs-test-building"

	// Create actual filesystem structure
	if err := createRealFilesystemStructure(tempDir); err != nil {
		t.Fatalf("failed to create filesystem structure: %v", err)
	}

	// Build index from real filesystem
	idx, err := BuildIndex(tempDir, buildingID)
	if err != nil {
		t.Fatalf("failed to build index from filesystem: %v", err)
	}

	// Verify filesystem structure was detected
	if !idx.Exists("/floors") {
		t.Error("expected /floors to exist from filesystem")
	}
	if !idx.Exists("/systems") {
		t.Error("expected /systems to exist from filesystem")
	}

	// Test that real files are detected
	floorEntries := idx.List("/floors")
	if len(floorEntries) == 0 {
		t.Error("expected floor entries from filesystem")
	}

	systemEntries := idx.List("/systems")
	if len(systemEntries) == 0 {
		t.Error("expected system entries from filesystem")
	}
}

// Helper functions for test setup

func createTestBuildingStructure(buildingRoot, buildingID string) error {
	// Create .arxos structure
	arxosDir := filepath.Join(buildingRoot, ".arxos")
	if err := os.MkdirAll(arxosDir, 0755); err != nil {
		return err
	}

	// Create building config
	configDir := filepath.Join(arxosDir, "config")
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return err
	}

	// Create session file
	session := &SessionState{
		BuildingID:  buildingID,
		CWD:         "/",
		PreviousCWD: "",
		Zoom:        1.0,
	}
	if err := saveSession(buildingRoot, session); err != nil {
		return err
	}

	// Create cache directory
	cacheDir := filepath.Join(arxosDir, "cache")
	if err := os.MkdirAll(cacheDir, 0755); err != nil {
		return err
	}

	return nil
}

func createRealFilesystemStructure(buildingRoot string) error {
	// Create floors directory
	floorsDir := filepath.Join(buildingRoot, "floors")
	if err := os.MkdirAll(floorsDir, 0755); err != nil {
		return err
	}

	// Create floor subdirectories
	floor1Dir := filepath.Join(floorsDir, "1")
	if err := os.MkdirAll(floor1Dir, 0755); err != nil {
		return err
	}

	floor2Dir := filepath.Join(floorsDir, "2")
	if err := os.MkdirAll(floor2Dir, 0755); err != nil {
		return err
	}

	// Create systems directory
	systemsDir := filepath.Join(buildingRoot, "systems")
	if err := os.MkdirAll(systemsDir, 0755); err != nil {
		return err
	}

	// Create system subdirectories
	hvacDir := filepath.Join(systemsDir, "hvac")
	if err := os.MkdirAll(hvacDir, 0755); err != nil {
		return err
	}

	electricalDir := filepath.Join(systemsDir, "electrical")
	if err := os.MkdirAll(electricalDir, 0755); err != nil {
		return err
	}

	// Create zones directory
	zonesDir := filepath.Join(buildingRoot, "zones")
	if err := os.MkdirAll(zonesDir, 0755); err != nil {
		return err
	}

	// Create assets directory
	assetsDir := filepath.Join(buildingRoot, "assets")
	if err := os.MkdirAll(assetsDir, 0755); err != nil {
		return err
	}

	// Create config directory
	configDir := filepath.Join(buildingRoot, "config")
	if err := os.MkdirAll(configDir, 0755); err != nil {
		return err
	}

	return nil
}
