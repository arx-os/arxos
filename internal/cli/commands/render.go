package commands

import (
	"context"
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/spf13/cobra"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/tui/models"
	"github.com/arx-os/arxos/internal/tui/services"
)

// RenderServiceProvider provides access to render services
type RenderServiceProvider interface {
	GetContainer() *app.Container
}

// CreateRenderCommand creates the render command for visualizing buildings
func CreateRenderCommand(serviceContext any) *cobra.Command {
	var (
		floor int
	)

	cmd := &cobra.Command{
		Use:   "render <building-id>",
		Short: "Render ASCII floor plan visualization",
		Long: `Launch an interactive terminal UI that displays building floor plans as ASCII art.
Shows rooms as boxes and equipment as symbols (H=HVAC, E=Electrical, etc.)`,
		Example: `  # Render floor plan for building
  arx render abc123

  # Render specific floor
  arx render abc123 --floor 3`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			buildingID := args[0]

			// Get service context
			sc, ok := serviceContext.(RenderServiceProvider)
			if !ok {
				return fmt.Errorf("service context is not available")
			}

			container := sc.GetContainer()
			ctx := context.Background()

			// Create data service with repositories
			dataService := services.NewDataService(
				container.GetBuildingRepository(),
				container.GetEquipmentRepository(),
				container.GetFloorRepository(),
			)
			defer dataService.Close()

			// Get building data to validate it exists
			buildingData, err := dataService.GetBuildingData(ctx, buildingID)
			if err != nil {
				return fmt.Errorf("failed to load building: %w", err)
			}

			if buildingData.Building == nil {
				return fmt.Errorf("building not found: %s", buildingID)
			}

			fmt.Printf("Loading building: %s\n", buildingData.Building.Name)
			if len(buildingData.Floors) == 0 {
				fmt.Println("\n⚠️  No floors found. Create floors with: arx floor create")
				return nil
			}

			// Create TUI configuration
			tuiConfig := &config.TUIConfig{
				Enabled:        true,
				Theme:          "dark",
				UpdateInterval: "1s",
			}

			// Create TUI model
			p := tea.NewProgram(
				models.NewFloorPlanModel(
					buildingID,
					tuiConfig,
					dataService,
				),
				tea.WithAltScreen(),
			)

			// Run the TUI
			if _, err := p.Run(); err != nil {
				fmt.Printf("Error running TUI: %v\n", err)
				os.Exit(1)
			}

			return nil
		},
	}

	// Add flags
	cmd.Flags().IntVarP(&floor, "floor", "f", 0, "Specific floor to render (default: first floor)")

	return cmd
}
