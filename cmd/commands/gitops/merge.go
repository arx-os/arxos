package gitops

import (
	"context"
	"encoding/json"
	"fmt"

	"github.com/arxos/arxos/core/internal/gitops"
	"github.com/arxos/arxos/core/internal/state"
	"github.com/spf13/cobra"
)

var mergeCmd = &cobra.Command{
	Use:   "merge [building-id] [source-branch]",
	Short: "Merge branches directly",
	Long: `Merge a source branch into the current branch without creating a pull request.
	
This is useful for simple merges or when working locally.`,
	Args: cobra.ExactArgs(2),
	RunE: runMerge,
}

var (
	mergeTarget   string
	mergeStrategy string
	mergeMessage  string
	mergeDryRun   bool
	mergeNoCommit bool
)

func init() {
	mergeCmd.Flags().StringVarP(&mergeTarget, "target", "t", "", "Target branch (default: current)")
	mergeCmd.Flags().StringVarP(&mergeStrategy, "strategy", "s", "merge", "Merge strategy (fast-forward/merge/squash/rebase)")
	mergeCmd.Flags().StringVarP(&mergeMessage, "message", "m", "", "Merge commit message")
	mergeCmd.Flags().BoolVar(&mergeDryRun, "dry-run", false, "Show what would be merged without doing it")
	mergeCmd.Flags().BoolVar(&mergeNoCommit, "no-commit", false, "Perform merge but don't create commit")
}

func runMerge(cmd *cobra.Command, args []string) error {
	buildingID := args[0]
	sourceBranch := args[1]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create managers
	stateManager := state.NewManager(db)
	branchManager := gitops.NewBranchManager(db, stateManager)
	mergeEngine := gitops.NewMergeEngine(db, stateManager, branchManager)

	ctx := context.Background()

	// Get target branch (current if not specified)
	if mergeTarget == "" {
		current, err := branchManager.GetCurrentBranch(ctx, buildingID)
		if err != nil {
			return fmt.Errorf("failed to get current branch: %w", err)
		}
		mergeTarget = current.Name
	}

	// Set default message
	if mergeMessage == "" {
		mergeMessage = fmt.Sprintf("Merge branch '%s' into '%s'", sourceBranch, mergeTarget)
	}

	// Map strategy
	strategyMap := map[string]gitops.MergeStrategy{
		"fast-forward": gitops.MergeStrategyFastForward,
		"merge":        gitops.MergeStrategyMerge,
		"squash":       gitops.MergeStrategySquash,
		"rebase":       gitops.MergeStrategyRebase,
	}

	strategy, ok := strategyMap[mergeStrategy]
	if !ok {
		return fmt.Errorf("invalid merge strategy: %s", mergeStrategy)
	}

	// Perform merge
	mergeReq := &gitops.MergeRequest{
		BuildingID:   buildingID,
		SourceBranch: sourceBranch,
		TargetBranch: mergeTarget,
		Strategy:     strategy,
		Author:       getCurrentUser(),
		Message:      mergeMessage,
		DryRun:       mergeDryRun || mergeNoCommit,
	}

	result, err := mergeEngine.Merge(ctx, mergeReq)
	if err != nil {
		return fmt.Errorf("merge failed: %w", err)
	}

	// Output result
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		jsonData, _ := json.MarshalIndent(result, "", "  ")
		fmt.Printf("%s\n", jsonData)
	} else {
		if mergeDryRun {
			fmt.Println("Dry run - no changes made")
		}

		if result.Success {
			fmt.Printf("✓ Merge successful\n")
			if !mergeDryRun && !mergeNoCommit {
				fmt.Printf("Merged state: %s\n", result.MergeStateID[:8])
			}
			fmt.Printf("Strategy: %s\n", result.Strategy)
			fmt.Printf("Changes: %d\n", len(result.Changes))
			
			if len(result.Changes) > 0 && len(result.Changes) <= 10 {
				fmt.Println("\nChanges:")
				for _, change := range result.Changes {
					fmt.Printf("  %s %s: %s\n", 
						getChangeTypeIcon(change.Type),
						change.ObjectID[:8],
						change.Description)
				}
			}
		} else {
			fmt.Printf("✗ Merge failed\n")
			if len(result.Conflicts) > 0 {
				fmt.Printf("\nConflicts detected (%d):\n", len(result.Conflicts))
				for _, conflict := range result.Conflicts {
					fmt.Printf("  - %s (%s): %s\n",
						conflict.ObjectID,
						conflict.Type,
						conflict.Description)
				}
				fmt.Println("\nResolve conflicts and try again, or use a pull request for collaborative resolution")
			}
		}
	}

	return nil
}

func getChangeTypeIcon(changeType string) string {
	switch changeType {
	case "add":
		return "+"
	case "modify":
		return "~"
	case "delete":
		return "-"
	default:
		return "?"
	}
}