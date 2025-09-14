package rendering

import (
	"fmt"
	"strings"
	
	"github.com/joelpate/arxos/pkg/models"
)

// RenderSchoolPlan creates an ASCII representation specifically for school floor plans
func RenderSchoolPlan(plan *models.FloorPlan) string {
	var sb strings.Builder
	
	// Header
	sb.WriteString(fmt.Sprintf("%s - %s\n", plan.Building, plan.Name))
	sb.WriteString("═══════════════════════════════════════════════════════════════\n")
	sb.WriteString("\n")
	
	// Create a simple grid layout
	// North wing (500s) on top, South wing (800s) on bottom
	// Central (600s) and Admin (300s) in middle
	
	sb.WriteString("┌─────────────────────────┬─────────────────────────┐\n")
	sb.WriteString("│    NORTH WING (500s)    │     CENTRAL (600s)      │\n")
	
	// Find and display equipment for each area
	northEquip := getEquipmentForRoom(plan, "north_wing")
	centralEquip := getEquipmentForRoom(plan, "central")
	
	sb.WriteString("│                         │                         │\n")
	sb.WriteString(fmt.Sprintf("│  %s%-21s │  %s%-21s │\n", 
		formatEquipment(northEquip), "",
		formatEquipment(centralEquip), ""))
	sb.WriteString("│                         │                         │\n")
	sb.WriteString("├─────────────────────────┼─────────────────────────┤\n")
	sb.WriteString("│    SOUTH WING (800s)    │      ADMIN (300s)       │\n")
	
	southEquip := getEquipmentForRoom(plan, "south_wing")
	adminEquip := getEquipmentForRoom(plan, "admin")
	
	sb.WriteString("│                         │                         │\n")
	sb.WriteString(fmt.Sprintf("│  %s%-21s │  %s%-21s │\n",
		formatEquipment(southEquip), "",
		formatEquipment(adminEquip), ""))
	sb.WriteString("│                         │                         │\n")
	sb.WriteString("└─────────────────────────┴─────────────────────────┘\n")
	sb.WriteString("\n")
	
	// Legend
	sb.WriteString("Network Equipment:\n")
	sb.WriteString("  ⚡ MDF (Main Distribution Frame)\n")
	sb.WriteString("  ◉ IDF (Intermediate Distribution Frame)\n")
	sb.WriteString("  ● Normal   ○ Needs Repair   ✗ Failed\n")
	sb.WriteString("\n")
	
	// Equipment List
	sb.WriteString("Equipment Status:\n")
	for _, equip := range plan.Equipment {
		if equip.Type == "idf" || equip.Type == "mdf" {
			status := "✓"
			if equip.Status == models.StatusDegraded {
				status = "⚠"
			} else if equip.Status == models.StatusFailed {
				status = "✗"
			}
			sb.WriteString(fmt.Sprintf("  [%s] %s - %s\n", status, equip.Name, equip.Status))
		}
	}
	
	return sb.String()
}

// getEquipmentForRoom finds equipment in a specific room
func getEquipmentForRoom(plan *models.FloorPlan, roomID string) []models.Equipment {
	var equipment []models.Equipment
	
	for _, room := range plan.Rooms {
		if room.ID == roomID {
			for _, equipID := range room.Equipment {
				for _, equip := range plan.Equipment {
					if equip.ID == equipID && (equip.Type == "idf" || equip.Type == "mdf") {
						equipment = append(equipment, equip)
					}
				}
			}
			break
		}
	}
	
	return equipment
}

// formatEquipment creates a display string for equipment
func formatEquipment(equipment []models.Equipment) string {
	if len(equipment) == 0 {
		return ""
	}
	
	var items []string
	for _, equip := range equipment {
		symbol := "◉"
		if equip.Type == "mdf" {
			symbol = "⚡"
		}
		
		// Add status indicator
		if equip.Status == models.StatusFailed {
			symbol = "✗"
		} else if equip.Status == models.StatusDegraded {
			symbol = "⚠"
		}
		
		items = append(items, fmt.Sprintf("%s %s", symbol, equip.Name))
	}
	
	return strings.Join(items, " ")
}