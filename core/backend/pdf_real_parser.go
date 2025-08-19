package main

import (
	"bytes"
	"encoding/json"
	"encoding/xml"
	"fmt"
	"image/png"
	"log"
	"os"
	"os/exec"
	"strings"
)

// RealPDFParser parses actual PDF floor plans
type RealPDFParser struct {
	pdfPath  string
	tempDir  string
	scale    float64 // pixels to mm conversion
	pdfWidth float64
	pdfHeight float64
}

// PDFText represents text extracted from PDF
type PDFText struct {
	Text   string
	X      float64
	Y      float64
	Width  float64
	Height float64
}

// PDFXMLPage represents the XML structure from pdftohtml
type PDFXMLPage struct {
	XMLName xml.Name     `xml:"page"`
	Number  int          `xml:"number,attr"`
	Width   int          `xml:"width,attr"`
	Height  int          `xml:"height,attr"`
	Texts   []PDFXMLText `xml:"text"`
}

// PDFXMLText represents text elements in the XML
type PDFXMLText struct {
	Top    int    `xml:"top,attr"`
	Left   int    `xml:"left,attr"`
	Width  int    `xml:"width,attr"`
	Height int    `xml:"height,attr"`
	Text   string `xml:",chardata"`
}

// NewRealPDFParser creates a parser that actually extracts from PDFs
func NewRealPDFParser(pdfPath string) *RealPDFParser {
	return &RealPDFParser{
		pdfPath: pdfPath,
		tempDir: "/tmp",
		scale:   100, // Default scale: 1 pixel = 100mm
	}
}

// ParseActualPDF extracts real architectural elements from the PDF
func (p *RealPDFParser) ParseActualPDF(buildingName, floorNumber string) ([]ArxObject, map[string]int, error) {
	log.Printf("Starting REAL PDF parsing of: %s", p.pdfPath)
	
	// Step 1: Convert PDF to image for line detection
	imgPath := fmt.Sprintf("%s/pdf_page.png", p.tempDir)
	cmd := exec.Command("pdftoppm", "-png", "-singlefile", "-r", "150", p.pdfPath, strings.TrimSuffix(imgPath, ".png"))
	if err := cmd.Run(); err != nil {
		return nil, nil, fmt.Errorf("failed to convert PDF to image: %w", err)
	}
	
	// Step 2: Extract text with positions using pdftohtml
	xmlPath := fmt.Sprintf("%s/pdf_text.xml", p.tempDir)
	cmd = exec.Command("pdftohtml", "-xml", "-i", p.pdfPath, xmlPath)
	cmd.Run() // Ignore errors as it may still produce useful output
	
	// Parse the XML to get text positions
	texts := p.extractTextFromXML(xmlPath)
	log.Printf("Extracted %d text labels from PDF", len(texts))
	
	// Step 3: Detect lines and rectangles from the image
	lines, rectangles := p.detectGeometry(imgPath)
	log.Printf("Detected %d lines and %d rectangles", len(lines), len(rectangles))
	
	// Step 4: Convert detected geometry to ArxObjects
	objects := p.convertToArxObjects(lines, rectangles, texts, buildingName, floorNumber)
	
	// Calculate statistics
	stats := make(map[string]int)
	for _, obj := range objects {
		stats[obj.Type]++
	}
	
	log.Printf("REAL PDF parsing complete: %d objects extracted", len(objects))
	return objects, stats, nil
}

// extractTextFromXML parses the pdftohtml XML output
func (p *RealPDFParser) extractTextFromXML(xmlPath string) []PDFText {
	var texts []PDFText
	
	data, err := os.ReadFile(xmlPath + "s.xml") // pdftohtml adds 's' to filename
	if err != nil {
		log.Printf("Could not read XML: %v", err)
		return texts
	}
	
	// Parse XML
	var page PDFXMLPage
	decoder := xml.NewDecoder(bytes.NewReader(data))
	
	for {
		token, err := decoder.Token()
		if err != nil {
			break
		}
		
		switch se := token.(type) {
		case xml.StartElement:
			if se.Name.Local == "page" {
				decoder.DecodeElement(&page, &se)
				p.pdfWidth = float64(page.Width)
				p.pdfHeight = float64(page.Height)
			} else if se.Name.Local == "text" {
				var text PDFXMLText
				decoder.DecodeElement(&text, &se)
				
				// Clean and filter text
				cleanText := strings.TrimSpace(text.Text)
				if cleanText != "" && len(cleanText) > 1 {
					texts = append(texts, PDFText{
						Text:   cleanText,
						X:      float64(text.Left),
						Y:      float64(text.Top),
						Width:  float64(text.Width),
						Height: float64(text.Height),
					})
				}
			}
		}
	}
	
	return texts
}

// Line represents a detected line in the floor plan
type Line struct {
	X1, Y1, X2, Y2 float64
	Thickness      float64
}

// Rectangle represents a detected rectangle
type Rectangle struct {
	X, Y, Width, Height float64
}

// detectGeometry detects lines and rectangles from the floor plan image
func (p *RealPDFParser) detectGeometry(imgPath string) ([]Line, []Rectangle) {
	var lines []Line
	var rectangles []Rectangle
	
	// Open the image
	file, err := os.Open(imgPath)
	if err != nil {
		log.Printf("Could not open image: %v", err)
		return lines, rectangles
	}
	defer file.Close()
	
	img, err := png.Decode(file)
	if err != nil {
		log.Printf("Could not decode image: %v", err)
		return lines, rectangles
	}
	
	bounds := img.Bounds()
	width := bounds.Max.X - bounds.Min.X
	height := bounds.Max.Y - bounds.Min.Y
	
	// Simple line detection: look for horizontal and vertical black lines
	// This is a simplified version - in production you'd use OpenCV or similar
	
	// Detect horizontal lines
	for y := 0; y < height; y += 5 { // Sample every 5 pixels
		lineStart := -1
		for x := 0; x < width; x++ {
			r, g, b, _ := img.At(x, y).RGBA()
			isBlack := r < 10000 && g < 10000 && b < 10000
			
			if isBlack && lineStart == -1 {
				lineStart = x
			} else if !isBlack && lineStart != -1 && (x-lineStart) > 20 {
				// Found a horizontal line
				lines = append(lines, Line{
					X1:        float64(lineStart),
					Y1:        float64(y),
					X2:        float64(x),
					Y2:        float64(y),
					Thickness: 2,
				})
				lineStart = -1
			}
		}
	}
	
	// Detect vertical lines
	for x := 0; x < width; x += 5 { // Sample every 5 pixels
		lineStart := -1
		for y := 0; y < height; y++ {
			r, g, b, _ := img.At(x, y).RGBA()
			isBlack := r < 10000 && g < 10000 && b < 10000
			
			if isBlack && lineStart == -1 {
				lineStart = y
			} else if !isBlack && lineStart != -1 && (y-lineStart) > 20 {
				// Found a vertical line
				lines = append(lines, Line{
					X1:        float64(x),
					Y1:        float64(lineStart),
					X2:        float64(x),
					Y2:        float64(y),
					Thickness: 2,
				})
				lineStart = -1
			}
		}
	}
	
	// Detect rectangles from intersecting lines
	// For now, use text positions to approximate room boundaries
	// In production, you'd use proper computer vision algorithms
	
	return lines, rectangles
}

// convertToArxObjects converts detected geometry to ArxObjects
func (p *RealPDFParser) convertToArxObjects(lines []Line, rectangles []Rectangle, texts []PDFText, buildingName, floorNumber string) []ArxObject {
	var objects []ArxObject
	floorZ := parseFloat(floorNumber) * 3000
	
	// Process text labels to identify rooms
	roomTexts := make(map[string]PDFText)
	for _, text := range texts {
		// Check if it's a room number (3 digits or with IDF/MDF prefix)
		if isRoomNumber(text.Text) {
			roomTexts[text.Text] = text
		}
	}
	
	// Convert coordinate scale (PDF coords to mm)
	// Assuming the building is approximately 150m x 100m
	scaleX := 150000.0 / p.pdfWidth  // 150m in mm
	scaleY := 100000.0 / p.pdfHeight // 100m in mm
	
	// Create walls from detected lines
	for _, line := range lines {
		// Convert to world coordinates
		x1 := line.X1 * scaleX
		y1 := line.Y1 * scaleY
		x2 := line.X2 * scaleX
		y2 := line.Y2 * scaleY
		
		// Determine if horizontal or vertical
		if abs(y2-y1) < abs(x2-x1) {
			// Horizontal wall
			objects = append(objects, ArxObject{
				Type:     "wall",
				System:   "structural",
				X:        minFloat(x1, x2),
				Y:        y1,
				Z:        floorZ,
				Width:    int(abs(x2 - x1)),
				Height:   int(line.Thickness * 100), // Wall thickness
				ScaleMin: 4,
				ScaleMax: 9,
				Properties: json.RawMessage(fmt.Sprintf(`{"building":"%s","floor":"%s","detected":true}`,
					buildingName, floorNumber)),
			})
		} else {
			// Vertical wall
			objects = append(objects, ArxObject{
				Type:     "wall",
				System:   "structural",
				X:        x1,
				Y:        minFloat(y1, y2),
				Z:        floorZ,
				Width:    int(line.Thickness * 100), // Wall thickness
				Height:   int(abs(y2 - y1)),
				ScaleMin: 4,
				ScaleMax: 9,
				Properties: json.RawMessage(fmt.Sprintf(`{"building":"%s","floor":"%s","detected":true}`,
					buildingName, floorNumber)),
			})
		}
	}
	
	// Create rooms from text positions
	// Group nearby texts to identify room areas
	for roomNum, text := range roomTexts {
		// Convert text position to world coordinates
		x := text.X * scaleX
		y := text.Y * scaleY
		
		// Estimate room size (this would be improved with actual room boundary detection)
		roomWidth := 12000.0  // 12m default
		roomHeight := 10000.0 // 10m default
		
		// Special handling for specific room types
		roomType := "classroom"
		if strings.Contains(roomNum, "IDF") || strings.Contains(roomNum, "MDF") {
			roomType = "network_room"
			roomWidth = 8000.0
			roomHeight = 6000.0
		} else if strings.HasPrefix(roomNum, "3") || strings.HasPrefix(roomNum, "7") {
			roomType = "office"
			roomWidth = 8000.0
			roomHeight = 8000.0
		}
		
		// Create room object
		objects = append(objects, ArxObject{
			Type:     "room",
			System:   "architectural",
			X:        x - roomWidth/2,  // Center the room on the label
			Y:        y - roomHeight/2,
			Z:        floorZ,
			Width:    int(roomWidth),
			Height:   int(roomHeight),
			ScaleMin: 4,
			ScaleMax: 9,
			Properties: json.RawMessage(fmt.Sprintf(`{"room_number":"%s","type":"%s","building":"%s","floor":"%s","from_pdf":true}`,
				roomNum, roomType, buildingName, floorNumber)),
		})
		
		// Add a door for each room
		objects = append(objects, ArxObject{
			Type:     "door",
			System:   "architectural",
			X:        x - 450,
			Y:        y + roomHeight/2 - 100,
			Z:        floorZ,
			Width:    900,
			Height:   200,
			ScaleMin: 6,
			ScaleMax: 9,
			Properties: json.RawMessage(fmt.Sprintf(`{"room":"%s","type":"single"}`, roomNum)),
		})
		
		// Add network equipment for IDF/MDF rooms
		if strings.Contains(roomNum, "IDF") || strings.Contains(roomNum, "MDF") {
			objects = append(objects, ArxObject{
				Type:     "equipment",
				System:   "data",
				X:        x - roomWidth/2 + 1000,
				Y:        y - roomHeight/2 + 1000,
				Z:        floorZ,
				Width:    600,
				Height:   800,
				ScaleMin: 7,
				ScaleMax: 9,
				Properties: json.RawMessage(fmt.Sprintf(`{"type":"network_rack","label":"%s","from_pdf":true}`, roomNum)),
			})
		}
	}
	
	return objects
}

// Helper functions
func isRoomNumber(text string) bool {
	// Check for room number patterns
	if strings.Contains(text, "IDF") || strings.Contains(text, "MDF") {
		return true
	}
	// Check if it's a 3-digit number possibly with a letter suffix
	if len(text) >= 3 && len(text) <= 4 {
		for i, r := range text {
			if i < 3 && (r < '0' || r > '9') {
				return false
			}
		}
		return true
	}
	return false
}

func abs(x float64) float64 {
	if x < 0 {
		return -x
	}
	return x
}

func minFloat(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}