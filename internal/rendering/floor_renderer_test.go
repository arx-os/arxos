package rendering

import (
	"fmt"
	"testing"

	"github.com/joelpate/arxos/pkg/models"
	"github.com/stretchr/testify/assert"
)

func TestFloorRenderer_RenderFromFloorPlan(t *testing.T) {
	// Create a simple floor plan
	plan := &models.FloorPlan{
		ID:       "test-floor",
		Name:     "Test Floor",
		Building: "Test Building",
		Level:    1,
		Rooms: []*models.Room{
			{
				ID:   "room1",
				Name: "Office",
				Bounds: models.Bounds{
					MinX: 0,
					MinY: 0,
					MaxX: 30,
					MaxY: 20,
				},
			},
			{
				ID:   "room2",
				Name: "Meeting",
				Bounds: models.Bounds{
					MinX: 30,
					MinY: 0,
					MaxX: 50,
					MaxY: 20,
				},
			},
		},
		Equipment: []*models.Equipment{
			{
				ID:   "outlet1",
				Name: "Outlet 1",
				Type: "outlet",
				Location: &models.Point{
					X: 10,
					Y: 5,
				},
				Status: models.StatusOperational,
			},
			{
				ID:   "switch1",
				Name: "Light Switch",
				Type: "switch",
				Location: &models.Point{
					X: 5,
					Y: 10,
				},
				Status: models.StatusOperational,
			},
			{
				ID:   "panel1",
				Name: "Main Panel",
				Type: "panel",
				Location: &models.Point{
					X: 40,
					Y: 10,
				},
				Status: models.StatusOperational,
			},
		},
	}

	// Create renderer
	renderer := NewFloorRenderer(80, 30)

	// Render the floor plan
	output, err := renderer.RenderFromFloorPlan(plan)
	assert.NoError(t, err)
	assert.NotEmpty(t, output)

	// Check that output contains expected elements
	assert.Contains(t, output, "FLOOR PLAN")
	assert.Contains(t, output, "LEGEND")
	assert.Contains(t, output, "Office")
	assert.Contains(t, output, "Mee")
	assert.Contains(t, output, "Rooms: 2")
	assert.Contains(t, output, "Equipment: 3")

	// Check for equipment characters in legend
	assert.Contains(t, output, "o = Electrical Outlet")
	assert.Contains(t, output, "s = Light Switch")
	assert.Contains(t, output, "P = Electrical Panel")
}

func TestFloorRenderer_DrawRectangle(t *testing.T) {
	renderer := NewFloorRenderer(20, 10)
	
	// Draw a rectangle
	renderer.drawRectangle(2, 2, 10, 6)
	
	// Check corners
	assert.Equal(t, CharCornerTL, renderer.getChar(2, 2))
	assert.Equal(t, CharCornerTR, renderer.getChar(10, 2))
	assert.Equal(t, CharCornerBL, renderer.getChar(2, 6))
	assert.Equal(t, CharCornerBR, renderer.getChar(10, 6))
	
	// Check walls
	assert.Equal(t, CharWallHorizontal, renderer.getChar(5, 2))
	assert.Equal(t, CharWallHorizontal, renderer.getChar(5, 6))
	assert.Equal(t, CharWallVertical, renderer.getChar(2, 4))
	assert.Equal(t, CharWallVertical, renderer.getChar(10, 4))
}

func TestFloorRenderer_GetEquipmentChar(t *testing.T) {
	renderer := NewFloorRenderer(10, 10)
	
	tests := []struct {
		equipType string
		expected  rune
	}{
		{"outlet", CharOutlet},
		{"electrical_outlet", CharOutlet},
		{"switch", CharSwitch},
		{"light_switch", CharSwitch},
		{"panel", CharPanel},
		{"electrical_panel", CharPanel},
		{"hvac", CharHVAC},
		{"fire_alarm", CharFireAlarm},
		{"camera", CharCamera},
		{"wifi", CharAccessPoint},
		{"unknown", CharEquipmentOther},
	}
	
	for _, tt := range tests {
		t.Run(tt.equipType, func(t *testing.T) {
			char := renderer.getEquipmentChar(tt.equipType)
			assert.Equal(t, tt.expected, char)
		})
	}
}

func TestFloorRenderer_EmptyFloorPlan(t *testing.T) {
	renderer := NewFloorRenderer(40, 20)
	
	// Render empty floor plan
	plan := &models.FloorPlan{
		ID:       "empty",
		Name:     "Empty Floor",
		Building: "Test",
		Level:    1,
		Rooms:    []*models.Room{},
		Equipment: []*models.Equipment{},
	}
	
	output, err := renderer.RenderFromFloorPlan(plan)
	assert.NoError(t, err)
	assert.NotEmpty(t, output)
	
	// Should still have structure
	assert.Contains(t, output, "FLOOR PLAN")
	assert.Contains(t, output, "LEGEND")
	assert.Contains(t, output, "Rooms: 0")
	assert.Contains(t, output, "Equipment: 0")
}

func TestFloorRenderer_LargeFloorPlan(t *testing.T) {
	// Test with many rooms and equipment
	plan := &models.FloorPlan{
		ID:       "large",
		Name:     "Large Floor",
		Building: "Big Building",
		Level:    1,
		Rooms:    make([]*models.Room, 0),
		Equipment: make([]*models.Equipment, 0),
	}
	
	// Add 10 rooms
	for i := 0; i < 10; i++ {
		room := &models.Room{
			ID:   fmt.Sprintf("room%d", i),
			Name: fmt.Sprintf("Room %d", i),
			Bounds: models.Bounds{
				MinX: float64(i * 10),
				MinY: 0,
				MaxX: float64((i + 1) * 10),
				MaxY: 10,
			},
		}
		plan.Rooms = append(plan.Rooms, room)
	}
	
	// Add 20 equipment items
	for i := 0; i < 20; i++ {
		equip := &models.Equipment{
			ID:   fmt.Sprintf("equip%d", i),
			Name: fmt.Sprintf("Equipment %d", i),
			Type: "outlet",
			Location: &models.Point{
				X: float64(i * 5),
				Y: 5,
			},
			Status: models.StatusOperational,
		}
		plan.Equipment = append(plan.Equipment, equip)
	}
	
	renderer := NewFloorRenderer(120, 40)
	output, err := renderer.RenderFromFloorPlan(plan)
	
	assert.NoError(t, err)
	assert.NotEmpty(t, output)
	assert.Contains(t, output, "Rooms: 10")
	assert.Contains(t, output, "Equipment: 20")
}

func TestFloorRenderer_ScaleCalculation(t *testing.T) {
	renderer := NewFloorRenderer(40, 20)
	
	// Test with a floor plan that needs scaling
	plan := &models.FloorPlan{
		ID: "scale-test",
		Rooms: []*models.Room{
			{
				ID:   "big-room",
				Name: "Big Room",
				Bounds: models.Bounds{
					MinX: 0,
					MinY: 0,
					MaxX: 100, // Larger than renderer width
					MaxY: 50,  // Larger than renderer height
				},
			},
		},
	}
	
	renderer.calculateScaleFromModel(plan)
	
	// Scale should be less than 1 to fit
	assert.Less(t, renderer.scale, 1.0)
	
	// Render should not panic
	output, err := renderer.RenderFromFloorPlan(plan)
	assert.NoError(t, err)
	assert.NotEmpty(t, output)
}