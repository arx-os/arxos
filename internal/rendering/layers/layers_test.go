package layers

import (
	"testing"

	"github.com/arx-os/arxos/pkg/models"
)

func TestLayerManager(t *testing.T) {
	manager := NewManager()

	// Test adding layers
	layer1 := NewBaseLayer("test1", 10)
	layer2 := NewBaseLayer("test2", 5)
	layer3 := NewBaseLayer("test3", 15)

	if err := manager.AddLayer(layer1); err != nil {
		t.Errorf("Failed to add layer1: %v", err)
	}
	if err := manager.AddLayer(layer2); err != nil {
		t.Errorf("Failed to add layer2: %v", err)
	}
	if err := manager.AddLayer(layer3); err != nil {
		t.Errorf("Failed to add layer3: %v", err)
	}

	// Test duplicate layer name
	duplicateLayer := NewBaseLayer("test1", 20)
	if err := manager.AddLayer(duplicateLayer); err == nil {
		t.Error("Expected error when adding duplicate layer name")
	}

	// Test getting layers sorted by priority
	layers := manager.GetLayers()
	if len(layers) != 3 {
		t.Errorf("Expected 3 layers, got %d", len(layers))
	}

	// Check sort order (lowest priority first)
	if layers[0].GetName() != "test2" { // priority 5
		t.Errorf("Expected first layer to be test2, got %s", layers[0].GetName())
	}
	if layers[1].GetName() != "test1" { // priority 10
		t.Errorf("Expected second layer to be test1, got %s", layers[1].GetName())
	}
	if layers[2].GetName() != "test3" { // priority 15
		t.Errorf("Expected third layer to be test3, got %s", layers[2].GetName())
	}

	// Test visibility
	if err := manager.SetLayerVisible("test1", false); err != nil {
		t.Errorf("Failed to set layer visibility: %v", err)
	}

	if layer, ok := manager.GetLayer("test1"); ok {
		if layer.IsVisible() {
			t.Error("Layer should not be visible after setting to false")
		}
	} else {
		t.Error("Failed to get layer test1")
	}

	// Test removing layer
	if err := manager.RemoveLayer("test2"); err != nil {
		t.Errorf("Failed to remove layer: %v", err)
	}

	layers = manager.GetLayers()
	if len(layers) != 2 {
		t.Errorf("Expected 2 layers after removal, got %d", len(layers))
	}

	// Test removing non-existent layer
	if err := manager.RemoveLayer("nonexistent"); err == nil {
		t.Error("Expected error when removing non-existent layer")
	}
}

func TestStructureLayer(t *testing.T) {
	// Create a test floor plan
	floorPlan := &models.FloorPlan{
		Name:     "Test Floor",
		Building: "Test Building",
		Rooms: []*models.Room{
			{
				ID:   "room1",
				Name: "Office",
				Bounds: models.Bounds{
					MinX: 0,
					MinY: 0,
					MaxX: 10,
					MaxY: 8,
				},
			},
		},
	}

	layer := NewStructureLayer(floorPlan)

	// Test layer properties
	if layer.GetName() != "structure" {
		t.Errorf("Expected layer name 'structure', got %s", layer.GetName())
	}

	if layer.GetPriority() != PriorityStructure {
		t.Errorf("Expected priority %d, got %d", PriorityStructure, layer.GetPriority())
	}

	if !layer.IsVisible() {
		t.Error("Layer should be visible by default")
	}

	// Test rendering
	buffer := make([][]rune, 20)
	for i := range buffer {
		buffer[i] = make([]rune, 30)
		for j := range buffer[i] {
			buffer[i][j] = ' '
		}
	}

	viewport := Viewport{
		X:      0,
		Y:      0,
		Width:  30,
		Height: 20,
		Zoom:   1.0,
	}

	layer.Render(buffer, viewport)

	// Check that walls were rendered
	// Top-left corner should have a corner character
	if buffer[0][0] != '┌' {
		t.Errorf("Expected top-left corner '┌', got '%c'", buffer[0][0])
	}

	// Top wall should have horizontal line
	if buffer[0][5] != '─' {
		t.Errorf("Expected horizontal wall '─', got '%c'", buffer[0][5])
	}

	// Room interior should have floor dots (avoid center where room name is)
	if buffer[2][3] != '·' {
		t.Errorf("Expected floor dot '·', got '%c'", buffer[2][3])
	}
}

func TestEquipmentLayer(t *testing.T) {
	equipment := []*models.Equipment{
		{
			ID:   "eq1",
			Name: "Outlet1",
			Type: "outlet",
			Location: &models.Point{
				X: 5,
				Y: 3,
			},
			Status: models.StatusOperational,
		},
		{
			ID:   "eq2",
			Name: "Switch1",
			Type: "switch",
			Location: &models.Point{
				X: 8,
				Y: 3,
			},
			Status: models.StatusFailed,
		},
	}

	layer := NewEquipmentLayer(equipment)

	// Test layer properties
	if layer.GetName() != "equipment" {
		t.Errorf("Expected layer name 'equipment', got %s", layer.GetName())
	}

	if layer.GetPriority() != PriorityEquipment {
		t.Errorf("Expected priority %d, got %d", PriorityEquipment, layer.GetPriority())
	}

	// Test rendering
	buffer := make([][]rune, 10)
	for i := range buffer {
		buffer[i] = make([]rune, 20)
		for j := range buffer[i] {
			buffer[i][j] = ' '
		}
	}

	viewport := Viewport{
		X:      0,
		Y:      0,
		Width:  20,
		Height: 10,
		Zoom:   1.0,
	}

	layer.Render(buffer, viewport)

	// Check outlet symbol
	if buffer[3][5] != '●' {
		t.Errorf("Expected outlet symbol '●', got '%c'", buffer[3][5])
	}

	// Check failed equipment symbol
	if buffer[3][8] != '✗' {
		t.Errorf("Expected failed symbol '✗', got '%c'", buffer[3][8])
	}

	// Test GetEquipmentAt
	found := layer.GetEquipmentAt(5, 3)
	if found == nil {
		t.Error("Expected to find equipment at (5, 3)")
	} else if found.ID != "eq1" {
		t.Errorf("Expected equipment ID 'eq1', got '%s'", found.ID)
	}

	// Test not finding equipment
	notFound := layer.GetEquipmentAt(10, 10)
	if notFound != nil {
		t.Error("Should not find equipment at (10, 10)")
	}
}

func TestLayerPrioritySorting(t *testing.T) {
	manager := NewManager()

	// Add layers in random order
	layers := []Layer{
		NewBaseLayer("ui", PriorityUI),
		NewBaseLayer("background", PriorityBackground),
		NewBaseLayer("equipment", PriorityEquipment),
		NewBaseLayer("structure", PriorityStructure),
		NewBaseLayer("overlay", PriorityOverlay),
	}

	for _, layer := range layers {
		if err := manager.AddLayer(layer); err != nil {
			t.Errorf("Failed to add layer %s: %v", layer.GetName(), err)
		}
	}

	// Get sorted layers
	sorted := manager.GetLayers()

	// Verify correct order
	expectedOrder := []string{"background", "structure", "equipment", "overlay", "ui"}

	for i, expected := range expectedOrder {
		if sorted[i].GetName() != expected {
			t.Errorf("Position %d: expected %s, got %s", i, expected, sorted[i].GetName())
		}
	}
}

func TestViewportClipping(t *testing.T) {
	// Test that rendering respects viewport boundaries
	equipment := []*models.Equipment{
		{
			ID:       "inside",
			Type:     "outlet",
			Location: &models.Point{X: 5, Y: 5},
		},
		{
			ID:       "outside",
			Type:     "outlet",
			Location: &models.Point{X: 50, Y: 50}, // Outside viewport
		},
	}

	layer := NewEquipmentLayer(equipment)

	buffer := make([][]rune, 10)
	for i := range buffer {
		buffer[i] = make([]rune, 10)
		for j := range buffer[i] {
			buffer[i][j] = ' '
		}
	}

	viewport := Viewport{
		X:      0,
		Y:      0,
		Width:  10,
		Height: 10,
		Zoom:   1.0,
	}

	layer.Render(buffer, viewport)

	// Check that inside equipment is rendered
	if buffer[5][5] != '●' {
		t.Error("Equipment inside viewport should be rendered")
	}

	// Buffer should not have any rendering artifacts from outside equipment
	// (This would cause a panic if not properly clipped)
	for y := 0; y < 10; y++ {
		for x := 0; x < 10; x++ {
			if (x != 5 || y != 5) && buffer[y][x] != ' ' {
				t.Errorf("Unexpected character at (%d, %d): %c", x, y, buffer[y][x])
			}
		}
	}
}
