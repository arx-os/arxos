package pdf

import (
	"encoding/json"
	"fmt"
	"math"
	"sort"

	"github.com/arxos/arxos/core/internal/arxobject"
	"github.com/arxos/arxos/core/wall_composition/engine"
	"github.com/arxos/arxos/core/wall_composition/types"
)

// PDFToBIMProcessor handles the complete pipeline from PDF extraction to BIM model
type PDFToBIMProcessor struct {
	wallEngine *engine.WallCompositionEngine
	config     ProcessorConfig
}

// ProcessorConfig holds configuration for the PDF to BIM processor
type ProcessorConfig struct {
	// Wall detection parameters
	WallThicknessMin float64 // Minimum wall thickness in mm
	WallThicknessMax float64 // Maximum wall thickness in mm
	
	// Line merging parameters
	MergeAngleTolerance   float64 // Degrees - lines within this angle are considered collinear
	MergeDistanceTolerance float64 // mm - maximum gap between segments to merge
	
	// Room detection parameters
	MinRoomArea float64 // Minimum area in sq mm to consider as a room
	MaxRoomArea float64 // Maximum area in sq mm
	
	// Coordinate scaling
	PDFToMMScale float64 // Conversion factor from PDF units to millimeters
}

// DefaultProcessorConfig returns sensible defaults
func DefaultProcessorConfig() ProcessorConfig {
	return ProcessorConfig{
		WallThicknessMin:       100.0,  // 10cm minimum wall thickness
		WallThicknessMax:       500.0,  // 50cm maximum wall thickness
		MergeAngleTolerance:    5.0,    // 5 degrees tolerance
		MergeDistanceTolerance: 50.0,   // 5cm gap tolerance
		MinRoomArea:            1000000.0, // 1 sq meter minimum room
		MaxRoomArea:            100000000.0, // 100 sq meter maximum room
		PDFToMMScale:           3.5278, // PDF points to mm (assuming 72 DPI)
	}
}

// NewPDFToBIMProcessor creates a new processor instance
func NewPDFToBIMProcessor(config ProcessorConfig) *PDFToBIMProcessor {
	wallConfig := engine.DefaultCompositionConfig()
	wallConfig.MaxGapDistance = config.MergeDistanceTolerance
	wallConfig.ParallelThreshold = config.MergeAngleTolerance
	
	return &PDFToBIMProcessor{
		wallEngine: engine.NewWallCompositionEngine(wallConfig),
		config:     config,
	}
}

// ProcessArxObjects takes raw ArxObjects from PDF extraction and creates a proper BIM model
func (p *PDFToBIMProcessor) ProcessArxObjects(rawObjects []arxobject.ArxObject) (*BIMResult, error) {
	// Step 1: Classify and filter objects
	classified := p.classifyObjects(rawObjects)
	
	// Step 2: Process walls - merge segments and compose structures
	wallStructures, err := p.processWalls(classified.walls)
	if err != nil {
		return nil, fmt.Errorf("wall processing failed: %w", err)
	}
	
	// Step 3: Detect rooms from closed wall loops
	rooms := p.detectRooms(wallStructures)
	
	// Step 4: Detect doors and windows from wall gaps
	doors, windows := p.detectOpenings(wallStructures)
	
	// Step 5: Process text labels and associate with rooms
	p.associateLabels(rooms, classified.texts)
	
	// Step 6: Calculate overall confidence
	confidence := p.calculateConfidence(wallStructures, rooms)
	
	return &BIMResult{
		WallStructures: wallStructures,
		Rooms:          rooms,
		Doors:          doors,
		Windows:        windows,
		Texts:          classified.texts,
		Columns:        classified.columns,
		Confidence:     confidence,
		Statistics:     p.generateStatistics(wallStructures, rooms),
	}, nil
}

// classifyObjects groups ArxObjects by type
func (p *PDFToBIMProcessor) classifyObjects(objects []arxobject.ArxObject) classifiedObjects {
	result := classifiedObjects{
		walls:   []arxobject.ArxObject{},
		texts:   []arxobject.ArxObject{},
		columns: []arxobject.ArxObject{},
		other:   []arxobject.ArxObject{},
	}
	
	for _, obj := range objects {
		switch p.detectObjectType(obj) {
		case "wall":
			result.walls = append(result.walls, obj)
		case "text":
			result.texts = append(result.texts, obj)
		case "column":
			result.columns = append(result.columns, obj)
		default:
			result.other = append(result.other, obj)
		}
	}
	
	return result
}

// detectObjectType determines the type of an ArxObject based on its properties
func (p *PDFToBIMProcessor) detectObjectType(obj arxobject.ArxObject) string {
	// Check explicit type
	if obj.Type != "" {
		objType := obj.Type
		if contains(objType, "wall") || contains(objType, "line") {
			// Check if it's a wall-like line (thickness, length)
			if p.isWallLike(obj) {
				return "wall"
			}
		}
		if contains(objType, "text") || contains(objType, "label") {
			return "text"
		}
		if contains(objType, "column") || contains(objType, "pillar") {
			return "column"
		}
	}
	
	// Infer from geometry
	if p.isWallLike(obj) {
		return "wall"
	}
	
	return "other"
}

// isWallLike checks if an object has wall-like properties
func (p *PDFToBIMProcessor) isWallLike(obj arxobject.ArxObject) bool {
	// Check if it's a line with appropriate thickness
	if obj.Data != nil {
		if thickness, ok := obj.Data["thickness"].(float64); ok {
			thicknessMM := thickness * p.config.PDFToMMScale
			if thicknessMM >= p.config.WallThicknessMin && thicknessMM <= p.config.WallThicknessMax {
				return true
			}
		}
		
		// Check for parallel lines (double-line walls)
		if lineType, ok := obj.Data["line_type"].(string); ok {
			if lineType == "double" || lineType == "parallel" {
				return true
			}
		}
	}
	
	return false
}

// processWalls merges wall segments and creates wall structures
func (p *PDFToBIMProcessor) processWalls(wallObjects []arxobject.ArxObject) ([]*types.WallStructure, error) {
	// Convert ArxObjects to format expected by wall composition engine
	wallInputs := make([]engine.ArxObject, len(wallObjects))
	for i, obj := range wallObjects {
		wallInputs[i] = &arxObjectAdapter{obj: obj, scale: p.config.PDFToMMScale}
	}
	
	// Use the wall composition engine
	structures, err := p.wallEngine.ComposeWalls(wallInputs)
	if err != nil {
		return nil, err
	}
	
	// Post-process: merge collinear segments
	p.mergeCollinearSegments(structures)
	
	return structures, nil
}

// mergeCollinearSegments combines wall segments that form continuous lines
func (p *PDFToBIMProcessor) mergeCollinearSegments(structures []*types.WallStructure) {
	for _, structure := range structures {
		if len(structure.Segments) <= 1 {
			continue
		}
		
		merged := []types.WallSegment{}
		current := structure.Segments[0]
		
		for i := 1; i < len(structure.Segments); i++ {
			next := structure.Segments[i]
			
			// Check if segments are collinear and connected
			if p.areCollinear(current, next) && p.areConnected(current, next) {
				// Merge segments
				current = p.mergeSegments(current, next)
			} else {
				merged = append(merged, current)
				current = next
			}
		}
		
		merged = append(merged, current)
		structure.Segments = merged
	}
}

// areCollinear checks if two wall segments are on the same line
func (p *PDFToBIMProcessor) areCollinear(seg1, seg2 types.WallSegment) bool {
	// Calculate angles
	angle1 := math.Atan2(
		seg1.EndPoint.ToMillimeters().Y-seg1.StartPoint.ToMillimeters().Y,
		seg1.EndPoint.ToMillimeters().X-seg1.StartPoint.ToMillimeters().X,
	)
	angle2 := math.Atan2(
		seg2.EndPoint.ToMillimeters().Y-seg2.StartPoint.ToMillimeters().Y,
		seg2.EndPoint.ToMillimeters().X-seg2.StartPoint.ToMillimeters().X,
	)
	
	// Convert to degrees and check tolerance
	angleDiff := math.Abs(angle1-angle2) * 180.0 / math.Pi
	
	// Handle angle wrap-around
	if angleDiff > 180 {
		angleDiff = 360 - angleDiff
	}
	
	return angleDiff <= p.config.MergeAngleTolerance
}

// areConnected checks if two segments are close enough to merge
func (p *PDFToBIMProcessor) areConnected(seg1, seg2 types.WallSegment) bool {
	// Check end-to-start connection
	dist := p.distance(seg1.EndPoint, seg2.StartPoint)
	if dist <= p.config.MergeDistanceTolerance {
		return true
	}
	
	// Check start-to-end connection
	dist = p.distance(seg1.StartPoint, seg2.EndPoint)
	return dist <= p.config.MergeDistanceTolerance
}

// distance calculates distance between two points in mm
func (p *PDFToBIMProcessor) distance(p1, p2 types.SmartPoint3D) float64 {
	p1mm := p1.ToMillimeters()
	p2mm := p2.ToMillimeters()
	
	dx := p1mm.X - p2mm.X
	dy := p1mm.Y - p2mm.Y
	
	return math.Sqrt(dx*dx + dy*dy)
}

// mergeSegments combines two wall segments into one
func (p *PDFToBIMProcessor) mergeSegments(seg1, seg2 types.WallSegment) types.WallSegment {
	// Determine the extreme points
	points := []types.SmartPoint3D{
		seg1.StartPoint, seg1.EndPoint,
		seg2.StartPoint, seg2.EndPoint,
	}
	
	// Find the two points that are furthest apart
	maxDist := 0.0
	var start, end types.SmartPoint3D
	
	for i := 0; i < len(points); i++ {
		for j := i + 1; j < len(points); j++ {
			dist := p.distance(points[i], points[j])
			if dist > maxDist {
				maxDist = dist
				start = points[i]
				end = points[j]
			}
		}
	}
	
	// Create merged segment
	merged := types.WallSegment{
		ID:         seg1.ID, // Keep first segment's ID
		StartPoint: start,
		EndPoint:   end,
		Length:     maxDist,
		Height:     seg1.Height,
		Thickness:  seg1.Thickness,
		Material:   seg1.Material,
		ArxObjects: append(seg1.ArxObjects, seg2.ArxObjects...),
		Confidence: (seg1.Confidence + seg2.Confidence) / 2,
	}
	
	return merged
}

// detectRooms identifies rooms from closed wall loops
func (p *PDFToBIMProcessor) detectRooms(wallStructures []*types.WallStructure) []*Room {
	rooms := []*Room{}
	
	// Build a graph of wall connections
	graph := p.buildWallGraph(wallStructures)
	
	// Find closed loops in the graph
	loops := p.findClosedLoops(graph)
	
	// Convert loops to rooms
	for _, loop := range loops {
		room := p.createRoomFromLoop(loop)
		if room != nil && p.isValidRoom(room) {
			rooms = append(rooms, room)
		}
	}
	
	return rooms
}

// detectOpenings finds doors and windows from gaps in walls
func (p *PDFToBIMProcessor) detectOpenings(wallStructures []*types.WallStructure) ([]*Door, []*Window) {
	doors := []*Door{}
	windows := []*Window{}
	
	// Look for gaps in wall structures
	for _, structure := range wallStructures {
		gaps := p.findGapsInStructure(structure)
		
		for _, gap := range gaps {
			if p.isDoorGap(gap) {
				doors = append(doors, p.createDoor(gap))
			} else if p.isWindowGap(gap) {
				windows = append(windows, p.createWindow(gap))
			}
		}
	}
	
	return doors, windows
}

// Helper structures

type classifiedObjects struct {
	walls   []arxobject.ArxObject
	texts   []arxobject.ArxObject
	columns []arxobject.ArxObject
	other   []arxobject.ArxObject
}

type BIMResult struct {
	WallStructures []*types.WallStructure `json:"wall_structures"`
	Rooms          []*Room                `json:"rooms"`
	Doors          []*Door                `json:"doors"`
	Windows        []*Window              `json:"windows"`
	Texts          []arxobject.ArxObject  `json:"texts"`
	Columns        []arxobject.ArxObject  `json:"columns"`
	Confidence     float64                `json:"confidence"`
	Statistics     map[string]interface{} `json:"statistics"`
}

type Room struct {
	ID         string                 `json:"id"`
	Boundaries []types.SmartPoint3D   `json:"boundaries"`
	Area       float64                `json:"area"`
	Label      string                 `json:"label"`
	Properties map[string]interface{} `json:"properties"`
}

type Door struct {
	ID       string               `json:"id"`
	Position types.SmartPoint3D   `json:"position"`
	Width    float64              `json:"width"`
	WallID   string               `json:"wall_id"`
}

type Window struct {
	ID       string               `json:"id"`
	Position types.SmartPoint3D   `json:"position"`
	Width    float64              `json:"width"`
	Height   float64              `json:"height"`
	WallID   string               `json:"wall_id"`
}

// arxObjectAdapter adapts ArxObject to the engine.ArxObject interface
type arxObjectAdapter struct {
	obj   arxobject.ArxObject
	scale float64
}

func (a *arxObjectAdapter) GetID() string {
	return a.obj.ID
}

func (a *arxObjectAdapter) GetCoordinates() [][]float64 {
	// Extract coordinates from geometry or x,y properties
	coords := [][]float64{}
	
	// Handle different geometry types
	if a.obj.Geometry != nil {
		// Assuming geometry has a coordinates field
		if coordData, ok := a.obj.Geometry["coordinates"].([]interface{}); ok {
			for _, coord := range coordData {
				if point, ok := coord.([]interface{}); ok && len(point) >= 2 {
					x, _ := point[0].(float64)
					y, _ := point[1].(float64)
					coords = append(coords, []float64{x * a.scale, y * a.scale})
				}
			}
		}
	}
	
	// Fallback to x,y properties
	if len(coords) == 0 && a.obj.X != 0 && a.obj.Y != 0 {
		coords = append(coords, []float64{float64(a.obj.X), float64(a.obj.Y)})
		if a.obj.Width > 0 {
			coords = append(coords, []float64{float64(a.obj.X + a.obj.Width), float64(a.obj.Y)})
		}
	}
	
	return coords
}

func (a *arxObjectAdapter) GetProperties() map[string]interface{} {
	return a.obj.Data
}

// Utility functions

func contains(s, substr string) bool {
	return strings.Contains(strings.ToLower(s), strings.ToLower(substr))
}

func containsString(slice []string, str string) bool {
	for _, s := range slice {
		if s == str {
			return true
		}
	}
	return false
}

// Stub implementations for complex algorithms
// These would need full implementation based on your specific requirements

func (p *PDFToBIMProcessor) buildWallGraph(structures []*types.WallStructure) map[string][]string {
	// Build adjacency graph from wall structures based on endpoint connections
	graph := make(map[string][]string)
	
	// Create a map of endpoints to wall IDs
	endpointMap := make(map[string][]string)
	
	for _, structure := range structures {
		for _, segment := range structure.Segments {
			// Get start and end points as strings for map keys
			startKey := fmt.Sprintf("%.0f,%.0f", 
				segment.StartPoint.ToMillimeters().X, 
				segment.StartPoint.ToMillimeters().Y)
			endKey := fmt.Sprintf("%.0f,%.0f",
				segment.EndPoint.ToMillimeters().X,
				segment.EndPoint.ToMillimeters().Y)
			
			// Add this segment to both endpoint maps
			endpointMap[startKey] = append(endpointMap[startKey], segment.ID)
			endpointMap[endKey] = append(endpointMap[endKey], segment.ID)
			
			// Initialize graph entry for this segment
			if _, exists := graph[segment.ID]; !exists {
				graph[segment.ID] = []string{}
			}
		}
	}
	
	// Build adjacency list - walls that share endpoints are connected
	for _, wallIDs := range endpointMap {
		if len(wallIDs) > 1 {
			// These walls share an endpoint, connect them in the graph
			for i, wall1 := range wallIDs {
				for j, wall2 := range wallIDs {
					if i != j {
						// Add wall2 to wall1's adjacency list if not already there
						if !containsString(graph[wall1], wall2) {
							graph[wall1] = append(graph[wall1], wall2)
						}
					}
				}
			}
		}
	}
	
	return graph
}

func (p *PDFToBIMProcessor) findClosedLoops(graph map[string][]string) [][]string {
	// Implement cycle detection using DFS to find closed loops (rooms)
	var loops [][]string
	visited := make(map[string]bool)
	
	// Try to find loops starting from each unvisited node
	for startNode := range graph {
		if !visited[startNode] {
			// Use DFS to find cycles
			path := []string{}
			if p.findCycleDFS(startNode, startNode, graph, visited, path, &loops, make(map[string]bool)) {
				visited[startNode] = true
			}
		}
	}
	
	// Filter out duplicate loops and very small loops
	uniqueLoops := p.filterUniqueLoops(loops)
	
	return uniqueLoops
}

func (p *PDFToBIMProcessor) findCycleDFS(current, start string, graph map[string][]string, 
	globalVisited map[string]bool, path []string, loops *[][]string, localVisited map[string]bool) bool {
	
	path = append(path, current)
	localVisited[current] = true
	
	// Check each neighbor
	for _, neighbor := range graph[current] {
		// Found a cycle back to start (minimum 3 walls for a room)
		if neighbor == start && len(path) >= 3 {
			// Make a copy of the path as a complete loop
			loop := make([]string, len(path))
			copy(loop, path)
			*loops = append(*loops, loop)
			return true
		}
		
		// Continue DFS if not visited in this path
		if !localVisited[neighbor] && len(path) < 20 { // Limit depth to prevent infinite recursion
			p.findCycleDFS(neighbor, start, graph, globalVisited, path, loops, localVisited)
		}
	}
	
	return false
}

func (p *PDFToBIMProcessor) filterUniqueLoops(loops [][]string) [][]string {
	uniqueLoops := [][]string{}
	seen := make(map[string]bool)
	
	for _, loop := range loops {
		// Skip very small loops (less than 3 walls can't form a room)
		if len(loop) < 3 {
			continue
		}
		
		// Create a normalized representation of the loop for deduplication
		// Sort the wall IDs to create a canonical form
		sortedLoop := make([]string, len(loop))
		copy(sortedLoop, loop)
		sort.Strings(sortedLoop)
		loopKey := strings.Join(sortedLoop, ",")
		
		if !seen[loopKey] {
			seen[loopKey] = true
			uniqueLoops = append(uniqueLoops, loop)
		}
	}
	
	return uniqueLoops
}

func (p *PDFToBIMProcessor) createRoomFromLoop(loop []string) *Room {
	// TODO: Create room from wall loop
	return nil
}

func (p *PDFToBIMProcessor) isValidRoom(room *Room) bool {
	return room.Area >= p.config.MinRoomArea && room.Area <= p.config.MaxRoomArea
}

func (p *PDFToBIMProcessor) findGapsInStructure(structure *types.WallStructure) []Gap {
	// TODO: Find discontinuities in wall structure
	return []Gap{}
}

type Gap struct {
	Start  types.SmartPoint3D
	End    types.SmartPoint3D
	Width  float64
	WallID string
}

func (p *PDFToBIMProcessor) isDoorGap(gap Gap) bool {
	// Doors are typically 700-1000mm wide
	return gap.Width >= 700 && gap.Width <= 1000
}

func (p *PDFToBIMProcessor) isWindowGap(gap Gap) bool {
	// Windows vary more in width
	return gap.Width >= 400 && gap.Width <= 2000
}

func (p *PDFToBIMProcessor) createDoor(gap Gap) *Door {
	return &Door{
		ID:       fmt.Sprintf("door_%s", gap.WallID),
		Position: gap.Start,
		Width:    gap.Width,
		WallID:   gap.WallID,
	}
}

func (p *PDFToBIMProcessor) createWindow(gap Gap) *Window {
	return &Window{
		ID:       fmt.Sprintf("window_%s", gap.WallID),
		Position: gap.Start,
		Width:    gap.Width,
		Height:   1200, // Standard window height
		WallID:   gap.WallID,
	}
}

func (p *PDFToBIMProcessor) associateLabels(rooms []*Room, texts []arxobject.ArxObject) {
	// TODO: Match text labels to rooms based on position
}

func (p *PDFToBIMProcessor) calculateConfidence(walls []*types.WallStructure, rooms []*Room) float64 {
	if len(walls) == 0 {
		return 0
	}
	
	totalConfidence := 0.0
	count := 0
	
	for _, wall := range walls {
		totalConfidence += float64(wall.Confidence)
		count++
	}
	
	return totalConfidence / float64(count)
}

func (p *PDFToBIMProcessor) generateStatistics(walls []*types.WallStructure, rooms []*Room) map[string]interface{} {
	return map[string]interface{}{
		"total_walls":     len(walls),
		"total_rooms":     len(rooms),
		"total_segments":  p.countSegments(walls),
		"average_wall_length": p.averageWallLength(walls),
	}
}

func (p *PDFToBIMProcessor) countSegments(walls []*types.WallStructure) int {
	count := 0
	for _, wall := range walls {
		count += len(wall.Segments)
	}
	return count
}

func (p *PDFToBIMProcessor) averageWallLength(walls []*types.WallStructure) float64 {
	if len(walls) == 0 {
		return 0
	}
	
	total := 0.0
	for _, wall := range walls {
		total += wall.Length
	}
	
	return total / float64(len(walls))
}