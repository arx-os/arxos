package merge

import (
	"fmt"
	"math"
	"sort"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/lidar"
	"github.com/arx-os/arxos/internal/spatial"
)

// DataSource represents a source of spatial data
type DataSource struct {
	ID         string                  `json:"id"`
	Type       string                  `json:"type"` // "pdf", "ifc", "lidar", "ar"
	Timestamp  time.Time               `json:"timestamp"`
	Confidence spatial.ConfidenceLevel `json:"confidence"`
	Data       interface{}             `json:"data"`
	Metadata   map[string]interface{}  `json:"metadata"`
}

// MergeStrategy defines how to merge data from multiple sources
type MergeStrategy string

const (
	// StrategyHighestConfidence uses data from the most confident source
	StrategyHighestConfidence MergeStrategy = "highest_confidence"
	// StrategyMostRecent uses the most recent data
	StrategyMostRecent MergeStrategy = "most_recent"
	// StrategyWeightedAverage uses weighted average based on confidence
	StrategyWeightedAverage MergeStrategy = "weighted_average"
	// StrategyConsensus requires agreement between sources
	StrategyConsensus MergeStrategy = "consensus"
)

// SmartMerger intelligently merges data from multiple sources
type SmartMerger struct {
	confidenceManager *spatial.ConfidenceManager
	coverageTracker   *spatial.CoverageTracker
	strategy          MergeStrategy
	conflictThreshold float64 // Distance threshold for conflict detection
	mu                sync.RWMutex
}

// NewSmartMerger creates a new smart merger
func NewSmartMerger(
	confidenceManager *spatial.ConfidenceManager,
	coverageTracker *spatial.CoverageTracker,
) *SmartMerger {
	return &SmartMerger{
		confidenceManager: confidenceManager,
		coverageTracker:   coverageTracker,
		strategy:          StrategyHighestConfidence,
		conflictThreshold: 0.5, // 50cm default
	}
}

// SetStrategy sets the merge strategy
func (m *SmartMerger) SetStrategy(strategy MergeStrategy) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.strategy = strategy
}

// SetConflictThreshold sets the distance threshold for conflict detection
func (m *SmartMerger) SetConflictThreshold(threshold float64) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.conflictThreshold = threshold
}

// MergeEquipmentData merges equipment data from multiple sources
func (m *SmartMerger) MergeEquipmentData(
	equipmentID string,
	sources []DataSource,
) (*MergedEquipment, error) {

	if len(sources) == 0 {
		return nil, fmt.Errorf("no data sources provided")
	}

	// Sort sources by strategy
	sortedSources := m.sortSources(sources)

	// Extract equipment data from each source
	equipmentData := make([]*EquipmentData, 0, len(sources))
	for _, source := range sortedSources {
		data, err := m.extractEquipmentData(source)
		if err != nil {
			continue // Skip invalid sources
		}
		equipmentData = append(equipmentData, data)
	}

	if len(equipmentData) == 0 {
		return nil, fmt.Errorf("no valid equipment data found")
	}

	// Detect conflicts
	conflicts := m.detectConflicts(equipmentData)

	// Set equipment ID for all conflicts
	for i := range conflicts {
		conflicts[i].EquipmentID = equipmentID
	}

	// Merge based on strategy
	merged := m.mergeByStrategy(equipmentData, conflicts)
	merged.EquipmentID = equipmentID
	merged.Sources = sources
	merged.Conflicts = conflicts
	merged.MergeTimestamp = time.Now()

	// Update confidence
	if m.confidenceManager != nil {
		m.updateConfidence(merged)
	}

	return merged, nil
}

// EquipmentData represents equipment from a single source
type EquipmentData struct {
	Source      DataSource      `json:"source"`
	Position    spatial.Point3D `json:"position"`
	Dimensions  Dimensions      `json:"dimensions"`
	Type        string          `json:"type"`
	Attributes  map[string]interface{} `json:"attributes"`
	Confidence  spatial.ConfidenceLevel `json:"confidence"`
}

// Dimensions represents equipment dimensions
type Dimensions struct {
	Length float64 `json:"length"`
	Width  float64 `json:"width"`
	Height float64 `json:"height"`
}

// MergedEquipment represents merged equipment data
type MergedEquipment struct {
	EquipmentID    string                  `json:"equipment_id"`
	Position       spatial.Point3D         `json:"position"`
	Dimensions     Dimensions              `json:"dimensions"`
	Type           string                  `json:"type"`
	Attributes     map[string]interface{}  `json:"attributes"`
	Confidence     spatial.ConfidenceLevel `json:"confidence"`
	Sources        []DataSource            `json:"sources"`
	Conflicts      []Conflict              `json:"conflicts"`
	MergeStrategy  MergeStrategy           `json:"merge_strategy"`
	MergeTimestamp time.Time               `json:"merge_timestamp"`
}

// Conflict represents a conflict between data sources
type Conflict struct {
	ID          string      `json:"id"`
	EquipmentID string      `json:"equipment_id"`
	Type        string      `json:"type"` // "position", "dimension", "type"
	Source1     DataSource  `json:"source1"`
	Source2     DataSource  `json:"source2"`
	Value1      interface{} `json:"value1"`
	Value2      interface{} `json:"value2"`
	Difference  float64     `json:"difference"`
	Resolution  string      `json:"resolution"`
}

// sortSources sorts data sources based on merge strategy
func (m *SmartMerger) sortSources(sources []DataSource) []DataSource {
	sorted := make([]DataSource, len(sources))
	copy(sorted, sources)

	switch m.strategy {
	case StrategyHighestConfidence:
		sort.Slice(sorted, func(i, j int) bool {
			return sorted[i].Confidence > sorted[j].Confidence
		})
	case StrategyMostRecent:
		sort.Slice(sorted, func(i, j int) bool {
			return sorted[i].Timestamp.After(sorted[j].Timestamp)
		})
	}

	return sorted
}

// extractEquipmentData extracts equipment data from a source
func (m *SmartMerger) extractEquipmentData(source DataSource) (*EquipmentData, error) {
	data := &EquipmentData{
		Source:     source,
		Confidence: source.Confidence,
		Attributes: make(map[string]interface{}),
	}

	switch source.Type {
	case "lidar":
		// Try to extract from lidar.EquipmentMatch first
		if match, ok := source.Data.(*lidar.EquipmentMatch); ok {
			data.Position = match.DetectedObject.Centroid
			data.Dimensions = Dimensions{
				Length: match.DetectedObject.Features.Dimensions.Length,
				Width:  match.DetectedObject.Features.Dimensions.Width,
				Height: match.DetectedObject.Features.Dimensions.Height,
			}
			data.Type = match.EquipmentType
		} else if genericData, ok := source.Data.(map[string]interface{}); ok {
			// Fall back to generic map extraction for lidar test data
			if pos, ok := genericData["position"].(spatial.Point3D); ok {
				data.Position = pos
			}
			if dims, ok := genericData["dimensions"].(Dimensions); ok {
				data.Dimensions = dims
			}
			if eqType, ok := genericData["type"].(string); ok {
				data.Type = eqType
			}
		}
	case "pdf", "ifc":
		// Extract from PDF/IFC data structures
		if equipment, ok := source.Data.(map[string]interface{}); ok {
			if pos, ok := equipment["position"].(spatial.Point3D); ok {
				data.Position = pos
			}
			if dims, ok := equipment["dimensions"].(Dimensions); ok {
				data.Dimensions = dims
			}
			if eqType, ok := equipment["type"].(string); ok {
				data.Type = eqType
			}
		}
	case "ar", "manual":
		// Extract from AR or manual data
		if arData, ok := source.Data.(map[string]interface{}); ok {
			if pos, ok := arData["position"].(spatial.Point3D); ok {
				data.Position = pos
			}
			if dims, ok := arData["dimensions"].(Dimensions); ok {
				data.Dimensions = dims
			}
			if eqType, ok := arData["type"].(string); ok {
				data.Type = eqType
			}
		}
	default:
		// Default: try to extract from generic map
		if genericData, ok := source.Data.(map[string]interface{}); ok {
			if pos, ok := genericData["position"].(spatial.Point3D); ok {
				data.Position = pos
			}
			if dims, ok := genericData["dimensions"].(Dimensions); ok {
				data.Dimensions = dims
			}
			if eqType, ok := genericData["type"].(string); ok {
				data.Type = eqType
			}
		}
	}

	return data, nil
}

// detectConflicts detects conflicts between data sources
func (m *SmartMerger) detectConflicts(equipmentData []*EquipmentData) []Conflict {
	conflicts := make([]Conflict, 0)

	for i := 0; i < len(equipmentData)-1; i++ {
		for j := i + 1; j < len(equipmentData); j++ {
			data1 := equipmentData[i]
			data2 := equipmentData[j]

			// Check position conflict
			distance := data1.Position.DistanceTo(data2.Position)
			if distance > m.conflictThreshold {
				conflicts = append(conflicts, Conflict{
					ID:          fmt.Sprintf("conflict_%d", time.Now().UnixNano()),
					EquipmentID: "", // Will be set by caller
					Type:        "position",
					Source1:     data1.Source,
					Source2:     data2.Source,
					Value1:      data1.Position,
					Value2:      data2.Position,
					Difference:  distance,
					Resolution:  m.suggestResolution("position", distance),
				})
			}

			// Check dimension conflict
			dimDiff := m.calculateDimensionDifference(data1.Dimensions, data2.Dimensions)
			if dimDiff > 0.2 { // 20% difference
				conflicts = append(conflicts, Conflict{
					ID:          fmt.Sprintf("conflict_%d", time.Now().UnixNano()),
					EquipmentID: "", // Will be set by caller
					Type:        "dimension",
					Source1:     data1.Source,
					Source2:     data2.Source,
					Value1:      data1.Dimensions,
					Value2:      data2.Dimensions,
					Difference:  dimDiff,
					Resolution:  m.suggestResolution("dimension", dimDiff),
				})
			}

			// Check type conflict
			if data1.Type != data2.Type && data1.Type != "" && data2.Type != "" {
				conflicts = append(conflicts, Conflict{
					ID:          fmt.Sprintf("conflict_%d", time.Now().UnixNano()),
					EquipmentID: "", // Will be set by caller
					Type:        "type",
					Source1:     data1.Source,
					Source2:     data2.Source,
					Value1:      data1.Type,
					Value2:      data2.Type,
					Difference:  1.0,
					Resolution:  m.suggestResolution("type", 1.0),
				})
			}
		}
	}

	return conflicts
}

// calculateDimensionDifference calculates relative difference between dimensions
func (m *SmartMerger) calculateDimensionDifference(d1, d2 Dimensions) float64 {
	lengthDiff := math.Abs(d1.Length-d2.Length) / math.Max(d1.Length, d2.Length)
	widthDiff := math.Abs(d1.Width-d2.Width) / math.Max(d1.Width, d2.Width)
	heightDiff := math.Abs(d1.Height-d2.Height) / math.Max(d1.Height, d2.Height)
	return (lengthDiff + widthDiff + heightDiff) / 3.0
}

// suggestResolution suggests how to resolve a conflict
func (m *SmartMerger) suggestResolution(conflictType string, difference float64) string {
	switch conflictType {
	case "position":
		if difference < 1.0 {
			return "use_highest_confidence"
		} else if difference < 3.0 {
			return "manual_verification_recommended"
		}
		return "field_verification_required"
	case "dimension":
		if difference < 0.1 {
			return "average_values"
		} else if difference < 0.3 {
			return "use_lidar_measurement"
		}
		return "remeasure_equipment"
	case "type":
		return "use_highest_confidence_source"
	default:
		return "manual_review"
	}
}

// mergeByStrategy merges equipment data based on selected strategy
func (m *SmartMerger) mergeByStrategy(equipmentData []*EquipmentData, conflicts []Conflict) *MergedEquipment {
	merged := &MergedEquipment{
		MergeStrategy: m.strategy,
		Attributes:    make(map[string]interface{}),
	}

	switch m.strategy {
	case StrategyHighestConfidence:
		// Use data from highest confidence source
		if len(equipmentData) > 0 {
			best := equipmentData[0]
			merged.Position = best.Position
			merged.Dimensions = best.Dimensions
			merged.Type = best.Type
			merged.Confidence = best.Confidence
			merged.Attributes = best.Attributes
		}

	case StrategyWeightedAverage:
		// Calculate weighted average for position and dimensions
		var totalWeight float64
		var weightedPos spatial.Point3D
		var weightedDims Dimensions

		for _, data := range equipmentData {
			weight := float64(data.Confidence) + 1 // Add 1 to avoid zero weight
			totalWeight += weight

			weightedPos.X += data.Position.X * weight
			weightedPos.Y += data.Position.Y * weight
			weightedPos.Z += data.Position.Z * weight

			weightedDims.Length += data.Dimensions.Length * weight
			weightedDims.Width += data.Dimensions.Width * weight
			weightedDims.Height += data.Dimensions.Height * weight
		}

		if totalWeight > 0 {
			merged.Position = spatial.Point3D{
				X: weightedPos.X / totalWeight,
				Y: weightedPos.Y / totalWeight,
				Z: weightedPos.Z / totalWeight,
			}
			merged.Dimensions = Dimensions{
				Length: weightedDims.Length / totalWeight,
				Width:  weightedDims.Width / totalWeight,
				Height: weightedDims.Height / totalWeight,
			}
		}

		// Use type from highest confidence
		if len(equipmentData) > 0 {
			merged.Type = equipmentData[0].Type
			merged.Confidence = m.calculateMergedConfidence(equipmentData)
		}

	case StrategyConsensus:
		// Require agreement between sources
		if len(conflicts) == 0 && len(equipmentData) > 1 {
			// No conflicts, use average
			var sumPos spatial.Point3D
			var sumDims Dimensions

			for _, data := range equipmentData {
				sumPos = sumPos.Add(data.Position)
				sumDims.Length += data.Dimensions.Length
				sumDims.Width += data.Dimensions.Width
				sumDims.Height += data.Dimensions.Height
			}

			n := float64(len(equipmentData))
			merged.Position = sumPos.Scale(1.0 / n)
			merged.Dimensions = Dimensions{
				Length: sumDims.Length / n,
				Width:  sumDims.Width / n,
				Height: sumDims.Height / n,
			}
			merged.Confidence = spatial.ConfidenceHigh
		} else {
			// Has conflicts or single source, use highest confidence
			if len(equipmentData) > 0 {
				best := equipmentData[0]
				merged.Position = best.Position
				merged.Dimensions = best.Dimensions
				merged.Type = best.Type
				merged.Confidence = spatial.ConfidenceMedium // Reduced due to conflicts
			}
		}

	case StrategyMostRecent:
		// Use most recent data
		if len(equipmentData) > 0 {
			recent := equipmentData[0]
			merged.Position = recent.Position
			merged.Dimensions = recent.Dimensions
			merged.Type = recent.Type
			merged.Confidence = recent.Confidence
			merged.Attributes = recent.Attributes
		}
	}

	return merged
}

// calculateMergedConfidence calculates confidence for merged data
func (m *SmartMerger) calculateMergedConfidence(equipmentData []*EquipmentData) spatial.ConfidenceLevel {
	if len(equipmentData) == 0 {
		return spatial.ConfidenceEstimated
	}

	// Average confidence levels
	var sum int
	for _, data := range equipmentData {
		sum += int(data.Confidence)
	}

	avg := sum / len(equipmentData)
	return spatial.ConfidenceLevel(avg)
}

// updateConfidence updates the confidence system
func (m *SmartMerger) updateConfidence(merged *MergedEquipment) {
	// Update position confidence
	m.confidenceManager.UpdateConfidence(
		merged.EquipmentID,
		spatial.AspectPosition,
		merged.Confidence,
		"merge",
	)

	// Update semantic confidence if type is known
	if merged.Type != "" {
		m.confidenceManager.UpdateConfidence(
			merged.EquipmentID,
			spatial.AspectSemantic,
			merged.Confidence,
			"merge",
		)
	}
}

// MergeSpatialRegions merges overlapping spatial regions
func (m *SmartMerger) MergeSpatialRegions(
	regions []spatial.ScannedRegion,
) (*spatial.ScannedRegion, error) {

	if len(regions) == 0 {
		return nil, fmt.Errorf("no regions to merge")
	}

	if len(regions) == 1 {
		return &regions[0], nil
	}

	// Combine all boundary points
	allPoints := make([]spatial.Point2D, 0)
	var maxConfidence float64
	var latestScan time.Time
	var totalDensity float64
	var count float64

	for _, region := range regions {
		allPoints = append(allPoints, region.Region.Boundary...)
		if region.Confidence > maxConfidence {
			maxConfidence = region.Confidence
		}
		if region.ScanDate.After(latestScan) {
			latestScan = region.ScanDate
		}
		totalDensity += region.PointDensity
		count++
	}

	// Calculate convex hull (simplified - just use bounding box)
	minX, minY := allPoints[0].X, allPoints[0].Y
	maxX, maxY := allPoints[0].X, allPoints[0].Y
	minZ, maxZ := regions[0].Region.MinZ, regions[0].Region.MaxZ

	for _, p := range allPoints {
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

	for _, region := range regions {
		if region.Region.MinZ < minZ {
			minZ = region.Region.MinZ
		}
		if region.Region.MaxZ > maxZ {
			maxZ = region.Region.MaxZ
		}
	}

	mergedRegion := &spatial.ScannedRegion{
		ID:         fmt.Sprintf("merged_%d", time.Now().Unix()),
		BuildingID: regions[0].BuildingID,
		Region: spatial.SpatialExtent{
			Boundary: []spatial.Point2D{
				{X: minX, Y: minY},
				{X: maxX, Y: minY},
				{X: maxX, Y: maxY},
				{X: minX, Y: maxY},
			},
			MinZ: minZ,
			MaxZ: maxZ,
		},
		ScanDate:     latestScan,
		ScanType:     "merged",
		PointDensity: totalDensity / count,
		Confidence:   maxConfidence,
	}

	return mergedRegion, nil
}