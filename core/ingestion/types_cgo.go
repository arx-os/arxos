package ingestion

import (
	"unsafe"

	"github.com/arxos/core/cgo"
)

// ============================================================================
// CGO WRAPPER TYPES
// ============================================================================

// ArxFileFormat represents the supported file formats for ingestion
type ArxFileFormat int

const (
	ArxFormatPDF     ArxFileFormat = 0
	ArxFormatIFC     ArxFileFormat = 1
	ArxFormatDWG     ArxFileFormat = 2
	ArxFormatImage   ArxFileFormat = 3
	ArxFormatExcel   ArxFileFormat = 4
	ArxFormatLiDAR   ArxFileFormat = 5
	ArxFormatUnknown ArxFileFormat = 99
)

// ArxIngestionOptions wraps the C ingestion options structure
type ArxIngestionOptions struct {
	EnableMerging     bool
	MinConfidence     float32
	RequireValidation bool
	CoordinateSystem  string
	UnitsOfMeasure    string
	MaxObjectsPerFile int
	EnableCaching     bool
}

// ArxFileMetadata wraps the C file metadata structure
type ArxFileMetadata struct {
	Filename     string
	Format       ArxFileFormat
	FileSize     uint64
	PageCount    int
	BuildingName string
	BuildingType string
	YearBuilt    int
	TotalArea    float32
	NumFloors    int
}

// ArxIngestionResult wraps the C ingestion result structure
type ArxIngestionResult struct {
	Success           bool
	ErrorMessage      string
	Objects           []cgo.ArxObject
	ObjectCount       int
	OverallConfidence float32
	ProcessingTimeMs  float64
	FileInfo          string
	ValidationSummary string
}

// ============================================================================
// CONVERSION FUNCTIONS
// ============================================================================

// toCArxIngestionOptions converts Go options to C structure
func (opts *ArxIngestionOptions) toCArxIngestionOptions() unsafe.Pointer {
	if opts == nil {
		return nil
	}

	// Get default options from C and modify them
	cOptions := cgo.ArxIngestionGetDefaultOptions()
	if cOptions == nil {
		return nil
	}

	// In a real implementation, we would modify the C structure
	// For now, we return the default options
	return cOptions
}

// fromCArxFileMetadata converts C metadata to Go structure
func fromCArxFileMetadata(cMetadata unsafe.Pointer) *ArxFileMetadata {
	if cMetadata == nil {
		return nil
	}

	// In a real implementation, we would read from the C structure
	// For now, return a default metadata structure
	return &ArxFileMetadata{
		Filename:     "Unknown",
		Format:       ArxFormatUnknown,
		FileSize:     0,
		PageCount:    1,
		BuildingName: "Unknown Building",
		BuildingType: "General",
		YearBuilt:    0,
		TotalArea:    0.0,
		NumFloors:    1,
	}
}

// fromCArxIngestionResult converts C result to Go structure
func fromCArxIngestionResult(cResult unsafe.Pointer) *ArxIngestionResult {
	if cResult == nil {
		return nil
	}

	// In a real implementation, we would read from the C structure
	// For now, return a default result structure
	return &ArxIngestionResult{
		Success:           false,
		ErrorMessage:      "Failed to convert C result",
		Objects:           nil,
		ObjectCount:       0,
		OverallConfidence: 0.0,
		ProcessingTimeMs:  0.0,
		FileInfo:          "",
		ValidationSummary: "",
	}
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

// String returns the string representation of the file format
func (f ArxFileFormat) String() string {
	switch f {
	case ArxFormatPDF:
		return "PDF"
	case ArxFormatIFC:
		return "IFC"
	case ArxFormatDWG:
		return "DWG"
	case ArxFormatImage:
		return "Image"
	case ArxFormatExcel:
		return "Excel"
	case ArxFormatLiDAR:
		return "LiDAR"
	default:
		return "Unknown"
	}
}

// IsValid returns true if the file format is valid
func (f ArxFileFormat) IsValid() bool {
	return f >= ArxFormatPDF && f <= ArxFormatLiDAR
}

// GetDefaultOptions returns the default ingestion options
func GetDefaultOptions() *ArxIngestionOptions {
	return &ArxIngestionOptions{
		EnableMerging:     true,
		MinConfidence:     0.7,
		RequireValidation: true,
		CoordinateSystem:  "WGS84",
		UnitsOfMeasure:    "millimeters",
		MaxObjectsPerFile: 1000,
		EnableCaching:     true,
	}
}

// ValidateOptions validates the ingestion options
func ValidateOptions(opts *ArxIngestionOptions) error {
	if opts == nil {
		return ErrNilOptions
	}

	if opts.MinConfidence < 0.0 || opts.MinConfidence > 1.0 {
		return ErrInvalidConfidence
	}

	if opts.MaxObjectsPerFile <= 0 {
		return ErrInvalidMaxObjects
	}

	return nil
}
