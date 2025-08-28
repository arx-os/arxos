package commands

import (
	"fmt"
	"strings"

	"github.com/arxos/arxos/cmd/models"
	"github.com/arxos/arxos/cmd/navigation"
	"github.com/arxos/arxos/cmd/store"
	"github.com/spf13/cobra"
)

// CdCmd changes the current directory in the building filesystem
var CdCmd = &cobra.Command{
	Use:   "cd [path]",
	Short: "Change current location in building filesystem",
	Long: `Navigate through the building using Unix-style paths.

Every component in the building has a path:
- /electrical/main-panel/circuit-7/outlet-3
- /hvac/air-handlers/ahu-1/supply-fan
- /floors/2/room-201

Special paths:
  ~  or /     Building root
  ..          Parent directory
  -           Previous directory (if implemented)

Examples:
  arxos cd /electrical/main-panel           # Go to main panel
  arxos cd circuit-7                        # Relative navigation
  arxos cd ../circuit-8                     # Go to sibling
  arxos cd /floors/2/room-201               # Go to specific room
  arxos cd ~                                # Go to building root`,
	RunE: runCd,
}

func runCd(cmd *cobra.Command, args []string) error {
	// Get navigation context
	ctx := navigation.GetContext()
	
	// Determine target path
	targetPath := ""
	if len(args) > 0 {
		targetPath = args[0]
	} else {
		targetPath = "/"
	}
	
	// Handle special cases
	switch targetPath {
	case "~":
		targetPath = "/"
	case "-":
		// Go to previous directory
		// TODO: Implement history navigation
		fmt.Println("Previous directory navigation not yet implemented")
		return nil
	}
	
	// Calculate absolute path
	absolutePath := ""
	if strings.HasPrefix(targetPath, "/") {
		// Absolute path
		absolutePath = targetPath
	} else if targetPath == ".." {
		// Parent directory
		absolutePath = navigation.GetContext().GetParentPath()
	} else if strings.HasPrefix(targetPath, "../") {
		// Relative to parent
		parent := navigation.GetContext().GetParentPath()
		relative := strings.TrimPrefix(targetPath, "../")
		absolutePath = navigation.NormalizePath(parent + "/" + relative)
	} else {
		// Relative to current
		absolutePath = ctx.GetRelativePath(targetPath)
	}
	
	// Normalize the path
	absolutePath = navigation.NormalizePath(absolutePath)
	
	// Validate the path exists (check with store)
	if !validatePath(absolutePath) {
		// For now, we'll allow navigation to any syntactically valid path
		// In production, we'd check if the object exists
		if !navigation.IsValidPath(absolutePath) {
			return fmt.Errorf("invalid path: %s", absolutePath)
		}
	}
	
	// Update navigation context
	ctx.SetCurrentPath(absolutePath)
	
	// Display new location
	displayLocation(absolutePath)
	
	return nil
}

func validatePath(path string) bool {
	// Check if path exists in the store
	// For demonstration, we'll check some known paths
	knownPaths := []string{
		"/",
		"/electrical",
		"/electrical/main-panel",
		"/electrical/main-panel/circuit-1",
		"/electrical/main-panel/circuit-2",
		"/electrical/main-panel/circuit-3",
		"/electrical/main-panel/circuit-4",
		"/electrical/main-panel/circuit-5",
		"/electrical/main-panel/circuit-6",
		"/electrical/main-panel/circuit-7",
		"/electrical/main-panel/circuit-7/outlet-1",
		"/electrical/main-panel/circuit-7/outlet-2",
		"/electrical/main-panel/circuit-7/outlet-3",
		"/hvac",
		"/hvac/air-handlers",
		"/hvac/air-handlers/ahu-1",
		"/hvac/air-handlers/ahu-1/supply-fan",
		"/hvac/thermostats",
		"/hvac/thermostats/t-101",
		"/plumbing",
		"/floors",
		"/floors/1",
		"/floors/1/room-101",
		"/floors/1/room-102",
		"/floors/2",
		"/floors/2/room-201",
	}
	
	for _, known := range knownPaths {
		if path == known {
			return true
		}
	}
	
	// In real implementation, query the store
	return false
}

func displayLocation(path string) {
	// Create a styled display of the new location
	fmt.Printf("\n📍 %s\n", navigation.FormatPath(path))
	
	// Show what's here (preview of ls functionality)
	components := navigation.ParsePath(path)
	
	if len(components) > 0 {
		objType := navigation.GetObjectTypeFromPath(path)
		
		// Add contextual information
		switch objType {
		case "circuit":
			fmt.Println("   Type: Electrical Circuit")
			fmt.Println("   ├─ Breaker: 20A")
			fmt.Println("   ├─ Load: ~12.5A")
			fmt.Println("   └─ Status: Active")
			
		case "outlet":
			outletNum := components[len(components)-1]
			fmt.Printf("   Type: Electrical Outlet (%s)\n", outletNum)
			fmt.Println("   ├─ Voltage: 120V")
			fmt.Println("   ├─ Load: 12.5A")
			fmt.Println("   └─ Confidence: 0.73")
			
		case "room":
			roomNum := components[len(components)-1]
			fmt.Printf("   Type: Room (%s)\n", roomNum)
			fmt.Println("   ├─ Area: 250 sq ft")
			fmt.Println("   ├─ Occupancy: Office")
			fmt.Println("   └─ HVAC Zone: 2")
			
		case "panel":
			fmt.Println("   Type: Electrical Panel")
			fmt.Println("   ├─ Voltage: 480V 3-phase")
			fmt.Println("   ├─ Circuits: 42")
			fmt.Println("   └─ Total Load: 285.7A")
			
		case "hvac_unit":
			fmt.Println("   Type: HVAC Equipment")
			fmt.Println("   ├─ Model: Carrier 50XL")
			fmt.Println("   ├─ Capacity: 10 tons")
			fmt.Println("   └─ Status: Running")
			
		default:
			fmt.Printf("   Type: %s\n", objType)
		}
	}
	
	fmt.Println()
}