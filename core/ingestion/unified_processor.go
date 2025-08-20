package ingestion

import (
	"fmt"
	"path/filepath"
	"strings"
	"time"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/google/uuid"
)

// FileFormat represents supported file formats
type FileFormat string

const (
	FormatPDF   FileFormat = "PDF"
	FormatDWG   FileFormat = "DWG"
	FormatDXF   FileFormat = "DXF"
	FormatIFC   FileFormat = "IFC"
	FormatImage FileFormat = "IMAGE"
	FormatExcel FileFormat = "EXCEL"
	FormatCSV   FileFormat = "CSV"
	FormatLiDAR FileFormat = "LIDAR"
	FormatRevit FileFormat = "REVIT"
)

// UnifiedProcessor handles all file format conversions
type UnifiedProcessor struct {
	processors map[FileFormat]FormatProcessor
}

// FormatProcessor interface for format-specific processors
type FormatProcessor interface {
	CanProcess(filepath string) bool
	Process(filepath string) (*ProcessingResult, error)
	GetConfidenceBase() float32
}

// ProcessingResult contains the results of file processing
type ProcessingResult struct {
	Format         FileFormat
	Objects        []arxobject.ArxObject
	Statistics     ProcessingStats
	ValidationQueue []ValidationItem
	ProcessingTime time.Duration
	Errors         []string
	Warnings       []string
}

// ProcessingStats contains statistics about processing
type ProcessingStats struct {
	TotalObjects       int
	HighConfidence     int
	MediumConfidence   int
	LowConfidence      int
	AverageConfidence  float32
	ObjectsByType      map[string]int
	ExtractedLayers    []string
	ProcessingMethod   string
}

// ValidationItem represents an item needing field validation
type ValidationItem struct {
	ObjectID   string
	ObjectType string
	Priority   float32
	Reason     string
	Location   arxobject.Geometry
}

// NewUnifiedProcessor creates a new unified processor
func NewUnifiedProcessor() *UnifiedProcessor {
	up := &UnifiedProcessor{
		processors: make(map[FileFormat]FormatProcessor),
	}
	
	// Register all format processors
	up.registerProcessors()
	
	return up
}

// registerProcessors registers all available format processors
func (up *UnifiedProcessor) registerProcessors() {
	// Register PDF processor
	up.processors[FormatPDF] = NewPDFProcessor()
	
	// Register DWG/DXF processor
	up.processors[FormatDWG] = NewDWGProcessor()
	up.processors[FormatDXF] = up.processors[FormatDWG] // Same processor
	
	// Register IFC processor
	up.processors[FormatIFC] = NewIFCProcessor()
	
	// Register Image processor
	up.processors[FormatImage] = NewImageProcessor()
	
	// Register Excel/CSV processor
	excelProcessor := NewExcelProcessor()
	up.processors[FormatExcel] = excelProcessor
	up.processors[FormatCSV] = excelProcessor
	
	// Register LiDAR processor
	up.processors[FormatLiDAR] = NewLiDARProcessor()
}

// Process processes any supported file format
func (up *UnifiedProcessor) Process(filepath string) (*ProcessingResult, error) {
	startTime := time.Now()
	
	// Detect format
	format := up.DetectFormat(filepath)
	if format == "" {
		return nil, fmt.Errorf("unsupported file format: %s", filepath)
	}
	
	// Get appropriate processor
	processor, exists := up.processors[format]
	if !exists {
		return nil, fmt.Errorf("no processor available for format: %s", format)
	}
	
	// Process the file
	result, err := processor.Process(filepath)
	if err != nil {
		return nil, fmt.Errorf("processing failed: %w", err)
	}
	
	// Set format and timing
	result.Format = format
	result.ProcessingTime = time.Since(startTime)
	
	// Calculate statistics
	result.Statistics = up.calculateStatistics(result.Objects)
	
	// Generate validation queue
	result.ValidationQueue = up.generateValidationQueue(result.Objects)
	
	return result, nil
}

// DetectFormat detects the file format from extension
func (up *UnifiedProcessor) DetectFormat(filepath string) FileFormat {
	ext := strings.ToLower(filepath.Ext(filepath))
	
	switch ext {
	case ".pdf":
		return FormatPDF
	case ".dwg":
		return FormatDWG
	case ".dxf":
		return FormatDXF
	case ".ifc", ".ifcxml":
		return FormatIFC
	case ".jpg", ".jpeg", ".png", ".heic", ".heif":
		return FormatImage
	case ".xlsx", ".xls":
		return FormatExcel
	case ".csv":
		return FormatCSV
	case ".las", ".laz", ".e57", ".ply":
		return FormatLiDAR
	case ".rvt", ".rfa":
		return FormatRevit
	default:
		return ""
	}
}

// calculateStatistics calculates processing statistics
func (up *UnifiedProcessor) calculateStatistics(objects []arxobject.ArxObject) ProcessingStats {
	stats := ProcessingStats{
		TotalObjects:  len(objects),
		ObjectsByType: make(map[string]int),
	}
	
	var totalConfidence float32
	
	for _, obj := range objects {
		// Count by type
		stats.ObjectsByType[string(obj.Type)]++
		
		// Categorize by confidence
		conf := obj.Confidence.Overall
		totalConfidence += conf
		
		switch {
		case conf >= 0.8:
			stats.HighConfidence++
		case conf >= 0.5:
			stats.MediumConfidence++
		default:
			stats.LowConfidence++
		}
	}
	
	if len(objects) > 0 {
		stats.AverageConfidence = totalConfidence / float32(len(objects))
	}
	
	return stats
}

// generateValidationQueue creates a prioritized validation queue
func (up *UnifiedProcessor) generateValidationQueue(objects []arxobject.ArxObject) []ValidationItem {
	var queue []ValidationItem
	
	for _, obj := range objects {
		// Calculate validation priority
		priority := up.calculateValidationPriority(obj)
		
		// Add to queue if needs validation
		if priority > 0.3 {
			item := ValidationItem{
				ObjectID:   obj.ID,
				ObjectType: string(obj.Type),
				Priority:   priority,
				Reason:     up.getValidationReason(obj),
				Location:   obj.Geometry,
			}
			queue = append(queue, item)
		}
	}
	
	// Sort by priority (highest first)
	// In production, implement proper sorting
	
	return queue
}

// calculateValidationPriority calculates validation priority for an object
func (up *UnifiedProcessor) calculateValidationPriority(obj arxobject.ArxObject) float32 {
	priority := float32(0.0)
	
	// Critical systems get higher priority
	criticalTypes := map[arxobject.ArxObjectType]float32{
		arxobject.ArxObjectType("electrical_panel"): 0.5,
		arxobject.ArxObjectType("fire_alarm"):       0.5,
		arxobject.ArxObjectType("emergency_exit"):   0.5,
		arxobject.ArxObjectType("sprinkler"):        0.4,
		arxobject.ArxObjectType("hvac_unit"):        0.3,
	}
	
	if weight, exists := criticalTypes[obj.Type]; exists {
		priority += weight
	}
	
	// Low confidence increases priority
	priority += (1.0 - obj.Confidence.Overall) * 0.3
	
	// Many relationships increase priority (hub objects)
	if len(obj.Relationships) > 5 {
		priority += 0.2
	}
	
	// Not validated increases priority
	if !obj.Metadata.Validated {
		priority += 0.1
	}
	
	return priority
}

// getValidationReason generates a human-readable validation reason
func (up *UnifiedProcessor) getValidationReason(obj arxobject.ArxObject) string {
	reasons := []string{}
	
	if obj.Confidence.Overall < 0.5 {
		reasons = append(reasons, "Low confidence")
	}
	
	if obj.Confidence.Position < 0.6 {
		reasons = append(reasons, "Uncertain position")
	}
	
	if obj.Type == arxobject.ArxObjectType("electrical_panel") ||
	   obj.Type == arxobject.ArxObjectType("fire_alarm") {
		reasons = append(reasons, "Critical system")
	}
	
	if len(obj.Relationships) > 5 {
		reasons = append(reasons, "Hub object")
	}
	
	if len(reasons) == 0 {
		return "General validation"
	}
	
	return strings.Join(reasons, ", ")
}

// GetSupportedFormats returns all supported file formats
func (up *UnifiedProcessor) GetSupportedFormats() []FileFormat {
	formats := []FileFormat{}
	for format := range up.processors {
		formats = append(formats, format)
	}
	return formats
}

// CanProcess checks if a file can be processed
func (up *UnifiedProcessor) CanProcess(filepath string) bool {
	format := up.DetectFormat(filepath)
	if format == "" {
		return false
	}
	
	processor, exists := up.processors[format]
	if !exists {
		return false
	}
	
	return processor.CanProcess(filepath)
}

// Helper function to create ArxObject with standard fields
func CreateArxObject(objType arxobject.ArxObjectType, confidence arxobject.ConfidenceScore) arxobject.ArxObject {
	return arxobject.ArxObject{
		ID:         uuid.New().String(),
		Type:       objType,
		Confidence: confidence,
		Metadata: arxobject.Metadata{
			Source:      "ingestion",
			Created:     time.Now(),
			Validated:   false,
		},
		Relationships: []arxobject.Relationship{},
		Data:         make(map[string]interface{}),
	}
}