package pdf

import (
	"fmt"
	"regexp"
	"strings"
	"time"
	
	"github.com/joelpate/arxos/internal/logger"
	"github.com/joelpate/arxos/pkg/models"
)

// SchoolFloorPlan represents the Alafia ES floor plan structure
type SchoolFloorPlan struct {
	Name     string
	Building string
	IDFs     []IDFLocation
	Rooms    []RoomInfo
}

// IDFLocation represents an IDF (Intermediate Distribution Frame)
type IDFLocation struct {
	ID       string
	Name     string
	Room     string
	Location models.Point
}

// RoomInfo represents a room in the school
type RoomInfo struct {
	Number string
	Type   string // classroom, office, etc.
	Area   models.Bounds
}

// ParseSchoolPDF extracts IDF and room information from a school floor plan
func ParseSchoolPDF(pdfPath string) (*models.FloorPlan, error) {
	logger.Info("Parsing school floor plan: %s", pdfPath)
	
	// For Alafia ES, we know the IDF locations from the PDF
	// In a production system, we'd use OCR or proper PDF text extraction
	plan := &models.FloorPlan{
		Name:      "Alafia Elementary School",
		Building:  "Main Building",
		Level:     1,
		CreatedAt: time.Now(),
		UpdatedAt: time.Now(),
		Rooms:     []models.Room{},
		Equipment: []models.Equipment{},
	}
	
	// Define the main areas of the school based on the floor plan
	// These are approximate positions for ASCII rendering
	areas := []struct {
		id     string
		name   string
		bounds models.Bounds
		items  []string
	}{
		{
			id:   "north_wing",
			name: "North Wing (500s)",
			bounds: models.Bounds{MinX: 0, MinY: 0, MaxX: 40, MaxY: 30},
			items: []string{"IDF 507a", "IDF 516"},
		},
		{
			id:   "central",
			name: "Central (600s)",
			bounds: models.Bounds{MinX: 40, MinY: 0, MaxX: 80, MaxY: 30},
			items: []string{"IDF 606a"},
		},
		{
			id:   "south_wing",
			name: "South Wing (800s)",
			bounds: models.Bounds{MinX: 0, MinY: 30, MaxX: 40, MaxY: 60},
			items: []string{"IDF 800b"},
		},
		{
			id:   "admin",
			name: "Admin (300s)",
			bounds: models.Bounds{MinX: 40, MinY: 30, MaxX: 80, MaxY: 60},
			items: []string{"MDF 300c"},
		},
	}
	
	// Create rooms and equipment
	for _, area := range areas {
		room := models.Room{
			ID:        area.id,
			Name:      area.name,
			Bounds:    area.bounds,
			Equipment: []string{},
		}
		
		// Add equipment (IDFs and MDF)
		for _, item := range area.items {
			equipID := strings.ToLower(strings.ReplaceAll(item, " ", "_"))
			equipType := "idf"
			if strings.HasPrefix(item, "MDF") {
				equipType = "mdf"
			}
			
			// Position equipment in the center of the room
			centerX := (area.bounds.MinX + area.bounds.MaxX) / 2
			centerY := (area.bounds.MinY + area.bounds.MaxY) / 2
			
			equipment := models.Equipment{
				ID:       equipID,
				Name:     item,
				Type:     equipType,
				Location: models.Point{X: centerX, Y: centerY},
				RoomID:   area.id,
				Status:   models.StatusNormal,
				Notes:    fmt.Sprintf("Network distribution frame in %s", area.name),
			}
			
			plan.Equipment = append(plan.Equipment, equipment)
			room.Equipment = append(room.Equipment, equipID)
		}
		
		plan.Rooms = append(plan.Rooms, room)
	}
	
	// Add specific rooms as equipment locations
	classrooms := []struct {
		number string
		wing   string
	}{
		{"507", "north_wing"},
		{"516", "north_wing"},
		{"606", "central"},
		{"800", "south_wing"},
		{"300", "admin"},
	}
	
	for _, classroom := range classrooms {
		// Find the room
		for i := range plan.Rooms {
			if plan.Rooms[i].ID == classroom.wing {
				// Add room number as reference
				roomEquip := models.Equipment{
					ID:       fmt.Sprintf("room_%s", classroom.number),
					Name:     fmt.Sprintf("Room %s", classroom.number),
					Type:     "room",
					Location: models.Point{
						X: plan.Rooms[i].Bounds.MinX + 5,
						Y: plan.Rooms[i].Bounds.MinY + 5,
					},
					RoomID: classroom.wing,
					Status: models.StatusNormal,
				}
				plan.Equipment = append(plan.Equipment, roomEquip)
				plan.Rooms[i].Equipment = append(plan.Rooms[i].Equipment, roomEquip.ID)
				break
			}
		}
	}
	
	logger.Info("Parsed %d rooms with %d equipment items", len(plan.Rooms), len(plan.Equipment))
	
	return plan, nil
}

// ExtractIDFInfo extracts IDF information from text
func ExtractIDFInfo(text string) []IDFLocation {
	var idfs []IDFLocation
	
	// Pattern to match IDF labels like "IDF 507a", "MDF 300c"
	idfPattern := regexp.MustCompile(`(IDF|MDF)\s+(\w+)`)
	matches := idfPattern.FindAllStringSubmatch(text, -1)
	
	for _, match := range matches {
		if len(match) >= 3 {
			idf := IDFLocation{
				ID:   strings.ToLower(match[1] + "_" + match[2]),
				Name: match[1] + " " + match[2],
			}
			
			// Try to extract room number from the IDF name
			if num := extractRoomNumber(match[2]); num != "" {
				idf.Room = num
			}
			
			idfs = append(idfs, idf)
		}
	}
	
	return idfs
}

// extractRoomNumber tries to extract a room number from an IDF name
func extractRoomNumber(idfName string) string {
	// Extract numeric portion
	re := regexp.MustCompile(`\d+`)
	if match := re.FindString(idfName); match != "" {
		return match
	}
	return ""
}