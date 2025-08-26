package commands

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestDirectoryEntry(t *testing.T) {
	entry := DirectoryEntry{
		Name:     "test-floor",
		Type:     "floor",
		Path:     "/floors/test-floor",
		IsDir:    true,
		Metadata: map[string]interface{}{"level": 2},
	}

	if entry.Name != "test-floor" {
		t.Errorf("expected name 'test-floor', got '%s'", entry.Name)
	}
	if entry.Type != "floor" {
		t.Errorf("expected type 'floor', got '%s'", entry.Type)
	}
	if entry.Path != "/floors/test-floor" {
		t.Errorf("expected path '/floors/test-floor', got '%s'", entry.Path)
	}
	if !entry.IsDir {
		t.Error("expected IsDir to be true")
	}
	if entry.Metadata["level"] != 2 {
		t.Errorf("expected metadata level 2, got %v", entry.Metadata["level"])
	}
}

func TestTreeEntry(t *testing.T) {
	child := TreeEntry{
		Name:  "child",
		Type:  "zone",
		Path:  "/zones/child",
		IsDir: true,
	}

	parent := TreeEntry{
		Name:     "parent",
		Type:     "directory",
		Path:     "/zones",
		IsDir:    true,
		Children: []TreeEntry{child},
	}

	if len(parent.Children) != 1 {
		t.Errorf("expected 1 child, got %d", len(parent.Children))
	}
	if parent.Children[0].Name != "child" {
		t.Errorf("expected child name 'child', got '%s'", parent.Children[0].Name)
	}
}

func TestIndexStructure(t *testing.T) {
	idx := &Index{
		BuiltAt:          time.Now(),
		BuildingID:       "test-building",
		PathToEntries:    make(map[string][]DirectoryEntry),
		KnownDirectories: make(map[string]bool),
	}

	if idx.BuildingID != "test-building" {
		t.Errorf("expected building ID 'test-building', got '%s'", idx.BuildingID)
	}
	if idx.PathToEntries == nil {
		t.Error("expected PathToEntries to be initialized")
	}
	if idx.KnownDirectories == nil {
		t.Error("expected KnownDirectories to be initialized")
	}
}

func TestIndexCachePath(t *testing.T) {
	buildingRoot := "/tmp/test-building"
	expected := filepath.Join(buildingRoot, ".arxos", "cache", "index.json")
	result := indexCachePath(buildingRoot)

	if result != expected {
		t.Errorf("expected cache path '%s', got '%s'", expected, result)
	}
}

func TestIndexAddDirEntry(t *testing.T) {
	idx := &Index{
		PathToEntries: make(map[string][]DirectoryEntry),
	}

	entry := DirectoryEntry{
		Name:  "test",
		Type:  "directory",
		Path:  "/test",
		IsDir: true,
	}

	idx.addDirEntry("/", entry)

	if len(idx.PathToEntries["/"]) != 1 {
		t.Errorf("expected 1 entry, got %d", len(idx.PathToEntries["/"]))
	}
	if idx.PathToEntries["/"][0].Name != "test" {
		t.Errorf("expected entry name 'test', got '%s'", idx.PathToEntries["/"][0].Name)
	}
}

func TestIndexExists(t *testing.T) {
	idx := &Index{
		KnownDirectories: map[string]bool{
			"/":         true,
			"/floors":   true,
			"/systems":  true,
			"/floors/1": true,
		},
	}

	testCases := []struct {
		path     string
		expected bool
	}{
		{"/", true},
		{"/floors", true},
		{"/systems", true},
		{"/floors/1", true},
		{"/nonexistent", false},
		{"/floors/2", false},
	}

	for _, tc := range testCases {
		result := idx.Exists(tc.path)
		if result != tc.expected {
			t.Errorf("Exists('%s'): expected %v, got %v", tc.path, tc.expected, result)
		}
	}
}

func TestIndexList(t *testing.T) {
	idx := &Index{
		PathToEntries: map[string][]DirectoryEntry{
			"/": {
				{Name: "floors", Type: "directory", Path: "/floors", IsDir: true},
				{Name: "systems", Type: "directory", Path: "/systems", IsDir: true},
			},
			"/floors": {
				{Name: "1", Type: "floor", Path: "/floors/1", IsDir: true},
				{Name: "2", Type: "floor", Path: "/floors/2", IsDir: true},
			},
		},
	}

	rootEntries := idx.List("/")
	if len(rootEntries) != 2 {
		t.Errorf("expected 2 root entries, got %d", len(rootEntries))
	}

	floorEntries := idx.List("/floors")
	if len(floorEntries) != 2 {
		t.Errorf("expected 2 floor entries, got %d", len(floorEntries))
	}

	// Test empty directory
	emptyEntries := idx.List("/systems")
	if len(emptyEntries) != 0 {
		t.Errorf("expected 0 system entries, got %d", len(emptyEntries))
	}
}

func TestIndexBuildTree(t *testing.T) {
	idx := &Index{
		PathToEntries: map[string][]DirectoryEntry{
			"/": {
				{Name: "floors", Type: "directory", Path: "/floors", IsDir: true},
			},
			"/floors": {
				{Name: "1", Type: "floor", Path: "/floors/1", IsDir: true},
				{Name: "2", Type: "floor", Path: "/floors/2", IsDir: true},
			},
		},
	}

	// Test root tree
	rootTree := idx.BuildTree("/", 0)
	if rootTree.Name != "building" {
		t.Errorf("expected root name 'building', got '%s'", rootTree.Name)
	}
	if len(rootTree.Children) != 1 {
		t.Errorf("expected 1 root child, got %d", len(rootTree.Children))
	}

	// Test limited depth
	limitedTree := idx.BuildTree("/", 1)
	if len(limitedTree.Children) != 1 {
		t.Errorf("expected 1 child at depth 1, got %d", len(limitedTree.Children))
	}
	if len(limitedTree.Children[0].Children) != 0 {
		t.Errorf("expected 0 children at depth 2, got %d", len(limitedTree.Children[0].Children))
	}

	// Test specific path
	floorTree := idx.BuildTree("/floors", 0)
	if floorTree.Name != "floors" {
		t.Errorf("expected floor tree name 'floors', got '%s'", floorTree.Name)
	}
	if len(floorTree.Children) != 2 {
		t.Errorf("expected 2 floor children, got %d", len(floorTree.Children))
	}
}

func TestIndexPersistence(t *testing.T) {
	// Create temporary directory
	tempDir, err := os.MkdirTemp("", "arxos-index-test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create .arxos/cache structure
	cacheDir := filepath.Join(tempDir, ".arxos", "cache")
	if err := os.MkdirAll(cacheDir, 0755); err != nil {
		t.Fatalf("failed to create cache dir: %v", err)
	}

	// Create test index
	idx := &Index{
		BuiltAt:          time.Now(),
		BuildingID:       "test-building",
		PathToEntries:    make(map[string][]DirectoryEntry),
		KnownDirectories: make(map[string]bool),
	}
	idx.KnownDirectories["/"] = true
	idx.addDirEntry("/", DirectoryEntry{
		Name:  "test",
		Type:  "directory",
		Path:  "/test",
		IsDir: true,
	})

	// Test save
	if err := SaveIndex(tempDir, idx); err != nil {
		t.Fatalf("failed to save index: %v", err)
	}

	// Test load
	loadedIdx, err := LoadIndex(tempDir)
	if err != nil {
		t.Fatalf("failed to load index: %v", err)
	}
	if loadedIdx == nil {
		t.Fatal("loaded index is nil")
	}

	// Verify loaded data
	if loadedIdx.BuildingID != "test-building" {
		t.Errorf("expected building ID 'test-building', got '%s'", loadedIdx.BuildingID)
	}
	if !loadedIdx.Exists("/test") {
		t.Error("expected /test to exist in loaded index")
	}
}

func TestGetOrBuildIndex(t *testing.T) {
	// Create temporary directory
	tempDir, err := os.MkdirTemp("", "arxos-index-test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Test building new index
	idx, err := GetOrBuildIndex(tempDir, "test-building")
	if err != nil {
		t.Fatalf("failed to build index: %v", err)
	}
	if idx == nil {
		t.Fatal("built index is nil")
	}
	if idx.BuildingID != "test-building" {
		t.Errorf("expected building ID 'test-building', got '%s'", idx.BuildingID)
	}

	// Test loading existing index
	loadedIdx, err := GetOrBuildIndex(tempDir, "test-building")
	if err != nil {
		t.Fatalf("failed to load existing index: %v", err)
	}
	if loadedIdx == nil {
		t.Fatal("loaded existing index is nil")
	}
	if loadedIdx.BuildingID != "test-building" {
		t.Errorf("expected building ID 'test-building', got '%s'", loadedIdx.BuildingID)
	}
}

func TestRefreshIndex(t *testing.T) {
	// Create temporary directory
	tempDir, err := os.MkdirTemp("", "arxos-index-test")
	if err != nil {
		t.Fatalf("failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create initial index
	idx, err := GetOrBuildIndex(tempDir, "test-building")
	if err != nil {
		t.Fatalf("failed to build initial index: %v", err)
	}

	// Refresh index
	refreshedIdx, err := RefreshIndex(tempDir, "test-building")
	if err != nil {
		t.Fatalf("failed to refresh index: %v", err)
	}
	if refreshedIdx == nil {
		t.Fatal("refreshed index is nil")
	}

	// Verify refresh timestamp is newer
	if !refreshedIdx.BuiltAt.After(idx.BuiltAt) {
		t.Error("expected refreshed index to have newer timestamp")
	}
}
