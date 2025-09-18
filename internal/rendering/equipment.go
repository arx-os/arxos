package rendering

import (
	"github.com/arx-os/arxos/pkg/models"
)

// EquipmentLayer renders equipment placement and status
type EquipmentLayer struct {
	equipment []models.Equipment
	visible   bool
	dirty     []Region
	symbols   map[string]rune // Equipment type to symbol mapping
}

// NewEquipmentLayer creates a new equipment visualization layer
func NewEquipmentLayer(equipment []models.Equipment) *EquipmentLayer {
	return &EquipmentLayer{
		equipment: equipment,
		visible:   true,
		dirty:     []Region{},
		symbols:   defaultEquipmentSymbols(),
	}
}

// defaultEquipmentSymbols returns standard symbols for equipment types
func defaultEquipmentSymbols() map[string]rune {
	return map[string]rune{
		// Electrical
		"outlet":        '○',
		"outlet_active": '●',
		"panel":         '⚡',
		"breaker":       '◉',
		"transformer":   '⊗',
		"switch":        '◇',
		"generator":     '⚙',

		// HVAC
		"hvac":       '▲',
		"thermostat": '▽',
		"vent":       '◈',
		"fan":        '⊕',
		"chiller":    '❄',
		"boiler":     '🔥',

		// Plumbing
		"valve":  '⊖',
		"pump":   '◎',
		"tank":   '■',
		"faucet": '💧',
		"drain":  '◌',

		// IT/Network
		"server":       '▣',
		"computer":     '▪',
		"router":       '◆',
		"access_point": '📡',
		"rack":         '▦',

		// Safety
		"fire_alarm":      '🔔',
		"sprinkler":       '☂',
		"extinguisher":    '🧯',
		"exit_sign":       '🚪',
		"emergency_light": '💡',

		// General
		"unknown":     '?',
		"failed":      '✗',
		"warning":     '⚠',
		"maintenance": '🔧',
	}
}

// Render produces the ASCII representation of equipment
func (e *EquipmentLayer) Render(viewport Viewport) [][]rune {
	// Initialize render buffer
	buffer := make([][]rune, viewport.Height)
	for i := range buffer {
		buffer[i] = make([]rune, viewport.Width)
		for j := range buffer[i] {
			buffer[i][j] = ' '
		}
	}

	if !e.visible {
		return buffer
	}

	// Render each piece of equipment
	for _, eq := range e.equipment {
		e.renderEquipment(buffer, eq, viewport)
	}

	return buffer
}

func (e *EquipmentLayer) renderEquipment(buffer [][]rune, eq models.Equipment, vp Viewport) {
	// Convert equipment position to viewport coordinates
	x := int((eq.Location.X - vp.X) * vp.Zoom)
	y := int((eq.Location.Y - vp.Y) * vp.Zoom)

	// Skip if outside viewport
	if x < 0 || x >= vp.Width || y < 0 || y >= vp.Height {
		return
	}

	// Determine symbol based on equipment type and status
	symbol := e.getEquipmentSymbol(eq)

	// Apply status modifiers
	if eq.Status == models.StatusFailed {
		symbol = e.symbols["failed"]
	} else if eq.Status == models.StatusDegraded {
		symbol = e.symbols["warning"]
	} else if eq.Status == "maintenance" {
		symbol = e.symbols["maintenance"]
	}

	// Place symbol in buffer
	buffer[y][x] = symbol

	// Add equipment ID label if zoom is high enough
	if vp.Zoom >= 2.0 && len(eq.ID) > 0 {
		// Place ID below equipment if space permits
		if y+1 < vp.Height {
			idStr := eq.ID
			if len(idStr) > 8 {
				idStr = idStr[:8] // Truncate long IDs
			}

			startX := x - len(idStr)/2
			if startX < 0 {
				startX = 0
			}

			for i, ch := range idStr {
				if startX+i < vp.Width {
					buffer[y+1][startX+i] = ch
				}
			}
		}
	}
}

func (e *EquipmentLayer) getEquipmentSymbol(eq models.Equipment) rune {
	// Check for specific state-based symbols
	if eq.Type == "outlet" && eq.Status == models.StatusOperational {
		return e.symbols["outlet_active"]
	}

	// Get symbol for equipment type
	if symbol, exists := e.symbols[eq.Type]; exists {
		return symbol
	}

	// Default to unknown symbol
	return e.symbols["unknown"]
}

// Update advances the layer's state
func (e *EquipmentLayer) Update(dt float64) {
	// Could animate equipment status changes here
	// For example, blinking failed equipment
}

// SetVisible controls layer visibility
func (e *EquipmentLayer) SetVisible(visible bool) {
	e.visible = visible
}

// IsVisible returns current visibility state
func (e *EquipmentLayer) IsVisible() bool {
	return e.visible
}

// GetZ returns the z-index for layering
func (e *EquipmentLayer) GetZ() int {
	return LayerEquipment
}

// GetName returns the layer name
func (e *EquipmentLayer) GetName() string {
	return "equipment"
}

// SetDirty marks regions that need re-rendering
func (e *EquipmentLayer) SetDirty(regions []Region) {
	e.dirty = regions
}

// UpdateEquipment updates the equipment list
func (e *EquipmentLayer) UpdateEquipment(equipment []models.Equipment) {
	e.equipment = equipment
	e.dirty = []Region{{0, 0, 1000, 1000}} // Force full redraw
}

// SetEquipmentSymbol allows customizing equipment symbols
func (e *EquipmentLayer) SetEquipmentSymbol(eqType string, symbol rune) {
	e.symbols[eqType] = symbol
}

// FindEquipmentAt returns equipment at a specific viewport position
func (e *EquipmentLayer) FindEquipmentAt(x, y int, vp Viewport) *models.Equipment {
	// Convert viewport coordinates to world coordinates
	worldX := vp.X + float64(x)/vp.Zoom
	worldY := vp.Y + float64(y)/vp.Zoom

	// Find equipment at this position (with some tolerance)
	tolerance := 0.5 / vp.Zoom

	for i := range e.equipment {
		eq := &e.equipment[i]
		if worldX >= eq.Location.X-tolerance && worldX <= eq.Location.X+tolerance &&
			worldY >= eq.Location.Y-tolerance && worldY <= eq.Location.Y+tolerance {
			return eq
		}
	}

	return nil
}

// HighlightEquipment marks specific equipment for highlighting
func (e *EquipmentLayer) HighlightEquipment(equipmentID string, highlight bool) {
	for i := range e.equipment {
		if e.equipment[i].ID == equipmentID {
			// Could store highlight state and render differently
			// For now, mark the equipment's region as dirty
			x := int(e.equipment[i].Location.X)
			y := int(e.equipment[i].Location.Y)
			e.dirty = append(e.dirty, Region{x - 1, y - 1, 3, 3})
			break
		}
	}
}
