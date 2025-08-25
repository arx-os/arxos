package ingestion

import "errors"

// ============================================================================
// INGESTION ERROR DEFINITIONS
// ============================================================================

var (
	// ErrNilOptions indicates that options were not provided
	ErrNilOptions = errors.New("ingestion options cannot be nil")
	
	// ErrInvalidConfidence indicates that confidence value is out of range
	ErrInvalidConfidence = errors.New("confidence must be between 0.0 and 1.0")
	
	// ErrInvalidMaxObjects indicates that max objects value is invalid
	ErrInvalidMaxObjects = errors.New("max objects per file must be greater than 0")
	
	// ErrUnsupportedFormat indicates that the file format is not supported
	ErrUnsupportedFormat = errors.New("unsupported file format")
	
	// ErrFileNotFound indicates that the file was not found
	ErrFileNotFound = errors.New("file not found")
	
	// ErrFileReadFailed indicates that reading the file failed
	ErrFileReadFailed = errors.New("failed to read file")
	
	// ErrProcessingFailed indicates that file processing failed
	ErrProcessingFailed = errors.New("file processing failed")
	
	// ErrInvalidFile indicates that the file is invalid or corrupted
	ErrInvalidFile = errors.New("invalid or corrupted file")
	
	// ErrNoObjectsFound indicates that no objects were extracted from the file
	ErrNoObjectsFound = errors.New("no objects found in file")
	
	// ErrValidationFailed indicates that object validation failed
	ErrValidationFailed = errors.New("object validation failed")
	
	// ErrCGOBridgeFailed indicates that the CGO bridge failed
	ErrCGOBridgeFailed = errors.New("CGO bridge failed")
	
	// ErrMemoryAllocationFailed indicates that memory allocation failed
	ErrMemoryAllocationFailed = errors.New("memory allocation failed")
)
