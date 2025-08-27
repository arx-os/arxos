// Package idf provides IDF (Intermediate Distribution Frame) detection and analysis
package idf

import (
	"fmt"
	"regexp"
	"strings"

	"github.com/arxos/arxos/internal/types"
)

// Detector implements IDF location detection
type Detector struct {
	config *types.ParseConfig
}

// NewDetector creates a new IDF detector
func NewDetector() *Detector {
	return &Detector{
		config: types.DefaultParseConfig(),
	}
}

// NewDetectorWithConfig creates a new IDF detector with custom configuration
func NewDetectorWithConfig(config *types.ParseConfig) *Detector {
	return &Detector{
		config: config,
	}
}

// DetectIDFLocations finds IDF references in text and associates them with rooms
func (d *Detector) DetectIDFLocations(text string, rooms []types.Room) ([]types.IDFLocation, error) {
	idfLocations := []types.IDFLocation{}
	
	// Extract IDF and MDF references
	idfRefs := d.extractIDFReferences(text)
	
	for _, idfRef := range idfRefs {
		location := d.createIDFLocation(idfRef, rooms)
		if location != nil {
			idfLocations = append(idfLocations, *location)
		}
	}

	// Mark IDF rooms for highlighting
	d.markIDFRooms(idfLocations)

	return idfLocations, nil
}

// extractIDFReferences extracts IDF/MDF references from text
func (d *Detector) extractIDFReferences(text string) []string {
	idfRefs := []string{}
	idfSet := make(map[string]bool)

	// Pattern for IDF and MDF references - more flexible matching
	patterns := []*regexp.Regexp{
		regexp.MustCompile(`(?i)\b(IDF\s*[-#]?\s*\d+[a-zA-Z]?)\b`),
		regexp.MustCompile(`(?i)\b(MDF\s*[-#]?\s*\d+[a-zA-Z]?)\b`),
		regexp.MustCompile(`(?i)\b(IDF[-#]?\d+[a-zA-Z]?)\b`),
		regexp.MustCompile(`(?i)\b(MDF[-#]?\d+[a-zA-Z]?)\b`),
	}

	for _, pattern := range patterns {
		matches := pattern.FindAllStringSubmatch(text, -1)
		for _, match := range matches {
			if len(match) >= 2 {
				idf := d.normalizeIDFReference(match[1])
				if !idfSet[idf] {
					idfRefs = append(idfRefs, idf)
					idfSet[idf] = true
				}
			}
		}
	}

	return idfRefs
}

// normalizeIDFReference standardizes IDF reference format
func (d *Detector) normalizeIDFReference(ref string) string {
	// Convert to uppercase and normalize spacing
	normalized := strings.ToUpper(strings.TrimSpace(ref))
	
	// Standardize separators
	normalized = regexp.MustCompile(`\s*[-#]\s*`).ReplaceAllString(normalized, "-")
	normalized = regexp.MustCompile(`\s+`).ReplaceAllString(normalized, " ")
	
	return normalized
}

// createIDFLocation creates an IDF location from a reference
func (d *Detector) createIDFLocation(idfRef string, rooms []types.Room) *types.IDFLocation {
	location := &types.IDFLocation{
		ID:          idfRef,
		Position:    types.Point{X: 0, Y: 0},
		Size:        types.Size{Width: 60, Height: 40},
		Equipment:   d.getDefaultEquipment(),
		RoomNumber:  d.findAssociatedRoom(idfRef, rooms),
		Highlighted: true,
	}

	// Position IDF within associated room if found
	for _, room := range rooms {
		if room.Number == location.RoomNumber {
			// Place IDF near center of room
			location.Position = types.Point{
				X: room.Bounds.X + room.Bounds.Width/2 - location.Size.Width/2,
				Y: room.Bounds.Y + room.Bounds.Height/2 - location.Size.Height/2,
			}
			break
		}
	}

	return location
}

// findAssociatedRoom attempts to find which room contains the IDF
func (d *Detector) findAssociatedRoom(idfRef string, rooms []types.Room) string {
	idfUpper := strings.ToUpper(idfRef)
	
	// Direct text matching first
	for _, room := range rooms {
		roomUpper := strings.ToUpper(room.Number)
		if strings.Contains(idfUpper, roomUpper) || strings.Contains(roomUpper, idfUpper) {
			return room.Number
		}
	}
	
	// Extract number from IDF reference for pattern matching
	numberPattern := regexp.MustCompile(`\d+`)
	matches := numberPattern.FindStringSubmatch(idfRef)
	
	if len(matches) > 0 {
		idfNumber := matches[0]
		
		// Look for rooms containing this number
		for _, room := range rooms {
			if strings.Contains(room.Number, idfNumber) {
				return room.Number
			}
		}
		
		// Look for rooms on same floor (first digit match)
		if len(idfNumber) > 0 {
			floorDigit := string(idfNumber[0])
			for _, room := range rooms {
				if strings.HasPrefix(room.Number, floorDigit) {
					return room.Number
				}
			}
		}
	}

	return "" // No association found
}

// getDefaultEquipment returns typical IDF equipment
func (d *Detector) getDefaultEquipment() []string {
	return []string{
		"Network Switch",
		"Patch Panel", 
		"UPS",
		"Cable Management",
	}
}

// markIDFRooms marks rooms that contain IDFs for special highlighting
func (d *Detector) markIDFRooms(idfLocations []types.IDFLocation) {
	for i := range idfLocations {
		if idfLocations[i].RoomNumber != "" {
			idfLocations[i].Highlighted = true
		}
	}
}

// AnalyzeIDFCoverage analyzes IDF coverage across the building
func (d *Detector) AnalyzeIDFCoverage(campus *types.Campus) *IDFAnalysis {
	analysis := &IDFAnalysis{
		TotalIDFs:    len(campus.IDFRooms),
		IDFDensity:   d.calculateIDFDensity(campus),
		Coverage:     d.calculateCoverage(campus),
		Gaps:         d.identifyGaps(campus),
		Redundancy:   d.assessRedundancy(campus),
	}

	return analysis
}

// IDFAnalysis represents analysis of IDF distribution
type IDFAnalysis struct {
	TotalIDFs    int
	IDFDensity   float64 // IDFs per square unit
	Coverage     float64 // Percentage of building covered
	Gaps         []types.Point // Areas with poor coverage
	Redundancy   []string // Areas with redundant coverage
}

// calculateIDFDensity calculates IDF density across the campus
func (d *Detector) calculateIDFDensity(campus *types.Campus) float64 {
	if campus.Bounds.Width == 0 || campus.Bounds.Height == 0 {
		return 0.0
	}
	
	totalArea := float64(campus.Bounds.Width * campus.Bounds.Height)
	return float64(len(campus.IDFRooms)) / totalArea * 1000000 // Per million square units
}

// calculateCoverage estimates network coverage percentage
func (d *Detector) calculateCoverage(campus *types.Campus) float64 {
	if len(campus.IDFRooms) == 0 {
		return 0.0
	}
	
	// Simplified coverage calculation - each IDF covers ~100m radius
	coverageRadius := 100.0
	totalRooms := 0
	coveredRooms := 0
	
	for _, building := range campus.Buildings {
		totalRooms += len(building.Rooms)
		
		for _, room := range building.Rooms {
			roomCenter := types.Point{
				X: room.Bounds.X + room.Bounds.Width/2,
				Y: room.Bounds.Y + room.Bounds.Height/2,
			}
			
			// Check if any IDF covers this room
			for _, idf := range campus.IDFRooms {
				distance := d.calculateDistance(roomCenter, idf.Position)
				if distance <= coverageRadius {
					coveredRooms++
					break
				}
			}
		}
	}
	
	if totalRooms == 0 {
		return 100.0
	}
	
	return float64(coveredRooms) / float64(totalRooms) * 100.0
}

// identifyGaps finds areas with poor IDF coverage
func (d *Detector) identifyGaps(campus *types.Campus) []types.Point {
	gaps := []types.Point{}
	
	// Grid-based gap analysis
	gridSize := 200
	coverageRadius := 150.0
	
	for x := campus.Bounds.X; x < campus.Bounds.X+campus.Bounds.Width; x += gridSize {
		for y := campus.Bounds.Y; y < campus.Bounds.Y+campus.Bounds.Height; y += gridSize {
			point := types.Point{X: x, Y: y}
			
			// Check if this point has IDF coverage
			hasCoverage := false
			for _, idf := range campus.IDFRooms {
				if d.calculateDistance(point, idf.Position) <= coverageRadius {
					hasCoverage = true
					break
				}
			}
			
			if !hasCoverage {
				gaps = append(gaps, point)
			}
		}
	}
	
	return gaps
}

// assessRedundancy identifies areas with overlapping IDF coverage
func (d *Detector) assessRedundancy(campus *types.Campus) []string {
	redundancy := []string{}
	
	for i, idf1 := range campus.IDFRooms {
		overlapCount := 0
		for j, idf2 := range campus.IDFRooms {
			if i != j {
				distance := d.calculateDistance(idf1.Position, idf2.Position)
				if distance < 100.0 { // Close proximity suggests potential overlap
					overlapCount++
				}
			}
		}
		
		if overlapCount > 0 {
			redundancy = append(redundancy, fmt.Sprintf("IDF %s has %d nearby IDFs", idf1.ID, overlapCount))
		}
	}
	
	return redundancy
}

// calculateDistance calculates Euclidean distance between two points
func (d *Detector) calculateDistance(p1, p2 types.Point) float64 {
	dx := float64(p2.X - p1.X)
	dy := float64(p2.Y - p1.Y)
	return dx*dx + dy*dy // Using squared distance for performance
}