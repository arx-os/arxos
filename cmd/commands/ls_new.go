package commands

import (
	"fmt"
	"sort"
	"strings"

	"github.com/arxos/arxos/cmd/models"
	"github.com/arxos/arxos/cmd/navigation"
	"github.com/spf13/cobra"
)

// LsCmd lists contents of current or specified directory
var LsCmd = &cobra.Command{
	Use:   "ls [path]",
	Short: "List building components at current or specified location",
	Long: `List the contents of the current location or a specified path
in the building filesystem, showing components and their properties.

Examples:
  arxos ls                                    # List current directory
  arxos ls /electrical                        # List electrical system
  arxos ls -l /electrical/main-panel         # Long format with details
  arxos ls /electrical/main-panel/circuit-7   # List specific circuit`,
	RunE: runLs,
}

func init() {
	LsCmd.Flags().BoolP("long", "l", false, "Use long listing format")
	LsCmd.Flags().BoolP("all", "a", false, "Show all items including hidden")
	LsCmd.Flags().BoolP("tree", "t", false, "Show as tree structure")
	LsCmd.Flags().BoolP("properties", "p", false, "Show object properties")
}

func runLs(cmd *cobra.Command, args []string) error {
	// Get navigation context
	ctx := navigation.GetContext()
	
	// Determine target path
	targetPath := ctx.GetCurrentPath()
	if len(args) > 0 {
		if strings.HasPrefix(args[0], "/") {
			targetPath = args[0]
		} else {
			targetPath = ctx.GetRelativePath(args[0])
		}
	}
	targetPath = navigation.NormalizePath(targetPath)
	
	// Get flags
	longFormat, _ := cmd.Flags().GetBool("long")
	showProperties, _ := cmd.Flags().GetBool("properties")
	treeFormat, _ := cmd.Flags().GetBool("tree")
	
	// Get contents for the path
	contents := getContentsForPath(targetPath)
	
	// Display based on format
	if treeFormat {
		displayTree(targetPath, contents, 0)
	} else if longFormat || showProperties {
		displayLongFormat(targetPath, contents)
	} else {
		displaySimpleFormat(contents)
	}
	
	return nil
}

// Mock function to get contents - in production would query store
func getContentsForPath(path string) []models.ArxObjectV2 {
	contents := []models.ArxObjectV2{}
	
	switch path {
	case "/":
		contents = []models.ArxObjectV2{
			{ID: "electrical", Type: "system", Name: "electrical", Properties: map[string]interface{}{"description": "Electrical distribution system"}},
			{ID: "hvac", Type: "system", Name: "hvac", Properties: map[string]interface{}{"description": "HVAC system"}},
			{ID: "plumbing", Type: "system", Name: "plumbing", Properties: map[string]interface{}{"description": "Plumbing infrastructure"}},
			{ID: "structural", Type: "system", Name: "structural", Properties: map[string]interface{}{"description": "Structural elements"}},
			{ID: "floors", Type: "system", Name: "floors", Properties: map[string]interface{}{"description": "Building floors"}},
		}
		
	case "/electrical":
		contents = []models.ArxObjectV2{
			{ID: "main-panel", Type: "panel", Name: "main-panel", Properties: map[string]interface{}{
				"voltage": "480V", "phase": "3-phase", "circuits": 42, "total_load": "285.7A",
			}},
			{ID: "sub-panel-a", Type: "panel", Name: "sub-panel-a", Properties: map[string]interface{}{
				"voltage": "208V", "phase": "3-phase", "circuits": 24,
			}},
			{ID: "sub-panel-b", Type: "panel", Name: "sub-panel-b", Properties: map[string]interface{}{
				"voltage": "208V", "phase": "single", "circuits": 12,
			}},
		}
		
	case "/electrical/main-panel":
		// Generate circuits
		for i := 1; i <= 10; i++ {
			contents = append(contents, models.ArxObjectV2{
				ID:   fmt.Sprintf("circuit-%d", i),
				Type: "circuit",
				Name: fmt.Sprintf("circuit-%d", i),
				Properties: map[string]interface{}{
					"breaker_rating": "20A",
					"current_load":   fmt.Sprintf("%.1fA", float64(8+i%5)),
					"voltage":        "120V",
					"status":         "active",
				},
			})
		}
		
	case "/electrical/main-panel/circuit-7":
		contents = []models.ArxObjectV2{
			{ID: "outlet-1", Type: "outlet", Name: "outlet-1", Properties: map[string]interface{}{
				"voltage": "120V", "load": "3.2A", "confidence": 0.95,
			}},
			{ID: "outlet-2", Type: "outlet", Name: "outlet-2", Properties: map[string]interface{}{
				"voltage": "120V", "load": "5.8A", "confidence": 0.88,
			}},
			{ID: "outlet-3", Type: "outlet", Name: "outlet-3", Properties: map[string]interface{}{
				"voltage": "120V", "load": "12.5A", "confidence": 0.73,
			}},
			{ID: "switch-1", Type: "switch", Name: "switch-1", Properties: map[string]interface{}{
				"type": "3-way", "load": "1.2A", "controls": "overhead-lights",
			}},
		}
		
	case "/electrical/main-panel/circuit-7/outlet-3":
		// This is a leaf node - show its properties
		fmt.Println("voltage: 120V")
		fmt.Println("load: 12.5A")
		fmt.Println("confidence: 0.73")
		fmt.Println("location: Room 201, North Wall")
		fmt.Println("height: 18 inches")
		fmt.Println("type: NEMA 5-15R")
		fmt.Println("last_validated: 2024-01-15")
		return contents
		
	case "/hvac":
		contents = []models.ArxObjectV2{
			{ID: "air-handlers", Type: "directory", Name: "air-handlers", Properties: map[string]interface{}{"count": 3}},
			{ID: "chillers", Type: "directory", Name: "chillers", Properties: map[string]interface{}{"count": 2}},
			{ID: "thermostats", Type: "directory", Name: "thermostats", Properties: map[string]interface{}{"count": 24}},
			{ID: "vav-boxes", Type: "directory", Name: "vav-boxes", Properties: map[string]interface{}{"count": 18}},
		}
		
	case "/hvac/air-handlers":
		contents = []models.ArxObjectV2{
			{ID: "ahu-1", Type: "ahu", Name: "ahu-1", Properties: map[string]interface{}{
				"model": "Carrier 50XL", "capacity": "10 tons", "status": "running",
			}},
			{ID: "ahu-2", Type: "ahu", Name: "ahu-2", Properties: map[string]interface{}{
				"model": "Trane Intellipak", "capacity": "15 tons", "status": "standby",
			}},
		}
		
	case "/floors":
		contents = []models.ArxObjectV2{
			{ID: "1", Type: "floor", Name: "1", Properties: map[string]interface{}{"rooms": 12, "area": "15000 sq ft"}},
			{ID: "2", Type: "floor", Name: "2", Properties: map[string]interface{}{"rooms": 10, "area": "15000 sq ft"}},
			{ID: "3", Type: "floor", Name: "3", Properties: map[string]interface{}{"rooms": 8, "area": "12000 sq ft"}},
		}
		
	case "/floors/1":
		for i := 101; i <= 106; i++ {
			contents = append(contents, models.ArxObjectV2{
				ID:   fmt.Sprintf("room-%d", i),
				Type: "room",
				Name: fmt.Sprintf("room-%d", i),
				Properties: map[string]interface{}{
					"area":     "250 sq ft",
					"occupancy": "office",
				},
			})
		}
		contents = append(contents, models.ArxObjectV2{
			ID: "corridor", Type: "space", Name: "corridor",
			Properties: map[string]interface{}{"area": "800 sq ft"},
		})
	}
	
	return contents
}

func displaySimpleFormat(contents []models.ArxObjectV2) {
	if len(contents) == 0 {
		return
	}
	
	// Sort by name
	sort.Slice(contents, func(i, j int) bool {
		return contents[i].Name < contents[j].Name
	})
	
	// Display in columns
	for i, obj := range contents {
		fmt.Printf("%-20s", obj.Name)
		if (i+1)%4 == 0 {
			fmt.Println()
		}
	}
	if len(contents)%4 != 0 {
		fmt.Println()
	}
}

func displayLongFormat(path string, contents []models.ArxObjectV2) {
	if len(contents) == 0 && !isLeafNode(path) {
		fmt.Println("No contents")
		return
	}
	
	// Sort by name
	sort.Slice(contents, func(i, j int) bool {
		return contents[i].Name < contents[j].Name
	})
	
	// Display with details
	for _, obj := range contents {
		typeIndicator := getTypeIndicator(obj.Type)
		
		// Format main properties
		mainProps := ""
		if obj.Properties != nil {
			propList := []string{}
			for key, val := range obj.Properties {
				if key != "description" { // Skip description in main line
					propList = append(propList, fmt.Sprintf("%s: %v", key, val))
				}
			}
			if len(propList) > 0 {
				// Show first 3 properties
				if len(propList) > 3 {
					propList = propList[:3]
				}
				mainProps = strings.Join(propList, ", ")
			}
		}
		
		// Display line
		fmt.Printf("%s %-20s %-10s %s\n", typeIndicator, obj.Name, obj.Type, mainProps)
	}
}

func displayTree(path string, contents []models.ArxObjectV2, depth int) {
	indent := strings.Repeat("  ", depth)
	
	// Display current directory
	if depth == 0 {
		fmt.Printf("%s\n", path)
	}
	
	// Sort contents
	sort.Slice(contents, func(i, j int) bool {
		return contents[i].Name < contents[j].Name
	})
	
	// Display each item
	for i, obj := range contents {
		isLast := (i == len(contents)-1)
		
		prefix := "├── "
		if isLast {
			prefix = "└── "
		}
		
		typeIndicator := getTypeIndicator(obj.Type)
		fmt.Printf("%s%s%s %s", indent, prefix, typeIndicator, obj.Name)
		
		// Add key property if present
		if obj.Properties != nil {
			if voltage, ok := obj.Properties["voltage"]; ok {
				fmt.Printf(" [%v]", voltage)
			} else if load, ok := obj.Properties["current_load"]; ok {
				fmt.Printf(" [%v]", load)
			} else if status, ok := obj.Properties["status"]; ok {
				fmt.Printf(" [%v]", status)
			}
		}
		
		fmt.Println()
		
		// Recursively show subdirectories in tree mode
		if obj.Type == "directory" || obj.Type == "system" {
			subPath := navigation.NormalizePath(path + "/" + obj.Name)
			subContents := getContentsForPath(subPath)
			if len(subContents) > 0 && depth < 2 { // Limit depth
				subIndent := indent
				if !isLast {
					subIndent += "│   "
				} else {
					subIndent += "    "
				}
				for _, subObj := range subContents {
					fmt.Printf("%s├── %s %s\n", subIndent, getTypeIndicator(subObj.Type), subObj.Name)
				}
			}
		}
	}
}

func getTypeIndicator(objType string) string {
	switch objType {
	case "system", "directory":
		return "📁"
	case "panel":
		return "⚡"
	case "circuit":
		return "🔌"
	case "outlet":
		return "🔘"
	case "switch":
		return "🎚️"
	case "floor":
		return "🏢"
	case "room":
		return "🚪"
	case "ahu", "hvac":
		return "❄️"
	case "thermostat":
		return "🌡️"
	default:
		return "📄"
	}
}

func isLeafNode(path string) bool {
	// Check if this is a leaf node (no children)
	leafPaths := []string{
		"/electrical/main-panel/circuit-7/outlet-3",
		// Add other known leaf paths
	}
	
	for _, leaf := range leafPaths {
		if path == leaf {
			return true
		}
	}
	
	return false
}