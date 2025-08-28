package state

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/spf13/cobra"
	// // "github.com/arxos/core/internal/state" // TODO: Fix import
)

var listCmd = &cobra.Command{
	Use:   "list [building-id]",
	Short: "List all captured states for a building",
	Long: `List all captured states for a building, showing version history,
branches, and basic statistics about each state.`,
	Args:    cobra.ExactArgs(1),
	Aliases: []string{"ls", "history"},
	RunE:    runList,
}

var (
	listBranch string
	listLimit  int
	listOffset int
	showTags   bool
	verbose    bool
)

func init() {
	listCmd.Flags().StringVarP(&listBranch, "branch", "b", "main", "Branch to list states from")
	listCmd.Flags().IntVarP(&listLimit, "limit", "l", 20, "Maximum number of states to show")
	listCmd.Flags().IntVar(&listOffset, "offset", 0, "Offset for pagination")
	listCmd.Flags().BoolVar(&showTags, "tags", false, "Show tags for each state")
	listCmd.Flags().BoolVarP(&verbose, "verbose", "v", false, "Show detailed information")
}

func runList(cmd *cobra.Command, args []string) error {
	buildingID := args[0]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create state manager
	stateManager := state.NewManager(db)

	// List states
	ctx := context.Background()
	states, err := stateManager.ListStates(ctx, buildingID, listBranch, listLimit, listOffset)
	if err != nil {
		return fmt.Errorf("failed to list states: %w", err)
	}

	if len(states) == 0 {
		fmt.Printf("No states found for building %s on branch '%s'\n", buildingID, listBranch)
		return nil
	}

	// Output JSON if requested
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		jsonData, _ := json.MarshalIndent(states, "", "  ")
		fmt.Printf("%s\n", jsonData)
		return nil
	}

	// Display header
	fmt.Printf("Building State History for %s (branch: %s)\n", buildingID, listBranch)
	fmt.Println(strings.Repeat("=", 80))

	// Display states
	for i, s := range states {
		fmt.Printf("\n")
		if i == 0 {
			fmt.Printf("→ ") // Current state indicator
		} else {
			fmt.Printf("  ")
		}
		
		fmt.Printf("Version %s", s.Version)
		if s.ParentStateID == nil {
			fmt.Printf(" (initial)")
		}
		fmt.Printf("\n")

		fmt.Printf("  ID:       %s\n", s.ID)
		fmt.Printf("  Hash:     %s\n", s.StateHash[:16]+"...")
		fmt.Printf("  Author:   %s\n", s.AuthorName)
		fmt.Printf("  Date:     %s\n", s.CapturedAt.Format(time.RFC3339))
		fmt.Printf("  Objects:  %d\n", s.ArxObjectCount)
		
		if showTags && len(s.Tags) > 0 {
			fmt.Printf("  Tags:     %v\n", s.Tags)
		}

		if s.Message != "" {
			messageLines := strings.Split(s.Message, "\n")
			fmt.Printf("  Message:  %s\n", messageLines[0])
			for j := 1; j < len(messageLines) && j < 3; j++ {
				fmt.Printf("           %s\n", messageLines[j])
			}
		}

		if verbose {
			fmt.Printf("  Size:     %d bytes\n", s.TotalSizeBytes)
			if s.MerkleRoot != "" {
				fmt.Printf("  Merkle:   %s\n", s.MerkleRoot[:16]+"...")
			}
			if s.PerformanceMetrics != nil {
				fmt.Printf("  Metrics:  ✓\n")
			}
			if s.ComplianceStatus != nil {
				fmt.Printf("  Compliance: ✓\n")
			}
		}
	}

	// Display pagination info
	if listLimit < len(states) || listOffset > 0 {
		fmt.Printf("\n")
		fmt.Printf("Showing %d states (offset: %d, limit: %d)\n", len(states), listOffset, listLimit)
		if len(states) == listLimit {
			fmt.Printf("Use --offset %d to see more\n", listOffset+listLimit)
		}
	}

	return nil
}