// Package pdf provides text extraction functionality
package pdf

import (
	"bytes"
	"compress/zlib"
	"fmt"
	"io"
	"regexp"
	"strings"

	"github.com/arxos/arxos/internal/types"
)

// TextExtractor implements the TextExtractor interface
type TextExtractor struct {
	config *types.ParseConfig
}

// NewTextExtractor creates a new text extractor
func NewTextExtractor() *TextExtractor {
	return &TextExtractor{
		config: types.DefaultParseConfig(),
	}
}

// NewTextExtractorWithConfig creates a new text extractor with custom configuration
func NewTextExtractorWithConfig(config *types.ParseConfig) *TextExtractor {
	return &TextExtractor{
		config: config,
	}
}

// ExtractText extracts all text from a PDF document
func (t *TextExtractor) ExtractText(doc *types.Document) (string, error) {
	switch t.config.TextExtractionMode {
	case "comprehensive":
		return t.extractComprehensiveText(doc)
	case "basic":
		return t.extractBasicText(doc)
	case "hybrid":
		return t.extractHybridText(doc)
	default:
		return t.extractComprehensiveText(doc)
	}
}

// extractComprehensiveText uses multiple methods to extract text
func (t *TextExtractor) extractComprehensiveText(doc *types.Document) (string, error) {
	textBuilder := strings.Builder{}

	// Method 1: Extract from compressed streams
	streamText, err := t.extractFromCompressedStreams(doc.Objects)
	if err == nil && len(streamText) > 0 {
		textBuilder.WriteString(streamText)
		textBuilder.WriteString(" ")
	}

	// Method 2: Extract from uncompressed objects
	uncompressedText := t.extractFromUncompressedObjects(doc.Objects)
	if len(uncompressedText) > 0 {
		textBuilder.WriteString(uncompressedText)
		textBuilder.WriteString(" ")
	}

	// Method 3: Raw data search as fallback
	if textBuilder.Len() == 0 {
		rawText := t.extractFromRawData(doc)
		textBuilder.WriteString(rawText)
	}

	allText := textBuilder.String()
	
	// Store extracted text in document
	doc.Text = allText

	if t.config.Debug {
		fmt.Printf("Extracted %d characters of text using comprehensive method\n", len(allText))
	}

	return allText, nil
}

// extractFromCompressedStreams extracts text from compressed PDF streams
func (t *TextExtractor) extractFromCompressedStreams(objects map[int]*types.PDFObject) (string, error) {
	textBuilder := strings.Builder{}

	for objID, obj := range objects {
		// Only process objects with FlateDecode filter
		if !t.hasFilter(obj, "FlateDecode") {
			continue
		}

		// Extract stream data
		streamPattern := regexp.MustCompile(`(?s)stream\s*([\s\S]*?)\s*endstream`)
		matches := streamPattern.FindAllSubmatch(obj.Data, -1)

		for _, match := range matches {
			if len(match) >= 2 {
				rawData := match[1]

				// Try to decompress
				if decompressed, err := t.decompressFlateData(rawData); err == nil {
					decompressedStr := string(decompressed)

					if t.config.Debug {
						fmt.Printf("Object %d: Decompressed %d bytes -> %d chars\n", 
							objID, len(rawData), len(decompressedStr))
					}

					// Extract readable text from decompressed content
					extractedText := t.extractReadableText(decompressedStr)
					if len(extractedText) > 0 {
						textBuilder.WriteString(extractedText + " ")
					}
				}
			}
		}
	}

	return textBuilder.String(), nil
}

// extractFromUncompressedObjects extracts text from uncompressed PDF objects
func (t *TextExtractor) extractFromUncompressedObjects(objects map[int]*types.PDFObject) string {
	textBuilder := strings.Builder{}

	for _, obj := range objects {
		objStr := string(obj.Data)
		extractedText := t.extractReadableText(objStr)
		if len(extractedText) > 0 {
			textBuilder.WriteString(extractedText + " ")
		}
	}

	return textBuilder.String()
}

// extractFromRawData searches raw document data as fallback
func (t *TextExtractor) extractFromRawData(doc *types.Document) string {
	// This would search through raw PDF data for text patterns
	// Implementation would depend on having access to raw document bytes
	// For now, return empty string as this is a fallback method
	return ""
}

// extractReadableText extracts readable text from PDF content
func (t *TextExtractor) extractReadableText(content string) string {
	textBuilder := strings.Builder{}

	// Method 1: Extract text between parentheses (PDF text format)
	textPattern := regexp.MustCompile(`\(([^)]+)\)`)
	matches := textPattern.FindAllStringSubmatch(content, -1)
	for _, match := range matches {
		if len(match) >= 2 {
			text := strings.TrimSpace(match[1])
			if t.isArchitecturalText(text) {
				textBuilder.WriteString(text + " ")
			}
		}
	}

	// Method 2: Extract text from 'Tj' and 'TJ' operators
	tjPattern := regexp.MustCompile(`\(([^)]+)\)\s*T[jJ]`)
	tjMatches := tjPattern.FindAllStringSubmatch(content, -1)
	for _, match := range tjMatches {
		if len(match) >= 2 {
			text := strings.TrimSpace(match[1])
			if t.isArchitecturalText(text) {
				textBuilder.WriteString(text + " ")
			}
		}
	}

	// Method 3: Look for standalone architectural text
	lines := strings.Split(content, "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if t.isArchitecturalText(line) && len(line) < 50 {
			textBuilder.WriteString(line + " ")
		}
	}

	return textBuilder.String()
}

// ExtractRoomNumbers extracts room numbers from text
func (t *TextExtractor) ExtractRoomNumbers(text string) ([]string, error) {
	roomNumbers := []string{}
	roomSet := make(map[string]bool)

	// Pattern for 3-digit room numbers, possibly with letter suffix
	roomPattern := regexp.MustCompile(`\b(\d{3}[a-zA-Z]?)\b`)
	matches := roomPattern.FindAllStringSubmatch(text, -1)

	for _, match := range matches {
		if len(match) >= 2 {
			room := match[1]
			
			// Validate it looks like a real room number (300-999 range)
			if t.isValidRoomNumber(room) && !roomSet[room] {
				roomNumbers = append(roomNumbers, room)
				roomSet[room] = true
			}
		}
	}

	return roomNumbers, nil
}

// ExtractIDFReferences extracts IDF location references from text
func (t *TextExtractor) ExtractIDFReferences(text string) ([]string, error) {
	idfLocations := []string{}
	idfSet := make(map[string]bool)

	// Pattern for IDF and MDF references
	idfPattern := regexp.MustCompile(`(?i)\b((IDF|MDF)\s*\d+[a-zA-Z]?)\b`)
	matches := idfPattern.FindAllStringSubmatch(text, -1)

	for _, match := range matches {
		if len(match) >= 2 {
			idf := strings.TrimSpace(match[1])
			if !idfSet[idf] {
				idfLocations = append(idfLocations, idf)
				idfSet[idf] = true
			}
		}
	}

	return idfLocations, nil
}

// isArchitecturalText checks if text is relevant to architectural drawings
func (t *TextExtractor) isArchitecturalText(text string) bool {
	text = strings.TrimSpace(text)
	if len(text) == 0 || len(text) > 100 {
		return false
	}

	// Room number patterns
	roomPattern := regexp.MustCompile(`^\d{3}[a-zA-Z]?$`)
	if roomPattern.MatchString(text) {
		return true
	}

	// IDF/MDF patterns
	idfPattern := regexp.MustCompile(`(?i)^(IDF|MDF)\s*\d+[a-zA-Z]?$`)
	if idfPattern.MatchString(text) {
		return true
	}

	// Architectural keywords
	archKeywords := []string{
		"IDF", "MDF", "ROOM", "PANEL", "RACK", "ELECTRICAL", "NETWORK",
		"CORRIDOR", "HALLWAY", "CLASSROOM", "OFFICE", "STORAGE", "UTILITY",
		"RESTROOM", "ENTRANCE", "EXIT", "DOOR", "WINDOW",
	}

	upperText := strings.ToUpper(text)
	for _, keyword := range archKeywords {
		if strings.Contains(upperText, keyword) {
			return true
		}
	}

	// Dimensions and measurements
	if strings.Contains(text, "'") || strings.Contains(text, "\"") ||
		strings.Contains(text, "ft") || strings.Contains(text, "foot") ||
		strings.Contains(text, "inch") {
		return true
	}

	return false
}

// isValidRoomNumber validates that a number looks like a real room number
func (t *TextExtractor) isValidRoomNumber(room string) bool {
	// Room numbers are typically in the 300-900 range for most buildings
	// This filters out coordinates, dimensions, and other numeric data
	
	if len(room) < 3 {
		return false
	}

	// Extract numeric part
	numStr := room
	for i, r := range room {
		if r < '0' || r > '9' {
			numStr = room[:i]
			break
		}
	}

	// Check if it's in a reasonable room number range
	if len(numStr) == 3 {
		firstDigit := numStr[0]
		// Most building room numbers start with 1-9, not 0
		if firstDigit >= '1' && firstDigit <= '9' {
			return true
		}
	}

	return false
}

// hasFilter checks if an object has a specific filter
func (t *TextExtractor) hasFilter(obj *types.PDFObject, filter string) bool {
	for _, f := range obj.Filters {
		if f == filter {
			return true
		}
	}
	return false
}

// decompressFlateData decompresses FlateDecode (zlib) data
func (t *TextExtractor) decompressFlateData(rawData []byte) ([]byte, error) {
	reader, err := zlib.NewReader(bytes.NewReader(rawData))
	if err != nil {
		return nil, err
	}
	defer reader.Close()

	decompressed, err := io.ReadAll(reader)
	if err != nil {
		return nil, err
	}

	return decompressed, nil
}

// extractBasicText uses simple text extraction methods
func (t *TextExtractor) extractBasicText(doc *types.Document) (string, error) {
	textBuilder := strings.Builder{}

	// Extract from uncompressed objects only
	uncompressedText := t.extractFromUncompressedObjects(doc.Objects)
	textBuilder.WriteString(uncompressedText)

	allText := textBuilder.String()
	doc.Text = allText

	if t.config.Debug {
		fmt.Printf("Extracted %d characters of text using basic method\n", len(allText))
	}

	return allText, nil
}

// extractHybridText combines multiple extraction approaches
func (t *TextExtractor) extractHybridText(doc *types.Document) (string, error) {
	textBuilder := strings.Builder{}

	// Method 1: Try compressed streams first
	streamText, err := t.extractFromCompressedStreams(doc.Objects)
	if err == nil && len(streamText) > 0 {
		textBuilder.WriteString(streamText)
		textBuilder.WriteString(" ")
	}

	// Method 2: Add uncompressed if we don't have much text yet
	if textBuilder.Len() < 1000 {
		uncompressedText := t.extractFromUncompressedObjects(doc.Objects)
		if len(uncompressedText) > 0 {
			textBuilder.WriteString(uncompressedText)
		}
	}

	allText := textBuilder.String()
	doc.Text = allText

	if t.config.Debug {
		fmt.Printf("Extracted %d characters of text using hybrid method\n", len(allText))
	}

	return allText, nil
}