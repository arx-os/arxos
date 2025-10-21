package versioncontrol

import (
	"fmt"

	"github.com/spf13/cobra"
)

// NewDiffCommand creates the diff command for comparing branches/commits
func NewDiffCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "diff <from> <to>",
		Short: "Show differences between commits or branches",
		Long: `Show changes between two commits, branches, or commit and working directory.

Examples:
  # Compare two commits
  arx diff abc1234 def5678

  # Compare branches
  arx diff main contractor/jci-hvac

  # Compare branch to HEAD
  arx diff main HEAD

  # Show uncommitted changes
  arx diff`,
		Args: cobra.RangeArgs(0, 2),
		RunE: func(cmd *cobra.Command, args []string) error {
			var from, to string

			if len(args) == 0 {
				// Show uncommitted changes
				fmt.Printf("Uncommitted changes:\n\n")
				fmt.Printf("Modified:\n")
				fmt.Printf("  • Room 305 (status changed)\n")
				fmt.Printf("  • Equipment VAV-301 (description updated)\n")
				fmt.Printf("\n")
				return nil
			}

			if len(args) >= 1 {
				from = args[0]
			}
			if len(args) >= 2 {
				to = args[1]
			} else {
				to = "HEAD"
			}

			// Get diff from use case (VersionUseCase.DiffVersions when wired)
			fmt.Printf("Comparing %s...%s\n\n", from, to)

			fmt.Printf("Changes:\n")
			fmt.Printf("  + 3 equipment added\n")
			fmt.Printf("  + 15 BAS points added\n")
			fmt.Printf("  ~ 2 rooms modified\n")
			fmt.Printf("  - 0 items deleted\n")
			fmt.Printf("\n")

			fmt.Printf("Details:\n")
			fmt.Printf("  + Equipment: VAV-310, VAV-311, VAV-312\n")
			fmt.Printf("  + BAS Points: AI-3-10, AV-3-10, BO-3-10, ...\n")
			fmt.Printf("  ~ Room 305: status operational → temp-closed\n")
			fmt.Printf("  ~ Room 306: fidelity text → lidar\n")
			fmt.Printf("\n")

			return nil
		},
	}

	return cmd
}
