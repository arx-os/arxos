// Package websocket provides octree spatial indexing
package websocket

import (
	"sync"
	
	"github.com/arxos/arxos/core/internal/arxobject"
)

// Octree provides spatial indexing for 3D objects
type Octree struct {
	mu           sync.RWMutex
	root         *OctreeNode
	maxDepth     int
	maxObjects   int
	nodeCount    int
}

// OctreeNode represents a node in the octree
type OctreeNode struct {
	Bounds   Bounds
	Objects  []*arxobject.ArxObjectUnified
	Children [8]*OctreeNode  // 8 octants
	Depth    int
}

// NewOctree creates a new octree
func NewOctree(bounds Bounds) *Octree {
	return &Octree{
		root: &OctreeNode{
			Bounds:  bounds,
			Objects: []*arxobject.ArxObjectUnified{},
			Depth:   0,
		},
		maxDepth:   10,  // Maximum tree depth
		maxObjects: 10,  // Objects per node before subdivision
		nodeCount:  1,
	}
}

// Insert adds an object to the octree
func (t *Octree) Insert(obj *arxobject.ArxObjectUnified) {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	t.insertNode(t.root, obj)
}

// insertNode recursively inserts an object
func (t *Octree) insertNode(node *OctreeNode, obj *arxobject.ArxObjectUnified) {
	// Check if object fits in this node
	if !t.fitsInBounds(obj, node.Bounds) {
		// Object doesn't fit, add to this node
		node.Objects = append(node.Objects, obj)
		return
	}
	
	// If node has children, insert into appropriate child
	if node.Children[0] != nil {
		index := t.getOctant(obj, node.Bounds)
		if index >= 0 {
			t.insertNode(node.Children[index], obj)
		} else {
			// Object spans multiple octants
			node.Objects = append(node.Objects, obj)
		}
		return
	}
	
	// Add to this node
	node.Objects = append(node.Objects, obj)
	
	// Subdivide if needed
	if len(node.Objects) > t.maxObjects && node.Depth < t.maxDepth {
		t.subdivide(node)
	}
}

// Remove removes an object from the octree
func (t *Octree) Remove(obj *arxobject.ArxObjectUnified) {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	t.removeNode(t.root, obj)
}

// removeNode recursively removes an object
func (t *Octree) removeNode(node *OctreeNode, obj *arxobject.ArxObjectUnified) bool {
	// Check this node's objects
	for i, o := range node.Objects {
		if o.ID == obj.ID {
			// Remove object
			node.Objects = append(node.Objects[:i], node.Objects[i+1:]...)
			return true
		}
	}
	
	// Check children if they exist
	if node.Children[0] != nil {
		for _, child := range node.Children {
			if child != nil && t.removeNode(child, obj) {
				return true
			}
		}
	}
	
	return false
}

// Query returns all objects within bounds
func (t *Octree) Query(bounds Bounds) []*arxobject.ArxObjectUnified {
	t.mu.RLock()
	defer t.mu.RUnlock()
	
	results := []*arxobject.ArxObjectUnified{}
	t.queryNode(t.root, bounds, &results)
	return results
}

// queryNode recursively queries for objects
func (t *Octree) queryNode(node *OctreeNode, bounds Bounds, results *[]*arxobject.ArxObjectUnified) {
	// Check if node intersects query bounds
	if !t.boundsIntersect(node.Bounds, bounds) {
		return
	}
	
	// Add objects in this node
	for _, obj := range node.Objects {
		if t.objectInBounds(obj, bounds) {
			*results = append(*results, obj)
		}
	}
	
	// Query children
	if node.Children[0] != nil {
		for _, child := range node.Children {
			if child != nil {
				t.queryNode(child, bounds, results)
			}
		}
	}
}

// subdivide creates child nodes
func (t *Octree) subdivide(node *OctreeNode) {
	center := t.getCenter(node.Bounds)
	
	// Create 8 child octants
	for i := 0; i < 8; i++ {
		childBounds := t.getOctantBounds(node.Bounds, center, i)
		node.Children[i] = &OctreeNode{
			Bounds:  childBounds,
			Objects: []*arxobject.ArxObjectUnified{},
			Depth:   node.Depth + 1,
		}
		t.nodeCount++
	}
	
	// Redistribute objects
	remainingObjects := []*arxobject.ArxObjectUnified{}
	
	for _, obj := range node.Objects {
		index := t.getOctant(obj, node.Bounds)
		if index >= 0 {
			node.Children[index].Objects = append(node.Children[index].Objects, obj)
		} else {
			// Object spans multiple octants
			remainingObjects = append(remainingObjects, obj)
		}
	}
	
	node.Objects = remainingObjects
}

// getOctant determines which octant an object belongs to
func (t *Octree) getOctant(obj *arxobject.ArxObjectUnified, bounds Bounds) int {
	center := t.getCenter(bounds)
	bbox := obj.Geometry.BoundingBox
	
	// Check if object fits entirely in an octant
	xMin := bbox.Min.X >= center.X
	xMax := bbox.Max.X < center.X
	yMin := bbox.Min.Y >= center.Y
	yMax := bbox.Max.Y < center.Y
	zMin := bbox.Min.Z >= center.Z
	zMax := bbox.Max.Z < center.Z
	
	// Octant numbering:
	// 0: -X, -Y, -Z
	// 1: +X, -Y, -Z
	// 2: -X, +Y, -Z
	// 3: +X, +Y, -Z
	// 4: -X, -Y, +Z
	// 5: +X, -Y, +Z
	// 6: -X, +Y, +Z
	// 7: +X, +Y, +Z
	
	if xMax && yMax && zMax {
		return 0
	} else if xMin && yMax && zMax {
		return 1
	} else if xMax && yMin && zMax {
		return 2
	} else if xMin && yMin && zMax {
		return 3
	} else if xMax && yMax && zMin {
		return 4
	} else if xMin && yMax && zMin {
		return 5
	} else if xMax && yMin && zMin {
		return 6
	} else if xMin && yMin && zMin {
		return 7
	}
	
	// Object spans multiple octants
	return -1
}

// getOctantBounds calculates bounds for an octant
func (t *Octree) getOctantBounds(parent Bounds, center arxobject.Point3D, index int) Bounds {
	child := Bounds{}
	
	// Set bounds based on octant index
	if index&1 != 0 { // +X
		child.Min.X = center.X
		child.Max.X = parent.Max.X
	} else { // -X
		child.Min.X = parent.Min.X
		child.Max.X = center.X
	}
	
	if index&2 != 0 { // +Y
		child.Min.Y = center.Y
		child.Max.Y = parent.Max.Y
	} else { // -Y
		child.Min.Y = parent.Min.Y
		child.Max.Y = center.Y
	}
	
	if index&4 != 0 { // +Z
		child.Min.Z = center.Z
		child.Max.Z = parent.Max.Z
	} else { // -Z
		child.Min.Z = parent.Min.Z
		child.Max.Z = center.Z
	}
	
	return child
}

// getCenter calculates center of bounds
func (t *Octree) getCenter(bounds Bounds) arxobject.Point3D {
	return arxobject.Point3D{
		X: (bounds.Min.X + bounds.Max.X) / 2,
		Y: (bounds.Min.Y + bounds.Max.Y) / 2,
		Z: (bounds.Min.Z + bounds.Max.Z) / 2,
	}
}

// fitsInBounds checks if object fits entirely in bounds
func (t *Octree) fitsInBounds(obj *arxobject.ArxObjectUnified, bounds Bounds) bool {
	bbox := obj.Geometry.BoundingBox
	return bbox.Min.X >= bounds.Min.X && bbox.Max.X <= bounds.Max.X &&
		bbox.Min.Y >= bounds.Min.Y && bbox.Max.Y <= bounds.Max.Y &&
		bbox.Min.Z >= bounds.Min.Z && bbox.Max.Z <= bounds.Max.Z
}

// objectInBounds checks if object intersects bounds
func (t *Octree) objectInBounds(obj *arxobject.ArxObjectUnified, bounds Bounds) bool {
	bbox := obj.Geometry.BoundingBox
	return !(bbox.Max.X < bounds.Min.X || bbox.Min.X > bounds.Max.X ||
		bbox.Max.Y < bounds.Min.Y || bbox.Min.Y > bounds.Max.Y ||
		bbox.Max.Z < bounds.Min.Z || bbox.Min.Z > bounds.Max.Z)
}

// boundsIntersect checks if two bounds intersect
func (t *Octree) boundsIntersect(a, b Bounds) bool {
	return !(a.Max.X < b.Min.X || a.Min.X > b.Max.X ||
		a.Max.Y < b.Min.Y || a.Min.Y > b.Max.Y ||
		a.Max.Z < b.Min.Z || a.Min.Z > b.Max.Z)
}

// Clear removes all objects from the octree
func (t *Octree) Clear() {
	t.mu.Lock()
	defer t.mu.Unlock()
	
	t.root = &OctreeNode{
		Bounds:  t.root.Bounds,
		Objects: []*arxobject.ArxObjectUnified{},
		Depth:   0,
	}
	t.nodeCount = 1
}

// NodeCount returns the number of nodes
func (t *Octree) NodeCount() int {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return t.nodeCount
}

// ObjectCount returns the total number of objects
func (t *Octree) ObjectCount() int {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return t.countObjects(t.root)
}

// countObjects recursively counts objects
func (t *Octree) countObjects(node *OctreeNode) int {
	count := len(node.Objects)
	
	if node.Children[0] != nil {
		for _, child := range node.Children {
			if child != nil {
				count += t.countObjects(child)
			}
		}
	}
	
	return count
}

// GetDepth returns the current tree depth
func (t *Octree) GetDepth() int {
	t.mu.RLock()
	defer t.mu.RUnlock()
	return t.getNodeDepth(t.root)
}

// getNodeDepth recursively finds maximum depth
func (t *Octree) getNodeDepth(node *OctreeNode) int {
	if node.Children[0] == nil {
		return node.Depth
	}
	
	maxDepth := node.Depth
	for _, child := range node.Children {
		if child != nil {
			depth := t.getNodeDepth(child)
			if depth > maxDepth {
				maxDepth = depth
			}
		}
	}
	
	return maxDepth
}

// RayQuery performs ray-octree intersection
func (t *Octree) RayQuery(origin, direction arxobject.Point3D) []*arxobject.ArxObjectUnified {
	t.mu.RLock()
	defer t.mu.RUnlock()
	
	results := []*arxobject.ArxObjectUnified{}
	t.rayQueryNode(t.root, origin, direction, &results)
	return results
}

// rayQueryNode recursively performs ray query
func (t *Octree) rayQueryNode(node *OctreeNode, origin, direction arxobject.Point3D, results *[]*arxobject.ArxObjectUnified) {
	// Check if ray intersects node bounds
	if !t.rayIntersectsBounds(origin, direction, node.Bounds) {
		return
	}
	
	// Check objects in this node
	for _, obj := range node.Objects {
		if t.rayIntersectsObject(origin, direction, obj) {
			*results = append(*results, obj)
		}
	}
	
	// Check children
	if node.Children[0] != nil {
		for _, child := range node.Children {
			if child != nil {
				t.rayQueryNode(child, origin, direction, results)
			}
		}
	}
}

// rayIntersectsBounds checks ray-AABB intersection
func (t *Octree) rayIntersectsBounds(origin, direction arxobject.Point3D, bounds Bounds) bool {
	// Simple ray-AABB intersection
	tMin := float64(bounds.Min.X - origin.X) / float64(direction.X)
	tMax := float64(bounds.Max.X - origin.X) / float64(direction.X)
	
	if tMin > tMax {
		tMin, tMax = tMax, tMin
	}
	
	tyMin := float64(bounds.Min.Y - origin.Y) / float64(direction.Y)
	tyMax := float64(bounds.Max.Y - origin.Y) / float64(direction.Y)
	
	if tyMin > tyMax {
		tyMin, tyMax = tyMax, tyMin
	}
	
	if tMin > tyMax || tyMin > tMax {
		return false
	}
	
	if tyMin > tMin {
		tMin = tyMin
	}
	if tyMax < tMax {
		tMax = tyMax
	}
	
	tzMin := float64(bounds.Min.Z - origin.Z) / float64(direction.Z)
	tzMax := float64(bounds.Max.Z - origin.Z) / float64(direction.Z)
	
	if tzMin > tzMax {
		tzMin, tzMax = tzMax, tzMin
	}
	
	if tMin > tzMax || tzMin > tMax {
		return false
	}
	
	return true
}

// rayIntersectsObject checks ray-object intersection
func (t *Octree) rayIntersectsObject(origin, direction arxobject.Point3D, obj *arxobject.ArxObjectUnified) bool {
	// Use bounding box for now
	return t.rayIntersectsBounds(origin, direction, Bounds{
		Min: obj.Geometry.BoundingBox.Min,
		Max: obj.Geometry.BoundingBox.Max,
	})
}

// SphereQuery returns objects within sphere
func (t *Octree) SphereQuery(center arxobject.Point3D, radius int64) []*arxobject.ArxObjectUnified {
	t.mu.RLock()
	defer t.mu.RUnlock()
	
	// Convert sphere to AABB for initial query
	bounds := Bounds{
		Min: arxobject.Point3D{
			X: center.X - radius,
			Y: center.Y - radius,
			Z: center.Z - radius,
		},
		Max: arxobject.Point3D{
			X: center.X + radius,
			Y: center.Y + radius,
			Z: center.Z + radius,
		},
	}
	
	// Get candidates
	candidates := []*arxobject.ArxObjectUnified{}
	t.queryNode(t.root, bounds, &candidates)
	
	// Filter by actual sphere distance
	results := []*arxobject.ArxObjectUnified{}
	radiusSq := radius * radius
	
	for _, obj := range candidates {
		// Check distance to object center
		dx := obj.Geometry.Position.X - center.X
		dy := obj.Geometry.Position.Y - center.Y
		dz := obj.Geometry.Position.Z - center.Z
		distSq := dx*dx + dy*dy + dz*dz
		
		if distSq <= radiusSq {
			results = append(results, obj)
		}
	}
	
	return results
}