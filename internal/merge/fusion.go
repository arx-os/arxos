package merge

import (
	"fmt"
	"math"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/lidar"
	"github.com/arx-os/arxos/internal/spatial"
)

// DataFusion handles multi-source data fusion for building models
type DataFusion struct {
	merger            *SmartMerger
	resolver          *ConflictResolver
	changeDetector    *ChangeDetector
	confidenceManager *spatial.ConfidenceManager
	coverageTracker   *spatial.CoverageTracker
	mu                sync.RWMutex
}

// NewDataFusion creates a new data fusion system
func NewDataFusion(
	confidenceManager *spatial.ConfidenceManager,
	coverageTracker *spatial.CoverageTracker,
) *DataFusion {
	return &DataFusion{
		merger:            NewSmartMerger(confidenceManager, coverageTracker),
		resolver:          NewConflictResolver(confidenceManager),
		changeDetector:    NewChangeDetector(),
		confidenceManager: confidenceManager,
		coverageTracker:   coverageTracker,
	}
}

// FusionResult represents the result of data fusion
type FusionResult struct {
	BuildingID      string              `json:"building_id"`
	Timestamp       time.Time           `json:"timestamp"`
	MergedEquipment []*MergedEquipment  `json:"merged_equipment"`
	Changes         []Change            `json:"changes"`
	Conflicts       []Conflict          `json:"conflicts"`
	Resolutions     []*ResolutionResult `json:"resolutions"`
	Coverage        float64             `json:"coverage_percentage"`
	ConfidenceScore float64             `json:"overall_confidence"`
	Statistics      FusionStatistics    `json:"statistics"`
}

// FusionStatistics contains statistics about the fusion process
type FusionStatistics struct {
	TotalSources           int                             `json:"total_sources"`
	SourceBreakdown        map[string]int                  `json:"source_breakdown"`
	EquipmentProcessed     int                             `json:"equipment_processed"`
	ConflictsDetected      int                             `json:"conflicts_detected"`
	ConflictsResolved      int                             `json:"conflicts_resolved"`
	ChangesDetected        int                             `json:"changes_detected"`
	AverageConfidence      float64                         `json:"average_confidence"`
	ConfidenceDistribution map[spatial.ConfidenceLevel]int `json:"confidence_distribution"`
	ProcessingTime         time.Duration                   `json:"processing_time"`
}

// FuseBuilding fuses all available data for a building
func (df *DataFusion) FuseBuilding(
	buildingID string,
	sources []DataSource,
	existingModel BuildingModel,
) (*FusionResult, error) {

	startTime := time.Now()
	result := &FusionResult{
		BuildingID:      buildingID,
		Timestamp:       time.Now(),
		MergedEquipment: make([]*MergedEquipment, 0),
		Changes:         make([]Change, 0),
		Conflicts:       make([]Conflict, 0),
		Resolutions:     make([]*ResolutionResult, 0),
	}

	// Group sources by equipment
	equipmentSources := df.groupSourcesByEquipment(sources)

	// Process each equipment
	for equipmentID, eqSources := range equipmentSources {
		// Merge equipment data
		merged, err := df.merger.MergeEquipmentData(equipmentID, eqSources)
		if err != nil {
			continue // Skip failed equipment
		}

		// Detect changes from existing model
		if existing := existingModel.GetEquipment(equipmentID); existing != nil {
			changes := df.changeDetector.DetectChanges(existing, merged)
			result.Changes = append(result.Changes, changes...)
		}

		// Resolve conflicts
		for _, conflict := range merged.Conflicts {
			resolution, err := df.resolver.ResolveConflict(conflict)
			if err == nil {
				result.Resolutions = append(result.Resolutions, resolution)
				// Apply resolution to merged equipment
				df.applyResolution(merged, conflict, resolution)
			}
		}

		result.MergedEquipment = append(result.MergedEquipment, merged)
		result.Conflicts = append(result.Conflicts, merged.Conflicts...)
	}

	// Calculate statistics
	result.Statistics = df.calculateStatistics(sources, result, time.Since(startTime))
	result.Coverage = df.coverageTracker.GetCoveragePercentage()
	result.ConfidenceScore = df.calculateOverallConfidence(result.MergedEquipment)

	return result, nil
}

// BuildingModel represents the existing building model
type BuildingModel interface {
	GetEquipment(id string) *MergedEquipment
	GetAllEquipment() []*MergedEquipment
	GetFloorPlan(floor int) interface{}
}

// groupSourcesByEquipment groups data sources by equipment ID
func (df *DataFusion) groupSourcesByEquipment(sources []DataSource) map[string][]DataSource {
	grouped := make(map[string][]DataSource)

	for _, source := range sources {
		// Extract equipment ID from source metadata
		if equipmentID := df.extractEquipmentID(source); equipmentID != "" {
			grouped[equipmentID] = append(grouped[equipmentID], source)
		}
	}

	return grouped
}

// extractEquipmentID extracts equipment ID from a data source
func (df *DataFusion) extractEquipmentID(source DataSource) string {
	if source.Metadata != nil {
		if id, ok := source.Metadata["equipment_id"].(string); ok {
			return id
		}
	}

	// Try to extract from data
	switch source.Type {
	case "lidar":
		if match, ok := source.Data.(*lidar.EquipmentMatch); ok {
			return match.EquipmentID
		}
	default:
		if data, ok := source.Data.(map[string]interface{}); ok {
			if id, ok := data["id"].(string); ok {
				return id
			}
		}
	}

	return ""
}

// applyResolution applies a resolution to merged equipment
func (df *DataFusion) applyResolution(
	merged *MergedEquipment,
	conflict Conflict,
	resolution *ResolutionResult,
) {
	if resolution.ResolvedValue == nil {
		return
	}

	switch conflict.Type {
	case "position":
		if pos, ok := resolution.ResolvedValue.(spatial.Point3D); ok {
			merged.Position = pos
		}
	case "dimension":
		if dims, ok := resolution.ResolvedValue.(Dimensions); ok {
			merged.Dimensions = dims
		}
	case "type":
		if eqType, ok := resolution.ResolvedValue.(string); ok {
			merged.Type = eqType
		}
	}

	// Update confidence based on resolution
	if resolution.Confidence > 0 {
		merged.Confidence = resolution.Confidence
	}
}

// calculateStatistics calculates fusion statistics
func (df *DataFusion) calculateStatistics(
	sources []DataSource,
	result *FusionResult,
	processingTime time.Duration,
) FusionStatistics {

	stats := FusionStatistics{
		TotalSources:           len(sources),
		SourceBreakdown:        make(map[string]int),
		EquipmentProcessed:     len(result.MergedEquipment),
		ConflictsDetected:      len(result.Conflicts),
		ConflictsResolved:      len(result.Resolutions),
		ChangesDetected:        len(result.Changes),
		ProcessingTime:         processingTime,
		ConfidenceDistribution: make(map[spatial.ConfidenceLevel]int),
	}

	// Count source types
	for _, source := range sources {
		stats.SourceBreakdown[source.Type]++
	}

	// Calculate confidence distribution
	var totalConfidence float64
	for _, equipment := range result.MergedEquipment {
		stats.ConfidenceDistribution[equipment.Confidence]++
		totalConfidence += float64(equipment.Confidence)
	}

	if stats.EquipmentProcessed > 0 {
		stats.AverageConfidence = totalConfidence / float64(stats.EquipmentProcessed)
	}

	return stats
}

// calculateOverallConfidence calculates overall confidence score
func (df *DataFusion) calculateOverallConfidence(equipment []*MergedEquipment) float64 {
	if len(equipment) == 0 {
		return 0
	}

	var totalScore float64
	for _, eq := range equipment {
		// Convert confidence level to score (0-1)
		score := float64(eq.Confidence) / 3.0
		// Weight by number of sources
		weight := math.Min(float64(len(eq.Sources))/5.0, 1.0)
		totalScore += score * (1 + weight*0.5)
	}

	return math.Min(totalScore/float64(len(equipment)), 1.0)
}

// FusePartialScan fuses a partial scan into the existing model
func (df *DataFusion) FusePartialScan(
	partialScan *lidar.PointCloud,
	existingModel BuildingModel,
	knownEquipment []lidar.KnownEquipment,
) (*PartialFusionResult, error) {

	// Process the LiDAR scan
	integrator := lidar.NewSpatialIntegrator(
		df.confidenceManager,
		df.coverageTracker,
	)

	integrationResult, err := integrator.ProcessAndIntegrate(
		partialScan,
		partialScan.Metadata.BuildingID,
		knownEquipment,
	)
	if err != nil {
		return nil, fmt.Errorf("failed to process scan: %w", err)
	}

	// Convert matches to data sources
	sources := make([]DataSource, 0, len(integrationResult.Matches))
	for _, match := range integrationResult.Matches {
		source := DataSource{
			ID:         fmt.Sprintf("lidar_%s_%d", match.EquipmentID, time.Now().Unix()),
			Type:       "lidar",
			Timestamp:  time.Now(),
			Confidence: match.Confidence,
			Data:       match,
			Metadata: map[string]interface{}{
				"equipment_id": match.EquipmentID,
				"scan_id":      partialScan.Metadata.ScanID,
			},
		}
		sources = append(sources, source)
	}

	// Fuse with existing model
	fusionResult, err := df.FuseBuilding(
		partialScan.Metadata.BuildingID,
		sources,
		existingModel,
	)
	if err != nil {
		return nil, err
	}

	return &PartialFusionResult{
		FusionResult:      fusionResult,
		IntegrationResult: integrationResult,
		NewEquipment:      df.identifyNewEquipment(integrationResult.UnmatchedObjects),
		RemovedEquipment:  df.identifyRemovedEquipment(existingModel, fusionResult),
	}, nil
}

// PartialFusionResult represents the result of partial scan fusion
type PartialFusionResult struct {
	*FusionResult
	IntegrationResult *lidar.IntegrationResult `json:"integration_result"`
	NewEquipment      []NewEquipment           `json:"new_equipment"`
	RemovedEquipment  []string                 `json:"removed_equipment"`
}

// NewEquipment represents newly detected equipment
type NewEquipment struct {
	DetectedObject *lidar.DetectedObject   `json:"detected_object"`
	SuggestedType  string                  `json:"suggested_type"`
	Confidence     spatial.ConfidenceLevel `json:"confidence"`
	Location       spatial.Point3D         `json:"location"`
}

// identifyNewEquipment identifies new equipment from unmatched objects
func (df *DataFusion) identifyNewEquipment(unmatched []*lidar.DetectedObject) []NewEquipment {
	newEquipment := make([]NewEquipment, 0, len(unmatched))

	for _, obj := range unmatched {
		new := NewEquipment{
			DetectedObject: obj,
			SuggestedType:  obj.ObjectClass,
			Confidence:     df.calculateObjectConfidence(obj),
			Location:       obj.Centroid,
		}
		newEquipment = append(newEquipment, new)
	}

	return newEquipment
}

// identifyRemovedEquipment identifies equipment that may have been removed
func (df *DataFusion) identifyRemovedEquipment(
	existingModel BuildingModel,
	fusionResult *FusionResult,
) []string {

	removed := make([]string, 0)
	mergedIDs := make(map[string]bool)

	for _, eq := range fusionResult.MergedEquipment {
		mergedIDs[eq.EquipmentID] = true
	}

	for _, existing := range existingModel.GetAllEquipment() {
		if !mergedIDs[existing.EquipmentID] {
			// Check if it's in an unscanned area
			if !df.isInScannedArea(existing.Position) {
				continue // Not in scanned area, can't determine if removed
			}
			removed = append(removed, existing.EquipmentID)
		}
	}

	return removed
}

// isInScannedArea checks if a position is in a scanned area
func (df *DataFusion) isInScannedArea(position spatial.Point3D) bool {
	// Check against coverage tracker
	confidence := df.coverageTracker.GetRegionConfidence(position)
	return confidence > spatial.ConfidenceEstimated
}

// calculateObjectConfidence calculates confidence for a detected object
func (df *DataFusion) calculateObjectConfidence(obj *lidar.DetectedObject) spatial.ConfidenceLevel {
	if obj.Confidence > 0.8 {
		return spatial.ConfidenceHigh
	} else if obj.Confidence > 0.6 {
		return spatial.ConfidenceMedium
	} else if obj.Confidence > 0.4 {
		return spatial.ConfidenceLow
	}
	return spatial.ConfidenceEstimated
}

// SetMergeStrategy sets the merge strategy
func (df *DataFusion) SetMergeStrategy(strategy MergeStrategy) {
	df.mu.Lock()
	defer df.mu.Unlock()
	df.merger.SetStrategy(strategy)
}

// SetResolutionMethod sets the default resolution method
func (df *DataFusion) SetResolutionMethod(method ResolutionMethod) {
	df.mu.Lock()
	defer df.mu.Unlock()
	df.resolver.SetDefaultMethod(method)
}

// GetStatistics returns fusion statistics for analysis
func (df *DataFusion) GetStatistics() map[string]interface{} {
	df.mu.RLock()
	defer df.mu.RUnlock()

	return map[string]interface{}{
		"resolution_history":  df.resolver.GetHistory(),
		"active_rules":        df.resolver.GetRules(),
		"coverage_percentage": df.coverageTracker.GetCoveragePercentage(),
		"recent_changes":      df.changeDetector.GetRecentChanges(24 * time.Hour),
	}
}
