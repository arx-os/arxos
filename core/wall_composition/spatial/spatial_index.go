package spatial

import (
	"fmt"

	"github.com/arxos/arxos/core/wall_composition/types"
)

// SpatialIndex provides spatial indexing for efficient wall queries
type SpatialIndex struct {
	root       *QuadNode
	maxObjects int
	maxDepth   int
	objects    map[string]ArxObject // Object lookup map
}

// QuadNode represents a node in the quadtree
type QuadNode struct {
	bounds   BoundingBox
	objects  []string // Store original string IDs instead of uint64
	children [4]*QuadNode
	isLeaf   bool
	depth    int
}

// NewSpatialIndex creates a new spatial index
func NewSpatialIndex() *SpatialIndex {
	return &SpatialIndex{
		maxObjects: 10,
		maxDepth:   8,
		objects:    make(map[string]ArxObject),
	}
}

// Build builds the spatial index from ArxObjects
func (si *SpatialIndex) Build(arxObjects []ArxObject) {
	if len(arxObjects) == 0 {
		return
	}

	// Calculate overall bounds
	bounds := si.calculateBounds(arxObjects)

	// Create root node
	si.root = &QuadNode{
		bounds: bounds,
		depth:  0,
		isLeaf: true,
	}

	// Insert all objects
	for _, obj := range arxObjects {
		coordinates := obj.GetCoordinates()
		if len(coordinates) > 0 {
			// Use first coordinate for spatial indexing
			si.insertObject(si.root, obj.GetID(), coordinates[0].X, coordinates[0].Y)
			si.objects[obj.GetID()] = obj // Add to lookup map
		}
	}
}

// FindNearbyObjects finds objects within a radius of a point
func (si *SpatialIndex) FindNearbyObjects(point types.SmartPoint3D, radius float64) []string {
	var results []string

	// Convert radius from mm to nm
	radiusNano := int64(radius * 1e6)

	searchBounds := BoundingBox{
		MinX: point.X - radiusNano,
		MinY: point.Y - radiusNano,
		MaxX: point.X + radiusNano,
		MaxY: point.Y + radiusNano,
	}

	si.query(si.root, searchBounds, &results)
	return results
}

// calculateBounds calculates the overall bounding box from ArxObjects
func (si *SpatialIndex) calculateBounds(arxObjects []ArxObject) BoundingBox {
	if len(arxObjects) == 0 {
		return BoundingBox{}
	}

	// Initialize with first object's coordinates
	firstCoords := arxObjects[0].GetCoordinates()
	if len(firstCoords) == 0 {
		return BoundingBox{}
	}

	minX := firstCoords[0].X
	minY := firstCoords[0].Y
	maxX := firstCoords[0].X
	maxY := firstCoords[0].Y

	// Find extremes
	for _, obj := range arxObjects {
		coordinates := obj.GetCoordinates()
		for _, coord := range coordinates {
			if coord.X < minX {
				minX = coord.X
			}
			if coord.X > maxX {
				maxX = coord.X
			}
			if coord.Y < minY {
				minY = coord.Y
			}
			if coord.Y > maxY {
				maxY = coord.Y
			}
		}
	}

	return BoundingBox{
		MinX: minX,
		MinY: minY,
		MaxX: maxX,
		MaxY: maxY,
	}
}

// insertObject inserts an object into the quadtree
func (si *SpatialIndex) insertObject(node *QuadNode, objectID string, x, y int64) {
	if !node.bounds.Contains(x, y) {
		return
	}

	if node.isLeaf {
		// Store the original string ID directly
		node.objects = append(node.objects, objectID)

		// Split if too many objects
		if len(node.objects) > si.maxObjects && node.depth < si.maxDepth {
			si.splitNode(node)
		}
	} else {
		// Find appropriate child
		for _, child := range node.children {
			if child != nil && child.bounds.Contains(x, y) {
				si.insertObject(child, objectID, x, y)
				break
			}
		}
	}
}

// splitNode splits a leaf node into four children
func (si *SpatialIndex) splitNode(node *QuadNode) {
	if !node.isLeaf {
		return
	}

	// Calculate child bounds
	midX := (node.bounds.MinX + node.bounds.MaxX) / 2
	midY := (node.bounds.MinY + node.bounds.MaxY) / 2

	node.children[0] = &QuadNode{ // Top-left
		bounds: BoundingBox{MinX: node.bounds.MinX, MinY: midY, MaxX: midX, MaxY: node.bounds.MaxY},
		depth:  node.depth + 1,
		isLeaf: true,
	}
	node.children[1] = &QuadNode{ // Top-right
		bounds: BoundingBox{MinX: midX, MinY: midY, MaxX: node.bounds.MaxX, MaxY: node.bounds.MaxY},
		depth:  node.depth + 1,
		isLeaf: true,
	}
	node.children[2] = &QuadNode{ // Bottom-left
		bounds: BoundingBox{MinX: node.bounds.MinX, MinY: node.bounds.MinY, MaxX: midX, MaxY: midY},
		depth:  node.depth + 1,
		isLeaf: true,
	}
	node.children[3] = &QuadNode{ // Bottom-right
		bounds: BoundingBox{MinX: midX, MinY: node.bounds.MinY, MaxX: node.bounds.MaxX, MaxY: midY},
		depth:  node.depth + 1,
		isLeaf: true,
	}

	// Redistribute objects to children
	for _, objectID := range node.objects {
		// Find object coordinates (simplified - in practice, you'd store these)
		// For now, we'll just distribute randomly
		for _, child := range node.children {
			if child != nil {
				child.objects = append(child.objects, objectID)
				break
			}
		}
	}

	// Clear parent objects and mark as non-leaf
	node.objects = nil
	node.isLeaf = false
}

// query performs a spatial query on the quadtree
func (si *SpatialIndex) query(node *QuadNode, bounds BoundingBox, results *[]string) {
	if node == nil || !node.bounds.Intersects(bounds) {
		return
	}

	if node.isLeaf {
		// Add all objects in this leaf
		*results = append(*results, node.objects...)
	} else {
		// Query children
		for _, child := range node.children {
			if child != nil {
				si.query(child, bounds, results)
			}
		}
	}
}

// ArxObject represents the minimal interface needed for spatial indexing
// This will be replaced with the actual ArxObject interface when available
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

// Clear clears the spatial index
func (si *SpatialIndex) Clear() {
	si.root = nil
	si.objects = make(map[string]ArxObject)
}

// Insert inserts a single ArxObject into the spatial index
func (si *SpatialIndex) Insert(obj ArxObject) {
	fmt.Printf("Debug: Insert called for object %s\n", obj.GetID())

	coordinates := obj.GetCoordinates()
	if len(coordinates) == 0 {
		fmt.Printf("Debug: Object has no coordinates, skipping\n")
		return
	}

	if si.root == nil {
		fmt.Printf("Debug: Creating root node for object %s\n", obj.GetID())
		// Create root node if it doesn't exist
		coord := coordinates[0]
		bounds := BoundingBox{
			MinX: coord.X - 1000000, // 1mm buffer
			MinY: coord.Y - 1000000,
			MaxX: coord.X + 1000000,
			MaxY: coord.Y + 1000000,
		}
		si.root = &QuadNode{
			bounds: bounds,
			depth:  0,
			isLeaf: true,
		}
		fmt.Printf("Debug: Root node created with bounds (%d, %d) to (%d, %d)\n", bounds.MinX, bounds.MinY, bounds.MaxX, bounds.MaxY)
	}

	fmt.Printf("Debug: Inserting object %s at coordinates (%d, %d)\n", obj.GetID(), coordinates[0].X, coordinates[0].Y)
	si.insertObject(si.root, obj.GetID(), coordinates[0].X, coordinates[0].Y)
	si.objects[obj.GetID()] = obj // Add to lookup map
	fmt.Printf("Debug: Object %s added to lookup map\n", obj.GetID())
}

// QueryNearby finds objects within a radius of a given ArxObject
func (si *SpatialIndex) QueryNearby(obj ArxObject, radius float64) []ArxObject {
	fmt.Printf("Debug: QueryNearby called for object %s with radius %f\n", obj.GetID(), radius)

	if si.root == nil {
		fmt.Printf("Debug: Spatial index root is nil\n")
		return []ArxObject{}
	}

	coordinates := obj.GetCoordinates()
	if len(coordinates) == 0 {
		fmt.Printf("Debug: Object has no coordinates\n")
		return []ArxObject{}
	}

	// Convert radius from mm to nm
	radiusNano := int64(radius * 1e6)
	coord := coordinates[0]
	fmt.Printf("Debug: Search center at (%d, %d) with radius %d nm\n", coord.X, coord.Y, radiusNano)

	searchBounds := BoundingBox{
		MinX: coord.X - radiusNano,
		MinY: coord.Y - radiusNano,
		MaxX: coord.X + radiusNano,
		MaxY: coord.Y + radiusNano,
	}
	fmt.Printf("Debug: Search bounds: (%d, %d) to (%d, %d)\n", searchBounds.MinX, searchBounds.MinY, searchBounds.MaxX, searchBounds.MaxY)

	var results []string
	si.query(si.root, searchBounds, &results)
	fmt.Printf("Debug: Query returned %d object IDs: %v\n", len(results), results)

	// Convert back to ArxObjects using the lookup map
	var objects []ArxObject
	for _, id := range results {
		// Look up the actual object by ID (now using original string IDs)
		if obj, exists := si.objects[id]; exists {
			objects = append(objects, obj)
		} else {
			fmt.Printf("Debug: Object with ID %s not found in lookup map\n", id)
		}
	}

	fmt.Printf("Debug: Returning %d objects\n", len(objects))
	return objects
}
