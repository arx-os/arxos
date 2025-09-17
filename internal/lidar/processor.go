package lidar

import (
	"fmt"
	"math"
	"sort"
	"sync"

	"github.com/arx-os/arxos/internal/spatial"
)

// Processor handles point cloud processing operations
type Processor struct {
	params ProcessingParams
	mu     sync.RWMutex
}

// NewProcessor creates a new point cloud processor
func NewProcessor(params ProcessingParams) *Processor {
	return &Processor{
		params: params,
	}
}

// NewDefaultProcessor creates a processor with default parameters
func NewDefaultProcessor() *Processor {
	return &Processor{
		params: DefaultProcessingParams(),
	}
}

// ProcessPointCloud applies the full processing pipeline to a point cloud
func (p *Processor) ProcessPointCloud(pc *PointCloud) (*ProcessedCloud, error) {
	if err := pc.Validate(); err != nil {
		return nil, fmt.Errorf("invalid point cloud: %w", err)
	}

	processed := &ProcessedCloud{
		PointCloud: pc,
	}

	// Apply noise filtering
	if p.params.NoiseFilterEnabled {
		removed := p.filterNoise(processed.PointCloud)
		processed.OutliersRemoved = removed
		processed.Filtered = true
	}

	// Apply downsampling
	if p.params.DownsampleEnabled {
		p.downsample(processed.PointCloud)
		processed.Downsampled = true
		processed.VoxelSize = p.params.VoxelSize
	}

	return processed, nil
}

// AlignToBuilding aligns a processed cloud to building coordinates
func (p *Processor) AlignToBuilding(pc *ProcessedCloud, buildingID string) (*AlignedCloud, error) {
	// Detect ground plane
	groundPlane := p.detectGroundPlane(pc.PointCloud)

	// Calculate transformation to align with building axes
	transform := p.calculateAlignment(pc.PointCloud, groundPlane)

	// Apply transformation
	alignedPoints := p.applyTransform(pc.Points, transform)
	pc.Points = alignedPoints

	aligned := &AlignedCloud{
		ProcessedCloud: pc,
		Transform:      transform,
		GroundPlane:    groundPlane,
		AlignmentError: p.calculateAlignmentError(pc.PointCloud, groundPlane),
		Confidence:     p.calculateAlignmentConfidence(pc.PointCloud),
	}

	return aligned, nil
}

// filterNoise removes noise using statistical outlier removal
func (p *Processor) filterNoise(pc *PointCloud) int {
	if len(pc.Points) == 0 {
		return 0
	}

	// Calculate mean distance to k nearest neighbors for each point
	distances := make([]float64, len(pc.Points))
	for i, point := range pc.Points {
		distances[i] = p.meanKNNDistance(point, pc.Points, p.params.StatisticalK)
	}

	// Calculate mean and std dev of distances
	mean := 0.0
	for _, d := range distances {
		mean += d
	}
	mean /= float64(len(distances))

	stdDev := 0.0
	for _, d := range distances {
		diff := d - mean
		stdDev += diff * diff
	}
	stdDev = math.Sqrt(stdDev / float64(len(distances)))

	// Remove outliers
	threshold := mean + p.params.StdDevMultiplier*stdDev
	filteredPoints := make([]Point, 0, len(pc.Points))
	filteredColors := make([]Color, 0)
	filteredIntensities := make([]float32, 0)
	filteredNormals := make([]Normal, 0)

	removed := 0
	for i, distance := range distances {
		if distance <= threshold {
			filteredPoints = append(filteredPoints, pc.Points[i])
			if len(pc.Colors) > i {
				filteredColors = append(filteredColors, pc.Colors[i])
			}
			if len(pc.Intensities) > i {
				filteredIntensities = append(filteredIntensities, pc.Intensities[i])
			}
			if len(pc.Normals) > i {
				filteredNormals = append(filteredNormals, pc.Normals[i])
			}
		} else {
			removed++
		}
	}

	pc.Points = filteredPoints
	pc.Colors = filteredColors
	pc.Intensities = filteredIntensities
	pc.Normals = filteredNormals
	pc.Metadata.PointCount = len(pc.Points)

	return removed
}

// meanKNNDistance calculates mean distance to k nearest neighbors
func (p *Processor) meanKNNDistance(point Point, points []Point, k int) float64 {
	if k >= len(points) {
		k = len(points) - 1
	}

	distances := make([]float64, 0, len(points))
	for _, other := range points {
		if point.X == other.X && point.Y == other.Y && point.Z == other.Z {
			continue
		}
		dist := math.Sqrt(
			math.Pow(point.X-other.X, 2) +
				math.Pow(point.Y-other.Y, 2) +
				math.Pow(point.Z-other.Z, 2),
		)
		distances = append(distances, dist)
	}

	sort.Float64s(distances)

	sum := 0.0
	for i := 0; i < k && i < len(distances); i++ {
		sum += distances[i]
	}

	if k > 0 {
		return sum / float64(k)
	}
	return 0
}

// downsample reduces point density using voxel grid filtering
func (p *Processor) downsample(pc *PointCloud) {
	if p.params.VoxelSize <= 0 {
		return
	}

	// Create voxel grid
	voxelMap := make(map[string][]int)
	for i, point := range pc.Points {
		voxelKey := p.getVoxelKey(point, p.params.VoxelSize)
		voxelMap[voxelKey] = append(voxelMap[voxelKey], i)
	}

	// Keep one point per voxel (centroid)
	newPoints := make([]Point, 0, len(voxelMap))
	newColors := make([]Color, 0)
	newIntensities := make([]float32, 0)
	newNormals := make([]Normal, 0)

	for _, indices := range voxelMap {
		// Calculate centroid
		centroid := Point{}
		for _, idx := range indices {
			centroid.X += pc.Points[idx].X
			centroid.Y += pc.Points[idx].Y
			centroid.Z += pc.Points[idx].Z
		}
		count := float64(len(indices))
		centroid.X /= count
		centroid.Y /= count
		centroid.Z /= count
		newPoints = append(newPoints, centroid)

		// Average colors if present
		if len(pc.Colors) > 0 {
			var r, g, b float64
			for _, idx := range indices {
				r += float64(pc.Colors[idx].R)
				g += float64(pc.Colors[idx].G)
				b += float64(pc.Colors[idx].B)
			}
			newColors = append(newColors, Color{
				R: uint8(r / count),
				G: uint8(g / count),
				B: uint8(b / count),
			})
		}

		// Average intensities if present
		if len(pc.Intensities) > 0 {
			var intensity float32
			for _, idx := range indices {
				intensity += pc.Intensities[idx]
			}
			newIntensities = append(newIntensities, intensity/float32(len(indices)))
		}

		// Average normals if present
		if len(pc.Normals) > 0 {
			var nx, ny, nz float32
			for _, idx := range indices {
				nx += pc.Normals[idx].NX
				ny += pc.Normals[idx].NY
				nz += pc.Normals[idx].NZ
			}
			// Normalize
			length := float32(math.Sqrt(float64(nx*nx + ny*ny + nz*nz)))
			if length > 0 {
				nx /= length
				ny /= length
				nz /= length
			}
			newNormals = append(newNormals, Normal{NX: nx, NY: ny, NZ: nz})
		}
	}

	// Check if we need further downsampling to meet target
	if p.params.TargetPoints > 0 && len(newPoints) > p.params.TargetPoints {
		// Randomly sample to reach target
		indices := make([]int, len(newPoints))
		for i := range indices {
			indices[i] = i
		}
		// Simple deterministic sampling (not truly random for reproducibility)
		step := len(newPoints) / p.params.TargetPoints
		sampledPoints := make([]Point, 0, p.params.TargetPoints)
		for i := 0; i < len(newPoints); i += step {
			sampledPoints = append(sampledPoints, newPoints[i])
		}
		newPoints = sampledPoints
	}

	pc.Points = newPoints
	pc.Colors = newColors
	pc.Intensities = newIntensities
	pc.Normals = newNormals
	pc.Metadata.PointCount = len(pc.Points)
}

// getVoxelKey returns a string key for the voxel containing the point
func (p *Processor) getVoxelKey(point Point, voxelSize float64) string {
	vx := int(math.Floor(point.X / voxelSize))
	vy := int(math.Floor(point.Y / voxelSize))
	vz := int(math.Floor(point.Z / voxelSize))
	return fmt.Sprintf("%d,%d,%d", vx, vy, vz)
}

// detectGroundPlane detects the ground plane using RANSAC
func (p *Processor) detectGroundPlane(pc *PointCloud) *Plane {
	if len(pc.Points) < 3 {
		return nil
	}

	// Find points likely to be ground (lowest Z values)
	sorted := make([]Point, len(pc.Points))
	copy(sorted, pc.Points)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].Z < sorted[j].Z
	})

	// Use bottom 20% of points for ground detection
	groundCandidates := sorted[:len(sorted)/5]

	// Simplified RANSAC for plane fitting
	bestPlane := &Plane{}
	maxInliers := 0
	iterations := 100
	threshold := 0.1 // 10cm threshold

	for i := 0; i < iterations; i++ {
		// Select 3 random points
		if len(groundCandidates) < 3 {
			break
		}

		// Simple deterministic sampling for reproducibility
		idx1 := i % len(groundCandidates)
		idx2 := (i * 7) % len(groundCandidates)
		idx3 := (i * 13) % len(groundCandidates)

		p1 := groundCandidates[idx1]
		p2 := groundCandidates[idx2]
		p3 := groundCandidates[idx3]

		// Calculate plane equation
		plane := p.fitPlane(p1, p2, p3)

		// Count inliers
		inliers := 0
		totalError := 0.0
		for _, point := range groundCandidates {
			dist := p.pointToPlaneDistance(point, plane)
			if math.Abs(dist) < threshold {
				inliers++
				totalError += dist * dist
			}
		}

		if inliers > maxInliers {
			maxInliers = inliers
			bestPlane = plane
			bestPlane.InlierCount = inliers
			if inliers > 0 {
				bestPlane.Error = math.Sqrt(totalError / float64(inliers))
			}
		}
	}

	return bestPlane
}

// fitPlane fits a plane through three points
func (p *Processor) fitPlane(p1, p2, p3 Point) *Plane {
	// Calculate normal vector using cross product
	v1 := Point{X: p2.X - p1.X, Y: p2.Y - p1.Y, Z: p2.Z - p1.Z}
	v2 := Point{X: p3.X - p1.X, Y: p3.Y - p1.Y, Z: p3.Z - p1.Z}

	normal := Point{
		X: v1.Y*v2.Z - v1.Z*v2.Y,
		Y: v1.Z*v2.X - v1.X*v2.Z,
		Z: v1.X*v2.Y - v1.Y*v2.X,
	}

	// Normalize
	length := math.Sqrt(normal.X*normal.X + normal.Y*normal.Y + normal.Z*normal.Z)
	if length > 0 {
		normal.X /= length
		normal.Y /= length
		normal.Z /= length
	}

	// Calculate D using point p1
	d := -(normal.X*p1.X + normal.Y*p1.Y + normal.Z*p1.Z)

	return &Plane{
		A: normal.X,
		B: normal.Y,
		C: normal.Z,
		D: d,
	}
}

// pointToPlaneDistance calculates distance from point to plane
func (p *Processor) pointToPlaneDistance(point Point, plane *Plane) float64 {
	numerator := math.Abs(plane.A*point.X + plane.B*point.Y + plane.C*point.Z + plane.D)
	denominator := math.Sqrt(plane.A*plane.A + plane.B*plane.B + plane.C*plane.C)
	if denominator == 0 {
		return 0
	}
	return numerator / denominator
}

// calculateAlignment calculates transformation to align with building axes
func (p *Processor) calculateAlignment(pc *PointCloud, groundPlane *Plane) spatial.Transform {
	transform := spatial.Transform{
		Scale: 1.0,
	}

	if groundPlane == nil {
		return transform
	}

	// Calculate rotation to make ground plane horizontal
	// Simplified: assume we want to rotate around X or Y axis
	groundNormal := Point{X: groundPlane.A, Y: groundPlane.B, Z: groundPlane.C}
	targetNormal := Point{X: 0, Y: 0, Z: 1} // Vertical normal

	// Calculate rotation angle
	dot := groundNormal.X*targetNormal.X + groundNormal.Y*targetNormal.Y + groundNormal.Z*targetNormal.Z
	angle := math.Acos(dot)

	// Rotation axis (cross product)
	axis := Point{
		X: groundNormal.Y*targetNormal.Z - groundNormal.Z*targetNormal.Y,
		Y: groundNormal.Z*targetNormal.X - groundNormal.X*targetNormal.Z,
		Z: groundNormal.X*targetNormal.Y - groundNormal.Y*targetNormal.X,
	}

	// Store rotation as Euler angles (simplified)
	transform.Rotation[0] = axis.X * angle
	transform.Rotation[1] = axis.Y * angle
	transform.Rotation[2] = axis.Z * angle

	// Calculate translation to center the point cloud
	stats := pc.CalculateStatistics()
	transform.Translation = spatial.Point3D{
		X: -stats.CenterOfMass.X,
		Y: -stats.CenterOfMass.Y,
		Z: -stats.MinBounds.Z, // Align bottom to Z=0
	}

	return transform
}

// applyTransform applies a transformation to all points
func (p *Processor) applyTransform(points []Point, transform spatial.Transform) []Point {
	transformed := make([]Point, len(points))

	for i, point := range points {
		// Convert to spatial.Point3D
		sp := point.ToSpatialPoint3D()

		// Apply transform
		sp = transform.Apply(sp)

		// Convert back
		transformed[i] = FromSpatialPoint3D(sp)
	}

	return transformed
}

// calculateAlignmentError calculates RMS error of alignment
func (p *Processor) calculateAlignmentError(pc *PointCloud, groundPlane *Plane) float64 {
	if groundPlane == nil || len(pc.Points) == 0 {
		return 0
	}

	totalError := 0.0
	count := 0

	for _, point := range pc.Points {
		// Only check points near ground
		if point.Z < 0.5 { // Within 50cm of ground
			dist := p.pointToPlaneDistance(point, groundPlane)
			totalError += dist * dist
			count++
		}
	}

	if count > 0 {
		return math.Sqrt(totalError / float64(count))
	}
	return 0
}

// calculateAlignmentConfidence estimates alignment quality
func (p *Processor) calculateAlignmentConfidence(pc *PointCloud) float64 {
	if len(pc.Points) == 0 {
		return 0
	}

	// Factors affecting confidence:
	// 1. Number of points
	pointScore := math.Min(float64(len(pc.Points))/100000.0, 1.0)

	// 2. Point distribution (using bounds)
	stats := pc.CalculateStatistics()
	volume := (stats.MaxBounds.X - stats.MinBounds.X) *
		(stats.MaxBounds.Y - stats.MinBounds.Y) *
		(stats.MaxBounds.Z - stats.MinBounds.Z)

	volumeScore := math.Min(volume/1000.0, 1.0) // Normalized by 1000 m³

	// 3. Density
	densityScore := math.Min(stats.Density/1000.0, 1.0)

	// Weighted average
	confidence := pointScore*0.3 + volumeScore*0.3 + densityScore*0.4

	return confidence
}

// SetParams updates processing parameters
func (p *Processor) SetParams(params ProcessingParams) {
	p.mu.Lock()
	defer p.mu.Unlock()
	p.params = params
}

// GetParams returns current processing parameters
func (p *Processor) GetParams() ProcessingParams {
	p.mu.RLock()
	defer p.mu.RUnlock()
	return p.params
}
