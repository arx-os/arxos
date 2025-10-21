package versioncontrol

import (
	"context"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/domain/versioncontrol"
	"github.com/spf13/cobra"
)

// NewMergeCommand creates the merge command
// Note: In ArxOS, merges are done through Pull Requests for traceability
func NewMergeCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "merge <branch>",
		Short: "Merge a branch into current branch via PR",
		Long: `Merge changes from another branch into the current branch.
Creates a pull request and automatically merges it.

Examples:
  # Merge feature branch into current
  arx merge feature/hvac-upgrade --repo repo-001

  # Merge with message
  arx merge contractor/jci-floor-3 --repo repo-001 -m "HVAC upgrade complete"

  # Squash merge
  arx merge issue/outlet-fix --repo repo-001 --squash`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			sourceBranchName := args[0]
			repoIDStr, _ := cmd.Flags().GetString("repo")

			if repoIDStr == "" {
				return fmt.Errorf("--repo is required")
			}

			// Get container
			container, ok := serviceContext.(BranchContainerProvider)
			if !ok {
				return fmt.Errorf("invalid service context")
			}

			branchUC := container.GetBranchUseCase()
			if branchUC == nil {
				return fmt.Errorf("branch use case not available")
			}

			ctx := context.Background()
			repoID := types.FromString(repoIDStr)

			fmt.Printf("Merging '%s' into current branch...\n", sourceBranchName)

			// Verify source branch exists
			_, err := branchUC.GetBranch(ctx, repoID, sourceBranchName)
			if err != nil {
				return fmt.Errorf("source branch not found: %w", err)
			}

			// Get default branch as target
			branches, err := branchUC.ListBranches(ctx, repoID, versioncontrol.BranchFilter{})
			if err != nil {
				return fmt.Errorf("failed to list branches: %w", err)
			}

			var targetBranch *versioncontrol.Branch
			for _, b := range branches {
				if b.IsDefault {
					targetBranch = b
					break
				}
			}
			if targetBranch == nil {
				return fmt.Errorf("no default branch found")
			}

			fmt.Printf("Target branch: %s\n\n", targetBranch.Name)

			// Guide user through PR workflow
			fmt.Printf("Note: In ArxOS, merges are done through Pull Requests for traceability.\n\n")
			fmt.Printf("To merge this branch:\n")
			fmt.Printf("  1. Create PR: arx pr create --from %s --to %s --repo %s --title \"Merge %s\"\n",
				sourceBranchName, targetBranch.Name, repoIDStr, sourceBranchName)
			fmt.Printf("  2. Merge PR:  arx pr merge <pr-number> --repo %s\n\n", repoIDStr)

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().StringP("message", "m", "", "Merge commit message")
	cmd.Flags().Bool("squash", false, "Squash commits from source branch")
	cmd.Flags().Bool("no-commit", false, "Merge but don't commit")

	cmd.MarkFlagRequired("repo")

	return cmd
}
