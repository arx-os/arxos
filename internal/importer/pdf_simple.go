package importer

import (
	"bufio"
	"fmt"
	"io"
	"regexp"
	"strings"

	"github.com/joelpate/arxos/internal/common/logger"
)

// ExtractedData holds data extracted from a PDF
type ExtractedData struct {
	Text      string
	Equipment []ExtractedEquipment
	Rooms     []ExtractedRoom
	Metadata  map[string]string
}

// ExtractedEquipment represents equipment found in the PDF
type ExtractedEquipment struct {
	ID       string
	Type     string
	Text     string
	Page     int
	Position Position
}

// ExtractedRoom represents a room found in the PDF
type ExtractedRoom struct {
	ID       string
	Name     string
	Page     int
	Position Position
}

// Position represents location in the PDF
type Position struct {
	X, Y float64
}

// SimplePDFExtractor provides basic PDF text extraction
// For full functionality, a proper PDF library would be integrated
type SimplePDFExtractor struct {
	equipmentPatterns map[string]*regexp.Regexp
	roomPattern       *regexp.Regexp
}

// NewSimplePDFExtractor creates a simple PDF extractor
func NewSimplePDFExtractor() *SimplePDFExtractor {
	return &SimplePDFExtractor{
		equipmentPatterns: map[string]*regexp.Regexp{
			"Network.IDF":        regexp.MustCompile(`(?i)IDF[- ]?(\d+[A-Z]?|\d+\.\d+)`),
			"Network.MDF":        regexp.MustCompile(`(?i)MDF[- ]?(\d+[A-Z]?)`),
			"Network.Switch":     regexp.MustCompile(`(?i)SW[- ]?(\d+[A-Z]?)`),
			"Network.AccessPoint": regexp.MustCompile(`(?i)WAP[- ]?(\d+)|AP[- ]?(\d+)`),
			"Electrical.Panel":   regexp.MustCompile(`(?i)PANEL[- ]?([A-Z\d]+)`),
			"Electrical.Outlet":  regexp.MustCompile(`(?i)OUTLET[- ]?(\d+)`),
			"HVAC.Unit":         regexp.MustCompile(`(?i)RTU[- ]?(\d+)|AHU[- ]?(\d+)`),
			"HVAC.Thermostat":   regexp.MustCompile(`(?i)TSTAT[- ]?(\d+)|THERM[- ]?(\d+)`),
		},
		roomPattern: regexp.MustCompile(`(?i)(?:ROOM|RM|SUITE|STE)[- ]?(\d+[A-Z]?|\d+\.\d+)`),
	}
}

// ExtractText performs basic text extraction from a reader
func (e *SimplePDFExtractor) ExtractText(reader io.Reader) (*ExtractedData, error) {
	logger.Debug("Starting simple text extraction")

	data := &ExtractedData{
		Equipment: make([]ExtractedEquipment, 0),
		Rooms:     make([]ExtractedRoom, 0),
		Metadata:  make(map[string]string),
	}

	scanner := bufio.NewScanner(reader)
	allText := strings.Builder{}
	lineNum := 0
	page := 1

	for scanner.Scan() {
		line := scanner.Text()
		lineNum++

		// Simple page detection (every 50 lines is a new page approximation)
		if lineNum%50 == 0 {
			page++
		}

		allText.WriteString(line)
		allText.WriteString("\n")

		// Find equipment in line
		e.findEquipmentInLine(line, page, lineNum, data)

		// Find rooms in line
		e.findRoomsInLine(line, page, lineNum, data)
	}

	if err := scanner.Err(); err != nil {
		return nil, fmt.Errorf("error reading input: %w", err)
	}

	data.Text = allText.String()

	logger.Info("Extracted %d equipment items and %d rooms",
		len(data.Equipment), len(data.Rooms))

	return data, nil
}

func (e *SimplePDFExtractor) findEquipmentInLine(line string, page, lineNum int, data *ExtractedData) {
	for eqType, pattern := range e.equipmentPatterns {
		matches := pattern.FindAllStringSubmatch(line, -1)
		for _, match := range matches {
			id := match[0]
			if len(match) > 1 && match[1] != "" {
				id = match[1]
			}

			id = strings.TrimSpace(id)
			id = strings.ReplaceAll(id, " ", "_")
			id = strings.ToUpper(id)

			fullID := fmt.Sprintf("%s_%s",
				strings.ReplaceAll(eqType, ".", "_"), id)

			// Check for duplicates
			found := false
			for _, existing := range data.Equipment {
				if existing.ID == fullID {
					found = true
					break
				}
			}

			if !found {
				eq := ExtractedEquipment{
					ID:   fullID,
					Type: eqType,
					Text: strings.TrimSpace(line),
					Page: page,
					Position: Position{
						X: float64((lineNum % 50) * 20), // Approximate position
						Y: float64(lineNum * 10),
					},
				}
				data.Equipment = append(data.Equipment, eq)
				logger.Debug("Found equipment: %s (%s) on page %d", eq.ID, eq.Type, page)
			}
		}
	}
}

func (e *SimplePDFExtractor) findRoomsInLine(line string, page, lineNum int, data *ExtractedData) {
	matches := e.roomPattern.FindAllStringSubmatch(line, -1)

	for _, match := range matches {
		roomID := match[0]
		if len(match) > 1 && match[1] != "" {
			roomID = match[1]
		}

		roomID = strings.TrimSpace(roomID)
		roomID = strings.ReplaceAll(roomID, " ", "_")
		roomID = strings.ToUpper(roomID)

		fullID := fmt.Sprintf("ROOM_%s", roomID)

		// Check for duplicates
		found := false
		for _, existing := range data.Rooms {
			if existing.ID == fullID {
				found = true
				break
			}
		}

		if !found {
			room := ExtractedRoom{
				ID:   fullID,
				Name: fmt.Sprintf("Room %s", roomID),
				Page: page,
				Position: Position{
					X: float64((lineNum % 50) * 20),
					Y: float64(lineNum * 10),
				},
			}
			data.Rooms = append(data.Rooms, room)
			logger.Debug("Found room: %s on page %d", room.ID, page)
		}
	}
}