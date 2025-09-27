package tui

import (
	"context"
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"

	"github.com/arx-os/arxos/cmd/arx/tui/models"
	"github.com/arx-os/arxos/cmd/arx/tui/services"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/database"
)

// TUI represents the Terminal User Interface
type TUI struct {
	config *config.Config
	db     database.DB
}

// NewTUI creates a new TUI instance
func NewTUI(cfg *config.Config, db database.DB) *TUI {
	return &TUI{
		config: cfg,
		db:     db,
	}
}

// RunDashboard starts the main dashboard TUI
func (t *TUI) RunDashboard() error {
	if !t.config.TUI.Enabled {
		return fmt.Errorf("TUI is disabled in configuration")
	}

	// Validate configuration
	if err := t.config.TUI.Validate(); err != nil {
		return fmt.Errorf("invalid TUI configuration: %w", err)
	}

	// Create data service
	dataService := services.NewDataService(t.db)
	defer dataService.Close()

	// Create dashboard model
	dashboard := models.NewDashboardModel(&t.config.TUI, dataService)

	// Create Bubble Tea program
	p := tea.NewProgram(dashboard, tea.WithAltScreen())

	// Run the program
	if _, err := p.Run(); err != nil {
		return fmt.Errorf("TUI error: %w", err)
	}

	return nil
}

// RunBuildingExplorer starts the building explorer TUI
func (t *TUI) RunBuildingExplorer(buildingID string) error {
	if !t.config.TUI.Enabled {
		return fmt.Errorf("TUI is disabled in configuration")
	}

	// Validate configuration
	if err := t.config.TUI.Validate(); err != nil {
		return fmt.Errorf("invalid TUI configuration: %w", err)
	}

	// Create data service
	dataService := services.NewDataService(t.db)
	defer dataService.Close()

	// Create building explorer model
	explorer := models.NewBuildingExplorerModel(buildingID, &t.config.TUI, dataService)

	// Create Bubble Tea program
	p := tea.NewProgram(explorer, tea.WithAltScreen())

	// Run the program
	if _, err := p.Run(); err != nil {
		return fmt.Errorf("TUI error: %w", err)
	}

	return nil
}

// RunEquipmentManager starts the equipment manager TUI
func (t *TUI) RunEquipmentManager(floorID string) error {
	if !t.config.TUI.Enabled {
		return fmt.Errorf("TUI is disabled in configuration")
	}

	// Validate configuration
	if err := t.config.TUI.Validate(); err != nil {
		return fmt.Errorf("invalid TUI configuration: %w", err)
	}

	// Create data service
	dataService := services.NewDataService(t.db)
	defer dataService.Close()

	// Create equipment manager model
	manager := models.NewEquipmentManagerModel(&t.config.TUI, dataService)

	// Create Bubble Tea program
	p := tea.NewProgram(manager, tea.WithAltScreen())

	// Run the program
	if _, err := p.Run(); err != nil {
		return fmt.Errorf("TUI error: %w", err)
	}

	return nil
}

// RunSpatialQuery starts the spatial query interface TUI
func (t *TUI) RunSpatialQuery() error {
	if !t.config.TUI.Enabled {
		return fmt.Errorf("TUI is disabled in configuration")
	}

	// Validate configuration
	if err := t.config.TUI.Validate(); err != nil {
		return fmt.Errorf("invalid TUI configuration: %w", err)
	}

	// Create data service
	dataService := services.NewDataService(t.db)
	defer dataService.Close()

	// Create spatial query model
	query := models.NewSpatialQueryModel(&t.config.TUI, dataService)

	// Create Bubble Tea program
	p := tea.NewProgram(query, tea.WithAltScreen())

	// Run the program
	if _, err := p.Run(); err != nil {
		return fmt.Errorf("TUI error: %w", err)
	}

	return nil
}

// RunEnergyVisualization starts the energy visualization TUI
func (t *TUI) RunEnergyVisualization(buildingID string) error {
	if !t.config.TUI.Enabled {
		return fmt.Errorf("TUI is disabled in configuration")
	}

	// TODO: Implement energy visualization model
	return fmt.Errorf("energy visualization not yet implemented")
}

// RunRepositoryManager starts the repository manager TUI
func (t *TUI) RunRepositoryManager() error {
	if !t.config.TUI.Enabled {
		return fmt.Errorf("TUI is disabled in configuration")
	}

	// TODO: Implement repository manager model
	return fmt.Errorf("repository manager not yet implemented")
}

// IsTUIEnabled checks if TUI is enabled and terminal supports it
func IsTUIEnabled() bool {
	// Check if terminal supports TUI
	if os.Getenv("TERM") == "" {
		return false
	}

	// Check if running in a proper terminal
	if os.Getenv("SSH_CLIENT") != "" || os.Getenv("SSH_TTY") != "" {
		return true // SSH is fine
	}

	// Check for common terminal emulators
	term := os.Getenv("TERM")
	switch term {
	case "xterm", "xterm-256color", "screen", "screen-256color", "tmux", "tmux-256color":
		return true
	default:
		return false
	}
}

// RunTUICommand runs a TUI command with proper error handling
func RunTUICommand(ctx context.Context, command string, args ...string) error {
	// Load configuration
	cfg, err := config.Load("")
	if err != nil {
		return fmt.Errorf("failed to load configuration: %w", err)
	}

	// Initialize database
	db, err := database.NewPostGISConnection(ctx)
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create TUI instance
	tui := NewTUI(cfg, db)

	// Check if TUI is enabled
	if !IsTUIEnabled() {
		return fmt.Errorf("TUI is not supported in this terminal environment")
	}

	// Run the appropriate TUI command
	switch command {
	case "dashboard":
		return tui.RunDashboard()
	case "building":
		buildingID := ""
		if len(args) > 0 {
			buildingID = args[0]
		}
		return tui.RunBuildingExplorer(buildingID)
	case "equipment":
		floorID := ""
		if len(args) > 0 {
			floorID = args[0]
		}
		return tui.RunEquipmentManager(floorID)
	case "query":
		return tui.RunSpatialQuery()
	case "energy":
		buildingID := ""
		if len(args) > 0 {
			buildingID = args[0]
		}
		return tui.RunEnergyVisualization(buildingID)
	case "repo":
		return tui.RunRepositoryManager()
	case "floorplan":
		buildingID := ""
		if len(args) > 0 {
			buildingID = args[0]
		}
		return tui.RunFloorPlan(buildingID)
	default:
		return fmt.Errorf("unknown TUI command: %s", command)
	}
}

// RunFloorPlan starts the floor plan TUI
func (t *TUI) RunFloorPlan(buildingID string) error {
	if !t.config.TUI.Enabled {
		return fmt.Errorf("TUI is disabled in configuration")
	}

	// Validate configuration
	if err := t.config.TUI.Validate(); err != nil {
		return fmt.Errorf("invalid TUI configuration: %w", err)
	}

	// Create data service
	dataService := services.NewDataService(t.db)
	defer dataService.Close()

	// Create floor plan model
	floorPlan := models.NewFloorPlanModel(buildingID, &t.config.TUI, dataService)

	// Create Bubble Tea program
	p := tea.NewProgram(floorPlan, tea.WithAltScreen())

	// Run the program
	if _, err := p.Run(); err != nil {
		return fmt.Errorf("TUI error: %w", err)
	}

	return nil
}

// TUICommands returns the list of available TUI commands
func TUICommands() []string {
	return []string{
		"dashboard",
		"building",
		"equipment",
		"query",
		"energy",
		"repo",
		"floorplan",
		"explorer",
	}
}
