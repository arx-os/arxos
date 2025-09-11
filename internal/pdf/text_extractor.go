package pdf

import (
	"bytes"
	"fmt"
	"os"
	"sort"
	"strings"
	
	"github.com/pdfcpu/pdfcpu/pkg/api"
	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu/model"
	"github.com/pdfcpu/pdfcpu/pkg/pdfcpu/types"
	
	"github.com/joelpate/arxos/internal/logger"
	arxmodels "github.com/joelpate/arxos/pkg/models"
)

// TextExtractor handles real PDF text extraction using pdfcpu
type TextExtractor struct {
	config *model.Configuration
}

// NewTextExtractor creates a new text extractor
func NewTextExtractor() *TextExtractor {
	return &TextExtractor{
		config: model.NewDefaultConfiguration(),
	}
}

// ExtractText extracts all text with positions from a PDF file
func (te *TextExtractor) ExtractText(pdfPath string) ([]TextData, error) {
	logger.Info("Extracting text from PDF: %s", pdfPath)
	
	// Read the PDF file
	f, err := os.Open(pdfPath)
	if err != nil {
		return nil, fmt.Errorf("failed to open PDF: %w", err)
	}
	defer f.Close()
	
	// Create context from file
	ctx, err := api.ReadContext(f, te.config)
	if err != nil {
		return nil, fmt.Errorf("failed to read PDF context: %w", err)
	}
	
	// Ensure we have a valid context
	if err := ctx.EnsurePageCount(); err != nil {
		return nil, fmt.Errorf("failed to ensure page count: %w", err)
	}
	
	var allText []TextData
	
	// Extract text from each page
	for pageNum := 1; pageNum <= ctx.PageCount; pageNum++ {
		pageText, err := te.extractPageText(ctx, pageNum)
		if err != nil {
			logger.Warn("Failed to extract text from page %d: %v", pageNum, err)
			continue
		}
		allText = append(allText, pageText...)
	}
	
	logger.Info("Extracted %d text elements from PDF", len(allText))
	return allText, nil
}

// extractPageText extracts text with positions from a specific page
func (te *TextExtractor) extractPageText(ctx *model.Context, pageNum int) ([]TextData, error) {
	// Get the page dictionary
	pageDict, _, _, err := ctx.PageDict(pageNum, false)
	if err != nil {
		return nil, fmt.Errorf("failed to get page dict: %w", err)
	}
	
	// Get content streams for the page
	contentObj, found := pageDict.Find("Contents")
	if !found {
		return []TextData{}, nil // No content on this page
	}
	
	var textData []TextData
	
	// Parse content streams
	switch content := contentObj.(type) {
	case types.StreamDict:
		// Single content stream
		texts := te.parseContentStream(content, pageNum)
		textData = append(textData, texts...)
		
	case types.Array:
		// Multiple content streams
		for _, obj := range content {
			if streamDict, ok := obj.(types.StreamDict); ok {
				texts := te.parseContentStream(streamDict, pageNum)
				textData = append(textData, texts...)
			}
		}
	}
	
	// Sort by Y position (top to bottom) then X position (left to right)
	sort.Slice(textData, func(i, j int) bool {
		if textData[i].Y != textData[j].Y {
			return textData[i].Y > textData[j].Y // Higher Y comes first (top of page)
		}
		return textData[i].X < textData[j].X
	})
	
	return textData, nil
}

// parseContentStream parses a single content stream for text
func (te *TextExtractor) parseContentStream(stream types.StreamDict, pageNum int) []TextData {
	var textData []TextData
	
	// Decode the stream if needed
	if err := stream.Decode(); err != nil {
		logger.Warn("Failed to decode stream: %v", err)
		return textData
	}
	
	// Get the decoded content
	content := stream.Content
	if len(content) == 0 {
		return textData
	}
	
	// Parse the content for text operations
	parser := &contentStreamParser{
		content:  content,
		pageNum:  pageNum,
		textData: []TextData{},
		currentX: 0,
		currentY: 0,
		fontSize: 12,
	}
	
	parser.parse()
	return parser.textData
}

// contentStreamParser parses PDF content stream operations
type contentStreamParser struct {
	content  []byte
	pageNum  int
	textData []TextData
	currentX float64
	currentY float64
	fontSize float64
}

// parse processes the content stream
func (p *contentStreamParser) parse() {
	// Convert content to string for easier parsing
	contentStr := string(p.content)
	lines := strings.Split(contentStr, "\n")
	
	var textBuffer strings.Builder
	inTextObject := false
	
	for _, line := range lines {
		line = strings.TrimSpace(line)
		
		// Check for text object boundaries
		if line == "BT" {
			inTextObject = true
			continue
		}
		if line == "ET" {
			if textBuffer.Len() > 0 {
				// Save accumulated text
				p.textData = append(p.textData, TextData{
					Text:     strings.TrimSpace(textBuffer.String()),
					X:        p.currentX,
					Y:        p.currentY,
					FontSize: p.fontSize,
					Page:     p.pageNum,
				})
				textBuffer.Reset()
			}
			inTextObject = false
			continue
		}
		
		if !inTextObject {
			continue
		}
		
		// Parse text positioning operators
		if strings.HasSuffix(line, " Td") {
			// Text positioning
			parts := strings.Fields(line)
			if len(parts) >= 3 {
				if x, err := parseFloat(parts[0]); err == nil {
					p.currentX += x
				}
				if y, err := parseFloat(parts[1]); err == nil {
					p.currentY += y
				}
			}
		} else if strings.HasSuffix(line, " Tm") {
			// Text matrix
			parts := strings.Fields(line)
			if len(parts) >= 7 {
				if x, err := parseFloat(parts[4]); err == nil {
					p.currentX = x
				}
				if y, err := parseFloat(parts[5]); err == nil {
					p.currentY = y
				}
			}
		} else if strings.HasSuffix(line, " Tf") {
			// Font and size
			parts := strings.Fields(line)
			if len(parts) >= 2 {
				if size, err := parseFloat(parts[len(parts)-2]); err == nil {
					p.fontSize = size
				}
			}
		} else if strings.Contains(line, "Tj") {
			// Text showing operators
			text := p.extractTextFromTj(line)
			if text != "" {
				textBuffer.WriteString(text)
				textBuffer.WriteString(" ")
			}
		} else if strings.Contains(line, "TJ") {
			// Array text showing
			text := p.extractTextFromTJ(line)
			if text != "" {
				textBuffer.WriteString(text)
				textBuffer.WriteString(" ")
			}
		}
	}
}

// extractTextFromTj extracts text from Tj operator
func (p *contentStreamParser) extractTextFromTj(line string) string {
	// Extract text between parentheses
	start := strings.Index(line, "(")
	end := strings.LastIndex(line, ")")
	
	if start >= 0 && end > start {
		text := line[start+1 : end]
		// Unescape PDF string
		text = unescapePDFString(text)
		return text
	}
	
	// Try hex string format
	start = strings.Index(line, "<")
	end = strings.LastIndex(line, ">")
	
	if start >= 0 && end > start {
		hexStr := line[start+1 : end]
		text := decodeHexString(hexStr)
		return text
	}
	
	return ""
}

// extractTextFromTJ extracts text from TJ operator (array format)
func (p *contentStreamParser) extractTextFromTJ(line string) string {
	var result strings.Builder
	
	// Extract array content between [ ]
	start := strings.Index(line, "[")
	end := strings.LastIndex(line, "]")
	
	if start < 0 || end <= start {
		return ""
	}
	
	arrayContent := line[start+1 : end]
	
	// Parse array elements
	inString := false
	inHex := false
	var current strings.Builder
	
	for i := 0; i < len(arrayContent); i++ {
		ch := arrayContent[i]
		
		if !inString && !inHex {
			if ch == '(' {
				inString = true
				current.Reset()
			} else if ch == '<' {
				inHex = true
				current.Reset()
			}
		} else if inString {
			if ch == ')' && (i == 0 || arrayContent[i-1] != '\\') {
				inString = false
				text := unescapePDFString(current.String())
				result.WriteString(text)
			} else {
				current.WriteByte(ch)
			}
		} else if inHex {
			if ch == '>' {
				inHex = false
				text := decodeHexString(current.String())
				result.WriteString(text)
			} else {
				current.WriteByte(ch)
			}
		}
	}
	
	return result.String()
}

// unescapePDFString unescapes a PDF string
func unescapePDFString(s string) string {
	// Handle common PDF escape sequences
	s = strings.ReplaceAll(s, "\\n", "\n")
	s = strings.ReplaceAll(s, "\\r", "\r")
	s = strings.ReplaceAll(s, "\\t", "\t")
	s = strings.ReplaceAll(s, "\\(", "(")
	s = strings.ReplaceAll(s, "\\)", ")")
	s = strings.ReplaceAll(s, "\\\\", "\\")
	
	// Handle octal sequences
	var result strings.Builder
	i := 0
	for i < len(s) {
		if s[i] == '\\' && i+1 < len(s) {
			// Check for octal sequence
			if i+3 < len(s) && isOctal(s[i+1]) && isOctal(s[i+2]) && isOctal(s[i+3]) {
				// Three-digit octal
				val := (int(s[i+1]-'0') << 6) | (int(s[i+2]-'0') << 3) | int(s[i+3]-'0')
				result.WriteByte(byte(val))
				i += 4
			} else if i+2 < len(s) && isOctal(s[i+1]) && isOctal(s[i+2]) {
				// Two-digit octal
				val := (int(s[i+1]-'0') << 3) | int(s[i+2]-'0')
				result.WriteByte(byte(val))
				i += 3
			} else if i+1 < len(s) && isOctal(s[i+1]) {
				// One-digit octal
				val := int(s[i+1] - '0')
				result.WriteByte(byte(val))
				i += 2
			} else {
				// Not an octal sequence
				result.WriteByte(s[i])
				i++
			}
		} else {
			result.WriteByte(s[i])
			i++
		}
	}
	
	return result.String()
}

// isOctal checks if a byte is an octal digit
func isOctal(b byte) bool {
	return b >= '0' && b <= '7'
}

// decodeHexString decodes a hex-encoded PDF string
func decodeHexString(hex string) string {
	// Remove spaces
	hex = strings.ReplaceAll(hex, " ", "")
	
	// Ensure even length
	if len(hex)%2 != 0 {
		hex += "0"
	}
	
	var result strings.Builder
	for i := 0; i < len(hex); i += 2 {
		if val, err := parseHexByte(hex[i : i+2]); err == nil {
			result.WriteByte(val)
		}
	}
	
	return result.String()
}

// parseHexByte parses a two-character hex string to a byte
func parseHexByte(hex string) (byte, error) {
	if len(hex) != 2 {
		return 0, fmt.Errorf("invalid hex byte")
	}
	
	val := 0
	for i := 0; i < 2; i++ {
		val <<= 4
		ch := hex[i]
		if ch >= '0' && ch <= '9' {
			val |= int(ch - '0')
		} else if ch >= 'a' && ch <= 'f' {
			val |= int(ch - 'a' + 10)
		} else if ch >= 'A' && ch <= 'F' {
			val |= int(ch - 'A' + 10)
		} else {
			return 0, fmt.Errorf("invalid hex character")
		}
	}
	
	return byte(val), nil
}

// parseFloat parses a string to float64
func parseFloat(s string) (float64, error) {
	var val float64
	_, err := fmt.Sscanf(s, "%f", &val)
	return val, err
}

// ExtractAndParse combines extraction and parsing for a complete solution
func (te *TextExtractor) ExtractAndParse(pdfPath string) (*arxmodels.FloorPlan, error) {
	// Extract text
	textData, err := te.ExtractText(pdfPath)
	if err != nil {
		return nil, fmt.Errorf("failed to extract text: %w", err)
	}
	
	// Use the universal parser to convert text to floor plan
	parser := NewUniversalParser()
	plan := &arxmodels.FloorPlan{
		Name:      strings.TrimSuffix(pdfPath, ".pdf"),
		Building:  "Imported Building",
		Level:     1,
		Rooms:     []arxmodels.Room{},
		Equipment: []arxmodels.Equipment{},
	}
	
	if len(textData) > 0 {
		parser.parseTextElements(textData, plan)
	}
	
	// Generate spatial layout if needed
	parser.generateSpatialLayout(plan)
	
	return plan, nil
}

// ExtractTextToBuffer extracts all text to a simple buffer for debugging
func (te *TextExtractor) ExtractTextToBuffer(pdfPath string) (string, error) {
	textData, err := te.ExtractText(pdfPath)
	if err != nil {
		return "", err
	}
	
	var buf bytes.Buffer
	currentY := -1.0
	
	for _, text := range textData {
		// Add newline when Y position changes significantly
		if currentY >= 0 && abs(text.Y-currentY) > 5 {
			buf.WriteString("\n")
		}
		
		buf.WriteString(text.Text)
		buf.WriteString(" ")
		currentY = text.Y
	}
	
	return buf.String(), nil
}

func abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}