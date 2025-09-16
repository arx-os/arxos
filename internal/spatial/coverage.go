package spatial

import (
	"fmt"
	"math"
	"sort"
	"sync"
	"time"
)

// CoverageTracker tracks scanned coverage for buildings
type CoverageTracker struct {
	buildingID  string
	coverageMap *CoverageMap
	mu          sync.RWMutex
}

// NewCoverageTracker creates a new coverage tracker
func NewCoverageTracker(buildingID string) *CoverageTracker {
	return &CoverageTracker{
		buildingID: buildingID,
		coverageMap: &CoverageMap{
			BuildingID:     buildingID,
			ScannedRegions: make([]ScannedRegion, 0),
			LastUpdated:    time.Now(),
		},
	}
}

// SetTotalArea sets the total building area
func (ct *CoverageTracker) SetTotalArea(area float64) error {
	if area <= 0 {
		return fmt.Errorf("total area must be positive, got %f", area)
	}

	ct.mu.Lock()
	defer ct.mu.Unlock()

	ct.coverageMap.TotalArea = area
	ct.coverageMap.LastUpdated = time.Now()
	return nil
}

// AddScannedRegion adds a newly scanned region
func (ct *CoverageTracker) AddScannedRegion(region ScannedRegion) error {
	if region.BuildingID != ct.buildingID {
		return fmt.Errorf("region building ID %s doesn't match tracker building ID %s",
			region.BuildingID, ct.buildingID)
	}

	if len(region.Region.Boundary) < 3 {
		return fmt.Errorf("region boundary must have at least 3 points")
	}

	ct.mu.Lock()
	defer ct.mu.Unlock()

	// Check for overlapping regions and merge if necessary
	merged := ct.mergeOverlappingRegions(region)
	if !merged {
		ct.coverageMap.ScannedRegions = append(ct.coverageMap.ScannedRegions, region)
	}

	ct.coverageMap.LastUpdated = time.Now()
	return nil
}

// GetCoveragePercentage returns the percentage of area covered
func (ct *CoverageTracker) GetCoveragePercentage() float64 {
	ct.mu.RLock()
	defer ct.mu.RUnlock()

	return ct.coverageMap.GetCoveragePercentage()
}

// GetRegionConfidence returns confidence for a specific point
func (ct *CoverageTracker) GetRegionConfidence(point Point3D) ConfidenceLevel {
	ct.mu.RLock()
	defer ct.mu.RUnlock()

	point2D := Point2D{X: point.X, Y: point.Y}

	// Find the most recent/highest confidence region containing this point
	var bestConfidence ConfidenceLevel = ConfidenceEstimated
	var mostRecentScan time.Time

	for _, region := range ct.coverageMap.ScannedRegions {
		if ct.pointInRegion(point2D, region.Region) {
			// Check if this region is more recent
			if region.ScanDate.After(mostRecentScan) {
				mostRecentScan = region.ScanDate
				bestConfidence = ct.scanTypeToConfidence(region.ScanType, region.PointDensity)
			}
		}
	}

	return bestConfidence
}

// GetUnscannedAreas returns areas that haven't been scanned
func (ct *CoverageTracker) GetUnscannedAreas() []SpatialExtent {
	ct.mu.RLock()
	defer ct.mu.RUnlock()

	if ct.coverageMap.TotalArea == 0 || len(ct.coverageMap.ScannedRegions) == 0 {
		// If no total area or no scans, return empty
		return []SpatialExtent{}
	}

	// Create a grid-based representation for simple difference calculation
	// This is a simplified approach - production would use computational geometry
	gridResolution := 1.0 // 1 meter grid cells

	// Calculate building bounds (assuming rectangular for simplicity)
	buildingSize := math.Sqrt(ct.coverageMap.TotalArea)
	gridSize := int(buildingSize/gridResolution) + 1

	// Create coverage grid (true = unscanned)
	grid := make([][]bool, gridSize)
	for i := range grid {
		grid[i] = make([]bool, gridSize)
		for j := range grid[i] {
			grid[i][j] = true // Initially all unscanned
		}
	}

	// Mark scanned areas
	for _, region := range ct.coverageMap.ScannedRegions {
		ct.markScannedInGrid(grid, region, gridResolution)
	}

	// Extract unscanned regions from grid
	unscanned := ct.extractUnscannedRegions(grid, gridResolution)

	return unscanned
}

// markScannedInGrid marks scanned areas in the grid
func (ct *CoverageTracker) markScannedInGrid(grid [][]bool, region ScannedRegion, resolution float64) {
	// Get bounds of region
	minX, minY, maxX, maxY := ct.getRegionBounds(region.Region.Boundary)

	// Convert to grid coordinates
	startX := int(minX / resolution)
	startY := int(minY / resolution)
	endX := int(maxX/resolution) + 1
	endY := int(maxY/resolution) + 1

	// Mark cells as scanned
	for i := startX; i < endX && i < len(grid); i++ {
		if i < 0 {
			continue
		}
		for j := startY; j < endY && j < len(grid[i]); j++ {
			if j < 0 {
				continue
			}
			grid[i][j] = false // Mark as scanned
		}
	}
}

// getRegionBounds returns the bounds of a region
func (ct *CoverageTracker) getRegionBounds(boundary []Point2D) (float64, float64, float64, float64) {
	if len(boundary) == 0 {
		return 0, 0, 0, 0
	}

	minX, minY := boundary[0].X, boundary[0].Y
	maxX, maxY := boundary[0].X, boundary[0].Y

	for _, p := range boundary {
		if p.X < minX {
			minX = p.X
		}
		if p.X > maxX {
			maxX = p.X
		}
		if p.Y < minY {
			minY = p.Y
		}
		if p.Y > maxY {
			maxY = p.Y
		}
	}

	return minX, minY, maxX, maxY
}

// extractUnscannedRegions converts grid back to spatial extents
func (ct *CoverageTracker) extractUnscannedRegions(grid [][]bool, resolution float64) []SpatialExtent {
	unscanned := make([]SpatialExtent, 0)
	visited := make([][]bool, len(grid))
	for i := range visited {
		visited[i] = make([]bool, len(grid[i]))
	}

	// Find connected unscanned regions
	for i := range grid {
		for j := range grid[i] {
			if grid[i][j] && !visited[i][j] {
				// Found unscanned cell, extract region
				region := ct.extractConnectedRegion(grid, visited, i, j, resolution)
				if len(region.Boundary) >= 4 { // Need at least 4 points for valid region
					unscanned = append(unscanned, region)
				}
			}
		}
	}

	return unscanned
}

// extractConnectedRegion extracts a connected region from grid
func (ct *CoverageTracker) extractConnectedRegion(grid [][]bool, visited [][]bool, startX, startY int, resolution float64) SpatialExtent {
	// Simple bounding box extraction for connected region
	minX, minY := startX, startY
	maxX, maxY := startX, startY

	// BFS to find extent of connected region
	queue := [][2]int{{startX, startY}}
	visited[startX][startY] = true

	for len(queue) > 0 {
		curr := queue[0]
		queue = queue[1:]
		x, y := curr[0], curr[1]

		// Update bounds
		if x < minX {
			minX = x
		}
		if x > maxX {
			maxX = x
		}
		if y < minY {
			minY = y
		}
		if y > maxY {
			maxY = y
		}

		// Check neighbors
		directions := [][2]int{{0, 1}, {0, -1}, {1, 0}, {-1, 0}}
		for _, dir := range directions {
			nx, ny := x+dir[0], y+dir[1]
			if nx >= 0 && nx < len(grid) && ny >= 0 && ny < len(grid[nx]) &&
				grid[nx][ny] && !visited[nx][ny] {
				visited[nx][ny] = true
				queue = append(queue, [2]int{nx, ny})
			}
		}
	}

	// Convert grid bounds to world coordinates
	boundary := []Point2D{
		{X: float64(minX) * resolution, Y: float64(minY) * resolution},
		{X: float64(maxX+1) * resolution, Y: float64(minY) * resolution},
		{X: float64(maxX+1) * resolution, Y: float64(maxY+1) * resolution},
		{X: float64(minX) * resolution, Y: float64(maxY+1) * resolution},
	}

	return SpatialExtent{
		Boundary: boundary,
		MinZ:     0,
		MaxZ:     3.0, // Default floor height
	}
}

// GetScannedRegions returns all scanned regions
func (ct *CoverageTracker) GetScannedRegions() []ScannedRegion {
	ct.mu.RLock()
	defer ct.mu.RUnlock()

	// Return a copy to prevent external modification
	regions := make([]ScannedRegion, len(ct.coverageMap.ScannedRegions))
	copy(regions, ct.coverageMap.ScannedRegions)
	return regions
}

// GetRecentScans returns scans within the specified duration
func (ct *CoverageTracker) GetRecentScans(since time.Duration) []ScannedRegion {
	ct.mu.RLock()
	defer ct.mu.RUnlock()

	cutoff := time.Now().Add(-since)
	recent := make([]ScannedRegion, 0)

	for _, region := range ct.coverageMap.ScannedRegions {
		if region.ScanDate.After(cutoff) {
			recent = append(recent, region)
		}
	}

	// Sort by date, most recent first
	sort.Slice(recent, func(i, j int) bool {
		return recent[i].ScanDate.After(recent[j].ScanDate)
	})

	return recent
}

// GetCoverageByFloor returns coverage percentage for a specific floor
func (ct *CoverageTracker) GetCoverageByFloor(floor int) float64 {
	ct.mu.RLock()
	defer ct.mu.RUnlock()

	// Filter regions by floor (assuming Z coordinate indicates floor)
	floorMin := float64(floor) * 3.0 // Assuming 3m floor height
	floorMax := float64(floor+1) * 3.0

	floorArea := 0.0
	for _, region := range ct.coverageMap.ScannedRegions {
		if region.Region.MinZ >= floorMin && region.Region.MaxZ <= floorMax {
			floorArea += calculatePolygonArea(region.Region.Boundary)
		}
	}

	// Assume floors have equal area
	// Real implementation would track per-floor areas
	floorsCount := ct.estimateFloorCount()
	if floorsCount == 0 {
		return 0
	}

	floorTotalArea := ct.coverageMap.TotalArea / float64(floorsCount)
	if floorTotalArea == 0 {
		return 0
	}

	percentage := (floorArea / floorTotalArea) * 100
	if percentage > 100 {
		return 100
	}
	return percentage
}

// GetCoverageByScanType returns coverage grouped by scan type
func (ct *CoverageTracker) GetCoverageByScanType() map[string]float64 {
	ct.mu.RLock()
	defer ct.mu.RUnlock()

	coverage := make(map[string]float64)

	for _, region := range ct.coverageMap.ScannedRegions {
		area := calculatePolygonArea(region.Region.Boundary)
		coverage[region.ScanType] += area
	}

	// Convert to percentages
	if ct.coverageMap.TotalArea > 0 {
		for scanType, area := range coverage {
			coverage[scanType] = (area / ct.coverageMap.TotalArea) * 100
		}
	}

	return coverage
}

// UpdateRegionConfidence updates confidence for an existing region
func (ct *CoverageTracker) UpdateRegionConfidence(scanID string, newConfidence float64) error {
	if newConfidence < 0 || newConfidence > 1 {
		return fmt.Errorf("confidence must be between 0 and 1, got %f", newConfidence)
	}

	ct.mu.Lock()
	defer ct.mu.Unlock()

	found := false
	for i := range ct.coverageMap.ScannedRegions {
		if ct.coverageMap.ScannedRegions[i].ID == scanID {
			ct.coverageMap.ScannedRegions[i].Confidence = newConfidence
			found = true
			break
		}
	}

	if !found {
		return fmt.Errorf("scan region %s not found", scanID)
	}

	ct.coverageMap.LastUpdated = time.Now()
	return nil
}

// MergeRegions merges multiple scanned regions into one
func (ct *CoverageTracker) MergeRegions(scanIDs []string) error {
	if len(scanIDs) < 2 {
		return fmt.Errorf("need at least 2 regions to merge")
	}

	ct.mu.Lock()
	defer ct.mu.Unlock()

	// Find regions to merge
	regionsToMerge := make([]ScannedRegion, 0)
	for _, id := range scanIDs {
		for _, region := range ct.coverageMap.ScannedRegions {
			if region.ID == id {
				regionsToMerge = append(regionsToMerge, region)
				break
			}
		}
	}

	if len(regionsToMerge) != len(scanIDs) {
		return fmt.Errorf("not all scan IDs found")
	}

	// Create merged region
	merged := ct.createMergedRegion(regionsToMerge)

	// Remove old regions and add merged
	ct.removeRegions(scanIDs)
	ct.coverageMap.ScannedRegions = append(ct.coverageMap.ScannedRegions, merged)

	ct.coverageMap.LastUpdated = time.Now()
	return nil
}

// Helper methods

func (ct *CoverageTracker) mergeOverlappingRegions(newRegion ScannedRegion) bool {
	// Simplified implementation - real version would do geometric intersection
	for i, existing := range ct.coverageMap.ScannedRegions {
		if ct.regionsOverlap(existing, newRegion) {
			// Merge regions by updating the existing one
			ct.coverageMap.ScannedRegions[i] = ct.createMergedRegion([]ScannedRegion{existing, newRegion})
			return true
		}
	}
	return false
}

func (ct *CoverageTracker) regionsOverlap(r1, r2 ScannedRegion) bool {
	// Simplified check - real implementation would use computational geometry
	// For now, just check if any points are very close
	for _, p1 := range r1.Region.Boundary {
		for _, p2 := range r2.Region.Boundary {
			dist := math.Sqrt(math.Pow(p1.X-p2.X, 2) + math.Pow(p1.Y-p2.Y, 2))
			if dist < 0.1 { // Within 10cm
				return true
			}
		}
	}
	return false
}

func (ct *CoverageTracker) createMergedRegion(regions []ScannedRegion) ScannedRegion {
	if len(regions) == 0 {
		return ScannedRegion{}
	}

	// Take the most recent scan date
	var latestDate time.Time
	var bestConfidence float64
	var highestDensity float64

	for _, r := range regions {
		if r.ScanDate.After(latestDate) {
			latestDate = r.ScanDate
		}
		if r.Confidence > bestConfidence {
			bestConfidence = r.Confidence
		}
		if r.PointDensity > highestDensity {
			highestDensity = r.PointDensity
		}
	}

	// Compute convex hull of all boundary points (simplified)
	allPoints := make([]Point2D, 0)
	for _, r := range regions {
		allPoints = append(allPoints, r.Region.Boundary...)
	}

	return ScannedRegion{
		ID:           fmt.Sprintf("merged_%d", time.Now().Unix()),
		BuildingID:   ct.buildingID,
		Region:       SpatialExtent{Boundary: ct.computeConvexHull(allPoints)},
		ScanDate:     latestDate,
		ScanType:     "merged",
		PointDensity: highestDensity,
		Confidence:   bestConfidence,
	}
}

func (ct *CoverageTracker) computeConvexHull(points []Point2D) []Point2D {
	// Simplified - just return bounding box corners
	// Real implementation would use proper convex hull algorithm
	if len(points) == 0 {
		return []Point2D{}
	}

	minX, minY := points[0].X, points[0].Y
	maxX, maxY := points[0].X, points[0].Y

	for _, p := range points {
		if p.X < minX {
			minX = p.X
		}
		if p.X > maxX {
			maxX = p.X
		}
		if p.Y < minY {
			minY = p.Y
		}
		if p.Y > maxY {
			maxY = p.Y
		}
	}

	return []Point2D{
		{X: minX, Y: minY},
		{X: maxX, Y: minY},
		{X: maxX, Y: maxY},
		{X: minX, Y: maxY},
	}
}

func (ct *CoverageTracker) removeRegions(scanIDs []string) {
	newRegions := make([]ScannedRegion, 0)
	for _, region := range ct.coverageMap.ScannedRegions {
		keep := true
		for _, id := range scanIDs {
			if region.ID == id {
				keep = false
				break
			}
		}
		if keep {
			newRegions = append(newRegions, region)
		}
	}
	ct.coverageMap.ScannedRegions = newRegions
}

func (ct *CoverageTracker) pointInRegion(point Point2D, region SpatialExtent) bool {
	// Simplified point-in-polygon test
	// Real implementation would use ray casting or winding number algorithm

	// For now, just check if point is within bounding box
	if len(region.Boundary) < 3 {
		return false
	}

	minX, minY := region.Boundary[0].X, region.Boundary[0].Y
	maxX, maxY := region.Boundary[0].X, region.Boundary[0].Y

	for _, p := range region.Boundary {
		if p.X < minX {
			minX = p.X
		}
		if p.X > maxX {
			maxX = p.X
		}
		if p.Y < minY {
			minY = p.Y
		}
		if p.Y > maxY {
			maxY = p.Y
		}
	}

	return point.X >= minX && point.X <= maxX &&
		point.Y >= minY && point.Y <= maxY
}

func (ct *CoverageTracker) scanTypeToConfidence(scanType string, pointDensity float64) ConfidenceLevel {
	switch scanType {
	case "lidar":
		if pointDensity > 1000 {
			return ConfidenceHigh
		}
		return ConfidenceMedium
	case "photogrammetry":
		return ConfidenceMedium
	case "ar_verify":
		return ConfidenceHigh
	default:
		return ConfidenceLow
	}
}

func (ct *CoverageTracker) estimateFloorCount() int {
	// Estimate based on Z extent of scanned regions
	maxZ := 0.0
	for _, region := range ct.coverageMap.ScannedRegions {
		if region.Region.MaxZ > maxZ {
			maxZ = region.Region.MaxZ
		}
	}

	if maxZ == 0 {
		return 1 // Default to single floor
	}

	// Assume 3m per floor
	return int(maxZ/3.0) + 1
}
