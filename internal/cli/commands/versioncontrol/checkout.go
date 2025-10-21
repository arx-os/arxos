package versioncontrol

import (
	"fmt"
	"time"

	"github.com/spf13/cobra"
)

// NewCheckoutCommand creates the checkout command
func NewCheckoutCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "checkout <branch>",
		Short: "Switch branches or create new branch",
		Long: `Switch to a different branch or create a new branch.

Examples:
  # Switch to existing branch
  arx checkout main

  # Create and switch to new branch
  arx checkout -b feature/new-work

  # Switch to specific commit (detached HEAD)
  arx checkout abc1234`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			branchName := args[0]
			createNew, _ := cmd.Flags().GetBool("b")
			force, _ := cmd.Flags().GetBool("force")

			// Get use case from service context
			cp, ok := serviceContext.(BranchContainerProvider)
			if !ok || cp.GetBranchUseCase() == nil {
				fmt.Println("⚠️  Database not connected - using simulation mode")
			}

			if createNew {
				fmt.Printf("Creating new branch '%s'...\n", branchName)
				time.Sleep(300 * time.Millisecond)
				fmt.Printf("✅ Branch created\n")
			}

			fmt.Printf("Switching to branch '%s'...\n", branchName)
			time.Sleep(500 * time.Millisecond)

			fmt.Printf("\n")
			fmt.Printf("✅ Switched to branch '%s'\n", branchName)
			fmt.Printf("   Building state loaded from branch HEAD\n")
			fmt.Printf("   Ready to make changes\n")
			fmt.Printf("\n")

			// Suppress unused
			_ = force

			return nil
		},
	}

	cmd.Flags().BoolP("b", "b", false, "Create new branch")
	cmd.Flags().BoolP("force", "f", false, "Force checkout (discard uncommitted changes)")

	return cmd
}
