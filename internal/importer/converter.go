package importer

import (
	"fmt"
	"io"
	"strings"
	"time"

	"github.com/joelpate/arxos/internal/bim"
	"github.com/joelpate/arxos/internal/common/logger"
)

// PDFToBIMConverter converts PDF floor plans to BIM format
type PDFToBIMConverter struct {
	extractor *SimplePDFExtractor
}

// NewPDFToBIMConverter creates a new converter
func NewPDFToBIMConverter() *PDFToBIMConverter {
	return &PDFToBIMConverter{
		extractor: NewSimplePDFExtractor(),
	}
}

// ConvertOptions provides options for conversion
type ConvertOptions struct {
	BuildingName string
	StartFloor   int
	FloorHeight  float64
}

// Convert converts a PDF to BIM format
func (c *PDFToBIMConverter) Convert(reader io.Reader, opts ConvertOptions) (*bim.Building, error) {
	logger.Debug("Starting PDF to BIM conversion")

	// Use simple extraction
	extractedData, err := c.extractor.ExtractText(reader)
	if err != nil {
		return nil, fmt.Errorf("failed to extract text: %w", err)
	}

	// Create building from extracted data
	building := &bim.Building{
		Name:        opts.BuildingName,
		FileVersion: "1.0",
		Generated:   time.Now(),
		Units:       bim.Feet,
		Metadata: bim.Metadata{
			CreatedBy:    "ArxOS PDF Import",
			Organization: "ArxOS",
			Notes:        fmt.Sprintf("Imported from PDF on %s", time.Now().Format("2006-01-02")),
		},
		Floors: make([]bim.Floor, 0),
	}

	// Group equipment by floor (simple heuristic based on page)
	floorEquipment := make(map[int][]bim.Equipment)
	floorRooms := make(map[int][]string)

	for _, eq := range extractedData.Equipment {
		floor := eq.Page
		if floor == 0 {
			floor = 1
		}

		equipment := bim.Equipment{
			ID:   eq.ID,
			Type: eq.Type,
			Status: bim.StatusUnknown,
			Location: bim.Location{
				X: eq.Position.X,
				Y: eq.Position.Y,
			},
			Notes: fmt.Sprintf("Imported from PDF page %d", eq.Page),
		}

		floorEquipment[floor] = append(floorEquipment[floor], equipment)
	}

	for _, room := range extractedData.Rooms {
		floor := room.Page
		if floor == 0 {
			floor = 1
		}
		floorRooms[floor] = append(floorRooms[floor], room.ID)
	}

	// Create floors
	for floorNum := 1; floorNum <= getMaxFloor(floorEquipment, floorRooms); floorNum++ {
		floor := bim.Floor{
			Level: floorNum,
			Name:  fmt.Sprintf("Floor %d", floorNum),
			Dimensions: bim.Dimensions{
				Width:  200, // Default dimensions
				Height: 150,
			},
			Equipment: floorEquipment[floorNum],
			Legend:    generateLegend(),
		}

		// Add room information to equipment
		rooms := floorRooms[floorNum]
		for i := range floor.Equipment {
			if len(rooms) > 0 {
				// Simple assignment - in reality would need spatial analysis
				floor.Equipment[i].Location.Room = rooms[i%len(rooms)]
			}
		}

		// Generate simple ASCII layout
		floor.Layout = generateSimpleLayout(floor)

		building.Floors = append(building.Floors, floor)
	}

	// Add validation
	totalEquipment := 0
	for _, floor := range building.Floors {
		totalEquipment += len(floor.Equipment)
	}

	building.Validation = bim.Validation{
		Checksum:        "SHA256:pending",
		EquipmentCount:  totalEquipment,
		ConnectionCount: 0,
		LastModified:    time.Now(),
		ModifiedBy:      "ArxOS PDF Import",
	}

	logger.Info("Conversion complete: %d floors, %d total equipment items",
		len(building.Floors), len(extractedData.Equipment))

	return building, nil
}

func getMaxFloor(equipment map[int][]bim.Equipment, rooms map[int][]string) int {
	maxFloor := 1
	for floor := range equipment {
		if floor > maxFloor {
			maxFloor = floor
		}
	}
	for floor := range rooms {
		if floor > maxFloor {
			maxFloor = floor
		}
	}
	return maxFloor
}

func generateLegend() map[rune]string {
	return map[rune]string{
		'#': "Wall",
		'.': "Open Space",
		'D': "Door",
		'+': "Operational Equipment",
		'*': "Critical Equipment",
		'!': "Failed Equipment",
		'@': "Electrical Panel",
		'$': "HVAC Equipment",
		'W': "Window",
	}
}

func generateSimpleLayout(floor bim.Floor) []string {
	width := int(floor.Dimensions.Width / 10)
	height := int(floor.Dimensions.Height / 10)

	if width > 80 {
		width = 80
	}
	if height > 30 {
		height = 30
	}

	// Create grid
	grid := make([][]rune, height)
	for i := range grid {
		grid[i] = make([]rune, width)
		for j := range grid[i] {
			grid[i][j] = '.'
		}
	}

	// Add borders
	for i := 0; i < width; i++ {
		grid[0][i] = '#'
		grid[height-1][i] = '#'
	}
	for i := 0; i < height; i++ {
		grid[i][0] = '#'
		grid[i][width-1] = '#'
	}

	// Place equipment
	for _, eq := range floor.Equipment {
		x := int(eq.Location.X / 10)
		y := int(eq.Location.Y / 10)

		if x >= 0 && x < width && y >= 0 && y < height {
			symbol := getEquipmentSymbol(eq)
			grid[y][x] = symbol
		}
	}

	// Convert to strings
	layout := make([]string, height)
	for i, row := range grid {
		layout[i] = string(row)
	}

	return layout
}

func getEquipmentSymbol(eq bim.Equipment) rune {
	// Determine symbol based on type and status
	if eq.Status == bim.StatusFailed {
		return '!'
	}

	typePrefix := strings.Split(eq.Type, ".")[0]
	switch typePrefix {
	case "Network":
		if strings.Contains(eq.Type, "MDF") || strings.Contains(eq.Type, "IDF") {
			return 'M'
		}
		return '+'
	case "Electrical":
		return '@'
	case "HVAC":
		return '$'
	case "Fire":
		return 'F'
	default:
		return '*'
	}
}