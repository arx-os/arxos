package pdf

import (
	"fmt"
	"regexp"
	"strings"
	"time"
	
	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// GenericFloorPlanParser can parse any floor plan PDF
type GenericFloorPlanParser struct {
	// Patterns to look for in PDFs
	equipmentPatterns []*regexp.Regexp
	roomPatterns      []*regexp.Regexp
}

// NewGenericParser creates a parser that works with any floor plan
func NewGenericParser() *GenericFloorPlanParser {
	return &GenericFloorPlanParser{
		equipmentPatterns: []*regexp.Regexp{
			// Network equipment
			regexp.MustCompile(`(?i)(MDF|IDF|AP|WAP|SWITCH)\s*[\-_]?\s*(\w+)`),
			// Electrical
			regexp.MustCompile(`(?i)(PANEL|BREAKER|OUTLET)\s*[\-_]?\s*(\w+)`),
			// HVAC
			regexp.MustCompile(`(?i)(AHU|VAV|RTU|FCU)\s*[\-_]?\s*(\w+)`),
			// Generic equipment codes
			regexp.MustCompile(`(?i)([A-Z]{2,4})[\-_](\d{3,4}\w?)`),
		},
		roomPatterns: []*regexp.Regexp{
			// Room numbers
			regexp.MustCompile(`(?i)(ROOM|RM|SUITE|STE)\s*(\d+\w?)`),
			// Building areas
			regexp.MustCompile(`(?i)(OFFICE|CLASSROOM|LAB|CAFETERIA|GYM|LIBRARY)`),
			// Wings/Sections
			regexp.MustCompile(`(?i)(NORTH|SOUTH|EAST|WEST|CENTRAL)\s*(WING|SECTION|AREA)?`),
		},
	}
}

// ParsePDFText attempts to extract structured data from PDF text
func (p *GenericFloorPlanParser) ParsePDFText(text string, filename string) (*models.FloorPlan, error) {
	logger.Info("Attempting generic parse of: %s", filename)
	
	plan := &models.FloorPlan{
		Name:      strings.TrimSuffix(filename, ".pdf"),
		Building:  "Imported Building",
		Level:     1,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		Rooms:     []models.Room{},
		Equipment: []models.Equipment{},
	}
	
	// Split text into lines for processing
	lines := strings.Split(text, "\n")
	
	// Extract equipment
	equipmentFound := p.extractEquipment(lines, plan)
	logger.Info("Found %d equipment items", equipmentFound)
	
	// Extract rooms
	roomsFound := p.extractRooms(lines, plan)
	logger.Info("Found %d rooms/areas", roomsFound)
	
	// If we didn't find much, create a default structure
	if equipmentFound == 0 && roomsFound == 0 {
		logger.Warn("No equipment or rooms found via text extraction")
		p.createDefaultStructure(plan, filename)
	}
	
	return plan, nil
}

// extractEquipment finds equipment references in text
func (p *GenericFloorPlanParser) extractEquipment(lines []string, plan *models.FloorPlan) int {
	found := 0
	seen := make(map[string]bool)
	
	for _, line := range lines {
		for _, pattern := range p.equipmentPatterns {
			matches := pattern.FindAllStringSubmatch(line, -1)
			for _, match := range matches {
				if len(match) >= 2 {
					// Create unique ID
					equipName := strings.TrimSpace(match[0])
					equipID := strings.ToLower(strings.ReplaceAll(equipName, " ", "_"))
					
					// Skip duplicates
					if seen[equipID] {
						continue
					}
					seen[equipID] = true
					
					// Determine type from the match
					equipType := "equipment"
					equipUpper := strings.ToUpper(match[1])
					switch {
					case strings.Contains(equipUpper, "IDF"):
						equipType = "idf"
					case strings.Contains(equipUpper, "MDF"):
						equipType = "mdf"
					case strings.Contains(equipUpper, "AP") || strings.Contains(equipUpper, "WAP"):
						equipType = "access_point"
					case strings.Contains(equipUpper, "SWITCH"):
						equipType = "switch"
					case strings.Contains(equipUpper, "PANEL"):
						equipType = "panel"
					case strings.Contains(equipUpper, "OUTLET"):
						equipType = "outlet"
					}
					
					equipment := models.Equipment{
						ID:     equipID,
						Name:   equipName,
						Type:   equipType,
						Status: models.StatusNormal,
						Notes:  "Auto-detected from PDF",
						Location: models.Point{
							X: float64(10 + found*10), // Simple spacing
							Y: 10,
						},
					}
					
					plan.Equipment = append(plan.Equipment, equipment)
					found++
					
					logger.Debug("Found equipment: %s (type: %s)", equipName, equipType)
				}
			}
		}
	}
	
	return found
}

// extractRooms finds room/area references in text
func (p *GenericFloorPlanParser) extractRooms(lines []string, plan *models.FloorPlan) int {
	found := 0
	seen := make(map[string]bool)
	
	for _, line := range lines {
		for _, pattern := range p.roomPatterns {
			matches := pattern.FindAllStringSubmatch(line, -1)
			for _, match := range matches {
				if len(match) >= 1 {
					roomName := strings.TrimSpace(match[0])
					roomID := strings.ToLower(strings.ReplaceAll(roomName, " ", "_"))
					
					// Skip duplicates
					if seen[roomID] {
						continue
					}
					seen[roomID] = true
					
					room := models.Room{
						ID:   roomID,
						Name: roomName,
						Bounds: models.Bounds{
							MinX: float64(found * 20),
							MinY: 0,
							MaxX: float64((found + 1) * 20),
							MaxY: 20,
						},
						Equipment: []string{},
					}
					
					plan.Rooms = append(plan.Rooms, room)
					found++
					
					logger.Debug("Found room/area: %s", roomName)
				}
			}
		}
	}
	
	// If we found equipment but no rooms, create a default room
	if found == 0 && len(plan.Equipment) > 0 {
		defaultRoom := models.Room{
			ID:   "main_area",
			Name: "Main Area",
			Bounds: models.Bounds{
				MinX: 0, MinY: 0,
				MaxX: 100, MaxY: 50,
			},
			Equipment: []string{},
		}
		
		// Assign all equipment to this room
		for i := range plan.Equipment {
			plan.Equipment[i].RoomID = defaultRoom.ID
			defaultRoom.Equipment = append(defaultRoom.Equipment, plan.Equipment[i].ID)
		}
		
		plan.Rooms = append(plan.Rooms, defaultRoom)
		found = 1
	}
	
	return found
}

// createDefaultStructure creates a basic structure when parsing fails
func (p *GenericFloorPlanParser) createDefaultStructure(plan *models.FloorPlan, filename string) {
	logger.Info("Creating default structure for manual editing")
	
	// Create a simple room
	room := models.Room{
		ID:   "main",
		Name: "Main Floor",
		Bounds: models.Bounds{
			MinX: 0, MinY: 0,
			MaxX: 50, MaxY: 30,
		},
		Equipment: []string{"sample_equipment"},
	}
	
	// Add sample equipment
	equipment := models.Equipment{
		ID:       "sample_equipment",
		Name:     "Sample Equipment",
		Type:     "unknown",
		Location: models.Point{X: 25, Y: 15},
		RoomID:   "main",
		Status:   models.StatusUnknown,
		Notes:    fmt.Sprintf("PDF parsing failed for %s. Please update manually.", filename),
	}
	
	plan.Rooms = append(plan.Rooms, room)
	plan.Equipment = append(plan.Equipment, equipment)
	
	logger.Warn("PDF parsing unsuccessful. Created placeholder structure.")
	logger.Info("To add equipment manually, use: arx add-equipment <name> --type <type> --room <room>")
}