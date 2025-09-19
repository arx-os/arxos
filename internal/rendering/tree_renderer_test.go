package rendering

import (
	"strings"
	"testing"

	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"

	"github.com/arx-os/arxos/internal/bim"
	"github.com/arx-os/arxos/internal/core/user"
)

func TestTreeRenderer_RenderBuilding(t *testing.T) {
	renderer := NewTreeRenderer()

	// Create test building
	building := &bim.Building{
		ArxosID: "TEST-001",
		Name:    "Test Building",
		Address: "123 Test St",
		Floors: []bim.Floor{
			{
				Number: 1,
				Name:   "Ground Floor",
				Rooms: []bim.Room{
					{
						Number: "101",
						Name:   "Lobby",
						Equipment: []bim.Equipment{
							{
								ID:     "OUTLET-001",
								Name:   "Main Outlet",
								Type:   "electrical",
								Status: "OK",
								GridX:  10,
								GridY:  5,
							},
							{
								ID:     "LIGHT-001",
								Name:   "Entry Light",
								Type:   "lighting",
								Status: "FAILED",
								GridX:  10,
								GridY:  10,
							},
						},
					},
					{
						Number: "102",
						Name:   "Office",
						Equipment: []bim.Equipment{
							{
								ID:     "PANEL-001",
								Name:   "Breaker Panel",
								Type:   "electrical",
								Status: "OK",
								GridX:  2,
								GridY:  2,
							},
						},
					},
				},
			},
		},
	}

	// Test with admin user (sees everything)
	t.Run("AdminUser", func(t *testing.T) {
		adminUser := &user.User{
			ID:       uuid.New(),
			Email:    "admin@test.com",
			FullName: "Admin User",
			Role:     user.RoleAdmin,
		}

		output, err := renderer.RenderBuilding(building, adminUser)
		assert.NoError(t, err)
		assert.NotEmpty(t, output)

		// Check structure is present
		assert.Contains(t, output, "Building: Test Building")
		assert.Contains(t, output, "Address: 123 Test St")
		assert.Contains(t, output, "Floor 1: Ground Floor")
		assert.Contains(t, output, "Room 101: Lobby")
		assert.Contains(t, output, "OUTLET-001")
		assert.Contains(t, output, "LIGHT-001")
		assert.Contains(t, output, "[FAILED]")

		// Admin sees coordinates
		assert.Contains(t, output, "@(10,5)")
	})

	// Test with viewer user (no coordinates)
	t.Run("ViewerUser", func(t *testing.T) {
		viewerUser := &user.User{
			ID:       uuid.New(),
			Email:    "viewer@test.com",
			FullName: "Viewer User",
			Role:     user.RoleViewer,
		}

		output, err := renderer.RenderBuilding(building, viewerUser)
		assert.NoError(t, err)
		assert.NotEmpty(t, output)

		// Check structure is present
		assert.Contains(t, output, "Building: Test Building")
		assert.Contains(t, output, "Floor 1: Ground Floor")

		// Viewer doesn't see coordinates
		assert.NotContains(t, output, "@(")
	})

	// Test with technician user (sees coordinates)
	t.Run("TechnicianUser", func(t *testing.T) {
		techUser := &user.User{
			ID:       uuid.New(),
			Email:    "tech@test.com",
			FullName: "Tech User",
			Role:     user.RoleTechnician,
		}

		output, err := renderer.RenderBuilding(building, techUser)
		assert.NoError(t, err)
		assert.NotEmpty(t, output)

		// Technician sees coordinates
		assert.Contains(t, output, "@(10,5)")
		assert.Contains(t, output, "@(10,10)")
	})
}

func TestTreeRenderer_FormatStatus(t *testing.T) {
	renderer := NewTreeRenderer()

	tests := []struct {
		input    string
		expected string
	}{
		{"OK", "OK"},
		{"OPERATIONAL", "OK"},
		{"ACTIVE", "OK"},
		{"FAILED", "FAILED"},
		{"ERROR", "FAILED"},
		{"FAULT", "FAILED"},
		{"WARNING", "WARN"},
		{"DEGRADED", "WARN"},
		{"OFFLINE", "OFFLINE"},
		{"DISABLED", "OFFLINE"},
		{"unknown_status", "UNKNOWN"},
		{"", "UNKNOWN"},
	}

	for _, tt := range tests {
		result := renderer.formatStatus(tt.input)
		assert.Equal(t, tt.expected, result, "Input: %s", tt.input)
	}
}

func TestTreeRenderer_EmptyBuilding(t *testing.T) {
	renderer := NewTreeRenderer()

	building := &bim.Building{
		ArxosID: "EMPTY-001",
		Name:    "Empty Building",
		Floors:  []bim.Floor{},
	}

	adminUser := &user.User{
		ID:   uuid.New(),
		Role: user.RoleAdmin,
	}

	output, err := renderer.RenderBuilding(building, adminUser)
	assert.NoError(t, err)
	assert.Contains(t, output, "Building: Empty Building")
	// Should not have floor information
	assert.NotContains(t, output, "Floor")
}

func TestTreeRenderer_TreeFormatting(t *testing.T) {
	renderer := NewTreeRenderer()

	// Create a building with specific structure to test tree formatting
	building := &bim.Building{
		ArxosID: "FORMAT-001",
		Name:    "Format Test",
		Floors: []bim.Floor{
			{
				Number: 1,
				Name:   "First",
				Rooms: []bim.Room{
					{
						Number: "101",
						Equipment: []bim.Equipment{
							{ID: "EQ1", Type: "sensor"},
							{ID: "EQ2", Type: "sensor"},
						},
					},
				},
			},
		},
	}

	adminUser := &user.User{
		ID:   uuid.New(),
		Role: user.RoleAdmin,
	}

	output, err := renderer.RenderBuilding(building, adminUser)
	assert.NoError(t, err)

	// Check tree structure characters
	lines := strings.Split(output, "\n")
	for _, line := range lines {
		if strings.Contains(line, "Floor") {
			assert.True(t, strings.HasPrefix(line, "├── ") || strings.HasPrefix(line, "└── "))
		}
		if strings.Contains(line, "Room") {
			assert.Contains(t, line, "── Room")
		}
		if strings.Contains(line, "EQ1") || strings.Contains(line, "EQ2") {
			assert.Contains(t, line, "── EQ")
		}
	}
}