package rendering

import (
	"fmt"
	"strings"

	"github.com/joelpate/arxos/pkg/models"
)

// TracingRenderer renders detailed system connections for systems engineers
// Focuses on power paths, network connections, HVAC flows, and fault analysis
type TracingRenderer struct {
	width  int
	height int
	config *RendererConfig
}

// TracingOptions configures system tracing rendering
type TracingOptions struct {
	SystemFilter     string // Filter to specific system (electrical, hvac, network)
	ShowPowerPaths   bool   // Show electrical power paths
	ShowNetworkPaths bool   // Show network connections
	ShowHVACPaths    bool   // Show HVAC air flow
	HighlightFaults  bool   // Highlight failed/warning equipment
	TraceFromID      string // Trace connections from specific equipment
}

// NewTracingRenderer creates a new tracing renderer
func NewTracingRenderer(config *RendererConfig) *TracingRenderer {
	return &TracingRenderer{
		width:  config.Width,
		height: config.Height,
		config: config,
	}
}

// RenderConnections renders system connections and traces
func (tr *TracingRenderer) RenderConnections(floorPlan *models.FloorPlan, options TracingOptions) (string, error) {
	var sb strings.Builder

	// Header
	sb.WriteString(tr.renderHeader(floorPlan, options))

	// System-specific rendering
	if options.SystemFilter != "" {
		sb.WriteString(tr.renderSpecificSystem(floorPlan, options))
	} else {
		sb.WriteString(tr.renderAllSystems(floorPlan, options))
	}

	// Connection tracing
	if options.TraceFromID != "" {
		sb.WriteString(tr.renderConnectionTrace(floorPlan, options.TraceFromID))
	}

	// Fault analysis
	if options.HighlightFaults {
		sb.WriteString(tr.renderFaultAnalysis(floorPlan))
	}

	return sb.String(), nil
}

// renderHeader renders the tracing view header
func (tr *TracingRenderer) renderHeader(floorPlan *models.FloorPlan, options TracingOptions) string {
	var sb strings.Builder

	title := fmt.Sprintf("%s - System Tracing", floorPlan.Name)
	sb.WriteString(fmt.Sprintf("%s\n", title))
	sb.WriteString(strings.Repeat("═", len(title)) + "\n")

	if options.SystemFilter != "" {
		sb.WriteString(fmt.Sprintf("System Filter: %s\n", strings.ToUpper(options.SystemFilter)))
	}

	if options.TraceFromID != "" {
		sb.WriteString(fmt.Sprintf("Tracing from: %s\n", options.TraceFromID))
	}

	sb.WriteString("\n")
	return sb.String()
}

// renderSpecificSystem renders a specific system (electrical, hvac, network)
func (tr *TracingRenderer) renderSpecificSystem(floorPlan *models.FloorPlan, options TracingOptions) string {
	var sb strings.Builder

	systemType := strings.ToLower(options.SystemFilter)
	sb.WriteString(fmt.Sprintf("%s System Analysis:\n", strings.ToTitle(systemType)))
	sb.WriteString(strings.Repeat("─", 40) + "\n")

	// Filter equipment by system type
	systemEquipment := tr.filterEquipmentBySystem(floorPlan.Equipment, systemType)

	if len(systemEquipment) == 0 {
		sb.WriteString(fmt.Sprintf("No %s equipment found.\n", systemType))
		return sb.String()
	}

	// Render system layout
	switch systemType {
	case "electrical":
		sb.WriteString(tr.renderElectricalSystem(systemEquipment))
	case "hvac":
		sb.WriteString(tr.renderHVACSystem(systemEquipment))
	case "network":
		sb.WriteString(tr.renderNetworkSystem(systemEquipment))
	default:
		sb.WriteString(tr.renderGenericSystem(systemEquipment, systemType))
	}

	return sb.String()
}

// renderAllSystems renders overview of all systems
func (tr *TracingRenderer) renderAllSystems(floorPlan *models.FloorPlan, options TracingOptions) string {
	var sb strings.Builder

	sb.WriteString("System Overview:\n")
	sb.WriteString(strings.Repeat("─", 20) + "\n")

	// Group equipment by system type
	systemGroups := tr.groupEquipmentBySystem(floorPlan.Equipment)

	for systemType, equipment := range systemGroups {
		operationalCount := 0
		faultCount := 0

		for _, eq := range equipment {
			switch eq.Status {
			case models.StatusOperational:
				operationalCount++
			case models.StatusFailed:
				faultCount++
			}
		}

		status := "✓"
		if faultCount > 0 {
			status = "⚠"
		}

		sb.WriteString(fmt.Sprintf("%s %-12s: %2d items (%d operational, %d faults)\n",
			status, strings.ToTitle(systemType), len(equipment), operationalCount, faultCount))
	}

	sb.WriteString("\n")
	return sb.String()
}

// renderElectricalSystem renders electrical power paths
func (tr *TracingRenderer) renderElectricalSystem(equipment []*models.Equipment) string {
	var sb strings.Builder

	sb.WriteString("Electrical Power Distribution:\n")

	// Find panels (power sources)
	panels := tr.findEquipmentByType(equipment, "panel")
	outlets := tr.findEquipmentByType(equipment, "outlet")

	sb.WriteString(fmt.Sprintf("  Panels: %d\n", len(panels)))
	sb.WriteString(fmt.Sprintf("  Outlets: %d\n", len(outlets)))

	// Simple power path visualization
	if len(panels) > 0 && len(outlets) > 0 {
		sb.WriteString("\nPower Paths:\n")
		for _, panel := range panels {
			sb.WriteString(fmt.Sprintf("  [%s] ──┬", panel.ID))

			// Show connections to outlets (simplified)
			connectedOutlets := 0
			for _, outlet := range outlets {
				if tr.areConnected(panel, outlet) {
					connectedOutlets++
				}
			}

			if connectedOutlets > 0 {
				sb.WriteString(fmt.Sprintf("── %d outlets\n", connectedOutlets))
			} else {
				sb.WriteString("── (no connections found)\n")
			}
		}
	}

	sb.WriteString("\n")
	return sb.String()
}

// renderHVACSystem renders HVAC air flow paths
func (tr *TracingRenderer) renderHVACSystem(equipment []*models.Equipment) string {
	var sb strings.Builder

	sb.WriteString("HVAC Air Distribution:\n")

	// Find HVAC components
	rtus := tr.findEquipmentByType(equipment, "rtu")
	vavs := tr.findEquipmentByType(equipment, "vav")

	sb.WriteString(fmt.Sprintf("  RTUs: %d\n", len(rtus)))
	sb.WriteString(fmt.Sprintf("  VAV Boxes: %d\n", len(vavs)))

	// Simple air flow visualization
	if len(rtus) > 0 {
		sb.WriteString("\nAir Flow Paths:\n")
		for _, rtu := range rtus {
			sb.WriteString(fmt.Sprintf("  [%s] ═══╤", rtu.ID))

			// Show connected VAVs
			connectedVAVs := 0
			for _, vav := range vavs {
				if tr.areConnected(rtu, vav) {
					connectedVAVs++
				}
			}

			if connectedVAVs > 0 {
				sb.WriteString(fmt.Sprintf("═══ %d VAV boxes\n", connectedVAVs))
			} else {
				sb.WriteString("═══ (no connections found)\n")
			}
		}
	}

	sb.WriteString("\n")
	return sb.String()
}

// renderNetworkSystem renders network topology
func (tr *TracingRenderer) renderNetworkSystem(equipment []*models.Equipment) string {
	var sb strings.Builder

	sb.WriteString("Network Topology:\n")

	// Find network components
	switches := tr.findEquipmentByType(equipment, "switch")
	aps := tr.findEquipmentByType(equipment, "access")

	sb.WriteString(fmt.Sprintf("  Switches: %d\n", len(switches)))
	sb.WriteString(fmt.Sprintf("  Access Points: %d\n", len(aps)))

	// Simple network topology
	if len(switches) > 0 {
		sb.WriteString("\nNetwork Connections:\n")
		for _, sw := range switches {
			sb.WriteString(fmt.Sprintf("  [%s] ─┬", sw.ID))

			// Show connected devices
			connectedDevices := 0
			for _, ap := range aps {
				if tr.areConnected(sw, ap) {
					connectedDevices++
				}
			}

			if connectedDevices > 0 {
				sb.WriteString(fmt.Sprintf("─ %d devices\n", connectedDevices))
			} else {
				sb.WriteString("─ (no connections found)\n")
			}
		}
	}

	sb.WriteString("\n")
	return sb.String()
}

// renderGenericSystem renders any other system type
func (tr *TracingRenderer) renderGenericSystem(equipment []*models.Equipment, systemType string) string {
	var sb strings.Builder

	sb.WriteString(fmt.Sprintf("%s System:\n", strings.ToTitle(systemType)))

	for _, eq := range equipment {
		statusSymbol := tr.getStatusSymbol(eq.Status)
		sb.WriteString(fmt.Sprintf("  %s %s (%s)\n", statusSymbol, eq.ID, eq.Status))
	}

	sb.WriteString("\n")
	return sb.String()
}

// renderConnectionTrace traces connections from a specific equipment
func (tr *TracingRenderer) renderConnectionTrace(floorPlan *models.FloorPlan, fromID string) string {
	var sb strings.Builder

	sb.WriteString(fmt.Sprintf("\nConnection Trace from %s:\n", fromID))
	sb.WriteString(strings.Repeat("─", 40) + "\n")

	// Find the source equipment
	var sourceEquipment *models.Equipment
	for _, eq := range floorPlan.Equipment {
		if eq.ID == fromID {
			sourceEquipment = eq
			break
		}
	}

	if sourceEquipment == nil {
		sb.WriteString(fmt.Sprintf("Equipment %s not found.\n", fromID))
		return sb.String()
	}

	// Trace connections (simplified - would need actual connection data)
	sb.WriteString(fmt.Sprintf("[%s] %s\n", sourceEquipment.ID, sourceEquipment.Name))
	sb.WriteString("  │\n")
	sb.WriteString("  ├─ Type: " + sourceEquipment.Type + "\n")
	sb.WriteString("  ├─ Status: " + sourceEquipment.Status + "\n")

	if sourceEquipment.Location != nil {
		sb.WriteString(fmt.Sprintf("  ├─ Location: (%.1f, %.1f)\n",
			sourceEquipment.Location.X, sourceEquipment.Location.Y))
	}

	sb.WriteString("  └─ Connected to: (connection tracing not yet implemented)\n")

	return sb.String()
}

// renderFaultAnalysis highlights equipment with issues
func (tr *TracingRenderer) renderFaultAnalysis(floorPlan *models.FloorPlan) string {
	var sb strings.Builder

	// Find equipment with issues
	var faultyEquipment []*models.Equipment
	for _, eq := range floorPlan.Equipment {
		if eq.Status == models.StatusFailed || strings.Contains(strings.ToLower(eq.Status), "warning") {
			faultyEquipment = append(faultyEquipment, eq)
		}
	}

	if len(faultyEquipment) == 0 {
		sb.WriteString("\n✓ No equipment faults detected.\n")
		return sb.String()
	}

	sb.WriteString(fmt.Sprintf("\n⚠ Equipment Issues (%d items):\n", len(faultyEquipment)))
	sb.WriteString(strings.Repeat("─", 30) + "\n")

	for _, eq := range faultyEquipment {
		statusSymbol := "⚠"
		if eq.Status == models.StatusFailed {
			statusSymbol = "✗"
		}

		sb.WriteString(fmt.Sprintf("  %s %s - %s\n", statusSymbol, eq.ID, eq.Status))
		if eq.Notes != "" {
			sb.WriteString(fmt.Sprintf("    Notes: %s\n", eq.Notes))
		}
	}

	return sb.String()
}

// Helper functions

// filterEquipmentBySystem filters equipment by system type
func (tr *TracingRenderer) filterEquipmentBySystem(equipment []*models.Equipment, systemType string) []*models.Equipment {
	var filtered []*models.Equipment
	for _, eq := range equipment {
		if strings.Contains(strings.ToLower(eq.Type), systemType) {
			filtered = append(filtered, eq)
		}
	}
	return filtered
}

// groupEquipmentBySystem groups equipment by system type
func (tr *TracingRenderer) groupEquipmentBySystem(equipment []*models.Equipment) map[string][]*models.Equipment {
	groups := make(map[string][]*models.Equipment)

	for _, eq := range equipment {
		systemType := tr.inferSystemType(eq.Type)
		groups[systemType] = append(groups[systemType], eq)
	}

	return groups
}

// findEquipmentByType finds equipment containing type keyword
func (tr *TracingRenderer) findEquipmentByType(equipment []*models.Equipment, typeKeyword string) []*models.Equipment {
	var found []*models.Equipment
	for _, eq := range equipment {
		if strings.Contains(strings.ToLower(eq.Type), typeKeyword) ||
			strings.Contains(strings.ToLower(eq.Name), typeKeyword) {
			found = append(found, eq)
		}
	}
	return found
}

// areConnected checks if two equipment items are connected (simplified)
func (tr *TracingRenderer) areConnected(eq1, eq2 *models.Equipment) bool {
	// This is a placeholder - would need actual connection data
	// For now, assume equipment in the same room might be connected
	if eq1.RoomID != "" && eq1.RoomID == eq2.RoomID {
		return true
	}
	return false
}

// inferSystemType infers system type from equipment type
func (tr *TracingRenderer) inferSystemType(equipmentType string) string {
	lowerType := strings.ToLower(equipmentType)
	switch {
	case strings.Contains(lowerType, "electrical") || strings.Contains(lowerType, "outlet") || strings.Contains(lowerType, "panel"):
		return "electrical"
	case strings.Contains(lowerType, "hvac") || strings.Contains(lowerType, "vav") || strings.Contains(lowerType, "rtu"):
		return "hvac"
	case strings.Contains(lowerType, "network") || strings.Contains(lowerType, "switch") || strings.Contains(lowerType, "access"):
		return "network"
	case strings.Contains(lowerType, "plumbing") || strings.Contains(lowerType, "valve") || strings.Contains(lowerType, "pump"):
		return "plumbing"
	case strings.Contains(lowerType, "fire") || strings.Contains(lowerType, "smoke") || strings.Contains(lowerType, "alarm"):
		return "fire_safety"
	case strings.Contains(lowerType, "security") || strings.Contains(lowerType, "camera") || strings.Contains(lowerType, "access_control"):
		return "security"
	default:
		return "other"
	}
}

// getStatusSymbol returns symbol for equipment status
func (tr *TracingRenderer) getStatusSymbol(status string) string {
	switch strings.ToLower(status) {
	case "operational", "normal":
		return "✓"
	case "warning", "degraded":
		return "⚠"
	case "failed", "error":
		return "✗"
	case "maintenance":
		return "🔧"
	case "offline":
		return "○"
	default:
		return "?"
	}
}
