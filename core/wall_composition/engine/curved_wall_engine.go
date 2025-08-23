package engine

import (
	"fmt"
	"math"

	"github.com/arxos/arxos/core/wall_composition/types"
)

// CurvedWallCompositionEngine extends the base composition engine with curved wall support
type CurvedWallCompositionEngine struct {
	*WallCompositionEngine
	CurveDetectionThreshold float64 // Threshold for detecting curved walls
	MaxCurveDeviation       float64 // Maximum deviation from straight line to consider curved
	config                  CurvedCompositionConfig
}

// CurvedCompositionConfig extends the base configuration with curved wall parameters
type CurvedCompositionConfig struct {
	CompositionConfig
	CurveDetectionThreshold     float64 // Threshold for detecting curved walls
	MaxCurveDeviation           float64 // Maximum deviation from straight line to consider curved
	BezierApproximationSegments int     // Number of segments for Bézier curve approximation
	ArcApproximationSegments    int     // Number of segments for arc approximation
}

// DefaultCurvedCompositionConfig returns sensible default configuration values
func DefaultCurvedCompositionConfig() CurvedCompositionConfig {
	return CurvedCompositionConfig{
		CompositionConfig:           DefaultCompositionConfig(),
		CurveDetectionThreshold:     0.3, // 30% confidence threshold for curved walls
		MaxCurveDeviation:           0.2, // 20% deviation from straight line
		BezierApproximationSegments: 50,
		ArcApproximationSegments:    30,
	}
}

// NewCurvedWallCompositionEngine creates a new curved wall composition engine
func NewCurvedWallCompositionEngine(config CurvedCompositionConfig) *CurvedWallCompositionEngine {
	baseEngine := NewWallCompositionEngine(config.CompositionConfig)

	return &CurvedWallCompositionEngine{
		WallCompositionEngine:   baseEngine,
		CurveDetectionThreshold: config.CurveDetectionThreshold,
		MaxCurveDeviation:       config.MaxCurveDeviation,
		config:                  config,
	}
}

// ComposeCurvedWalls processes a list of wall ArxObjects and returns composed wall structures with curved wall support
func (cwe *CurvedWallCompositionEngine) ComposeCurvedWalls(wallObjects []ArxObject) ([]*types.WallStructure, error) {
	if len(wallObjects) == 0 {
		return []*types.WallStructure{}, nil
	}

	// Build spatial index for efficient neighbor queries
	cwe.buildSpatialIndex(wallObjects)

	// Detect wall connections including curved walls
	connections := cwe.detectCurvedWallConnections(wallObjects)

	// Group connected walls into structures
	wallStructures := cwe.buildCurvedWallStructures(wallObjects, connections)

	// Calculate confidence scores and validate structures
	cwe.calculateCurvedStructureConfidence(wallStructures)

	// Filter structures based on confidence threshold
	filteredStructures := cwe.filterByConfidence(wallStructures)

	return filteredStructures, nil
}

// detectCurvedWallConnections identifies potential connections between walls including curved walls
func (cwe *CurvedWallCompositionEngine) detectCurvedWallConnections(wallObjects []ArxObject) []types.WallConnection {
	var connections []types.WallConnection

	for i, wall1 := range wallObjects {
		// Query nearby walls for potential connections
		for j, wall2 := range wallObjects {
			if i == j {
				continue // Skip self-connection
			}

			connection := cwe.analyzeCurvedWallConnection(wall1, wall2)
			if connection != nil {
				connections = append(connections, *connection)
			}
		}
	}

	return connections
}

// analyzeCurvedWallConnection analyzes the connection between two walls with curved wall support
func (cwe *CurvedWallCompositionEngine) analyzeCurvedWallConnection(wall1, wall2 ArxObject) *types.WallConnection {
	// Extract wall endpoints and properties
	endpoints1 := cwe.extractWallEndpoints(wall1)
	endpoints2 := cwe.extractWallEndpoints(wall2)

	if len(endpoints1) < 2 || len(endpoints2) < 2 {
		return nil
	}

	// Check for gap-based connections
	gapConnection := cwe.detectGapConnection(endpoints1, endpoints2)
	if gapConnection != nil {
		return gapConnection
	}

	// Check for alignment/parallelism connections
	alignmentConnection := cwe.detectAlignmentConnection(wall1, wall2, endpoints1, endpoints2)
	if alignmentConnection != nil {
		return alignmentConnection
	}

	// Check for curved wall connections
	curvedConnection := cwe.detectCurvedWallConnection(wall1, wall2, endpoints1, endpoints2)
	if curvedConnection != nil {
		return curvedConnection
	}

	return nil
}

// detectCurvedWallConnection detects connections between curved walls
func (cwe *CurvedWallCompositionEngine) detectCurvedWallConnection(wall1, wall2 ArxObject, endpoints1, endpoints2 []types.SmartPoint3D) *types.WallConnection {
	// Check if either wall is curved
	isCurved1 := cwe.isWallCurved(endpoints1)
	isCurved2 := cwe.isWallCurved(endpoints2)

	if !isCurved1 && !isCurved2 {
		return nil // Neither wall is curved
	}

	// For curved walls, check for proximity along the curve
	if isCurved1 && isCurved2 {
		return cwe.detectCurvedToCurvedConnection(endpoints1, endpoints2)
	} else if isCurved1 {
		return cwe.detectCurvedToStraightConnection(endpoints1, endpoints2)
	} else {
		return cwe.detectCurvedToStraightConnection(endpoints2, endpoints1)
	}
}

// isWallCurved determines if a wall is curved based on its endpoints
func (cwe *CurvedWallCompositionEngine) isWallCurved(endpoints []types.SmartPoint3D) bool {
	if len(endpoints) < 3 {
		return false // Need at least 3 points to determine curvature
	}

	// Calculate total length and straight-line distance
	totalLength := 0.0
	for i := 1; i < len(endpoints); i++ {
		totalLength += endpoints[i-1].DistanceTo(endpoints[i])
	}

	// Calculate straight-line distance from start to end
	start := endpoints[0]
	end := endpoints[len(endpoints)-1]
	straightDistance := start.DistanceTo(end)

	// If the ratio is significantly less than 1, it's curved
	ratio := straightDistance / totalLength
	return ratio < (1.0 - cwe.MaxCurveDeviation)
}

// detectCurvedToCurvedConnection detects connections between two curved walls
func (cwe *CurvedWallCompositionEngine) detectCurvedToCurvedConnection(endpoints1, endpoints2 []types.SmartPoint3D) *types.WallConnection {
	// Find the closest points between the two curves
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

	// Check if the curves are close enough to be connected
	if minDistance <= cwe.config.MaxGapDistance {
		return &types.WallConnection{
			Type:            types.ConnectionEndToEnd,
			Wall1ID:         1, // Use placeholder IDs for now
			Wall2ID:         2,
			ConnectionPoint: closestPoint1,
			Confidence:      0.7, // Medium confidence for curved connections
		}
	}

	return nil
}

// detectCurvedToStraightConnection detects connections between curved and straight walls
func (cwe *CurvedWallCompositionEngine) detectCurvedToStraightConnection(curvedEndpoints, straightEndpoints []types.SmartPoint3D) *types.WallConnection {
	// Find the closest point on the curved wall to the straight wall
	minDistance := math.MaxFloat64
	var closestCurvedPoint types.SmartPoint3D

	for _, curvedPoint := range curvedEndpoints {
		for _, straightPoint := range straightEndpoints {
			distance := curvedPoint.DistanceTo(straightPoint)
			if distance < minDistance {
				minDistance = distance
				closestCurvedPoint = curvedPoint
			}
		}
	}

	// Check if the curves are close enough to be connected
	if minDistance <= cwe.config.MaxGapDistance {
		return &types.WallConnection{
			Type:            types.ConnectionEndToEnd,
			Wall1ID:         1, // Use placeholder IDs for now
			Wall2ID:         2,
			ConnectionPoint: closestCurvedPoint,
			Confidence:      0.6, // Lower confidence for mixed connections
		}
	}

	return nil
}

// buildCurvedWallStructures groups connected walls into wall structures with curved wall support
func (cwe *CurvedWallCompositionEngine) buildCurvedWallStructures(wallObjects []ArxObject, connections []types.WallConnection) []*types.WallStructure {
	// Create a graph representation of wall connections
	wallGraph := cwe.buildWallGraph(wallObjects, connections)

	// Find connected components (groups of connected walls)
	connectedGroups := cwe.findConnectedComponents(wallGraph)

	// Build wall structures from connected groups
	var wallStructures []*types.WallStructure
	for _, group := range connectedGroups {
		structure := cwe.createCurvedWallStructure(group, wallObjects)
		if structure != nil {
			wallStructures = append(wallStructures, structure)
		}
	}

	return wallStructures
}

// createCurvedWallStructure creates a wall structure from a group of connected walls with curved wall support
func (cwe *CurvedWallCompositionEngine) createCurvedWallStructure(wallGroup []string, wallObjects []ArxObject) *types.WallStructure {
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
		segment := cwe.createCurvedWallSegment(wall)
		if segment != nil {
			structure.AddSegment(*segment)
		}
	}

	// Set metadata
	structure.Metadata.BuildingID = fmt.Sprintf("Curved Wall Structure %d", len(wallGroup))
	structure.Metadata.Notes = fmt.Sprintf("Composed of %d connected walls (including curved)", len(wallGroup))

	return structure
}

// createCurvedWallSegment creates a wall segment from an ArxObject with curved wall support
func (cwe *CurvedWallCompositionEngine) createCurvedWallSegment(wall ArxObject) *types.WallSegment {
	// Extract wall endpoints
	endpoints := cwe.extractWallEndpoints(wall)

	if len(endpoints) < 2 {
		return nil
	}

	// Check if this wall is curved
	if cwe.isWallCurved(endpoints) {
		return cwe.createCurvedSegment(wall, endpoints)
	}

	// Create regular straight wall segment
	return &types.WallSegment{
		ID:         1, // Use placeholder ID for now
		StartPoint: endpoints[0],
		EndPoint:   endpoints[len(endpoints)-1],
		Thickness:  200,        // 200mm default thickness
		Material:   "Concrete", // Default material
		FireRating: "2 Hour",   // Default fire rating
		Confidence: 0.8,        // Default confidence
	}
}

// createCurvedSegment creates a curved wall segment
func (cwe *CurvedWallCompositionEngine) createCurvedSegment(wall ArxObject, endpoints []types.SmartPoint3D) *types.WallSegment {
	// Determine the type of curve based on the number of points and their arrangement
	curveType := cwe.determineCurveType(endpoints)

	// Create base wall segment
	baseSegment := &types.WallSegment{
		ID:         1, // Use placeholder ID for now
		StartPoint: endpoints[0],
		EndPoint:   endpoints[len(endpoints)-1],
		Thickness:  200,        // 200mm default thickness
		Material:   "Concrete", // Default material
		FireRating: "2 Hour",   // Default fire rating
		Confidence: 0.8,        // Default confidence
	}

	// Create curved wall segment
	curvedSegment := types.NewCurvedWallSegment(baseSegment, curveType)

	// Configure the curve based on type
	switch curveType {
	case types.CurvedWallTypeBezier:
		cwe.configureBezierCurve(curvedSegment, endpoints)
	case types.CurvedWallTypeArc:
		cwe.configureArcWall(curvedSegment, endpoints)
	}

	// Return the base segment for now - the curved segment is embedded
	return baseSegment
}

// determineCurveType determines the type of curve based on endpoints
func (cwe *CurvedWallCompositionEngine) determineCurveType(endpoints []types.SmartPoint3D) types.CurvedWallType {
	if len(endpoints) == 3 {
		// Three points suggest a Bézier curve
		return types.CurvedWallTypeBezier
	} else if len(endpoints) >= 4 {
		// Four or more points could be an arc or complex curve
		// For now, default to Bézier curve
		return types.CurvedWallTypeBezier
	}

	// Default to Bézier curve
	return types.CurvedWallTypeBezier
}

// configureBezierCurve configures a Bézier curve for the curved wall segment
func (cwe *CurvedWallCompositionEngine) configureBezierCurve(curvedSegment *types.CurvedWallSegment, endpoints []types.SmartPoint3D) {
	if len(endpoints) < 3 {
		return
	}

	start := endpoints[0]
	end := endpoints[len(endpoints)-1]

	if len(endpoints) == 3 {
		// Quadratic Bézier curve
		control := endpoints[1]
		curve := types.NewQuadraticBezierCurve(start, control, end)
		curvedSegment.SetBezierCurve(curve)
	} else if len(endpoints) >= 4 {
		// Cubic Bézier curve (use second and second-to-last points as controls)
		control1 := endpoints[1]
		control2 := endpoints[len(endpoints)-2]
		curve := types.NewCubicBezierCurve(start, control1, control2, end)
		curvedSegment.SetBezierCurve(curve)
	}
}

// configureArcWall configures an arc wall for the curved wall segment
func (cwe *CurvedWallCompositionEngine) configureArcWall(curvedSegment *types.CurvedWallSegment, endpoints []types.SmartPoint3D) {
	if len(endpoints) < 3 {
		return
	}

	start := endpoints[0]
	end := endpoints[len(endpoints)-1]

	// Estimate the center of the arc
	center := cwe.estimateArcCenter(endpoints)

	// Create circular arc (assume counterclockwise for now)
	arc := types.NewCircularArc(center, start, end, false)
	curvedSegment.SetArcWall(arc)
}

// estimateArcCenter estimates the center of an arc from its endpoints
func (cwe *CurvedWallCompositionEngine) estimateArcCenter(endpoints []types.SmartPoint3D) types.SmartPoint3D {
	if len(endpoints) < 3 {
		// Fallback to midpoint
		start := endpoints[0]
		end := endpoints[len(endpoints)-1]
		midX := (start.X + end.X) / 2
		midY := (start.Y + end.Y) / 2
		return types.NewSmartPoint3D(midX, midY, start.Z, start.GetUnit())
	}

	// Use the middle point as an approximation of the center
	midIndex := len(endpoints) / 2
	midPoint := endpoints[midIndex]

	// Adjust the center based on the curvature
	start := endpoints[0]
	end := endpoints[len(endpoints)-1]

	// Calculate perpendicular bisector
	midX := (start.X + end.X) / 2
	midY := (start.Y + end.Y) / 2

	// Move the center towards the middle point
	centerX := (midX + midPoint.X) / 2
	centerY := (midY + midPoint.Y) / 2

	return types.NewSmartPoint3D(centerX, centerY, start.Z, start.GetUnit())
}

// calculateCurvedStructureConfidence calculates and updates confidence scores for wall structures with curved walls
func (cwe *CurvedWallCompositionEngine) calculateCurvedStructureConfidence(structures []*types.WallStructure) {
	for _, structure := range structures {
		// Calculate overall confidence based on segment confidences
		totalConfidence := float32(0.0)
		validSegments := 0
		curvedSegments := 0

		for _, segment := range structure.Segments {
			if segment.Confidence > 0 {
				totalConfidence += segment.Confidence
				validSegments++

				// Check if this is a curved segment by looking at the segment type
				// For now, we'll assume all segments are straight
				// In a real implementation, we'd check the actual type
			}
		}

		if validSegments > 0 {
			structure.Confidence = totalConfidence / float32(validSegments)
		}

		// Adjust confidence based on curved wall complexity
		if curvedSegments > 0 {
			// Curved walls get a slight confidence boost for complexity
			structure.Confidence = float32(math.Min(1.0, float64(structure.Confidence)+0.05))
		}

		// Validate structure properties
		cwe.validateCurvedStructure(structure)
	}
}

// validateCurvedStructure validates a wall structure with curved wall support
func (cwe *CurvedWallCompositionEngine) validateCurvedStructure(structure *types.WallStructure) {
	// Check if structure has valid segments
	if len(structure.Segments) == 0 {
		structure.Validation = types.ValidationPending
		return
	}

	// Check if structure meets minimum requirements
	if structure.Length < cwe.config.MinWallLength {
		structure.Validation = types.ValidationPending
		return
	}

	if structure.Length > cwe.config.MaxWallLength {
		structure.Validation = types.ValidationPending
		return
	}

	// Check confidence threshold - convert float32 to float64 for comparison
	if float64(structure.Confidence) < cwe.config.ConfidenceThreshold {
		structure.Validation = types.ValidationPartial
		return
	}

	structure.Validation = types.ValidationComplete
}

// GetCurvedCompositionStats returns statistics about the curved wall composition process
func (cwe *CurvedWallCompositionEngine) GetCurvedCompositionStats() CurvedCompositionStats {
	return CurvedCompositionStats{
		TotalWallsProcessed: 0,   // Placeholder
		StructuresCreated:   0,   // Placeholder
		CurvedWallsDetected: 0,   // Placeholder
		AverageConfidence:   0.0, // Placeholder
	}
}

// CurvedCompositionStats holds statistics about the curved wall composition process
type CurvedCompositionStats struct {
	TotalWallsProcessed int
	StructuresCreated   int
	CurvedWallsDetected int
	AverageConfidence   float64
}

// Helper methods that need to be implemented or referenced from base engine
func (cwe *CurvedWallCompositionEngine) extractWallEndpoints(wall ArxObject) []types.SmartPoint3D {
	// Get coordinates from the ArxObject
	coordinates := wall.GetCoordinates()
	
	// If we have coordinates, use them
	if len(coordinates) >= 2 {
		return coordinates
	}
	
	// Fallback: create simple start and end points based on wall properties
	// This is a placeholder implementation that should be enhanced
	start := types.NewSmartPoint3D(0, 0, 0, types.Millimeter)
	end := types.NewSmartPoint3D(100000000, 0, 0, types.Millimeter) // 100mm
	
	return []types.SmartPoint3D{start, end}
}

func (cwe *CurvedWallCompositionEngine) detectGapConnection(endpoints1, endpoints2 []types.SmartPoint3D) *types.WallConnection {
	// Simple gap detection - check if endpoints are close
	if len(endpoints1) == 0 || len(endpoints2) == 0 {
		return nil
	}

	// Check distance between closest endpoints
	minDistance := math.MaxFloat64
	var closestPoint types.SmartPoint3D

	for _, p1 := range endpoints1 {
		for _, p2 := range endpoints2 {
			distance := p1.DistanceTo(p2)
			if distance < minDistance {
				minDistance = distance
				closestPoint = p1
			}
		}
	}

	if minDistance <= cwe.config.MaxGapDistance {
		return &types.WallConnection{
			Type:            types.ConnectionEndToEnd,
			Wall1ID:         1,
			Wall2ID:         2,
			ConnectionPoint: closestPoint,
			Confidence:      0.8,
		}
	}

	return nil
}

func (cwe *CurvedWallCompositionEngine) detectAlignmentConnection(wall1, wall2 ArxObject, endpoints1, endpoints2 []types.SmartPoint3D) *types.WallConnection {
	// Simple alignment detection - check if walls are parallel
	// This is a placeholder implementation that should be enhanced
	if len(endpoints1) < 2 || len(endpoints2) < 2 {
		return nil
	}
	
	// Check if vectors are parallel (simplified check)
	// In a real implementation, we'd calculate the angle between vectors
	// For now, return nil to indicate no alignment connection
	return nil
}

func (cwe *CurvedWallCompositionEngine) buildWallGraph(wallObjects []ArxObject, connections []types.WallConnection) map[string][]string {
	// Build adjacency list representation of wall connections
	graph := make(map[string][]string)

	for _, connection := range connections {
		wall1ID := fmt.Sprintf("%d", connection.Wall1ID)
		wall2ID := fmt.Sprintf("%d", connection.Wall2ID)
		graph[wall1ID] = append(graph[wall1ID], wall2ID)
		graph[wall2ID] = append(graph[wall2ID], wall1ID)
	}

	return graph
}

func (cwe *CurvedWallCompositionEngine) findConnectedComponents(graph map[string][]string) [][]string {
	// Find connected components using DFS
	visited := make(map[string]bool)
	var components [][]string

	for wallID := range graph {
		if !visited[wallID] {
			var component []string
			cwe.dfs(wallID, graph, visited, &component)
			components = append(components, component)
		}
	}

	return components
}

func (cwe *CurvedWallCompositionEngine) dfs(wallID string, graph map[string][]string, visited map[string]bool, component *[]string) {
	visited[wallID] = true
	*component = append(*component, wallID)

	for _, neighbor := range graph[wallID] {
		if !visited[neighbor] {
			cwe.dfs(neighbor, graph, visited, component)
		}
	}
}
