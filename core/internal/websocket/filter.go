// Package websocket provides precision-based data filtering
package websocket

import (
	"math"
	"sort"
	
	"github.com/arxos/arxos/core/internal/arxobject"
)

// DataFilter handles precision-based filtering and LOD
type DataFilter struct {
	precisionThresholds map[Precision]FilterConfig
}

// FilterConfig defines filtering parameters for each precision level
type FilterConfig struct {
	MaxPoints       int     // Maximum points in point cloud
	MaxVertices     int     // Maximum vertices in mesh
	MaxProperties   int     // Maximum properties to send
	SimplifyFactor  float64 // Geometry simplification factor
	UpdateRate      float64 // Updates per second
	DataResolution  float64 // Data resolution in meters
}

// NewDataFilter creates a new data filter
func NewDataFilter() *DataFilter {
	return &DataFilter{
		precisionThresholds: map[Precision]FilterConfig{
			PrecisionMeter: {
				MaxPoints:      100,
				MaxVertices:    50,
				MaxProperties:  5,
				SimplifyFactor: 0.1,
				UpdateRate:     1.0,
				DataResolution: 1.0,
			},
			PrecisionDecimeter: {
				MaxPoints:      500,
				MaxVertices:    200,
				MaxProperties:  10,
				SimplifyFactor: 0.3,
				UpdateRate:     5.0,
				DataResolution: 0.1,
			},
			PrecisionCentimeter: {
				MaxPoints:      2000,
				MaxVertices:    1000,
				MaxProperties:  20,
				SimplifyFactor: 0.5,
				UpdateRate:     10.0,
				DataResolution: 0.01,
			},
			PrecisionMillimeter: {
				MaxPoints:      10000,
				MaxVertices:    5000,
				MaxProperties:  50,
				SimplifyFactor: 0.7,
				UpdateRate:     30.0,
				DataResolution: 0.001,
			},
			Precision100Micrometer: {
				MaxPoints:      50000,
				MaxVertices:    20000,
				MaxProperties:  100,
				SimplifyFactor: 0.85,
				UpdateRate:     60.0,
				DataResolution: 0.0001,
			},
			Precision10Micrometer: {
				MaxPoints:      100000,
				MaxVertices:    50000,
				MaxProperties:  200,
				SimplifyFactor: 0.9,
				UpdateRate:     120.0,
				DataResolution: 0.00001,
			},
			PrecisionMicrometer: {
				MaxPoints:      500000,
				MaxVertices:    200000,
				MaxProperties:  500,
				SimplifyFactor: 0.95,
				UpdateRate:     240.0,
				DataResolution: 0.000001,
			},
			Precision100Nanometer: {
				MaxPoints:      1000000,
				MaxVertices:    500000,
				MaxProperties:  1000,
				SimplifyFactor: 0.98,
				UpdateRate:     480.0,
				DataResolution: 0.0000001,
			},
			Precision10Nanometer: {
				MaxPoints:      5000000,
				MaxVertices:    2000000,
				MaxProperties:  2000,
				SimplifyFactor: 0.99,
				UpdateRate:     960.0,
				DataResolution: 0.00000001,
			},
			PrecisionNanometer: {
				MaxPoints:      10000000,
				MaxVertices:    5000000,
				MaxProperties:  -1, // No limit
				SimplifyFactor: 1.0,
				UpdateRate:     1920.0,
				DataResolution: 0.000000001,
			},
		},
	}
}

// FilterObject applies precision-based filtering to an object
func (f *DataFilter) FilterObject(obj *arxobject.ArxObjectUnified, precision Precision) *arxobject.ArxObjectUnified {
	config := f.precisionThresholds[precision]
	
	// Clone object to avoid modifying original
	filtered := obj.Clone()
	
	// Apply geometry filtering
	f.filterGeometry(&filtered.Geometry, config)
	
	// Apply property filtering
	f.filterProperties(filtered.Properties, config)
	
	// Apply relationship filtering
	filtered.Relationships = f.filterRelationships(filtered.Relationships, config)
	
	return filtered
}

// filterGeometry applies geometry simplification
func (f *DataFilter) filterGeometry(geom *arxobject.Geometry, config FilterConfig) {
	// Simplify point cloud
	if len(geom.Points) > config.MaxPoints {
		geom.Points = f.decimatePoints(geom.Points, config.MaxPoints)
	}
	
	// Simplify mesh
	if len(geom.Vertices) > config.MaxVertices {
		geom.Vertices, geom.Faces = f.simplifyMesh(
			geom.Vertices,
			geom.Faces,
			config.MaxVertices,
			config.SimplifyFactor,
		)
	}
	
	// Quantize coordinates based on resolution
	f.quantizeGeometry(geom, config.DataResolution)
}

// decimatePoints reduces point cloud density
func (f *DataFilter) decimatePoints(points []arxobject.Point3D, maxPoints int) []arxobject.Point3D {
	if len(points) <= maxPoints {
		return points
	}
	
	// Use spatial decimation
	decimated := make([]arxobject.Point3D, 0, maxPoints)
	stride := len(points) / maxPoints
	
	for i := 0; i < len(points); i += stride {
		decimated = append(decimated, points[i])
	}
	
	return decimated
}

// simplifyMesh reduces mesh complexity using quadric error metrics
func (f *DataFilter) simplifyMesh(vertices []arxobject.Point3D, faces [][]int, maxVerts int, factor float64) ([]arxobject.Point3D, [][]int) {
	if len(vertices) <= maxVerts {
		return vertices, faces
	}
	
	// Calculate target vertex count
	targetCount := int(float64(len(vertices)) * factor)
	if targetCount < maxVerts {
		targetCount = maxVerts
	}
	
	// Build edge collapse queue
	collapses := f.buildEdgeCollapses(vertices, faces)
	
	// Perform edge collapses until target reached
	currentVerts := len(vertices)
	newVertices := make([]arxobject.Point3D, len(vertices))
	copy(newVertices, vertices)
	newFaces := make([][]int, len(faces))
	copy(newFaces, faces)
	
	for currentVerts > targetCount && len(collapses) > 0 {
		// Get cheapest collapse
		collapse := collapses[0]
		collapses = collapses[1:]
		
		// Perform collapse
		newVertices, newFaces = f.collapseEdge(
			newVertices,
			newFaces,
			collapse.v1,
			collapse.v2,
		)
		currentVerts--
	}
	
	return newVertices, newFaces
}

// EdgeCollapse represents an edge collapse operation
type EdgeCollapse struct {
	v1, v2 int     // Vertex indices
	cost   float64 // Collapse cost
	target arxobject.Point3D // Target position
}

// buildEdgeCollapses creates edge collapse queue
func (f *DataFilter) buildEdgeCollapses(vertices []arxobject.Point3D, faces [][]int) []EdgeCollapse {
	collapses := []EdgeCollapse{}
	
	// Find all edges
	edges := make(map[[2]int]bool)
	for _, face := range faces {
		for i := 0; i < len(face); i++ {
			v1 := face[i]
			v2 := face[(i+1)%len(face)]
			
			// Normalize edge (smaller index first)
			if v1 > v2 {
				v1, v2 = v2, v1
			}
			edges[[2]int{v1, v2}] = true
		}
	}
	
	// Calculate collapse cost for each edge
	for edge := range edges {
		cost := f.calculateCollapseCost(
			vertices[edge[0]],
			vertices[edge[1]],
		)
		
		collapses = append(collapses, EdgeCollapse{
			v1:   edge[0],
			v2:   edge[1],
			cost: cost,
			target: f.calculateCollapseTarget(
				vertices[edge[0]],
				vertices[edge[1]],
			),
		})
	}
	
	// Sort by cost (cheapest first)
	sort.Slice(collapses, func(i, j int) bool {
		return collapses[i].cost < collapses[j].cost
	})
	
	return collapses
}

// calculateCollapseCost computes cost of collapsing an edge
func (f *DataFilter) calculateCollapseCost(v1, v2 arxobject.Point3D) float64 {
	// Simple distance-based cost
	dx := float64(v1.X - v2.X)
	dy := float64(v1.Y - v2.Y)
	dz := float64(v1.Z - v2.Z)
	
	return math.Sqrt(dx*dx + dy*dy + dz*dz)
}

// calculateCollapseTarget computes target position for collapse
func (f *DataFilter) calculateCollapseTarget(v1, v2 arxobject.Point3D) arxobject.Point3D {
	// Midpoint for simplicity
	return arxobject.Point3D{
		X: (v1.X + v2.X) / 2,
		Y: (v1.Y + v2.Y) / 2,
		Z: (v1.Z + v2.Z) / 2,
	}
}

// collapseEdge performs an edge collapse
func (f *DataFilter) collapseEdge(vertices []arxobject.Point3D, faces [][]int, v1, v2 int) ([]arxobject.Point3D, [][]int) {
	// Move v1 to midpoint
	vertices[v1] = f.calculateCollapseTarget(vertices[v1], vertices[v2])
	
	// Update faces - replace v2 with v1
	newFaces := [][]int{}
	for _, face := range faces {
		newFace := make([]int, len(face))
		degenerate := false
		
		for i, v := range face {
			if v == v2 {
				newFace[i] = v1
			} else {
				newFace[i] = v
			}
			
			// Check for degenerate face
			for j := 0; j < i; j++ {
				if newFace[i] == newFace[j] {
					degenerate = true
					break
				}
			}
		}
		
		if !degenerate {
			newFaces = append(newFaces, newFace)
		}
	}
	
	return vertices, newFaces
}

// quantizeGeometry snaps coordinates to grid
func (f *DataFilter) quantizeGeometry(geom *arxobject.Geometry, resolution float64) {
	// Convert resolution to integer units (millimeters)
	gridSize := int64(resolution * 1000)
	if gridSize < 1 {
		gridSize = 1
	}
	
	// Quantize position
	geom.Position.X = (geom.Position.X / gridSize) * gridSize
	geom.Position.Y = (geom.Position.Y / gridSize) * gridSize
	geom.Position.Z = (geom.Position.Z / gridSize) * gridSize
	
	// Quantize bounding box
	geom.BoundingBox.Min.X = (geom.BoundingBox.Min.X / gridSize) * gridSize
	geom.BoundingBox.Min.Y = (geom.BoundingBox.Min.Y / gridSize) * gridSize
	geom.BoundingBox.Min.Z = (geom.BoundingBox.Min.Z / gridSize) * gridSize
	
	geom.BoundingBox.Max.X = ((geom.BoundingBox.Max.X + gridSize - 1) / gridSize) * gridSize
	geom.BoundingBox.Max.Y = ((geom.BoundingBox.Max.Y + gridSize - 1) / gridSize) * gridSize
	geom.BoundingBox.Max.Z = ((geom.BoundingBox.Max.Z + gridSize - 1) / gridSize) * gridSize
	
	// Quantize points
	for i := range geom.Points {
		geom.Points[i].X = (geom.Points[i].X / gridSize) * gridSize
		geom.Points[i].Y = (geom.Points[i].Y / gridSize) * gridSize
		geom.Points[i].Z = (geom.Points[i].Z / gridSize) * gridSize
	}
	
	// Quantize vertices
	for i := range geom.Vertices {
		geom.Vertices[i].X = (geom.Vertices[i].X / gridSize) * gridSize
		geom.Vertices[i].Y = (geom.Vertices[i].Y / gridSize) * gridSize
		geom.Vertices[i].Z = (geom.Vertices[i].Z / gridSize) * gridSize
	}
}

// filterProperties reduces property count
func (f *DataFilter) filterProperties(props arxobject.Properties, config FilterConfig) {
	if config.MaxProperties < 0 || len(props) <= config.MaxProperties {
		return
	}
	
	// Priority properties to keep
	priorityKeys := []string{
		"id", "name", "type", "status", "confidence",
		"material", "color", "width", "height", "depth",
		"area", "volume", "weight", "cost", "manufacturer",
	}
	
	// Keep priority properties first
	kept := 0
	filtered := make(arxobject.Properties)
	
	for _, key := range priorityKeys {
		if val, exists := props[key]; exists && kept < config.MaxProperties {
			filtered[key] = val
			kept++
		}
	}
	
	// Fill remaining with other properties
	for key, val := range props {
		if kept >= config.MaxProperties {
			break
		}
		if _, exists := filtered[key]; !exists {
			filtered[key] = val
			kept++
		}
	}
	
	// Replace original properties
	for key := range props {
		delete(props, key)
	}
	for key, val := range filtered {
		props[key] = val
	}
}

// filterRelationships reduces relationship count
func (f *DataFilter) filterRelationships(rels []arxobject.Relationship, config FilterConfig) []arxobject.Relationship {
	if config.MaxProperties < 0 {
		return rels
	}
	
	// Limit relationships to 1/5 of max properties
	maxRels := config.MaxProperties / 5
	if maxRels < 1 {
		maxRels = 1
	}
	
	if len(rels) <= maxRels {
		return rels
	}
	
	// Sort by confidence and keep highest
	sort.Slice(rels, func(i, j int) bool {
		return rels[i].Confidence > rels[j].Confidence
	})
	
	return rels[:maxRels]
}

// BatchFilter applies filtering to multiple objects
func (f *DataFilter) BatchFilter(objects []*arxobject.ArxObjectUnified, precision Precision, maxObjects int) []*arxobject.ArxObjectUnified {
	// Filter individual objects
	filtered := make([]*arxobject.ArxObjectUnified, 0, len(objects))
	
	for _, obj := range objects {
		filtered = append(filtered, f.FilterObject(obj, precision))
	}
	
	// Limit object count if needed
	if maxObjects > 0 && len(filtered) > maxObjects {
		// Sort by confidence and proximity
		sort.Slice(filtered, func(i, j int) bool {
			// Primary sort by confidence
			if filtered[i].GetConfidenceScore() != filtered[j].GetConfidenceScore() {
				return filtered[i].GetConfidenceScore() > filtered[j].GetConfidenceScore()
			}
			
			// Secondary sort by distance from origin
			dist_i := f.distanceFromOrigin(filtered[i].Geometry.Position)
			dist_j := f.distanceFromOrigin(filtered[j].Geometry.Position)
			return dist_i < dist_j
		})
		
		filtered = filtered[:maxObjects]
	}
	
	return filtered
}

// distanceFromOrigin calculates distance from origin
func (f *DataFilter) distanceFromOrigin(p arxobject.Point3D) float64 {
	x := float64(p.X)
	y := float64(p.Y)
	z := float64(p.Z)
	return math.Sqrt(x*x + y*y + z*z)
}

// GetUpdateRate returns the update rate for a precision level
func (f *DataFilter) GetUpdateRate(precision Precision) float64 {
	if config, exists := f.precisionThresholds[precision]; exists {
		return config.UpdateRate
	}
	return 1.0 // Default 1 Hz
}

// GetDataResolution returns the data resolution for a precision level
func (f *DataFilter) GetDataResolution(precision Precision) float64 {
	if config, exists := f.precisionThresholds[precision]; exists {
		return config.DataResolution
	}
	return 1.0 // Default 1 meter
}

// ShouldUpdate checks if an update should be sent based on rate limiting
func (f *DataFilter) ShouldUpdate(lastUpdate float64, precision Precision) bool {
	updateRate := f.GetUpdateRate(precision)
	updateInterval := 1.0 / updateRate
	
	return lastUpdate >= updateInterval
}