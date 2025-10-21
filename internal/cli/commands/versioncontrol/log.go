package versioncontrol

import (
	"fmt"

	"github.com/spf13/cobra"
)

// NewLogCommand creates the log command for viewing commit history
func NewLogCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "log",
		Short: "Show commit history",
		Long: `Show commit history for current branch or repository.

Examples:
  # Show recent commits
  arx log

  # Show commits for specific branch
  arx log --branch contractor/jci-hvac

  # Show commits since date
  arx log --since "2025-01-01"

  # Show commits by author
  arx log --author john@contractor.com`,
		RunE: func(cmd *cobra.Command, args []string) error {
			branch, _ := cmd.Flags().GetString("branch")
			since, _ := cmd.Flags().GetString("since")
			author, _ := cmd.Flags().GetString("author")
			limit, _ := cmd.Flags().GetInt("limit")

			// Get commits from use case (CommitUseCase when wired)
			fmt.Printf("Commit History:\n\n")

			// Placeholder commits
			commits := []struct {
				hash    string
				message string
				author  string
				date    string
				changes string
			}{
				{"abc1234", "Added BAS points from Metasys", "john@facilities.com", "2 hours ago", "+145 points"},
				{"def5678", "Imported IFC architectural data", "jane@architect.com", "2 days ago", "+50 rooms"},
				{"ghi9012", "Initial repository creation", "admin@district.com", "1 week ago", ""},
			}

			for _, c := range commits {
				fmt.Printf("commit %s\n", c.hash)
				fmt.Printf("Author: %s\n", c.author)
				fmt.Printf("Date:   %s\n", c.date)
				fmt.Printf("\n")
				fmt.Printf("    %s\n", c.message)
				if c.changes != "" {
					fmt.Printf("    %s\n", c.changes)
				}
				fmt.Printf("\n")
			}

			// Suppress unused
			_ = branch
			_ = since
			_ = author
			_ = limit

			return nil
		},
	}

	cmd.Flags().String("branch", "", "Show history for specific branch")
	cmd.Flags().String("since", "", "Show commits since date")
	cmd.Flags().String("author", "", "Filter by author")
	cmd.Flags().IntP("limit", "n", 10, "Limit number of commits")

	return cmd
}
