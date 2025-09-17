package converter

import (
	"bytes"
	"fmt"
	"io"
	"strings"
)

// PDFExtractedData represents data extracted from a PDF
type PDFExtractedData struct {
	Equipment []ExtractedEquipment
	Rooms     []ExtractedRoom
	RawText   string
}

// ExtractedEquipment represents equipment found in a PDF
type ExtractedEquipment struct {
	ID          string
	Type        string
	Name        string
	Room        string
	Description string
}

// ExtractedRoom represents a room found in a PDF
type ExtractedRoom struct {
	Number string
	Name   string
	Type   string
	Area   float64
}

// SimplePDFExtractor provides PDF text extraction functionality
// This bridges the gap between the old importer interface and new converter
type SimplePDFExtractor struct {
	converter *RealPDFConverter
}

// NewSimplePDFExtractor creates a new PDF extractor
func NewSimplePDFExtractor() *SimplePDFExtractor {
	return &SimplePDFExtractor{
		converter: NewRealPDFConverter(),
	}
}

// ExtractText extracts structured data from a PDF file
func (e *SimplePDFExtractor) ExtractText(input io.Reader) (*PDFExtractedData, error) {
	// Convert the PDF to BIM format using the existing converter
	var bimOutput bytes.Buffer
	if err := e.converter.ConvertToBIM(input, &bimOutput); err != nil {
		return nil, fmt.Errorf("failed to convert PDF: %w", err)
	}

	// Parse the BIM output to extract structured data
	bimText := bimOutput.String()
	data := &PDFExtractedData{
		Equipment: make([]ExtractedEquipment, 0),
		Rooms:     make([]ExtractedRoom, 0),
		RawText:   bimText,
	}

	// Parse equipment from BIM text
	lines := strings.Split(bimText, "\n")
	currentRoom := ""

	for _, line := range lines {
		line = strings.TrimSpace(line)

		// Skip empty lines and comments
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}

		// Parse room definitions
		if strings.HasPrefix(line, "ROOM:") {
			parts := strings.Fields(line)
			if len(parts) >= 3 {
				roomNum := parts[1]
				roomType := ""
				roomName := ""

				// Extract room type if present [type]
				for i, part := range parts[2:] {
					if strings.HasPrefix(part, "[") && strings.HasSuffix(part, "]") {
						roomType = strings.Trim(part, "[]")
						// Rest is room name
						if i+3 < len(parts) {
							roomName = strings.Join(parts[i+3:], " ")
						}
						break
					}
				}

				if roomName == "" && len(parts) > 2 {
					roomName = strings.Join(parts[2:], " ")
				}

				currentRoom = roomNum
				data.Rooms = append(data.Rooms, ExtractedRoom{
					Number: roomNum,
					Name:   roomName,
					Type:   roomType,
				})
			}
		}

		// Parse equipment definitions
		if strings.HasPrefix(line, "EQUIPMENT:") {
			parts := strings.Fields(line)
			if len(parts) >= 3 {
				eqID := parts[1]
				eqType := ""
				eqName := ""

				// Extract equipment type if present [type]
				for i, part := range parts[2:] {
					if strings.HasPrefix(part, "[") && strings.HasSuffix(part, "]") {
						eqType = strings.Trim(part, "[]")
						// Rest is equipment name
						if i+3 < len(parts) {
							eqName = strings.Join(parts[i+3:], " ")
						}
						break
					}
				}

				if eqName == "" && len(parts) > 2 {
					eqName = strings.Join(parts[2:], " ")
				}

				data.Equipment = append(data.Equipment, ExtractedEquipment{
					ID:   eqID,
					Type: eqType,
					Name: eqName,
					Room: currentRoom,
				})
			}
		}
	}

	return data, nil
}

// ExtractFromFile is a convenience method to extract from a file path
func (e *SimplePDFExtractor) ExtractFromFile(filepath string) (*PDFExtractedData, error) {
	// This method exists for compatibility but is not used by import.go
	// The import.go opens the file itself and passes the reader
	return nil, fmt.Errorf("ExtractFromFile not implemented - use ExtractText with an io.Reader")
}