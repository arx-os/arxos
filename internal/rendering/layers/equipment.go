package layers

import (
	"github.com/joelpate/arxos/pkg/models"
)

// EquipmentLayer renders equipment and fixtures
type EquipmentLayer struct {
	*BaseLayer
	equipment    []models.Equipment
	showLabels   bool
	highlightID  string // Equipment ID to highlight
	symbolMap    map[string]rune
}

// Default equipment symbols
var defaultEquipmentSymbols = map[string]rune{
	"outlet":         '●',
	"switch":         '▪',
	"panel":          '▣',
	"light":          '◊',
	"sensor":         '◉',
	"thermostat":     '⊕',
	"alarm":          '🔔',
	"camera":         '📷',
	"junction_box":   '▫',
	"appliance":      '▤',
	"hvac":           '❄',
	"pump":           '⊙',
	"valve":          '◈',
	"meter":          '⊡',
	"transformer":    '⚡',
	"generator":      '⊞',
	"battery":        '🔋',
	"server":         '▦',
	"network_switch": '◫',
	"access_point":   '📶',
}

// Status indicators
const (
	StatusOperationalChar  = ' ' // No special indicator
	StatusFailedChar  = '✗'
	StatusWarningChar = '⚠'
	StatusUnknownChar = '?'
)

// NewEquipmentLayer creates a new equipment layer
func NewEquipmentLayer(equipment []models.Equipment) *EquipmentLayer {
	layer := &EquipmentLayer{
		BaseLayer:  NewBaseLayer("equipment", PriorityEquipment),
		equipment:  equipment,
		showLabels: false,
		symbolMap:  make(map[string]rune),
	}
	
	// Copy default symbols
	for k, v := range defaultEquipmentSymbols {
		layer.symbolMap[k] = v
	}
	
	// Calculate bounds from equipment positions
	if len(equipment) > 0 {
		minX, minY := float64(1e9), float64(1e9)
		maxX, maxY := float64(-1e9), float64(-1e9)
		
		for _, equip := range equipment {
			if equip.Location.X < minX {
				minX = equip.Location.X
			}
			if equip.Location.Y < minY {
				minY = equip.Location.Y
			}
			if equip.Location.X > maxX {
				maxX = equip.Location.X
			}
			if equip.Location.Y > maxY {
				maxY = equip.Location.Y
			}
		}
		
		layer.bounds = Bounds{
			MinX: minX - 1,
			MinY: minY - 1,
			MaxX: maxX + 1,
			MaxY: maxY + 1,
		}
	}
	
	return layer
}

// SetEquipment updates the equipment list
func (e *EquipmentLayer) SetEquipment(equipment []models.Equipment) {
	e.equipment = equipment
}

// SetShowLabels enables/disables equipment labels
func (e *EquipmentLayer) SetShowLabels(show bool) {
	e.showLabels = show
}

// SetHighlight sets the equipment ID to highlight
func (e *EquipmentLayer) SetHighlight(equipmentID string) {
	e.highlightID = equipmentID
}

// SetSymbol sets a custom symbol for an equipment type
func (e *EquipmentLayer) SetSymbol(equipType string, symbol rune) {
	e.symbolMap[equipType] = symbol
}

// Render renders the equipment to the buffer
func (e *EquipmentLayer) Render(buffer [][]rune, viewport Viewport) {
	for _, equip := range e.equipment {
		e.renderEquipment(buffer, viewport, equip)
	}
}

// renderEquipment renders a single piece of equipment
func (e *EquipmentLayer) renderEquipment(buffer [][]rune, viewport Viewport, equip models.Equipment) {
	// Convert world coordinates to screen coordinates
	screenX := int((equip.Location.X - viewport.X) * viewport.Zoom)
	screenY := int((equip.Location.Y - viewport.Y) * viewport.Zoom)
	
	// Check if equipment is in viewport
	if screenX < 0 || screenX >= viewport.Width ||
		screenY < 0 || screenY >= viewport.Height {
		return
	}
	
	// Get the base symbol for this equipment type
	symbol, exists := e.symbolMap[equip.Type]
	if !exists {
		symbol = '•' // Default symbol
	}
	
	// Apply status indicator if needed
	if equip.Status != models.StatusOperational {
		statusChar := e.getStatusChar(equip.Status)
		if statusChar != StatusOperationalChar {
			// For failed/warning status, override the symbol
			if equip.Status == models.StatusFailed {
				symbol = StatusFailedChar
			} else if equip.Status == models.StatusDegraded {
				symbol = StatusWarningChar
			}
		}
	}
	
	// Highlight if this is the highlighted equipment
	if equip.ID == e.highlightID {
		// Draw highlight box around equipment
		e.drawHighlight(buffer, screenX, screenY)
	}
	
	// Set the equipment symbol
	if screenY >= 0 && screenY < len(buffer) && screenX >= 0 && screenX < len(buffer[screenY]) {
		buffer[screenY][screenX] = symbol
	}
	
	// Draw label if enabled
	if e.showLabels && equip.Name != "" {
		e.drawLabel(buffer, viewport, screenX, screenY, equip.Name)
	}
}

// getStatusChar returns the character representing equipment status
func (e *EquipmentLayer) getStatusChar(status string) rune {
	switch status {
	case models.StatusFailed:
		return StatusFailedChar
	case models.StatusDegraded:
		return StatusWarningChar
	case models.StatusUnknown:
		return StatusUnknownChar
	default:
		return StatusOperationalChar
	}
}

// drawHighlight draws a highlight box around a position
func (e *EquipmentLayer) drawHighlight(buffer [][]rune, x, y int) {
	// Draw brackets around the highlighted equipment
	if x > 0 && y >= 0 && y < len(buffer) && x-1 < len(buffer[y]) {
		buffer[y][x-1] = '['
	}
	if y >= 0 && y < len(buffer) && x+1 < len(buffer[y]) {
		buffer[y][x+1] = ']'
	}
}

// drawLabel draws a text label near equipment
func (e *EquipmentLayer) drawLabel(buffer [][]rune, viewport Viewport, x, y int, label string) {
	// Draw label below equipment if there's space
	labelY := y + 1
	if labelY >= viewport.Height {
		// Try above if no space below
		labelY = y - 1
		if labelY < 0 {
			return // No space for label
		}
	}
	
	// Center the label on the equipment
	labelRunes := []rune(label)
	startX := x - len(labelRunes)/2
	
	// Draw the label
	for i, ch := range labelRunes {
		labelX := startX + i
		if labelX >= 0 && labelX < viewport.Width && labelY >= 0 && labelY < len(buffer) {
			buffer[labelY][labelX] = ch
		}
	}
}

// GetEquipmentAt returns the equipment at the given world coordinates
func (e *EquipmentLayer) GetEquipmentAt(x, y float64) *models.Equipment {
	tolerance := 0.5 // How close to equipment position to count as "at"
	
	for i := range e.equipment {
		equip := &e.equipment[i]
		dx := equip.Location.X - x
		dy := equip.Location.Y - y
		if dx*dx+dy*dy <= tolerance*tolerance {
			return equip
		}
	}
	
	return nil
}

// Update can be used for animations (e.g., blinking failed equipment)
func (e *EquipmentLayer) Update(deltaTime float64) {
	// Could implement blinking animations for failed equipment here
	// For now, static rendering
}