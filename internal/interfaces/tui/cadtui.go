package tui

import (
	"context"
	"fmt"
	"strings"

	"github.com/arx-os/arxos/internal/domain/component"
	"github.com/arx-os/arxos/internal/domain/design"
)

// CADTUI represents the Computer-Aided Design Terminal User Interface
type CADTUI struct {
	designInterface   design.DesignInterface
	viewport          design.Viewport
	selectedComponent *string
	scene             *design.Scene
}

// NewCADTUI creates a new CADTUI instance
func NewCADTUI(designInterface design.DesignInterface) *CADTUI {
	return &CADTUI{
		designInterface: designInterface,
		viewport: design.Viewport{
			X:      0,
			Y:      0,
			Width:  80,
			Height: 24,
			Zoom:   1.0,
			Center: design.Position{X: 40, Y: 12},
		},
	}
}

// Render renders the CADTUI interface
func (tui *CADTUI) Render(ctx context.Context) error {
	// Get current scene
	scene, err := tui.designInterface.RenderScene(ctx, component.ComponentFilter{
		Limit: 100,
	})
	if err != nil {
		return fmt.Errorf("failed to render scene: %w", err)
	}
	tui.scene = scene

	// Clear screen and render
	fmt.Print("\033[2J\033[H") // Clear screen and move cursor to top-left

	// Render header
	tui.renderHeader()

	// Render viewport
	tui.renderViewport()

	// Render status bar
	tui.renderStatusBar()

	// Render command prompt
	tui.renderCommandPrompt()

	return nil
}

// renderHeader renders the CADTUI header
func (tui *CADTUI) renderHeader() {
	header := "🏗️  ArxOS CADTUI - Universal Building Design Interface"
	fmt.Printf("\033[1;36m%s\033[0m\n", header)
	fmt.Printf("\033[36m%s\033[0m\n", strings.Repeat("=", len(header)))
	fmt.Println()
}

// renderViewport renders the main design viewport
func (tui *CADTUI) renderViewport() {
	// Create a grid representation
	grid := make([][]string, tui.viewport.Height)
	for i := range grid {
		grid[i] = make([]string, tui.viewport.Width)
		for j := range grid[i] {
			grid[i][j] = "·" // Grid dots
		}
	}

	// Place components on the grid
	for _, comp := range tui.scene.Components {
		x := comp.Position.X
		y := comp.Position.Y

		// Ensure coordinates are within viewport bounds
		if x >= 0 && x < tui.viewport.Width && y >= 0 && y < tui.viewport.Height {
			// Highlight selected component
			if tui.selectedComponent != nil && comp.ComponentID == *tui.selectedComponent {
				grid[y][x] = fmt.Sprintf("\033[1;33m%s\033[0m", comp.Symbol) // Bold yellow
			} else {
				grid[y][x] = comp.Symbol
			}
		}
	}

	// Render the grid
	fmt.Printf("\033[37mViewport (%dx%d, Zoom: %.1f):\033[0m\n",
		tui.viewport.Width, tui.viewport.Height, tui.viewport.Zoom)
	fmt.Println()

	for _, row := range grid {
		fmt.Println(strings.Join(row, ""))
	}
	fmt.Println()
}

// renderStatusBar renders the status bar with component information
func (tui *CADTUI) renderStatusBar() {
	status := fmt.Sprintf("Components: %d | Viewport: %dx%d | Zoom: %.1f",
		len(tui.scene.Components),
		tui.viewport.Width,
		tui.viewport.Height,
		tui.viewport.Zoom)

	if tui.selectedComponent != nil {
		status += fmt.Sprintf(" | Selected: %s", *tui.selectedComponent)
	}

	fmt.Printf("\033[32m%s\033[0m\n", status)
	fmt.Println()
}

// renderCommandPrompt renders the command prompt
func (tui *CADTUI) renderCommandPrompt() {
	fmt.Print("\033[33mCADTUI> \033[0m")
}

// HandleCommand handles CADTUI commands
func (tui *CADTUI) HandleCommand(ctx context.Context, command string) error {
	parts := strings.Fields(command)
	if len(parts) == 0 {
		return nil
	}

	switch parts[0] {
	case "list", "ls":
		return tui.handleListCommand(ctx, parts[1:])
	case "create", "c":
		return tui.handleCreateCommand(ctx, parts[1:])
	case "select", "s":
		return tui.handleSelectCommand(ctx, parts[1:])
	case "move", "m":
		return tui.handleMoveCommand(ctx, parts[1:])
	case "connect", "conn":
		return tui.handleConnectCommand(ctx, parts[1:])
	case "tools", "t":
		return tui.handleToolsCommand(ctx, parts[1:])
	case "zoom", "z":
		return tui.handleZoomCommand(ctx, parts[1:])
	case "help", "h":
		return tui.handleHelpCommand()
	case "quit", "q", "exit":
		return fmt.Errorf("exit requested")
	default:
		fmt.Printf("Unknown command: %s. Type 'help' for available commands.\n", parts[0])
		return nil
	}
}

// handleListCommand handles the list command
func (tui *CADTUI) handleListCommand(ctx context.Context, args []string) error {
	fmt.Println("\n📋 Components in Scene:")
	fmt.Println("ID                                   | Name                | Type        | Path")
	fmt.Println(strings.Repeat("-", 80))

	for _, comp := range tui.scene.Components {
		// For now, just show the visual representation info
		fmt.Printf("%-36s | %-18s | %-11s | %s\n",
			comp.ComponentID[:8]+"...",
			comp.Symbol,
			"component",
			fmt.Sprintf("(%d,%d)", comp.Position.X, comp.Position.Y))
	}
	fmt.Println()
	return nil
}

// handleCreateCommand handles the create command
func (tui *CADTUI) handleCreateCommand(ctx context.Context, args []string) error {
	if len(args) < 4 {
		fmt.Println("Usage: create <name> <type> <path> <creator>")
		fmt.Println("Example: create 'HVAC Unit' hvac_unit '/B1/3/CONF-301/HVAC/UNIT-01' admin")
		return nil
	}

	name := args[0]
	compType := component.ComponentType(args[1])
	path := args[2]
	creator := args[3]

	req := design.CreateComponentRequest{
		Name:      name,
		Type:      compType,
		Path:      path,
		Location:  component.Location{X: 10, Y: 10, Z: 0}, // Default location
		CreatedBy: creator,
	}

	comp, err := tui.designInterface.CreateComponent(ctx, req)
	if err != nil {
		fmt.Printf("❌ Failed to create component: %v\n", err)
		return nil
	}

	fmt.Printf("✅ Created component: %s (%s)\n", comp.Name, comp.ID)
	return nil
}

// handleSelectCommand handles the select command
func (tui *CADTUI) handleSelectCommand(ctx context.Context, args []string) error {
	if len(args) < 1 {
		fmt.Println("Usage: select <component_id>")
		return nil
	}

	componentID := args[0]
	tui.selectedComponent = &componentID

	err := tui.designInterface.SelectComponent(ctx, componentID)
	if err != nil {
		fmt.Printf("❌ Failed to select component: %v\n", err)
		return nil
	}

	fmt.Printf("✅ Selected component: %s\n", componentID)
	return nil
}

// handleMoveCommand handles the move command
func (tui *CADTUI) handleMoveCommand(ctx context.Context, args []string) error {
	if len(args) < 3 {
		fmt.Println("Usage: move <component_id> <x> <y>")
		return nil
	}

	componentID := args[0]
	x := 0.0 // TODO: Parse float
	y := 0.0 // TODO: Parse float

	newLocation := component.Location{X: x, Y: y, Z: 0}

	err := tui.designInterface.MoveComponent(ctx, componentID, newLocation)
	if err != nil {
		fmt.Printf("❌ Failed to move component: %v\n", err)
		return nil
	}

	fmt.Printf("✅ Moved component %s to (%.1f, %.1f)\n", componentID, x, y)
	return nil
}

// handleConnectCommand handles the connect command
func (tui *CADTUI) handleConnectCommand(ctx context.Context, args []string) error {
	if len(args) < 3 {
		fmt.Println("Usage: connect <source_id> <target_id> <relation_type>")
		fmt.Println("Relation types: connected, controlled, supplies, depends_on, contains, adjacent")
		return nil
	}

	sourceID := args[0]
	targetID := args[1]
	relationType := component.RelationType(args[2])

	err := tui.designInterface.ConnectComponents(ctx, sourceID, targetID, relationType)
	if err != nil {
		fmt.Printf("❌ Failed to connect components: %v\n", err)
		return nil
	}

	fmt.Printf("✅ Connected %s -> %s (%s)\n", sourceID, targetID, relationType)
	return nil
}

// handleToolsCommand handles the tools command
func (tui *CADTUI) handleToolsCommand(ctx context.Context, args []string) error {
	tools, err := tui.designInterface.GetDesignTools(ctx)
	if err != nil {
		fmt.Printf("❌ Failed to get tools: %v\n", err)
		return nil
	}

	fmt.Println("\n🛠️  Available Design Tools:")
	fmt.Println("ID                   | Name                | Category    | Description")
	fmt.Println(strings.Repeat("-", 80))

	for _, tool := range tools {
		fmt.Printf("%-20s | %-18s | %-11s | %s\n",
			tool.ID,
			tool.Name,
			tool.Category,
			tool.Description)
	}
	fmt.Println()
	return nil
}

// handleZoomCommand handles the zoom command
func (tui *CADTUI) handleZoomCommand(ctx context.Context, args []string) error {
	if len(args) < 1 {
		fmt.Println("Usage: zoom <level> or zoom fit")
		return nil
	}

	if args[0] == "fit" {
		fmt.Println("🔍 Zooming to fit all components...")
		// TODO: Implement zoom to fit
		return nil
	}

	fmt.Printf("🔍 Zoom level: %s\n", args[0])
	// TODO: Implement zoom level setting
	return nil
}

// handleHelpCommand handles the help command
func (tui *CADTUI) handleHelpCommand() error {
	fmt.Println("\n📖 CADTUI Commands:")
	fmt.Println("  list, ls           - List all components")
	fmt.Println("  create, c          - Create a new component")
	fmt.Println("  select, s          - Select a component")
	fmt.Println("  move, m            - Move a component")
	fmt.Println("  connect, conn      - Connect two components")
	fmt.Println("  tools, t           - Show available design tools")
	fmt.Println("  zoom, z            - Set zoom level or fit view")
	fmt.Println("  help, h            - Show this help")
	fmt.Println("  quit, q, exit      - Exit CADTUI")
	fmt.Println()
	return nil
}
