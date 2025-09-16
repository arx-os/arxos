package lidar

import (
	"fmt"
	"time"

	"github.com/joelpate/arxos/internal/spatial"
)

// SpatialIntegrator integrates LiDAR data with spatial confidence system
type SpatialIntegrator struct {
	confidenceManager *spatial.ConfidenceManager
	coverageTracker   *spatial.CoverageTracker
	matcher           *EquipmentMatcher
}

// NewSpatialIntegrator creates a new spatial integrator
func NewSpatialIntegrator(
	confidenceManager *spatial.ConfidenceManager,
	coverageTracker *spatial.CoverageTracker,
) *SpatialIntegrator {
	return &SpatialIntegrator{
		confidenceManager: confidenceManager,
		coverageTracker:   coverageTracker,
		matcher:           NewDefaultMatcher(),
	}
}

// ProcessAndIntegrate processes a LiDAR scan and integrates with spatial system
func (si *SpatialIntegrator) ProcessAndIntegrate(
	pointCloud *PointCloud,
	buildingID string,
	knownEquipment []KnownEquipment,
) (*IntegrationResult, error) {

	startTime := time.Now()
	result := &IntegrationResult{
		BuildingID:      buildingID,
		ScanID:          pointCloud.Metadata.ScanID,
		ProcessingStart: startTime,
	}

	// Step 1: Process point cloud
	processor := NewDefaultProcessor()
	processed, err := processor.ProcessPointCloud(pointCloud)
	if err != nil {
		return nil, fmt.Errorf("failed to process point cloud: %w", err)
	}

	// Step 2: Align to building coordinates
	aligned, err := processor.AlignToBuilding(processed, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to align point cloud: %w", err)
	}
	result.AlignmentConfidence = aligned.Confidence

	// Step 3: Segment objects
	segmenter := NewSegmenter(DefaultProcessingParams())
	clusters, err := segmenter.SegmentObjects(aligned.PointCloud)
	if err != nil {
		return nil, fmt.Errorf("failed to segment objects: %w", err)
	}

	// Step 4: Classify objects
	detectedObjects := make([]*DetectedObject, 0, len(clusters))
	for _, cluster := range clusters {
		obj := segmenter.ClassifyObject(cluster)
		detectedObjects = append(detectedObjects, obj)
	}
	result.ObjectsDetected = len(detectedObjects)

	// Step 5: Match with known equipment
	matches, err := si.matcher.MatchDetectedObjects(detectedObjects, knownEquipment)
	if err != nil {
		return nil, fmt.Errorf("failed to match objects: %w", err)
	}
	result.EquipmentMatched = len(matches)
	result.Matches = matches

	// Step 6: Update confidence for matched equipment
	for _, match := range matches {
		err := si.updateEquipmentConfidence(match)
		if err != nil {
			// Log error but continue
			fmt.Printf("Warning: failed to update confidence for %s: %v\n",
				match.EquipmentID, err)
		}
	}

	// Step 7: Update coverage tracking
	region := si.createScannedRegion(aligned, buildingID)
	err = si.coverageTracker.AddScannedRegion(region)
	if err != nil {
		// Log error but continue
		fmt.Printf("Warning: failed to update coverage: %v\n", err)
	}

	// Step 8: Identify new/unknown objects
	unmatched := si.matcher.FindUnmatchedObjects(detectedObjects, matches)
	result.UnknownObjects = len(unmatched)
	result.UnmatchedObjects = unmatched

	// Calculate statistics
	result.ProcessingTime = time.Since(startTime)
	result.CoveragePercentage = si.coverageTracker.GetCoveragePercentage()
	result.Success = true

	return result, nil
}

// updateEquipmentConfidence updates confidence based on LiDAR match
func (si *SpatialIntegrator) updateEquipmentConfidence(match *EquipmentMatch) error {
	// Update position confidence
	positionConfidence := si.matchScoreToConfidence(match.LocationScore)
	err := si.confidenceManager.UpdateConfidence(
		match.EquipmentID,
		spatial.AspectPosition,
		positionConfidence,
		"lidar",
	)
	if err != nil {
		return err
	}

	// Update semantic confidence if object was classified
	if match.DetectedObject.ObjectClass != "unknown" {
		semanticConfidence := si.matchScoreToConfidence(match.ShapeScore)
		err = si.confidenceManager.UpdateConfidence(
			match.EquipmentID,
			spatial.AspectSemantic,
			semanticConfidence,
			"lidar",
		)
		if err != nil {
			return err
		}
	}

	// Record verification
	return si.confidenceManager.RecordVerification(
		match.EquipmentID,
		"lidar",
		"system",
		fmt.Sprintf("Match score: %.2f", match.MatchScore),
	)
}

// matchScoreToConfidence converts match score to confidence level
func (si *SpatialIntegrator) matchScoreToConfidence(score float64) spatial.ConfidenceLevel {
	if score >= 0.9 {
		return spatial.ConfidenceHigh
	} else if score >= 0.7 {
		return spatial.ConfidenceMedium
	} else if score >= 0.5 {
		return spatial.ConfidenceLow
	}
	return spatial.ConfidenceEstimated
}

// createScannedRegion creates a scanned region from aligned point cloud
func (si *SpatialIntegrator) createScannedRegion(
	aligned *AlignedCloud,
	buildingID string,
) spatial.ScannedRegion {

	// Calculate 2D boundary from point cloud
	bounds := aligned.PointCloud.GetBoundingBox()
	boundary := []spatial.Point2D{
		{X: bounds.Min.X, Y: bounds.Min.Y},
		{X: bounds.Max.X, Y: bounds.Min.Y},
		{X: bounds.Max.X, Y: bounds.Max.Y},
		{X: bounds.Min.X, Y: bounds.Max.Y},
	}

	return spatial.ScannedRegion{
		ID:         aligned.Metadata.ScanID,
		BuildingID: buildingID,
		Region: spatial.SpatialExtent{
			Boundary: boundary,
			MinZ:     bounds.Min.Z,
			MaxZ:     bounds.Max.Z,
		},
		ScanDate:     aligned.Metadata.ScanDate,
		ScanType:     "lidar",
		PointDensity: float64(aligned.Metadata.PointCount) / bounds.Volume(),
		Confidence:   aligned.Confidence,
	}
}

// IntegrationResult represents the result of LiDAR integration
type IntegrationResult struct {
	BuildingID          string
	ScanID              string
	Success             bool
	ObjectsDetected     int
	EquipmentMatched    int
	UnknownObjects      int
	CoveragePercentage  float64
	AlignmentConfidence float64
	ProcessingTime      time.Duration
	ProcessingStart     time.Time
	Matches             []*EquipmentMatch
	UnmatchedObjects    []*DetectedObject
	Errors              []string
}

// MergePartialScan merges a partial LiDAR scan with existing data
func (si *SpatialIntegrator) MergePartialScan(
	partialScan *PointCloud,
	buildingID string,
	existingEquipment []KnownEquipment,
) (*MergeResult, error) {

	startTime := time.Now()

	// Process the partial scan
	integrationResult, err := si.ProcessAndIntegrate(
		partialScan,
		buildingID,
		existingEquipment,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to process partial scan: %w", err)
	}

	// Identify conflicts (objects that moved significantly)
	conflicts := si.identifyConflicts(integrationResult.Matches, existingEquipment)

	// Calculate coverage increase
	oldCoverage := si.coverageTracker.GetCoveragePercentage()
	newCoverage := integrationResult.CoveragePercentage
	coverageIncrease := newCoverage - oldCoverage

	// Count updated positions
	updatedPositions := 0
	for _, match := range integrationResult.Matches {
		if match.LocationScore < 0.95 { // Position changed slightly
			updatedPositions++
		}
	}

	return &MergeResult{
		MatchedEquipment: integrationResult.EquipmentMatched,
		UnknownObjects:   integrationResult.UnknownObjects,
		CoverageIncrease: coverageIncrease,
		UpdatedPositions: updatedPositions,
		Conflicts:        conflicts,
		ProcessingTime:   time.Since(startTime),
	}, nil
}

// identifyConflicts finds equipment with significant position changes
func (si *SpatialIntegrator) identifyConflicts(
	matches []*EquipmentMatch,
	existingEquipment []KnownEquipment,
) []MergeConflict {

	conflicts := make([]MergeConflict, 0)

	// Create map of existing equipment for quick lookup
	existingMap := make(map[string]KnownEquipment)
	for _, eq := range existingEquipment {
		existingMap[eq.ID] = eq
	}

	for _, match := range matches {
		if existing, ok := existingMap[match.EquipmentID]; ok {
			// Calculate position difference
			distance := match.DetectedObject.Centroid.DistanceTo(existing.Position)

			// Flag as conflict if moved significantly (> 0.5m)
			if distance > 0.5 {
				conflicts = append(conflicts, MergeConflict{
					ObjectID:     match.EquipmentID,
					ConflictType: "position_change",
					OldPosition:  existing.Position,
					NewPosition:  match.DetectedObject.Centroid,
					Distance:     distance,
					Resolution:   si.suggestResolution(distance),
				})
			}
		}
	}

	return conflicts
}

// suggestResolution suggests how to resolve a conflict
func (si *SpatialIntegrator) suggestResolution(distance float64) string {
	if distance < 1.0 {
		return "accept_new_position"
	} else if distance < 3.0 {
		return "verify_manually"
	}
	return "investigate_major_change"
}

// UpdateEquipmentFromScan updates equipment positions based on LiDAR scan
func (si *SpatialIntegrator) UpdateEquipmentFromScan(
	matches []*EquipmentMatch,
) ([]EquipmentUpdate, error) {

	updates := make([]EquipmentUpdate, 0, len(matches))

	for _, match := range matches {
		// Only update if confidence is high enough
		if match.MatchScore >= 0.8 {
			update := EquipmentUpdate{
				EquipmentID:   match.EquipmentID,
				NewPosition:   match.DetectedObject.Centroid,
				NewDimensions: match.DetectedObject.Features.Dimensions,
				Confidence:    match.Confidence,
				Source:        "lidar",
				Timestamp:     time.Now(),
			}
			updates = append(updates, update)

			// Update confidence system
			err := si.updateEquipmentConfidence(match)
			if err != nil {
				return nil, err
			}
		}
	}

	return updates, nil
}

// EquipmentUpdate represents an equipment position/dimension update
type EquipmentUpdate struct {
	EquipmentID   string
	NewPosition   spatial.Point3D
	NewDimensions Dimensions
	Confidence    spatial.ConfidenceLevel
	Source        string
	Timestamp     time.Time
}

// ValidateScanQuality validates the quality of a LiDAR scan
func (si *SpatialIntegrator) ValidateScanQuality(pc *PointCloud) (*QualityReport, error) {
	report := &QualityReport{
		ScanID:     pc.Metadata.ScanID,
		Timestamp:  pc.Metadata.ScanDate,
		PointCount: pc.Metadata.PointCount,
	}

	// Check point density
	volume := pc.Metadata.Bounds.Volume()
	if volume > 0 {
		report.PointDensity = float64(pc.Metadata.PointCount) / volume
	}

	// Evaluate density quality
	if report.PointDensity >= 1000 {
		report.DensityQuality = "high"
	} else if report.PointDensity >= 100 {
		report.DensityQuality = "medium"
	} else {
		report.DensityQuality = "low"
	}

	// Check coverage
	if volume > 0 {
		// Estimate based on bounds
		report.CoverageQuality = "partial"
		if volume > 100 { // More than 100 m³
			report.CoverageQuality = "good"
		}
		if volume > 1000 { // More than 1000 m³
			report.CoverageQuality = "comprehensive"
		}
	}

	// Check for data completeness
	report.HasColors = len(pc.Colors) > 0
	report.HasIntensities = len(pc.Intensities) > 0
	report.HasNormals = len(pc.Normals) > 0

	// Calculate overall quality score (0-1)
	score := 0.0
	if report.DensityQuality == "high" {
		score += 0.4
	} else if report.DensityQuality == "medium" {
		score += 0.2
	}

	if report.CoverageQuality == "comprehensive" {
		score += 0.3
	} else if report.CoverageQuality == "good" {
		score += 0.2
	}

	if report.HasColors {
		score += 0.1
	}
	if report.HasIntensities {
		score += 0.1
	}
	if report.HasNormals {
		score += 0.1
	}

	report.OverallQuality = score

	// Add recommendations
	report.Recommendations = si.generateQualityRecommendations(report)

	return report, nil
}

// QualityReport represents scan quality assessment
type QualityReport struct {
	ScanID          string
	Timestamp       time.Time
	PointCount      int
	PointDensity    float64
	DensityQuality  string // "low", "medium", "high"
	CoverageQuality string // "partial", "good", "comprehensive"
	HasColors       bool
	HasIntensities  bool
	HasNormals      bool
	OverallQuality  float64 // 0-1 score
	Recommendations []string
}

// generateQualityRecommendations generates improvement recommendations
func (si *SpatialIntegrator) generateQualityRecommendations(report *QualityReport) []string {
	recommendations := make([]string, 0)

	if report.DensityQuality == "low" {
		recommendations = append(recommendations,
			"Increase scan resolution for better object detection")
	}

	if report.CoverageQuality == "partial" {
		recommendations = append(recommendations,
			"Perform additional scans to cover missing areas")
	}

	if !report.HasColors {
		recommendations = append(recommendations,
			"Enable color capture for better object classification")
	}

	if report.OverallQuality < 0.5 {
		recommendations = append(recommendations,
			"Consider rescanning with higher quality settings")
	}

	return recommendations
}
