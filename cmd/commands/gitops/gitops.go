package gitops

import (
	"github.com/spf13/cobra"
)

// GitOpsCmd represents the gitops command group
var GitOpsCmd = &cobra.Command{
	Use:   "gitops",
	Short: "GitOps operations for building configuration management",
	Long: `GitOps provides version control and collaboration features for building configurations.

This includes branch management, pull requests, code reviews, and merge operations
for Building Infrastructure as Code (BIaC).`,
}

func init() {
	// Add subcommands
	GitOpsCmd.AddCommand(
		branchCmd,
		prCmd,
		mergeCmd,
		diffCmd,
		protectCmd,
	)
}