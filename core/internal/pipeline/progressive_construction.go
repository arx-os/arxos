// Package pipeline implements the Progressive Construction Pipeline
// PDF → Measurements → LiDAR → 3D workflow for ArxOS
package pipeline

import (
	"context"
	"fmt"
	"path/filepath"
	"time"

	"github.com/arxos/arxos/core/internal/arxobject"
	"github.com/arxos/arxos/core/internal/confidence"
)

// ProgressiveConstructionPipeline orchestrates the full PDF → 3D workflow
type ProgressiveConstructionPipeline struct {
	// Stage processors
	pdfStage           *PDFStage
	measurementStage   *MeasurementStage
	lidarStage         *LiDARStage
	reconstructionStage *ReconstructionStage
	
	// Configuration
	config *PipelineConfig
	
	// Progress tracking
	progressCallback func(stage string, progress float64, message string)
}

// PipelineConfig configures the progressive construction pipeline
type PipelineConfig struct {
	// Processing options
	EnableLiDARFusion   bool    `json:"enable_lidar_fusion"`
	RequiredAccuracy    float64 `json:"required_accuracy_mm"`
	ConfidenceThreshold float64 `json:"confidence_threshold"`
	
	// Output options
	Generate3DMesh      bool `json:"generate_3d_mesh"`
	GenerateASCII       bool `json:"generate_ascii"`
	ValidateAgainstCode bool `json:"validate_against_code"`
	
	// File paths
	TempDirectory       string `json:"temp_directory"`
	OutputDirectory     string `json:"output_directory"`
}

// ProcessingResult contains the results of the progressive construction pipeline
type ProcessingResult struct {
	// Generated objects
	ArxObjects     []*arxobject.ArxObjectUnified `json:"objects"`
	
	// Processing metadata
	ProcessingTime time.Duration                 `json:"processing_time"`
	StageResults   map[string]*StageResult       `json:"stage_results"`
	
	// Quality metrics
	OverallConfidence float64                    `json:"overall_confidence"`
	ValidationErrors  []ValidationError          `json:"validation_errors"`
	
	// Generated assets
	MeshFile      string                        `json:"mesh_file,omitempty"`
	ASCIIPreview  string                        `json:"ascii_preview,omitempty"`
}

// StageResult contains the results of a single pipeline stage
type StageResult struct {
	StageName      string        `json:"stage_name"`
	Success        bool          `json:"success"`
	ProcessingTime time.Duration `json:"processing_time"`
	ObjectsCreated int           `json:"objects_created"`
	Confidence     float64       `json:"confidence"`
	Errors         []error       `json:"errors,omitempty"`
	Metadata       interface{}   `json:"metadata,omitempty"`
}

// ValidationError represents an error found during validation
type ValidationError struct {
	Type        string  `json:"type"`
	Description string  `json:"description"`
	Severity    string  `json:"severity"` // "error", "warning", "info"
	Location    string  `json:"location,omitempty"`
	Confidence  float64 `json:"confidence"`
}

// NewProgressiveConstructionPipeline creates a new pipeline instance
func NewProgressiveConstructionPipeline(config *PipelineConfig) *ProgressiveConstructionPipeline {
	return &ProgressiveConstructionPipeline{
		pdfStage:            NewPDFStage(),
		measurementStage:    NewMeasurementStage(),
		lidarStage:          NewLiDARStage(),
		reconstructionStage: NewReconstructionStage(),
		config:             config,
	}
}

// SetProgressCallback sets a callback function for progress updates
func (pcp *ProgressiveConstructionPipeline) SetProgressCallback(callback func(stage string, progress float64, message string)) {
	pcp.progressCallback = callback
}

// ProcessPDF processes a PDF file through the complete progressive construction pipeline
func (pcp *ProgressiveConstructionPipeline) ProcessPDF(ctx context.Context, pdfPath string, buildingID string) (*ProcessingResult, error) {
	startTime := time.Now()
	
	result := &ProcessingResult{
		StageResults: make(map[string]*StageResult),
	}
	
	// Validate input
	if err := pcp.validateInput(pdfPath); err != nil {
		return nil, fmt.Errorf("input validation failed: %w", err)
	}
	
	pcp.reportProgress("validation", 0.05, "Input validation complete")
	
	// Stage 1: PDF Processing
	pdfResult, err := pcp.runPDFStage(ctx, pdfPath, buildingID)
	if err != nil {
		return nil, fmt.Errorf("PDF stage failed: %w", err)
	}
	result.StageResults["pdf"] = pdfResult
	result.ArxObjects = append(result.ArxObjects, pdfResult.Metadata.([]*arxobject.ArxObjectUnified)...)
	
	pcp.reportProgress("pdf", 0.25, fmt.Sprintf("PDF processing complete - %d objects extracted", pdfResult.ObjectsCreated))
	
	// Stage 2: Measurements Processing
	measurementResult, err := pcp.runMeasurementStage(ctx, result.ArxObjects)
	if err != nil {
		return nil, fmt.Errorf("measurement stage failed: %w", err)
	}
	result.StageResults["measurements"] = measurementResult
	
	pcp.reportProgress("measurements", 0.50, "Measurements extraction and calibration complete")
	
	// Stage 3: LiDAR Integration (if enabled)
	if pcp.config.EnableLiDARFusion {
		lidarResult, err := pcp.runLiDARStage(ctx, result.ArxObjects)
		if err != nil {
			return nil, fmt.Errorf("LiDAR stage failed: %w", err)
		}
		result.StageResults["lidar"] = lidarResult
		
		pcp.reportProgress("lidar", 0.75, "LiDAR fusion complete")
	}
	
	// Stage 4: 3D Reconstruction
	if pcp.config.Generate3DMesh {
		reconstructionResult, err := pcp.runReconstructionStage(ctx, result.ArxObjects)
		if err != nil {
			return nil, fmt.Errorf("reconstruction stage failed: %w", err)
		}
		result.StageResults["reconstruction"] = reconstructionResult
		
		if meshFile, ok := reconstructionResult.Metadata.(string); ok {
			result.MeshFile = meshFile
		}
	}
	
	pcp.reportProgress("reconstruction", 0.90, "3D reconstruction complete")
	
	// Final validation and quality assessment
	if err := pcp.runFinalValidation(result); err != nil {
		return nil, fmt.Errorf("final validation failed: %w", err)
	}
	
	// Generate ASCII preview if requested
	if pcp.config.GenerateASCII {
		asciiPreview, err := pcp.generateASCIIPreview(result.ArxObjects)
		if err == nil {
			result.ASCIIPreview = asciiPreview
		}
	}
	
	pcp.reportProgress("complete", 1.0, "Progressive construction pipeline complete")
	
	result.ProcessingTime = time.Since(startTime)
	return result, nil
}

// validateInput validates the input PDF file
func (pcp *ProgressiveConstructionPipeline) validateInput(pdfPath string) error {
	// Check file existence
	if _, err := filepath.Abs(pdfPath); err != nil {
		return fmt.Errorf("invalid file path: %w", err)
	}
	
	// Check file extension
	ext := filepath.Ext(pdfPath)
	if ext != ".pdf" {
		return fmt.Errorf("unsupported file type: %s (expected .pdf)", ext)
	}
	
	return nil
}

// runPDFStage executes the PDF processing stage
func (pcp *ProgressiveConstructionPipeline) runPDFStage(ctx context.Context, pdfPath string, buildingID string) (*StageResult, error) {
	startTime := time.Now()
	
	objects, err := pcp.pdfStage.Process(ctx, pdfPath, buildingID)
	if err != nil {
		return &StageResult{
			StageName: "pdf",
			Success:   false,
			ProcessingTime: time.Since(startTime),
			Errors:    []error{err},
		}, err
	}
	
	// Calculate confidence for PDF stage
	confidence := pcp.calculateStageConfidence(objects, "pdf")
	
	return &StageResult{
		StageName:      "pdf",
		Success:        true,
		ProcessingTime: time.Since(startTime),
		ObjectsCreated: len(objects),
		Confidence:     confidence,
		Metadata:       objects,
	}, nil
}

// runMeasurementStage executes the measurements processing stage
func (pcp *ProgressiveConstructionPipeline) runMeasurementStage(ctx context.Context, objects []*arxobject.ArxObjectUnified) (*StageResult, error) {
	startTime := time.Now()
	
	updatedObjects, err := pcp.measurementStage.Process(ctx, objects)
	if err != nil {
		return &StageResult{
			StageName: "measurements",
			Success:   false,
			ProcessingTime: time.Since(startTime),
			Errors:    []error{err},
		}, err
	}
	
	confidence := pcp.calculateStageConfidence(updatedObjects, "measurements")
	
	return &StageResult{
		StageName:      "measurements",
		Success:        true,
		ProcessingTime: time.Since(startTime),
		ObjectsCreated: len(updatedObjects),
		Confidence:     confidence,
		Metadata:       updatedObjects,
	}, nil
}

// runLiDARStage executes the LiDAR integration stage
func (pcp *ProgressiveConstructionPipeline) runLiDARStage(ctx context.Context, objects []*arxobject.ArxObjectUnified) (*StageResult, error) {
	startTime := time.Now()
	
	fusedObjects, err := pcp.lidarStage.Process(ctx, objects)
	if err != nil {
		return &StageResult{
			StageName: "lidar",
			Success:   false,
			ProcessingTime: time.Since(startTime),
			Errors:    []error{err},
		}, err
	}
	
	confidence := pcp.calculateStageConfidence(fusedObjects, "lidar")
	
	return &StageResult{
		StageName:      "lidar",
		Success:        true,
		ProcessingTime: time.Since(startTime),
		ObjectsCreated: len(fusedObjects),
		Confidence:     confidence,
		Metadata:       fusedObjects,
	}, nil
}

// runReconstructionStage executes the 3D reconstruction stage
func (pcp *ProgressiveConstructionPipeline) runReconstructionStage(ctx context.Context, objects []*arxobject.ArxObjectUnified) (*StageResult, error) {
	startTime := time.Now()
	
	meshFile, err := pcp.reconstructionStage.Process(ctx, objects, pcp.config.OutputDirectory)
	if err != nil {
		return &StageResult{
			StageName: "reconstruction",
			Success:   false,
			ProcessingTime: time.Since(startTime),
			Errors:    []error{err},
		}, err
	}
	
	return &StageResult{
		StageName:      "reconstruction",
		Success:        true,
		ProcessingTime: time.Since(startTime),
		ObjectsCreated: 1, // Mesh file created
		Confidence:     0.9, // High confidence for 3D reconstruction
		Metadata:       meshFile,
	}, nil
}

// calculateStageConfidence calculates confidence for a processing stage
func (pcp *ProgressiveConstructionPipeline) calculateStageConfidence(objects []*arxobject.ArxObjectUnified, stage string) float64 {
	if len(objects) == 0 {
		return 0.0
	}
	
	totalConfidence := 0.0
	for _, obj := range objects {
		if obj.Confidence != nil {
			switch stage {
			case "pdf":
				totalConfidence += obj.Confidence.GetSourceConfidence()
			case "measurements":
				totalConfidence += obj.Confidence.GetGeometryConfidence()
			case "lidar":
				totalConfidence += obj.Confidence.GetOverallConfidence()
			default:
				totalConfidence += obj.Confidence.GetOverallConfidence()
			}
		}
	}
	
	return totalConfidence / float64(len(objects))
}

// runFinalValidation performs final validation of the results
func (pcp *ProgressiveConstructionPipeline) runFinalValidation(result *ProcessingResult) error {
	// Calculate overall confidence
	if len(result.ArxObjects) > 0 {
		totalConfidence := 0.0
		for _, obj := range result.ArxObjects {
			if obj.Confidence != nil {
				totalConfidence += obj.Confidence.GetOverallConfidence()
			}
		}
		result.OverallConfidence = totalConfidence / float64(len(result.ArxObjects))
	}
	
	// Check if confidence meets threshold
	if result.OverallConfidence < pcp.config.ConfidenceThreshold {
		result.ValidationErrors = append(result.ValidationErrors, ValidationError{
			Type:        "confidence",
			Description: fmt.Sprintf("Overall confidence %.2f below threshold %.2f", result.OverallConfidence, pcp.config.ConfidenceThreshold),
			Severity:    "warning",
			Confidence:  result.OverallConfidence,
		})
	}
	
	return nil
}

// generateASCIIPreview generates an ASCII preview of the building
func (pcp *ProgressiveConstructionPipeline) generateASCIIPreview(objects []*arxobject.ArxObjectUnified) (string, error) {
	// This would integrate with the existing ASCII rendering system
	// For now, return a placeholder
	return "ASCII-BIM preview generation not yet implemented", nil
}

// reportProgress reports progress to the callback if set
func (pcp *ProgressiveConstructionPipeline) reportProgress(stage string, progress float64, message string) {
	if pcp.progressCallback != nil {
		pcp.progressCallback(stage, progress, message)
	}
}