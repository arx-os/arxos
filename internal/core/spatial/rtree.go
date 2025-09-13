package spatial

import (
	"math"
	"sort"
	
	"github.com/joelpate/arxos/internal/common/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// RTree implements an R-tree spatial index for efficient proximity searches
type RTree struct {
	root     *Node
	maxItems int
	minItems int
}

// Node represents a node in the R-tree
type Node struct {
	BBox     BoundingBox
	Items    []Item
	Children []*Node
	IsLeaf   bool
}

// Item represents an indexed equipment item
type Item struct {
	ID       string
	Location models.Point
	BBox     BoundingBox
	Data     interface{} // Can store equipment pointer
}

// BoundingBox represents a rectangular region
type BoundingBox struct {
	MinX, MinY, MaxX, MaxY float64
}

// NewRTree creates a new R-tree spatial index
func NewRTree(maxItems int) *RTree {
	if maxItems < 4 {
		maxItems = 9 // Default max items per node
	}
	
	return &RTree{
		root: &Node{
			IsLeaf: true,
			Items:  []Item{},
		},
		maxItems: maxItems,
		minItems: maxItems / 2,
	}
}

// Insert adds an item to the R-tree
func (rt *RTree) Insert(id string, x, y float64, data interface{}) {
	item := Item{
		ID:       id,
		Location: models.Point{X: x, Y: y},
		BBox:     BoundingBox{MinX: x, MinY: y, MaxX: x, MaxY: y},
		Data:     data,
	}
	
	leaf := rt.chooseLeaf(rt.root, item)
	leaf.Items = append(leaf.Items, item)
	
	if len(leaf.Items) > rt.maxItems {
		rt.split(leaf)
	}
	
	rt.adjustBounds(leaf)
}

// Search finds all items within a bounding box
func (rt *RTree) Search(minX, minY, maxX, maxY float64) []Item {
	searchBox := BoundingBox{MinX: minX, MinY: minY, MaxX: maxX, MaxY: maxY}
	results := []Item{}
	rt.searchNode(rt.root, searchBox, &results)
	return results
}

// NearestNeighbors finds k nearest neighbors to a point
func (rt *RTree) NearestNeighbors(x, y float64, k int) []Item {
	point := models.Point{X: x, Y: y}
	
	// Priority queue for nearest neighbor search
	queue := &PriorityQueue{}
	queue.Push(&QueueItem{Node: rt.root, Distance: 0})
	
	results := []Item{}
	maxDist := math.Inf(1)
	
	for queue.Len() > 0 && len(results) < k {
		current := queue.Pop()
		
		if current.Distance > maxDist {
			continue
		}
		
		if current.Node.IsLeaf {
			// Process leaf node items
			for _, item := range current.Node.Items {
				dist := distance(point, item.Location)
				if dist < maxDist {
					results = append(results, item)
					
					// Sort and trim results
					sort.Slice(results, func(i, j int) bool {
						di := distance(point, results[i].Location)
						dj := distance(point, results[j].Location)
						return di < dj
					})
					
					if len(results) > k {
						results = results[:k]
					}
					
					if len(results) == k {
						maxDist = distance(point, results[k-1].Location)
					}
				}
			}
		} else {
			// Process internal node children
			for _, child := range current.Node.Children {
				dist := distanceToBBox(point, child.BBox)
				if dist < maxDist {
					queue.Push(&QueueItem{Node: child, Distance: dist})
				}
			}
		}
	}
	
	return results
}

// FindWithinRadius finds all items within a given radius of a point
func (rt *RTree) FindWithinRadius(x, y, radius float64) []Item {
	// Search bounding box
	minX := x - radius
	minY := y - radius
	maxX := x + radius
	maxY := y + radius
	
	candidates := rt.Search(minX, minY, maxX, maxY)
	
	// Filter by actual distance
	point := models.Point{X: x, Y: y}
	results := []Item{}
	
	for _, item := range candidates {
		if distance(point, item.Location) <= radius {
			results = append(results, item)
		}
	}
	
	return results
}

// Delete removes an item from the R-tree
func (rt *RTree) Delete(id string) bool {
	return rt.deleteFromNode(rt.root, id)
}

// GetStatistics returns tree statistics for performance monitoring
func (rt *RTree) GetStatistics() TreeStats {
	stats := TreeStats{}
	rt.calculateStats(rt.root, 0, &stats)
	return stats
}

// TreeStats contains R-tree statistics
type TreeStats struct {
	TotalNodes   int
	TotalItems   int
	TreeHeight   int
	LeafNodes    int
	AverageItems float64
	MinItems     int
	MaxItems     int
}

// Internal methods

func (rt *RTree) chooseLeaf(node *Node, item Item) *Node {
	if node.IsLeaf {
		return node
	}
	
	// Choose child with minimum enlargement
	minEnlargement := math.Inf(1)
	var bestChild *Node
	
	for _, child := range node.Children {
		enlargement := calculateEnlargement(child.BBox, item.BBox)
		if enlargement < minEnlargement {
			minEnlargement = enlargement
			bestChild = child
		}
	}
	
	return rt.chooseLeaf(bestChild, item)
}

func (rt *RTree) split(node *Node) {
	if !node.IsLeaf {
		return // Only split leaf nodes in this implementation
	}
	
	// Quadratic split algorithm
	seed1, seed2 := rt.pickSeeds(node.Items)
	
	group1 := []Item{node.Items[seed1]}
	group2 := []Item{node.Items[seed2]}
	
	bbox1 := node.Items[seed1].BBox
	bbox2 := node.Items[seed2].BBox
	
	// Distribute remaining items
	for i, item := range node.Items {
		if i == seed1 || i == seed2 {
			continue
		}
		
		enlargement1 := calculateEnlargement(bbox1, item.BBox)
		enlargement2 := calculateEnlargement(bbox2, item.BBox)
		
		if enlargement1 < enlargement2 {
			group1 = append(group1, item)
			bbox1 = combineBounds(bbox1, item.BBox)
		} else {
			group2 = append(group2, item)
			bbox2 = combineBounds(bbox2, item.BBox)
		}
	}
	
	// Update current node with group1
	node.Items = group1
	node.BBox = bbox1
	
	// Create new node with group2
	newNode := &Node{
		IsLeaf: true,
		Items:  group2,
		BBox:   bbox2,
	}
	
	// If this is root, create new root
	if node == rt.root {
		newRoot := &Node{
			IsLeaf:   false,
			Children: []*Node{node, newNode},
			BBox:     combineBounds(bbox1, bbox2),
		}
		rt.root = newRoot
	}
}

func (rt *RTree) pickSeeds(items []Item) (int, int) {
	maxWaste := -1.0
	seed1, seed2 := 0, 1
	
	for i := 0; i < len(items); i++ {
		for j := i + 1; j < len(items); j++ {
			combined := combineBounds(items[i].BBox, items[j].BBox)
			waste := area(combined) - area(items[i].BBox) - area(items[j].BBox)
			
			if waste > maxWaste {
				maxWaste = waste
				seed1 = i
				seed2 = j
			}
		}
	}
	
	return seed1, seed2
}

func (rt *RTree) adjustBounds(node *Node) {
	if node.IsLeaf {
		// Recalculate bounds from items
		if len(node.Items) > 0 {
			node.BBox = node.Items[0].BBox
			for i := 1; i < len(node.Items); i++ {
				node.BBox = combineBounds(node.BBox, node.Items[i].BBox)
			}
		}
	} else {
		// Recalculate bounds from children
		if len(node.Children) > 0 {
			node.BBox = node.Children[0].BBox
			for i := 1; i < len(node.Children); i++ {
				node.BBox = combineBounds(node.BBox, node.Children[i].BBox)
			}
		}
	}
}

func (rt *RTree) searchNode(node *Node, searchBox BoundingBox, results *[]Item) {
	if !intersects(node.BBox, searchBox) {
		return
	}
	
	if node.IsLeaf {
		for _, item := range node.Items {
			if intersects(item.BBox, searchBox) {
				*results = append(*results, item)
			}
		}
	} else {
		for _, child := range node.Children {
			rt.searchNode(child, searchBox, results)
		}
	}
}

func (rt *RTree) deleteFromNode(node *Node, id string) bool {
	if node.IsLeaf {
		for i, item := range node.Items {
			if item.ID == id {
				// Remove item
				node.Items = append(node.Items[:i], node.Items[i+1:]...)
				rt.adjustBounds(node)
				return true
			}
		}
	} else {
		for _, child := range node.Children {
			if rt.deleteFromNode(child, id) {
				rt.adjustBounds(node)
				return true
			}
		}
	}
	return false
}

func (rt *RTree) calculateStats(node *Node, depth int, stats *TreeStats) {
	stats.TotalNodes++
	
	if depth > stats.TreeHeight {
		stats.TreeHeight = depth
	}
	
	if node.IsLeaf {
		stats.LeafNodes++
		stats.TotalItems += len(node.Items)
		
		if stats.MinItems == 0 || len(node.Items) < stats.MinItems {
			stats.MinItems = len(node.Items)
		}
		if len(node.Items) > stats.MaxItems {
			stats.MaxItems = len(node.Items)
		}
	} else {
		for _, child := range node.Children {
			rt.calculateStats(child, depth+1, stats)
		}
	}
	
	if stats.LeafNodes > 0 {
		stats.AverageItems = float64(stats.TotalItems) / float64(stats.LeafNodes)
	}
}

// Utility functions

func intersects(a, b BoundingBox) bool {
	return a.MinX <= b.MaxX && a.MaxX >= b.MinX &&
		a.MinY <= b.MaxY && a.MaxY >= b.MinY
}

func combineBounds(a, b BoundingBox) BoundingBox {
	return BoundingBox{
		MinX: math.Min(a.MinX, b.MinX),
		MinY: math.Min(a.MinY, b.MinY),
		MaxX: math.Max(a.MaxX, b.MaxX),
		MaxY: math.Max(a.MaxY, b.MaxY),
	}
}

func area(bbox BoundingBox) float64 {
	return (bbox.MaxX - bbox.MinX) * (bbox.MaxY - bbox.MinY)
}

func calculateEnlargement(bbox, itemBBox BoundingBox) float64 {
	combined := combineBounds(bbox, itemBBox)
	return area(combined) - area(bbox)
}

func distance(p1, p2 models.Point) float64 {
	dx := p1.X - p2.X
	dy := p1.Y - p2.Y
	return math.Sqrt(dx*dx + dy*dy)
}

func distanceToBBox(point models.Point, bbox BoundingBox) float64 {
	dx := math.Max(math.Max(bbox.MinX-point.X, 0), point.X-bbox.MaxX)
	dy := math.Max(math.Max(bbox.MinY-point.Y, 0), point.Y-bbox.MaxY)
	return math.Sqrt(dx*dx + dy*dy)
}

// PriorityQueue for nearest neighbor search
type QueueItem struct {
	Node     *Node
	Distance float64
}

type PriorityQueue []*QueueItem

func (pq PriorityQueue) Len() int           { return len(pq) }
func (pq PriorityQueue) Less(i, j int) bool { return pq[i].Distance < pq[j].Distance }
func (pq PriorityQueue) Swap(i, j int)      { pq[i], pq[j] = pq[j], pq[i] }

func (pq *PriorityQueue) Push(item *QueueItem) {
	*pq = append(*pq, item)
	sort.Sort(pq)
}

func (pq *PriorityQueue) Pop() *QueueItem {
	if len(*pq) == 0 {
		return nil
	}
	item := (*pq)[0]
	*pq = (*pq)[1:]
	return item
}

// SpatialIndex provides high-level spatial indexing for building data
type SpatialIndex struct {
	equipmentTree *RTree
	roomTree      *RTree
}

// NewSpatialIndex creates a new spatial index for building data
func NewSpatialIndex() *SpatialIndex {
	return &SpatialIndex{
		equipmentTree: NewRTree(9),
		roomTree:      NewRTree(9),
	}
}

// IndexEquipment adds equipment to the spatial index
func (si *SpatialIndex) IndexEquipment(equipment []models.Equipment) {
	for i := range equipment {
		eq := &equipment[i]
		si.equipmentTree.Insert(eq.ID, eq.Location.X, eq.Location.Y, eq)
	}
	
	logger.Info("Indexed %d equipment items in R-tree", len(equipment))
}

// IndexRooms adds rooms to the spatial index
func (si *SpatialIndex) IndexRooms(rooms []models.Room) {
	for i := range rooms {
		room := &rooms[i]
		centerX := (room.Bounds.MinX + room.Bounds.MaxX) / 2
		centerY := (room.Bounds.MinY + room.Bounds.MaxY) / 2
		si.roomTree.Insert(room.ID, centerX, centerY, room)
	}
	
	logger.Info("Indexed %d rooms in R-tree", len(rooms))
}

// FindNearbyEquipment finds equipment within radius of a point
func (si *SpatialIndex) FindNearbyEquipment(x, y, radius float64) []*models.Equipment {
	items := si.equipmentTree.FindWithinRadius(x, y, radius)
	
	results := make([]*models.Equipment, len(items))
	for i, item := range items {
		results[i] = item.Data.(*models.Equipment)
	}
	
	return results
}

// FindNearestEquipment finds k nearest equipment to a point
func (si *SpatialIndex) FindNearestEquipment(x, y float64, k int) []*models.Equipment {
	items := si.equipmentTree.NearestNeighbors(x, y, k)
	
	results := make([]*models.Equipment, len(items))
	for i, item := range items {
		results[i] = item.Data.(*models.Equipment)
	}
	
	return results
}

// FindEquipmentInArea finds all equipment in a rectangular area
func (si *SpatialIndex) FindEquipmentInArea(minX, minY, maxX, maxY float64) []*models.Equipment {
	items := si.equipmentTree.Search(minX, minY, maxX, maxY)
	
	results := make([]*models.Equipment, len(items))
	for i, item := range items {
		results[i] = item.Data.(*models.Equipment)
	}
	
	return results
}

// GetStatistics returns spatial index statistics
func (si *SpatialIndex) GetStatistics() map[string]TreeStats {
	return map[string]TreeStats{
		"equipment": si.equipmentTree.GetStatistics(),
		"rooms":     si.roomTree.GetStatistics(),
	}
}