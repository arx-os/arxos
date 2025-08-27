package commands

import (
	"fmt"
	"strings"

	"github.com/arxos/arxos/cmd/display"
	"github.com/arxos/arxos/cmd/models"
	"github.com/spf13/cobra"
)

// ViewCmd - Display ASCII-BIM visualization
var ViewCmd = &cobra.Command{
	Use:   "view [target]",
	Short: "Display ASCII-BIM visualization of the building",
	Long: `Render building components in ASCII art (like Minecraft creative mode).
	
View modes:
- floor: Top-down floor plan (default)
- 3d: Pseudo-3D isometric view
- system: Show system overlay (electrical, hvac, plumbing)
- live: Interactive mode with navigation

Examples:
  arxos view f1              - View floor 1
  arxos view f1/room/101     - View specific room
  arxos view --system=electrical f1  - Show electrical overlay
  arxos view --mode=3d       - 3D view of current location`,
	RunE: runView,
}

func init() {
	ViewCmd.Flags().String("mode", "floor", "View mode: floor, 3d, system, live, hardware, pcb")
	ViewCmd.Flags().String("system", "", "System overlay: electrical, hvac, plumbing, fire, hardware, all")
	ViewCmd.Flags().Int("width", 80, "Display width")
	ViewCmd.Flags().Int("height", 40, "Display height")
	ViewCmd.Flags().Float64("scale", 1.0, "Zoom scale")
	ViewCmd.Flags().Bool("grid", true, "Show grid")
	ViewCmd.Flags().Bool("legend", true, "Show legend")
	ViewCmd.Flags().String("highlight", "", "Highlight specific objects (comma-separated IDs)")
	ViewCmd.Flags().Bool("trace", false, "Show circuit trace visualization")
}

func runView(cmd *cobra.Command, args []string) error {
	// Get flags
	mode, _ := cmd.Flags().GetString("mode")
	system, _ := cmd.Flags().GetString("system")
	width, _ := cmd.Flags().GetInt("width")
	height, _ := cmd.Flags().GetInt("height")
	scale, _ := cmd.Flags().GetFloat64("scale")
	showGrid, _ := cmd.Flags().GetBool("grid")
	showLegend, _ := cmd.Flags().GetBool("legend")
	highlightStr, _ := cmd.Flags().GetString("highlight")

	// Determine target
	target := ""
	if len(args) > 0 {
		target = args[0]
	} else if navContext.CurrentPath != "" {
		target = navContext.CurrentPath
	} else {
		target = "f1" // Default to floor 1
	}

	// Create renderer
	renderer := display.NewASCIIRenderer(width, height)
	renderer.ViewMode = mode
	renderer.SystemLayer = system
	renderer.Scale = scale
	renderer.ShowGrid = showGrid
	renderer.ShowLegend = showLegend

	// Set highlights
	if highlightStr != "" {
		for _, id := range strings.Split(highlightStr, ",") {
			renderer.Highlights[strings.TrimSpace(id)] = true
		}
	}

	// Load objects for target
	objects, err := loadObjectsForView(target)
	if err != nil {
		return fmt.Errorf("failed to load objects: %w", err)
	}
	renderer.Objects = objects

	// Check for special visualization flags
	showTrace, _ := cmd.Flags().GetBool("trace")
	if showTrace {
		fmt.Println(renderer.RenderCircuitTrace())
		return nil
	}
	
	// Render based on mode
	switch mode {
	case "floor":
		renderFloorView(renderer, target)
	case "3d":
		render3DView(renderer, target)
	case "system":
		renderSystemView(renderer, target, system)
	case "hardware":
		renderHardwareView(renderer, target)
	case "pcb":
		renderer.ViewMode = "pcb"
		renderHardwareView(renderer, target)
	case "live":
		return runInteractiveView(renderer, target)
	default:
		renderFloorView(renderer, target)
	}

	return nil
}

func renderFloorView(renderer *display.ASCIIRenderer, target string) {
	// Extract floor from target
	floor := extractFloor(target)
	if floor == "" {
		floor = "f1"
	}

	fmt.Printf("\n═══ Floor Plan: %s ═══\n\n", floor)
	
	renderer.RenderFloorPlan(floor)
	fmt.Println(renderer.ToString())
	
	if renderer.SystemLayer != "" {
		fmt.Printf("\n[System Overlay: %s]\n", renderer.SystemLayer)
	}
}

func render3DView(renderer *display.ASCIIRenderer, target string) {
	fmt.Printf("\n═══ 3D View: %s ═══\n\n", target)
	fmt.Println(renderer.MinecraftStyle3D())
}

func renderSystemView(renderer *display.ASCIIRenderer, target string, system string) {
	if system == "" {
		system = "electrical" // Default
	}
	
	floor := extractFloor(target)
	fmt.Printf("\n═══ System View: %s - %s ═══\n\n", floor, system)
	
	renderer.SystemLayer = system
	renderer.RenderFloorPlan(floor)
	fmt.Println(renderer.ToString())
	
	// Show system statistics
	showSystemStats(renderer.Objects, system)
}

func runInteractiveView(renderer *display.ASCIIRenderer, target string) error {
	// This would be a full interactive mode with keyboard input
	// For now, show a static interactive display
	
	currentObj := &models.ArxObjectV2{
		ID:     target,
		Type:   "room",
		System: "spatial",
		Coordinates: &models.Coordinates{
			X: 100,
			Y: 200,
			Z: 0,
		},
	}
	
	floor := extractFloor(target)
	renderer.RenderFloorPlan(floor)
	
	fmt.Println(renderer.RenderInteractive(currentObj))
	
	return nil
}

func loadObjectsForView(target string) ([]*models.ArxObjectV2, error) {
	// This would load actual objects from the store
	// For demonstration, create sample objects
	
	objects := []*models.ArxObjectV2{
		// Rooms
		{
			ID:   "hq/f1/room/101",
			Type: "room",
			Name: "Room 101",
			Coordinates: &models.Coordinates{X: 0, Y: 0, Z: 0},
		},
		{
			ID:   "hq/f1/room/102",
			Type: "room",
			Name: "Room 102",
			Coordinates: &models.Coordinates{X: 500, Y: 0, Z: 0},
		},
		// Walls
		{
			ID:       "hq/f1/room/101/wall_north",
			Type:     "wall",
			Position: &models.Position{Wall: "north"},
			Coordinates: &models.Coordinates{X: 0, Y: 0, Z: 0},
		},
		// Doors
		{
			ID:       "hq/f1/room/101/door_main",
			Type:     "door",
			Position: &models.Position{Wall: "south"},
			Coordinates: &models.Coordinates{X: 250, Y: 400, Z: 0},
		},
		// Electrical
		{
			ID:     "hq/electrical/panel/mdf/breaker/1/circuit/outlet/1",
			Type:   "outlet",
			System: "electrical",
			Position: &models.Position{
				Wall:   "north",
				Height: 18,
			},
			Coordinates: &models.Coordinates{X: 100, Y: 50, Z: 0},
		},
		{
			ID:     "hq/electrical/switch/f1_r101_entrance",
			Type:   "switch",
			System: "electrical",
			Position: &models.Position{
				Wall:   "south",
				Height: 48,
			},
			Coordinates: &models.Coordinates{X: 280, Y: 380, Z: 0},
		},
		// HVAC
		{
			ID:     "hq/hvac/diffuser/f1_r101_1",
			Type:   "diffuser",
			System: "hvac",
			Coordinates: &models.Coordinates{X: 250, Y: 200, Z: 240},
		},
		// Sensors
		{
			ID:     "hq/bas/sensor/temp_f1_r101",
			Type:   "sensor",
			System: "bas",
			Coordinates: &models.Coordinates{X: 250, Y: 200, Z: 200},
		},
	}
	
	return objects, nil
}

func extractFloor(target string) string {
	parts := strings.Split(target, "/")
	for _, part := range parts {
		if strings.HasPrefix(part, "f") || strings.HasPrefix(part, "b") {
			return part
		}
	}
	return "f1" // Default
}

func renderHardwareView(renderer *display.ASCIIRenderer, target string) {
	fmt.Printf("\n═══ Hardware View: %s ═══\n", target)
	fmt.Println(renderer.RenderHardwareView(target))
}

func showSystemStats(objects []*models.ArxObjectV2, system string) {
	// Count objects by type
	counts := make(map[string]int)
	for _, obj := range objects {
		if obj.System == system {
			counts[obj.Type]++
		}
	}
	
	if len(counts) > 0 {
		fmt.Printf("\n╔════ %s System Statistics ════╗\n", strings.Title(system))
		for objType, count := range counts {
			fmt.Printf("║ %-15s: %3d           ║\n", strings.Title(objType), count)
		}
		fmt.Println("╚" + strings.Repeat("═", 30) + "╝")
	}
}

// MinecraftCmd - Minecraft-style commands for fun
var MinecraftCmd = &cobra.Command{
	Use:   "mc [command]",
	Short: "Minecraft-style building commands",
	Long: `Fun Minecraft-inspired commands for building interaction.
	
Commands:
  mc place outlet    - Place an outlet at current location
  mc break wall      - Remove a wall
  mc fill room water - Fill room with... water? (simulation)
  mc spawn sensor    - Add a sensor
  mc tp f2/room/201  - Teleport to location`,
	RunE: func(cmd *cobra.Command, args []string) error {
		if len(args) < 1 {
			return fmt.Errorf("specify minecraft command")
		}
		
		switch args[0] {
		case "place":
			if len(args) < 2 {
				return fmt.Errorf("specify what to place")
			}
			fmt.Printf("🔨 Placing %s at current location...\n", args[1])
			fmt.Println("*pop* ✨")
			fmt.Printf("Successfully placed %s!\n", args[1])
			
		case "break":
			if len(args) < 2 {
				return fmt.Errorf("specify what to break")
			}
			fmt.Printf("⛏️ Breaking %s...\n", args[1])
			fmt.Println("*crack* *crack* *crack*")
			fmt.Printf("%s removed!\n", args[1])
			
		case "fill":
			if len(args) < 3 {
				return fmt.Errorf("specify area and material")
			}
			fmt.Printf("🪣 Filling %s with %s...\n", args[1], args[2])
			fmt.Println("*whoosh*")
			fmt.Printf("Area filled! (Just kidding, this is a building, not Minecraft!)\n")
			
		case "spawn":
			if len(args) < 2 {
				return fmt.Errorf("specify what to spawn")
			}
			fmt.Printf("✨ Spawning %s...\n", args[1])
			fmt.Printf("%s appeared!\n", args[1])
			
		case "tp":
			if len(args) < 2 {
				return fmt.Errorf("specify destination")
			}
			fmt.Printf("🌀 Teleporting to %s...\n", args[1])
			fmt.Println("*whoosh*")
			fmt.Printf("Teleported to %s!\n", args[1])
			
		default:
			return fmt.Errorf("unknown minecraft command: %s", args[0])
		}
		
		return nil
	},
}

// PokemonGoCmd - Pokemon Go style AR commands
var PokemonGoCmd = &cobra.Command{
	Use:   "ar [command]",
	Short: "AR field technician commands (Pokemon Go style)",
	Long: `Augmented Reality commands for field technicians.
	
Commands:
  ar scan         - Scan equipment in front of you
  ar capture      - Capture new equipment into system
  ar overlay      - Show AR overlay for current view
  ar navigate     - Navigate to equipment with AR arrows`,
	RunE: func(cmd *cobra.Command, args []string) error {
		if len(args) < 1 {
			return fmt.Errorf("specify AR command")
		}
		
		switch args[0] {
		case "scan":
			fmt.Println("📷 Scanning equipment...")
			fmt.Println("╔════════════════════════════╗")
			fmt.Println("║     🔌  DETECTED!          ║")
			fmt.Println("║                            ║")
			fmt.Println("║  Type: Electrical Outlet   ║")
			fmt.Println("║  Circuit: 12               ║")
			fmt.Println("║  Load: 180W                ║")
			fmt.Println("║  Status: ✅ Active         ║")
			fmt.Println("║                            ║")
			fmt.Println("║  [TAP TO VIEW DETAILS]     ║")
			fmt.Println("╚════════════════════════════╝")
			
		case "capture":
			fmt.Println("📸 Capturing new equipment...")
			fmt.Println("Aim at equipment and hold...")
			fmt.Println("3... 2... 1...")
			fmt.Println("✨ Captured! New ArxObject added to building database")
			fmt.Printf("ID: hq/electrical/outlet/new_%d\n", 42)
			
		case "overlay":
			fmt.Println("👓 AR Overlay Active")
			fmt.Println("┌─────────────────────────────┐")
			fmt.Println("│ ⚡ Panel MDF     [50m] ←    │")
			fmt.Println("│ 🔌 Outlet        [2m]  ↑    │")
			fmt.Println("│ 💨 VAV Box       [5m]  ↗    │")
			fmt.Println("│ 🚰 Shutoff Valve [8m]  →    │")
			fmt.Println("└─────────────────────────────┘")
			
		case "navigate":
			fmt.Println("🧭 AR Navigation Mode")
			fmt.Println("Destination: Electrical Panel MDF")
			fmt.Println("           ↑")
			fmt.Println("          50m")
			fmt.Println("    Turn left ahead")
			fmt.Println("         ◐")
			fmt.Println("Following wire path...")
			
		default:
			return fmt.Errorf("unknown AR command: %s", args[0])
		}
		
		return nil
	},
}