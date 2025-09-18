package charts

import (
	"fmt"
	"strings"

	"github.com/arx-os/arxos/internal/visualization/core"
)

// TreeNode represents a node in a tree structure
type TreeNode struct {
	Label    string
	Value    interface{}
	Status   string
	Children []*TreeNode
	Expanded bool
	Metadata map[string]string
}

// TreeData represents hierarchical data for tree visualization
type TreeData struct {
	Root      *TreeNode
	Title     string
	ShowIcons bool
	ShowValue bool
	MaxDepth  int
}

// GetType implements DataSet interface
func (t *TreeData) GetType() string {
	return "tree"
}

// Validate implements DataSet interface
func (t *TreeData) Validate() error {
	if t.Root == nil {
		return fmt.Errorf("no root node provided")
	}
	return nil
}

// TreeView renders hierarchical tree structures
type TreeView struct {
	renderer *core.TerminalRenderer
}

// NewTreeView creates a new tree view renderer
func NewTreeView() *TreeView {
	return &TreeView{
		renderer: core.NewTerminalRenderer(),
	}
}

// Render renders a tree view
func (tv *TreeView) Render(data *TreeData, options core.RenderOptions) string {
	if err := data.Validate(); err != nil {
		return fmt.Sprintf("Error: %v", err)
	}

	// Apply defaults
	if options.SymbolSet.IsEmpty() {
		if tv.renderer.SupportsUnicode() {
			options.SymbolSet = core.UnicodeSymbols
		} else {
			options.SymbolSet = core.ASCIISymbols
		}
	}

	if options.ColorScheme.IsEmpty() {
		if tv.renderer.SupportsColors() {
			options.ColorScheme = core.DefaultColorScheme
		} else {
			options.ColorScheme = core.MonochromeScheme
		}
	}

	var output strings.Builder

	// Render title
	if data.Title != "" {
		output.WriteString(data.Title)
		output.WriteString("\n")
		output.WriteString(strings.Repeat("─", len(data.Title)))
		output.WriteString("\n\n")
	}

	// Render tree
	tv.renderNode(&output, data.Root, "", true, 0, data.MaxDepth, data.ShowIcons, data.ShowValue, options)

	return output.String()
}

// renderNode recursively renders a tree node
func (tv *TreeView) renderNode(output *strings.Builder, node *TreeNode, prefix string, isLast bool, depth int, maxDepth int, showIcons bool, showValue bool, options core.RenderOptions) {
	if maxDepth > 0 && depth >= maxDepth {
		return
	}

	// Determine connector symbols
	var connector, childPrefix string
	if depth == 0 {
		// Root node
		connector = ""
		childPrefix = ""
	} else {
		if isLast {
			connector = string(options.SymbolSet.TreeEnd) + " "
			childPrefix = "  "
		} else {
			connector = string(options.SymbolSet.TreeMid) + " "
			childPrefix = string(options.SymbolSet.TreeVert) + " "
		}
	}

	// Build node line
	output.WriteString(prefix)
	output.WriteString(connector)

	// Add status icon if enabled
	if showIcons {
		icon := tv.getStatusIcon(node.Status, options.SymbolSet)
		output.WriteString(string(icon))
		output.WriteString(" ")
	}

	// Add label
	output.WriteString(node.Label)

	// Add value if enabled
	if showValue && node.Value != nil {
		output.WriteString(fmt.Sprintf(" (%v)", node.Value))
	}

	// Add metadata if present
	if len(node.Metadata) > 0 {
		output.WriteString(" [")
		first := true
		for k, v := range node.Metadata {
			if !first {
				output.WriteString(", ")
			}
			output.WriteString(fmt.Sprintf("%s: %s", k, v))
			first = false
		}
		output.WriteString("]")
	}

	output.WriteString("\n")

	// Render children
	if node.Expanded || depth < 2 { // Auto-expand first 2 levels
		for i, child := range node.Children {
			isLastChild := i == len(node.Children)-1
			tv.renderNode(output, child, prefix+childPrefix, isLastChild, depth+1, maxDepth, showIcons, showValue, options)
		}
	} else if len(node.Children) > 0 {
		// Show collapsed indicator
		output.WriteString(prefix)
		output.WriteString(childPrefix)
		output.WriteString("  ")
		output.WriteString(fmt.Sprintf("... (%d children)", len(node.Children)))
		output.WriteString("\n")
	}
}

// getStatusIcon returns the appropriate icon for a status
func (tv *TreeView) getStatusIcon(status string, symbols core.SymbolSet) rune {
	switch status {
	case "operational", "success", "ok", "healthy":
		return symbols.CheckMark
	case "warning", "maintenance", "degraded":
		return symbols.Warning
	case "error", "failed", "critical", "down":
		return symbols.Error
	case "info", "unknown":
		return symbols.Info
	default:
		return symbols.Bullet
	}
}

// RenderBuildingHierarchy renders a building's hierarchical structure
func RenderBuildingHierarchy(buildingID string) string {
	tree := NewTreeView()

	// Create sample building hierarchy
	root := &TreeNode{
		Label:  buildingID,
		Status: "operational",
		Metadata: map[string]string{
			"type":   "building",
			"floors": "5",
		},
		Children: []*TreeNode{
			{
				Label:  "Power System",
				Status: "operational",
				Children: []*TreeNode{
					{Label: "Main Panel", Status: "operational", Value: "480V"},
					{Label: "Backup Generator", Status: "operational", Value: "500kW"},
					{Label: "UPS Systems", Status: "operational", Children: []*TreeNode{
						{Label: "UPS-1", Status: "operational", Value: "20kVA"},
						{Label: "UPS-2", Status: "operational", Value: "20kVA"},
					}},
				},
			},
			{
				Label:  "HVAC System",
				Status: "warning",
				Children: []*TreeNode{
					{Label: "Chiller-1", Status: "operational", Value: "100 tons"},
					{Label: "Chiller-2", Status: "maintenance", Value: "100 tons"},
					{Label: "AHU Units", Status: "operational", Children: []*TreeNode{
						{Label: "AHU-01", Status: "operational", Value: "Floor 1-2"},
						{Label: "AHU-02", Status: "operational", Value: "Floor 3-4"},
						{Label: "AHU-03", Status: "operational", Value: "Floor 5"},
					}},
				},
			},
			{
				Label:  "Water System",
				Status: "operational",
				Children: []*TreeNode{
					{Label: "Domestic Water", Status: "operational", Value: "60 PSI"},
					{Label: "Fire Suppression", Status: "operational", Value: "Ready"},
					{Label: "Cooling Tower", Status: "operational", Value: "Active"},
				},
			},
			{
				Label:  "Security System",
				Status: "operational",
				Children: []*TreeNode{
					{Label: "Access Control", Status: "operational", Value: "142 doors"},
					{Label: "CCTV", Status: "operational", Value: "84 cameras"},
					{Label: "Fire Alarm", Status: "operational", Value: "Armed"},
				},
			},
		},
	}

	data := &TreeData{
		Root:      root,
		Title:     fmt.Sprintf("Building System Hierarchy - %s", buildingID),
		ShowIcons: true,
		ShowValue: true,
		MaxDepth:  0, // No limit
	}

	options := core.RenderOptions{
		Width:  80,
		Height: 40,
	}

	return tree.Render(data, options)
}

// RenderEquipmentTree renders equipment hierarchy for a floor
func RenderEquipmentTree(buildingID string, floor int) string {
	tree := NewTreeView()

	root := &TreeNode{
		Label:  fmt.Sprintf("%s - Floor %d", buildingID, floor),
		Status: "operational",
		Children: []*TreeNode{
			{
				Label:  "Zone A",
				Status: "operational",
				Children: []*TreeNode{
					{
						Label:  "Room A101",
						Status: "operational",
						Children: []*TreeNode{
							{Label: "OUTLET-A101-01", Status: "operational", Value: "120V"},
							{Label: "OUTLET-A101-02", Status: "operational", Value: "120V"},
							{Label: "SWITCH-A101-01", Status: "operational", Value: "3-way"},
						},
					},
					{
						Label:  "Room A102",
						Status: "warning",
						Children: []*TreeNode{
							{Label: "OUTLET-A102-01", Status: "maintenance", Value: "120V"},
							{Label: "THERMOSTAT-A102", Status: "operational", Value: "72°F"},
						},
					},
				},
			},
			{
				Label:  "Zone B",
				Status: "operational",
				Children: []*TreeNode{
					{
						Label:  "Conference Room B101",
						Status: "operational",
						Children: []*TreeNode{
							{Label: "AV-SYSTEM", Status: "operational", Value: "Ready"},
							{Label: "LIGHTING-B101", Status: "operational", Value: "Dimmer"},
							{Label: "HVAC-VAV-B101", Status: "operational", Value: "Auto"},
						},
					},
				},
			},
		},
	}

	data := &TreeData{
		Root:      root,
		Title:     "Equipment Hierarchy",
		ShowIcons: true,
		ShowValue: true,
	}

	options := core.RenderOptions{}
	return tree.Render(data, options)
}

// RenderDependencyTree renders system dependencies
func RenderDependencyTree(component string) string {
	tree := NewTreeView()

	root := &TreeNode{
		Label:  component,
		Status: "info",
		Metadata: map[string]string{
			"type": "target",
		},
		Children: []*TreeNode{
			{
				Label:  "Depends On",
				Status: "info",
				Children: []*TreeNode{
					{Label: "PANEL-A", Status: "operational", Value: "Power"},
					{Label: "SWITCH-MAIN", Status: "operational", Value: "Control"},
					{Label: "BREAKER-15", Status: "operational", Value: "Protection"},
				},
			},
			{
				Label:  "Affects",
				Status: "info",
				Children: []*TreeNode{
					{Label: "WORKSTATION-01", Status: "operational", Value: "Device"},
					{Label: "WORKSTATION-02", Status: "operational", Value: "Device"},
					{Label: "PRINTER-SHARED", Status: "operational", Value: "Device"},
				},
			},
			{
				Label:  "Related Systems",
				Status: "info",
				Children: []*TreeNode{
					{Label: "Emergency Lighting", Status: "operational"},
					{Label: "UPS Backup", Status: "operational"},
				},
			},
		},
	}

	data := &TreeData{
		Root:      root,
		Title:     fmt.Sprintf("Dependency Analysis - %s", component),
		ShowIcons: true,
		ShowValue: true,
	}

	options := core.RenderOptions{}
	return tree.Render(data, options)
}

// Example usage
func ExampleTreeView() {
	tree := NewTreeView()

	// Sample organizational tree
	root := &TreeNode{
		Label:  "ArxOS System",
		Status: "operational",
		Children: []*TreeNode{
			{
				Label:  "Database",
				Status: "operational",
				Children: []*TreeNode{
					{Label: "SQLite", Status: "operational", Value: "Primary"},
					{Label: "PostGIS", Status: "operational", Value: "Spatial"},
				},
			},
			{
				Label:  "Services",
				Status: "operational",
				Children: []*TreeNode{
					{Label: "API Server", Status: "operational", Value: "Port 8080"},
					{Label: "File Watcher", Status: "operational", Value: "Active"},
					{Label: "Import Pipeline", Status: "operational", Value: "Ready"},
				},
			},
			{
				Label:  "Interfaces",
				Status: "operational",
				Children: []*TreeNode{
					{Label: "Terminal CLI", Status: "operational"},
					{Label: "HTMX Web", Status: "operational"},
					{Label: "REST API", Status: "operational"},
				},
			},
		},
	}

	data := &TreeData{
		Root:      root,
		Title:     "System Architecture",
		ShowIcons: true,
		ShowValue: true,
	}

	options := core.RenderOptions{}
	fmt.Println(tree.Render(data, options))
}

// BuildNodeFromPath creates a tree node from a universal path
func BuildNodeFromPath(path string) *TreeNode {
	parts := strings.Split(path, "/")
	if len(parts) == 0 {
		return nil
	}

	root := &TreeNode{
		Label:  parts[0],
		Status: "operational",
	}

	current := root
	for i := 1; i < len(parts); i++ {
		child := &TreeNode{
			Label:  parts[i],
			Status: "operational",
		}
		current.Children = append(current.Children, child)
		current = child
	}

	return root
}
