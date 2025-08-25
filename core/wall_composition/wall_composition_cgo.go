package wall_composition

import (
	"fmt"
	"time"

	"github.com/arxos/arxos/core/cgo"
)

// =============================================================================
// CGO-OPTIMIZED WALL COMPOSITION SERVICE
// =============================================================================

// WallCompositionServiceCGO provides high-performance wall composition using the C core
type WallCompositionServiceCGO struct {
	engine *cgo.WallCompositionEngine
	config cgo.CompositionConfig
}

// NewWallCompositionServiceCGO creates a new CGO-optimized wall composition service
func NewWallCompositionServiceCGO(config cgo.CompositionConfig) (*WallCompositionServiceCGO, error) {
	engine, err := cgo.CreateWallCompositionEngine(config.MaxGapDistance, config.ParallelThreshold, config.ConfidenceThreshold)
	if err != nil {
		return nil, fmt.Errorf("failed to create wall composition engine: %w", err)
	}

	return &WallCompositionServiceCGO{
		engine: engine,
		config: config,
	}, nil
}

// Close frees the CGO resources
func (s *WallCompositionServiceCGO) Close() error {
	if s.engine != nil {
		s.engine.Destroy()
		s.engine = nil
	}
	return nil
}

// =============================================================================
// WALL SEGMENT OPERATIONS
// =============================================================================

// CreateWallSegment creates a new wall segment with CGO optimization
func (s *WallCompositionServiceCGO) CreateWallSegment(id uint64, startX, startY, startZ, endX, endY, endZ, height, thickness, confidence float64) (*cgo.WallSegment, error) {
	segment, err := cgo.CreateWallSegment(id, startX, startY, startZ, endX, endY, endZ, height, thickness, confidence)
	if err != nil {
		return nil, fmt.Errorf("failed to create wall segment: %w", err)
	}

	// Set additional properties
	segment.WallType = cgo.WallTypeInterior
	segment.CreatedAt = time.Now()

	return segment, nil
}

// CreateCurvedWallSegment creates a new curved wall segment with CGO optimization
func (s *WallCompositionServiceCGO) CreateCurvedWallSegment(id uint64, curveType cgo.CurveType, centerX, centerY, centerZ, radius, startAngle, endAngle, height, thickness, confidence float64) (*cgo.CurvedWallSegment, error) {
	segment, err := cgo.CreateCurvedWallSegment(id, curveType, centerX, centerY, centerZ, radius, startAngle, endAngle, height, thickness, confidence)
	if err != nil {
		return nil, fmt.Errorf("failed to create curved wall segment: %w", err)
	}

	return segment, nil
}

// =============================================================================
// WALL COMPOSITION OPERATIONS
// =============================================================================

// ComposeWalls composes walls from segments using CGO optimization
func (s *WallCompositionServiceCGO) ComposeWalls(segments []*cgo.WallSegment) ([]*cgo.WallStructure, error) {
	if s.engine == nil {
		return nil, fmt.Errorf("wall composition engine is not initialized")
	}

	// Use CGO-optimized composition
	structures, err := s.engine.ComposeWalls(segments)
	if err != nil {
		return nil, fmt.Errorf("failed to compose walls: %w", err)
	}

	// Post-process structures
	for _, structure := range structures {
		s.postProcessWallStructure(structure)
	}

	return structures, nil
}

// DetectConnections detects connections between wall segments using CGO optimization
func (s *WallCompositionServiceCGO) DetectConnections(segments []*cgo.WallSegment) ([]*cgo.WallConnection, error) {
	if s.engine == nil {
		return nil, fmt.Errorf("wall composition engine is not initialized")
	}

	// Use CGO-optimized connection detection
	connections, err := s.engine.DetectConnections(segments)
	if err != nil {
		return nil, fmt.Errorf("failed to detect connections: %w", err)
	}

	return connections, nil
}

// =============================================================================
// WALL STRUCTURE OPERATIONS
// =============================================================================

// GetWallStructureProperties gets properties from a wall structure using CGO
func (s *WallCompositionServiceCGO) GetWallStructureProperties(structure *cgo.WallStructure) (totalLength, maxHeight, overallConfidence float64) {
	return cgo.GetWallStructureProperties(structure)
}

// ValidateWallStructure validates a wall structure using CGO optimization
func (s *WallCompositionServiceCGO) ValidateWallStructure(structure *cgo.WallStructure) cgo.ValidationState {
	if structure == nil {
		return cgo.ValidationConflict
	}

	// Get properties using CGO
	totalLength, maxHeight, overallConfidence := s.GetWallStructureProperties(structure)

	// Validate based on configuration
	if totalLength < s.config.MinWallLength {
		return cgo.ValidationConflict
	}

	if totalLength > s.config.MaxWallLength {
		return cgo.ValidationConflict
	}

	if overallConfidence < s.config.ConfidenceThreshold {
		return cgo.ValidationPartial
	}

	// Check segment consistency
	if len(structure.Segments) == 0 {
		return cgo.ValidationConflict
	}

	// Validate individual segments
	validSegments := 0
	for _, segment := range structure.Segments {
		if segment.Confidence >= s.config.ConfidenceThreshold {
			validSegments++
		}
	}

	if validSegments == 0 {
		return cgo.ValidationConflict
	}

	if validSegments == len(structure.Segments) {
		return cgo.ValidationComplete
	}

	return cgo.ValidationPartial
}

// =============================================================================
// ADVANCED FEATURES
// =============================================================================

// AnalyzeWallComposition performs advanced analysis of wall composition
func (s *WallCompositionServiceCGO) AnalyzeWallComposition(structures []*cgo.WallStructure) *WallCompositionAnalysis {
	analysis := &WallCompositionAnalysis{
		TotalStructures:    len(structures),
		TotalSegments:      0,
		TotalLength:        0.0,
		MaxHeight:          0.0,
		AvgConfidence:      0.0,
		ValidationStats:    make(map[cgo.ValidationState]int),
		WallTypeStats:      make(map[cgo.WallType]int),
		ConnectionAnalysis: &ConnectionAnalysis{},
		PerformanceMetrics: &PerformanceMetrics{},
	}

	if len(structures) == 0 {
		return analysis
	}

	// Analyze structures
	totalConfidence := 0.0
	for _, structure := range structures {
		analysis.TotalSegments += len(structure.Segments)
		analysis.TotalLength += structure.TotalLength

		if structure.MaxHeight > analysis.MaxHeight {
			analysis.MaxHeight = structure.MaxHeight
		}

		totalConfidence += structure.OverallConfidence
		analysis.ValidationStats[structure.Validation]++
		analysis.WallTypeStats[structure.PrimaryWallType]++
	}

	analysis.AvgConfidence = totalConfidence / float64(len(structures))

	return analysis
}

// OptimizeWallComposition optimizes wall composition for better performance
func (s *WallCompositionServiceCGO) OptimizeWallComposition(structures []*cgo.WallStructure) ([]*cgo.WallStructure, error) {
	if len(structures) == 0 {
		return structures, nil
	}

	// Filter by confidence threshold
	optimizedStructures := make([]*cgo.WallStructure, 0, len(structures))
	for _, structure := range structures {
		if structure.OverallConfidence >= s.config.ConfidenceThreshold {
			optimizedStructures = append(optimizedStructures, structure)
		}
	}

	// Sort by confidence (highest first)
	// This is a simple optimization - in production, you might want more sophisticated sorting
	for i := 0; i < len(optimizedStructures)-1; i++ {
		for j := i + 1; j < len(optimizedStructures); j++ {
			if optimizedStructures[i].OverallConfidence < optimizedStructures[j].OverallConfidence {
				optimizedStructures[i], optimizedStructures[j] = optimizedStructures[j], optimizedStructures[i]
			}
		}
	}

	return optimizedStructures, nil
}

// =============================================================================
// HELPER FUNCTIONS
// =============================================================================

// postProcessWallStructure performs post-processing on a wall structure
func (s *WallCompositionServiceCGO) postProcessWallStructure(structure *cgo.WallStructure) {
	if structure == nil {
		return
	}

	// Set metadata if not already set
	if structure.BuildingID == "" {
		structure.BuildingID = "default"
	}
	if structure.FloorID == "" {
		structure.FloorID = "ground"
	}
	if structure.RoomID == "" {
		structure.RoomID = "unknown"
	}

	// Update timestamps
	structure.UpdatedAt = time.Now()
	if structure.CreatedAt.IsZero() {
		structure.CreatedAt = time.Now()
	}

	// Determine primary wall type based on segments
	if len(structure.Segments) > 0 {
		wallTypeCounts := make(map[cgo.WallType]int)
		for _, segment := range structure.Segments {
			wallTypeCounts[segment.WallType]++
		}

		// Find most common wall type
		maxCount := 0
		var primaryType cgo.WallType
		for wallType, count := range wallTypeCounts {
			if count > maxCount {
				maxCount = count
				primaryType = wallType
			}
		}
		structure.PrimaryWallType = primaryType
	}
}

// =============================================================================
// ANALYSIS STRUCTURES
// =============================================================================

// WallCompositionAnalysis provides comprehensive analysis of wall composition
type WallCompositionAnalysis struct {
	TotalStructures    int
	TotalSegments      int
	TotalLength        float64
	MaxHeight          float64
	AvgConfidence      float64
	ValidationStats    map[cgo.ValidationState]int
	WallTypeStats      map[cgo.WallType]int
	ConnectionAnalysis *ConnectionAnalysis
	PerformanceMetrics *PerformanceMetrics
}

// ConnectionAnalysis provides analysis of wall connections
type ConnectionAnalysis struct {
	TotalConnections   int
	ParallelWalls      int
	PerpendicularWalls int
	ConnectedWalls     int
	AvgGapDistance     float64
	AvgAngleDifference float64
}

// PerformanceMetrics provides performance metrics for wall composition
type PerformanceMetrics struct {
	CompositionTimeMs float64
	ConnectionTimeMs  float64
	ValidationTimeMs  float64
	MemoryUsageMB     float64
	CPUUsagePercent   float64
}

// =============================================================================
// CONFIGURATION HELPERS
// =============================================================================

// GetDefaultConfig returns the default configuration for wall composition
func GetDefaultConfig() cgo.CompositionConfig {
	return cgo.DefaultCompositionConfig()
}

// GetAdvancedConfig returns an advanced configuration for wall composition
func GetAdvancedConfig() cgo.CompositionConfig {
	config := cgo.DefaultCompositionConfig()
	config.SetAdvanced(true)
	return config
}

// GetHighPerformanceConfig returns a high-performance configuration
func GetHighPerformanceConfig() cgo.CompositionConfig {
	config := cgo.DefaultCompositionConfig()
	config.MaxGapDistance = 25.0     // Tighter gap tolerance
	config.ParallelThreshold = 2.0   // Tighter parallel tolerance
	config.ConfidenceThreshold = 0.8 // Higher confidence threshold
	config.EnableAdvancedValidation = true
	return config
}

// GetHighAccuracyConfig returns a high-accuracy configuration
func GetHighAccuracyConfig() cgo.CompositionConfig {
	config := cgo.DefaultCompositionConfig()
	config.MaxGapDistance = 10.0     // Very tight gap tolerance
	config.ParallelThreshold = 1.0   // Very tight parallel tolerance
	config.ConfidenceThreshold = 0.9 // Very high confidence threshold
	config.EnableAdvancedValidation = true
	config.MaxCurveApproximationPoints = 128
	return config
}
