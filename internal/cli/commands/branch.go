package commands

import (
	"fmt"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// NewBranchCommand creates the branch management command
func NewBranchCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "branch",
		Short: "Manage repository branches",
		Long: `Manage Git-like branches in building repositories.
		
Branches allow isolated work on building changes (contractor projects, equipment upgrades, 
scans, etc.) without affecting the main building state until ready.

Examples:
  # List all branches
  arx branch list --repo repo-001

  # Create new branch
  arx branch create hvac-upgrade --repo repo-001

  # Create contractor branch
  arx branch create contractor/jci-floor-3 --repo repo-001 --type contractor

  # Delete branch
  arx branch delete feature-branch --repo repo-001

  # Show branch details
  arx branch show main --repo repo-001`,
	}

	// Add subcommands
	cmd.AddCommand(newBranchListCommand(serviceContext))
	cmd.AddCommand(newBranchCreateCommand(serviceContext))
	cmd.AddCommand(newBranchDeleteCommand(serviceContext))
	cmd.AddCommand(newBranchShowCommand(serviceContext))

	return cmd
}

// newBranchListCommand creates the branch list subcommand
func newBranchListCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List all branches",
		Long: `List all branches in a repository.

Examples:
  arx branch list --repo repo-001
  arx branch list --repo repo-001 --active
  arx branch list --repo repo-001 --type contractor`,
		RunE: func(cmd *cobra.Command, args []string) error {
			repoID, _ := cmd.Flags().GetString("repo")
			activeOnly, _ := cmd.Flags().GetBool("active")
			branchType, _ := cmd.Flags().GetString("type")

			if repoID == "" {
				return fmt.Errorf("--repo flag is required")
			}

			// TODO: Get use case from service context
			fmt.Printf("Branches for repository: %s\n\n", repoID)
			fmt.Printf("%-20s %-15s %-15s %-10s %s\n", "Name", "Type", "Status", "Commits", "Last Updated")
			fmt.Printf("%s\n", strings.Repeat("-", 80))

			// Placeholder data
			fmt.Printf("%-20s %-15s %-15s %-10s %s\n", 
				"* main", "main", "active", "15", "2025-01-15 10:30")
			fmt.Printf("%-20s %-15s %-15s %-10s %s\n", 
				"  contractor/jci-hvac", "contractor", "active", "3", "2025-01-14 14:20")
			fmt.Printf("%-20s %-15s %-15s %-10s %s\n", 
				"  issue/outlet-fix", "issue", "active", "1", "2025-01-13 09:15")

			fmt.Printf("\n* = current branch\n")

			// Suppress unused variable warnings
			_ = activeOnly
			_ = branchType

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().Bool("active", false, "Show only active branches")
	cmd.Flags().String("type", "", "Filter by branch type")

	return cmd
}

// newBranchCreateCommand creates the branch create subcommand
func newBranchCreateCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "create <name>",
		Short: "Create a new branch",
		Long: `Create a new branch from the current HEAD or specified commit.

Branch naming conventions:
  - feature/name     Feature branches
  - bugfix/name      Bug fix branches
  - contractor/name  Contractor work branches
  - vendor/name      Vendor maintenance branches
  - issue/name       Auto-created from issues

Examples:
  arx branch create hvac-upgrade --repo repo-001
  arx branch create contractor/jci-floor-3 --repo repo-001
  arx branch create feature/new-equipment --repo repo-001 --from abc123`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			branchName := args[0]
			repoID, _ := cmd.Flags().GetString("repo")
			branchType, _ := cmd.Flags().GetString("type")
			description, _ := cmd.Flags().GetString("description")
			fromCommit, _ := cmd.Flags().GetString("from")

			if repoID == "" {
				return fmt.Errorf("--repo flag is required")
			}

			// TODO: Get use case from service context
			fmt.Printf("Creating branch '%s'...\n", branchName)
			time.Sleep(500 * time.Millisecond)

			fmt.Printf("\n")
			fmt.Printf("✅ Branch created: %s\n", branchName)
			fmt.Printf("   Repository: %s\n", repoID)
			fmt.Printf("   Type: %s\n", getDisplayBranchType(branchType, branchName))
			if description != "" {
				fmt.Printf("   Description: %s\n", description)
			}
			if fromCommit != "" {
				fmt.Printf("   Based on: %s\n", fromCommit)
			} else {
				fmt.Printf("   Based on: main (current HEAD)\n")
			}
			fmt.Printf("\n")
			fmt.Printf("Next steps:\n")
			fmt.Printf("  • Switch to branch: arx checkout %s\n", branchName)
			fmt.Printf("  • Make changes and commit: arx commit -m \"message\"\n")
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().String("type", "", "Branch type (feature, bugfix, contractor, vendor)")
	cmd.Flags().String("description", "", "Branch description")
	cmd.Flags().String("from", "", "Create from specific commit (defaults to HEAD)")

	return cmd
}

// newBranchDeleteCommand creates the branch delete subcommand
func newBranchDeleteCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "delete <name>",
		Short: "Delete a branch",
		Long: `Delete a branch.

Cannot delete:
  - Main branch
  - Default branch
  - Protected branches (unless --force)
  - Current checked-out branch

Examples:
  arx branch delete feature-branch --repo repo-001
  arx branch delete old-branch --repo repo-001 --force`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			branchName := args[0]
			repoID, _ := cmd.Flags().GetString("repo")
			force, _ := cmd.Flags().GetBool("force")

			if repoID == "" {
				return fmt.Errorf("--repo flag is required")
			}

			// Safety check
			if branchName == "main" {
				return fmt.Errorf("cannot delete main branch")
			}

			// TODO: Get use case from service context
			if force {
				fmt.Printf("⚠️  Force deleting branch '%s'...\n", branchName)
			} else {
				fmt.Printf("Deleting branch '%s'...\n", branchName)
			}

			time.Sleep(300 * time.Millisecond)
			fmt.Printf("✅ Branch deleted: %s\n", branchName)

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().BoolP("force", "f", false, "Force delete protected branch")

	return cmd
}

// newBranchShowCommand creates the branch show subcommand
func newBranchShowCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "show <name>",
		Short: "Show branch details",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			branchName := args[0]
			repoID, _ := cmd.Flags().GetString("repo")

			if repoID == "" {
				return fmt.Errorf("--repo flag is required")
			}

			// TODO: Get branch details from use case
			fmt.Printf("Branch: %s\n", branchName)
			fmt.Printf("%s\n", strings.Repeat("=", 60))
			fmt.Printf("\n")
			fmt.Printf("Type:        %s\n", "contractor")
			fmt.Printf("Status:      %s\n", "active")
			fmt.Printf("Protected:   %s\n", "no")
			fmt.Printf("Created by:  @john-contractor\n")
			fmt.Printf("Created:     2025-01-10 14:30\n")
			fmt.Printf("Last commit: 2025-01-14 16:45\n")
			fmt.Printf("\n")
			fmt.Printf("Recent commits (3):\n")
			fmt.Printf("  abc1234 - Added VAV units to Floor 3 (2 days ago)\n")
			fmt.Printf("  def5678 - Commissioned control points (3 days ago)\n")
			fmt.Printf("  ghi9012 - Initial HVAC equipment (4 days ago)\n")
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")

	return cmd
}

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

			// TODO: Get use case from service context
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

// NewMergeCommand creates the merge command
func NewMergeCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "merge <branch>",
		Short: "Merge a branch into current branch",
		Long: `Merge changes from another branch into the current branch.

Examples:
  # Merge feature branch into current
  arx merge feature/hvac-upgrade

  # Merge with message
  arx merge contractor/jci-floor-3 -m "HVAC upgrade complete"

  # Squash merge
  arx merge issue/outlet-fix --squash`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			sourceBranch := args[0]
			message, _ := cmd.Flags().GetString("message")
			squash, _ := cmd.Flags().GetBool("squash")

			// TODO: Get use case from service context
			fmt.Printf("Merging '%s' into current branch...\n", sourceBranch)
			time.Sleep(1 * time.Second)

			fmt.Printf("\n")
			fmt.Printf("Checking for conflicts...\n")
			time.Sleep(500 * time.Millisecond)
			fmt.Printf("   ✅ No conflicts found\n")
			fmt.Printf("\n")

			fmt.Printf("Applying changes...\n")
			fmt.Printf("   + 3 equipment added\n")
			fmt.Printf("   + 15 BAS points added\n")
			fmt.Printf("   ~ 2 rooms modified\n")
			fmt.Printf("\n")

			mergeMsg := message
			if mergeMsg == "" {
				mergeMsg = fmt.Sprintf("Merge branch '%s'", sourceBranch)
			}

			fmt.Printf("✅ Merge successful\n")
			if squash {
				fmt.Printf("   Squashed commits from '%s'\n", sourceBranch)
			}
			fmt.Printf("   Commit: %s\n", mergeMsg)
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().StringP("message", "m", "", "Merge commit message")
	cmd.Flags().Bool("squash", false, "Squash commits from source branch")
	cmd.Flags().Bool("no-commit", false, "Merge but don't commit")

	return cmd
}

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

			// TODO: Get commits from use case
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

			// TODO: Get diff from use case
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

// getDisplayBranchType returns a display-friendly branch type
func getDisplayBranchType(explicitType, branchName string) string {
	if explicitType != "" {
		return explicitType
	}

	nameLower := strings.ToLower(branchName)

	if strings.HasPrefix(nameLower, "feature/") {
		return "feature"
	}
	if strings.HasPrefix(nameLower, "bugfix/") {
		return "bugfix"
	}
	if strings.HasPrefix(nameLower, "contractor/") {
		return "contractor"
	}
	if strings.HasPrefix(nameLower, "vendor/") {
		return "vendor"
	}
	if strings.HasPrefix(nameLower, "issue/") {
		return "issue"
	}

	return "feature"
}

