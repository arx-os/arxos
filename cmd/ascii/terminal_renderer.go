// Package ascii implements the terminal ASCII-BIM rendering system
// This is the heart of Arxos - buildings rendered as navigable ASCII art
package ascii

import (
	"fmt"
	"strings"

	"github.com/arxos/arxos/cmd/models"
	// "github.com/arxos/arxos/core/cgo" // TODO: Fix import path
)

// ZoomLevel represents the 7 levels of detail from vision.md
type ZoomLevel int

const (
	ZoomCampus    ZoomLevel = 0 // 1 char = 100m
	ZoomBuilding  ZoomLevel = 1 // 1 char = 10m
	ZoomFloor     ZoomLevel = 2 // 1 char = 1m
	ZoomRoom      ZoomLevel = 3 // 1 char = 1m
	ZoomEquipment ZoomLevel = 4 // 1 char = 10cm
	ZoomComponent ZoomLevel = 5 // 1 char = 1cm
	ZoomChip      ZoomLevel = 6 // 1 char = 1mm
)

// CharacterSet defines the Pixatool-inspired ASCII characters for each zoom level
type CharacterSet struct {
	Wall       rune
	Door       rune
	Window     rune
	Room       rune
	Furniture  rune
	MEP        rune
	Equipment  rune
	Empty      rune
	Connection rune
}

// TerminalRenderer handles ASCII-BIM rendering to terminal
type TerminalRenderer struct {
	Width       int
	Height      int
	ZoomLevel   ZoomLevel
	UsePixatool bool
	CharSets    map[ZoomLevel]CharacterSet
	Canvas      [][]rune
}

// NewTerminalRenderer creates a renderer with Pixatool-inspired character sets
func NewTerminalRenderer(width, height int) *TerminalRenderer {
	r := &TerminalRenderer{
		Width:       width,
		Height:      height,
		ZoomLevel:   ZoomFloor,
		UsePixatool: true,
		Canvas:      make([][]rune, height),
	}
	
	// Initialize canvas
	for i := range r.Canvas {
		r.Canvas[i] = make([]rune, width)
		for j := range r.Canvas[i] {
			r.Canvas[i][j] = ' '
		}
	}
	
	// Initialize Pixatool-inspired character sets for each zoom level
	r.CharSets = map[ZoomLevel]CharacterSet{
		ZoomCampus: {
			Wall: '▓', Door: '░', Window: '─', Room: ' ',
			Furniture: '·', MEP: '×', Equipment: '□', Empty: ' ', Connection: '·',
		},
		ZoomBuilding: {
			Wall: '█', Door: '╬', Window: '═', Room: '░',
			Furniture: '▫', MEP: '⊡', Equipment: '▣', Empty: ' ', Connection: '─',
		},
		ZoomFloor: {
			Wall: '█', Door: '╫', Window: '═', Room: '·',
			Furniture: '▢', MEP: '⊞', Equipment: '▣', Empty: ' ', Connection: '│',
		},
		ZoomRoom: {
			Wall: '▓', Door: '◊', Window: '═', Room: '·',
			Furniture: '▢', MEP: '○', Equipment: '▣', Empty: ' ', Connection: '├',
		},
		ZoomEquipment: {
			Wall: '▣', Door: '◊', Window: '─', Room: ' ',
			Furniture: '□', MEP: '⊞', Equipment: '●', Empty: ' ', Connection: '┼',
		},
		ZoomComponent: {
			Wall: '●', Door: '○', Window: '·', Room: ' ',
			Furniture: '·', MEP: '○', Equipment: '◉', Empty: ' ', Connection: '─',
		},
		ZoomChip: {
			Wall: '∙', Door: '·', Window: '·', Room: ' ',
			Furniture: '·', MEP: '·', Equipment: '•', Empty: ' ', Connection: '·',
		},
	}
	
	return r
}

// RenderPath renders objects at a specific path with appropriate zoom
func (r *TerminalRenderer) RenderPath(path string, objects []*models.ArxObject, zoom ZoomLevel) (string, error) {
	r.ZoomLevel = zoom
	r.clearCanvas()
	
	// Get character set for current zoom level
	charSet := r.CharSets[zoom]
	
	// TODO: Re-enable CGO integration
	// For now, use fallback renderer
	ascii := r.fallbackRender(objects, zoom, charSet)
	
	// Add frame and information
	output := r.addFrame(ascii, path, zoom)
	
	return output, nil
}

// fallbackRender provides Go-based rendering if C engine is unavailable
func (r *TerminalRenderer) fallbackRender(objects []*models.ArxObject, zoom ZoomLevel, charSet CharacterSet) string {
	// Simple grid-based rendering
	for _, obj := range objects {
		r.renderObject(obj, charSet)
	}
	
	// Apply Pixatool optimizations if enabled
	if r.UsePixatool {
		pixatool := NewPixatoolRenderer()
		r.Canvas = pixatool.OptimizeCanvas(r.Canvas, r.Width, r.Height)
	}
	
	// Apply any additional rendering based on zoom level
	switch r.ZoomLevel {
	case ZoomChip:
		// At chip level, show circuit paths
		r.renderCircuitPaths()
	case ZoomComponent:
		// At component level, show connections
		r.renderConnections()
	}
	
	return r.canvasToString()
}

// renderObject renders a single object to the canvas
func (r *TerminalRenderer) renderObject(obj *models.ArxObject, charSet CharacterSet) {
	// Map object type to character
	char := r.getCharForType(obj.Type, charSet)
	
	// Calculate position based on zoom and scale
	x, y := r.worldToCanvas(obj.Position.X, obj.Position.Y)
	
	if x >= 0 && x < r.Width && y >= 0 && y < r.Height {
		r.Canvas[y][x] = char
	}
}

// getCharForType returns appropriate character for object type
func (r *TerminalRenderer) getCharForType(objType string, charSet CharacterSet) rune {
	switch objType {
	case "wall":
		return charSet.Wall
	case "door":
		return charSet.Door
	case "window":
		return charSet.Window
	case "room":
		return charSet.Room
	case "furniture":
		return charSet.Furniture
	case "electrical", "hvac", "plumbing":
		return charSet.MEP
	case "equipment":
		return charSet.Equipment
	default:
		return charSet.Empty
	}
}

// worldToCanvas converts world coordinates to canvas position
func (r *TerminalRenderer) worldToCanvas(worldX, worldY float64) (int, int) {
	scale := getScaleForZoom(r.ZoomLevel)
	canvasX := int(worldX * scale)
	canvasY := int(worldY * scale)
	return canvasX, canvasY
}

// clearCanvas resets the canvas
func (r *TerminalRenderer) clearCanvas() {
	for i := range r.Canvas {
		for j := range r.Canvas[i] {
			r.Canvas[i][j] = ' '
		}
	}
}

// canvasToString converts canvas to string
func (r *TerminalRenderer) canvasToString() string {
	var lines []string
	for _, row := range r.Canvas {
		lines = append(lines, string(row))
	}
	return strings.Join(lines, "\n")
}

// addFrame adds border and information to the ASCII output
func (r *TerminalRenderer) addFrame(ascii, path string, zoom ZoomLevel) string {
	var output strings.Builder
	
	// Top border with info
	borderLine := strings.Repeat("═", r.Width-2)
	output.WriteString(fmt.Sprintf("╔%s╗\n", borderLine))
	
	// Header with path and zoom info
	header := fmt.Sprintf(" Path: %s │ Zoom: %s (%d) ", path, getZoomName(zoom), zoom)
	headerPadding := r.Width - len(header) - 2
	if headerPadding > 0 {
		header += strings.Repeat(" ", headerPadding)
	}
	output.WriteString(fmt.Sprintf("║%s║\n", header))
	
	// Separator
	output.WriteString(fmt.Sprintf("╠%s╣\n", borderLine))
	
	// ASCII content
	lines := strings.Split(ascii, "\n")
	for _, line := range lines {
		paddedLine := padOrTruncate(line, r.Width-2)
		output.WriteString(fmt.Sprintf("║%s║\n", paddedLine))
	}
	
	// Bottom border with legend
	output.WriteString(fmt.Sprintf("╠%s╣\n", borderLine))
	
	// Legend based on zoom level
	legend := r.getLegend(zoom)
	output.WriteString(fmt.Sprintf("║%s║\n", padOrTruncate(legend, r.Width-2)))
	
	// Controls
	controls := " +/- zoom │ arrows: pan │ q: quit "
	output.WriteString(fmt.Sprintf("║%s║\n", padOrTruncate(controls, r.Width-2)))
	
	output.WriteString(fmt.Sprintf("╚%s╝\n", borderLine))
	
	return output.String()
}

// getLegend returns legend for current zoom level
func (r *TerminalRenderer) getLegend(zoom ZoomLevel) string {
	charSet := r.CharSets[zoom]
	return fmt.Sprintf(" Legend: %c=Wall %c=Door %c=Window %c=MEP %c=Equipment",
		charSet.Wall, charSet.Door, charSet.Window, charSet.MEP, charSet.Equipment)
}

// getRenderOptions creates C-compatible render options
// getRenderOptions is temporarily disabled until CGO is properly integrated
/*
func (r *TerminalRenderer) getRenderOptions(zoom ZoomLevel, charSet CharacterSet) *cgo.ASCIIRenderOptions {
	return &cgo.ASCIIRenderOptions{
		ShowLabels:      zoom >= ZoomRoom,
		ShowCoordinates: zoom >= ZoomEquipment,
		ShowLegend:      true,
		OptimizeSpacing: true,
		MaxWidth:        r.Width,
		MaxHeight:       r.Height,
		WallChar:        byte(charSet.Wall),
		DoorChar:        byte(charSet.Door),
		WindowChar:      byte(charSet.Window),
		RoomChar:        byte(charSet.Room),
		FurnitureChar:   byte(charSet.Furniture),
		MEPChar:         byte(charSet.MEP),
	}
}
*/

// Helper functions

func shouldRenderAtZoom(obj *models.ArxObject, zoom ZoomLevel) bool {
	// Determine if object should be visible at current zoom level
	switch zoom {
	case ZoomCampus:
		return obj.Type == "building"
	case ZoomBuilding:
		return obj.Type == "floor" || obj.Type == "building"
	case ZoomFloor, ZoomRoom:
		return obj.Type != "component" && obj.Type != "chip"
	case ZoomEquipment:
		return obj.Type != "chip"
	default:
		return true
	}
}

func convertToC(obj *models.ArxObject) interface{} { // *cgo.ArxObject {
	// Convert Go ArxObject to C format
	// This would use the actual CGO bridge
	return nil // Placeholder
}

func getScaleForZoom(zoom ZoomLevel) float64 {
	scales := map[ZoomLevel]float64{
		ZoomCampus:    0.01,   // 1 char = 100m
		ZoomBuilding:  0.1,    // 1 char = 10m
		ZoomFloor:     1.0,    // 1 char = 1m
		ZoomRoom:      1.0,    // 1 char = 1m
		ZoomEquipment: 10.0,   // 1 char = 10cm
		ZoomComponent: 100.0,  // 1 char = 1cm
		ZoomChip:      1000.0, // 1 char = 1mm
	}
	return scales[zoom]
}

func getZoomName(zoom ZoomLevel) string {
	names := []string{
		"Campus", "Building", "Floor", "Room",
		"Equipment", "Component", "Chip",
	}
	if int(zoom) < len(names) {
		return names[zoom]
	}
	return "Unknown"
}

func padOrTruncate(s string, width int) string {
	if len(s) >= width {
		return s[:width]
	}
	return s + strings.Repeat(" ", width-len(s))
}

// renderCircuitPaths renders circuit paths at chip zoom level
func (r *TerminalRenderer) renderCircuitPaths() {
	// Add circuit traces as thin lines
	for y := 1; y < r.Height-1; y += 4 {
		for x := 2; x < r.Width-2; x++ {
			if r.Canvas[y][x] == ' ' {
				r.Canvas[y][x] = '·'
			}
		}
	}
}

// renderConnections renders component connections
func (r *TerminalRenderer) renderConnections() {
	// Add connection lines between components
	charSet := r.CharSets[r.ZoomLevel]
	for y := 0; y < r.Height; y++ {
		for x := 0; x < r.Width; x++ {
			if r.Canvas[y][x] == charSet.Equipment && x < r.Width-1 {
				// Draw connection to the right if there's another component
				if r.Canvas[y][x+1] == charSet.Equipment {
					r.Canvas[y][x] = charSet.Connection
				}
			}
		}
	}
}