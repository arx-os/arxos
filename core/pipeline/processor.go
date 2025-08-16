// Package pipeline provides the complete PDF to BIM conversion pipeline
package pipeline

import (
	"arxos/core/semantic"
	"arxos/core/topology"
	"fmt"
	"log"
	"time"
)

// ProcessorConfig contains pipeline configuration
type ProcessorConfig struct {
	// Clustering parameters
	ClusterEpsilon   float64
	ClusterMinPoints int
	
	// Semantic analysis
	EnableSemantic   bool
	BuildingTypology string
	
	// Quality thresholds
	MinConfidence      float64
	RequireManualReview bool
	
	// Processing options
	EnableOCR          bool
	EnableSymbolDetection bool
	ParallelProcessing bool
}

// DefaultConfig returns standard configuration
func DefaultConfig() ProcessorConfig {
	return ProcessorConfig{
		ClusterEpsilon:     0.005, // 0.5% of drawing size
		ClusterMinPoints:   3,
		EnableSemantic:     true,
		BuildingTypology:   "educational",
		MinConfidence:      0.85,
		RequireManualReview: true,
		EnableOCR:          true,
		EnableSymbolDetection: true,
		ParallelProcessing: true,
	}
}

// Processor handles the complete conversion pipeline
type Processor struct {
	config         ProcessorConfig
	semanticEngine *semantic.SemanticEngine
	reviewQueue    *ManualReviewQueue
	metrics        *ProcessingMetrics
}

// ProcessingMetrics tracks performance
type ProcessingMetrics struct {
	TotalProcessed     int
	SuccessfulCount    int
	RequiredReview     int
	AverageConfidence  float64
	AverageTime        time.Duration
	AccuracyRate       float64
}

// NewProcessor creates a configured processor
func NewProcessor(config ProcessorConfig) *Processor {
	return &Processor{
		config:         config,
		semanticEngine: semantic.NewSemanticEngine(),
		reviewQueue:    NewManualReviewQueue(),
		metrics:        &ProcessingMetrics{},
	}
}

// ProcessPDF converts PDF to BIM with confidence tracking
func (p *Processor) ProcessPDF(pdfPath string, metadata BuildingMetadata) (*ProcessingResult, error) {
	startTime := time.Now()
	
	result := &ProcessingResult{
		InputFile: pdfPath,
		Metadata:  metadata,
		StartTime: startTime,
		Status:    StatusProcessing,
	}
	
	// Stage 1: Extract segments from PDF
	log.Printf("Stage 1: Extracting segments from %s", pdfPath)
	segments, extractErr := p.extractSegments(pdfPath)
	if extractErr != nil {
		result.Status = StatusFailed
		result.Error = extractErr
		return result, extractErr
	}
	result.RawSegments = len(segments)
	
	// Stage 2: Geometric processing with DBSCAN
	log.Printf("Stage 2: Clustering %d segments", len(segments))
	mergedSegments, clusterResult := p.clusterSegments(segments)
	result.MergedSegments = len(mergedSegments)
	result.ClusteringResult = clusterResult
	
	// Stage 3: Build topology
	log.Printf("Stage 3: Building topology from %d merged segments", len(mergedSegments))
	building, topoErr := p.buildTopology(mergedSegments, metadata)
	if topoErr != nil {
		result.Status = StatusFailed
		result.Error = topoErr
		return result, topoErr
	}
	result.Building = building
	
	// Stage 4: Semantic analysis
	if p.config.EnableSemantic {
		log.Printf("Stage 4: Performing semantic analysis")
		semanticAnalysis := p.semanticEngine.AnalyzeBuilding(building, metadata.BuildingType)
		result.SemanticAnalysis = semanticAnalysis
		result.Confidence = semanticAnalysis.OverallConfidence
		
		// Add semantic violations as issues
		for _, violation := range semanticAnalysis.Violations {
			result.ValidationIssues = append(result.ValidationIssues, topology.ValidationIssue{
				Type:        topology.IssueTypeSemanticViolation,
				Severity:    violation.Severity,
				Description: violation.Description,
				AffectedIDs: violation.AffectedIDs,
			})
		}
	}
	
	// Stage 5: Validation
	log.Printf("Stage 5: Validating building topology")
	validationResult := p.validateBuilding(building)
	result.ValidationResult = validationResult
	result.ValidationIssues = append(result.ValidationIssues, validationResult.Issues...)
	
	// Calculate overall confidence
	result.Confidence = p.calculateOverallConfidence(result)
	
	// Stage 6: Determine if manual review needed
	if p.requiresManualReview(result) {
		log.Printf("Stage 6: Queuing for manual review (confidence: %.2f)", result.Confidence)
		result.Status = StatusPendingReview
		result.RequiresReview = true
		
		// Add to review queue
		reviewTask := p.reviewQueue.AddTask(result)
		result.ReviewTaskID = reviewTask.ID
	} else {
		result.Status = StatusCompleted
		log.Printf("Stage 6: Processing completed successfully (confidence: %.2f)", result.Confidence)
	}
	
	// Record metrics
	result.ProcessingTime = time.Since(startTime)
	p.updateMetrics(result)
	
	return result, nil
}

// ProcessingResult contains complete pipeline output
type ProcessingResult struct {
	// Input
	InputFile string
	Metadata  BuildingMetadata
	
	// Processing stages
	RawSegments      int
	MergedSegments   int
	ClusteringResult *topology.ClusterResult
	Building         *topology.Building
	
	// Analysis
	SemanticAnalysis *semantic.SemanticAnalysis
	ValidationResult *ValidationResult
	ValidationIssues []topology.ValidationIssue
	
	// Quality metrics
	Confidence     float64
	RequiresReview bool
	ReviewTaskID   string
	
	// Status
	Status         ProcessingStatus
	Error          error
	StartTime      time.Time
	ProcessingTime time.Duration
}

// ProcessingStatus tracks pipeline state
type ProcessingStatus string

const (
	StatusProcessing     ProcessingStatus = "processing"
	StatusPendingReview  ProcessingStatus = "pending_review"
	StatusInReview       ProcessingStatus = "in_review"
	StatusCompleted      ProcessingStatus = "completed"
	StatusFailed         ProcessingStatus = "failed"
)

// BuildingMetadata contains building information
type BuildingMetadata struct {
	BuildingID   string
	BuildingName string
	BuildingType string
	Address      string
	YearBuilt    int
	SchoolLevel  string // For educational buildings
	DistrictID   string
	PrototypeID  string // For standardized designs
}

// ValidationResult contains topology validation
type ValidationResult struct {
	Valid            bool
	Issues           []topology.ValidationIssue
	DisconnectedWalls int
	UnclosedRooms    int
	OverlappingWalls int
	TotalWalls       int
	TotalRooms       int
}

// extractSegments gets line segments from PDF
func (p *Processor) extractSegments(pdfPath string) ([]topology.LineSegment, error) {
	// TODO: Integrate with existing PDF extraction
	// This would call the JavaScript extraction or Go PDF parser
	
	// Placeholder implementation
	segments := []topology.LineSegment{
		{
			ID:        1,
			Start:     topology.Point2D{X: 0, Y: 0},
			End:       topology.Point2D{X: 10 * 1e9, Y: 0},
			Thickness: 200 * 1e6, // 200mm wall
			Source:    "pdf_vector",
		},
	}
	
	return segments, nil
}

// clusterSegments applies DBSCAN clustering
func (p *Processor) clusterSegments(segments []topology.LineSegment) ([]topology.LineSegment, *topology.ClusterResult) {
	merged, result := topology.ClusterEndpoints(
		segments,
		p.config.ClusterEpsilon,
		p.config.ClusterMinPoints,
	)
	
	// Apply collinear merging
	merged = topology.MergeCollinearSegments(merged, 0.087) // 5 degrees
	
	return merged, result
}

// buildTopology constructs building from segments
func (p *Processor) buildTopology(segments []topology.LineSegment, metadata BuildingMetadata) (*topology.Building, error) {
	building := &topology.Building{
		ID:    generateBuildingID(),
		Name:  metadata.BuildingName,
		Walls: make(map[uint64]*topology.Wall),
		Rooms: make(map[uint64]*topology.Room),
		Metadata: topology.BuildingMetadata{
			BuildingType: mapBuildingType(metadata.BuildingType),
			YearBuilt:    metadata.YearBuilt,
			SchoolLevel:  metadata.SchoolLevel,
			DistrictID:   metadata.DistrictID,
			PrototypeID:  metadata.PrototypeID,
		},
	}
	
	// Convert segments to walls
	for i, seg := range segments {
		wall := &topology.Wall{
			ID: uint64(i + 1),
			StartPoint: topology.Point3D{
				X: seg.Start.X,
				Y: seg.Start.Y,
				Z: 0,
			},
			EndPoint: topology.Point3D{
				X: seg.End.X,
				Y: seg.End.Y,
				Z: 0,
			},
			Thickness:  seg.Thickness,
			Height:     3 * 1e9, // 3m standard height
			Confidence: seg.Confidence,
		}
		building.Walls[wall.ID] = wall
	}
	
	// Build wall connectivity graph
	p.buildWallConnections(building)
	
	// Detect rooms from wall graph
	p.detectRooms(building)
	
	return building, nil
}

// buildWallConnections creates wall adjacency
func (p *Processor) buildWallConnections(building *topology.Building) {
	threshold := int64(1e7) // 10mm connection threshold
	
	for id1, wall1 := range building.Walls {
		for id2, wall2 := range building.Walls {
			if id1 >= id2 {
				continue
			}
			
			// Check if walls connect at endpoints
			if wallsConnect(wall1, wall2, threshold) {
				wall1.ConnectedWalls = append(wall1.ConnectedWalls, id2)
				wall2.ConnectedWalls = append(wall2.ConnectedWalls, id1)
			}
		}
	}
}

// detectRooms finds closed polygons
func (p *Processor) detectRooms(building *topology.Building) {
	// TODO: Implement planar graph face detection
	// This would use graph algorithms to find closed cycles
	
	// Placeholder: Create a sample room
	room := &topology.Room{
		ID:            1,
		BoundaryWalls: []uint64{1, 2, 3, 4},
		Area:          80 * 1e18, // 80 m²
		CeilingHeight: 3 * 1e9,
		Function:      topology.RoomFunctionClassroom,
	}
	
	building.Rooms[room.ID] = room
}

// validateBuilding checks topology integrity
func (p *Processor) validateBuilding(building *topology.Building) *ValidationResult {
	result := &ValidationResult{
		Valid:      true,
		TotalWalls: len(building.Walls),
		TotalRooms: len(building.Rooms),
	}
	
	// Check for disconnected walls
	for _, wall := range building.Walls {
		if len(wall.ConnectedWalls) == 0 {
			result.DisconnectedWalls++
			result.Issues = append(result.Issues, topology.ValidationIssue{
				Type:        topology.IssueTypeDisconnectedWall,
				Severity:    topology.SeverityWarning,
				Description: fmt.Sprintf("Wall %d is not connected to any other walls", wall.ID),
				AffectedIDs: []uint64{wall.ID},
			})
		}
	}
	
	// Check for unclosed rooms
	for _, room := range building.Rooms {
		if !isRoomClosed(room, building) {
			result.UnclosedRooms++
			result.Issues = append(result.Issues, topology.ValidationIssue{
				Type:        topology.IssueTypeUnclosedRoom,
				Severity:    topology.SeverityError,
				Description: fmt.Sprintf("Room %d has unclosed boundary", room.ID),
				AffectedIDs: []uint64{room.ID},
			})
		}
	}
	
	if result.DisconnectedWalls > 0 || result.UnclosedRooms > 0 {
		result.Valid = false
	}
	
	return result
}

// calculateOverallConfidence computes final confidence score
func (p *Processor) calculateOverallConfidence(result *ProcessingResult) float64 {
	confidence := 1.0
	
	// Reduce for clustering issues
	if result.ClusteringResult != nil {
		clusterRatio := float64(result.ClusteringResult.NumClusters) / float64(result.RawSegments)
		if clusterRatio > 0.1 { // More than 10% clustering
			confidence *= 0.9
		}
	}
	
	// Reduce for validation issues
	for _, issue := range result.ValidationIssues {
		switch issue.Severity {
		case topology.SeverityCritical:
			confidence *= 0.7
		case topology.SeverityError:
			confidence *= 0.85
		case topology.SeverityWarning:
			confidence *= 0.95
		}
	}
	
	// Include semantic confidence if available
	if result.SemanticAnalysis != nil {
		confidence = (confidence + result.SemanticAnalysis.OverallConfidence) / 2
	}
	
	return confidence
}

// requiresManualReview determines if human review needed
func (p *Processor) requiresManualReview(result *ProcessingResult) bool {
	// Always require review if configured
	if p.config.RequireManualReview {
		return true
	}
	
	// Require review if confidence below threshold
	if result.Confidence < p.config.MinConfidence {
		return true
	}
	
	// Require review for critical issues
	for _, issue := range result.ValidationIssues {
		if issue.Severity == topology.SeverityCritical {
			return true
		}
	}
	
	return false
}

// updateMetrics records processing statistics
func (p *Processor) updateMetrics(result *ProcessingResult) {
	p.metrics.TotalProcessed++
	
	if result.Status == StatusCompleted {
		p.metrics.SuccessfulCount++
	}
	
	if result.RequiresReview {
		p.metrics.RequiredReview++
	}
	
	// Update running averages
	p.metrics.AverageConfidence = (p.metrics.AverageConfidence*float64(p.metrics.TotalProcessed-1) + result.Confidence) / float64(p.metrics.TotalProcessed)
	p.metrics.AverageTime = (p.metrics.AverageTime*time.Duration(p.metrics.TotalProcessed-1) + result.ProcessingTime) / time.Duration(p.metrics.TotalProcessed)
	p.metrics.AccuracyRate = float64(p.metrics.SuccessfulCount) / float64(p.metrics.TotalProcessed)
}

// Helper functions

func generateBuildingID() uint64 {
	return uint64(time.Now().UnixNano())
}

func mapBuildingType(typeName string) topology.BuildingType {
	mapping := map[string]topology.BuildingType{
		"educational": topology.BuildingTypeEducational,
		"healthcare":  topology.BuildingTypeHealthcare,
		"office":      topology.BuildingTypeOffice,
		"residential": topology.BuildingTypeResidential,
		"industrial":  topology.BuildingTypeIndustrial,
		"retail":      topology.BuildingTypeRetail,
	}
	
	if t, exists := mapping[typeName]; exists {
		return t
	}
	return topology.BuildingTypeUnknown
}

func wallsConnect(wall1, wall2 *topology.Wall, threshold int64) bool {
	// Check all endpoint combinations
	dist1 := distance3D(wall1.StartPoint, wall2.StartPoint)
	dist2 := distance3D(wall1.StartPoint, wall2.EndPoint)
	dist3 := distance3D(wall1.EndPoint, wall2.StartPoint)
	dist4 := distance3D(wall1.EndPoint, wall2.EndPoint)
	
	return dist1 < threshold || dist2 < threshold || dist3 < threshold || dist4 < threshold
}

func distance3D(p1, p2 topology.Point3D) int64 {
	dx := p2.X - p1.X
	dy := p2.Y - p1.Y
	dz := p2.Z - p1.Z
	return int64(math.Sqrt(float64(dx*dx + dy*dy + dz*dz)))
}

func isRoomClosed(room *topology.Room, building *topology.Building) bool {
	// Check if boundary walls form a closed loop
	if len(room.BoundaryWalls) < 3 {
		return false
	}
	
	// TODO: Implement proper closed loop detection
	return true
}

// ManualReviewQueue manages tasks requiring human review
type ManualReviewQueue struct {
	tasks   []*ReviewTask
	pending int
}

type ReviewTask struct {
	ID        string
	Result    *ProcessingResult
	Status    ReviewStatus
	Reviewer  string
	StartTime time.Time
	EndTime   time.Time
}

type ReviewStatus string

const (
	ReviewPending    ReviewStatus = "pending"
	ReviewInProgress ReviewStatus = "in_progress"
	ReviewCompleted  ReviewStatus = "completed"
	ReviewRejected   ReviewStatus = "rejected"
)

func NewManualReviewQueue() *ManualReviewQueue {
	return &ManualReviewQueue{
		tasks: make([]*ReviewTask, 0),
	}
}

func (q *ManualReviewQueue) AddTask(result *ProcessingResult) *ReviewTask {
	task := &ReviewTask{
		ID:        fmt.Sprintf("review_%d", time.Now().UnixNano()),
		Result:    result,
		Status:    ReviewPending,
		StartTime: time.Now(),
	}
	
	q.tasks = append(q.tasks, task)
	q.pending++
	
	return task
}

func math.Sqrt(x float64) float64 {
	return x // Placeholder for actual math.Sqrt
}