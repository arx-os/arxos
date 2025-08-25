package state

import (
	"context"
	"fmt"
	"strings"

	"github.com/spf13/cobra"
	"github.com/arxos/core/internal/state"
)

var restoreCmd = &cobra.Command{
	Use:   "restore [building-id] [state-id|version]",
	Short: "Restore a building to a previous state",
	Long: `Restore a building to a previously captured state.
	
This command will apply the specified state to the building, effectively rolling back
any changes made since that state was captured. A new state will be created to record
the restoration.

WARNING: This operation will modify the building's current configuration.`,
	Args: cobra.ExactArgs(2),
	RunE: runRestore,
}

var (
	restoreMessage string
	restoreDryRun  bool
	restoreForce   bool
)

func init() {
	restoreCmd.Flags().StringVarP(&restoreMessage, "message", "m", "", "Message describing why the restore is being performed")
	restoreCmd.Flags().BoolVar(&restoreDryRun, "dry-run", false, "Show what would be restored without making changes")
	restoreCmd.Flags().BoolVarP(&restoreForce, "force", "f", false, "Skip confirmation prompt")
}

func runRestore(cmd *cobra.Command, args []string) error {
	buildingID := args[0]
	targetState := args[1]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create state manager
	stateManager := state.NewManager(db)

	ctx := context.Background()

	// TODO: Resolve state identifier (version -> ID)
	// For now, assume ID is provided
	targetStateID := targetState

	// Get target state details
	stateDetails, err := stateManager.GetState(ctx, targetStateID)
	if err != nil {
		return fmt.Errorf("failed to get target state: %w", err)
	}

	// Verify it's the correct building
	if stateDetails.BuildingID != buildingID {
		return fmt.Errorf("state %s does not belong to building %s", targetStateID, buildingID)
	}

	// Show what will be restored
	fmt.Printf("Restore Target\n")
	fmt.Printf("%s\n", strings.Repeat("=", 60))
	fmt.Printf("Building:     %s\n", buildingID)
	fmt.Printf("Target State: v%s\n", stateDetails.Version)
	fmt.Printf("State ID:     %s\n", stateDetails.ID)
	fmt.Printf("Branch:       %s\n", stateDetails.BranchName)
	fmt.Printf("Captured:     %s\n", stateDetails.CapturedAt.Format("2006-01-02 15:04:05"))
	fmt.Printf("Author:       %s\n", stateDetails.AuthorName)
	fmt.Printf("Message:      %s\n", stateDetails.Message)
	fmt.Printf("\n")

	// Show state contents
	fmt.Printf("State Contents:\n")
	fmt.Printf("  ArxObjects:    %d\n", stateDetails.ArxObjectCount)
	fmt.Printf("  Size:          %d bytes\n", stateDetails.TotalSizeBytes)
	if stateDetails.PerformanceMetrics != nil {
		fmt.Printf("  Metrics:       ✓\n")
	}
	if stateDetails.ComplianceStatus != nil {
		fmt.Printf("  Compliance:    ✓\n")
	}
	fmt.Printf("\n")

	// Dry run - just show what would happen
	if restoreDryRun {
		fmt.Printf("DRY RUN: No changes will be made.\n")
		fmt.Printf("\nThis would restore the building to state v%s\n", stateDetails.Version)
		return nil
	}

	// Confirmation prompt (unless forced)
	if !restoreForce {
		fmt.Printf("⚠️  WARNING: This will modify the building's current configuration.\n")
		fmt.Printf("Are you sure you want to restore to v%s? (yes/no): ", stateDetails.Version)
		
		var response string
		fmt.Scanln(&response)
		
		if strings.ToLower(response) != "yes" && strings.ToLower(response) != "y" {
			fmt.Printf("Restore cancelled.\n")
			return nil
		}
	}

	// Set default message if not provided
	if restoreMessage == "" {
		restoreMessage = fmt.Sprintf("Restored to version %s", stateDetails.Version)
	}

	// Perform the restore
	fmt.Printf("\nRestoring building to v%s...\n", stateDetails.Version)
	
	opts := state.CaptureOptions{
		Message:    restoreMessage,
		AuthorID:   "cli",
		AuthorName: authorName,
	}

	err = stateManager.RestoreState(ctx, buildingID, targetStateID, opts)
	if err != nil {
		return fmt.Errorf("failed to restore state: %w", err)
	}

	fmt.Printf("\n✓ Building successfully restored to v%s\n", stateDetails.Version)
	fmt.Printf("\nA new state has been created to record this restoration.\n")
	fmt.Printf("Use 'arxos state list %s' to see the updated history.\n", buildingID)

	return nil
}