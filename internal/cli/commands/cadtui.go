package commands

import (
	"bufio"
	"context"
	"fmt"
	"os"
	"strings"

	"github.com/arx-os/arxos/internal/domain/design"
	"github.com/arx-os/arxos/internal/interfaces/tui"
	"github.com/spf13/cobra"
)

// DesignServiceProvider provides access to design services
type DesignServiceProvider interface {
	GetDesignService() design.DesignInterface
}

// CreateCADTUICommand creates the CADTUI command
func CreateCADTUICommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "cadtui",
		Short: "Launch Computer-Aided Design Terminal User Interface",
		Long:  "Launch the CADTUI for designing and managing building components in the terminal",
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()
			sc, ok := serviceContext.(DesignServiceProvider)
			if !ok {
				return fmt.Errorf("design service context is not available")
			}

			designService := sc.GetDesignService()

			// Create CADTUI instance
			cadtui := tui.NewCADTUI(designService)

			// Initial render
			if err := cadtui.Render(ctx); err != nil {
				return fmt.Errorf("failed to render CADTUI: %w", err)
			}

			// Command loop
			scanner := bufio.NewScanner(os.Stdin)
			for {
				command := ""
				if scanner.Scan() {
					command = strings.TrimSpace(scanner.Text())
				}

				if command == "" {
					continue
				}

				// Handle command
				if err := cadtui.HandleCommand(ctx, command); err != nil {
					if err.Error() == "exit requested" {
						fmt.Println("\n👋 Goodbye!")
						break
					}
					fmt.Printf("❌ Error: %v\n", err)
				}

				// Re-render after command
				if err := cadtui.Render(ctx); err != nil {
					fmt.Printf("❌ Render error: %v\n", err)
				}
			}

			return nil
		},
	}

	return cmd
}
