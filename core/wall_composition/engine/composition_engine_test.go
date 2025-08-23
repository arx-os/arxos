package engine

import (
	"testing"

	"github.com/arxos/arxos/core/wall_composition/types"
)

func TestNewWallCompositionEngine(t *testing.T) {
	config := DefaultCompositionConfig()
	engine := NewWallCompositionEngine(config)

	if engine == nil {
		t.Fatal("Expected engine to be created, got nil")
	}

	if engine.config.MaxGapDistance != config.MaxGapDistance {
		t.Errorf("Expected MaxGapDistance %f, got %f", config.MaxGapDistance, engine.config.MaxGapDistance)
	}
}

func TestDefaultCompositionConfig(t *testing.T) {
	config := DefaultCompositionConfig()

	expectedGapDistance := 50.0
	if config.MaxGapDistance != expectedGapDistance {
		t.Errorf("Expected MaxGapDistance %f, got %f", expectedGapDistance, config.MaxGapDistance)
	}

	expectedParallelThreshold := 5.0
	if config.ParallelThreshold != expectedParallelThreshold {
		t.Errorf("Expected ParallelThreshold %f, got %f", expectedParallelThreshold, config.ParallelThreshold)
	}

	expectedConfidenceThreshold := 0.6
	if config.ConfidenceThreshold != expectedConfidenceThreshold {
		t.Errorf("Expected ConfidenceThreshold %f, got %f", expectedConfidenceThreshold, config.ConfidenceThreshold)
	}
}

func TestComposeWallsEmptyInput(t *testing.T) {
	engine := NewWallCompositionEngine(DefaultCompositionConfig())
	structures, err := engine.ComposeWalls([]ArxObject{})

	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}

	if len(structures) != 0 {
		t.Errorf("Expected 0 structures, got %d", len(structures))
	}
}

func TestComposeWallsSingleWall(t *testing.T) {
	engine := NewWallCompositionEngine(DefaultCompositionConfig())

	// Create a single wall object
	wall := &PlaceholderArxObject{
		ID:         "wall1",
		Type:       "wall",
		Confidence: 0.9,
		Coordinates: []types.SmartPoint3D{
			types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
			types.NewSmartPoint3D(1000, 0, 0, types.Millimeter),
		},
	}

	structures, err := engine.ComposeWalls([]ArxObject{wall})
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if len(structures) != 1 {
		t.Fatalf("Expected 1 structure, got %d", len(structures))
	}

	structure := structures[0]
	if len(structure.Segments) != 1 {
		t.Errorf("Expected 1 segment, got %d", len(structure.Segments))
	}
}

func TestDetectWallConnections(t *testing.T) {
	engine := NewWallCompositionEngine(DefaultCompositionConfig())

	wall1 := &PlaceholderArxObject{
		ID:         "wall1",
		Type:       "wall",
		Confidence: 0.9,
		Coordinates: []types.SmartPoint3D{
			types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
			types.NewSmartPoint3D(50, 0, 0, types.Millimeter), // 50mm wall
		},
	}

	wall2 := &PlaceholderArxObject{
		ID:         "wall2",
		Type:       "wall",
		Confidence: 0.9,
		Coordinates: []types.SmartPoint3D{
			types.NewSmartPoint3D(50, 0, 0, types.Millimeter), // Connected to wall1 at endpoint
			types.NewSmartPoint3D(50, 50, 0, types.Millimeter), // 50mm wall
		},
	}

	// Build the spatial index first
	engine.buildSpatialIndex([]ArxObject{wall1, wall2})

	// Now detect wall connections
	connections := engine.detectWallConnections([]ArxObject{wall1, wall2})

	if len(connections) == 0 {
		t.Error("Expected connections to be detected")
	}
}

func TestCalculateWallOrientation(t *testing.T) {
	engine := NewWallCompositionEngine(DefaultCompositionConfig())

	// Horizontal wall (0 degrees)
	endpoints := []types.SmartPoint3D{
		types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		types.NewSmartPoint3D(1000, 0, 0, types.Millimeter),
	}

	orientation := engine.calculateWallOrientation(endpoints)
	expectedOrientation := 0.0

	if abs(orientation-expectedOrientation) > 0.1 {
		t.Errorf("Expected orientation %f, got %f", expectedOrientation, orientation)
	}

	// Vertical wall (90 degrees)
	endpoints = []types.SmartPoint3D{
		types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		types.NewSmartPoint3D(0, 1000, 0, types.Millimeter),
	}

	orientation = engine.calculateWallOrientation(endpoints)
	expectedOrientation = 90.0

	if abs(orientation-expectedOrientation) > 0.1 {
		t.Errorf("Expected orientation %f, got %f", expectedOrientation, orientation)
	}
}

func TestAreWallsParallel(t *testing.T) {
	engine := NewWallCompositionEngine(DefaultCompositionConfig())

	// Test parallel walls
	angle1 := 0.0
	angle2 := 2.0 // Within 5 degree threshold

	if !engine.areWallsParallel(angle1, angle2) {
		t.Error("Expected walls to be considered parallel")
	}

	// Test non-parallel walls
	angle1 = 0.0
	angle2 = 10.0 // Outside 5 degree threshold

	if engine.areWallsParallel(angle1, angle2) {
		t.Error("Expected walls to not be considered parallel")
	}
}

func TestBuildWallGraph(t *testing.T) {
	engine := NewWallCompositionEngine(DefaultCompositionConfig())

	wall1 := &PlaceholderArxObject{ID: "wall1"}
	wall2 := &PlaceholderArxObject{ID: "wall2"}

	connections := []types.WallConnection{
		{
			Type:       types.ConnectionEndToEnd,
			Wall1ID:    1,
			Wall2ID:    2,
			Confidence: 0.8,
		},
	}

	graph := engine.buildWallGraph([]ArxObject{wall1, wall2}, connections)

	if len(graph) != 2 {
		t.Errorf("Expected 2 nodes in graph, got %d", len(graph))
	}
}

func TestGetCompositionStats(t *testing.T) {
	engine := NewWallCompositionEngine(DefaultCompositionConfig())

	stats := engine.GetCompositionStats()

	if stats.TotalWallsProcessed != 0 {
		t.Errorf("Expected 0 walls processed, got %d", stats.TotalWallsProcessed)
	}
}

// Helper function for math operations
func abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}
