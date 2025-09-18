package converter

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"

	"github.com/pdfcpu/pdfcpu/pkg/api"
	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/common/progress"
)

// RealPDFConverter handles actual PDF files with text extraction
type RealPDFConverter struct{}

func NewRealPDFConverter() *RealPDFConverter {
	return &RealPDFConverter{}
}

func (c *RealPDFConverter) GetFormat() string {
	return "pdf"
}

func (c *RealPDFConverter) GetDescription() string {
	return "PDF floor plans with text extraction"
}

func (c *RealPDFConverter) CanConvert(filename string) bool {
	lower := strings.ToLower(filename)
	return strings.HasSuffix(lower, ".pdf")
}

func (c *RealPDFConverter) ConvertToBIM(input io.Reader, output io.Writer) error {
	// Initialize progress tracker
	progress := progress.New(5, "PDF Conversion")
	defer func() {
		progress.Finish()
	}()

	building := &Building{
		Metadata: Metadata{
			Source: "PDF Import",
			Format: "PDF",
			Properties: map[string]string{
				"extraction_method": "text extraction",
			},
		},
	}

	progress.Step("Initializing PDF conversion")

	// Read input data
	buf := new(bytes.Buffer)
	_, err := buf.ReadFrom(input)
	if err != nil {
		progress.Error(err)
		return fmt.Errorf("failed to read input: %w", err)
	}
	data := buf.Bytes()

	if len(data) == 0 {
		err := fmt.Errorf("input file is empty")
		progress.Error(err)
		return err
	}

	progress.Step("Reading PDF file")

	// Verify it's a PDF
	if len(data) < 5 || string(data[:4]) != "%PDF" {
		err := fmt.Errorf("not a valid PDF file\n\nThe file does not contain a valid PDF header.\n\nPlease check:\n  • The file is actually a PDF (not renamed with .pdf extension)\n  • The file is not corrupted\n  • You have the correct file path")
		progress.Error(err)
		return err
	}

	// Write to temp file for processing
	tempFile := filepath.Join(os.TempDir(), fmt.Sprintf("arxos_pdf_%d.pdf", os.Getpid()))
	err = os.WriteFile(tempFile, data, 0644)
	if err != nil {
		return fmt.Errorf("failed to write temp PDF: %w", err)
	}
	defer func() {
		if removeErr := os.Remove(tempFile); removeErr != nil {
			logger.Warn("Failed to remove temp file %s: %v", tempFile, removeErr)
		}
	}()

	progress.Step("Extracting text from PDF")

	// Extract text from PDF with multiple fallback methods
	extractedText, extractionMethod, err := c.extractPDFTextWithFallbacks(tempFile)
	if err != nil {
		progress.Error(err)
		return fmt.Errorf("failed to extract PDF text: %w", err)
	}

	building.Metadata.Properties["extraction_method"] = extractionMethod

	if strings.TrimSpace(extractedText) == "" {
		err := fmt.Errorf("no text content found in PDF\n\nThis usually means:\n  • The PDF contains only scanned images (not searchable text)\n  • The PDF is encrypted or password-protected\n  • The PDF format is not supported by text extraction\n\nTry:\n  • Using a PDF with searchable text\n  • Converting scanned PDFs to text using OCR first\n  • Checking if the PDF is password-protected")
		progress.Error(err)
		return err
	}

	progress.Step("Parsing rooms and equipment")

	// Parse the extracted text
	rooms := c.extractRooms(extractedText)
	equipment := c.extractEquipment(extractedText)

	// Build floor structure
	floor := Floor{
		ID:    "1",
		Name:  "Extracted Floor",
		Rooms: make([]Room, 0),
	}

	// Create rooms
	for _, roomData := range rooms {
		room := Room{
			Number: roomData["number"],
			Name:   roomData["name"],
			Type:   c.inferRoomType(roomData["name"]),
		}

		// Parse area if available
		if areaStr, ok := roomData["area"]; ok {
			if area, err := strconv.ParseFloat(areaStr, 64); err == nil {
				room.Area = area
			}
		}

		// Add equipment to rooms
		for _, eq := range equipment {
			if eq["room"] == room.Number {
				room.Equipment = append(room.Equipment, Equipment{
					Tag:    eq["tag"],
					Name:   eq["name"],
					Type:   eq["type"],
					Status: "operational",
				})
			}
		}

		floor.Rooms = append(floor.Rooms, room)
	}

	building.Floors = append(building.Floors, floor)

	progress.Step("Building data structure")

	// Validate building data before output
	if issues := building.Validate(); len(issues) > 0 {
		logger.Warn("Data quality issues found (%d issues):", len(issues))
		for _, issue := range issues {
			logger.Warn("  - %s", issue)
		}
	}

	// Convert to BIM
	bimText := building.ToBIM()
	_, err = output.Write([]byte(bimText))
	return err
}

func (c *RealPDFConverter) ConvertFromBIM(input io.Reader, output io.Writer) error {
	return fmt.Errorf("PDF generation not implemented")
}

func (c *RealPDFConverter) ConvertToDB(input io.Reader, db interface{}) error {
	// PDF files typically don't have precise spatial data
	// This would require OCR and floor plan recognition for spatial extraction
	return fmt.Errorf("direct PDF to database import not implemented - use ConvertToBIM first")
}

func (c *RealPDFConverter) extractPDFTextWithFallbacks(pdfPath string) (string, string, error) {
	var lastErr error

	// Method 1: Try pdftotext (most reliable for text-based PDFs)
	text, err := c.tryPdfToText(pdfPath)
	if err == nil && strings.TrimSpace(text) != "" {
		return text, "pdftotext", nil
	}
	lastErr = err

	// Method 2: Try pdfcpu extraction
	text, err = c.tryPdfcpuExtraction(pdfPath)
	if err == nil && strings.TrimSpace(text) != "" {
		return text, "pdfcpu", nil
	}
	if lastErr == nil {
		lastErr = err
	}

	// Method 3: Try other PDF libraries or techniques
	// For now, just return the last error
	return "", "none", fmt.Errorf("all text extraction methods failed, last error: %w", lastErr)
}

func (c *RealPDFConverter) tryPdfToText(pdfPath string) (string, error) {
	cmd := exec.Command("pdftotext", pdfPath, "-")
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("pdftotext failed: %w", err)
	}

	text := string(output)
	if strings.TrimSpace(text) == "" {
		return "", fmt.Errorf("pdftotext returned empty text")
	}

	return text, nil
}

func (c *RealPDFConverter) tryPdfcpuExtraction(pdfPath string) (string, error) {
	// Create temp directory for pdfcpu extraction
	tempDir := filepath.Join(os.TempDir(), fmt.Sprintf("arxos_pdfcpu_%d", os.Getpid()))
	err := os.MkdirAll(tempDir, 0755)
	if err != nil {
		return "", fmt.Errorf("failed to create temp dir: %w", err)
	}
	defer os.RemoveAll(tempDir)

	// Extract content to temp directory
	err = api.ExtractContentFile(pdfPath, tempDir, nil, nil)
	if err != nil {
		return "", fmt.Errorf("pdfcpu extraction failed: %w", err)
	}

	// Read extracted text files
	var result strings.Builder
	files, err := os.ReadDir(tempDir)
	if err != nil {
		return "", fmt.Errorf("failed to read extraction dir: %w", err)
	}

	for _, file := range files {
		if strings.HasSuffix(file.Name(), ".txt") {
			content, err := os.ReadFile(filepath.Join(tempDir, file.Name()))
			if err == nil && len(content) > 0 {
				result.Write(content)
				result.WriteString("\n\n")
			}
		}
	}

	text := result.String()
	if strings.TrimSpace(text) == "" {
		return "", fmt.Errorf("pdfcpu extracted no text")
	}

	return text, nil
}

func (c *RealPDFConverter) extractRooms(text string) []map[string]string {
	rooms := []map[string]string{}
	lines := strings.Split(text, "\n")

	for _, line := range lines {
		// Skip empty lines
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// Clean up PDF artifacts more thoroughly
		line = strings.ReplaceAll(line, " Tj", "")
		line = strings.ReplaceAll(line, ")", "")
		line = strings.ReplaceAll(line, "(", "")
		line = regexp.MustCompile(`\s+`).ReplaceAllString(line, " ")
		line = strings.TrimSpace(line)


		// Look for room patterns (multiple formats)
		patterns := []*regexp.Regexp{
			// ROOM 101 - Name - Area (standard format) - with specific area detection
			regexp.MustCompile(`(?i)ROOM\s+(\d+[A-Za-z]*)\s*[-–]\s*(.+?)(?:\s*[-–]\s*(\d+(?:\.\d+)?\s*(?:sq\s*ft|sqft|SF|m2|m²)))?$`),

			// IDF 101, MDF 803b (telecoms) - improved to capture full name
			regexp.MustCompile(`(?i)(IDF|MDF|TDF|BDF|FDF)\s+(\d+[A-Za-z]*)\s*[-:]?\s*(.*)$`),

			// Space/Area: 101 Name Area (tabular format)
			regexp.MustCompile(`(?i)(?:space|area|room)?\s*:?\s*(\d{3,4}[A-Za-z]*)\s+([A-Z][^0-9\n]+?)\s+(\d+(?:\.\d+)?\s*(?:sq\s*ft|sqft|SF|m2|m²))`),

			// R101: Name or Room 101: Name
			regexp.MustCompile(`(?i)(?:room\s*|r\s*)(\d{3,4}[A-Za-z]*)\s*:\s*([^\n]+)`),

			// 101. Name (numbered list)
			regexp.MustCompile(`^\s*(\d{3,4}[A-Za-z]*)\.\s+([A-Z][^\n]+)`),

			// Building/Office naming: SUITE 201 - Name - Area - with specific area detection
			regexp.MustCompile(`(?i)(suite|office|building|unit)\s+([A-Z]?\d+[A-Za-z]*)\s*[-:]?\s*(.+?)(?:\s*[-–]\s*(\d+(?:\.\d+)?\s*(?:sq\s*ft|sqft|SF|m2|m²)))?$`),
		}

		for i, pattern := range patterns {
			if match := pattern.FindStringSubmatch(line); match != nil {
				var roomData map[string]string

				switch i {
				case 1: // IDF/MDF pattern - now captures description
					name := fmt.Sprintf("%s %s", match[1], match[2])
					if len(match) > 3 && strings.TrimSpace(match[3]) != "" {
						name = fmt.Sprintf("%s %s - %s", match[1], match[2], strings.TrimSpace(match[3]))
					}
					roomData = map[string]string{
						"number": match[2],
						"name":   name,
						"type":   "telecom",
					}

				case 5: // Building/Office pattern (suite, office, building, unit)
					name := fmt.Sprintf("%s %s", match[1], match[2])
					if len(match) > 3 && strings.TrimSpace(match[3]) != "" {
						name = fmt.Sprintf("%s %s - %s", match[1], match[2], strings.TrimSpace(match[3]))
					}
					roomData = map[string]string{
						"number": match[2],
						"name":   name,
						"type":   strings.ToLower(match[1]),
					}
					// Extract area from match[4] for this pattern
					if len(match) > 4 && match[4] != "" {
						areaStr := regexp.MustCompile(`\d+(?:\.\d+)?`).FindString(match[4])
						if areaStr != "" {
							roomData["area"] = areaStr
						}
					}

				default: // Standard patterns
					name := ""
					number := ""

					if len(match) > 2 && match[2] != "" {
						name = strings.TrimSpace(match[2])
						number = match[1]
					} else if len(match) > 1 {
						// Fallback if only one capture group
						name = strings.TrimSpace(match[1])
						number = match[1]
					}

					roomData = map[string]string{
						"number": number,
						"name":   name,
					}

					// Extract area if present (usually in match[3])
					if len(match) > 3 && match[3] != "" {
						areaStr := regexp.MustCompile(`\d+(?:\.\d+)?`).FindString(match[3])
						if areaStr != "" {
							roomData["area"] = areaStr
						}
					}
				}

				// Only add if we have meaningful data
				if roomData["number"] != "" || roomData["name"] != "" {
					rooms = append(rooms, roomData)
				}
				break
			}
		}
	}

	return rooms
}

func (c *RealPDFConverter) extractEquipment(text string) []map[string]string {
	equipment := []map[string]string{}
	lines := strings.Split(text, "\n")
	currentRoom := ""

	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}

		// Track room context
		if strings.Contains(strings.ToUpper(line), "LOCATION") {
			if match := regexp.MustCompile(`(?i)ROOM\s+(\d+[A-Z]?)`).FindStringSubmatch(line); match != nil {
				currentRoom = match[1]
			}
		}

		// Look for equipment patterns
		patterns := []*regexp.Regexp{
			// TAG-01: Description
			regexp.MustCompile(`([A-Z]{2,}[-]?\d+[A-Z]?)\s*:\s*(.+?)(?:\s*\((.+?)\))?$`),
			// Equipment type patterns
			regexp.MustCompile(`(?i)(AHU|VAV|FCU|RTU|HVAC|UPS|PDU|PANEL|EP)[-\s]?(\d+[A-Z]?)\s*[-:]?\s*(.+)`),
		}

		for _, pattern := range patterns {
			if match := pattern.FindStringSubmatch(line); match != nil {
				var tag, name string
				if len(match[1]) > 5 { // First pattern
					tag = match[1]
					name = strings.TrimSpace(match[2])
				} else { // Second pattern
					tag = match[1] + "-" + match[2]
					name = strings.TrimSpace(match[3])
				}

				eq := map[string]string{
					"tag":  tag,
					"name": name,
					"type": c.inferEquipmentType(tag),
					"room": currentRoom,
				}
				equipment = append(equipment, eq)
				break
			}
		}
	}

	return equipment
}

func (c *RealPDFConverter) inferRoomType(name string) string {
	nameLower := strings.ToLower(name)
	switch {
	case strings.Contains(nameLower, "idf") || strings.Contains(nameLower, "mdf") || strings.Contains(nameLower, "tdf"):
		return "telecom"
	case strings.Contains(nameLower, "lobby"):
		return "lobby"
	case strings.Contains(nameLower, "conference"):
		return "conference"
	case strings.Contains(nameLower, "office"):
		return "office"
	case strings.Contains(nameLower, "server"):
		return "datacenter"
	case strings.Contains(nameLower, "storage"):
		return "storage"
	case strings.Contains(nameLower, "mechanical"):
		return "mechanical"
	case strings.Contains(nameLower, "electrical"):
		return "electrical"
	case strings.Contains(nameLower, "restroom") || strings.Contains(nameLower, "bathroom"):
		return "restroom"
	default:
		return "room"
	}
}

func (c *RealPDFConverter) inferEquipmentType(tag string) string {
	tagUpper := strings.ToUpper(tag)
	switch {
	case strings.Contains(tagUpper, "AHU") || strings.Contains(tagUpper, "VAV") ||
		strings.Contains(tagUpper, "FCU") || strings.Contains(tagUpper, "RTU") ||
		strings.Contains(tagUpper, "HVAC"):
		return "hvac"
	case strings.Contains(tagUpper, "PANEL") || strings.Contains(tagUpper, "EP") ||
		strings.Contains(tagUpper, "PDU") || strings.Contains(tagUpper, "UPS"):
		return "electrical"
	case strings.Contains(tagUpper, "PUMP") || strings.Contains(tagUpper, "VALVE"):
		return "plumbing"
	case strings.Contains(tagUpper, "FIRE") || strings.Contains(tagUpper, "SMOKE"):
		return "fire_safety"
	default:
		return "equipment"
	}
}