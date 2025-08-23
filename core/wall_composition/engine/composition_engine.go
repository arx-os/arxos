package engine

import (
	"fmt"
	"math"

	"github.com/arxos/arxos/core/wall_composition/spatial"
	"github.com/arxos/arxos/core/wall_composition/types"
)

// WallCompositionEngine orchestrates the wall composition process
type WallCompositionEngine struct {
	spatialIndex *spatial.SpatialIndex
	config       CompositionConfig
}

// CompositionConfig holds configuration parameters for the composition engine
type CompositionConfig struct {
	MaxGapDistance      float64 // Maximum gap distance for wall connections (in mm)
	ParallelThreshold   float64 // Threshold for considering walls parallel (in degrees)
	MinWallLength       float64 // Minimum wall length to consider (in mm)
	MaxWallLength       float64 // Maximum wall length to consider (in mm)
	ConfidenceThreshold float64 // Minimum confidence threshold for composition
}

// DefaultCompositionConfig returns sensible default configuration values
func DefaultCompositionConfig() CompositionConfig {
	return CompositionConfig{
		MaxGapDistance:      50.0,    // 50mm gap tolerance
		ParallelThreshold:   5.0,     // 5 degrees tolerance for parallel walls
		MinWallLength:       100.0,   // 100mm minimum wall length
		MaxWallLength:       50000.0, // 50m maximum wall length
		ConfidenceThreshold: 0.6,     // 60% confidence threshold
	}
}

// NewWallCompositionEngine creates a new composition engine with the given configuration
func NewWallCompositionEngine(config CompositionConfig) *WallCompositionEngine {
	return &WallCompositionEngine{
		spatialIndex: spatial.NewSpatialIndex(),
		config:       config,
	}
}

// ComposeWalls processes a list of wall ArxObjects and returns composed wall structures
func (e *WallCompositionEngine) ComposeWalls(wallObjects []ArxObject) ([]*types.WallStructure, error) {
	if len(wallObjects) == 0 {
		return []*types.WallStructure{}, nil
	}

	// Build spatial index for efficient neighbor queries
	e.buildSpatialIndex(wallObjects)

	// Detect wall connections
	connections := e.detectWallConnections(wallObjects)

	// Group connected walls into structures
	wallStructures := e.buildWallStructures(wallObjects, connections)

	// Calculate confidence scores and validate structures
	e.calculateStructureConfidence(wallStructures)

	// Filter structures based on confidence threshold
	filteredStructures := e.filterByConfidence(wallStructures)

	return filteredStructures, nil
}

// buildSpatialIndex populates the spatial index with wall objects
func (e *WallCompositionEngine) buildSpatialIndex(wallObjects []ArxObject) {
	fmt.Printf("Debug: buildSpatialIndex called with %d wall objects\n", len(wallObjects))
	
	e.spatialIndex.Clear()
	fmt.Printf("Debug: Spatial index cleared\n")
	
	for _, obj := range wallObjects {
		fmt.Printf("Debug: Inserting object %s with %d coordinates\n", obj.GetID(), len(obj.GetCoordinates()))
		e.spatialIndex.Insert(obj)
	}
	
	fmt.Printf("Debug: Spatial index built for %d objects\n", len(wallObjects))
}

// detectWallConnections identifies potential connections between walls
func (e *WallCompositionEngine) detectWallConnections(wallObjects []ArxObject) []types.WallConnection {
	var connections []types.WallConnection

	fmt.Printf("Debug: detectWallConnections called with %d wall objects\n", len(wallObjects))

	for _, wall1 := range wallObjects {
		fmt.Printf("Debug: Processing wall1 ID: %s\n", wall1.GetID())
		
		// Query nearby walls for potential connections
		nearbyWalls := e.spatialIndex.QueryNearby(wall1, e.config.MaxGapDistance)
		fmt.Printf("Debug: Found %d nearby walls for wall1\n", len(nearbyWalls))

		for _, wall2 := range nearbyWalls {
			if wall1.GetID() == wall2.GetID() {
				continue // Skip self-connection
			}

			fmt.Printf("Debug: Analyzing connection between wall1 (%s) and wall2 (%s)\n", wall1.GetID(), wall2.GetID())
			
			connection := e.analyzeWallConnection(wall1, wall2)
			if connection != nil {
				fmt.Printf("Debug: Connection detected!\n")
				connections = append(connections, *connection)
			} else {
				fmt.Printf("Debug: No connection detected\n")
			}
		}
	}

	fmt.Printf("Debug: Total connections found: %d\n", len(connections))
	return connections
}

// analyzeWallConnection analyzes the connection between two walls
func (e *WallCompositionEngine) analyzeWallConnection(wall1, wall2 ArxObject) *types.WallConnection {
	// Extract wall endpoints and properties
	endpoints1 := e.extractWallEndpoints(wall1)
	endpoints2 := e.extractWallEndpoints(wall2)

	if len(endpoints1) < 2 || len(endpoints2) < 2 {
		return nil
	}

	// Check for gap-based connections
	gapConnection := e.detectGapConnection(endpoints1, endpoints2)
	if gapConnection != nil {
		return gapConnection
	}

	// Check for alignment/parallelism connections
	alignmentConnection := e.detectAlignmentConnection(wall1, wall2, endpoints1, endpoints2)
	if alignmentConnection != nil {
		return alignmentConnection
	}

	return nil
}

// extractWallEndpoints extracts the start and end points of a wall
func (e *WallCompositionEngine) extractWallEndpoints(wall ArxObject) []types.SmartPoint3D {
	// Extract coordinates from the ArxObject
	coordinates := wall.GetCoordinates()
	
	// Ensure we have at least 2 points (start and end)
	if len(coordinates) < 2 {
		return []types.SmartPoint3D{
			types.NewSmartPoint3D(0, 0, 0, types.Nanometer),
			types.NewSmartPoint3D(1000, 0, 0, types.Nanometer), // Fallback 1mm wall
		}
	}
	
	return coordinates
}

// detectGapConnection detects if two walls are connected by a small gap
func (e *WallCompositionEngine) detectGapConnection(endpoints1, endpoints2 []types.SmartPoint3D) *types.WallConnection {
	// Calculate minimum distance between any two endpoints
	minDistance := math.MaxFloat64
	var closestPoint1 types.SmartPoint3D

	for _, p1 := range endpoints1 {
		for _, p2 := range endpoints2 {
			distance := p1.DistanceTo(p2)
			if distance < minDistance {
				minDistance = distance
				closestPoint1 = p1
			}
		}
	}

	// Check if the gap is within tolerance
	if minDistance <= e.config.MaxGapDistance {
		return &types.WallConnection{
			Type:            types.ConnectionEndToEnd,
			Wall1ID:         1, // Placeholder ID
			Wall2ID:         2, // Placeholder ID
			ConnectionPoint: closestPoint1,
			Confidence:      0.8, // High confidence for gap connections
		}
	}

	return nil
}

// detectAlignmentConnection detects if two walls are aligned or parallel
func (e *WallCompositionEngine) detectAlignmentConnection(wall1, wall2 ArxObject, endpoints1, endpoints2 []types.SmartPoint3D) *types.WallConnection {
	// Calculate wall orientations
	orientation1 := e.calculateWallOrientation(endpoints1)
	orientation2 := e.calculateWallOrientation(endpoints2)

	// Check if walls are parallel
	if e.areWallsParallel(orientation1, orientation2) {
		// Check for overlap or close proximity
		if e.checkWallOverlap(endpoints1, endpoints2) {
			return &types.WallConnection{
				Type:            types.ConnectionAdjacent,
				Wall1ID:         1,             // Placeholder ID
				Wall2ID:         2,             // Placeholder ID
				ConnectionPoint: endpoints1[0], // Use first endpoint as reference
				Confidence:      0.7,           // Medium confidence for alignment
			}
		}
	}

	return nil
}

// calculateWallOrientation calculates the orientation angle of a wall
func (e *WallCompositionEngine) calculateWallOrientation(endpoints []types.SmartPoint3D) float64 {
	if len(endpoints) < 2 {
		return 0.0
	}

	start := endpoints[0]
	end := endpoints[1]

	dx := end.X - start.X
	dy := end.Y - start.Y

	return math.Atan2(float64(dy), float64(dx)) * 180.0 / math.Pi
}

// areWallsParallel checks if two walls are parallel within the threshold
func (e *WallCompositionEngine) areWallsParallel(angle1, angle2 float64) bool {
	diff := math.Abs(angle1 - angle2)

	// Normalize to handle angles around 0/360 degrees
	if diff > 180 {
		diff = 360 - diff
	}

	return diff <= e.config.ParallelThreshold
}

// checkWallOverlap checks if two walls overlap or are very close
func (e *WallCompositionEngine) checkWallOverlap(endpoints1, endpoints2 []types.SmartPoint3D) bool {
	// Simple distance check for now
	// In a real implementation, this would check for actual overlap
	for _, p1 := range endpoints1 {
		for _, p2 := range endpoints2 {
			if p1.DistanceTo(p2) <= e.config.MaxGapDistance {
				return true
			}
		}
	}
	return false
}

// buildWallStructures groups connected walls into wall structures
func (e *WallCompositionEngine) buildWallStructures(wallObjects []ArxObject, connections []types.WallConnection) []*types.WallStructure {
	// Create a graph representation of wall connections
	wallGraph := e.buildWallGraph(wallObjects, connections)

	// Find connected components (groups of connected walls)
	connectedGroups := e.findConnectedComponents(wallGraph)

	// Build wall structures from connected groups
	var wallStructures []*types.WallStructure
	for _, group := range connectedGroups {
		structure := e.createWallStructure(group, wallObjects)
		if structure != nil {
			wallStructures = append(wallStructures, structure)
		}
	}

	return wallStructures
}

// buildWallGraph creates a graph representation of wall connections
func (e *WallCompositionEngine) buildWallGraph(wallObjects []ArxObject, connections []types.WallConnection) map[string][]string {
	graph := make(map[string][]string)

	// Initialize graph with all walls
	for _, wall := range wallObjects {
		graph[wall.GetID()] = []string{}
	}

	// Add connections
	for _, conn := range connections {
		wall1ID := fmt.Sprintf("%d", conn.Wall1ID)
		wall2ID := fmt.Sprintf("%d", conn.Wall2ID)

		if neighbors, exists := graph[wall1ID]; exists {
			graph[wall1ID] = append(neighbors, wall2ID)
		}
		if neighbors, exists := graph[wall2ID]; exists {
			graph[wall2ID] = append(neighbors, wall1ID)
		}
	}

	return graph
}

// findConnectedComponents finds groups of connected walls using DFS
func (e *WallCompositionEngine) findConnectedComponents(graph map[string][]string) [][]string {
	visited := make(map[string]bool)
	var components [][]string

	for wallID := range graph {
		if !visited[wallID] {
			component := e.dfsComponent(graph, wallID, visited)
			if len(component) > 0 {
				components = append(components, component)
			}
		}
	}

	return components
}

// dfsComponent performs depth-first search to find a connected component
func (e *WallCompositionEngine) dfsComponent(graph map[string][]string, start string, visited map[string]bool) []string {
	var component []string
	stack := []string{start}
	visited[start] = true

	for len(stack) > 0 {
		current := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		component = append(component, current)

		for _, neighbor := range graph[current] {
			if !visited[neighbor] {
				visited[neighbor] = true
				stack = append(stack, neighbor)
			}
		}
	}

	return component
}

// createWallStructure creates a wall structure from a group of connected walls
func (e *WallCompositionEngine) createWallStructure(wallGroup []string, wallObjects []ArxObject) *types.WallStructure {
	if len(wallGroup) == 0 {
		return nil
	}

	// Find the actual wall objects for this group
	var groupWalls []ArxObject
	for _, wallID := range wallGroup {
		for _, wall := range wallObjects {
			if wall.GetID() == wallID {
				groupWalls = append(groupWalls, wall)
				break
			}
		}
	}

	if len(groupWalls) == 0 {
		return nil
	}

	// Create wall structure
	structure := types.NewWallStructure()

	// Add wall segments
	for _, wall := range groupWalls {
		segment := e.createWallSegment(wall)
		if segment != nil {
			structure.AddSegment(*segment)
		}
	}

	// Set metadata
	structure.Metadata.BuildingID = fmt.Sprintf("Wall Structure %d", len(wallGroup))
	structure.Metadata.Notes = fmt.Sprintf("Composed of %d connected walls", len(wallGroup))

	return structure
}

// createWallSegment creates a wall segment from an ArxObject
func (e *WallCompositionEngine) createWallSegment(wall ArxObject) *types.WallSegment {
	// This is a placeholder implementation
	// In the real system, this would extract actual wall properties
	return &types.WallSegment{
		ID:         1, // Placeholder ID
		StartPoint: types.NewSmartPoint3D(0, 0, 0, types.Millimeter),
		EndPoint:   types.NewSmartPoint3D(1000, 0, 0, types.Millimeter),
		Thickness:  200,        // 200mm default thickness
		Material:   "Concrete", // Default material
		FireRating: "2 Hour",   // Default fire rating
		Confidence: 0.8,        // Default confidence
	}
}

// calculateStructureConfidence calculates and updates confidence scores for wall structures
func (e *WallCompositionEngine) calculateStructureConfidence(structures []*types.WallStructure) {
	for _, structure := range structures {
		// Calculate overall confidence based on segment confidences
		totalConfidence := float32(0.0)
		validSegments := 0

		for _, segment := range structure.Segments {
			if segment.Confidence > 0 {
				totalConfidence += segment.Confidence
				validSegments++
			}
		}

		if validSegments > 0 {
			structure.Confidence = totalConfidence / float32(validSegments)
		}

		// Validate structure properties
		e.validateStructure(structure)
	}
}

// validateStructure validates a wall structure and updates its validation state
func (e *WallCompositionEngine) validateStructure(structure *types.WallStructure) {
	// Check if structure has valid segments
	if len(structure.Segments) == 0 {
		structure.Validation = types.ValidationPending
		return
	}

	// Check if structure meets minimum requirements
	if structure.Length < e.config.MinWallLength {
		structure.Validation = types.ValidationPending
		return
	}

	if structure.Length > e.config.MaxWallLength {
		structure.Validation = types.ValidationPending
		return
	}

	// Check confidence threshold
	if structure.Confidence < float32(e.config.ConfidenceThreshold) {
		structure.Validation = types.ValidationPending
		return
	}

	structure.Validation = types.ValidationPending
}

// filterByConfidence filters wall structures based on confidence threshold
func (e *WallCompositionEngine) filterByConfidence(structures []*types.WallStructure) []*types.WallStructure {
	var filtered []*types.WallStructure

	for _, structure := range structures {
		if structure.Confidence >= float32(e.config.ConfidenceThreshold) {
			filtered = append(filtered, structure)
		}
	}

	return filtered
}

// GetCompositionStats returns statistics about the composition process
func (e *WallCompositionEngine) GetCompositionStats() CompositionStats {
	return CompositionStats{
		TotalWallsProcessed: 0,   // Placeholder
		StructuresCreated:   0,   // Placeholder
		AverageConfidence:   0.0, // Placeholder
	}
}

// CompositionStats holds statistics about the composition process
type CompositionStats struct {
	TotalWallsProcessed int
	StructuresCreated   int
	AverageConfidence   float64
}

// ArxObject is a placeholder interface for the actual ArxObject type
// This will be replaced with the real ArxObject interface when available
type ArxObject interface {
	GetID() string
	GetType() string
	GetConfidence() float64
	GetCoordinates() []types.SmartPoint3D
}

// Placeholder ArxObject implementation for testing
type PlaceholderArxObject struct {
	ID          string
	Type        string
	Confidence  float64
	Coordinates []types.SmartPoint3D
}

func (a PlaceholderArxObject) GetID() string                        { return a.ID }
func (a PlaceholderArxObject) GetType() string                      { return a.Type }
func (a PlaceholderArxObject) GetConfidence() float64               { return a.Confidence }
func (a PlaceholderArxObject) GetCoordinates() []types.SmartPoint3D { return a.Coordinates }
