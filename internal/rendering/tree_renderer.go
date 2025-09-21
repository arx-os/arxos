package rendering

import (
	"fmt"
	"strings"

	"github.com/arx-os/arxos/internal/bim"
	"github.com/arx-os/arxos/internal/core/user"
)

// TreeRenderer renders .bim.txt files as a hierarchical tree structure
// Access control determines what parts are visible based on user role
type TreeRenderer struct {
	showStatus bool
	indent     string
}

// NewTreeRenderer creates a new tree renderer
func NewTreeRenderer() *TreeRenderer {
	return &TreeRenderer{
		showStatus: true,
		indent:     "  ",
	}
}

// RenderBuilding renders a building as a tree, filtered by user permissions
func (r *TreeRenderer) RenderBuilding(building *bim.Building, user *user.User) (string, error) {
	if building == nil {
		return "", fmt.Errorf("building data required")
	}

	var sb strings.Builder

	// Building root
	sb.WriteString(fmt.Sprintf("Building: %s\n", building.Name))
	// Address is in metadata if available
	if building.Metadata.Location.Address != "" && r.canViewAddress(user) {
		sb.WriteString(fmt.Sprintf("Address: %s\n", building.Metadata.Location.Address))
	}

	// Render floors based on access
	for _, floor := range building.Floors {
		if !r.canViewFloor(user, building.Name, floor.Level) {
			continue
		}
		r.renderFloor(&sb, floor, user, "├── ")
	}

	return sb.String(), nil
}

// renderFloor renders a floor and its contents
func (r *TreeRenderer) renderFloor(sb *strings.Builder, floor bim.Floor, user *user.User, prefix string) {
	sb.WriteString(fmt.Sprintf("%sFloor %d: %s\n", prefix, floor.Level, floor.Name))

	// Determine if this is the last floor for proper tree formatting
	roomPrefix := strings.Replace(prefix, "├── ", "│   ", 1)

	// Rooms are represented in the floor layout
	for i := range floor.Equipment {
		// Skip if user can't view this equipment
		if !r.canViewEquipment(user, floor.Equipment[i].ID) {
			continue
		}

		isLastRoom := i == len(floor.Equipment)-1
		roomBranch := "├── "
		if isLastRoom {
			roomBranch = "└── "
		}

		r.renderEquipment(sb, floor.Equipment[i], user, roomPrefix+roomBranch)
	}
}

// renderEquipmentItem renders a single equipment item from a floor
func (r *TreeRenderer) renderEquipmentItem(sb *strings.Builder, eq bim.Equipment, user *user.User, prefix string) {
	sb.WriteString(fmt.Sprintf("%s%s", prefix, eq.ID))
	if eq.Type != "" {
		sb.WriteString(fmt.Sprintf(" [%s]", eq.Type))
	}
	sb.WriteString("\n")
}

// renderEquipment renders a single equipment item
func (r *TreeRenderer) renderEquipment(sb *strings.Builder, eq bim.Equipment, user *user.User, prefix string) {
	sb.WriteString(fmt.Sprintf("%s%s", prefix, eq.ID))

	if eq.Type != "" {
		sb.WriteString(fmt.Sprintf(" [%s]", eq.Type))
	}

	if r.showStatus && eq.Status != "" {
		status := r.formatStatus(string(eq.Status))
		sb.WriteString(fmt.Sprintf(" [%s]", status))
	}

	// Show coordinates only for technicians and above
	if r.canViewCoordinates(user) && eq.Location.X > 0 && eq.Location.Y > 0 {
		sb.WriteString(fmt.Sprintf(" @(%.1f,%.1f)", eq.Location.X, eq.Location.Y))
	}

	sb.WriteString("\n")
}

// Permission checking methods based on user role

func (r *TreeRenderer) canViewAddress(user *user.User) bool {
	// Everyone can see address
	return true
}

func (r *TreeRenderer) canViewFloor(user *user.User, buildingID string, floorNumber int) bool {
	switch user.Role {
	case "admin":
		return true // Admin sees all
	case "manager":
		// TODO: Check if user manages this building
		return true
	case "technician":
		// TODO: Check if technician is assigned to this floor
		return true
	case "viewer":
		return true // Viewers can see structure, just not modify
	default:
		return false
	}
}

func (r *TreeRenderer) canViewRoom(user *user.User, roomNumber string) bool {
	// Similar logic to floor
	// Could be more granular based on assignment
	return true
}

func (r *TreeRenderer) canViewEquipment(user *user.User, equipmentType string) bool {
	switch user.Role {
	case "admin", "manager":
		return true // See all equipment
	case "technician":
		// Technicians might only see equipment for their specialization
		// e.g., electrical tech only sees electrical equipment
		return r.isAssignedSystem(user, equipmentType)
	case "viewer":
		return true // Can view but not modify
	default:
		return false
	}
}

func (r *TreeRenderer) canViewCoordinates(user *user.User) bool {
	// Only technicians and above see precise coordinates
	return user.Role == "admin" ||
	       user.Role == "manager" ||
	       user.Role == "technician"
}

func (r *TreeRenderer) isAssignedSystem(user *user.User, equipmentType string) bool {
	// TODO: Check user's assigned systems against equipment type
	// For now, return true
	return true
}

func (r *TreeRenderer) formatStatus(status string) string {
	switch strings.ToUpper(status) {
	case "OK", "OPERATIONAL", "ACTIVE":
		return "OK"
	case "FAILED", "ERROR", "FAULT":
		return "FAILED"
	case "WARNING", "DEGRADED":
		return "WARN"
	case "OFFLINE", "DISABLED":
		return "OFFLINE"
	default:
		return "UNKNOWN"
	}
}