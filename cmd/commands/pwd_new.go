package commands

import (
	"fmt"

	"github.com/arxos/arxos/cmd/navigation"
	"github.com/spf13/cobra"
)

// PwdCmd prints the current working directory in the building filesystem
var PwdCmd = &cobra.Command{
	Use:   "pwd",
	Short: "Print current location in building filesystem",
	Long: `Display the current path in the building's Unix-style filesystem.

The path shows your current location in the building hierarchy,
from the building root (/) down to the specific component.

Examples:
  arxos pwd
  # Output: /electrical/main-panel/circuit-7/outlet-3
  
  arxos pwd
  # Output: /hvac/air-handlers/ahu-1`,
	RunE: runPwd,
}

func runPwd(cmd *cobra.Command, args []string) error {
	// Get navigation context
	ctx := navigation.GetContext()
	
	// Get current path
	currentPath := ctx.GetCurrentPath()
	
	// Check for verbose flag
	verbose, _ := cmd.Flags().GetBool("verbose")
	
	if verbose {
		// Detailed output
		displayPwdVerbose(currentPath)
	} else {
		// Simple output (just the path)
		fmt.Println(currentPath)
	}
	
	return nil
}

func displayPwdVerbose(path string) {
	fmt.Printf("Current Location: %s\n\n", path)
	
	// Break down the path
	components := navigation.ParsePath(path)
	
	if len(components) == 0 {
		fmt.Println("📍 You are at the building root")
		fmt.Println("   Available systems:")
		fmt.Println("   ├─ /electrical   - Electrical distribution")
		fmt.Println("   ├─ /hvac        - HVAC systems")
		fmt.Println("   ├─ /plumbing    - Plumbing infrastructure")
		fmt.Println("   ├─ /structural  - Structural elements")
		fmt.Println("   ├─ /floors      - Physical floors")
		fmt.Println("   └─ /network     - Network infrastructure")
	} else {
		// Show path hierarchy
		fmt.Println("Path Hierarchy:")
		fmt.Println("   /  (root)")
		
		currentPath := ""
		for i, component := range components {
			currentPath += "/" + component
			indent := ""
			for j := 0; j <= i; j++ {
				indent += "   "
			}
			
			if i == len(components)-1 {
				fmt.Printf("%s└─ %s  ← You are here\n", indent, component)
			} else {
				fmt.Printf("%s├─ %s\n", indent, component)
			}
		}
		
		// Add context about current location
		fmt.Println()
		objType := navigation.GetObjectTypeFromPath(path)
		system := navigation.GetSystemFromPath(path)
		
		fmt.Printf("System: %s\n", system)
		fmt.Printf("Type: %s\n", objType)
		
		// Add example properties based on type
		if objType == "outlet" && path == "/electrical/main-panel/circuit-7/outlet-3" {
			fmt.Println("\nProperties:")
			fmt.Println("   voltage: 120V")
			fmt.Println("   load: 12.5A")
			fmt.Println("   confidence: 0.73")
			fmt.Println("   last_validated: 2024-01-15")
		}
	}
}

func init() {
	PwdCmd.Flags().BoolP("verbose", "v", false, "Show detailed path information")
}