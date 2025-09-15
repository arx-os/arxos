package converter

import (
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/joelpate/arxos/internal/common/logger"
)

// ValidationConfig holds file validation parameters
type ValidationConfig struct {
	// MaxFileSizeMB limits file size during validation
	MaxFileSizeMB int64

	// SupportedExtensions lists allowed file extensions
	SupportedExtensions []string

	// RequiredPermissions specifies needed file permissions
	RequiredPermissions os.FileMode

	// EnableContentValidation enables deep content validation
	EnableContentValidation bool
}

// DefaultValidationConfig returns sensible validation defaults
func DefaultValidationConfig() *ValidationConfig {
	return &ValidationConfig{
		MaxFileSizeMB:           100, // 100MB limit
		SupportedExtensions:     []string{".pdf", ".ifc", ".ifcxml"},
		RequiredPermissions:     0444, // Read permission required
		EnableContentValidation: true,
	}
}

// ValidationResult holds validation results and any issues found
type ValidationResult struct {
	IsValid      bool
	FileSize     int64
	Extension    string
	ContentType  string
	Issues       []string
	Warnings     []string
	Suggestions  []string
}

// FileValidator provides comprehensive file validation
type FileValidator struct {
	config *ValidationConfig
}

// NewFileValidator creates a new file validator
func NewFileValidator(config *ValidationConfig) *FileValidator {
	if config == nil {
		config = DefaultValidationConfig()
	}
	return &FileValidator{config: config}
}

// ValidateFile performs comprehensive file validation
func (v *FileValidator) ValidateFile(filePath string) (*ValidationResult, error) {
	result := &ValidationResult{
		IsValid: true,
		Issues:  make([]string, 0),
		Warnings: make([]string, 0),
		Suggestions: make([]string, 0),
	}

	// Check if file exists
	fileInfo, err := os.Stat(filePath)
	if err != nil {
		if os.IsNotExist(err) {
			result.Issues = append(result.Issues, fmt.Sprintf("File does not exist: %s", filePath))
		} else {
			result.Issues = append(result.Issues, fmt.Sprintf("Cannot access file: %v", err))
		}
		result.IsValid = false
		return result, nil
	}

	// Check if it's a regular file
	if !fileInfo.Mode().IsRegular() {
		result.Issues = append(result.Issues, "Path does not point to a regular file")
		result.IsValid = false
		return result, nil
	}

	// Validate file size
	result.FileSize = fileInfo.Size()
	if err := v.validateFileSize(result); err != nil {
		result.Issues = append(result.Issues, err.Error())
		result.IsValid = false
	}

	// Validate file extension
	result.Extension = strings.ToLower(filepath.Ext(filePath))
	if err := v.validateExtension(result); err != nil {
		result.Issues = append(result.Issues, err.Error())
		result.IsValid = false
	}

	// Validate file permissions
	if err := v.validatePermissions(fileInfo, result); err != nil {
		result.Issues = append(result.Issues, err.Error())
		result.IsValid = false
	}

	// Perform content validation if enabled and file passes basic checks
	if v.config.EnableContentValidation && result.IsValid {
		if err := v.validateContent(filePath, result); err != nil {
			logger.Warn("Content validation failed: %v", err)
			result.Issues = append(result.Issues, fmt.Sprintf("Content validation failed: %v", err))
			result.IsValid = false
		}
	}

	// Add suggestions for optimization
	v.addSuggestions(result)

	return result, nil
}

// validateFileSize checks if file size is within acceptable limits
func (v *FileValidator) validateFileSize(result *ValidationResult) error {
	sizeMB := result.FileSize / (1024 * 1024)

	if sizeMB > v.config.MaxFileSizeMB {
		return fmt.Errorf("file size (%d MB) exceeds maximum allowed size (%d MB)", sizeMB, v.config.MaxFileSizeMB)
	}

	if result.FileSize == 0 {
		return fmt.Errorf("file is empty")
	}

	// Warn about very large files
	if sizeMB > v.config.MaxFileSizeMB/2 {
		result.Warnings = append(result.Warnings, fmt.Sprintf("Large file detected (%d MB) - processing may take longer", sizeMB))
	}

	return nil
}

// validateExtension checks if file extension is supported
func (v *FileValidator) validateExtension(result *ValidationResult) error {
	if result.Extension == "" {
		return fmt.Errorf("file has no extension")
	}

	for _, ext := range v.config.SupportedExtensions {
		if result.Extension == strings.ToLower(ext) {
			return nil
		}
	}

	return fmt.Errorf("unsupported file extension '%s', supported extensions: %v",
		result.Extension, v.config.SupportedExtensions)
}

// validatePermissions checks if file has required permissions
func (v *FileValidator) validatePermissions(fileInfo os.FileInfo, result *ValidationResult) error {
	mode := fileInfo.Mode()

	// Check if file is readable
	if mode&0400 == 0 {
		return fmt.Errorf("file is not readable")
	}

	return nil
}

// validateContent performs deep content validation based on file type
func (v *FileValidator) validateContent(filePath string, result *ValidationResult) error {
	file, err := os.Open(filePath)
	if err != nil {
		return fmt.Errorf("cannot open file for content validation: %v", err)
	}
	defer file.Close()

	// Read first few bytes to determine content type
	buffer := make([]byte, 512)
	n, err := file.Read(buffer)
	if err != nil && err != io.EOF {
		return fmt.Errorf("cannot read file content: %v", err)
	}

	header := string(buffer[:n])

	switch result.Extension {
	case ".pdf":
		return v.validatePDFContent(header, result)
	case ".ifc":
		return v.validateIFCContent(header, result)
	case ".ifcxml":
		return v.validateIFCXMLContent(header, result)
	default:
		result.Warnings = append(result.Warnings, "Content validation not implemented for this file type")
	}

	return nil
}

// validatePDFContent validates PDF file structure
func (v *FileValidator) validatePDFContent(header string, result *ValidationResult) error {
	result.ContentType = "PDF"

	// Check PDF header
	if !strings.HasPrefix(header, "%PDF-") {
		return fmt.Errorf("invalid PDF header - file may be corrupted")
	}

	// Extract PDF version
	if len(header) >= 8 {
		version := header[5:8]
		logger.Debug("PDF version detected: %s", version)

		// Warn about very old PDF versions
		if version < "1.3" {
			result.Warnings = append(result.Warnings, fmt.Sprintf("Old PDF version (%s) detected - may have compatibility issues", version))
		}
	}

	return nil
}

// validateIFCContent validates IFC file structure
func (v *FileValidator) validateIFCContent(header string, result *ValidationResult) error {
	result.ContentType = "IFC"

	// Check IFC header
	if !strings.Contains(header, "ISO-10303-21") {
		return fmt.Errorf("invalid IFC header - file may not be a valid IFC file")
	}

	// Look for HEADER section
	if !strings.Contains(header, "HEADER;") {
		result.Warnings = append(result.Warnings, "IFC HEADER section not found in expected location")
	}

	// Check for DATA section
	if !strings.Contains(header, "DATA;") {
		result.Warnings = append(result.Warnings, "IFC DATA section not found in expected location")
	}

	return nil
}

// validateIFCXMLContent validates IFCXML file structure
func (v *FileValidator) validateIFCXMLContent(header string, result *ValidationResult) error {
	result.ContentType = "IFCXML"

	// Check XML header
	if !strings.Contains(header, "<?xml") {
		return fmt.Errorf("invalid XML header - file may be corrupted")
	}

	// Check for IFC namespace
	if !strings.Contains(header, "ifc") && !strings.Contains(header, "IFC") {
		result.Warnings = append(result.Warnings, "IFC namespace not found in XML header - may not be a valid IFCXML file")
	}

	return nil
}

// addSuggestions provides optimization suggestions based on validation results
func (v *FileValidator) addSuggestions(result *ValidationResult) {
	// Size-based suggestions
	sizeMB := result.FileSize / (1024 * 1024)

	if sizeMB > 50 {
		result.Suggestions = append(result.Suggestions, "Consider using streaming conversion for large files to optimize memory usage")
	}

	if sizeMB > 20 && result.Extension == ".pdf" {
		result.Suggestions = append(result.Suggestions, "Large PDF detected - ensure it contains building data rather than just images")
	}

	// Format-specific suggestions
	switch result.Extension {
	case ".pdf":
		result.Suggestions = append(result.Suggestions, "For best results, ensure PDF contains searchable text rather than scanned images")
	case ".ifc":
		result.Suggestions = append(result.Suggestions, "IFC files typically provide the most comprehensive building data")
	case ".ifcxml":
		result.Suggestions = append(result.Suggestions, "IFCXML files are typically larger than binary IFC - consider using .ifc format for better performance")
	}

	// Performance suggestions
	if len(result.Warnings) > 0 {
		result.Suggestions = append(result.Suggestions, "Check file integrity if conversion fails - some warnings were detected")
	}
}

// ValidateBeforeConversion is a convenience method for converter integration
func ValidateBeforeConversion(filePath string) error {
	validator := NewFileValidator(nil)
	result, err := validator.ValidateFile(filePath)
	if err != nil {
		return fmt.Errorf("validation failed: %v", err)
	}

	if !result.IsValid {
		return fmt.Errorf("file validation failed: %s", strings.Join(result.Issues, "; "))
	}

	// Log warnings and suggestions
	for _, warning := range result.Warnings {
		logger.Warn("📋 %s", warning)
	}

	for _, suggestion := range result.Suggestions {
		logger.Info("💡 %s", suggestion)
	}

	logger.Info("✅ File validation passed - %s (%d MB, %s)",
		filepath.Base(filePath), result.FileSize/(1024*1024), result.ContentType)

	return nil
}