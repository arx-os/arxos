package ingestion

import (
	"fmt"
	"time"

	"github.com/arxos/arxos/core/arxobject"
)

// IngestionPipeline orchestrates the complete building data ingestion process
type IngestionPipeline struct {
	registry    *ProcessorRegistry
	validator   *ValidationEngine
	merger      *ObjectMerger
	confidence  *ConfidenceEngine
}

// NewIngestionPipeline creates a new pipeline instance
func NewIngestionPipeline() *IngestionPipeline {
	return &IngestionPipeline{
		registry:    NewProcessorRegistry(),
		validator:   NewValidationEngine(),
		merger:      NewObjectMerger(),
		confidence:  NewConfidenceEngine(),
	}
}

// PipelineRequest contains all files and processing options
type PipelineRequest struct {
	Files           []string                `json:"files"`
	BuildingMetadata BuildingMetadata       `json:"building_metadata"`
	ProcessingOptions ProcessingOptions     `json:"processing_options"`
}

// BuildingMetadata contains building-specific information
type BuildingMetadata struct {
	Name         string  `json:"name"`
	Address      string  `json:"address"`
	BuildingType string  `json:"building_type"`
	YearBuilt    int     `json:"year_built"`
	TotalArea    float64 `json:"total_area_sqft"`
	NumFloors    int     `json:"num_floors"`
}

// ProcessingOptions contains processing configuration
type ProcessingOptions struct {
	EnableMerging       bool    `json:"enable_merging"`
	MinConfidence       float64 `json:"min_confidence"`
	RequireValidation   bool    `json:"require_validation"`
	CoordinateSystem    string  `json:"coordinate_system"`
	UnitsOfMeasure      string  `json:"units_of_measure"`
}

// PipelineResult contains the complete processing result
type PipelineResult struct {
	BuildingID       string                   `json:"building_id"`
	Objects          []arxobject.ArxObject    `json:"objects"`
	Statistics       PipelineStatistics       `json:"statistics"`
	ValidationQueue  []ValidationItem         `json:"validation_queue"`
	ProcessingSteps  []ProcessingStep         `json:"processing_steps"`
	OverallConfidence float64                 `json:"overall_confidence"`
	Warnings         []string                 `json:"warnings"`
	Errors           []string                 `json:"errors"`
	ProcessingTime   time.Duration            `json:"processing_time"`
}

// PipelineStatistics contains comprehensive statistics
type PipelineStatistics struct {
	TotalFiles        int                     `json:"total_files"`
	ProcessedFiles    int                     `json:"processed_files"`
	FailedFiles       int                     `json:"failed_files"`
	TotalObjects      int                     `json:"total_objects"`
	ObjectsByType     map[string]int          `json:"objects_by_type"`
	ObjectsBySystem   map[string]int          `json:"objects_by_system"`
	ConfidenceStats   ConfidenceStatistics    `json:"confidence_stats"`
	FormatStats       map[string]FormatStats  `json:"format_stats"`
	ProcessingTime    time.Duration           `json:"processing_time"`
}

// ProcessingStep tracks each step in the pipeline
type ProcessingStep struct {
	StepName      string        `json:"step_name"`
	ProcessorType string        `json:"processor_type"`
	FilePath      string        `json:"file_path"`
	StartTime     time.Time     `json:"start_time"`
	Duration      time.Duration `json:"duration"`
	ObjectsFound  int           `json:"objects_found"`
	Confidence    float64       `json:"confidence"`
	Success       bool          `json:"success"`
	Warnings      []string      `json:"warnings"`
	Error         string        `json:"error,omitempty"`
}

// FormatStats contains statistics for each file format
type FormatStats struct {
	FileCount     int     `json:"file_count"`
	ObjectCount   int     `json:"object_count"`
	AvgConfidence float64 `json:"avg_confidence"`
	ProcessingTime time.Duration `json:"processing_time"`
}

// ConfidenceStatistics contains confidence metrics
type ConfidenceStatistics struct {
	Overall     float64 `json:"overall"`
	Average     float64 `json:"average"`
	Median      float64 `json:"median"`
	Minimum     float64 `json:"minimum"`
	Maximum     float64 `json:"maximum"`
	StdDev      float64 `json:"std_dev"`
	Distribution map[string]int `json:"distribution"` // confidence ranges
}

// ProcessBuilding runs the complete ingestion pipeline
func (p *IngestionPipeline) ProcessBuilding(request PipelineRequest) (*PipelineResult, error) {
	startTime := time.Now()
	
	result := &PipelineResult{
		BuildingID:      generateUUID(),
		Objects:         []arxobject.ArxObject{},
		ProcessingSteps: []ProcessingStep{},
		Warnings:        []string{},
		Errors:          []string{},
	}
	
	// Initialize statistics
	result.Statistics = PipelineStatistics{
		TotalFiles:      len(request.Files),
		ObjectsByType:   make(map[string]int),
		ObjectsBySystem: make(map[string]int),
		FormatStats:     make(map[string]FormatStats),
	}
	
	// Step 1: Process each file
	for _, filePath := range request.Files {
		step := p.processFile(filePath, request.ProcessingOptions)
		result.ProcessingSteps = append(result.ProcessingSteps, step)
		
		if step.Success {
			result.Statistics.ProcessedFiles++
		} else {
			result.Statistics.FailedFiles++
			result.Errors = append(result.Errors, step.Error)
		}
	}
	
	// Step 2: Collect all objects from successful steps
	for _, step := range result.ProcessingSteps {
		if step.Success {
			// In a real implementation, we'd get the actual objects from the step
			// For now, simulate by getting objects from the processor
			processor := p.registry.GetProcessor(step.FilePath)
			if processor != nil {
				stepResult, err := processor.Process(step.FilePath)
				if err == nil {
					result.Objects = append(result.Objects, stepResult.Objects...)
					
					// Update statistics
					for _, obj := range stepResult.Objects {
						result.Statistics.ObjectsByType[obj.Type]++
						result.Statistics.ObjectsBySystem[obj.System]++
					}
					
					// Collect warnings
					if stepResult.Warnings != nil {
						result.Warnings = append(result.Warnings, stepResult.Warnings...)
					}
				}
			}
		}
	}
	
	// Step 3: Merge duplicate objects if enabled
	if request.ProcessingOptions.EnableMerging {
		mergeStep := p.mergeObjects(result.Objects)
		result.ProcessingSteps = append(result.ProcessingSteps, mergeStep)
		// result.Objects would be updated with merged objects
	}
	
	// Step 4: Generate validation queue
	result.ValidationQueue = p.generateValidationQueue(result.Objects, request.ProcessingOptions)
	
	// Step 5: Calculate confidence metrics
	result.OverallConfidence = p.calculateOverallConfidence(result.Objects)
	result.Statistics.ConfidenceStats = p.calculateConfidenceStats(result.Objects)
	
	// Step 6: Update final statistics
	result.Statistics.TotalObjects = len(result.Objects)
	result.ProcessingTime = time.Since(startTime)
	result.Statistics.ProcessingTime = result.ProcessingTime
	
	return result, nil
}

// processFile processes a single file using the appropriate processor
func (p *IngestionPipeline) processFile(filePath string, options ProcessingOptions) ProcessingStep {
	step := ProcessingStep{
		StepName:  "file_processing",
		FilePath:  filePath,
		StartTime: time.Now(),
	}
	
	processor := p.registry.GetProcessor(filePath)
	if processor == nil {
		step.Success = false
		step.Error = fmt.Sprintf("no processor found for file: %s", filePath)
		step.Duration = time.Since(step.StartTime)
		return step
	}
	
	step.ProcessorType = fmt.Sprintf("%T", processor)
	
	result, err := processor.Process(filePath)
	step.Duration = time.Since(step.StartTime)
	
	if err != nil {
		step.Success = false
		step.Error = err.Error()
		return step
	}
	
	step.Success = true
	step.ObjectsFound = len(result.Objects)
	step.Confidence = result.Confidence
	step.Warnings = result.Warnings
	
	return step
}

// mergeObjects attempts to merge duplicate or overlapping objects
func (p *IngestionPipeline) mergeObjects(objects []arxobject.ArxObject) ProcessingStep {
	step := ProcessingStep{
		StepName:      "object_merging",
		ProcessorType: "ObjectMerger",
		StartTime:     time.Now(),
	}
	
	// TODO: Implement object merging logic
	// This would identify and merge duplicate objects from different sources
	
	step.Duration = time.Since(step.StartTime)
	step.Success = true
	step.ObjectsFound = len(objects) // In reality, might be fewer after merging
	
	return step
}

// generateValidationQueue creates validation tasks for low-confidence objects
func (p *IngestionPipeline) generateValidationQueue(objects []arxobject.ArxObject, options ProcessingOptions) []ValidationItem {
	var queue []ValidationItem
	
	for _, obj := range objects {
		if obj.Confidence.Overall < float32(options.MinConfidence) {
			priority := 1.0 - float64(obj.Confidence.Overall)
			
			// Boost priority for critical systems
			if obj.System == "electrical" || obj.System == "fire_safety" {
				priority += 0.3
			}
			
			queue = append(queue, ValidationItem{
				ObjectID:    obj.ID,
				ObjectType:  obj.Type,
				Priority:    priority,
				Reason:      fmt.Sprintf("Confidence %.2f below threshold %.2f", obj.Confidence.Overall, options.MinConfidence),
				System:      obj.System,
				CreatedAt:   time.Now(),
			})
		}
	}
	
	return queue
}

// calculateOverallConfidence computes the building-wide confidence score
func (p *IngestionPipeline) calculateOverallConfidence(objects []arxobject.ArxObject) float64 {
	if len(objects) == 0 {
		return 0.0
	}
	
	totalConfidence := 0.0
	for _, obj := range objects {
		totalConfidence += float64(obj.Confidence.Overall)
	}
	
	return totalConfidence / float64(len(objects))
}

// calculateConfidenceStats computes detailed confidence statistics
func (p *IngestionPipeline) calculateConfidenceStats(objects []arxobject.ArxObject) ConfidenceStatistics {
	if len(objects) == 0 {
		return ConfidenceStatistics{}
	}
	
	confidences := make([]float64, len(objects))
	sum := 0.0
	min := 1.0
	max := 0.0
	
	for i, obj := range objects {
		conf := float64(obj.Confidence.Overall)
		confidences[i] = conf
		sum += conf
		
		if conf < min {
			min = conf
		}
		if conf > max {
			max = conf
		}
	}
	
	avg := sum / float64(len(objects))
	
	// Calculate standard deviation
	sumSquares := 0.0
	for _, conf := range confidences {
		sumSquares += (conf - avg) * (conf - avg)
	}
	stdDev := 0.0
	if len(confidences) > 1 {
		stdDev = sumSquares / float64(len(confidences)-1)
	}
	
	// Create distribution buckets
	distribution := map[string]int{
		"0.0-0.2": 0,
		"0.2-0.4": 0,
		"0.4-0.6": 0,
		"0.6-0.8": 0,
		"0.8-1.0": 0,
	}
	
	for _, conf := range confidences {
		switch {
		case conf < 0.2:
			distribution["0.0-0.2"]++
		case conf < 0.4:
			distribution["0.2-0.4"]++
		case conf < 0.6:
			distribution["0.4-0.6"]++
		case conf < 0.8:
			distribution["0.6-0.8"]++
		default:
			distribution["0.8-1.0"]++
		}
	}
	
	return ConfidenceStatistics{
		Overall:      avg,
		Average:      avg,
		Minimum:      min,
		Maximum:      max,
		StdDev:       stdDev,
		Distribution: distribution,
	}
}

// GetSupportedFormats returns all supported file formats
func (p *IngestionPipeline) GetSupportedFormats() []string {
	return p.registry.GetSupportedFormats()
}

// Stub implementations for missing components

// ValidationEngine handles object validation
type ValidationEngine struct{}

func NewValidationEngine() *ValidationEngine {
	return &ValidationEngine{}
}

// ObjectMerger handles merging duplicate objects
type ObjectMerger struct{}

func NewObjectMerger() *ObjectMerger {
	return &ObjectMerger{}
}

// ConfidenceEngine handles confidence calculations
type ConfidenceEngine struct{}

func NewConfidenceEngine() *ConfidenceEngine {
	return &ConfidenceEngine{}
}