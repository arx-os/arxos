// Package topology provides planar graph algorithms for room detection
package topology

import (
	"fmt"
	"math"
	"sort"
)

// RoomDetector finds closed polygons (rooms) from wall segments
type RoomDetector struct {
	walls      []*Wall
	graph      *PlanarGraph
	rooms      []*Room
	nextRoomID uint64
}

// PlanarGraph represents walls as a planar graph structure
type PlanarGraph struct {
	vertices  map[uint64]*Vertex
	edges     map[uint64]*Edge
	faces     []*Face
	nextID    uint64
}

// Vertex represents a wall intersection or endpoint
type Vertex struct {
	ID       uint64
	Position Point2D
	Edges    []*Edge // Edges connected to this vertex
	Visited  bool
}

// Edge represents a wall segment between vertices
type Edge struct {
	ID       uint64
	Start    *Vertex
	End      *Vertex
	WallID   uint64 // Reference to original wall
	Twin     *Edge  // Opposite direction edge
	Next     *Edge  // Next edge in face traversal
	Face     *Face  // Adjacent face (room)
	Visited  bool
	Angle    float64 // Angle from start vertex
}

// Face represents a closed polygon (potential room)
type Face struct {
	ID          uint64
	Edges       []*Edge
	Vertices    []*Vertex
	IsExterior  bool
	Area        int64
	Centroid    Point2D
}

// NewRoomDetector creates a room detection engine
func NewRoomDetector(walls []*Wall) *RoomDetector {
	return &RoomDetector{
		walls:      walls,
		graph:      NewPlanarGraph(),
		rooms:      make([]*Room, 0),
		nextRoomID: 1,
	}
}

// NewPlanarGraph creates an empty planar graph
func NewPlanarGraph() *PlanarGraph {
	return &PlanarGraph{
		vertices: make(map[uint64]*Vertex),
		edges:    make(map[uint64]*Edge),
		faces:    make([]*Face, 0),
		nextID:   1,
	}
}

// DetectRooms finds all rooms from wall segments
func (rd *RoomDetector) DetectRooms() ([]*Room, error) {
	// Step 1: Build planar graph from walls
	if err := rd.buildGraph(); err != nil {
		return nil, fmt.Errorf("failed to build graph: %w", err)
	}
	
	// Step 2: Sort edges around each vertex for proper traversal
	rd.sortEdgesAroundVertices()
	
	// Step 3: Find all faces using face traversal
	rd.findFaces()
	
	// Step 4: Filter faces to identify rooms
	rd.identifyRooms()
	
	// Step 5: Build room adjacency
	rd.buildRoomAdjacency()
	
	return rd.rooms, nil
}

// buildGraph constructs planar graph from walls
func (rd *RoomDetector) buildGraph() error {
	// Create vertices from wall endpoints
	vertexMap := make(map[string]*Vertex)
	
	for _, wall := range rd.walls {
		// Create or get start vertex
		startKey := fmt.Sprintf("%d_%d", wall.StartPoint.X, wall.StartPoint.Y)
		startVertex, exists := vertexMap[startKey]
		if !exists {
			startVertex = &Vertex{
				ID:       rd.graph.nextID,
				Position: Point2D{X: wall.StartPoint.X, Y: wall.StartPoint.Y},
				Edges:    make([]*Edge, 0),
			}
			rd.graph.vertices[startVertex.ID] = startVertex
			vertexMap[startKey] = startVertex
			rd.graph.nextID++
		}
		
		// Create or get end vertex
		endKey := fmt.Sprintf("%d_%d", wall.EndPoint.X, wall.EndPoint.Y)
		endVertex, exists := vertexMap[endKey]
		if !exists {
			endVertex = &Vertex{
				ID:       rd.graph.nextID,
				Position: Point2D{X: wall.EndPoint.X, Y: wall.EndPoint.Y},
				Edges:    make([]*Edge, 0),
			}
			rd.graph.vertices[endVertex.ID] = endVertex
			vertexMap[endKey] = endVertex
			rd.graph.nextID++
		}
		
		// Create bidirectional edges for the wall
		edge1 := &Edge{
			ID:     rd.graph.nextID,
			Start:  startVertex,
			End:    endVertex,
			WallID: wall.ID,
			Angle:  rd.calculateAngle(startVertex.Position, endVertex.Position),
		}
		rd.graph.edges[edge1.ID] = edge1
		rd.graph.nextID++
		
		edge2 := &Edge{
			ID:     rd.graph.nextID,
			Start:  endVertex,
			End:    startVertex,
			WallID: wall.ID,
			Angle:  rd.calculateAngle(endVertex.Position, startVertex.Position),
		}
		rd.graph.edges[edge2.ID] = edge2
		rd.graph.nextID++
		
		// Set twin references
		edge1.Twin = edge2
		edge2.Twin = edge1
		
		// Add edges to vertices
		startVertex.Edges = append(startVertex.Edges, edge1)
		endVertex.Edges = append(endVertex.Edges, edge2)
	}
	
	// Find and split edge intersections
	rd.handleIntersections()
	
	return nil
}

// handleIntersections finds and splits intersecting edges
func (rd *RoomDetector) handleIntersections() {
	edges := make([]*Edge, 0, len(rd.graph.edges))
	for _, e := range rd.graph.edges {
		edges = append(edges, e)
	}
	
	// Check all edge pairs for intersections
	for i := 0; i < len(edges); i++ {
		for j := i + 1; j < len(edges); j++ {
			e1, e2 := edges[i], edges[j]
			
			// Skip if edges share a vertex
			if e1.Start == e2.Start || e1.Start == e2.End ||
			   e1.End == e2.Start || e1.End == e2.End {
				continue
			}
			
			// Check for intersection
			if intersect, point := rd.edgesIntersect(e1, e2); intersect {
				// Create new vertex at intersection
				vertex := &Vertex{
					ID:       rd.graph.nextID,
					Position: point,
					Edges:    make([]*Edge, 0),
				}
				rd.graph.vertices[vertex.ID] = vertex
				rd.graph.nextID++
				
				// Split both edges at intersection
				rd.splitEdge(e1, vertex)
				rd.splitEdge(e2, vertex)
			}
		}
	}
}

// edgesIntersect checks if two edges intersect
func (rd *RoomDetector) edgesIntersect(e1, e2 *Edge) (bool, Point2D) {
	// Line segment intersection using parametric equations
	p1, p2 := e1.Start.Position, e1.End.Position
	p3, p4 := e2.Start.Position, e2.End.Position
	
	denom := float64((p4.Y-p3.Y)*(p2.X-p1.X) - (p4.X-p3.X)*(p2.Y-p1.Y))
	
	if math.Abs(denom) < 1e-10 {
		return false, Point2D{} // Parallel lines
	}
	
	ua := float64((p4.X-p3.X)*(p1.Y-p3.Y) - (p4.Y-p3.Y)*(p1.X-p3.X)) / denom
	ub := float64((p2.X-p1.X)*(p1.Y-p3.Y) - (p2.Y-p1.Y)*(p1.X-p3.X)) / denom
	
	if ua >= 0 && ua <= 1 && ub >= 0 && ub <= 1 {
		// Intersection point
		x := p1.X + int64(ua*float64(p2.X-p1.X))
		y := p1.Y + int64(ua*float64(p2.Y-p1.Y))
		return true, Point2D{X: x, Y: y}
	}
	
	return false, Point2D{}
}

// splitEdge splits an edge at a vertex
func (rd *RoomDetector) splitEdge(edge *Edge, vertex *Vertex) {
	// Create new edge from intersection to end
	newEdge := &Edge{
		ID:     rd.graph.nextID,
		Start:  vertex,
		End:    edge.End,
		WallID: edge.WallID,
		Angle:  rd.calculateAngle(vertex.Position, edge.End.Position),
	}
	rd.graph.edges[newEdge.ID] = newEdge
	rd.graph.nextID++
	
	// Update original edge to end at intersection
	edge.End = vertex
	edge.Angle = rd.calculateAngle(edge.Start.Position, vertex.Position)
	
	// Update vertex edges
	vertex.Edges = append(vertex.Edges, newEdge)
	
	// Handle twin edges
	if edge.Twin != nil {
		twinNew := &Edge{
			ID:     rd.graph.nextID,
			Start:  vertex,
			End:    edge.Twin.Start,
			WallID: edge.WallID,
			Angle:  rd.calculateAngle(vertex.Position, edge.Twin.Start.Position),
		}
		rd.graph.edges[twinNew.ID] = twinNew
		rd.graph.nextID++
		
		edge.Twin.Start = vertex
		edge.Twin.Angle = rd.calculateAngle(vertex.Position, edge.Twin.End.Position)
		
		newEdge.Twin = edge.Twin
		edge.Twin.Twin = newEdge
		edge.Twin = twinNew
		twinNew.Twin = edge
		
		vertex.Edges = append(vertex.Edges, twinNew)
	}
}

// sortEdgesAroundVertices sorts edges counter-clockwise around each vertex
func (rd *RoomDetector) sortEdgesAroundVertices() {
	for _, vertex := range rd.graph.vertices {
		// Sort edges by angle
		sort.Slice(vertex.Edges, func(i, j int) bool {
			return vertex.Edges[i].Angle < vertex.Edges[j].Angle
		})
		
		// Set next pointers for face traversal
		for i, edge := range vertex.Edges {
			nextIndex := (i + 1) % len(vertex.Edges)
			
			// Find the twin of the next edge around the end vertex
			nextEdge := vertex.Edges[nextIndex]
			if nextEdge.Twin != nil {
				edge.Next = nextEdge.Twin
			}
		}
	}
}

// findFaces discovers all faces using edge traversal
func (rd *RoomDetector) findFaces() {
	faceID := uint64(1)
	
	// Try to start a face from each unvisited edge
	for _, edge := range rd.graph.edges {
		if edge.Visited || edge.Face != nil {
			continue
		}
		
		face := rd.traceFace(edge, faceID)
		if face != nil {
			rd.graph.faces = append(rd.graph.faces, face)
			faceID++
		}
	}
}

// traceFace follows edges to form a closed face
func (rd *RoomDetector) traceFace(startEdge *Edge, faceID uint64) *Face {
	face := &Face{
		ID:       faceID,
		Edges:    make([]*Edge, 0),
		Vertices: make([]*Vertex, 0),
	}
	
	currentEdge := startEdge
	maxIterations := len(rd.graph.edges) // Prevent infinite loops
	iterations := 0
	
	for iterations < maxIterations {
		if currentEdge.Visited {
			break
		}
		
		currentEdge.Visited = true
		currentEdge.Face = face
		face.Edges = append(face.Edges, currentEdge)
		face.Vertices = append(face.Vertices, currentEdge.Start)
		
		// Find next edge: most counter-clockwise from current
		nextEdge := rd.findNextEdge(currentEdge)
		if nextEdge == nil {
			return nil // Can't form closed face
		}
		
		if nextEdge == startEdge {
			// Closed the face
			break
		}
		
		currentEdge = nextEdge
		iterations++
	}
	
	if iterations >= maxIterations {
		return nil // Failed to close face
	}
	
	// Calculate face properties
	rd.calculateFaceProperties(face)
	
	return face
}

// findNextEdge finds the next edge in counter-clockwise order
func (rd *RoomDetector) findNextEdge(currentEdge *Edge) *Edge {
	endVertex := currentEdge.End
	
	// Find current edge's twin in the end vertex's edge list
	var currentIndex int
	for i, e := range endVertex.Edges {
		if e.Twin == currentEdge {
			currentIndex = i
			break
		}
	}
	
	// Get next edge counter-clockwise
	nextIndex := (currentIndex + 1) % len(endVertex.Edges)
	return endVertex.Edges[nextIndex]
}

// calculateFaceProperties computes area and centroid
func (rd *RoomDetector) calculateFaceProperties(face *Face) {
	if len(face.Vertices) < 3 {
		return
	}
	
	// Calculate area using shoelace formula
	var area int64
	var cx, cy int64
	n := len(face.Vertices)
	
	for i := 0; i < n; i++ {
		j := (i + 1) % n
		v1, v2 := face.Vertices[i].Position, face.Vertices[j].Position
		
		crossProduct := v1.X*v2.Y - v2.X*v1.Y
		area += crossProduct
		
		cx += (v1.X + v2.X) * crossProduct
		cy += (v1.Y + v2.Y) * crossProduct
	}
	
	area = int64(math.Abs(float64(area) / 2))
	face.Area = area
	
	if area > 0 {
		face.Centroid = Point2D{
			X: cx / (6 * area),
			Y: cy / (6 * area),
		}
	}
	
	// Determine if exterior face (largest area)
	face.IsExterior = false
}

// identifyRooms converts faces to rooms
func (rd *RoomDetector) identifyRooms() {
	// Find exterior face (typically largest area)
	var maxArea int64
	var exteriorFace *Face
	
	for _, face := range rd.graph.faces {
		if face.Area > maxArea {
			maxArea = face.Area
			exteriorFace = face
		}
	}
	
	if exteriorFace != nil {
		exteriorFace.IsExterior = true
	}
	
	// Convert interior faces to rooms
	for _, face := range rd.graph.faces {
		if face.IsExterior {
			continue
		}
		
		// Minimum area threshold for valid room (1 square meter)
		minArea := int64(1e18) // 1m² in square nanometers
		if face.Area < minArea {
			continue
		}
		
		room := rd.faceToRoom(face)
		rd.rooms = append(rd.rooms, room)
	}
}

// faceToRoom converts a face to a room
func (rd *RoomDetector) faceToRoom(face *Face) *Room {
	room := &Room{
		ID:            rd.nextRoomID,
		Area:          face.Area,
		Centroid:      Point3D{X: face.Centroid.X, Y: face.Centroid.Y, Z: 0},
		CeilingHeight: 3 * 1e9, // Default 3m
		Footprint:     make([]Point2D, 0),
		BoundaryWalls: make([]uint64, 0),
	}
	
	rd.nextRoomID++
	
	// Extract footprint polygon
	for _, vertex := range face.Vertices {
		room.Footprint = append(room.Footprint, vertex.Position)
	}
	
	// Extract boundary wall IDs
	wallSet := make(map[uint64]bool)
	for _, edge := range face.Edges {
		wallSet[edge.WallID] = true
	}
	
	for wallID := range wallSet {
		room.BoundaryWalls = append(room.BoundaryWalls, wallID)
	}
	
	return room
}

// buildRoomAdjacency determines which rooms are adjacent
func (rd *RoomDetector) buildRoomAdjacency() {
	// Check each pair of rooms for shared walls
	for i := 0; i < len(rd.rooms); i++ {
		for j := i + 1; j < len(rd.rooms); j++ {
			room1, room2 := rd.rooms[i], rd.rooms[j]
			
			// Check for shared walls
			for _, wall1 := range room1.BoundaryWalls {
				for _, wall2 := range room2.BoundaryWalls {
					if wall1 == wall2 {
						// Rooms share a wall
						room1.AdjacentRooms = append(room1.AdjacentRooms, room2.ID)
						room2.AdjacentRooms = append(room2.AdjacentRooms, room1.ID)
						break
					}
				}
			}
		}
	}
}

// calculateAngle computes angle from p1 to p2
func (rd *RoomDetector) calculateAngle(p1, p2 Point2D) float64 {
	dx := float64(p2.X - p1.X)
	dy := float64(p2.Y - p1.Y)
	angle := math.Atan2(dy, dx)
	
	// Normalize to [0, 2π]
	if angle < 0 {
		angle += 2 * math.Pi
	}
	
	return angle
}

// ValidateRooms checks room topology for issues
func (rd *RoomDetector) ValidateRooms() []ValidationIssue {
	issues := make([]ValidationIssue, 0)
	
	for _, room := range rd.rooms {
		// Check for minimum area
		minArea := int64(4e18) // 4m² minimum
		if room.Area < minArea {
			issues = append(issues, ValidationIssue{
				Type:        IssueTypeInvalidDimensions,
				Severity:    SeverityWarning,
				Description: fmt.Sprintf("Room %d area too small: %.2f m²", 
					room.ID, float64(room.Area)/1e18),
				AffectedIDs: []uint64{room.ID},
			})
		}
		
		// Check for proper closure
		if len(room.Footprint) < 3 {
			issues = append(issues, ValidationIssue{
				Type:        IssueTypeUnclosedRoom,
				Severity:    SeverityError,
				Description: fmt.Sprintf("Room %d has insufficient vertices", room.ID),
				AffectedIDs: []uint64{room.ID},
			})
		}
		
		// Check for self-intersection
		if rd.polygonSelfIntersects(room.Footprint) {
			issues = append(issues, ValidationIssue{
				Type:        IssueTypeUnclosedRoom,
				Severity:    SeverityError,
				Description: fmt.Sprintf("Room %d polygon self-intersects", room.ID),
				AffectedIDs: []uint64{room.ID},
			})
		}
	}
	
	return issues
}

// polygonSelfIntersects checks if polygon edges cross
func (rd *RoomDetector) polygonSelfIntersects(polygon []Point2D) bool {
	n := len(polygon)
	
	for i := 0; i < n; i++ {
		for j := i + 2; j < n; j++ {
			// Skip adjacent edges
			if (j == i+1) || (i == 0 && j == n-1) {
				continue
			}
			
			// Create temporary edges for intersection test
			e1 := &Edge{
				Start: &Vertex{Position: polygon[i]},
				End:   &Vertex{Position: polygon[(i+1)%n]},
			}
			e2 := &Edge{
				Start: &Vertex{Position: polygon[j]},
				End:   &Vertex{Position: polygon[(j+1)%n]},
			}
			
			if intersect, _ := rd.edgesIntersect(e1, e2); intersect {
				return true
			}
		}
	}
	
	return false
}

// OptimizeRoomDetection applies heuristics for better detection
func (rd *RoomDetector) OptimizeRoomDetection() {
	// Merge very small adjacent rooms
	rd.mergeSmallRooms()
	
	// Split large irregular rooms
	rd.splitIrregularRooms()
	
	// Infer missing walls from patterns
	rd.inferMissingWalls()
}

// mergeSmallRooms combines tiny adjacent rooms
func (rd *RoomDetector) mergeSmallRooms() {
	minArea := int64(2e18) // 2m² threshold
	
	for i := 0; i < len(rd.rooms); i++ {
		room := rd.rooms[i]
		
		if room.Area >= minArea {
			continue
		}
		
		// Find adjacent room to merge with
		for _, adjID := range room.AdjacentRooms {
			for _, adjRoom := range rd.rooms {
				if adjRoom.ID == adjID {
					// Merge rooms
					adjRoom.Area += room.Area
					// Remove small room
					rd.rooms = append(rd.rooms[:i], rd.rooms[i+1:]...)
					i--
					break
				}
			}
			break
		}
	}
}

// splitIrregularRooms divides complex polygons
func (rd *RoomDetector) splitIrregularRooms() {
	// TODO: Implement room splitting for L-shaped or irregular rooms
	// This would use algorithms like polygon decomposition
}

// inferMissingWalls adds walls based on patterns
func (rd *RoomDetector) inferMissingWalls() {
	// TODO: Use semantic patterns to infer missing walls
	// E.g., if three walls form most of a classroom-sized rectangle,
	// infer the fourth wall
}