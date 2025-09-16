package lidar

import (
	"fmt"
	"math"
	"sort"

	"github.com/joelpate/arxos/internal/spatial"
)

// Segmenter performs point cloud segmentation
type Segmenter struct {
	params ProcessingParams
}

// NewSegmenter creates a new segmenter
func NewSegmenter(params ProcessingParams) *Segmenter {
	return &Segmenter{
		params: params,
	}
}

// SegmentObjects segments point cloud into individual objects
func (s *Segmenter) SegmentObjects(pc *PointCloud) ([]*PointCluster, error) {
	if len(pc.Points) == 0 {
		return nil, fmt.Errorf("empty point cloud")
	}

	// Remove ground plane points
	nonGroundPoints := s.removeGroundPoints(pc.Points)

	// Perform Euclidean clustering
	clusters := s.euclideanClustering(nonGroundPoints)

	// Filter clusters by size
	filteredClusters := s.filterClusters(clusters)

	// Convert to PointCluster objects
	pointClusters := make([]*PointCluster, 0, len(filteredClusters))
	for i, cluster := range filteredClusters {
		pointCluster := s.createPointCluster(cluster, fmt.Sprintf("cluster_%d", i))
		pointClusters = append(pointClusters, pointCluster)
	}

	return pointClusters, nil
}

// removeGroundPoints filters out points likely to be ground
func (s *Segmenter) removeGroundPoints(points []Point) []Point {
	if len(points) == 0 {
		return points
	}

	// Find minimum Z value
	minZ := points[0].Z
	for _, p := range points {
		if p.Z < minZ {
			minZ = p.Z
		}
	}

	// Keep points above ground threshold (e.g., 10cm above minimum)
	groundThreshold := minZ + 0.1
	nonGround := make([]Point, 0)
	for _, p := range points {
		if p.Z > groundThreshold {
			nonGround = append(nonGround, p)
		}
	}

	return nonGround
}

// euclideanClustering performs Euclidean clustering on points
func (s *Segmenter) euclideanClustering(points []Point) [][]Point {
	if len(points) == 0 {
		return nil
	}

	// Build spatial index (simple grid-based)
	gridIndex := s.buildGridIndex(points)

	// Track which points have been processed
	processed := make([]bool, len(points))
	clusters := make([][]Point, 0)

	for i := range points {
		if processed[i] {
			continue
		}

		// Start new cluster
		cluster := make([]Point, 0)
		queue := []int{i}
		processed[i] = true

		for len(queue) > 0 {
			// Pop from queue
			currentIdx := queue[0]
			queue = queue[1:]
			currentPoint := points[currentIdx]
			cluster = append(cluster, currentPoint)

			// Find neighbors
			neighbors := s.findNeighbors(currentPoint, points, processed, gridIndex)

			for _, neighborIdx := range neighbors {
				if !processed[neighborIdx] {
					processed[neighborIdx] = true
					queue = append(queue, neighborIdx)
				}
			}
		}

		if len(cluster) >= s.params.MinClusterSize {
			clusters = append(clusters, cluster)
		}
	}

	return clusters
}

// gridIndex represents a spatial grid index
type gridIndex map[string][]int

// buildGridIndex creates a spatial grid index for fast neighbor queries
func (s *Segmenter) buildGridIndex(points []Point) gridIndex {
	index := make(gridIndex)
	gridSize := s.params.ClusterTolerance * 2

	for i, point := range points {
		key := s.getGridKey(point, gridSize)
		index[key] = append(index[key], i)
	}

	return index
}

// getGridKey returns grid cell key for a point
func (s *Segmenter) getGridKey(point Point, gridSize float64) string {
	gx := int(math.Floor(point.X / gridSize))
	gy := int(math.Floor(point.Y / gridSize))
	gz := int(math.Floor(point.Z / gridSize))
	return fmt.Sprintf("%d,%d,%d", gx, gy, gz)
}

// findNeighbors finds neighboring points within cluster tolerance
func (s *Segmenter) findNeighbors(point Point, points []Point, processed []bool, index gridIndex) []int {
	neighbors := make([]int, 0)
	gridSize := s.params.ClusterTolerance * 2

	// Check adjacent grid cells
	for dx := -1; dx <= 1; dx++ {
		for dy := -1; dy <= 1; dy++ {
			for dz := -1; dz <= 1; dz++ {
				gx := int(math.Floor(point.X / gridSize))
				gy := int(math.Floor(point.Y / gridSize))
				gz := int(math.Floor(point.Z / gridSize))

				key := fmt.Sprintf("%d,%d,%d", gx+dx, gy+dy, gz+dz)
				if indices, ok := index[key]; ok {
					for _, idx := range indices {
						if processed[idx] {
							continue
						}

						// Check actual distance
						other := points[idx]
						dist := math.Sqrt(
							math.Pow(point.X-other.X, 2) +
								math.Pow(point.Y-other.Y, 2) +
								math.Pow(point.Z-other.Z, 2),
						)

						if dist <= s.params.ClusterTolerance {
							neighbors = append(neighbors, idx)
						}
					}
				}
			}
		}
	}

	return neighbors
}

// filterClusters filters clusters by size and volume constraints
func (s *Segmenter) filterClusters(clusters [][]Point) [][]Point {
	filtered := make([][]Point, 0)

	for _, cluster := range clusters {
		// Check size constraints
		if len(cluster) < s.params.MinClusterSize {
			continue
		}
		if s.params.MaxClusterSize > 0 && len(cluster) > s.params.MaxClusterSize {
			continue
		}

		// Calculate bounding box volume
		minP, maxP := s.getBounds(cluster)
		volume := (maxP.X - minP.X) * (maxP.Y - minP.Y) * (maxP.Z - minP.Z)

		// Check volume constraints
		if volume < s.params.MinObjectVolume {
			continue
		}
		if volume > s.params.MaxObjectVolume {
			continue
		}

		filtered = append(filtered, cluster)
	}

	return filtered
}

// getBounds returns min and max points of a cluster
func (s *Segmenter) getBounds(points []Point) (Point, Point) {
	if len(points) == 0 {
		return Point{}, Point{}
	}

	min := points[0]
	max := points[0]

	for _, p := range points {
		if p.X < min.X {
			min.X = p.X
		}
		if p.Y < min.Y {
			min.Y = p.Y
		}
		if p.Z < min.Z {
			min.Z = p.Z
		}
		if p.X > max.X {
			max.X = p.X
		}
		if p.Y > max.Y {
			max.Y = p.Y
		}
		if p.Z > max.Z {
			max.Z = p.Z
		}
	}

	return min, max
}

// createPointCluster creates a PointCluster from points
func (s *Segmenter) createPointCluster(points []Point, id string) *PointCluster {
	cluster := &PointCluster{
		ID:         id,
		Points:     points,
		PointCount: len(points),
	}

	// Calculate centroid
	centroid := Point{}
	for _, p := range points {
		centroid.X += p.X
		centroid.Y += p.Y
		centroid.Z += p.Z
	}
	count := float64(len(points))
	cluster.Centroid = spatial.Point3D{
		X: centroid.X / count,
		Y: centroid.Y / count,
		Z: centroid.Z / count,
	}

	// Calculate bounding box
	minP, maxP := s.getBounds(points)
	cluster.BoundingBox = spatial.NewBoundingBox(
		minP.ToSpatialPoint3D(),
		maxP.ToSpatialPoint3D(),
	)

	return cluster
}

// ClassifyObject attempts to classify a cluster as a specific object type
func (s *Segmenter) ClassifyObject(cluster *PointCluster) *DetectedObject {
	features := s.extractFeatures(cluster)
	objectClass := s.classifyByFeatures(features)

	return &DetectedObject{
		ID:          fmt.Sprintf("obj_%s", cluster.ID),
		Cluster:     cluster,
		ObjectClass: objectClass,
		Confidence:  s.calculateClassificationConfidence(features, objectClass),
		BoundingBox: cluster.BoundingBox,
		Centroid:    cluster.Centroid,
		Features:    features,
	}
}

// extractFeatures extracts geometric features from a cluster
func (s *Segmenter) extractFeatures(cluster *PointCluster) ObjectFeatures {
	features := ObjectFeatures{
		Properties: make(map[string]float64),
	}

	// Calculate dimensions
	bbox := cluster.BoundingBox
	features.Dimensions = Dimensions{
		Length: bbox.Max.X - bbox.Min.X,
		Width:  bbox.Max.Y - bbox.Min.Y,
		Height: bbox.Max.Z - bbox.Min.Z,
	}

	// Calculate volume and surface area (approximated)
	features.Volume = features.Dimensions.Length *
		features.Dimensions.Width *
		features.Dimensions.Height

	features.SurfaceArea = 2 * (features.Dimensions.Length*features.Dimensions.Width +
		features.Dimensions.Length*features.Dimensions.Height +
		features.Dimensions.Width*features.Dimensions.Height)

	// Calculate shape descriptors
	features.Planarity = s.calculatePlanarity(cluster.Points)
	features.Linearity = s.calculateLinearity(cluster.Points)
	features.Sphericity = s.calculateSphericity(cluster.Points)

	// Determine primary shape
	if features.Planarity > 0.8 {
		features.Shape = "planar"
	} else if features.Linearity > 0.8 {
		features.Shape = "linear"
	} else if features.Sphericity > 0.8 {
		features.Shape = "spherical"
	} else {
		features.Shape = "irregular"
	}

	// Additional properties
	features.Properties["point_density"] = float64(cluster.PointCount) / features.Volume
	features.Properties["aspect_ratio"] = features.Dimensions.Length / features.Dimensions.Width
	features.Properties["height_ratio"] = features.Dimensions.Height /
		math.Max(features.Dimensions.Length, features.Dimensions.Width)

	return features
}

// calculatePlanarity calculates how planar a point cluster is
func (s *Segmenter) calculatePlanarity(points []Point) float64 {
	if len(points) < 3 {
		return 0
	}

	// Compute eigenvalues of covariance matrix (simplified)
	// Real implementation would use PCA
	eigenvalues := s.computeEigenvalues(points)
	sort.Float64s(eigenvalues)

	if eigenvalues[2] > 0 {
		return (eigenvalues[2] - eigenvalues[0]) / eigenvalues[2]
	}
	return 0
}

// calculateLinearity calculates how linear a point cluster is
func (s *Segmenter) calculateLinearity(points []Point) float64 {
	if len(points) < 2 {
		return 0
	}

	eigenvalues := s.computeEigenvalues(points)
	sort.Float64s(eigenvalues)

	if eigenvalues[2] > 0 {
		return (eigenvalues[2] - eigenvalues[1]) / eigenvalues[2]
	}
	return 0
}

// calculateSphericity calculates how spherical a point cluster is
func (s *Segmenter) calculateSphericity(points []Point) float64 {
	if len(points) < 4 {
		return 0
	}

	eigenvalues := s.computeEigenvalues(points)
	sort.Float64s(eigenvalues)

	if eigenvalues[2] > 0 {
		return eigenvalues[0] / eigenvalues[2]
	}
	return 0
}

// computeEigenvalues computes eigenvalues of covariance matrix (simplified)
func (s *Segmenter) computeEigenvalues(points []Point) []float64 {
	// Calculate centroid
	var cx, cy, cz float64
	for _, p := range points {
		cx += p.X
		cy += p.Y
		cz += p.Z
	}
	n := float64(len(points))
	cx /= n
	cy /= n
	cz /= n

	// Calculate covariance matrix elements
	var xx, yy, zz, xy, xz, yz float64
	for _, p := range points {
		dx := p.X - cx
		dy := p.Y - cy
		dz := p.Z - cz
		xx += dx * dx
		yy += dy * dy
		zz += dz * dz
		xy += dx * dy
		xz += dx * dz
		yz += dy * dz
	}

	// Normalize
	xx /= n
	yy /= n
	zz /= n
	xy /= n
	xz /= n
	yz /= n

	// Approximate eigenvalues (diagonal elements for simplicity)
	// Real implementation would solve characteristic polynomial
	return []float64{xx, yy, zz}
}

// classifyByFeatures classifies object based on features
func (s *Segmenter) classifyByFeatures(features ObjectFeatures) string {
	// Simple rule-based classification
	dims := features.Dimensions

	// Check for common equipment types based on dimensions
	if s.isHVACUnit(dims, features) {
		return "hvac_unit"
	}
	if s.isPipe(dims, features) {
		return "pipe"
	}
	if s.isDuct(dims, features) {
		return "duct"
	}
	if s.isColumn(dims, features) {
		return "column"
	}
	if s.isWall(dims, features) {
		return "wall_segment"
	}

	return "unknown"
}

// Equipment classification helpers

func (s *Segmenter) isHVACUnit(dims Dimensions, features ObjectFeatures) bool {
	// HVAC units are typically boxy with moderate size
	return dims.Length > 0.5 && dims.Length < 3.0 &&
		dims.Width > 0.5 && dims.Width < 3.0 &&
		dims.Height > 0.3 && dims.Height < 2.0 &&
		features.Shape != "linear" && features.Shape != "planar"
}

func (s *Segmenter) isPipe(dims Dimensions, features ObjectFeatures) bool {
	// Pipes are linear and cylindrical
	return features.Linearity > 0.7 &&
		math.Min(dims.Width, dims.Height) < 0.3 &&
		math.Max(dims.Length, math.Max(dims.Width, dims.Height)) > 1.0
}

func (s *Segmenter) isDuct(dims Dimensions, features ObjectFeatures) bool {
	// Ducts are linear but larger than pipes
	return features.Linearity > 0.6 &&
		math.Min(dims.Width, dims.Height) > 0.2 &&
		math.Min(dims.Width, dims.Height) < 1.0 &&
		math.Max(dims.Length, math.Max(dims.Width, dims.Height)) > 2.0
}

func (s *Segmenter) isColumn(dims Dimensions, features ObjectFeatures) bool {
	// Columns are vertical and cylindrical or rectangular
	return dims.Height > 2.0 &&
		dims.Length < 1.0 &&
		dims.Width < 1.0 &&
		features.Properties["height_ratio"] > 2.0
}

func (s *Segmenter) isWall(dims Dimensions, features ObjectFeatures) bool {
	// Walls are planar and large
	return features.Planarity > 0.8 &&
		math.Min(dims.Length, dims.Width) < 0.3 &&
		math.Max(dims.Length, dims.Width) > 2.0
}

// calculateClassificationConfidence calculates confidence in classification
func (s *Segmenter) calculateClassificationConfidence(features ObjectFeatures, objectClass string) float64 {
	baseConfidence := 0.5

	// Increase confidence based on feature quality
	if features.Shape != "irregular" {
		baseConfidence += 0.2
	}

	// Increase confidence for known object types
	if objectClass != "unknown" {
		baseConfidence += 0.2
	}

	// Consider feature strengths
	maxFeature := math.Max(features.Planarity,
		math.Max(features.Linearity, features.Sphericity))
	if maxFeature > 0.8 {
		baseConfidence += 0.1
	}

	return math.Min(baseConfidence, 1.0)
}
