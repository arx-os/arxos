// Package building provides building layout construction and analysis
package building

import (
	"fmt"
	"math"
	"regexp"
	"strings"

	"github.com/arxos/arxos/internal/types"
)

// Builder implements the CampusBuilder interface
type Builder struct {
	config *types.ParseConfig
}

// NewBuilder creates a new campus builder
func NewBuilder() *Builder {
	return &Builder{
		config: types.DefaultParseConfig(),
	}
}

// NewBuilderWithConfig creates a new campus builder with custom configuration
func NewBuilderWithConfig(config *types.ParseConfig) *Builder {
	return &Builder{
		config: config,
	}
}

// ExtractCampus constructs a campus layout from parsed data
func (b *Builder) ExtractCampus(doc *types.Document, processedImages []*types.ProcessedImage) (*types.Campus, error) {
	campus := &types.Campus{
		Name:      "Extracted Campus",
		Buildings: []types.Building{},
		IDFRooms:  []types.IDFLocation{},
		Method:    "hybrid",
	}

	// Extract rooms from text
	rooms, err := b.DetectRooms(nil, doc.Text)
	if err != nil {
		return nil, fmt.Errorf("failed to detect rooms: %w", err)
	}

	// Extract rooms from image features
	for _, processedImg := range processedImages {
		imageRooms := b.extractRoomsFromImage(processedImg)
		rooms = append(rooms, imageRooms...)
	}

	// Detect IDF locations
	idfLocations, err := b.DetectIDFLocations(doc.Text, rooms)
	if err != nil {
		return nil, fmt.Errorf("failed to detect IDF locations: %w", err)
	}

	// Calculate campus bounds
	bounds := b.calculateCampusBounds(rooms, idfLocations)

	// Group rooms into buildings (simplified - single building for now)
	building := types.Building{
		Name:      "Main Building",
		Rooms:     rooms,
		Bounds:    bounds,
		Hallways:  []types.Hallway{},
		Entrances: []types.Point{},
	}

	campus.Buildings = []types.Building{building}
	campus.IDFRooms = idfLocations
	campus.Bounds = bounds
	campus.Scale = b.config.RenderScale

	return campus, nil
}

// DetectRooms identifies rooms from text and line data
func (b *Builder) DetectRooms(lines []types.Line, text string) ([]types.Room, error) {
	rooms := []types.Room{}
	roomNumbers := b.extractRoomNumbers(text)

	// Create rooms from text-based room numbers
	for _, roomNum := range roomNumbers {
		room := types.Room{
			Number: roomNum,
			Type:   b.classifyRoomType(roomNum),
			Bounds: types.Rect{
				X:      0, // Will be positioned based on image analysis
				Y:      0,
				Width:  200, // Default dimensions
				Height: 150,
			},
			Area: 30000, // Default area in square pixels
		}
		rooms = append(rooms, room)
	}

	return rooms, nil
}

// extractRoomsFromImage extracts room information from processed image features
func (b *Builder) extractRoomsFromImage(processedImg *types.ProcessedImage) []types.Room {
	rooms := []types.Room{}

	for _, feature := range processedImg.Features {
		if feature.Type == "room" {
			// Generate room number based on position
			roomNum := b.generateRoomNumber(feature.Bounds)
			
			room := types.Room{
				Number: roomNum,
				Type:   b.classifyRoomType(roomNum),
				Bounds: feature.Bounds,
				Area:   float64(feature.Bounds.Width * feature.Bounds.Height),
			}

			// Extract confidence from metadata
			if confidence, ok := feature.Metadata["confidence"]; ok {
				if conf, ok := confidence.(float64); ok && conf > 15.0 {
					rooms = append(rooms, room)
				}
			} else {
				rooms = append(rooms, room)
			}
		}
	}

	return rooms
}

// DetectIDFLocations identifies IDF locations from text and room data
func (b *Builder) DetectIDFLocations(text string, rooms []types.Room) ([]types.IDFLocation, error) {
	idfLocations := []types.IDFLocation{}
	
	// Extract IDF references from text
	idfPattern := regexp.MustCompile(`(?i)\b((?:IDF|MDF)\s*\d+[a-zA-Z]?)\b`)
	matches := idfPattern.FindAllStringSubmatch(text, -1)
	
	idfSet := make(map[string]bool)
	for _, match := range matches {
		if len(match) >= 2 {
			idfID := strings.TrimSpace(match[1])
			idfID = strings.ToUpper(idfID)
			
			if !idfSet[idfID] {
				// Try to find associated room
				roomNumber := b.findAssociatedRoom(idfID, rooms)
				
				idfLocation := types.IDFLocation{
					ID:         idfID,
					Position:   types.Point{X: 0, Y: 0}, // Default position
					Size:       types.Size{Width: 50, Height: 50},
					Equipment:  []string{"Network Switch", "Patch Panel"},
					RoomNumber: roomNumber,
				}
				
				// Position IDF based on associated room
				if roomNumber != "" {
					for _, room := range rooms {
						if room.Number == roomNumber {
							idfLocation.Position = types.Point{
								X: room.Bounds.X + room.Bounds.Width/2,
								Y: room.Bounds.Y + room.Bounds.Height/2,
							}
							break
						}
					}
				}
				
				idfLocations = append(idfLocations, idfLocation)
				idfSet[idfID] = true
			}
		}
	}

	return idfLocations, nil
}

// extractRoomNumbers extracts valid room numbers from text
func (b *Builder) extractRoomNumbers(text string) []string {
	roomNumbers := []string{}
	roomSet := make(map[string]bool)

	// Pattern for 3-digit room numbers with optional letter suffix
	roomPattern := regexp.MustCompile(`\b(\d{3}[a-zA-Z]?)\b`)
	matches := roomPattern.FindAllStringSubmatch(text, -1)

	for _, match := range matches {
		if len(match) >= 2 {
			room := match[1]
			
			// Filter out obviously non-room numbers
			if b.isValidRoomNumber(room) && !roomSet[room] {
				roomNumbers = append(roomNumbers, room)
				roomSet[room] = true
			}
		}
	}

	return roomNumbers
}

// isValidRoomNumber validates that a number looks like a real room number
func (b *Builder) isValidRoomNumber(room string) bool {
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

	// Room numbers typically start with floor number (1-9, not 0)
	if len(numStr) == 3 {
		firstDigit := numStr[0]
		if firstDigit >= '1' && firstDigit <= '9' {
			// Avoid technical numbers that appear in PDFs
			if !b.looksLikeTechnicalNumber(room) {
				return true
			}
		}
	}

	return false
}

// looksLikeTechnicalNumber identifies numbers that are likely technical specs
func (b *Builder) looksLikeTechnicalNumber(room string) bool {
	// Generic patterns that commonly appear in technical specs across PDFs
	// Avoid round hundreds, repeated digits, and common technical values
	if len(room) == 3 {
		// Round hundreds (100, 200, 300, etc.)
		if room[1] == '0' && room[2] == '0' {
			return true
		}
		// Repeated digits (111, 222, etc.)
		if room[0] == room[1] && room[1] == room[2] {
			return true
		}
	}
	
	return false
}

// classifyRoomType determines room type based on room number and context
func (b *Builder) classifyRoomType(roomNumber string) types.RoomType {
	roomUpper := strings.ToUpper(roomNumber)
	
	// IDF rooms often have specific patterns
	if strings.Contains(roomUpper, "IDF") {
		return types.IDF
	}
	
	// Extract numeric part for floor/room analysis
	if len(roomNumber) >= 3 {
		// First digit often indicates floor
		// Second and third digits indicate room type or sequence
		secondDigit := roomNumber[1]
		
		// Common patterns in educational buildings
		switch secondDigit {
		case '0': // Often utility or special purpose
			return types.Utility
		case '1', '2', '3', '4': // Often classrooms
			return types.Classroom
		case '5', '6': // Often offices
			return types.Office
		case '7', '8', '9': // Often storage or utility
			return types.Storage
		}
	}
	
	return types.Unknown
}

// generateRoomNumber generates a room number based on position
func (b *Builder) generateRoomNumber(bounds types.Rect) string {
	// Generate generic room identifier based on position
	// Format: R_X_Y (e.g., "R_1200_800" for room at coordinates 1200,800)
	return fmt.Sprintf("R_%d_%d", bounds.X/100*100, bounds.Y/100*100)
}

// findAssociatedRoom finds which room an IDF might be located in
func (b *Builder) findAssociatedRoom(idfID string, rooms []types.Room) string {
	// Look for exact matches first
	for _, room := range rooms {
		if strings.Contains(strings.ToUpper(room.Number), strings.ToUpper(idfID)) {
			return room.Number
		}
	}
	
	// Extract number from IDF ID for pattern matching
	idfPattern := regexp.MustCompile(`\d+`)
	matches := idfPattern.FindStringSubmatch(idfID)
	
	if len(matches) > 0 {
		idfNum := matches[0]
		
		// Look for room numbers that contain this number
		for _, room := range rooms {
			if strings.Contains(room.Number, idfNum) {
				return room.Number
			}
		}
	}
	
	return "" // No association found
}

// calculateCampusBounds calculates the overall bounds of the campus
func (b *Builder) calculateCampusBounds(rooms []types.Room, idfLocations []types.IDFLocation) types.Rect {
	if len(rooms) == 0 && len(idfLocations) == 0 {
		return types.Rect{X: 0, Y: 0, Width: 1000, Height: 800}
	}

	minX, minY := math.MaxInt32, math.MaxInt32
	maxX, maxY := math.MinInt32, math.MinInt32

	// Consider room bounds
	for _, room := range rooms {
		if room.Bounds.X < minX {
			minX = room.Bounds.X
		}
		if room.Bounds.Y < minY {
			minY = room.Bounds.Y
		}
		if room.Bounds.X+room.Bounds.Width > maxX {
			maxX = room.Bounds.X + room.Bounds.Width
		}
		if room.Bounds.Y+room.Bounds.Height > maxY {
			maxY = room.Bounds.Y + room.Bounds.Height
		}
	}

	// Consider IDF positions
	for _, idf := range idfLocations {
		if idf.Position.X < minX {
			minX = idf.Position.X
		}
		if idf.Position.Y < minY {
			minY = idf.Position.Y
		}
		if idf.Position.X+idf.Size.Width > maxX {
			maxX = idf.Position.X + idf.Size.Width
		}
		if idf.Position.Y+idf.Size.Height > maxY {
			maxY = idf.Position.Y + idf.Size.Height
		}
	}

	return types.Rect{
		X:      minX,
		Y:      minY,
		Width:  maxX - minX,
		Height: maxY - minY,
	}
}