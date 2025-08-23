package integration

import (
	"fmt"
	"log"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/arxos/arxos/core/wall_composition/engine"
	"github.com/arxos/arxos/core/wall_composition/renderer"
	"github.com/arxos/arxos/core/wall_composition/types"
)

// ArxObjectAdapter bridges the existing ArxObject system with the wall composition engine
type ArxObjectAdapter struct {
	compositionEngine *engine.WallCompositionEngine
	svgRenderer       *renderer.SVGRenderer
}

// NewArxObjectAdapter creates a new adapter with default configuration
func NewArxObjectAdapter() *ArxObjectAdapter {
	// Create composition engine with default configuration
	compConfig := engine.DefaultCompositionConfig()
	compositionEngine := engine.NewWallCompositionEngine(compConfig)

	// Create SVG renderer with default configuration
	renderConfig := renderer.DefaultRenderConfig()
	svgRenderer := renderer.NewSVGRenderer(renderConfig)

	return &ArxObjectAdapter{
		compositionEngine: compositionEngine,
		svgRenderer:       svgRenderer,
	}
}

// NewArxObjectAdapterWithConfig creates a new adapter with custom configuration
func NewArxObjectAdapterWithConfig(compConfig engine.CompositionConfig, renderConfig renderer.RenderConfig) *ArxObjectAdapter {
	compositionEngine := engine.NewWallCompositionEngine(compConfig)
	svgRenderer := renderer.NewSVGRenderer(renderConfig)

	return &ArxObjectAdapter{
		compositionEngine: compositionEngine,
		svgRenderer:       svgRenderer,
	}
}

// ProcessArxObjects processes ArxObjects and returns composed wall structures
func (a *ArxObjectAdapter) ProcessArxObjects(arxObjects []*arxobject.ArxObject) ([]*types.WallStructure, error) {
	// Filter ArxObjects to only include walls
	wallObjects := a.filterWallArxObjects(arxObjects)

	if len(wallObjects) == 0 {
		log.Println("No wall ArxObjects found to process")
		return []*types.WallStructure{}, nil
	}

	log.Printf("Processing %d wall ArxObjects", len(wallObjects))

	// Convert ArxObjects to engine-compatible format
	engineObjects := a.convertToEngineObjects(wallObjects)

	// Process walls through composition engine
	wallStructures, err := a.compositionEngine.ComposeWalls(engineObjects)
	if err != nil {
		return nil, fmt.Errorf("failed to compose walls: %w", err)
	}

	log.Printf("Successfully created %d wall structures", len(wallStructures))

	return wallStructures, nil
}

// RenderWallStructures renders wall structures to SVG
func (a *ArxObjectAdapter) RenderWallStructures(structures []*types.WallStructure) (string, error) {
	svg, err := a.svgRenderer.RenderWallStructures(structures)
	if err != nil {
		return "", fmt.Errorf("failed to render wall structures: %w", err)
	}

	return svg, nil
}

// ProcessAndRender combines processing and rendering in one operation
func (a *ArxObjectAdapter) ProcessAndRender(arxObjects []*arxobject.ArxObject) (string, error) {
	// Process ArxObjects into wall structures
	wallStructures, err := a.ProcessArxObjects(arxObjects)
	if err != nil {
		return "", err
	}

	// Render wall structures to SVG
	svg, err := a.RenderWallStructures(wallStructures)
	if err != nil {
		return "", err
	}

	return svg, nil
}

// filterWallArxObjects filters ArxObjects to only include walls
func (a *ArxObjectAdapter) filterWallArxObjects(arxObjects []*arxobject.ArxObject) []*arxobject.ArxObject {
	var wallObjects []*arxobject.ArxObject

	for _, obj := range arxObjects {
		if a.isWallArxObject(obj) {
			wallObjects = append(wallObjects, obj)
		}
	}

	return wallObjects
}

// isWallArxObject determines if an ArxObject represents a wall
func (a *ArxObjectAdapter) isWallArxObject(obj *arxobject.ArxObject) bool {
	// Check if the object type is a structural wall
	if obj.Type == arxobject.StructuralWall {
		return true
	}

	// For now, only structural walls are considered walls
	// Additional wall types can be added here in the future
	return false
}

// hasLinearGeometry checks if ArxObject forms a linear structure
func (a *ArxObjectAdapter) hasLinearGeometry(obj *arxobject.ArxObject) bool {
	// For now, use a simple heuristic based on dimensions
	// A wall should be much longer than it is wide
	lengthRatio := float64(obj.Length) / float64(obj.Width)
	return lengthRatio > 3.0 && obj.Length > 1000 // At least 1mm long and 3:1 ratio
}

// convertToEngineObjects converts ArxObjects to engine-compatible format
func (a *ArxObjectAdapter) convertToEngineObjects(arxObjects []*arxobject.ArxObject) []engine.ArxObject {
	var engineObjects []engine.ArxObject

	for _, obj := range arxObjects {
		engineObj := a.convertSingleArxObject(obj)
		if engineObj != nil {
			engineObjects = append(engineObjects, engineObj)
		}
	}

	return engineObjects
}

// convertSingleArxObject converts a single ArxObject to engine format
func (a *ArxObjectAdapter) convertSingleArxObject(obj *arxobject.ArxObject) engine.ArxObject {
	// Extract coordinates from ArxObject position and dimensions
	coordinates := a.extractCoordinates(obj)
	
	// Create engine-compatible object
	engineObj := &engine.PlaceholderArxObject{
		ID:          fmt.Sprintf("%d", obj.ID), // Convert uint64 to string
		Type:        "wall", // Use string type for engine compatibility
		Confidence:  a.calculateConfidence(obj),
		Coordinates: coordinates,
	}

	return engineObj
}

// extractCoordinates extracts SmartPoint3D coordinates from ArxObject position and dimensions
func (a *ArxObjectAdapter) extractCoordinates(obj *arxobject.ArxObject) []types.SmartPoint3D {
	var coordinates []types.SmartPoint3D

	// Create start point from ArxObject position
	startPoint := types.NewSmartPoint3D(
		obj.X,
		obj.Y,
		obj.Z,
		types.Nanometer, // ArxObject uses nanometers
	)
	coordinates = append(coordinates, startPoint)

	// Create end point based on length and rotation
	// For now, assume wall extends along X-axis (can be enhanced later)
	endX := obj.X + obj.Length
	endY := obj.Y
	endZ := obj.Z
	
	endPoint := types.NewSmartPoint3D(
		endX,
		endY,
		endZ,
		types.Nanometer,
	)
	coordinates = append(coordinates, endPoint)

	return coordinates
}

// calculateConfidence calculates confidence score for an ArxObject
func (a *ArxObjectAdapter) calculateConfidence(obj *arxobject.ArxObject) float64 {
	// Use the ArxObject's built-in confidence score
	baseConfidence := float64(obj.Confidence.Overall)

	// Adjust confidence based on object type
	if a.isWallArxObject(obj) {
		baseConfidence += 0.1
	}

	// Ensure confidence is within valid range
	if baseConfidence > 1.0 {
		baseConfidence = 1.0
	}

	return baseConfidence
}

// GetCompositionStats returns statistics from the composition engine
func (a *ArxObjectAdapter) GetCompositionStats() engine.CompositionStats {
	return a.compositionEngine.GetCompositionStats()
}

// GetRenderStats returns statistics from the SVG renderer
func (a *ArxObjectAdapter) GetRenderStats() renderer.RenderStats {
	return a.svgRenderer.GetRenderStats()
}

// UpdateCompositionConfig updates the composition engine configuration
func (a *ArxObjectAdapter) UpdateCompositionConfig(config engine.CompositionConfig) {
	a.compositionEngine = engine.NewWallCompositionEngine(config)
}

// UpdateRenderConfig updates the SVG renderer configuration
func (a *ArxObjectAdapter) UpdateRenderConfig(config renderer.RenderConfig) {
	a.svgRenderer = renderer.NewSVGRenderer(config)
}

// ValidateWallStructure validates a wall structure and returns validation results
func (a *ArxObjectAdapter) ValidateWallStructure(structure *types.WallStructure) ValidationResult {
	result := ValidationResult{
		IsValid:     structure.Validation == types.ValidationComplete, // Valid when validation is complete
		Confidence:  float64(structure.Confidence), // Cast float32 to float64
		Issues:      []string{},
		Suggestions: []string{},
	}

	// Check for common issues
	if structure.Length < 100 {
		result.Issues = append(result.Issues, "Wall structure is too short (less than 100mm)")
		result.Suggestions = append(result.Suggestions, "Consider merging with adjacent walls or removing if noise")
	}

	if structure.Confidence < 0.6 {
		result.Issues = append(result.Issues, "Low confidence score")
		result.Suggestions = append(result.Suggestions, "Review source data quality and consider manual verification")
	}

	if len(structure.Segments) == 0 {
		result.Issues = append(result.Issues, "No wall segments found")
		result.Suggestions = append(result.Suggestions, "Check if wall detection is working correctly")
	}

	return result
}

// ValidationResult holds validation results for a wall structure
type ValidationResult struct {
	IsValid     bool
	Confidence  float64
	Issues      []string
	Suggestions []string
}
