package commands

import (
	"fmt"
	"strings"

	"github.com/arxos/arxos/cmd/models"
	"github.com/arxos/arxos/cmd/navigation"
	"github.com/spf13/cobra"
)

// TreeCmd displays directory tree structure
var TreeCmd = &cobra.Command{
	Use:   "tree [path]",
	Short: "Display building components in tree structure",
	Long: `Display the hierarchical structure of building components
starting from the current location or specified path.

Examples:
  arxos tree                # Tree from current location
  arxos tree /hvac          # Full HVAC system tree
  arxos tree -L 2 /         # Limit depth to 2 levels
  arxos tree /electrical    # Electrical system tree`,
	RunE: runTree,
}

func init() {
	TreeCmd.Flags().IntP("level", "L", 3, "Maximum depth to display")
	TreeCmd.Flags().BoolP("all", "a", false, "Show all items including hidden")
	TreeCmd.Flags().BoolP("directories", "d", false, "Show only directories")
	TreeCmd.Flags().BoolP("full", "f", false, "Show full paths")
	TreeCmd.Flags().BoolP("properties", "p", false, "Show properties")
}

func runTree(cmd *cobra.Command, args []string) error {
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
	maxLevel, _ := cmd.Flags().GetInt("level")
	showProperties, _ := cmd.Flags().GetBool("properties")
	directoriesOnly, _ := cmd.Flags().GetBool("directories")
	
	// Display tree header
	fmt.Printf("%s\n", targetPath)
	
	// Build and display tree
	stats := &TreeStats{}
	buildTree(targetPath, "", 0, maxLevel, true, showProperties, directoriesOnly, stats)
	
	// Display statistics
	fmt.Printf("\n%d directories, %d files\n", stats.Directories, stats.Files)
	
	return nil
}

type TreeStats struct {
	Directories int
	Files       int
}

func buildTree(path string, prefix string, currentLevel int, maxLevel int, isLastItem bool, showProperties bool, directoriesOnly bool) *TreeStats {
	stats := &TreeStats{}
	
	if currentLevel >= maxLevel {
		return stats
	}
	
	// Get contents
	contents := getTreeContents(path)
	
	// Filter if directories only
	if directoriesOnly {
		filtered := []models.ArxObjectV2{}
		for _, obj := range contents {
			if isDirectory(obj.Type) {
				filtered = append(filtered, obj)
			}
		}
		contents = filtered
	}
	
	// Display each item
	for i, obj := range contents {
		isLast := (i == len(contents)-1)
		
		// Determine tree characters
		nodePrefix := "├── "
		extension := "│   "
		if isLast {
			nodePrefix = "└── "
			extension = "    "
		}
		
		// Display the item
		displayTreeNode(obj, prefix+nodePrefix, showProperties)
		
		// Update statistics
		if isDirectory(obj.Type) {
			stats.Directories++
		} else {
			stats.Files++
		}
		
		// Recurse for directories
		if isDirectory(obj.Type) {
			childPath := navigation.NormalizePath(path + "/" + obj.Name)
			childStats := buildTree(childPath, prefix+extension, currentLevel+1, maxLevel, isLast, showProperties, directoriesOnly)
			stats.Directories += childStats.Directories
			stats.Files += childStats.Files
		}
	}
	
	return stats
}

func displayTreeNode(obj models.ArxObjectV2, prefix string, showProperties bool) {
	// Get type indicator
	indicator := getTreeTypeIndicator(obj.Type)
	
	// Build display string
	display := fmt.Sprintf("%s%s %s", prefix, indicator, obj.Name)
	
	// Add properties if requested
	if showProperties && obj.Properties != nil {
		props := []string{}
		
		// Select key properties to display
		if voltage, ok := obj.Properties["voltage"]; ok {
			props = append(props, fmt.Sprintf("voltage=%v", voltage))
		}
		if load, ok := obj.Properties["current_load"]; ok {
			props = append(props, fmt.Sprintf("load=%v", load))
		}
		if status, ok := obj.Properties["status"]; ok {
			props = append(props, fmt.Sprintf("status=%v", status))
		}
		if capacity, ok := obj.Properties["capacity"]; ok {
			props = append(props, fmt.Sprintf("capacity=%v", capacity))
		}
		if confidence, ok := obj.Properties["confidence"]; ok {
			props = append(props, fmt.Sprintf("conf=%.2f", confidence))
		}
		
		if len(props) > 0 {
			display += fmt.Sprintf(" [%s]", strings.Join(props, ", "))
		}
	}
	
	fmt.Println(display)
}

func getTreeTypeIndicator(objType string) string {
	// Return different indicators based on type
	switch objType {
	case "system", "directory":
		return "📁"
	case "panel":
		return "⚡"
	case "circuit":
		return "⚙️"
	case "outlet":
		return "🔌"
	case "switch":
		return "🎚️"
	case "floor":
		return "🏢"
	case "room":
		return "🚪"
	case "ahu":
		return "❄️"
	case "thermostat":
		return "🌡️"
	case "hvac":
		return "💨"
	default:
		return "•"
	}
}

func isDirectory(objType string) bool {
	return objType == "system" || objType == "directory" || objType == "floor"
}

// Mock function to get contents for tree - in production would query store
func getTreeContents(path string) []models.ArxObjectV2 {
	// Reuse the ls command's content function
	return getContentsForPath(path)
}

// Example tree output for /hvac path as specified in vision
func generateHVACTreeExample() {
	example := `
/hvac
├── 📁 air-handlers
│   ├── ❄️ ahu-1
│   │   ├── supply-fan [status=running]
│   │   ├── return-fan [status=running]
│   │   ├── cooling-coil [temp=45F]
│   │   ├── heating-coil [temp=72F]
│   │   └── vfd [speed=75%]
│   ├── ❄️ ahu-2
│   │   ├── supply-fan [status=standby]
│   │   ├── return-fan [status=standby]
│   │   └── vfd [speed=0%]
│   └── ❄️ ahu-3
│       ├── supply-fan [status=running]
│       └── vfd [speed=60%]
├── 📁 chillers
│   ├── chiller-1 [capacity=200tons, status=running]
│   └── chiller-2 [capacity=200tons, status=standby]
├── 📁 thermostats
│   ├── 🌡️ t-101 [setpoint=72F, current=71F]
│   ├── 🌡️ t-102 [setpoint=72F, current=73F]
│   ├── 🌡️ t-103 [setpoint=70F, current=70F]
│   └── ... (21 more)
└── 📁 vav-boxes
    ├── vav-101 [flow=450cfm, damper=65%]
    ├── vav-102 [flow=380cfm, damper=55%]
    └── ... (16 more)

4 directories, 35 components
`
	fmt.Print(example)
}