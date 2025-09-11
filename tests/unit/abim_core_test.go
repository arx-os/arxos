package unit

import (
	"fmt"
	"testing"
	"time"

	"github.com/joelpate/arxos/internal/ascii/abim"
	"github.com/joelpate/arxos/internal/ascii/layers"
	"github.com/joelpate/arxos/pkg/models"
)

// TestABIMRenderer tests the core ABIM renderer functionality
func TestABIMRenderer(t *testing.T) {
	plan := createTestFloorPlanCore()
	
	t.Run("RendererCreation", func(t *testing.T) {
		renderer := abim.NewRenderer(80, 30)
		if renderer == nil {
			t.Fatal("Failed to create renderer")
		}
		
		// Test initial state
		layerNames := renderer.GetLayerNames()
		if len(layerNames) != 0 {
			t.Errorf("New renderer should have no layers, got %d", len(layerNames))
		}
	})
	
	t.Run("LayerManagement", func(t *testing.T) {
		renderer := abim.NewRenderer(80, 30)
		structureLayer := layers.NewStructureLayer(plan)
		
		// Test adding layer
		err := renderer.AddLayer("structure", structureLayer)
		if err != nil {
			t.Errorf("Failed to add layer: %v", err)
		}
		
		layerNames := renderer.GetLayerNames()
		if len(layerNames) != 1 {
			t.Errorf("Expected 1 layer, got %d", len(layerNames))
		}
		
		if layerNames[0] != "structure" {
			t.Errorf("Expected layer name 'structure', got %s", layerNames[0])
		}
		
		// Test removing layer
		err = renderer.RemoveLayer("structure")
		if err != nil {
			t.Errorf("Failed to remove layer: %v", err)
		}
		
		layerNames = renderer.GetLayerNames()
		if len(layerNames) != 0 {
			t.Errorf("Expected 0 layers after removal, got %d", len(layerNames))
		}
	})
	
	t.Run("LayerVisibility", func(t *testing.T) {
		renderer := abim.NewRenderer(80, 30)
		structureLayer := layers.NewStructureLayer(plan)
		renderer.AddLayer("structure", structureLayer)
		
		// Test hiding layer
		err := renderer.SetLayerVisible("structure", false)
		if err != nil {
			t.Errorf("Failed to hide layer: %v", err)
		}
		
		// Test showing layer
		err = renderer.SetLayerVisible("structure", true)
		if err != nil {
			t.Errorf("Failed to show layer: %v", err)
		}
		
		// Test invalid layer
		err = renderer.SetLayerVisible("nonexistent", true)
		if err == nil {
			t.Error("Expected error for non-existent layer")
		}
	})
	
	t.Run("DuplicateLayerNames", func(t *testing.T) {
		renderer := abim.NewRenderer(80, 30)
		structureLayer := layers.NewStructureLayer(plan)
		
		// Add first layer
		err := renderer.AddLayer("test", structureLayer)
		if err != nil {
			t.Errorf("Failed to add first layer: %v", err)
		}
		
		// Try to add layer with same name
		err = renderer.AddLayer("test", structureLayer)
		if err == nil {
			t.Error("Expected error when adding duplicate layer name")
		}
	})
}

// TestABIMViewport tests viewport functionality
func TestABIMViewport(t *testing.T) {
	t.Run("ViewportCreation", func(t *testing.T) {
		viewport := abim.Viewport{
			X: 10, Y: 20,
			Width: 80, Height: 30,
			Zoom: 1.5,
		}
		
		if viewport.X != 10 || viewport.Y != 20 {
			t.Error("Viewport position incorrect")
		}
		
		if viewport.Width != 80 || viewport.Height != 30 {
			t.Error("Viewport dimensions incorrect")
		}
		
		if viewport.Zoom != 1.5 {
			t.Error("Viewport zoom incorrect")
		}
	})
	
	t.Run("ZeroSizeViewport", func(t *testing.T) {
		renderer := abim.NewRenderer(0, 0)
		structureLayer := layers.NewStructureLayer(createTestFloorPlanCore())
		renderer.AddLayer("structure", structureLayer)
		
		output := renderer.Render()
		if len(output) != 0 {
			t.Error("Zero height viewport should produce empty output")
		}
	})
}

// TestABIMPerformanceEdgeCases tests performance with edge cases
func TestABIMPerformanceEdgeCases(t *testing.T) {
	t.Run("ManyLayers", func(t *testing.T) {
		renderer := abim.NewRenderer(50, 25)
		plan := createTestFloorPlanCore()
		
		// Add many layers
		for i := 0; i < 50; i++ {
			layerName := fmt.Sprintf("layer_%d", i)
			structureLayer := layers.NewStructureLayer(plan)
			err := renderer.AddLayer(layerName, structureLayer)
			if err != nil {
				t.Errorf("Failed to add layer %s: %v", layerName, err)
			}
		}
		
		// Test rendering performance
		start := time.Now()
		output := renderer.Render()
		duration := time.Since(start)
		
		if len(output) != 25 {
			t.Error("Incorrect output height with many layers")
		}
		
		// Should still render reasonably fast even with many layers
		if duration > 100*time.Millisecond {
			t.Errorf("Rendering too slow with many layers: %v", duration)
		}
	})
	
	t.Run("RapidUpdates", func(t *testing.T) {
		renderer := abim.NewRenderer(40, 20)
		plan := createTestFloorPlanCore()
		renderer.AddLayer("structure", layers.NewStructureLayer(plan))
		
		// Perform rapid updates
		start := time.Now()
		for i := 0; i < 100; i++ {
			renderer.Update(1.0/60.0) // 60 FPS
			output := renderer.Render()
			
			if len(output) != 20 {
				t.Errorf("Incorrect output height on iteration %d", i)
			}
		}
		duration := time.Since(start)
		
		// 100 frames should complete quickly
		if duration > 500*time.Millisecond {
			t.Errorf("Rapid updates too slow: %v", duration)
		}
	})
}

// TestABIMMemoryUsage tests memory behavior
func TestABIMMemoryUsage(t *testing.T) {
	t.Run("LayerAddRemoveCycle", func(t *testing.T) {
		renderer := abim.NewRenderer(80, 30)
		plan := createTestFloorPlanCore()
		
		// Add and remove layers repeatedly
		for cycle := 0; cycle < 100; cycle++ {
			layerName := fmt.Sprintf("cycle_%d", cycle)
			structureLayer := layers.NewStructureLayer(plan)
			
			err := renderer.AddLayer(layerName, structureLayer)
			if err != nil {
				t.Errorf("Failed to add layer in cycle %d: %v", cycle, err)
			}
			
			// Render once
			output := renderer.Render()
			if len(output) != 30 {
				t.Errorf("Incorrect output in cycle %d", cycle)
			}
			
			err = renderer.RemoveLayer(layerName)
			if err != nil {
				t.Errorf("Failed to remove layer in cycle %d: %v", cycle, err)
			}
		}
		
		// Should have no layers at the end
		layerNames := renderer.GetLayerNames()
		if len(layerNames) != 0 {
			t.Errorf("Expected 0 layers after cycles, got %d", len(layerNames))
		}
	})
}

// createTestFloorPlanCore creates a test floor plan for core tests
func createTestFloorPlanCore() *models.FloorPlan {
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
		},
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
	}
}