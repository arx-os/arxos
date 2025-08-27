package commands

import (
	"fmt"
	"path/filepath"
	"sort"
	"strings"

	"github.com/arxos/arxos/cmd/models"
	"github.com/spf13/cobra"
)

// NavigationContext maintains the current position in the building
type NavigationContext struct {
	BuildingID      string
	CurrentPath     string   // Current location in hierarchy
	Mode            string   // "spatial" or "system"
	History         []string // Navigation history for back/forward
	HistoryIndex    int
}

var navContext = &NavigationContext{
	Mode:    "spatial", // Default to spatial navigation
	History: []string{},
}

// cdV2Cmd - Change Directory in the ArxObject hierarchy
var cdV2Cmd = &cobra.Command{
	Use:   "cd [path]",
	Short: "Navigate through the building hierarchy",
	Long: `Navigate through the building using the new underscore-based naming convention.
	
Supports both spatial and system navigation modes:
- Spatial: cd f1/room/101 (navigate by physical location)
- System: cd electrical/panel/mdf (navigate by system hierarchy)

Special paths:
- /       : Go to building root
- ..      : Go up one level
- -       : Go to previous location
- ~       : Go to building root
- @system : Switch to system mode
- @spatial: Switch to spatial mode`,
	RunE: runCdV2,
}

// lsV2Cmd - List contents at current location
var lsV2Cmd = &cobra.Command{
	Use:   "ls [path]",
	Short: "List ArxObjects at current or specified location",
	Long: `List ArxObjects using the new naming convention.
	
Options:
- No args: List current location
- Path: List specific location
- -l: Long format with details
- -s: Show system components
- -a: Show all including hidden`,
	RunE: runLsV2,
}

// pwdV2Cmd - Print Working Directory
var pwdV2Cmd = &cobra.Command{
	Use:   "pwd",
	Short: "Show current location in building",
	Long:  "Display the current path in the building hierarchy with context information",
	RunE:  runPwdV2,
}

func init() {
	// Add flags
	lsV2Cmd.Flags().BoolP("long", "l", false, "Long format")
	lsV2Cmd.Flags().BoolP("all", "a", false, "Show all objects")
	lsV2Cmd.Flags().BoolP("systems", "s", false, "Show system components")
	lsV2Cmd.Flags().String("type", "", "Filter by type")
	
	cdV2Cmd.Flags().Bool("system", false, "Switch to system navigation")
	cdV2Cmd.Flags().Bool("spatial", false, "Switch to spatial navigation")
}

// runCdV2 implements the cd command
func runCdV2(cmd *cobra.Command, args []string) error {
	// Initialize context if needed
	if navContext.BuildingID == "" {
		if err := initializeNavContext(); err != nil {
			return fmt.Errorf("failed to initialize navigation: %w", err)
		}
	}

	// Handle mode switches
	systemMode, _ := cmd.Flags().GetBool("system")
	spatialMode, _ := cmd.Flags().GetBool("spatial")
	
	if systemMode {
		navContext.Mode = "system"
		fmt.Println("Switched to system navigation mode")
		return nil
	}
	if spatialMode {
		navContext.Mode = "spatial"
		fmt.Println("Switched to spatial navigation mode")
		return nil
	}

	// Handle navigation
	target := ""
	if len(args) > 0 {
		target = args[0]
	} else {
		target = "/"
	}

	newPath, err := resolvePath(navContext.CurrentPath, target)
	if err != nil {
		return err
	}

	// Verify the path exists
	if !pathExists(newPath) {
		return fmt.Errorf("path does not exist: %s", newPath)
	}

	// Update navigation context
	if navContext.CurrentPath != newPath {
		// Add to history
		navContext.History = append(navContext.History[:navContext.HistoryIndex+1], navContext.CurrentPath)
		navContext.HistoryIndex = len(navContext.History) - 1
		navContext.CurrentPath = newPath
	}

	// Show new location
	fmt.Printf("%s\n", formatPath(newPath))
	return nil
}

// runLsV2 implements the ls command
func runLsV2(cmd *cobra.Command, args []string) error {
	// Initialize context if needed
	if navContext.BuildingID == "" {
		if err := initializeNavContext(); err != nil {
			return fmt.Errorf("failed to initialize navigation: %w", err)
		}
	}

	// Determine target path
	target := navContext.CurrentPath
	if len(args) > 0 {
		var err error
		target, err = resolvePath(navContext.CurrentPath, args[0])
		if err != nil {
			return err
		}
	}

	// Get flags
	longFormat, _ := cmd.Flags().GetBool("long")
	showAll, _ := cmd.Flags().GetBool("all")
	showSystems, _ := cmd.Flags().GetBool("systems")
	typeFilter, _ := cmd.Flags().GetString("type")

	// List objects at target
	objects, err := listObjects(target, navContext.Mode, showAll, showSystems, typeFilter)
	if err != nil {
		return err
	}

	// Display results
	if longFormat {
		displayLongFormat(objects)
	} else {
		displayShortFormat(objects)
	}

	return nil
}

// runPwdV2 implements the pwd command
func runPwdV2(cmd *cobra.Command, args []string) error {
	// Initialize context if needed
	if navContext.BuildingID == "" {
		if err := initializeNavContext(); err != nil {
			return fmt.Errorf("failed to initialize navigation: %w", err)
		}
	}

	// Display current location with context
	fmt.Printf("📍 Current Location:\n")
	fmt.Printf("  Building: %s\n", navContext.BuildingID)
	fmt.Printf("  Mode: %s\n", navContext.Mode)
	fmt.Printf("  Path: %s\n", formatPath(navContext.CurrentPath))
	
	// Show what's here
	objects, _ := listObjects(navContext.CurrentPath, navContext.Mode, false, false, "")
	if len(objects) > 0 {
		fmt.Printf("  Contents: %d objects\n", len(objects))
		
		// Count by type
		typeCounts := make(map[string]int)
		for _, obj := range objects {
			typeCounts[obj.Type]++
		}
		
		fmt.Printf("  Types: ")
		types := []string{}
		for t, c := range typeCounts {
			types = append(types, fmt.Sprintf("%s(%d)", t, c))
		}
		fmt.Printf("%s\n", strings.Join(types, ", "))
	}

	return nil
}

// initializeNavContext sets up the navigation context
func initializeNavContext() error {
	// Find building root
	buildingRoot := findBuildingRootV2()
	if buildingRoot == "" {
		return fmt.Errorf("not in a building workspace")
	}

	// Extract building ID from path
	buildingID := filepath.Base(buildingRoot)
	if strings.Contains(buildingID, "_") {
		parts := strings.Split(buildingID, "_")
		buildingID = parts[0] // Use first part as ID
	}

	navContext.BuildingID = buildingID
	navContext.CurrentPath = buildingID
	navContext.History = []string{buildingID}
	navContext.HistoryIndex = 0

	return nil
}

// resolvePath resolves a navigation target to an absolute path
func resolvePath(current, target string) (string, error) {
	switch target {
	case "/", "~":
		return navContext.BuildingID, nil
	case "-":
		// Go back in history
		if navContext.HistoryIndex > 0 {
			navContext.HistoryIndex--
			return navContext.History[navContext.HistoryIndex], nil
		}
		return current, nil
	case "..":
		// Go up one level
		parts := strings.Split(current, "/")
		if len(parts) > 1 {
			return strings.Join(parts[:len(parts)-1], "/"), nil
		}
		return current, nil
	default:
		// Handle relative and absolute paths
		if strings.HasPrefix(target, "/") {
			// Absolute path from building root
			return navContext.BuildingID + target, nil
		} else {
			// Relative path
			if current == navContext.BuildingID {
				return current + "/" + target, nil
			}
			return current + "/" + target, nil
		}
	}
}

// pathExists checks if a path exists in the ArxObject hierarchy
func pathExists(path string) bool {
	// For now, simulate existence check
	// In real implementation, query the ArxObject store
	
	// Common valid paths for testing
	validPaths := map[string]bool{
		navContext.BuildingID:                          true,
		navContext.BuildingID + "/f1":                  true,
		navContext.BuildingID + "/f1/room":             true,
		navContext.BuildingID + "/f1/room/101":         true,
		navContext.BuildingID + "/electrical":          true,
		navContext.BuildingID + "/electrical/panel":    true,
		navContext.BuildingID + "/electrical/panel/mdf": true,
	}

	return validPaths[path]
}

// listObjects retrieves objects at a given path
func listObjects(path string, mode string, showAll, showSystems bool, typeFilter string) ([]*models.ArxObjectV2, error) {
	// This would query the actual ArxObject store
	// For now, return mock data for demonstration

	objects := []*models.ArxObjectV2{}

	if path == navContext.BuildingID {
		// Building root - show floors or systems
		if mode == "spatial" {
			objects = append(objects, 
				&models.ArxObjectV2{ID: path + "/f1", Type: "floor", Name: "Floor 1"},
				&models.ArxObjectV2{ID: path + "/f2", Type: "floor", Name: "Floor 2"},
				&models.ArxObjectV2{ID: path + "/f3", Type: "floor", Name: "Floor 3"},
				&models.ArxObjectV2{ID: path + "/b1", Type: "floor", Name: "Basement 1"},
			)
		} else {
			objects = append(objects,
				&models.ArxObjectV2{ID: path + "/electrical", Type: "system", Name: "Electrical System"},
				&models.ArxObjectV2{ID: path + "/hvac", Type: "system", Name: "HVAC System"},
				&models.ArxObjectV2{ID: path + "/plumbing", Type: "system", Name: "Plumbing System"},
				&models.ArxObjectV2{ID: path + "/fire_alarm", Type: "system", Name: "Fire Alarm System"},
			)
		}
	} else if strings.Contains(path, "/f1") {
		// Floor 1
		if strings.HasSuffix(path, "/f1") {
			objects = append(objects,
				&models.ArxObjectV2{ID: path + "/room", Type: "directory", Name: "Rooms"},
				&models.ArxObjectV2{ID: path + "/corridor", Type: "directory", Name: "Corridors"},
				&models.ArxObjectV2{ID: path + "/equipment", Type: "directory", Name: "Equipment"},
			)
		} else if strings.Contains(path, "/room") {
			if strings.HasSuffix(path, "/room") {
				// List rooms
				for i := 101; i <= 110; i++ {
					objects = append(objects,
						&models.ArxObjectV2{
							ID:   fmt.Sprintf("%s/%d", path, i),
							Type: "room",
							Name: fmt.Sprintf("Room %d", i),
						},
					)
				}
			}
		}
	}

	// Apply type filter
	if typeFilter != "" {
		filtered := []*models.ArxObjectV2{}
		for _, obj := range objects {
			if obj.Type == typeFilter {
				filtered = append(filtered, obj)
			}
		}
		objects = filtered
	}

	return objects, nil
}

// formatPath formats a path for display
func formatPath(path string) string {
	// Make path more readable
	display := strings.ReplaceAll(path, navContext.BuildingID, "~")
	if display == "~" {
		display = "~/"
	}
	return display
}

// displayShortFormat shows objects in short format
func displayShortFormat(objects []*models.ArxObjectV2) {
	if len(objects) == 0 {
		fmt.Println("(empty)")
		return
	}

	// Group by type
	byType := make(map[string][]string)
	for _, obj := range objects {
		baseName := filepath.Base(obj.ID)
		byType[obj.Type] = append(byType[obj.Type], baseName)
	}

	// Display grouped
	types := []string{}
	for t := range byType {
		types = append(types, t)
	}
	sort.Strings(types)

	for _, t := range types {
		names := byType[t]
		sort.Strings(names)
		
		// Use different colors/prefixes for different types
		prefix := getTypePrefix(t)
		for _, name := range names {
			fmt.Printf("%s %s\n", prefix, name)
		}
	}
}

// displayLongFormat shows objects in detailed format
func displayLongFormat(objects []*models.ArxObjectV2) {
	if len(objects) == 0 {
		fmt.Println("(empty)")
		return
	}

	fmt.Printf("%-10s %-15s %-30s %s\n", "Type", "Name", "ID", "Status")
	fmt.Println(strings.Repeat("-", 70))

	for _, obj := range objects {
		baseName := filepath.Base(obj.ID)
		status := obj.Status
		if status == "" {
			status = "active"
		}
		
		fmt.Printf("%-10s %-15s %-30s %s\n", 
			obj.Type, 
			baseName,
			obj.ID, 
			status,
		)
	}
}

// getTypePrefix returns a visual prefix for object types
func getTypePrefix(objType string) string {
	prefixes := map[string]string{
		"floor":     "📁",
		"room":      "🚪",
		"system":    "⚙️",
		"directory": "📂",
		"equipment": "🔧",
		"sensor":    "📡",
		"panel":     "⚡",
		"breaker":   "🔌",
		"outlet":    "🔌",
		"valve":     "🚰",
		"vav":       "💨",
	}
	
	if prefix, ok := prefixes[objType]; ok {
		return prefix
	}
	return "•"
}

// findBuildingRootV2 finds the building root directory
func findBuildingRootV2() string {
	// Look for .arxos directory
	// This is a simplified version - real implementation would walk up directories
	return "/Users/joelpate/repos/arxos/cmd/building_hq"
}

// Minecraft-style navigation helpers

// TeleportCmd - Minecraft-style teleport to any location
var TeleportCmd = &cobra.Command{
	Use:   "tp [coordinates]",
	Short: "Teleport to specific coordinates or object",
	Long: `Teleport directly to a location (like Minecraft /tp).
	
Examples:
  tp f1/room/101         - Teleport to room 101
  tp electrical/panel/mdf - Teleport to main panel
  tp @sensor_temp_1      - Teleport to specific sensor`,
	RunE: func(cmd *cobra.Command, args []string) error {
		if len(args) < 1 {
			return fmt.Errorf("specify destination")
		}
		
		// Direct navigation without path checking (for now)
		navContext.CurrentPath = navContext.BuildingID + "/" + args[0]
		fmt.Printf("Teleported to: %s\n", formatPath(navContext.CurrentPath))
		return nil
	},
}

// WhereAmICmd - Show current location with visual context
var WhereAmICmd = &cobra.Command{
	Use:   "whereami",
	Short: "Show current location with visual context",
	RunE: func(cmd *cobra.Command, args []string) error {
		// Show ASCII representation of current location
		fmt.Println("You are here:")
		fmt.Println("    [N]")
		fmt.Println("     |")
		fmt.Println("[W]--⚹--[E]")
		fmt.Println("     |")
		fmt.Println("    [S]")
		fmt.Printf("\n%s\n", formatPath(navContext.CurrentPath))
		return nil
	},
}