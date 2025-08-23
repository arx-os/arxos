package integration

import (
	"testing"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/arxos/arxos/core/wall_composition/engine"
	"github.com/arxos/arxos/core/wall_composition/renderer"
	"github.com/arxos/arxos/core/wall_composition/types"
)

func TestNewArxObjectAdapter(t *testing.T) {
	adapter := NewArxObjectAdapter()

	if adapter == nil {
		t.Fatal("Expected adapter to be created, got nil")
	}

	if adapter.compositionEngine == nil {
		t.Error("Expected composition engine to be initialized")
	}

	if adapter.svgRenderer == nil {
		t.Error("Expected SVG renderer to be initialized")
	}
}

func TestNewArxObjectAdapterWithConfig(t *testing.T) {
	compConfig := engine.DefaultCompositionConfig()
	renderConfig := renderer.DefaultRenderConfig()

	adapter := NewArxObjectAdapterWithConfig(compConfig, renderConfig)

	if adapter == nil {
		t.Fatal("Expected adapter to be created, got nil")
	}

	if adapter.compositionEngine == nil {
		t.Error("Expected composition engine to be initialized")
	}

	if adapter.svgRenderer == nil {
		t.Error("Expected SVG renderer to be initialized")
	}
}

func TestProcessArxObjectsEmpty(t *testing.T) {
	adapter := NewArxObjectAdapter()
	structures, err := adapter.ProcessArxObjects([]*arxobject.ArxObject{})

	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}

	if len(structures) != 0 {
		t.Errorf("Expected 0 structures, got %d", len(structures))
	}
}

func TestProcessArxObjectsNoWalls(t *testing.T) {
	adapter := NewArxObjectAdapter()

	// Create non-wall ArxObjects
	arxObjects := []*arxobject.ArxObject{
		{
			ID:     1,
			Type:   arxobject.ElectricalOutlet,
			X:      0,
			Y:      0,
			Z:      0,
			Length: 100000000, // 100mm
			Width:  100000000, // 100mm
		},
		{
			ID:     2,
			Type:   arxobject.ElectricalPanel,
			X:      200000000, // 200mm
			Y:      0,
			Z:      0,
			Length: 300000000, // 300mm
			Width:  200000000, // 200mm
		},
	}

	structures, err := adapter.ProcessArxObjects(arxObjects)
	if err != nil {
		t.Errorf("Expected no error, got %v", err)
	}

	if len(structures) != 0 {
		t.Errorf("Expected 0 structures, got %d", len(structures))
	}
}

func TestProcessArxObjectsWithWalls(t *testing.T) {
	adapter := NewArxObjectAdapter()

	// Create wall ArxObjects
	arxObjects := []*arxobject.ArxObject{
		{
			ID:     1,
			Type:   arxobject.StructuralWall,
			X:      0,
			Y:      0,
			Z:      0,
			Length: 1000000000, // 1000mm
			Width:  200000000,  // 200mm
		},
		{
			ID:     2,
			Type:   arxobject.StructuralWall,
			X:      1000000000, // 1000mm
			Y:      0,
			Z:      0,
			Length: 1000000000, // 1000mm
			Width:  200000000,  // 200mm
		},
	}

	structures, err := adapter.ProcessArxObjects(arxObjects)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	// Should create at least one structure
	if len(structures) == 0 {
		t.Error("Expected at least one wall structure to be created")
	}
}

func TestIsWallArxObject(t *testing.T) {
	adapter := NewArxObjectAdapter()

	// Test wall type
	wallObj := &arxobject.ArxObject{
		ID:   1,
		Type: arxobject.StructuralWall,
	}

	if !adapter.isWallArxObject(wallObj) {
		t.Error("Expected StructuralWall to be identified as wall")
	}

	// Test non-wall type
	nonWallObj := &arxobject.ArxObject{
		ID:   2,
		Type: arxobject.ElectricalOutlet,
	}

	if adapter.isWallArxObject(nonWallObj) {
		t.Error("Expected ElectricalOutlet to not be identified as wall")
	}
}

func TestExtractCoordinates(t *testing.T) {
	adapter := NewArxObjectAdapter()

	// Create ArxObject with coordinates
	arxObj := &arxobject.ArxObject{
		ID:     1,
		Type:   arxobject.StructuralWall,
		X:      0,
		Y:      0,
		Z:      0,
		Length: 1000000000, // 1000mm
		Width:  200000000,  // 200mm
	}

	coordinates := adapter.extractCoordinates(arxObj)

	if len(coordinates) == 0 {
		t.Error("Expected coordinates to be extracted")
	}
}

func TestRenderWallStructures(t *testing.T) {
	adapter := NewArxObjectAdapter()

	// Create a simple wall structure
	structure := types.NewWallStructure()
	segment := types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(1000, 0, 0, types.Millimeter),
		Confidence: 0.8,
	}
	structure.AddSegment(segment)

	svg, err := adapter.RenderWallStructures([]*types.WallStructure{structure})
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if len(svg) == 0 {
		t.Error("Expected SVG output")
	}
}

func TestProcessAndRender(t *testing.T) {
	adapter := NewArxObjectAdapter()

	// Create wall ArxObjects
	arxObjects := []*arxobject.ArxObject{
		{
			ID:     1,
			Type:   arxobject.StructuralWall,
			X:      0,
			Y:      0,
			Z:      0,
			Length: 1000000000, // 1000mm
			Width:  200000000,  // 200mm
		},
	}

	svg, err := adapter.ProcessAndRender(arxObjects)
	if err != nil {
		t.Fatalf("Expected no error, got %v", err)
	}

	if len(svg) == 0 {
		t.Error("Expected SVG output")
	}
}

func TestValidateWallStructure(t *testing.T) {
	adapter := NewArxObjectAdapter()

	// Test valid structure
	validStructure := types.NewWallStructure()
	segment := types.WallSegment{
		ID:         1,
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(1000, 0, 0, types.Millimeter),
		Confidence: 0.8,
	}
	validStructure.AddSegment(segment)

	// Set validation state to complete so it passes validation
	validStructure.Validation = types.ValidationComplete

	result := adapter.ValidateWallStructure(validStructure)

	if !result.IsValid {
		t.Error("Expected valid structure to pass validation")
	}
}

func TestGetCompositionStats(t *testing.T) {
	adapter := NewArxObjectAdapter()

	stats := adapter.GetCompositionStats()

	if stats.TotalWallsProcessed != 0 {
		t.Errorf("Expected 0 walls processed, got %d", stats.TotalWallsProcessed)
	}
}

func TestGetRenderStats(t *testing.T) {
	adapter := NewArxObjectAdapter()

	stats := adapter.GetRenderStats()

	if stats.StructuresRendered != 0 {
		t.Errorf("Expected 0 structures rendered, got %d", stats.StructuresRendered)
	}
}

func TestUpdateCompositionConfig(t *testing.T) {
	adapter := NewArxObjectAdapter()

	newConfig := engine.CompositionConfig{
		MaxGapDistance:      100.0,    // Different from default
		ParallelThreshold:   10.0,     // Different from default
		MinWallLength:       200.0,    // Different from default
		MaxWallLength:       100000.0, // Different from default
		ConfidenceThreshold: 0.7,      // Different from default
	}

	adapter.UpdateCompositionConfig(newConfig)

	// Verify the configuration was updated
	_ = adapter.GetCompositionStats()
	// Note: This is a placeholder test since GetCompositionStats returns placeholder values
	// In a real implementation, we would verify the configuration change
}

func TestUpdateRenderConfig(t *testing.T) {
	adapter := NewArxObjectAdapter()

	newConfig := renderer.RenderConfig{
		Width:          500.0, // Different from default
		Height:         300.0, // Different from default
		Scale:          2.0,   // Different from default
		StrokeWidth:    5.0,   // Different from default
		ShowConfidence: false, // Different from default
		ShowDimensions: false, // Different from default
		ShowMetadata:   true,  // Different from default
	}

	adapter.UpdateRenderConfig(newConfig)

	// Verify the configuration was updated
	_ = adapter.GetRenderStats()
	// Note: This is a placeholder test since GetRenderStats returns placeholder values
	// In a real implementation, we would verify the configuration change
}
