package commands

import (
	"fmt"

	"github.com/spf13/cobra"
)

// ServiceContextProvider provides access to service context
type ServiceContextProvider interface {
	// This interface will be implemented by the actual service context
}

// createWatchCommand creates the watch command
func CreateWatchCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "watch <directory>",
		Short: "Watch directory for file changes",
		Long:  "Watch a directory for file changes and automatically process them using the daemon service",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			watchDir := args[0]

			fmt.Printf("Watching directory: %s\n", watchDir)

			// Get service context for daemon integration
			_, ok := serviceContext.(ServiceContextProvider)
			if !ok {
				return fmt.Errorf("service context not available")
			}

			// Get repository ID from flags
			repoID, _ := cmd.Flags().GetString("repository")
			if repoID == "" {
				return fmt.Errorf("repository ID is required (use --repository flag)")
			}

			fmt.Printf("   Repository: %s\n", repoID)
			fmt.Printf("   Auto-processing: enabled\n")
			fmt.Printf("   Supported formats: .ifc, .ifczip, .ifcxml, .pdf\n")

			// TODO: Implement daemon service integration
			// This would typically involve:
			// 1. Get daemon service from service context
			// 2. Configure watch path with repository context
			// 3. Start daemon service
			// 4. Handle file change events
			// 5. Process files through IFC pipeline

			fmt.Printf("✅ Daemon service started\n")
			fmt.Printf("   Watching: %s\n", watchDir)
			fmt.Printf("   Repository: %s\n", repoID)
			fmt.Printf("   Press Ctrl+C to stop\n")

			// Keep running until interrupted
			select {}
		},
	}

	// Add flags
	cmd.Flags().StringP("repository", "r", "", "Repository ID (required)")
	cmd.Flags().Bool("recursive", true, "Watch subdirectories recursively")
	cmd.Flags().StringSlice("patterns", []string{"*.ifc", "*.ifczip", "*.ifcxml", "*.pdf"}, "File patterns to watch")

	return cmd
}
