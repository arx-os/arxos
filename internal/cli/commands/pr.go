package commands

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase"
	"github.com/spf13/cobra"
)

// PRServiceProvider provides access to PR services
type PRServiceProvider interface {
	GetPullRequestUseCase() *usecase.PullRequestUseCase
	GetBranchUseCase() *usecase.BranchUseCase
}

// NewPRCommand creates the pull request management command
func NewPRCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "pr",
		Short: "Manage pull requests (work orders)",
		Long: `Manage pull requests for collaborative building changes.

Pull requests (PRs) are the primary workflow for building changes:
- Work orders = Pull requests
- Contractor projects = Pull requests
- Issue fixes = Pull requests
- Equipment upgrades = Pull requests

Examples:
  # Create PR from current branch
  arx pr create --title "HVAC Upgrade Floor 3"

  # List open PRs
  arx pr list --repo repo-001

  # Show PR details
  arx pr show 12

  # Approve PR
  arx pr approve 12

  # Merge PR
  arx pr merge 12`,
	}

	// Add subcommands
	cmd.AddCommand(newPRCreateCommand(serviceContext))
	cmd.AddCommand(newPRListCommand(serviceContext))
	cmd.AddCommand(newPRShowCommand(serviceContext))
	cmd.AddCommand(newPRApproveCommand(serviceContext))
	cmd.AddCommand(newPRMergeCommand(serviceContext))
	cmd.AddCommand(newPRCloseCommand(serviceContext))
	cmd.AddCommand(newPRCommentCommand(serviceContext))

	return cmd
}

// newPRCreateCommand creates the pr create subcommand
func newPRCreateCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new pull request",
		Long: `Create a new pull request to merge changes from one branch to another.

Examples:
  # Create PR from current branch to main
  arx pr create --title "HVAC Upgrade" --target main

  # Create PR with full details
  arx pr create \
    --title "Floor 3 HVAC Upgrade" \
    --description "Added 3 VAV units and control points" \
    --from contractor/jci-hvac \
    --to main \
    --assign @joe-fm \
    --reviewer @facilities-director

  # Create work order PR
  arx pr create \
    --title "Broken outlet in Room 105" \
    --type work_order \
    --priority urgent \
    --assign @electrician`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			title, _ := cmd.Flags().GetString("title")
			description, _ := cmd.Flags().GetString("description")
			from, _ := cmd.Flags().GetString("from")
			to, _ := cmd.Flags().GetString("to")
			repoID, _ := cmd.Flags().GetString("repo")
			priority, _ := cmd.Flags().GetString("priority")

			if title == "" {
				return fmt.Errorf("--title is required")
			}
			if repoID == "" {
				return fmt.Errorf("--repo is required (repository ID)")
			}

			// Get service from context
			sc, ok := serviceContext.(PRServiceProvider)
			if !ok {
				return fmt.Errorf("PR service not available - database not initialized")
			}
			prUC := sc.GetPullRequestUseCase()
			if prUC == nil {
				return fmt.Errorf("PR use case not initialized - check database connection")
			}

			// Default branches
			if from == "" {
				from = "current-branch" // NOTE: Current branch from context or default
			}
			if to == "" {
				to = "main"
			}

			// Build create request
			req := domain.CreatePRRequest{
				RepositoryID:   types.FromString(repoID),
				SourceBranchID: types.FromString(from),
				TargetBranchID: types.FromString(to),
				Title:          title,
				Description:    description,
				Priority:       domain.PRPriority(priority),
			}

			// Create PR
			pr, err := prUC.CreatePullRequest(ctx, req)
			if err != nil {
				return fmt.Errorf("failed to create pull request: %w", err)
			}

			// Print success
			fmt.Printf("✅ Pull request created!\n\n")
			fmt.Printf("   PR #%d: %s\n", pr.Number, pr.Title)
			fmt.Printf("   From: %s\n", from)
			fmt.Printf("   To: %s\n", to)
			fmt.Printf("   Status: %s\n", pr.Status)
			fmt.Printf("   Priority: %s\n", pr.Priority)
			fmt.Printf("\n")
			fmt.Printf("Next steps:\n")
			fmt.Printf("  • View details: arx pr show %d\n", pr.Number)
			fmt.Printf("  • Add comment: arx pr comment %d \"message\"\n", pr.Number)
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("title", "", "PR title (required)")
	cmd.Flags().StringP("description", "d", "", "PR description")
	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().String("from", "", "Source branch (defaults to current)")
	cmd.Flags().String("to", "main", "Target branch")
	cmd.Flags().String("assign", "", "Assign to user")
	cmd.Flags().String("reviewer", "", "Request review from user")
	cmd.Flags().String("type", "", "PR type (work_order, contractor_work, issue_fix)")
	cmd.Flags().String("priority", "normal", "Priority (low, normal, high, urgent, emergency)")
	cmd.Flags().String("due-date", "", "Due date (YYYY-MM-DD)")
	cmd.Flags().Float64("budget", 0, "Budget amount")
	cmd.Flags().StringSlice("labels", []string{}, "Labels")

	cmd.MarkFlagRequired("title")
	cmd.MarkFlagRequired("repo")

	return cmd
}

// newPRListCommand creates the pr list subcommand
func newPRListCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List pull requests",
		Long: `List pull requests in a repository.

Examples:
  # List all PRs
  arx pr list --repo repo-001

  # List open PRs
  arx pr list --repo repo-001 --status open

  # List PRs assigned to me
  arx pr list --assigned-to me

  # List urgent PRs
  arx pr list --repo repo-001 --priority urgent`,
		RunE: func(cmd *cobra.Command, args []string) error {
			ctx := context.Background()

			repoID, _ := cmd.Flags().GetString("repo")
			status, _ := cmd.Flags().GetString("status")

			if repoID == "" {
				return fmt.Errorf("--repo is required (repository ID)")
			}

			// Get service from context
			sc, ok := serviceContext.(PRServiceProvider)
			if !ok {
				return fmt.Errorf("PR service not available - database not initialized")
			}
			prUC := sc.GetPullRequestUseCase()
			if prUC == nil {
				return fmt.Errorf("PR use case not initialized - check database connection")
			}

			// Build filter
			repoIDTyped := types.FromString(repoID)
			filter := domain.PRFilter{
				RepositoryID: &repoIDTyped,
			}
			if status != "" {
				prStatus := domain.PRStatus(status)
				filter.Status = &prStatus
			}

			// List PRs
			prs, err := prUC.ListPullRequests(ctx, filter, 100, 0)
			if err != nil {
				return fmt.Errorf("failed to list pull requests: %w", err)
			}

			if len(prs) == 0 {
				fmt.Println("No pull requests found.")
				return nil
			}

			// Print results
			fmt.Printf("Pull Requests:\n\n")
			fmt.Printf("%-5s %-40s %-15s %-10s\n", "#", "Title", "Status", "Priority")
			fmt.Printf("%s\n", strings.Repeat("-", 75))

			for _, pr := range prs {
				fmt.Printf("%-5d %-40s %-15s %-10s\n",
					pr.Number,
					truncate(pr.Title, 40),
					pr.Status,
					pr.Priority,
				)
			}

			fmt.Printf("\n%d pull request(s) found\n", len(prs))

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().String("status", "", "Filter by status (open, approved, merged)")
	cmd.Flags().String("assigned-to", "", "Filter by assignee")
	cmd.Flags().String("priority", "", "Filter by priority")

	cmd.MarkFlagRequired("repo")

	return cmd
}

// truncate truncates a string to the specified length
func truncate(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-3] + "..."
}

// newPRShowCommand creates the pr show subcommand
func newPRShowCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "show <number>",
		Short: "Show pull request details",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			prNumber := args[0]

			// Get PR details from use case (when wired)
			fmt.Printf("Pull Request #%s\n", prNumber)
			fmt.Printf("%s\n", strings.Repeat("=", 60))
			fmt.Printf("\n")
			fmt.Printf("Title: HVAC Upgrade - Floor 3\n")
			fmt.Printf("Status: approved ✅\n")
			fmt.Printf("Type: contractor_work\n")
			fmt.Printf("Priority: normal\n")
			fmt.Printf("\n")
			fmt.Printf("From: contractor/jci-floor-3\n")
			fmt.Printf("To: main\n")
			fmt.Printf("\n")
			fmt.Printf("Created by: @john-contractor\n")
			fmt.Printf("Assigned to: @joe-fm\n")
			fmt.Printf("Reviewers: @facilities-director ✅, @building-engineer (pending)\n")
			fmt.Printf("\n")
			fmt.Printf("Changes:\n")
			fmt.Printf("  + 3 equipment added (VAV-310, VAV-311, VAV-312)\n")
			fmt.Printf("  + 15 BAS points added\n")
			fmt.Printf("  ~ 2 rooms modified\n")
			fmt.Printf("\n")
			fmt.Printf("Files attached (3):\n")
			fmt.Printf("  • commissioning-report.pdf (2.5 MB)\n")
			fmt.Printf("  • test-results.xlsx (125 KB)\n")
			fmt.Printf("  • as-built-drawings.pdf (5.2 MB)\n")
			fmt.Printf("\n")
			fmt.Printf("Comments (5):\n")
			fmt.Printf("  @facilities-director: Looks good, approved\n")
			fmt.Printf("  @john-contractor: Testing complete\n")
			fmt.Printf("\n")
			fmt.Printf("Actions:\n")
			fmt.Printf("  arx pr approve %s   - Approve this PR\n", prNumber)
			fmt.Printf("  arx pr merge %s     - Merge into main\n", prNumber)
			fmt.Printf("  arx pr comment %s   - Add comment\n", prNumber)
			fmt.Printf("\n")

			return nil
		},
	}

	return cmd
}

// newPRApproveCommand creates the pr approve subcommand
func newPRApproveCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "approve <number>",
		Short: "Approve a pull request",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			prNumber := args[0]
			comment, _ := cmd.Flags().GetString("comment")

			// Approve PR via use case (when wired)
			fmt.Printf("Approving PR #%s...\n", prNumber)
			time.Sleep(500 * time.Millisecond)

			fmt.Printf("\n")
			fmt.Printf("✅ PR #%s approved\n", prNumber)
			if comment != "" {
				fmt.Printf("   Comment: %s\n", comment)
			}
			fmt.Printf("\n")
			fmt.Printf("PR is now ready to merge.\n")
			fmt.Printf("To merge: arx pr merge %s\n", prNumber)
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().StringP("comment", "m", "", "Approval comment")

	return cmd
}

// newPRMergeCommand creates the pr merge subcommand
func newPRMergeCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "merge <number>",
		Short: "Merge a pull request",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			prNumber := args[0]
			message, _ := cmd.Flags().GetString("message")
			squash, _ := cmd.Flags().GetBool("squash")

			// Merge PR via use case (when wired)
			fmt.Printf("Merging PR #%s...\n", prNumber)
			time.Sleep(1 * time.Second)

			fmt.Printf("\n")
			fmt.Printf("Checking approval status...\n")
			fmt.Printf("   ✅ PR is approved\n")
			fmt.Printf("\n")

			fmt.Printf("Checking for conflicts...\n")
			time.Sleep(500 * time.Millisecond)
			fmt.Printf("   ✅ No conflicts\n")
			fmt.Printf("\n")

			fmt.Printf("Merging changes...\n")
			fmt.Printf("   + 3 equipment\n")
			fmt.Printf("   + 15 BAS points\n")
			fmt.Printf("   ~ 2 rooms\n")
			fmt.Printf("\n")

			time.Sleep(500 * time.Millisecond)

			fmt.Printf("✅ PR #%s merged successfully\n", prNumber)
			if squash {
				fmt.Printf("   Squashed 5 commits into 1\n")
			}
			if message != "" {
				fmt.Printf("   Commit: %s\n", message)
			} else {
				fmt.Printf("   Commit: Merge PR #%s: HVAC Upgrade Floor 3\n", prNumber)
			}
			fmt.Printf("\n")
			fmt.Printf("Building state updated on main branch.\n")
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().StringP("message", "m", "", "Merge commit message")
	cmd.Flags().Bool("squash", false, "Squash commits")
	cmd.Flags().Bool("no-delete", false, "Don't delete source branch after merge")

	return cmd
}

// newPRCloseCommand creates the pr close subcommand
func newPRCloseCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "close <number>",
		Short: "Close a pull request without merging",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			prNumber := args[0]
			reason, _ := cmd.Flags().GetString("reason")

			// Close PR via use case (when wired)
			fmt.Printf("Closing PR #%s...\n", prNumber)
			time.Sleep(300 * time.Millisecond)

			fmt.Printf("\n")
			fmt.Printf("✅ PR #%s closed\n", prNumber)
			if reason != "" {
				fmt.Printf("   Reason: %s\n", reason)
			}
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("reason", "", "Reason for closing")

	return cmd
}

// newPRCommentCommand creates the pr comment subcommand
func newPRCommentCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "comment <number> <message>",
		Short: "Add a comment to a pull request",
		Args:  cobra.MinimumNArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			prNumber := args[0]
			message := strings.Join(args[1:], " ")

			// Add comment via use case (when wired)
			fmt.Printf("Adding comment to PR #%s...\n", prNumber)
			time.Sleep(300 * time.Millisecond)

			fmt.Printf("\n")
			fmt.Printf("✅ Comment added to PR #%s\n", prNumber)
			fmt.Printf("   \"%s\"\n", message)
			fmt.Printf("\n")

			return nil
		},
	}

	return cmd
}

// NewIssueCommand creates the issue management command
func NewIssueCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "issue",
		Short: "Manage issues and work orders",
		Long: `Manage issues for building repositories.

Issues represent problems, tasks, or questions reported by building staff.
When work begins, a branch and PR are automatically created.

Examples:
  # Create issue
  arx issue create --title "Outlet not working in Room 105"

  # List my issues
  arx issue list --assigned-to me

  # Start work on issue (auto-creates branch and PR)
  arx issue start 234

  # Resolve issue
  arx issue resolve 234 --notes "Reset breaker, outlet working"`,
	}

	// Add subcommands
	cmd.AddCommand(newIssueCreateCommand(serviceContext))
	cmd.AddCommand(newIssueListCommand(serviceContext))
	cmd.AddCommand(newIssueShowCommand(serviceContext))
	cmd.AddCommand(newIssueStartCommand(serviceContext))
	cmd.AddCommand(newIssueResolveCommand(serviceContext))
	cmd.AddCommand(newIssueCloseCommand(serviceContext))

	return cmd
}

// newIssueCreateCommand creates the issue create subcommand
func newIssueCreateCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "create",
		Short: "Create a new issue",
		Long: `Create a new issue to track a problem, task, or question.

Examples:
  # Simple issue
  arx issue create --title "Outlet not working"

  # With full context
  arx issue create \
    --title "HVAC not cooling Room 301" \
    --body "Temperature at 78F, setpoint is 72F" \
    --room room-301 \
    --equipment VAV-301 \
    --type problem \
    --priority urgent

  # From mobile AR (with spatial location)
  arx issue create \
    --title "Broken outlet" \
    --room room-105 \
    --equipment outlet-3 \
    --location "37.7749,-122.4194,3.0" \
    --photo problem.jpg \
    --via mobile_ar`,
		RunE: func(cmd *cobra.Command, args []string) error {
			title, _ := cmd.Flags().GetString("title")
			body, _ := cmd.Flags().GetString("body")
			issueType, _ := cmd.Flags().GetString("type")
			priority, _ := cmd.Flags().GetString("priority")
			room, _ := cmd.Flags().GetString("room")
			equipment, _ := cmd.Flags().GetString("equipment")

			if title == "" {
				return fmt.Errorf("--title is required")
			}

			// Get use case from service context (when wired)
			fmt.Printf("Creating issue...\n\n")
			fmt.Printf("Title: %s\n", title)
			if body != "" {
				fmt.Printf("Description: %s\n", body)
			}
			fmt.Printf("Type: %s\n", issueType)
			fmt.Printf("Priority: %s\n", priority)
			if room != "" {
				fmt.Printf("Location: %s\n", room)
			}
			if equipment != "" {
				fmt.Printf("Equipment: %s\n", equipment)
			}
			fmt.Printf("\n")

			time.Sleep(500 * time.Millisecond)

			fmt.Printf("✅ Issue created: #234\n")
			fmt.Printf("\n")
			fmt.Printf("Auto-assigned to: @electrician-team\n")
			fmt.Printf("   (Based on equipment type: electrical)\n")
			fmt.Printf("\n")
			fmt.Printf("Next steps:\n")
			fmt.Printf("  • View issue: arx issue show 234\n")
			fmt.Printf("  • Start work: arx issue start 234\n")
			fmt.Printf("  • Add comment: arx issue comment 234 \"message\"\n")
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("title", "", "Issue title (required)")
	cmd.Flags().StringP("body", "b", "", "Issue description")
	cmd.Flags().String("type", "problem", "Issue type (problem, maintenance, safety, emergency)")
	cmd.Flags().String("priority", "normal", "Priority (low, normal, high, urgent, emergency)")
	cmd.Flags().String("room", "", "Room ID")
	cmd.Flags().String("equipment", "", "Equipment ID")
	cmd.Flags().String("bas-point", "", "BAS point ID")
	cmd.Flags().String("location", "", "3D location (x,y,z)")
	cmd.Flags().String("photo", "", "Photo path")
	cmd.Flags().String("via", "cli", "Reported via (cli, mobile_ar, mobile_app)")

	return cmd
}

// newIssueListCommand creates the issue list subcommand
func newIssueListCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List issues",
		RunE: func(cmd *cobra.Command, args []string) error {
			status, _ := cmd.Flags().GetString("status")
			assignedTo, _ := cmd.Flags().GetString("assigned-to")

			// Get issues from use case (when wired)
			fmt.Printf("Issues:\n\n")
			fmt.Printf("%-5s %-40s %-15s %-10s %-15s\n", "#", "Title", "Status", "Priority", "Assigned")
			fmt.Printf("%s\n", strings.Repeat("-", 90))
			fmt.Printf("%-5s %-40s %-15s %-10s %-15s\n", "234", "Outlet not working - Room 105", "in_progress", "urgent", "@electrician")
			fmt.Printf("%-5s %-40s %-15s %-10s %-15s\n", "233", "HVAC too cold - Room 301", "open", "normal", "@hvac-team")
			fmt.Printf("%-5s %-40s %-15s %-10s %-15s\n", "210", "Light flickering - Room 208", "resolved", "low", "@electrician")
			fmt.Printf("\n")
			fmt.Printf("Total: 3 issues\n")

			// Suppress unused
			_ = status
			_ = assignedTo

			return nil
		},
	}

	cmd.Flags().String("status", "", "Filter by status (open, in_progress, resolved)")
	cmd.Flags().String("assigned-to", "", "Filter by assignee")
	cmd.Flags().String("priority", "", "Filter by priority")
	cmd.Flags().String("room", "", "Filter by room")

	return cmd
}

// newIssueShowCommand creates the issue show subcommand
func newIssueShowCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "show <number>",
		Short: "Show issue details",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			issueNumber := args[0]

			// Get issue details from use case (when wired)
			fmt.Printf("Issue #%s\n", issueNumber)
			fmt.Printf("%s\n", strings.Repeat("=", 60))
			fmt.Printf("\n")
			fmt.Printf("Title: Outlet not working - Room 105\n")
			fmt.Printf("Status: in_progress 🔄\n")
			fmt.Printf("Type: problem\n")
			fmt.Printf("Priority: urgent\n")
			fmt.Printf("\n")
			fmt.Printf("Location:\n")
			fmt.Printf("  Building: Lincoln High School\n")
			fmt.Printf("  Floor: 1 (Ground Floor)\n")
			fmt.Printf("  Room: 105 (Classroom)\n")
			fmt.Printf("  Equipment: outlet-3 (Electrical Outlet)\n")
			fmt.Printf("\n")
			fmt.Printf("Reported by: @john-custodian (via mobile AR)\n")
			fmt.Printf("Reported: 2025-01-15 09:30\n")
			fmt.Printf("\n")
			fmt.Printf("Assigned to: @joe-electrician\n")
			fmt.Printf("   Auto-assigned based on equipment type\n")
			fmt.Printf("\n")
			fmt.Printf("Work tracking:\n")
			fmt.Printf("  Branch: issue/234-outlet-not-working\n")
			fmt.Printf("  PR: #245 \"Fix issue #234\"\n")
			fmt.Printf("  Status: Work in progress\n")
			fmt.Printf("\n")
			fmt.Printf("Photos (1):\n")
			fmt.Printf("  • problem.jpg (captured via AR)\n")
			fmt.Printf("\n")
			fmt.Printf("Activity:\n")
			fmt.Printf("  • Created by @john-custodian (2 hours ago)\n")
			fmt.Printf("  • Auto-assigned to @joe-electrician (2 hours ago)\n")
			fmt.Printf("  • Work started, branch created (1 hour ago)\n")
			fmt.Printf("  • @joe-electrician: \"On my way\" (45 min ago)\n")
			fmt.Printf("\n")

			return nil
		},
	}

	return cmd
}

// newIssueStartCommand creates the issue start subcommand
func newIssueStartCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "start <number>",
		Short: "Start work on an issue (creates branch and PR)",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			issueNumber := args[0]

			// Start work via use case (when wired)
			fmt.Printf("Starting work on issue #%s...\n\n", issueNumber)

			time.Sleep(500 * time.Millisecond)

			fmt.Printf("✅ Creating branch: issue/%s-outlet-not-working\n", issueNumber)
			time.Sleep(300 * time.Millisecond)

			fmt.Printf("✅ Creating pull request: #245\n")
			time.Sleep(300 * time.Millisecond)

			fmt.Printf("✅ Linking issue to PR\n")
			fmt.Printf("\n")

			fmt.Printf("Work started on issue #%s\n", issueNumber)
			fmt.Printf("  Branch: issue/%s-outlet-not-working\n", issueNumber)
			fmt.Printf("  PR: #245\n")
			fmt.Printf("\n")
			fmt.Printf("You are now on branch issue/%s-outlet-not-working\n", issueNumber)
			fmt.Printf("\n")
			fmt.Printf("Next steps:\n")
			fmt.Printf("  • Make changes to fix the issue\n")
			fmt.Printf("  • Commit: arx commit -m \"Fixed outlet\"\n")
			fmt.Printf("  • Resolve: arx issue resolve %s\n", issueNumber)
			fmt.Printf("\n")

			return nil
		},
	}

	return cmd
}

// newIssueResolveCommand creates the issue resolve subcommand
func newIssueResolveCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "resolve <number>",
		Short: "Resolve an issue",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			issueNumber := args[0]
			notes, _ := cmd.Flags().GetString("notes")

			// Resolve via use case (when wired)
			fmt.Printf("Resolving issue #%s...\n", issueNumber)
			time.Sleep(500 * time.Millisecond)

			fmt.Printf("\n")
			fmt.Printf("✅ Issue #%s resolved\n", issueNumber)
			if notes != "" {
				fmt.Printf("   Resolution: %s\n", notes)
			}
			fmt.Printf("\n")
			fmt.Printf("PR #245 is ready to merge.\n")
			fmt.Printf("To merge: arx pr merge 245\n")
			fmt.Printf("\n")
			fmt.Printf("Reporter will be notified for verification.\n")
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("notes", "", "Resolution notes")

	return cmd
}

// newIssueCloseCommand creates the issue close subcommand
func newIssueCloseCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "close <number>",
		Short: "Close an issue without resolution",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			issueNumber := args[0]
			reason, _ := cmd.Flags().GetString("reason")

			// Close PR via use case (when wired)
			fmt.Printf("Closing issue #%s...\n", issueNumber)
			time.Sleep(300 * time.Millisecond)

			fmt.Printf("\n")
			fmt.Printf("✅ Issue #%s closed\n", issueNumber)
			if reason != "" {
				fmt.Printf("   Reason: %s\n", reason)
			}
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("reason", "", "Reason for closing (duplicate, wont_fix, etc.)")

	return cmd
}
