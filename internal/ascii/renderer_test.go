package ascii

import (
	"strings"
	"testing"
	"time"
	
	"github.com/joelpate/arxos/pkg/models"
)

func TestRendererCreation(t *testing.T) {
	renderer := NewRenderer(80, 24)
	
	if renderer.Width != 80 {
		t.Errorf("Expected width 80, got %d", renderer.Width)
	}
	
	if renderer.Height != 24 {
		t.Errorf("Expected height 24, got %d", renderer.Height)
	}
}

func TestRenderCompact(t *testing.T) {
	plan := createTestFloorPlan()
	renderer := NewRenderer(80, 24)
	
	output := renderer.RenderCompact(plan)
	
	// Check that output contains expected elements
	expectedStrings := []string{
		"Test Building - Test Floor",
		"═══════════════════════════════",
		"Room 2A",
		"Room 2B",
		"Mech",
		"●", // Normal outlet
		"○", // Failed outlet
		"⚡", // Panel
	}
	
	for _, expected := range expectedStrings {
		if !strings.Contains(output, expected) {
			t.Errorf("Output missing expected string: %s", expected)
		}
	}
}

func TestGetSymbol(t *testing.T) {
	renderer := NewRenderer(80, 24)
	
	tests := []struct {
		name     string
		equip    models.Equipment
		expected string
	}{
		{
			name: "normal outlet",
			equip: models.Equipment{
				Type:   "outlet",
				Status: models.StatusNormal,
			},
			expected: "●",
		},
		{
			name: "failed outlet",
			equip: models.Equipment{
				Type:   "outlet",
				Status: models.StatusFailed,
			},
			expected: "○",
		},
		{
			name: "needs repair outlet",
			equip: models.Equipment{
				Type:   "outlet",
				Status: models.StatusNeedsRepair,
			},
			expected: "◐",
		},
		{
			name: "panel",
			equip: models.Equipment{
				Type:   "panel",
				Status: models.StatusNormal,
			},
			expected: "⚡",
		},
		{
			name: "switch",
			equip: models.Equipment{
				Type:   "switch",
				Status: models.StatusNormal,
			},
			expected: "▪",
		},
		{
			name: "unknown type",
			equip: models.Equipment{
				Type:   "unknown",
				Status: models.StatusNormal,
			},
			expected: "?",
		},
	}
	
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			symbol := renderer.getSymbol(tt.equip)
			if symbol != tt.expected {
				t.Errorf("getSymbol() = %s, want %s", symbol, tt.expected)
			}
		})
	}
}

func TestCreateGrid(t *testing.T) {
	renderer := NewRenderer(10, 5)
	grid := renderer.createGrid()
	
	if len(grid) != 5 {
		t.Errorf("Expected grid height 5, got %d", len(grid))
	}
	
	for i, row := range grid {
		if len(row) != 10 {
			t.Errorf("Expected row %d width 10, got %d", i, len(row))
		}
		
		// Check all cells are initialized to space
		for j, cell := range row {
			if cell != ' ' {
				t.Errorf("Cell [%d][%d] not initialized to space, got %c", i, j, cell)
			}
		}
	}
}

func TestRenderWithEquipment(t *testing.T) {
	plan := createTestFloorPlan()
	renderer := NewRenderer(80, 24)
	
	output := renderer.Render(plan)
	
	// Check header
	if !strings.Contains(output, "Floor Plan - ASCII View") {
		t.Error("Missing header in output")
	}
	
	// Check legend
	if !strings.Contains(output, "Legend:") {
		t.Error("Missing legend in output")
	}
	
	// Check for room boundaries (box drawing characters)
	boxChars := []string{"┌", "┐", "└", "┘", "─", "│"}
	for _, char := range boxChars {
		if !strings.Contains(output, char) {
			t.Errorf("Missing box drawing character: %s", char)
		}
	}
}

func TestGridToString(t *testing.T) {
	renderer := NewRenderer(5, 3)
	grid := [][]rune{
		{'┌', '─', '─', '─', '┐'},
		{'│', ' ', '●', ' ', '│'},
		{'└', '─', '─', '─', '┘'},
	}
	
	output := renderer.gridToString(grid)
	
	// Check that grid is properly converted
	if !strings.Contains(output, "┌───┐") {
		t.Error("Top border not found in output")
	}
	
	if !strings.Contains(output, "│ ● │") {
		t.Error("Middle row with equipment not found in output")
	}
	
	if !strings.Contains(output, "└───┘") {
		t.Error("Bottom border not found in output")
	}
}

// Helper function to create a test floor plan
func createTestFloorPlan() *models.FloorPlan {
	return &models.FloorPlan{
		Name:      "Test Floor",
		Building:  "Test Building",
		Level:     2,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		Rooms: []models.Room{
			{
				ID:   "room_2a",
				Name: "Room 2A",
				Bounds: models.Bounds{
					MinX: 0, MinY: 0,
					MaxX: 10, MaxY: 10,
				},
				Equipment: []string{"outlet_2a_1", "outlet_2a_2"},
			},
			{
				ID:   "room_2b",
				Name: "Room 2B",
				Bounds: models.Bounds{
					MinX: 10, MinY: 0,
					MaxX: 20, MaxY: 10,
				},
				Equipment: []string{"outlet_2b_1", "outlet_2b_2"},
			},
			{
				ID:   "mech",
				Name: "Mech",
				Bounds: models.Bounds{
					MinX: 20, MinY: 0,
					MaxX: 25, MaxY: 10,
				},
				Equipment: []string{"panel_1"},
			},
		},
		Equipment: []models.Equipment{
			{
				ID:       "outlet_2a_1",
				Name:     "Outlet 2A-1",
				Type:     "outlet",
				Location: models.Point{X: 2, Y: 5},
				RoomID:   "room_2a",
				Status:   models.StatusNormal,
			},
			{
				ID:       "outlet_2a_2",
				Name:     "Outlet 2A-2",
				Type:     "outlet",
				Location: models.Point{X: 5, Y: 5},
				RoomID:   "room_2a",
				Status:   models.StatusNormal,
			},
			{
				ID:       "outlet_2b_1",
				Name:     "Outlet 2B-1",
				Type:     "outlet",
				Location: models.Point{X: 12, Y: 5},
				RoomID:   "room_2b",
				Status:   models.StatusNormal,
			},
			{
				ID:       "outlet_2b_2",
				Name:     "Outlet 2B-2",
				Type:     "outlet",
				Location: models.Point{X: 15, Y: 5},
				RoomID:   "room_2b",
				Status:   models.StatusFailed,
			},
			{
				ID:       "panel_1",
				Name:     "Panel 1",
				Type:     "panel",
				Location: models.Point{X: 22, Y: 5},
				RoomID:   "mech",
				Status:   models.StatusNormal,
			},
		},
	}
}