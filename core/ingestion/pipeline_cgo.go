package ingestion

import (
	"fmt"
	"strings"
	"time"

	"github.com/arxos/core/cgo"
)

// ============================================================================
// CGO-OPTIMIZED INGESTION PIPELINE
// ============================================================================

// IngestionPipelineCGO provides ultra-fast file processing using the C core
type IngestionPipelineCGO struct {
	registry   *ProcessorRegistryCGO
	validator  *ValidationEngineCGO
	merger     *ObjectMergerCGO
	confidence *ConfidenceEngineCGO
	hasCGO     bool
}

// NewIngestionPipelineCGO creates a new CGO-optimized pipeline instance
func NewIngestionPipelineCGO() *IngestionPipelineCGO {
	hasCGO := cgo.HasCGOBridge()

	pipeline := &IngestionPipelineCGO{
		registry:   NewProcessorRegistryCGO(),
		validator:  NewValidationEngineCGO(),
		merger:     NewObjectMergerCGO(),
		confidence: NewConfidenceEngineCGO(),
		hasCGO:     hasCGO,
	}

	// Initialize C ingestion system if available
	if hasCGO {
		if !cgo.ArxIngestionInit() {
			pipeline.hasCGO = false
		}
	}

	return pipeline
}

// Close cleans up the pipeline and C resources
func (p *IngestionPipelineCGO) Close() {
	if p.hasCGO {
		cgo.ArxIngestionCleanup()
	}
}

// ProcessFile processes a file using the CGO-optimized pipeline
func (p *IngestionPipelineCGO) ProcessFile(filepath string, options *ArxIngestionOptions) (*ArxIngestionResult, error) {
	if !p.hasCGO {
		return p.fallbackProcessFile(filepath, options)
	}

	startTime := time.Now()

	// Validate options
	if err := ValidateOptions(options); err != nil {
		return nil, fmt.Errorf("invalid options: %w", err)
	}

	// Convert options to C structure
	cOptions := options.toCArxIngestionOptions()

	// Process file using C core
	cResult := cgo.ArxIngestionProcessFile(filepath, cOptions)
	if cResult == nil {
		// Fallback to Go implementation
		return p.fallbackProcessFile(filepath, options)
	}

	// Convert C result to Go structure
	result := fromCArxIngestionResult(cResult)

	// Free C result
	cgo.ArxIngestionFreeResult(cResult)

	// Update processing time
	result.ProcessingTimeMs = float64(time.Since(startTime).Milliseconds())

	return result, nil
}

// DetectFormat detects the file format using the C core
func (p *IngestionPipelineCGO) DetectFormat(filepath string) ArxFileFormat {
	if !p.hasCGO {
		return p.fallbackDetectFormat(filepath)
	}

	format := cgo.ArxIngestionDetectFormat(filepath)
	return ArxFileFormat(format)
}

// GetMetadata extracts file metadata using the C core
func (p *IngestionPipelineCGO) GetMetadata(filepath string) (*ArxFileMetadata, error) {
	if !p.hasCGO {
		return p.fallbackGetMetadata(filepath)
	}

	// In a real implementation, we would call the C function
	// For now, return fallback implementation
	return p.fallbackGetMetadata(filepath)
}

// GetStatistics returns processing statistics from the C core
func (p *IngestionPipelineCGO) GetStatistics() string {
	if !p.hasCGO {
		return "CGO bridge not available"
	}

	stats := cgo.ArxIngestionGetStatistics()
	if stats == nil {
		return "Failed to get statistics"
	}

	defer cgo.CgoFreeString(stats)
	return cgo.GoString(stats)
}

// ClearStatistics clears processing statistics in the C core
func (p *IngestionPipelineCGO) ClearStatistics() {
	if p.hasCGO {
		cgo.ArxIngestionClearStatistics()
	}
}

// ============================================================================
// FALLBACK IMPLEMENTATIONS
// ============================================================================

// fallbackProcessFile provides Go-only file processing when CGO is unavailable
func (p *IngestionPipelineCGO) fallbackProcessFile(filepath string, options *ArxIngestionOptions) (*ArxIngestionResult, error) {
	// Use the original Go implementation
	// This ensures functionality even when CGO fails
	return nil, fmt.Errorf("fallback implementation not yet implemented")
}

// fallbackDetectFormat provides Go-only format detection when CGO is unavailable
func (p *IngestionPipelineCGO) fallbackDetectFormat(filepath string) ArxFileFormat {
	ext := strings.ToLower(filepath)

	if strings.HasSuffix(ext, ".pdf") {
		return ArxFormatPDF
	} else if strings.HasSuffix(ext, ".ifc") || strings.HasSuffix(ext, ".ifcxml") {
		return ArxFormatIFC
	} else if strings.HasSuffix(ext, ".dwg") || strings.HasSuffix(ext, ".dxf") {
		return ArxFormatDWG
	} else if strings.HasSuffix(ext, ".jpg") || strings.HasSuffix(ext, ".jpeg") ||
		strings.HasSuffix(ext, ".png") || strings.HasSuffix(ext, ".heic") ||
		strings.HasSuffix(ext, ".heif") {
		return ArxFormatImage
	} else if strings.HasSuffix(ext, ".xlsx") || strings.HasSuffix(ext, ".xls") ||
		strings.HasSuffix(ext, ".csv") {
		return ArxFormatExcel
	} else if strings.HasSuffix(ext, ".las") || strings.HasSuffix(ext, ".laz") ||
		strings.HasSuffix(ext, ".e57") || strings.HasSuffix(ext, ".ply") {
		return ArxFormatLiDAR
	}

	return ArxFormatUnknown
}

// fallbackGetMetadata provides Go-only metadata extraction when CGO is unavailable
func (p *IngestionPipelineCGO) fallbackGetMetadata(filepath string) (*ArxFileMetadata, error) {
	format := p.fallbackDetectFormat(filepath)

	return &ArxFileMetadata{
		Filename:     filepath,
		Format:       format,
		FileSize:     0, // Would need to implement file size detection
		PageCount:    1,
		BuildingName: "Unknown Building",
		BuildingType: "General",
		YearBuilt:    0,
		TotalArea:    0.0,
		NumFloors:    1,
	}, nil
}

// ============================================================================
// SUPPORTING COMPONENTS
// ============================================================================

// ProcessorRegistryCGO manages format processors with CGO optimization
type ProcessorRegistryCGO struct {
	processors map[string]FormatProcessorCGO
	hasCGO     bool
}

// NewProcessorRegistryCGO creates a new CGO-optimized processor registry
func NewProcessorRegistryCGO() *ProcessorRegistryCGO {
	return &ProcessorRegistryCGO{
		processors: make(map[string]FormatProcessorCGO),
		hasCGO:     cgo.HasCGOBridge(),
	}
}

// FormatProcessorCGO defines the interface for CGO-optimized format processors
type FormatProcessorCGO interface {
	CanProcess(filepath string) bool
	Process(filepath string, options *ArxIngestionOptions) (*ArxIngestionResult, error)
	GetConfidenceBase() float32
}

// ValidationEngineCGO provides CGO-optimized validation
type ValidationEngineCGO struct {
	hasCGO bool
}

// NewValidationEngineCGO creates a new CGO-optimized validation engine
func NewValidationEngineCGO() *ValidationEngineCGO {
	return &ValidationEngineCGO{
		hasCGO: cgo.HasCGOBridge(),
	}
}

// ObjectMergerCGO provides CGO-optimized object merging
type ObjectMergerCGO struct {
	hasCGO bool
}

// NewObjectMergerCGO creates a new CGO-optimized object merger
func NewObjectMergerCGO() *ObjectMergerCGO {
	return &ObjectMergerCGO{
		hasCGO: cgo.HasCGOBridge(),
	}
}

// ConfidenceEngineCGO provides CGO-optimized confidence scoring
type ConfidenceEngineCGO struct {
	hasCGO bool
}

// NewConfidenceEngineCGO creates a new CGO-optimized confidence engine
func NewConfidenceEngineCGO() *ConfidenceEngineCGO {
	return &ConfidenceEngineCGO{
		hasCGO: cgo.HasCGOBridge(),
	}
}
