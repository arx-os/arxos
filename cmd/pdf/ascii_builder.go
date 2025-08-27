package pdf

import (
	"fmt"
	"path/filepath"
	"sort"
	"strings"

	"github.com/arxos/arxos/cmd/models"
)

// ASCIIBuilder creates ASCII-BIM visualizations from parsed data
type ASCIIBuilder struct {
	BuildingID string
	Objects    []*models.ArxObjectV2
	Width      int
	Height     int
}

// NewASCIIBuilder creates a new ASCII builder
func NewASCIIBuilder(buildingID string) *ASCIIBuilder {
	return &ASCIIBuilder{
		BuildingID: buildingID,
		Width:      80,
		Height:     40,
	}
}

// BuildElectricalRiser creates an electrical riser diagram
func (b *ASCIIBuilder) BuildElectricalRiser(objects []*models.ArxObjectV2) string {
	var sb strings.Builder
	
	// Find panels and organize hierarchy
	panels := []*models.ArxObjectV2{}
	breakersByPanel := make(map[string][]*models.ArxObjectV2)
	
	for _, obj := range objects {
		if obj.Type == "panel" {
			panels = append(panels, obj)
		} else if obj.Type == "breaker" {
			if len(obj.Relationships["fed_from"]) > 0 {
				panelID := obj.Relationships["fed_from"][0]
				breakersByPanel[panelID] = append(breakersByPanel[panelID], obj)
			}
		}
	}
	
	// Sort panels by ID for consistent display
	sort.Slice(panels, func(i, j int) bool {
		return panels[i].ID < panels[j].ID
	})
	
	sb.WriteString("\n═══ ELECTRICAL RISER DIAGRAM ═══\n\n")
	sb.WriteString("    🏢 Building Main Service\n")
	sb.WriteString("    │\n")
	sb.WriteString("    ├─⚡ Utility Transformer\n")
	sb.WriteString("    │   480V 3-Phase\n")
	sb.WriteString("    │\n")
	sb.WriteString("    └─📊 Main Distribution\n")
	
	// Display each panel
	for i, panel := range panels {
		isLast := (i == len(panels)-1)
		prefix := "        ├─"
		if isLast {
			prefix = "        └─"
		}
		
		voltage := 208
		if v, ok := panel.Properties["voltage"].(int); ok {
			voltage = v
		}
		
		panelName := panel.Properties["panel_name"]
		if panelName == nil {
			panelName = strings.ToUpper(filepath.Base(panel.ID))
		}
		
		sb.WriteString(fmt.Sprintf("%s 🔌 Panel %s (%dV)\n", prefix, panelName, voltage))
		
		// Show breakers
		breakers := breakersByPanel[panel.ID]
		if len(breakers) > 0 {
			// Sort breakers by number
			sort.Slice(breakers, func(i, j int) bool {
				num1, _ := breakers[i].Properties["number"].(int)
				num2, _ := breakers[j].Properties["number"].(int)
				return num1 < num2
			})
			
			// Show first few breakers
			maxShow := 5
			if len(breakers) < maxShow {
				maxShow = len(breakers)
			}
			
			for j, breaker := range breakers[:maxShow] {
				num := breaker.Properties["number"]
				desc := breaker.Properties["description"]
				amp := breaker.Properties["amperage"]
				
				indent := "        │   "
				if isLast {
					indent = "            "
				}
				
				breakerPrefix := "├─"
				if j == maxShow-1 && len(breakers) == maxShow {
					breakerPrefix = "└─"
				}
				
				sb.WriteString(fmt.Sprintf("%s%s [%2d] %dA - %s\n", 
					indent, breakerPrefix, num, amp, desc))
			}
			
			if len(breakers) > maxShow {
				indent := "        │   "
				if isLast {
					indent = "            "
				}
				sb.WriteString(fmt.Sprintf("%s└─ ... %d more breakers\n", 
					indent, len(breakers)-maxShow))
			}
		}
		
		if !isLast {
			sb.WriteString("        │\n")
		}
	}
	
	return sb.String()
}

// BuildFloorPlan creates an ASCII floor plan
func (b *ASCIIBuilder) BuildFloorPlan(objects []*models.ArxObjectV2) string {
	var sb strings.Builder
	
	// Group objects by floor
	floorRooms := make(map[string][]*models.ArxObjectV2)
	floorEquipment := make(map[string][]*models.ArxObjectV2)
	
	for _, obj := range objects {
		if obj.System == "spatial" && obj.Type == "room" {
			floor := "1"
			if f, ok := obj.Properties["floor"].(string); ok {
				floor = f
			}
			floorRooms[floor] = append(floorRooms[floor], obj)
		} else if obj.SpatialLocation != "" {
			// Extract floor from spatial location
			parts := strings.Split(obj.SpatialLocation, "/")
			for _, part := range parts {
				if strings.HasPrefix(part, "f") {
					floor := strings.TrimPrefix(part, "f")
					floorEquipment[floor] = append(floorEquipment[floor], obj)
					break
				}
			}
		}
	}
	
	// Build floor plan for each floor
	floors := []string{}
	for floor := range floorRooms {
		floors = append(floors, floor)
	}
	sort.Strings(floors)
	
	for _, floor := range floors {
		rooms := floorRooms[floor]
		equipment := floorEquipment[floor]
		
		sb.WriteString(fmt.Sprintf("\n═══ FLOOR %s PLAN ═══\n\n", floor))
		
		// Create simple grid layout
		sb.WriteString(b.createFloorGrid(rooms, equipment))
		
		// List rooms
		if len(rooms) > 0 {
			sb.WriteString("\nROOMS:\n")
			sort.Slice(rooms, func(i, j int) bool {
				num1 := rooms[i].Properties["number"].(string)
				num2 := rooms[j].Properties["number"].(string)
				return num1 < num2
			})
			
			for _, room := range rooms {
				num := room.Properties["number"]
				name := room.Properties["name"]
				area := room.Properties["area_sqft"]
				sb.WriteString(fmt.Sprintf("  • Room %s: %s (%d sq ft)\n", num, name, area))
			}
		}
		
		// List equipment on this floor
		if len(equipment) > 0 {
			sb.WriteString("\nEQUIPMENT:\n")
			
			// Group by system
			bySys := make(map[string][]*models.ArxObjectV2)
			for _, eq := range equipment {
				bySys[eq.System] = append(bySys[eq.System], eq)
			}
			
			systems := []string{}
			for sys := range bySys {
				systems = append(systems, sys)
			}
			sort.Strings(systems)
			
			for _, sys := range systems {
				items := bySys[sys]
				sb.WriteString(fmt.Sprintf("  %s:\n", strings.ToUpper(sys)))
				for _, item := range items {
					tag := item.Name
					if t, ok := item.Properties["tag"].(string); ok {
						tag = t
					}
					sb.WriteString(fmt.Sprintf("    - %s\n", tag))
				}
			}
		}
	}
	
	return sb.String()
}

// createFloorGrid creates a simple ASCII grid representation
func (b *ASCIIBuilder) createFloorGrid(rooms, equipment []*models.ArxObjectV2) string {
	// Create a simple representation
	// This is a basic version - could be enhanced with actual coordinates
	
	grid := [][]rune{}
	gridWidth := 60
	gridHeight := 20
	
	// Initialize grid
	for y := 0; y < gridHeight; y++ {
		row := make([]rune, gridWidth)
		for x := 0; x < gridWidth; x++ {
			if y == 0 || y == gridHeight-1 {
				row[x] = '═'
			} else if x == 0 || x == gridWidth-1 {
				row[x] = '║'
			} else {
				row[x] = ' '
			}
		}
		grid = append(grid, row)
	}
	
	// Fix corners
	grid[0][0] = '╔'
	grid[0][gridWidth-1] = '╗'
	grid[gridHeight-1][0] = '╚'
	grid[gridHeight-1][gridWidth-1] = '╝'
	
	// Place rooms (simplified - just divide into grid)
	if len(rooms) > 0 {
		// Simple 3x3 room layout
		roomWidth := (gridWidth - 2) / 3
		roomHeight := (gridHeight - 2) / 3
		
		roomIdx := 0
		for row := 0; row < 3 && roomIdx < len(rooms); row++ {
			for col := 0; col < 3 && roomIdx < len(rooms); col++ {
				room := rooms[roomIdx]
				roomNum := "?"
				if n, ok := room.Properties["number"].(string); ok {
					roomNum = n
				}
				
				// Draw room boundaries
				startX := 1 + col*roomWidth
				startY := 1 + row*roomHeight
				
				// Draw room number in center
				if len(roomNum) <= 3 {
					centerX := startX + roomWidth/2 - len(roomNum)/2
					centerY := startY + roomHeight/2
					
					for i, ch := range roomNum {
						if centerY < gridHeight-1 && centerX+i < gridWidth-1 {
							grid[centerY][centerX+i] = ch
						}
					}
				}
				
				// Draw room dividers
				if col < 2 {
					// Vertical divider
					for y := startY; y < startY+roomHeight && y < gridHeight-1; y++ {
						if startX+roomWidth < gridWidth {
							grid[y][startX+roomWidth] = '│'
						}
					}
				}
				if row < 2 {
					// Horizontal divider
					for x := startX; x < startX+roomWidth && x < gridWidth-1; x++ {
						if startY+roomHeight < gridHeight {
							grid[startY+roomHeight][x] = '─'
						}
					}
				}
				
				roomIdx++
			}
		}
	}
	
	// Convert grid to string
	var sb strings.Builder
	for _, row := range grid {
		sb.WriteString(string(row))
		sb.WriteString("\n")
	}
	
	return sb.String()
}

// BuildSystemDiagram creates a system interconnection diagram
func (b *ASCIIBuilder) BuildSystemDiagram(objects []*models.ArxObjectV2) string {
	var sb strings.Builder
	
	sb.WriteString("\n═══ SYSTEM INTERCONNECTIONS ═══\n\n")
	
	// Find HVAC equipment and their power sources
	hvacEquipment := []*models.ArxObjectV2{}
	for _, obj := range objects {
		if obj.System == "hvac" {
			hvacEquipment = append(hvacEquipment, obj)
		}
	}
	
	if len(hvacEquipment) > 0 {
		sb.WriteString("HVAC EQUIPMENT POWER REQUIREMENTS:\n\n")
		
		for _, equip := range hvacEquipment {
			tag := equip.Name
			if t, ok := equip.Properties["tag"].(string); ok {
				tag = t
			}
			
			sb.WriteString(fmt.Sprintf("🌡️ %s\n", tag))
			
			// Show power requirements
			if equip.PowerLoad != nil && equip.PowerLoad.Power > 0 {
				kw := equip.PowerLoad.Power / 1000
				sb.WriteString(fmt.Sprintf("   └─⚡ Power: %.1f kW\n", kw))
			} else if hp, ok := equip.Properties["horsepower"].(float64); ok {
				sb.WriteString(fmt.Sprintf("   └─⚡ Power: %.1f HP (%.1f kW)\n", hp, hp*0.746))
			} else if kw, ok := equip.Properties["power_kw"].(float64); ok {
				sb.WriteString(fmt.Sprintf("   └─⚡ Power: %.1f kW\n", kw))
			}
			
			// Show airflow for HVAC
			if cfm, ok := equip.Properties["airflow_cfm"].(int); ok {
				sb.WriteString(fmt.Sprintf("   └─💨 Airflow: %d CFM\n", cfm))
			}
			
			// Show if it needs special power
			if equip.Type == "air_handler" || strings.Contains(equip.Type, "rtu") {
				sb.WriteString("   └─🔌 Requires: 208V 3-Phase Circuit\n")
			}
			
			sb.WriteString("\n")
		}
	}
	
	// Summary statistics
	sb.WriteString("\n═══ BUILDING SUMMARY ═══\n\n")
	
	// Count by system
	systemCounts := make(map[string]int)
	for _, obj := range objects {
		systemCounts[obj.System]++
	}
	
	sb.WriteString("SYSTEMS IDENTIFIED:\n")
	systems := []string{}
	for sys := range systemCounts {
		systems = append(systems, sys)
	}
	sort.Strings(systems)
	
	for _, sys := range systems {
		count := systemCounts[sys]
		emoji := ""
		switch sys {
		case "electrical":
			emoji = "⚡"
		case "hvac":
			emoji = "🌡️"
		case "plumbing":
			emoji = "💧"
		case "spatial":
			emoji = "🏢"
		default:
			emoji = "•"
		}
		
		sb.WriteString(fmt.Sprintf("  %s %-12s: %3d objects\n", emoji, strings.Title(sys), count))
	}
	
	// Calculate total electrical load
	totalLoad := 0.0
	for _, obj := range objects {
		if obj.PowerLoad != nil {
			totalLoad += obj.PowerLoad.Power
		}
	}
	
	if totalLoad > 0 {
		sb.WriteString(fmt.Sprintf("\nTOTAL ELECTRICAL LOAD: %.1f kW\n", totalLoad/1000))
	}
	
	return sb.String()
}

// BuildFullVisualization creates complete ASCII-BIM visualization
func (b *ASCIIBuilder) BuildFullVisualization(objects []*models.ArxObjectV2) string {
	var sb strings.Builder
	
	sb.WriteString("\n")
	sb.WriteString("╔═══════════════════════════════════════════════════════════╗\n")
	sb.WriteString(fmt.Sprintf("║            ASCII-BIM: %s                    ║\n", b.BuildingID))
	sb.WriteString("╚═══════════════════════════════════════════════════════════╝\n")
	
	// Add electrical riser
	electricalObjs := filterBySystem(objects, "electrical")
	if len(electricalObjs) > 0 {
		sb.WriteString(b.BuildElectricalRiser(electricalObjs))
	}
	
	// Add floor plans
	sb.WriteString(b.BuildFloorPlan(objects))
	
	// Add system diagram
	sb.WriteString(b.BuildSystemDiagram(objects))
	
	return sb.String()
}

// filterBySystem filters objects by system type
func filterBySystem(objects []*models.ArxObjectV2, system string) []*models.ArxObjectV2 {
	filtered := []*models.ArxObjectV2{}
	for _, obj := range objects {
		if obj.System == system {
			filtered = append(filtered, obj)
		}
	}
	return filtered
}

