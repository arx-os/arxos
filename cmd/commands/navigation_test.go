package commands

import (
	"os"
	"path/filepath"
	"testing"
)

func TestNavigationCommandsIntegration(t *testing.T) {
	// Create a temporary building workspace for testing
	tempDir, err := os.MkdirTemp("", "arxos-building-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create the .arxos/config directory structure
	configDir := filepath.Join(tempDir, ".arxos", "config")
	if err := os.MkdirAll(configDir, 0755); err != nil {
		t.Fatalf("Failed to create config dir: %v", err)
	}

	// Change to the temp directory for testing
	originalCWD, err := os.Getwd()
	if err != nil {
		t.Fatalf("Failed to get current working directory: %v", err)
	}
	defer os.Chdir(originalCWD)

	if err := os.Chdir(tempDir); err != nil {
		t.Fatalf("Failed to change to temp directory: %v", err)
	}

	// Test initial pwd (should show root)
	root, err := findBuildingRoot(tempDir)
	if err != nil {
		t.Fatalf("findBuildingRoot failed: %v", err)
	}

	session, err := loadSession(root)
	if err != nil {
		t.Fatalf("loadSession failed: %v", err)
	}

	if session.CWD != "/" {
		t.Errorf("Initial CWD should be '/', got '%s'", session.CWD)
	}

	if session.BuildingID != filepath.Base(tempDir) {
		t.Errorf("Expected BuildingID '%s', got '%s'", filepath.Base(tempDir), session.BuildingID)
	}
}

func TestPathResolutionScenarios(t *testing.T) {
	resolver := NewPathResolver("/tmp/test-building")

	// Test various path resolution scenarios
	scenarios := []struct {
		name        string
		currentPath string
		targetPath  string
		expected    string
		description string
	}{
		{
			name:        "absolute_path",
			currentPath: "/systems/electrical",
			targetPath:  "/floors/1",
			expected:    "/floors/1",
			description: "Absolute paths should work from anywhere",
		},
		{
			name:        "relative_path",
			currentPath: "/systems",
			targetPath:  "electrical",
			expected:    "/systems/electrical",
			description: "Relative paths should append to current",
		},
		{
			name:        "parent_navigation",
			currentPath: "/systems/electrical/panels",
			targetPath:  "..",
			expected:    "/systems/electrical",
			description: "Parent navigation should work",
		},
		{
			name:        "complex_relative",
			currentPath: "/systems/electrical",
			targetPath:  "../hvac/units",
			expected:    "/systems/hvac/units",
			description: "Complex relative paths should resolve correctly",
		},
		{
			name:        "root_navigation",
			currentPath: "/systems/electrical",
			targetPath:  "~",
			expected:    "/",
			description: "Tilde should navigate to root",
		},
		{
			name:        "current_directory",
			currentPath: "/systems/electrical",
			targetPath:  ".",
			expected:    "/systems/electrical",
			description: "Dot should stay in current directory",
		},
	}

	for _, scenario := range scenarios {
		t.Run(scenario.name, func(t *testing.T) {
			result, err := resolver.ResolvePath(scenario.currentPath, scenario.targetPath)
			if err != nil {
				t.Errorf("%s: Unexpected error: %v", scenario.description, err)
				return
			}
			if result != scenario.expected {
				t.Errorf("%s: Expected '%s', got '%s'", scenario.description, scenario.expected, result)
			}
		})
	}
}

func TestPathValidationEdgeCases(t *testing.T) {
	resolver := NewPathResolver("/tmp/test-building")

	// Test edge cases and invalid paths
	edgeCases := []struct {
		name        string
		path        string
		expectError bool
		description string
	}{
		{
			name:        "empty_path",
			path:        "",
			expectError: true,
			description: "Empty paths should be invalid",
		},
		{
			name:        "root_path",
			path:        "/",
			expectError: false,
			description: "Root path should be valid",
		},
		{
			name:        "single_segment",
			path:        "/systems",
			expectError: false,
			description: "Single segment paths should be valid",
		},
		{
			name:        "multiple_segments",
			path:        "/systems/electrical/panels",
			expectError: false,
			description: "Multiple segment paths should be valid",
		},
		{
			name:        "invalid_chars_lt",
			path:        "/systems<electrical",
			expectError: true,
			description: "Less than character should be invalid",
		},
		{
			name:        "invalid_chars_gt",
			path:        "/systems>electrical",
			expectError: true,
			description: "Greater than character should be invalid",
		},
		{
			name:        "invalid_chars_colon",
			path:        "/systems:electrical",
			expectError: true,
			description: "Colon character should be invalid",
		},
		{
			name:        "invalid_chars_quote",
			path:        "/systems\"electrical",
			expectError: true,
			description: "Quote character should be invalid",
		},
		{
			name:        "invalid_chars_pipe",
			path:        "/systems|electrical",
			expectError: true,
			description: "Pipe character should be invalid",
		},
		{
			name:        "invalid_chars_question",
			path:        "/systems?electrical",
			expectError: true,
			description: "Question mark character should be invalid",
		},
		{
			name:        "invalid_chars_star",
			path:        "/systems*electrical",
			expectError: true,
			description: "Star character should be invalid",
		},
		{
			name:        "double_slash",
			path:        "/systems//electrical",
			expectError: true,
			description: "Double slashes should be invalid",
		},
		{
			name:        "trailing_slash",
			path:        "/systems/",
			expectError: true,
			description: "Trailing slash should be invalid",
		},
	}

	for _, edgeCase := range edgeCases {
		t.Run(edgeCase.name, func(t *testing.T) {
			err := resolver.ValidatePath(edgeCase.path)
			if edgeCase.expectError && err == nil {
				t.Errorf("%s: Expected error for path '%s'", edgeCase.description, edgeCase.path)
			}
			if !edgeCase.expectError && err != nil {
				t.Errorf("%s: Unexpected error for path '%s': %v", edgeCase.description, edgeCase.path, err)
			}
		})
	}
}

func TestSessionPersistence(t *testing.T) {
	// Create a temporary directory for testing
	tempDir, err := os.MkdirTemp("", "arxos-session-test-*")
	if err != nil {
		t.Fatalf("Failed to create temp dir: %v", err)
	}
	defer os.RemoveAll(tempDir)

	// Create the .arxos/config directory structure
	configDir := filepath.Join(tempDir, ".arxos", "config")
	if err := os.MkdirAll(configDir, 0755); err != nil {
		t.Fatalf("Failed to create config dir: %v", err)
	}

	// Test session creation and modification
	initialSession := &SessionState{
		BuildingID: "test-building",
		CWD:        "/",
		Zoom:       1,
	}

	// Save initial session
	if err := saveSession(tempDir, initialSession); err != nil {
		t.Fatalf("Failed to save initial session: %v", err)
	}

	// Load and verify initial session
	loadedSession, err := loadSession(tempDir)
	if err != nil {
		t.Fatalf("Failed to load initial session: %v", err)
	}

	if loadedSession.BuildingID != initialSession.BuildingID {
		t.Errorf("BuildingID mismatch: expected '%s', got '%s'", initialSession.BuildingID, loadedSession.BuildingID)
	}

	// Modify session
	loadedSession.CWD = "/systems/electrical"
	loadedSession.PreviousCWD = "/systems"
	loadedSession.Zoom = 2

	// Save modified session
	if err := saveSession(tempDir, loadedSession); err != nil {
		t.Fatalf("Failed to save modified session: %v", err)
	}

	// Load and verify modified session
	reloadedSession, err := loadSession(tempDir)
	if err != nil {
		t.Fatalf("Failed to reload modified session: %v", err)
	}

	if reloadedSession.CWD != "/systems/electrical" {
		t.Errorf("Modified CWD not persisted: expected '/systems/electrical', got '%s'", reloadedSession.CWD)
	}

	if reloadedSession.PreviousCWD != "/systems" {
		t.Errorf("PreviousCWD not persisted: expected '/systems', got '%s'", reloadedSession.PreviousCWD)
	}

	if reloadedSession.Zoom != 2 {
		t.Errorf("Zoom not persisted: expected 2, got %d", reloadedSession.Zoom)
	}
}
