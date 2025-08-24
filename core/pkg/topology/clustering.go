// Package topology provides DBSCAN clustering for endpoint merging
package topology

import (
	"math"
	"sort"
)

// DBSCANConfig contains clustering parameters
type DBSCANConfig struct {
	Epsilon    int64 // Maximum distance in nanometers
	MinPoints  int   // Minimum points to form cluster
	GridSize   int   // Spatial grid cell size for optimization
}

// PointCluster represents a group of merged points
type PointCluster struct {
	Points   []Point2D
	Centroid Point2D
	ID       int
}

// ClusterResult contains clustering output
type ClusterResult struct {
	Clusters      []PointCluster
	NoisePoints   []Point2D
	MergeMap      map[Point2D]Point2D // Original -> Merged
	NumMerged     int
	NumClusters   int
}

// DBSCAN performs density-based clustering on endpoints
type DBSCAN struct {
	config   DBSCANConfig
	points   []Point2D
	labels   []int // -1: noise, 0: unvisited, >0: cluster ID
	visited  map[Point2D]bool
	grid     map[int64][]int // Spatial grid for acceleration
}

// NewDBSCAN creates a new clusterer with configuration
func NewDBSCAN(config DBSCANConfig) *DBSCAN {
	return &DBSCAN{
		config:  config,
		visited: make(map[Point2D]bool),
		grid:    make(map[int64][]int),
	}
}

// ClusterEndpoints merges nearby segment endpoints
func ClusterEndpoints(segments []LineSegment, epsilon float64, minPoints int) ([]LineSegment, *ClusterResult) {
	// Convert epsilon from drawing units to nanometers
	epsilonNano := int64(epsilon * 1e9)
	
	config := DBSCANConfig{
		Epsilon:   epsilonNano,
		MinPoints: minPoints,
		GridSize:  int(epsilonNano * 10), // Grid cells 10x epsilon
	}
	
	dbscan := NewDBSCAN(config)
	
	// Extract all unique endpoints
	endpoints := extractEndpoints(segments)
	
	// Perform clustering
	result := dbscan.Cluster(endpoints)
	
	// Rebuild segments with merged endpoints
	mergedSegments := rebuildSegments(segments, result.MergeMap)
	
	return mergedSegments, result
}

// extractEndpoints gets unique points from segments
func extractEndpoints(segments []LineSegment) []Point2D {
	pointSet := make(map[Point2D]bool)
	
	for _, seg := range segments {
		pointSet[seg.Start] = true
		pointSet[seg.End] = true
	}
	
	points := make([]Point2D, 0, len(pointSet))
	for p := range pointSet {
		points = append(points, p)
	}
	
	return points
}

// rebuildSegments updates segments with merged endpoints
func rebuildSegments(segments []LineSegment, mergeMap map[Point2D]Point2D) []LineSegment {
	merged := make([]LineSegment, len(segments))
	
	for i, seg := range segments {
		merged[i] = seg
		
		// Update start point if it was merged
		if newStart, exists := mergeMap[seg.Start]; exists {
			merged[i].Start = newStart
		}
		
		// Update end point if it was merged
		if newEnd, exists := mergeMap[seg.End]; exists {
			merged[i].End = newEnd
		}
	}
	
	return merged
}

// Cluster performs DBSCAN clustering
func (d *DBSCAN) Cluster(points []Point2D) *ClusterResult {
	d.points = points
	d.labels = make([]int, len(points))
	
	// Build spatial grid for acceleration
	d.buildSpatialGrid()
	
	clusterID := 0
	
	for i := range d.points {
		if d.labels[i] != 0 { // Already processed
			continue
		}
		
		neighbors := d.regionQuery(i)
		
		if len(neighbors) < d.config.MinPoints {
			d.labels[i] = -1 // Mark as noise
		} else {
			clusterID++
			d.expandCluster(i, neighbors, clusterID)
		}
	}
	
	return d.buildResult()
}

// buildSpatialGrid creates grid index for fast neighbor queries
func (d *DBSCAN) buildSpatialGrid() {
	gridSize := int64(d.config.GridSize)
	
	for i, p := range d.points {
		gridX := p.X / gridSize
		gridY := p.Y / gridSize
		key := gridX*1000000 + gridY // Simple grid hash
		
		d.grid[key] = append(d.grid[key], i)
	}
}

// regionQuery finds all points within epsilon distance
func (d *DBSCAN) regionQuery(pointIdx int) []int {
	point := d.points[pointIdx]
	var neighbors []int
	
	// Check neighboring grid cells
	gridSize := int64(d.config.GridSize)
	gridX := point.X / gridSize
	gridY := point.Y / gridSize
	
	// Search 3x3 grid around point
	for dx := int64(-1); dx <= 1; dx++ {
		for dy := int64(-1); dy <= 1; dy++ {
			key := (gridX+dx)*1000000 + (gridY+dy)
			
			for _, idx := range d.grid[key] {
				if d.distance(point, d.points[idx]) <= d.config.Epsilon {
					neighbors = append(neighbors, idx)
				}
			}
		}
	}
	
	return neighbors
}

// expandCluster grows cluster from seed point
func (d *DBSCAN) expandCluster(seedIdx int, neighbors []int, clusterID int) {
	d.labels[seedIdx] = clusterID
	
	queue := make([]int, len(neighbors))
	copy(queue, neighbors)
	
	for len(queue) > 0 {
		currentIdx := queue[0]
		queue = queue[1:]
		
		if d.labels[currentIdx] == -1 { // Was noise
			d.labels[currentIdx] = clusterID
		}
		
		if d.labels[currentIdx] != 0 { // Already processed
			continue
		}
		
		d.labels[currentIdx] = clusterID
		
		newNeighbors := d.regionQuery(currentIdx)
		if len(newNeighbors) >= d.config.MinPoints {
			queue = append(queue, newNeighbors...)
		}
	}
}

// distance calculates Euclidean distance
func (d *DBSCAN) distance(p1, p2 Point2D) int64 {
	dx := p2.X - p1.X
	dy := p2.Y - p1.Y
	return int64(math.Sqrt(float64(dx*dx + dy*dy)))
}

// buildResult constructs clustering output
func (d *DBSCAN) buildResult() *ClusterResult {
	result := &ClusterResult{
		MergeMap: make(map[Point2D]Point2D),
	}
	
	// Group points by cluster
	clusterMap := make(map[int][]Point2D)
	
	for i, label := range d.labels {
		if label == -1 {
			result.NoisePoints = append(result.NoisePoints, d.points[i])
		} else if label > 0 {
			clusterMap[label] = append(clusterMap[label], d.points[i])
		}
	}
	
	// Create clusters and merge map
	for clusterID, points := range clusterMap {
		centroid := Centroid(points)
		
		cluster := PointCluster{
			Points:   points,
			Centroid: centroid,
			ID:       clusterID,
		}
		
		result.Clusters = append(result.Clusters, cluster)
		
		// Map all points to centroid
		for _, p := range points {
			result.MergeMap[p] = centroid
		}
	}
	
	result.NumClusters = len(result.Clusters)
	result.NumMerged = len(result.MergeMap)
	
	return result
}

// AdaptiveDBSCAN adjusts parameters based on drawing scale
type AdaptiveDBSCAN struct {
	BaseEpsilon   float64
	BaseMinPoints int
	ScaleFactor   float64 // Drawing scale
}

// NewAdaptiveDBSCAN creates scale-aware clusterer
func NewAdaptiveDBSCAN(drawingScale float64) *AdaptiveDBSCAN {
	return &AdaptiveDBSCAN{
		BaseEpsilon:   0.005, // 0.5% of drawing dimension
		BaseMinPoints: 3,
		ScaleFactor:   drawingScale,
	}
}

// Cluster performs adaptive clustering
func (a *AdaptiveDBSCAN) Cluster(segments []LineSegment) ([]LineSegment, *ClusterResult) {
	// Calculate drawing bounds
	bounds := calculateBounds(segments)
	drawingSize := math.Max(
		float64(bounds.Max.X-bounds.Min.X),
		float64(bounds.Max.Y-bounds.Min.Y),
	)
	
	// Adjust epsilon based on drawing size
	epsilon := a.BaseEpsilon * drawingSize / 1e9 // Convert from nano
	
	// Adjust minPoints based on segment density
	density := float64(len(segments)) / (drawingSize / 1e9)
	minPoints := a.BaseMinPoints
	if density > 100 {
		minPoints = 4 // Increase for dense drawings
	}
	
	return ClusterEndpoints(segments, epsilon, minPoints)
}

// calculateBounds finds drawing extents
func calculateBounds(segments []LineSegment) BoundingBox {
	if len(segments) == 0 {
		return BoundingBox{}
	}
	
	minX, minY := segments[0].Start.X, segments[0].Start.Y
	maxX, maxY := minX, minY
	
	for _, seg := range segments {
		// Check start point
		if seg.Start.X < minX {
			minX = seg.Start.X
		}
		if seg.Start.X > maxX {
			maxX = seg.Start.X
		}
		if seg.Start.Y < minY {
			minY = seg.Start.Y
		}
		if seg.Start.Y > maxY {
			maxY = seg.Start.Y
		}
		
		// Check end point
		if seg.End.X < minX {
			minX = seg.End.X
		}
		if seg.End.X > maxX {
			maxX = seg.End.X
		}
		if seg.End.Y < minY {
			minY = seg.End.Y
		}
		if seg.End.Y > maxY {
			maxY = seg.End.Y
		}
	}
	
	return BoundingBox{
		Min: Point2D{X: minX, Y: minY},
		Max: Point2D{X: maxX, Y: maxY},
	}
}

// MergeCollinearSegments combines aligned segments
func MergeCollinearSegments(segments []LineSegment, angleTolerance float64) []LineSegment {
	// Sort segments by angle and position
	sort.Slice(segments, func(i, j int) bool {
		angleI := segmentAngle(segments[i])
		angleJ := segmentAngle(segments[j])
		if math.Abs(angleI-angleJ) < angleTolerance {
			return segments[i].Start.X < segments[j].Start.X
		}
		return angleI < angleJ
	})
	
	var merged []LineSegment
	var current *LineSegment
	
	for i := range segments {
		seg := &segments[i]
		
		if current == nil {
			current = seg
			continue
		}
		
		// Check if collinear and adjacent
		if isCollinear(current, seg, angleTolerance) && isAdjacent(current, seg) {
			// Extend current segment
			current = mergeSegments(current, seg)
		} else {
			// Save current and start new
			merged = append(merged, *current)
			current = seg
		}
	}
	
	if current != nil {
		merged = append(merged, *current)
	}
	
	return merged
}

// segmentAngle calculates angle in radians
func segmentAngle(seg LineSegment) float64 {
	dx := float64(seg.End.X - seg.Start.X)
	dy := float64(seg.End.Y - seg.Start.Y)
	return math.Atan2(dy, dx)
}

// isCollinear checks if segments are aligned
func isCollinear(seg1, seg2 *LineSegment, tolerance float64) bool {
	angle1 := segmentAngle(*seg1)
	angle2 := segmentAngle(*seg2)
	
	diff := math.Abs(angle1 - angle2)
	return diff < tolerance || math.Abs(diff-math.Pi) < tolerance
}

// isAdjacent checks if segments are connected
func isAdjacent(seg1, seg2 *LineSegment) bool {
	threshold := int64(1e7) // 10mm in nanometers
	
	// Check all endpoint combinations
	return Distance(seg1.End, seg2.Start) < float64(threshold) ||
		Distance(seg1.Start, seg2.End) < float64(threshold) ||
		Distance(seg1.End, seg2.End) < float64(threshold) ||
		Distance(seg1.Start, seg2.Start) < float64(threshold)
}

// mergeSegments combines two segments
func mergeSegments(seg1, seg2 *LineSegment) *LineSegment {
	// Find extreme points
	points := []Point2D{seg1.Start, seg1.End, seg2.Start, seg2.End}
	
	var minX, maxX = points[0].X, points[0].X
	var minPoint, maxPoint = points[0], points[0]
	
	for _, p := range points {
		if p.X < minX || (p.X == minX && p.Y < minPoint.Y) {
			minX = p.X
			minPoint = p
		}
		if p.X > maxX || (p.X == maxX && p.Y > maxPoint.Y) {
			maxX = p.X
			maxPoint = p
		}
	}
	
	return &LineSegment{
		ID:        seg1.ID, // Keep first segment's ID
		Start:     minPoint,
		End:       maxPoint,
		Thickness: seg1.Thickness,
		Confidence: (seg1.Confidence + seg2.Confidence) / 2,
		Source:    seg1.Source,
	}
}