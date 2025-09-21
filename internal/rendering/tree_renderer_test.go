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
		Name: "Test Building",
		Metadata: bim.Metadata{
			Location: struct {
				Address string `json:"address,omitempty"`
				City    string `json:"city,omitempty"`
				State   string `json:"state,omitempty"`
				Country string `json:"country,omitempty"`
			}{
				Address: "123 Test St",
			},
		},
		Floors: []bim.Floor{
			{
				Level: 1,
				Name:  "Ground Floor",
				Equipment: []bim.Equipment{
					{
						ID:   "OUTLET-001",
						Type: "electrical",
						Location: bim.Location{
							X:    10,
							Y:    5,
							Room: "101",
						},
						Status: bim.StatusOperational,
					},
					{
						ID:   "LIGHT-001",
						Type: "lighting",
						Location: bim.Location{
							X:    10,
							Y:    10,
							Room: "101",
						},
						Status: bim.StatusFailed,
					},
				},
			},
			{
				Level: 2,
				Name:  "Second Floor",
				Equipment: []bim.Equipment{
					{
						ID:   "PANEL-001",
						Type: "electrical",
						Location: bim.Location{
							X:    2,
							Y:    2,
							Room: "Office",
						},
						Status: bim.StatusOperational,
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
		assert.Contains(t, output, "OUTLET-001")
		assert.Contains(t, output, "LIGHT-001")
		assert.Contains(t, output, "[FAILED]")

		// Admin sees coordinates
		assert.Contains(t, output, "@(10.0,5.0)")
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
		assert.Contains(t, output, "@(10.0,5.0)")
		assert.Contains(t, output, "@(10.0,10.0)")
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
		Name:   "Empty Building",
		Floors: []bim.Floor{},
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
		Name: "Format Test",
		Floors: []bim.Floor{
			{
				Level: 1,
				Name:  "First",
				Equipment: []bim.Equipment{
					{ID: "EQ1", Type: "sensor", Location: bim.Location{Room: "101"}},
					{ID: "EQ2", Type: "sensor", Location: bim.Location{Room: "101"}},
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