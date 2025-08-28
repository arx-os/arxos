package navigation

import (
	"testing"
)

func TestNavigationSystem(t *testing.T) {
	ctx := GetContext()
	
	// Test initial state
	if ctx.GetCurrentPath() != "/" {
		t.Errorf("Expected initial path to be '/', got '%s'", ctx.GetCurrentPath())
	}
	
	// Test absolute path navigation
	err := ctx.NavigateTo("/electrical")
	if err != nil {
		t.Fatalf("Failed to navigate to /electrical: %v", err)
	}
	
	if ctx.GetCurrentPath() != "/electrical" {
		t.Errorf("Expected path to be '/electrical', got '%s'", ctx.GetCurrentPath())
	}
	
	// Test relative path navigation
	err = ctx.NavigateTo("panel-a")
	if err != nil {
		t.Fatalf("Failed to navigate relatively to panel-a: %v", err)
	}
	
	if ctx.GetCurrentPath() != "/electrical/panel-a" {
		t.Errorf("Expected path to be '/electrical/panel-a', got '%s'", ctx.GetCurrentPath())
	}
	
	// Test parent navigation
	err = ctx.NavigateTo("..")
	if err != nil {
		t.Fatalf("Failed to navigate to parent: %v", err)
	}
	
	if ctx.GetCurrentPath() != "/electrical" {
		t.Errorf("Expected path to be '/electrical', got '%s'", ctx.GetCurrentPath())
	}
	
	// Test root navigation
	err = ctx.NavigateTo("/")
	if err != nil {
		t.Fatalf("Failed to navigate to root: %v", err)
	}
	
	if ctx.GetCurrentPath() != "/" {
		t.Errorf("Expected path to be '/', got '%s'", ctx.GetCurrentPath())
	}
}

func TestSystemExtraction(t *testing.T) {
	tests := []struct {
		path     string
		expected string
	}{
		{"/electrical/panel-a", "electrical"},
		{"/hvac/unit-001", "hvac"},
		{"/structural/f1/room-101", "structural"},
		{"/fire/sprinkler-zone-1", "fire"},
		{"/security/camera-entrance", "security"},
		{"/network/switch-floor1", "network"},
		{"/plumbing/main-line", "plumbing"},
		{"/zones/hvac-zone-1", "zones"},
		{"/equipment/elevator-1", "equipment"},
		{"/floors/f1", "floors"},
		{"/", ""},
	}
	
	for _, test := range tests {
		result := GetSystemFromPath(test.path)
		if result != test.expected {
			t.Errorf("GetSystemFromPath(%s) = %s, expected %s", test.path, result, test.expected)
		}
	}
}

func TestPathValidation(t *testing.T) {
	validPaths := []string{
		"/",
		"/electrical",
		"/electrical/panel-a",
		"/electrical/panel-a/breaker-12",
		"/hvac/unit-001",
		"/structural/f1/room-101",
		"/fire/sprinkler-zone-1",
		"/security/camera-entrance",
		"/network/switch-floor1",
		"/plumbing/main-line",
		"/zones/hvac-zone-1", 
		"/equipment/elevator-1",
		"/floors/f1",
	}
	
	for _, path := range validPaths {
		if !IsValidPath(path) {
			t.Errorf("IsValidPath(%s) = false, expected true", path)
		}
	}
	
	invalidPaths := []string{
		"",
		"relative/path",
		"/invalid-system",
		"/electrical//double-slash",
		"/electrical/panel-a/",  // trailing slash
	}
	
	for _, path := range invalidPaths {
		if IsValidPath(path) {
			t.Errorf("IsValidPath(%s) = true, expected false", path)
		}
	}
}

func TestObjectTypeInference(t *testing.T) {
	tests := []struct {
		path     string
		expected string
	}{
		{"/electrical/outlet/room-101", "outlet"},
		{"/electrical/switch/main", "switch"},
		{"/electrical/panel/mdf", "panel"},
		{"/hvac/ahu/rooftop-1", "ahu"},
		{"/hvac/vav/zone-1", "vav"},
		{"/hvac/duct/main-supply", "duct"},
		{"/structural/wall/north", "wall"},
		{"/structural/beam/main-support", "beam"},
		{"/structural/column/structural-1", "column"},
		{"/fire/sprinkler/zone-1", "sprinkler"},
		{"/fire/alarm/system-1", "alarm"},
		{"/security/camera/entrance", "camera"},
		{"/network/switch/floor-1", "network_switch"},
		{"/plumbing/pipe/main-line", "pipe"},
		{"/plumbing/valve/shutoff-1", "valve"},
	}
	
	for _, test := range tests {
		result := GetObjectTypeFromPath(test.path)
		if result != test.expected {
			t.Errorf("GetObjectTypeFromPath(%s) = %s, expected %s", test.path, result, test.expected)
		}
	}
}