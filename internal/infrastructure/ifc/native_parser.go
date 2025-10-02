package ifc

import (
	"context"
	"fmt"
	"strings"
	"time"
)

// NativeParser provides a basic Go-based IFC parser as a fallback
type NativeParser struct {
	// Basic configuration for native parser
	maxFileSize int64
}

// NewNativeParser creates a new native IFC parser
func NewNativeParser(maxFileSize int64) *NativeParser {
	return &NativeParser{
		maxFileSize: maxFileSize,
	}
}

// ParseIFC parses an IFC file using native Go implementation
func (p *NativeParser) ParseIFC(ctx context.Context, data []byte) (*IFCResult, error) {
	startTime := time.Now()

	// Check file size
	if int64(len(data)) > p.maxFileSize {
		return nil, fmt.Errorf("file size exceeds maximum allowed size of %d bytes", p.maxFileSize)
	}

	// Basic IFC file validation
	if !p.isValidIFC(data) {
		return nil, fmt.Errorf("invalid IFC file format")
	}

	// Parse IFC content
	content := string(data)

	// Count basic entities using string matching
	// This is a simplified approach for basic parsing
	buildings := p.countEntities(content, "IFCBUILDING")
	spaces := p.countEntities(content, "IFCSPACE")
	equipment := p.countEntities(content, "IFCFLOWTERMINAL")
	walls := p.countEntities(content, "IFCWALL")
	doors := p.countEntities(content, "IFCDOOR")
	windows := p.countEntities(content, "IFCWINDOW")

	// Get IFC version
	ifcVersion := p.extractIFCVersion(content)

	processingTime := time.Since(startTime)

	result := &IFCResult{
		Success:       true,
		Buildings:     buildings,
		Spaces:        spaces,
		Equipment:     equipment,
		Walls:         walls,
		Doors:         doors,
		Windows:       windows,
		TotalEntities: buildings + spaces + equipment + walls + doors + windows,
		Metadata: IFCMetadata{
			IFCVersion:     ifcVersion,
			FileSize:       len(data),
			ProcessingTime: fmt.Sprintf("%.2fs", processingTime.Seconds()),
			Timestamp:      time.Now().UTC().Format(time.RFC3339),
		},
	}

	return result, nil
}

// ValidateIFC validates an IFC file using native Go implementation
func (p *NativeParser) ValidateIFC(ctx context.Context, data []byte) (*ValidationResult, error) {
	startTime := time.Now()

	// Check file size
	if int64(len(data)) > p.maxFileSize {
		return nil, fmt.Errorf("file size exceeds maximum allowed size of %d bytes", p.maxFileSize)
	}

	// Basic validation
	warnings := []string{}
	errors := []string{}

	// Check if it's a valid IFC file
	if !p.isValidIFC(data) {
		errors = append(errors, "Invalid IFC file format")
		return &ValidationResult{
			Success:  false,
			Valid:    false,
			Warnings: warnings,
			Errors:   errors,
			Compliance: ComplianceInfo{
				BuildingSMART:      false,
				IFC4:               false,
				SpatialConsistency: false,
			},
			Metadata: IFCMetadata{
				FileSize:       len(data),
				ProcessingTime: fmt.Sprintf("%.2fs", time.Since(startTime).Seconds()),
				Timestamp:      time.Now().UTC().Format(time.RFC3339),
			},
		}, nil
	}

	content := string(data)

	// Check for required entities
	buildings := p.countEntities(content, "IFCBUILDING")
	spaces := p.countEntities(content, "IFCSPACE")

	if buildings == 0 {
		warnings = append(warnings, "No buildings found in IFC file")
	}

	if spaces == 0 {
		warnings = append(warnings, "No spaces found in IFC file")
	}

	// Check IFC version
	ifcVersion := p.extractIFCVersion(content)
	if !strings.HasPrefix(ifcVersion, "IFC4") {
		warnings = append(warnings, fmt.Sprintf("IFC version %s may not be fully supported", ifcVersion))
	}

	// Basic compliance checks
	buildingSMART := len(errors) == 0
	ifc4Compliant := strings.HasPrefix(ifcVersion, "IFC4")
	spatialConsistent := spaces > 0

	result := &ValidationResult{
		Success:  true,
		Valid:    len(errors) == 0,
		Warnings: warnings,
		Errors:   errors,
		Compliance: ComplianceInfo{
			BuildingSMART:      buildingSMART,
			IFC4:               ifc4Compliant,
			SpatialConsistency: spatialConsistent,
		},
		Metadata: IFCMetadata{
			IFCVersion:     ifcVersion,
			FileSize:       len(data),
			ProcessingTime: fmt.Sprintf("%.2fs", time.Since(startTime).Seconds()),
			Timestamp:      time.Now().UTC().Format(time.RFC3339),
		},
	}

	return result, nil
}

// isValidIFC checks if the data appears to be a valid IFC file
func (p *NativeParser) isValidIFC(data []byte) bool {
	content := string(data)

	// Check for IFC file header
	if !strings.Contains(content, "ISO-10303-21") {
		return false
	}

	// Check for IFC file footer
	if !strings.Contains(content, "END-ISO-10303-21") {
		return false
	}

	// Check for basic IFC structure
	if !strings.Contains(content, "IFCPROJECT") {
		return false
	}

	return true
}

// countEntities counts occurrences of a specific IFC entity type
func (p *NativeParser) countEntities(content, entityType string) int {
	// Convert to uppercase for case-insensitive matching
	upperContent := strings.ToUpper(content)
	upperEntityType := strings.ToUpper(entityType)

	// Count occurrences of the entity type
	count := strings.Count(upperContent, upperEntityType)

	// Subtract 1 if the entity type appears in comments or other contexts
	// This is a basic heuristic and may not be 100% accurate
	return count
}

// extractIFCVersion extracts the IFC version from the file content
func (p *NativeParser) extractIFCVersion(content string) string {
	// Look for IFC version in the file
	lines := strings.Split(content, "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if strings.Contains(line, "IFC4") {
			return "IFC4"
		}
		if strings.Contains(line, "IFC2X3") {
			return "IFC2X3"
		}
		if strings.Contains(line, "IFC2X2") {
			return "IFC2X2"
		}
	}

	return "Unknown"
}

// GetMaxFileSize returns the maximum file size allowed by the parser
func (p *NativeParser) GetMaxFileSize() int64 {
	return p.maxFileSize
}

// SetMaxFileSize sets the maximum file size allowed by the parser
func (p *NativeParser) SetMaxFileSize(size int64) {
	p.maxFileSize = size
}
