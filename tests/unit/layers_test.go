package unit

import (
	"context"
	"testing"
	"time"

	"github.com/joelpate/arxos/internal/rendering"
	"github.com/joelpate/arxos/internal/rendering"
	"github.com/joelpate/arxos/internal/connections"
	"github.com/joelpate/arxos/internal/database"
	"github.com/joelpate/arxos/internal/energy"
	"github.com/joelpate/arxos/internal/maintenance"
	"github.com/joelpate/arxos/pkg/models"
)

// TestStructureLayer tests the structure layer functionality
func TestStructureLayer(t *testing.T) {
	plan := createTestFloorPlan()
	layer := layers.NewStructureLayer(plan)
	
	// Test layer properties
	if layer.GetName() != "structure" {
		t.Errorf("Expected name 'structure', got %s", layer.GetName())
	}
	
	if layer.GetZ() != abim.LayerStructure {
		t.Errorf("Expected z-index %d, got %d", abim.LayerStructure, layer.GetZ())
	}
	
	if !layer.IsVisible() {
		t.Error("Layer should be visible by default")
	}
	
	// Test visibility toggle
	layer.SetVisible(false)
	if layer.IsVisible() {
		t.Error("Layer should be hidden after SetVisible(false)")
	}
	
	// Test rendering
	viewport := abim.Viewport{
		X: 0, Y: 0,
		Width: 80, Height: 30,
		Zoom: 1.0,
	}
	
	output := layer.Render(viewport)
	if len(output) != 30 {
		t.Errorf("Expected 30 rows, got %d", len(output))
	}
	
	for i, row := range output {
		if len(row) != 80 {
			t.Errorf("Row %d: expected 80 columns, got %d", i, len(row))
		}
	}
}

// TestEquipmentLayer tests the equipment layer functionality
func TestEquipmentLayer(t *testing.T) {
	plan := createTestFloorPlan()
	layer := layers.NewEquipmentLayer(plan.Equipment)
	
	// Test layer properties
	if layer.GetName() != "equipment" {
		t.Errorf("Expected name 'equipment', got %s", layer.GetName())
	}
	
	if layer.GetZ() != abim.LayerEquipment {
		t.Errorf("Expected z-index %d, got %d", abim.LayerEquipment, layer.GetZ())
	}
	
	// Test equipment update
	newEquipment := []models.Equipment{
		{
			ID:       "new_panel",
			Name:     "New Panel",
			Type:     "panel",
			Location: models.Point{X: 30, Y: 20},
			Status:   models.StatusNormal,
		},
	}
	
	layer.UpdateEquipment(newEquipment)
	
	// Test equipment finding
	viewport := abim.Viewport{
		X: 0, Y: 0,
		Width: 80, Height: 30,
		Zoom: 1.0,
	}
	
	// Should find equipment at its location
	equipment := layer.FindEquipmentAt(30, 20, viewport)
	if equipment == nil {
		t.Error("Should find equipment at its location")
	} else if equipment.ID != "new_panel" {
		t.Errorf("Expected equipment ID 'new_panel', got %s", equipment.ID)
	}
	
	// Should not find equipment at empty location
	equipment = layer.FindEquipmentAt(50, 25, viewport)
	if equipment != nil {
		t.Error("Should not find equipment at empty location")
	}
	
	// Test equipment highlighting
	layer.HighlightEquipment("new_panel", true)
	layer.HighlightEquipment("nonexistent", true) // Should not crash
}

// TestConnectionLayer tests the connection layer functionality
func TestConnectionLayer(t *testing.T) {
	db := createTestDB(t)
	defer db.Close()
	
	connManager := connections.NewManager(db)
	layer := layers.NewConnectionLayer(connManager)
	
	// Test layer properties
	if layer.GetName() != "connections" {
		t.Errorf("Expected name 'connections', got %s", layer.GetName())
	}
	
	if layer.GetZ() != abim.LayerConnections {
		t.Errorf("Expected z-index %d, got %d", abim.LayerConnections, layer.GetZ())
	}
	
	// Test label visibility
	layer.SetShowLabels(true)
	layer.SetShowLabels(false)
	
	// Test path style setting
	style := layers.PathStyle{
		Character:    '═',
		ActiveChar:   '▬',
		OverloadChar: '█',
	}
	layer.SetPathStyle(connections.TypeElectrical, style)
	
	// Test rendering with empty connections
	viewport := abim.Viewport{
		X: 0, Y: 0,
		Width: 80, Height: 30,
		Zoom: 1.0,
	}
	
	output := layer.Render(viewport)
	verifyOutputDimensions(t, output, 80, 30)
	
	// Test update
	layer.Update(1.0/30.0)
}

// TestEnergyLayer tests the energy layer functionality
func TestEnergyLayer(t *testing.T) {
	db := createTestDB(t)
	defer db.Close()
	
	connManager := connections.NewManager(db)
	energySystem := createTestEnergySystem(connManager)
	
	layer := layers.NewEnergyLayer(energySystem)
	
	// Test layer properties
	if layer.GetName() != "energy" {
		t.Errorf("Expected name 'energy', got %s", layer.GetName())
	}
	
	if layer.GetZ() != abim.LayerEnergy {
		t.Errorf("Expected z-index %d, got %d", abim.LayerEnergy, layer.GetZ())
	}
	
	// Test flow type setting
	layer.SetFlowType("electrical")
	layer.SetFlowType("thermal")
	layer.SetFlowType("fluid")
	
	// Test simulation
	err := layer.RunSimulation()
	if err != nil {
		t.Errorf("Simulation failed: %v", err)
	}
	
	// Test metrics retrieval
	efficiency := layer.GetEfficiency()
	if efficiency < 0 || efficiency > 100 {
		t.Errorf("Invalid efficiency: %f", efficiency)
	}
	
	totalFlow := layer.GetTotalFlow()
	if totalFlow < 0 {
		t.Errorf("Invalid total flow: %f", totalFlow)
	}
	
	totalLoss := layer.GetTotalLoss()
	if totalLoss < 0 {
		t.Errorf("Invalid total loss: %f", totalLoss)
	}
	
	// Test rendering
	viewport := abim.Viewport{
		X: 0, Y: 0,
		Width: 80, Height: 30,
		Zoom: 1.0,
	}
	
	output := layer.Render(viewport)
	verifyOutputDimensions(t, output, 80, 30)
	
	// Test update
	layer.Update(1.0/30.0)
}

// TestFailureLayer tests the failure layer functionality
func TestFailureLayer(t *testing.T) {
	db := createTestDB(t)
	defer db.Close()
	
	connManager := connections.NewManager(db)
	predictor := maintenance.NewPredictor(db, connManager)
	
	layer := layers.NewFailureLayer(connManager, predictor)
	
	// Test layer properties
	if layer.GetName() != "failure" {
		t.Errorf("Expected name 'failure', got %s", layer.GetName())
	}
	
	if layer.GetZ() != abim.LayerFailure {
		t.Errorf("Expected z-index %d, got %d", abim.LayerFailure, layer.GetZ())
	}
	
	// Test simulation mode
	layer.SetSimulationMode(true)
	layer.SetSimulationMode(false)
	
	// Test failure simulation
	position := models.Point{X: 10, Y: 10}
	layer.SimulateFailure("test_eq", position, layers.FailureElectrical, layers.SeverityMajor)
	
	// Verify active failures
	failures := layer.GetActiveFailures()
	if len(failures) != 1 {
		t.Errorf("Expected 1 active failure, got %d", len(failures))
	}
	
	if len(failures) > 0 {
		failure := failures[0]
		if failure.EquipmentID != "test_eq" {
			t.Errorf("Expected equipment ID 'test_eq', got %s", failure.EquipmentID)
		}
		
		if failure.FailureType != layers.FailureElectrical {
			t.Errorf("Expected electrical failure, got %s", failure.FailureType)
		}
		
		if failure.Severity != layers.SeverityMajor {
			t.Errorf("Expected major severity, got %s", failure.Severity)
		}
	}
	
	// Test failure clearing
	layer.ClearFailures()
	failures = layer.GetActiveFailures()
	if len(failures) != 0 {
		t.Errorf("Expected 0 failures after clearing, got %d", len(failures))
	}
	
	// Test rendering
	viewport := abim.Viewport{
		X: 0, Y: 0,
		Width: 80, Height: 30,
		Zoom: 1.0,
	}
	
	output := layer.Render(viewport)
	verifyOutputDimensions(t, output, 80, 30)
	
	// Test update
	layer.Update(1.0/30.0)
}

// TestLayerZOrdering tests that layers are properly ordered by z-index
func TestLayerZOrdering(t *testing.T) {
	expectedOrder := []struct {
		name string
		z    int
	}{
		{"structure", abim.LayerStructure},
		{"equipment", abim.LayerEquipment},
		{"connections", abim.LayerConnections},
		{"particles", abim.LayerParticles},
		{"energy", abim.LayerEnergy},
		{"failure", abim.LayerFailure},
	}
	
	// Verify z-indices are in correct order
	for i := 1; i < len(expectedOrder); i++ {
		prev := expectedOrder[i-1]
		curr := expectedOrder[i]
		
		if prev.z >= curr.z {
			t.Errorf("Layer %s (z=%d) should be below %s (z=%d)", 
				prev.name, prev.z, curr.name, curr.z)
		}
	}
}

// TestLayerPerformance tests individual layer rendering performance
func TestLayerPerformance(t *testing.T) {
	plan := createTestFloorPlan()
	
	layers := map[string]abim.Layer{
		"structure": layers.NewStructureLayer(plan),
		"equipment": layers.NewEquipmentLayer(plan.Equipment),
	}
	
	viewport := abim.Viewport{
		X: 0, Y: 0,
		Width: 100, Height: 50,
		Zoom: 1.0,
	}
	
	for name, layer := range layers {
		t.Run(name, func(t *testing.T) {
			start := time.Now()
			iterations := 50
			
			for i := 0; i < iterations; i++ {
				layer.Update(1.0/30.0)
				output := layer.Render(viewport)
				verifyOutputDimensions(t, output, 100, 50)
			}
			
			duration := time.Since(start)
			avgTime := duration / time.Duration(iterations)
			
			// Individual layers should render very quickly
			if avgTime > 5*time.Millisecond {
				t.Errorf("Layer %s rendering too slow: %v per frame", name, avgTime)
			}
			
			t.Logf("Layer %s: %v per frame", name, avgTime)
		})
	}
}

// Helper functions

func createTestFloorPlan() *models.FloorPlan {
	return &models.FloorPlan{
		Name:     "Test Floor",
		Building: "Test Building",
		Level:    1,
		Rooms: []models.Room{
			{
				ID:   "room_001",
				Name: "Test Room",
				Bounds: models.Bounds{
					MinX: 0, MinY: 0,
					MaxX: 50, MaxY: 30,
				},
			},
		},
		Equipment: []models.Equipment{
			{
				ID:       "panel_001",
				Name:     "Test Panel",
				Type:     "panel",
				Location: models.Point{X: 5, Y: 5},
				Status:   models.StatusNormal,
			},
			{
				ID:       "outlet_001",
				Name:     "Test Outlet",
				Type:     "outlet",
				Location: models.Point{X: 15, Y: 10},
				Status:   models.StatusNormal,
			},
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}

func createTestDB(t *testing.T) database.DB {
	config := database.NewConfig(":memory:")
	db := database.NewSQLiteDB(config)
	
	ctx := context.Background()
	err := db.Connect(ctx, "")
	if err != nil {
		t.Fatalf("Failed to create test database: %v", err)
	}
	
	return db
}

func createTestEnergySystem(connManager *connections.Manager) *energy.FlowSystem {
	// Create a real energy flow system for testing
	return energy.NewFlowSystem(energy.FlowElectrical, connManager)
}

func verifyOutputDimensions(t *testing.T, output [][]rune, expectedWidth, expectedHeight int) {
	if len(output) != expectedHeight {
		t.Errorf("Expected %d rows, got %d", expectedHeight, len(output))
	}
	
	for i, row := range output {
		if len(row) != expectedWidth {
			t.Errorf("Row %d: expected %d columns, got %d", i, expectedWidth, len(row))
		}
	}
}