package commands

import (
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestSessionState(t *testing.T) {
	session := &SessionState{
		BuildingID:       "test-building",
		CWD:              "/systems/electrical",
		PreviousCWD:      "/systems",
		Zoom:             2,
		LastIndexRefresh: time.Now(),
	}

	if session.BuildingID != "test-building" {
		t.Errorf("Expected BuildingID 'test-building', got '%s'", session.BuildingID)
	}

	if session.CWD != "/systems/electrical" {
		t.Errorf("Expected CWD '/systems/electrical', got '%s'", session.CWD)
	}
}

func TestNormalizeVirtualPath(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"", "/"},
		{"/", "/"},
		{"systems", "/systems"},
		{"/systems/", "/systems"},
		{"systems/electrical", "/systems/electrical"},
		{"../floors/2", "/../floors/2"},
		{"C:\\Windows\\Path", "/C:/Windows/Path"}, // Windows path conversion
	}

	for _, test := range tests {
		result := normalizeVirtualPath(test.input)
		if result != test.expected {
			t.Errorf("normalizeVirtualPath('%s') = '%s', expected '%s'", test.input, result, test.expected)
		}
	}
}

func TestPathResolver(t *testing.T) {
	resolver := NewPathResolver("/tmp/test-building")

	if resolver.buildingRoot != "/tmp/test-building" {
		t.Errorf("Expected building root '/tmp/test-building', got '%s'", resolver.buildingRoot)
	}
}

func TestResolvePath(t *testing.T) {
	resolver := NewPathResolver("/tmp/test-building")

	tests := []struct {
		currentPath string
		targetPath  string
		expected    string
		expectError bool
	}{
		{"/", "", "/", false},
		{"/", ".", "/", false},
		{"/", "..", "/", false},
		{"/", "~", "/", false},
		{"/", "systems", "/systems", false},
		{"/systems", "electrical", "/systems/electrical", false},
		{"/systems/electrical", "..", "/systems", false},
		{"/systems/electrical", "../hvac", "/systems/hvac", false},
		{"/systems/electrical", "/floors/1", "/floors/1", false},
		{"/systems/electrical", "-", "/systems/electrical", true}, // Not implemented yet
	}

	for _, test := range tests {
		result, err := resolver.ResolvePath(test.currentPath, test.targetPath)
		if test.expectError && err == nil {
			t.Errorf("Expected error for ResolvePath('%s', '%s')", test.currentPath, test.targetPath)
		}
		if !test.expectError && err != nil {
			t.Errorf("Unexpected error for ResolvePath('%s', '%s'): %v", test.currentPath, test.targetPath, err)
		}
		if !test.expectError && result != test.expected {
			t.Errorf("ResolvePath('%s', '%s') = '%s', expected '%s'", test.currentPath, test.targetPath, result, test.expected)
		}
	}
}

func TestValidatePath(t *testing.T) {
	resolver := NewPathResolver("/tmp/test-building")

	tests := []struct {
		path        string
		expectError bool
	}{
		{"/", false},
		{"/systems", false},
		{"/systems/electrical", false},
		{"/invalid<path", true},
		{"/invalid:path", true},
		{"/invalid\"path", true},
		{"/invalid|path", true},
		{"/invalid?path", true},
		{"/invalid*path", true},
		{"/double//slash", true},
		{"/trailing/", true},
	}

	for _, test := range tests {
		err := resolver.ValidatePath(test.path)
		if test.expectError && err == nil {
			t.Errorf("Expected error for ValidatePath('%s')", test.path)
		}
		if !test.expectError && err != nil {
			t.Errorf("Unexpected error for ValidatePath('%s'): %v", test.path, err)
		}
	}
}

func TestSplitPath(t *testing.T) {
	resolver := NewPathResolver("/tmp/test-building")

	tests := []struct {
		path     string
		expected []string
	}{
		{"/", []string{}},
		{"/systems", []string{"systems"}},
		{"/systems/electrical", []string{"systems", "electrical"}},
		{"/floors/1/rooms/101", []string{"floors", "1", "rooms", "101"}},
	}

	for _, test := range tests {
		result := resolver.SplitPath(test.path)
		if len(result) != len(test.expected) {
			t.Errorf("SplitPath('%s') returned %d segments, expected %d", test.path, len(result), len(test.expected))
			continue
		}
		for i, segment := range result {
			if segment != test.expected[i] {
				t.Errorf("SplitPath('%s')[%d] = '%s', expected '%s'", test.path, i, segment, test.expected[i])
			}
		}
	}
}

func TestJoinPath(t *testing.T) {
	resolver := NewPathResolver("/tmp/test-building")

	tests := []struct {
		segments []string
		expected string
	}{
		{[]string{}, "/"},
		{[]string{"systems"}, "/systems"},
		{[]string{"systems", "electrical"}, "/systems/electrical"},
		{[]string{"floors", "1", "rooms", "101"}, "/floors/1/rooms/101"},
		{[]string{"", "systems", ""}, "/systems"}, // Empty segments filtered
	}

	for _, test := range tests {
		result := resolver.JoinPath(test.segments...)
		if result != test.expected {
			t.Errorf("JoinPath(%v) = '%s', expected '%s'", test.segments, result, test.expected)
		}
	}
}

func TestIsSubPath(t *testing.T) {
	resolver := NewPathResolver("/tmp/test-building")

	tests := []struct {
		parentPath string
		childPath  string
		expected   bool
	}{
		{"/", "/systems", true},
		{"/", "/systems/electrical", true},
		{"/systems", "/systems/electrical", true},
		{"/systems", "/floors/1", false},
		{"/systems/electrical", "/systems", false},
		{"/", "/", false}, // Root is not a subpath of itself
	}

	for _, test := range tests {
		result := resolver.IsSubPath(test.parentPath, test.childPath)
		if result != test.expected {
			t.Errorf("IsSubPath('%s', '%s') = %t, expected %t", test.parentPath, test.childPath, result, test.expected)
		}
	}
}

func TestSessionFileOperations(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create the .arxos/config directory structure
	configDir := filepath.Join(tempDir, ".arxos", "config")
	if err := os.MkdirAll(configDir, 0755); err != nil {
		t.Fatalf("Failed to create config dir: %v", err)
	}

	// Test session file path
	expectedPath := filepath.Join(configDir, "session.json")
	actualPath := sessionFilePath(tempDir)
	if actualPath != expectedPath {
		t.Errorf("sessionFilePath returned '%s', expected '%s'", actualPath, expectedPath)
	}

	// Test loading non-existent session (should return default)
	session, err := loadSession(tempDir)
	if err != nil {
		t.Errorf("loadSession failed: %v", err)
	}
	if session.BuildingID != filepath.Base(tempDir) {
		t.Errorf("Expected BuildingID '%s', got '%s'", filepath.Base(tempDir), session.BuildingID)
	}
	if session.CWD != "/" {
		t.Errorf("Expected CWD '/', got '%s'", session.CWD)
	}

	// Test saving and loading session
	testSession := &SessionState{
		BuildingID: "test-building",
		CWD:        "/systems/electrical",
		Zoom:       2,
	}

	if err := saveSession(tempDir, testSession); err != nil {
		t.Errorf("saveSession failed: %v", err)
	}

	// Load the saved session
	loadedSession, err := loadSession(tempDir)
	if err != nil {
		t.Errorf("loadSession after save failed: %v", err)
	}

	if loadedSession.BuildingID != testSession.BuildingID {
		t.Errorf("Loaded BuildingID '%s' != saved '%s'", loadedSession.BuildingID, testSession.BuildingID)
	}
	if loadedSession.CWD != testSession.CWD {
		t.Errorf("Loaded CWD '%s' != saved '%s'", loadedSession.CWD, testSession.CWD)
	}
	if loadedSession.Zoom != testSession.Zoom {
		t.Errorf("Loaded Zoom %d != saved %d", loadedSession.Zoom, testSession.Zoom)
	}
}
