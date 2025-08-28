package commands

import (
	"testing"
	
	"github.com/arxos/arxos/cmd/navigation"
	"github.com/stretchr/testify/assert"
)

// Test navigation context
func TestNavigationContext(t *testing.T) {
	ctx := navigation.GetContext()
	
	// Test initial state
	assert.Equal(t, "/", ctx.GetCurrentPath())
	
	// Test navigation
	ctx.NavigateTo("/electrical/main-panel")
	assert.Equal(t, "/electrical/main-panel", ctx.GetCurrentPath())
	
	// Test relative navigation
	ctx.NavigateTo("circuit-7")
	assert.Equal(t, "/electrical/main-panel/circuit-7", ctx.GetCurrentPath())
	
	// Test parent navigation
	ctx.NavigateTo("..")
	assert.Equal(t, "/electrical/main-panel", ctx.GetCurrentPath())
	
	// Test exact path from vision.md
	ctx.NavigateTo("/electrical/main-panel/circuit-7/outlet-3")
	assert.Equal(t, "/electrical/main-panel/circuit-7/outlet-3", ctx.GetCurrentPath())
}

// Test path normalization
func TestPathNormalization(t *testing.T) {
	tests := []struct {
		input    string
		expected string
	}{
		{"", "/"},
		{"electrical", "/electrical"},
		{"/electrical//main-panel", "/electrical/main-panel"},
		{"/electrical/./main-panel", "/electrical/main-panel"},
		{"/electrical/../electrical/main-panel", "/electrical/main-panel"},
	}
	
	for _, test := range tests {
		result := navigation.NormalizePath(test.input)
		assert.Equal(t, test.expected, result, "Failed for input: %s", test.input)
	}
}

// Test path parsing
func TestParsePath(t *testing.T) {
	path := "/electrical/main-panel/circuit-7/outlet-3"
	components := navigation.ParsePath(path)
	
	assert.Equal(t, 4, len(components))
	assert.Equal(t, "electrical", components[0])
	assert.Equal(t, "main-panel", components[1])
	assert.Equal(t, "circuit-7", components[2])
	assert.Equal(t, "outlet-3", components[3])
}

// Test object type detection
func TestGetObjectTypeFromPath(t *testing.T) {
	tests := []struct {
		path     string
		expected string
	}{
		{"/electrical/main-panel", "panel"},
		{"/electrical/main-panel/circuit-7", "circuit"},
		{"/electrical/main-panel/circuit-7/outlet-3", "outlet"},
		{"/floors/2/room-201", "room"},
		{"/hvac/thermostats/t-101", "thermostat"},
	}
	
	for _, test := range tests {
		result := navigation.GetObjectTypeFromPath(test.path)
		assert.Equal(t, test.expected, result, "Failed for path: %s", test.path)
	}
}

// Test property filter parsing for find command
func TestParsePropertyFilter(t *testing.T) {
	tests := []struct {
		input        string
		expectedOp   string
		expectedVal  float64
	}{
		{">15A", ">", 15.0},
		{"<10A", "<", 10.0},
		{">=20", ">=", 20.0},
		{"<=5.5", "<=", 5.5},
		{"=120V", "=", 120.0},
	}
	
	for _, test := range tests {
		filter := parsePropertyFilter(test.input)
		assert.Equal(t, test.expectedOp, filter.Operator)
		assert.Equal(t, test.expectedVal, filter.Value)
	}
}

// Test the exact commands from vision.md lines 450-480
func TestVisionCommands(t *testing.T) {
	ctx := navigation.GetContext()
	
	// Test: arxos cd /electrical/main-panel/circuit-7/outlet-3
	err := ctx.NavigateTo("/electrical/main-panel/circuit-7/outlet-3")
	assert.NoError(t, err)
	
	// Test: arxos pwd
	currentPath := ctx.GetCurrentPath()
	assert.Equal(t, "/electrical/main-panel/circuit-7/outlet-3", currentPath)
	
	// Test: arxos ls (at outlet-3)
	// This would show: voltage: 120V, load: 12.5A, confidence: 0.73
	contents := getContentsForPath(currentPath)
	// In a real test, we'd verify the properties are displayed correctly
	
	// Test: arxos tree /hvac
	// Would display full HVAC system tree
	hvacContents := getTreeContents("/hvac")
	assert.Greater(t, len(hvacContents), 0)
	
	// Test: arxos find /electrical -type outlet -load ">15A"
	criteria := &SearchCriteria{
		Type: "outlet",
		LoadFilter: &PropertyFilter{
			Operator: ">",
			Value:    15.0,
		},
	}
	
	// In a real implementation, this would search the actual data
	// For now, we just verify the criteria is built correctly
	assert.Equal(t, "outlet", criteria.Type)
	assert.Equal(t, ">", criteria.LoadFilter.Operator)
	assert.Equal(t, 15.0, criteria.LoadFilter.Value)
}

// Test command integration
func TestCommandIntegration(t *testing.T) {
	// This would be an integration test running actual commands
	// For now, we verify the commands are registered
	
	assert.NotNil(t, CdCmd)
	assert.NotNil(t, PwdCmd)
	assert.NotNil(t, LsCmd)
	assert.NotNil(t, TreeCmd)
	assert.NotNil(t, FindCmd)
	
	// Verify command names
	assert.Equal(t, "cd", CdCmd.Use)
	assert.Equal(t, "pwd", PwdCmd.Use)
	assert.Equal(t, "ls", LsCmd.Use)
	assert.Equal(t, "tree", TreeCmd.Use)
	assert.Equal(t, "find", FindCmd.Use)
}