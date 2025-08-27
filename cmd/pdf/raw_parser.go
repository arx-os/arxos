package pdf

import (
	"bytes"
	"compress/zlib"
	"fmt"
	"io"
	"os"
	"regexp"
	"strconv"
	"strings"
)

// RawPDFParser parses PDF files directly without external dependencies
type RawPDFParser struct {
	data        []byte
	xref        map[int]int // object number -> byte offset
	pages       []PDFPage
	currentPage int
}

// PDFPage represents a page with its content
type PDFPage struct {
	Number  int
	Content string
	Objects []PDFObject
}

// PDFObject represents an object in the PDF
type PDFObject struct {
	Number int
	Type   string
	Data   []byte
}

// NewRawPDFParser creates a new PDF parser
func NewRawPDFParser() *RawPDFParser {
	return &RawPDFParser{
		xref: make(map[int]int),
	}
}

// ParseFile parses a PDF file
func (p *RawPDFParser) ParseFile(filename string) error {
	data, err := os.ReadFile(filename)
	if err != nil {
		return fmt.Errorf("failed to read file: %w", err)
	}
	
	p.data = data
	
	// Verify PDF header
	if !bytes.HasPrefix(data, []byte("%PDF")) {
		return fmt.Errorf("not a valid PDF file")
	}
	
	// Parse cross-reference table
	if err := p.parseXRef(); err != nil {
		return fmt.Errorf("failed to parse xref: %w", err)
	}
	
	// Extract content streams
	if err := p.extractContent(); err != nil {
		return fmt.Errorf("failed to extract content: %w", err)
	}
	
	return nil
}

// parseXRef parses the cross-reference table
func (p *RawPDFParser) parseXRef() error {
	// Find xref position (usually at end of file)
	xrefPos := bytes.LastIndex(p.data, []byte("xref"))
	if xrefPos == -1 {
		// Try to find it from startxref
		startxrefPos := bytes.LastIndex(p.data, []byte("startxref"))
		if startxrefPos == -1 {
			return fmt.Errorf("xref table not found")
		}
		
		// Read the offset
		offsetData := p.data[startxrefPos+10 : startxrefPos+30]
		lines := bytes.Split(offsetData, []byte("\n"))
		if len(lines) > 0 {
			offset, _ := strconv.Atoi(strings.TrimSpace(string(lines[0])))
			xrefPos = offset
		}
	}
	
	if xrefPos < 0 || xrefPos >= len(p.data) {
		return fmt.Errorf("invalid xref position")
	}
	
	// Parse xref entries
	xrefData := p.data[xrefPos:]
	lines := bytes.Split(xrefData, []byte("\n"))
	
	for i, line := range lines {
		lineStr := string(bytes.TrimSpace(line))
		
		// Skip empty lines and headers
		if lineStr == "" || lineStr == "xref" || strings.HasPrefix(lineStr, "trailer") {
			continue
		}
		
		// Check if this is a subsection header (e.g., "0 6")
		if regexp.MustCompile(`^\d+\s+\d+$`).MatchString(lineStr) {
			continue
		}
		
		// Parse xref entry (e.g., "0000000015 00000 n")
		parts := strings.Fields(lineStr)
		if len(parts) == 3 && parts[2] == "n" {
			offset, err := strconv.Atoi(parts[0])
			if err == nil {
				// The object number is determined by position in xref
				objNum := i // Simplified - real implementation needs subsection tracking
				p.xref[objNum] = offset
			}
		}
	}
	
	return nil
}

// extractContent extracts text content from the PDF
func (p *RawPDFParser) extractContent() error {
	p.pages = []PDFPage{}
	
	// Find all stream objects
	streamPattern := regexp.MustCompile(`(\d+)\s+\d+\s+obj[\s\S]*?stream([\s\S]*?)endstream`)
	matches := streamPattern.FindAllSubmatch(p.data, -1)
	
	for _, match := range matches {
		if len(match) > 2 {
			objNum, _ := strconv.Atoi(string(match[1]))
			streamData := match[2]
			
			// Check if this might be a content stream
			if p.isContentStream(streamData) {
				// Try to decompress if compressed
				content := p.decompressStream(streamData)
				
				// Extract text from content
				text := p.extractTextFromStream(content)
				if text != "" {
					p.pages = append(p.pages, PDFPage{
						Number:  len(p.pages) + 1,
						Content: text,
						Objects: []PDFObject{
							{Number: objNum, Type: "stream", Data: content},
						},
					})
				}
			}
		}
	}
	
	return nil
}

// isContentStream checks if a stream might contain text content
func (p *RawPDFParser) isContentStream(data []byte) bool {
	// Look for text operators (BT, ET, Tj, TJ, etc.)
	textOps := [][]byte{
		[]byte("BT"), // Begin text
		[]byte("ET"), // End text
		[]byte("Tj"), // Show text
		[]byte("TJ"), // Show text array
		[]byte("Tm"), // Text matrix
		[]byte("Tf"), // Text font
	}
	
	for _, op := range textOps {
		if bytes.Contains(data, op) {
			return true
		}
	}
	
	// Also check for common text patterns
	return bytes.Contains(data, []byte("(")) && bytes.Contains(data, []byte(")"))
}

// decompressStream attempts to decompress a stream if it's compressed
func (p *RawPDFParser) decompressStream(data []byte) []byte {
	// Try FlateDecode (most common)
	reader, err := zlib.NewReader(bytes.NewReader(data))
	if err == nil {
		decompressed, err := io.ReadAll(reader)
		reader.Close()
		if err == nil {
			return decompressed
		}
	}
	
	// Return original if decompression fails
	return data
}

// extractTextFromStream extracts readable text from a content stream
func (p *RawPDFParser) extractTextFromStream(data []byte) string {
	var text strings.Builder
	
	// Find text between parentheses (simplified text extraction)
	// Format: (text) Tj or [(text)] TJ
	
	inText := false
	inParen := false
	parenDepth := 0
	current := strings.Builder{}
	
	for i := 0; i < len(data); i++ {
		b := data[i]
		
		// Check for BT (begin text)
		if i < len(data)-1 && data[i] == 'B' && data[i+1] == 'T' {
			inText = true
			i++
			continue
		}
		
		// Check for ET (end text)
		if i < len(data)-1 && data[i] == 'E' && data[i+1] == 'T' {
			inText = false
			i++
			continue
		}
		
		if inText {
			if b == '(' {
				if !inParen {
					inParen = true
					parenDepth = 1
					current.Reset()
				} else {
					parenDepth++
					current.WriteByte(b)
				}
			} else if b == ')' {
				parenDepth--
				if parenDepth == 0 {
					inParen = false
					// Process the text
					extracted := p.processExtractedText(current.String())
					if extracted != "" {
						text.WriteString(extracted)
						text.WriteString(" ")
					}
				} else {
					current.WriteByte(b)
				}
			} else if inParen {
				// Handle escape sequences
				if b == '\\' && i < len(data)-1 {
					next := data[i+1]
					switch next {
					case 'n':
						current.WriteString("\n")
						i++
					case 'r':
						current.WriteString("\r")
						i++
					case 't':
						current.WriteString("\t")
						i++
					case '\\', '(', ')':
						current.WriteByte(next)
						i++
					default:
						// Octal codes (e.g., \040 for space)
						if next >= '0' && next <= '7' {
							octal := string([]byte{next})
							if i+2 < len(data) && data[i+2] >= '0' && data[i+2] <= '7' {
								octal += string(data[i+2])
								if i+3 < len(data) && data[i+3] >= '0' && data[i+3] <= '7' {
									octal += string(data[i+3])
									i++
								}
								i++
							}
							code, _ := strconv.ParseInt(octal, 8, 16)
							current.WriteByte(byte(code))
							i++
						}
					}
				} else {
					current.WriteByte(b)
				}
			}
		}
	}
	
	return strings.TrimSpace(text.String())
}

// processExtractedText cleans up extracted text
func (p *RawPDFParser) processExtractedText(text string) string {
	// Remove null characters
	text = strings.ReplaceAll(text, "\x00", "")
	
	// Handle common PDF encodings
	// This is simplified - real PDF parsing needs proper encoding handling
	
	// Clean up whitespace
	text = strings.TrimSpace(text)
	
	return text
}

// GetText returns all extracted text
func (p *RawPDFParser) GetText() string {
	var allText strings.Builder
	
	for _, page := range p.pages {
		if page.Content != "" {
			allText.WriteString(fmt.Sprintf("Page %d:\n", page.Number))
			allText.WriteString(page.Content)
			allText.WriteString("\n\n")
		}
	}
	
	return allText.String()
}

// GetStructuredText attempts to identify tables and structured data
func (p *RawPDFParser) GetStructuredText() []ExtractedTable {
	tables := []ExtractedTable{}
	
	for _, page := range p.pages {
		// Look for patterns that indicate tables
		lines := strings.Split(page.Content, "\n")
		
		var currentTable *ExtractedTable
		for _, line := range lines {
			// Check if line has multiple columns (multiple spaces)
			if strings.Count(line, "  ") >= 2 {
				fields := regexp.MustCompile(`\s{2,}`).Split(line, -1)
				
				if len(fields) >= 3 {
					if currentTable == nil {
						currentTable = &ExtractedTable{
							Headers: fields,
							Rows:    [][]string{},
						}
					} else {
						currentTable.Rows = append(currentTable.Rows, fields)
					}
				}
			} else if currentTable != nil && len(currentTable.Rows) > 0 {
				// End of table
				tables = append(tables, *currentTable)
				currentTable = nil
			}
		}
		
		if currentTable != nil && len(currentTable.Rows) > 0 {
			tables = append(tables, *currentTable)
		}
	}
	
	return tables
}

// ParseGraphicsOperators extracts vector graphics and drawings
func (p *RawPDFParser) ParseGraphicsOperators() []GraphicsElement {
	elements := []GraphicsElement{}
	
	for _, page := range p.pages {
		for _, obj := range page.Objects {
			// Parse drawing commands
			elements = append(elements, p.extractGraphics(obj.Data)...)
		}
	}
	
	return elements
}

// GraphicsElement represents a vector drawing element
type GraphicsElement struct {
	Type     string  // line, rect, circle, text
	X        float64
	Y        float64
	Width    float64
	Height   float64
	EndX     float64
	EndY     float64
	Text     string
	LineWidth float64
}

// extractGraphics parses PDF graphics operators
func (p *RawPDFParser) extractGraphics(data []byte) []GraphicsElement {
	elements := []GraphicsElement{}
	lines := bytes.Split(data, []byte("\n"))
	
	var currentX, currentY float64
	var pathStartX, pathStartY float64
	
	for _, line := range lines {
		parts := bytes.Fields(line)
		if len(parts) == 0 {
			continue
		}
		
		lastOp := string(parts[len(parts)-1])
		
		switch lastOp {
		case "m": // moveto
			if len(parts) >= 3 {
				currentX, _ = strconv.ParseFloat(string(parts[0]), 64)
				currentY, _ = strconv.ParseFloat(string(parts[1]), 64)
				pathStartX, pathStartY = currentX, currentY
			}
		case "l": // lineto
			if len(parts) >= 3 {
				newX, _ := strconv.ParseFloat(string(parts[0]), 64)
				newY, _ := strconv.ParseFloat(string(parts[1]), 64)
				elements = append(elements, GraphicsElement{
					Type: "line",
					X:    currentX,
					Y:    currentY,
					EndX: newX,
					EndY: newY,
				})
				currentX, currentY = newX, newY
			}
		case "re": // rectangle
			if len(parts) >= 5 {
				x, _ := strconv.ParseFloat(string(parts[0]), 64)
				y, _ := strconv.ParseFloat(string(parts[1]), 64)
				w, _ := strconv.ParseFloat(string(parts[2]), 64)
				h, _ := strconv.ParseFloat(string(parts[3]), 64)
				elements = append(elements, GraphicsElement{
					Type:   "rect",
					X:      x,
					Y:      y,
					Width:  w,
					Height: h,
				})
			}
		case "h": // close path
			if currentX != pathStartX || currentY != pathStartY {
				elements = append(elements, GraphicsElement{
					Type: "line",
					X:    currentX,
					Y:    currentY,
					EndX: pathStartX,
					EndY: pathStartY,
				})
			}
		case "w": // line width
			if len(parts) >= 2 {
				width, _ := strconv.ParseFloat(string(parts[0]), 64)
				// Apply to subsequent elements
				if len(elements) > 0 {
					elements[len(elements)-1].LineWidth = width
				}
			}
		}
	}
	
	return elements
}

// ExtractFloorPlan attempts to extract room layout from graphics
func (p *RawPDFParser) ExtractFloorPlan() *FloorPlanData {
	graphics := p.ParseGraphicsOperators()
	electrical := p.ParseElectricalData()
	
	plan := &FloorPlanData{
		Rooms:      []RoomData{},
		Electrical: electrical,
	}
	
	// Group lines into potential rooms (rectangles)
	rects := p.findRectangles(graphics)
	
	for i, rect := range rects {
		room := RoomData{
			ID:     fmt.Sprintf("room_%d", i+1),
			Bounds: rect,
		}
		
		// Find text labels within room bounds
		for _, elem := range graphics {
			if elem.Type == "text" && p.pointInRect(elem.X, elem.Y, rect) {
				if room.Name == "" {
					room.Name = elem.Text
				} else {
					room.Description = elem.Text
				}
			}
		}
		
		plan.Rooms = append(plan.Rooms, room)
	}
	
	return plan
}

// FloorPlanData represents extracted floor plan information
type FloorPlanData struct {
	Rooms      []RoomData
	Electrical []ElectricalItem
}

// RoomData represents a room extracted from PDF
type RoomData struct {
	ID          string
	Name        string
	Description string
	Bounds      GraphicsElement
}

// findRectangles identifies rectangles that could be rooms
func (p *RawPDFParser) findRectangles(graphics []GraphicsElement) []GraphicsElement {
	rects := []GraphicsElement{}
	
	for _, elem := range graphics {
		if elem.Type == "rect" {
			// Filter for room-sized rectangles
			if elem.Width > 10 && elem.Height > 10 {
				rects = append(rects, elem)
			}
		}
	}
	
	// Also look for closed line loops forming rectangles
	// This is more complex and would need proper implementation
	
	return rects
}

// pointInRect checks if a point is inside a rectangle
func (p *RawPDFParser) pointInRect(x, y float64, rect GraphicsElement) bool {
	return x >= rect.X && x <= rect.X+rect.Width &&
	       y >= rect.Y && y <= rect.Y+rect.Height
}

// ExtractedTable represents a table found in the PDF
type ExtractedTable struct {
	Headers []string
	Rows    [][]string
}

// ParseElectricalData looks for electrical panel and circuit data
func (p *RawPDFParser) ParseElectricalData() []ElectricalItem {
	items := []ElectricalItem{}
	text := p.GetText()
	
	// Look for panel identifiers
	panelPattern := regexp.MustCompile(`(?i)(PANEL|MDF|IDF|LP)[\s\-]?([A-Z0-9]+)`)
	circuitPattern := regexp.MustCompile(`(?i)(?:CKT|CIRCUIT|BKR|BREAKER)[\s#]?(\d+)`)
	ampPattern := regexp.MustCompile(`(\d+)\s*A(?:MP)?`)
	voltPattern := regexp.MustCompile(`(\d+)\s*V(?:OLT)?`)
	
	lines := strings.Split(text, "\n")
	
	var currentPanel string
	for _, line := range lines {
		// Check for panel
		if matches := panelPattern.FindStringSubmatch(line); matches != nil {
			currentPanel = matches[2]
			
			item := ElectricalItem{
				Type:  "panel",
				ID:    currentPanel,
				Name:  fmt.Sprintf("Panel %s", currentPanel),
			}
			
			// Extract voltage if present
			if vMatch := voltPattern.FindStringSubmatch(line); vMatch != nil {
				item.Voltage, _ = strconv.Atoi(vMatch[1])
			}
			
			items = append(items, item)
		}
		
		// Check for circuit/breaker
		if matches := circuitPattern.FindStringSubmatch(line); matches != nil {
			circuitNum := matches[1]
			
			item := ElectricalItem{
				Type:    "circuit",
				ID:      fmt.Sprintf("%s_%s", currentPanel, circuitNum),
				Name:    fmt.Sprintf("Circuit %s", circuitNum),
				Panel:   currentPanel,
				Circuit: circuitNum,
			}
			
			// Extract amperage
			if aMatch := ampPattern.FindStringSubmatch(line); aMatch != nil {
				item.Amperage, _ = strconv.Atoi(aMatch[1])
			}
			
			// Extract description (rest of line after circuit number)
			descStart := strings.Index(line, circuitNum) + len(circuitNum)
			if descStart < len(line) {
				item.Description = strings.TrimSpace(line[descStart:])
			}
			
			items = append(items, item)
		}
	}
	
	return items
}

// ElectricalItem represents an electrical component
type ElectricalItem struct {
	Type        string // panel, circuit, outlet, switch
	ID          string
	Name        string
	Panel       string
	Circuit     string
	Amperage    int
	Voltage     int
	Description string
}