// Package pdf provides PDF document parsing functionality
package pdf

import (
	"fmt"
	"os"
	"regexp"
	"strconv"
	"strings"

	"github.com/arxos/arxos/internal/types"
)

// Parser implements the PDFParser interface
type Parser struct {
	config *types.ParseConfig
}

// NewParser creates a new PDF parser with default configuration
func NewParser() *Parser {
	return &Parser{
		config: types.DefaultParseConfig(),
	}
}

// NewParserWithConfig creates a new PDF parser with custom configuration
func NewParserWithConfig(config *types.ParseConfig) *Parser {
	return &Parser{
		config: config,
	}
}

// ParseFile parses a PDF file and returns a Document
func (p *Parser) ParseFile(path string) (*types.Document, error) {
	// Read PDF file
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read PDF file: %w", err)
	}

	// Validate PDF format
	if !p.isValidPDF(data) {
		return nil, fmt.Errorf("invalid PDF format")
	}

	// Extract version
	version := p.extractVersion(data)

	// Extract all objects
	objects, err := p.extractObjects(data)
	if err != nil {
		return nil, fmt.Errorf("failed to extract PDF objects: %w", err)
	}

	// Extract images
	images, err := p.extractImages(objects)
	if err != nil {
		return nil, fmt.Errorf("failed to extract images: %w", err)
	}

	// Extract metadata
	metadata := p.extractMetadata(objects, path)

	doc := &types.Document{
		Version:  version,
		Objects:  objects,
		Images:   images,
		Metadata: metadata,
	}

	return doc, nil
}

// ParseStream parses a PDF from an io.Reader (not implemented yet)
func (p *Parser) ParseStream(reader interface{}) (*types.Document, error) {
	return nil, fmt.Errorf("ParseStream not yet implemented")
}

// isValidPDF checks if the data represents a valid PDF
func (p *Parser) isValidPDF(data []byte) bool {
	if len(data) < 8 {
		return false
	}
	return strings.HasPrefix(string(data[:8]), "%PDF-")
}

// extractVersion extracts the PDF version
func (p *Parser) extractVersion(data []byte) string {
	if len(data) < 8 {
		return "unknown"
	}
	
	header := string(data[:20])
	if strings.HasPrefix(header, "%PDF-") {
		return strings.TrimSpace(header[5:9])
	}
	
	return "unknown"
}

// extractObjects extracts all PDF objects from the document
func (p *Parser) extractObjects(data []byte) (map[int]*types.PDFObject, error) {
	objects := make(map[int]*types.PDFObject)

	// Use the proven regex pattern from our working parsers
	objPattern := regexp.MustCompile(`(?s)(\d+)\s+(\d+)\s+obj(.*?)endobj`)
	matches := objPattern.FindAllSubmatch(data, -1)

	for _, match := range matches {
		if len(match) >= 4 {
			objNum, err := strconv.Atoi(string(match[1]))
			if err != nil {
				continue
			}

			generation, err := strconv.Atoi(string(match[2]))
			if err != nil {
				generation = 0
			}

			objData := match[3]
			objStr := string(objData)

			// Determine object type
			objType := p.determineObjectType(objStr)

			// Extract filters
			filters := p.extractFilters(objStr)

			objects[objNum] = &types.PDFObject{
				ID:         objNum,
				Generation: generation,
				Data:       objData,
				Type:       objType,
				Filters:    filters,
			}
		}
	}

	return objects, nil
}

// extractImages finds and extracts embedded images from PDF objects
func (p *Parser) extractImages(objects map[int]*types.PDFObject) ([]*types.EmbeddedImage, error) {
	images := []*types.EmbeddedImage{}

	for objID, obj := range objects {
		if p.isImageObject(obj) {
			img, err := p.parseImageObject(objID, obj)
			if err != nil {
				if p.config.Debug {
					fmt.Printf("Warning: failed to parse image object %d: %v\n", objID, err)
				}
				continue
			}
			images = append(images, img)
		}
	}

	return images, nil
}

// isImageObject checks if a PDF object represents an image
func (p *Parser) isImageObject(obj *types.PDFObject) bool {
	objStr := string(obj.Data)
	return strings.Contains(objStr, "/Type") &&
		strings.Contains(objStr, "/XObject") &&
		strings.Contains(objStr, "/Subtype") &&
		strings.Contains(objStr, "/Image")
}

// parseImageObject parses an image object and extracts its properties
func (p *Parser) parseImageObject(objID int, obj *types.PDFObject) (*types.EmbeddedImage, error) {
	objStr := string(obj.Data)

	img := &types.EmbeddedImage{
		ObjectID:         objID,
		Width:            p.extractIntValue(objStr, "/Width"),
		Height:           p.extractIntValue(objStr, "/Height"),
		BitsPerComponent: p.extractIntValue(objStr, "/BitsPerComponent"),
		ColorSpace:       p.extractStringValue(objStr, "/ColorSpace"),
		Filter:           p.extractStringValue(objStr, "/Filter"),
	}

	// Extract raw image data
	streamPattern := regexp.MustCompile(`(?s)stream\s*([\s\S]*?)\s*endstream`)
	if matches := streamPattern.FindAllSubmatch(obj.Data, -1); len(matches) > 0 {
		img.RawData = matches[0][1]
	}

	return img, nil
}

// determineObjectType determines the type of PDF object
func (p *Parser) determineObjectType(objStr string) string {
	if strings.Contains(objStr, "/Type") {
		if strings.Contains(objStr, "/XObject") {
			if strings.Contains(objStr, "/Image") {
				return "image"
			}
			return "xobject"
		}
		if strings.Contains(objStr, "/Page") {
			return "page"
		}
		if strings.Contains(objStr, "/Font") {
			return "font"
		}
		if strings.Contains(objStr, "/Catalog") {
			return "catalog"
		}
	}
	
	if strings.Contains(objStr, "stream") {
		return "stream"
	}
	
	return "unknown"
}

// extractFilters extracts compression/encoding filters from object
func (p *Parser) extractFilters(objStr string) []string {
	filters := []string{}
	
	if strings.Contains(objStr, "/FlateDecode") {
		filters = append(filters, "FlateDecode")
	}
	if strings.Contains(objStr, "/LZWDecode") {
		filters = append(filters, "LZWDecode")
	}
	if strings.Contains(objStr, "/DCTDecode") {
		filters = append(filters, "DCTDecode")
	}
	
	return filters
}

// extractIntValue extracts an integer value for a given key
func (p *Parser) extractIntValue(content, key string) int {
	pattern := regexp.MustCompile(key + `\s*(\d+)`)
	if matches := pattern.FindStringSubmatch(content); len(matches) > 1 {
		if val, err := strconv.Atoi(matches[1]); err == nil {
			return val
		}
	}
	return 0
}

// extractStringValue extracts a string value for a given key
func (p *Parser) extractStringValue(content, key string) string {
	pattern := regexp.MustCompile(key + `\s*/([A-Za-z0-9]+)`)
	if matches := pattern.FindStringSubmatch(content); len(matches) > 1 {
		return matches[1]
	}
	return ""
}

// extractMetadata extracts document metadata
func (p *Parser) extractMetadata(objects map[int]*types.PDFObject, path string) types.DocumentMetadata {
	metadata := types.DocumentMetadata{
		Creator:   "Unknown",
		CreatedAt: "Unknown",
		Title:     "Unknown",
		PageCount: 1,
	}

	// Get file size
	if info, err := os.Stat(path); err == nil {
		metadata.FileSize = info.Size()
	}

	// Extract metadata from document info objects
	for _, obj := range objects {
		if obj.Type == "unknown" {
			objStr := string(obj.Data)
			
			if createdDate := p.extractStringValue(objStr, "/CreationDate"); createdDate != "" {
				metadata.CreatedAt = createdDate
			}
			
			if creator := p.extractStringValue(objStr, "/Creator"); creator != "" {
				metadata.Creator = creator
			}
			
			if title := p.extractStringValue(objStr, "/Title"); title != "" {
				metadata.Title = title
			}
		}
	}

	return metadata
}