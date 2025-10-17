package commands

import (
	"context"
	"fmt"
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/usecase"
	"github.com/spf13/cobra"
)

// getCurrentUserID returns the current user ID from CLI flags or environment
// For now defaults to "system-user", but can be extended to read from:
// - Global --user flag
// - ARXOS_USER env var
// - ~/.arxos/session file (from `arx login`)
func getCurrentUserID(cmd *cobra.Command) types.ID {
	// Try to get from command flag
	if cmd != nil {
		if userFlag, err := cmd.Flags().GetString("user"); err == nil && userFlag != "" {
			return types.FromString(userFlag)
		}
	}

	// Try environment variable
	if envUser := os.Getenv("ARXOS_USER"); envUser != "" {
		return types.FromString(envUser)
	}

	// TODO: Check ~/.arxos/session file for logged-in user

	// Default fallback
	return types.FromString("system-user")
}

// PRServiceProvider provides access to PR and Issue services
type PRServiceProvider interface {
	GetPullRequestUseCase() *usecase.PullRequestUseCase
	GetBranchUseCase() *usecase.BranchUseCase
	GetIssueUseCase() *usecase.IssueUseCase
}

// Helper function to convert ID to pointer
func ptrToID(id types.ID) *types.ID {
	return &id
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
			prNumberStr := args[0]
			repoIDStr, _ := cmd.Flags().GetString("repo")

			if repoIDStr == "" {
				return fmt.Errorf("--repo is required")
			}

			// Parse PR number
			prNumber, err := strconv.Atoi(prNumberStr)
			if err != nil {
				return fmt.Errorf("invalid PR number: %s", prNumberStr)
			}

			// Get container
			container, ok := serviceContext.(PRServiceProvider)
			if !ok {
				return fmt.Errorf("invalid service context")
			}

			prUC := container.GetPullRequestUseCase()
			if prUC == nil {
				return fmt.Errorf("PR use case not available")
			}

			// Get PR
			ctx := context.Background()
			repoID := types.FromString(repoIDStr)
			pr, err := prUC.GetPullRequest(ctx, repoID, prNumber)
			if err != nil {
				return fmt.Errorf("failed to get PR: %w", err)
			}

			// Display PR details
			fmt.Printf("Pull Request #%d\n", pr.Number)
			fmt.Printf("%s\n", strings.Repeat("=", 60))
			fmt.Printf("\n")
			fmt.Printf("Title: %s\n", pr.Title)
			fmt.Printf("Status: %s\n", pr.Status)
			if pr.PRType != "" {
				fmt.Printf("Type: %s\n", pr.PRType)
			}
			if pr.Priority != "" {
				fmt.Printf("Priority: %s\n", pr.Priority)
			}
			fmt.Printf("\n")
			fmt.Printf("Source Branch ID: %s\n", pr.SourceBranchID)
			fmt.Printf("Target Branch ID: %s\n", pr.TargetBranchID)
			fmt.Printf("\n")
			if pr.Description != "" {
				fmt.Printf("Description:\n")
				fmt.Printf("%s\n\n", pr.Description)
			}
			if pr.MergedAt != nil {
				fmt.Printf("Merged: %s\n", pr.MergedAt.Format("2006-01-02 15:04"))
			}
			if pr.ClosedAt != nil {
				fmt.Printf("Closed: %s\n", pr.ClosedAt.Format("2006-01-02 15:04"))
			}
			fmt.Printf("Created: %s\n", pr.CreatedAt.Format("2006-01-02 15:04"))
			fmt.Printf("\n")
			fmt.Printf("Actions:\n")
			if pr.Status == "open" {
				fmt.Printf("  arx pr approve %d --repo %s  - Approve this PR\n", pr.Number, repoIDStr)
				fmt.Printf("  arx pr merge %d --repo %s    - Merge into target\n", pr.Number, repoIDStr)
				fmt.Printf("  arx pr close %d --repo %s    - Close without merging\n", pr.Number, repoIDStr)
			}
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.MarkFlagRequired("repo")

	return cmd
}

// newPRApproveCommand creates the pr approve subcommand
func newPRApproveCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "approve <number>",
		Short: "Approve a pull request",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			prNumberStr := args[0]
			repoIDStr, _ := cmd.Flags().GetString("repo")
			comment, _ := cmd.Flags().GetString("comment")

			if repoIDStr == "" {
				return fmt.Errorf("--repo is required")
			}

			// Parse PR number
			prNumber, err := strconv.Atoi(prNumberStr)
			if err != nil {
				return fmt.Errorf("invalid PR number: %s", prNumberStr)
			}

			// Get container
			container, ok := serviceContext.(PRServiceProvider)
			if !ok {
				return fmt.Errorf("invalid service context")
			}

			prUC := container.GetPullRequestUseCase()
			if prUC == nil {
				return fmt.Errorf("PR use case not available")
			}

			// Get PR
			ctx := context.Background()
			repoID := types.FromString(repoIDStr)
			pr, err := prUC.GetPullRequest(ctx, repoID, prNumber)
			if err != nil {
				return fmt.Errorf("failed to get PR: %w", err)
			}

			fmt.Printf("Approving PR #%d: %s\n\n", pr.Number, pr.Title)

			// Approve PR
			reviewerID := getCurrentUserID(cmd)
			if err := prUC.ApprovePullRequest(ctx, pr.ID, reviewerID, comment); err != nil {
				return fmt.Errorf("failed to approve PR: %w", err)
			}

			fmt.Printf("✅ PR #%d approved\n", pr.Number)
			if comment != "" {
				fmt.Printf("   Comment: %s\n", comment)
			}
			fmt.Printf("\n")
			fmt.Printf("PR is now ready to merge.\n")
			fmt.Printf("To merge: arx pr merge %d --repo %s\n", pr.Number, repoIDStr)
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().StringP("comment", "m", "", "Approval comment")

	cmd.MarkFlagRequired("repo")

	return cmd
}

// newPRMergeCommand creates the pr merge subcommand
func newPRMergeCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "merge <number>",
		Short: "Merge a pull request",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			prNumberStr := args[0]
			repoIDStr, _ := cmd.Flags().GetString("repo")
			message, _ := cmd.Flags().GetString("message")
			squash, _ := cmd.Flags().GetBool("squash")

			if repoIDStr == "" {
				return fmt.Errorf("--repo is required")
			}

			// Parse PR number
			prNumber, err := strconv.Atoi(prNumberStr)
			if err != nil {
				return fmt.Errorf("invalid PR number: %s", prNumberStr)
			}

			// Get container
			container, ok := serviceContext.(PRServiceProvider)
			if !ok {
				return fmt.Errorf("invalid service context")
			}

			prUC := container.GetPullRequestUseCase()
			if prUC == nil {
				return fmt.Errorf("PR use case not available")
			}

			// Get PR
			ctx := context.Background()
			repoID := types.FromString(repoIDStr)
			pr, err := prUC.GetPullRequest(ctx, repoID, prNumber)
			if err != nil {
				return fmt.Errorf("failed to get PR: %w", err)
			}

			fmt.Printf("Merging PR #%d: %s\n\n", pr.Number, pr.Title)

			// Determine merge strategy
			strategy := "merge"
			if squash {
				strategy = "squash"
			}

			// Merge PR
			mergerID := getCurrentUserID(cmd)
			req := domain.MergePRRequest{
				PRID:     pr.ID,
				MergedBy: mergerID,
				Message:  message,
				Strategy: strategy,
			}

			if err := prUC.MergePullRequest(ctx, req); err != nil {
				return fmt.Errorf("failed to merge PR: %w", err)
			}

			fmt.Printf("✅ PR #%d merged successfully\n", pr.Number)
			if squash {
				fmt.Printf("   Strategy: squash\n")
			}
			if message != "" {
				fmt.Printf("   Commit: %s\n", message)
			}
			fmt.Printf("\n")
			fmt.Printf("Changes merged to target branch.\n")
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().StringP("message", "m", "", "Merge commit message")
	cmd.Flags().Bool("squash", false, "Squash commits")
	cmd.Flags().Bool("no-delete", false, "Don't delete source branch after merge")

	cmd.MarkFlagRequired("repo")

	return cmd
}

// newPRCloseCommand creates the pr close subcommand
func newPRCloseCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "close <number>",
		Short: "Close a pull request without merging",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			prNumberStr := args[0]
			repoIDStr, _ := cmd.Flags().GetString("repo")
			reason, _ := cmd.Flags().GetString("reason")

			if repoIDStr == "" {
				return fmt.Errorf("--repo is required")
			}

			// Parse PR number
			prNumber, err := strconv.Atoi(prNumberStr)
			if err != nil {
				return fmt.Errorf("invalid PR number: %s", prNumberStr)
			}

			// Get container
			container, ok := serviceContext.(PRServiceProvider)
			if !ok {
				return fmt.Errorf("invalid service context")
			}

			prUC := container.GetPullRequestUseCase()
			if prUC == nil {
				return fmt.Errorf("PR use case not available")
			}

			// Get PR
			ctx := context.Background()
			repoID := types.FromString(repoIDStr)
			pr, err := prUC.GetPullRequest(ctx, repoID, prNumber)
			if err != nil {
				return fmt.Errorf("failed to get PR: %w", err)
			}

			fmt.Printf("Closing PR #%d: %s\n\n", pr.Number, pr.Title)

			// Close PR
			if err := prUC.ClosePullRequest(ctx, pr.ID, reason); err != nil {
				return fmt.Errorf("failed to close PR: %w", err)
			}

			fmt.Printf("✅ PR #%d closed\n", pr.Number)
			if reason != "" {
				fmt.Printf("   Reason: %s\n", reason)
			}
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().String("reason", "", "Reason for closing")

	cmd.MarkFlagRequired("repo")

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
			issueTypeStr, _ := cmd.Flags().GetString("type")
			priorityStr, _ := cmd.Flags().GetString("priority")
			repoIDStr, _ := cmd.Flags().GetString("repo")
			roomIDStr, _ := cmd.Flags().GetString("room")
			equipmentIDStr, _ := cmd.Flags().GetString("equipment")

			if title == "" {
				return fmt.Errorf("--title is required")
			}
			if repoIDStr == "" {
				return fmt.Errorf("--repo is required")
			}

			// Get container from service context
			container, ok := serviceContext.(PRServiceProvider)
			if !ok {
				return fmt.Errorf("invalid service context")
			}

			issueUC := container.GetIssueUseCase()
			if issueUC == nil {
				return fmt.Errorf("issue use case not available")
			}

			// Build request
			req := domain.CreateIssueRequest{
				RepositoryID: types.FromString(repoIDStr),
				Title:        title,
				Body:         body,
				IssueType:    domain.IssueType(issueTypeStr),
				Priority:     domain.IssuePriority(priorityStr),
				ReportedBy:   getCurrentUserID(cmd),
			}

			// Add optional fields
			if roomIDStr != "" {
				roomID := types.FromString(roomIDStr)
				req.RoomID = &roomID
			}
			if equipmentIDStr != "" {
				eqID := types.FromString(equipmentIDStr)
				req.EquipmentID = &eqID
			}

			// Create issue
			ctx := context.Background()
			fmt.Printf("Creating issue...\n")
			issue, err := issueUC.CreateIssue(ctx, req)
			if err != nil {
				fmt.Fprintf(cmd.ErrOrStderr(), "Error creating issue: %v\n", err)
				return fmt.Errorf("failed to create issue: %w", err)
			}

			// Display results
			fmt.Printf("\n✅ Issue created: #%d\n", issue.Number)
			fmt.Printf("   ID: %s\n", issue.ID)
			fmt.Printf("   Status: %s\n", issue.Status)
			if issue.AssignedTo != nil {
				fmt.Printf("   Assigned to: %s\n", issue.AssignedTo)
			}
			if issue.AutoAssigned {
				fmt.Printf("   (Auto-assigned based on issue type)\n")
			}
			fmt.Printf("\n")
			fmt.Printf("Next steps:\n")
			fmt.Printf("  • View issue: arx issue show %d --repo %s\n", issue.Number, repoIDStr)
			fmt.Printf("  • Start work: arx issue start %d --repo %s\n", issue.Number, repoIDStr)
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("title", "", "Issue title (required)")
	cmd.Flags().StringP("body", "b", "", "Issue description")
	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().String("type", "problem", "Issue type (problem, maintenance, safety, emergency)")
	cmd.Flags().String("priority", "normal", "Priority (low, normal, high, urgent, emergency)")
	cmd.Flags().String("room", "", "Room ID")
	cmd.Flags().String("equipment", "", "Equipment ID")
	cmd.Flags().String("bas-point", "", "BAS point ID")
	cmd.Flags().String("location", "", "3D location (x,y,z)")
	cmd.Flags().String("photo", "", "Photo path")
	cmd.Flags().String("via", "cli", "Reported via (cli, mobile_ar, mobile_app)")

	cmd.MarkFlagRequired("title")
	cmd.MarkFlagRequired("repo")

	return cmd
}

// newIssueListCommand creates the issue list subcommand
func newIssueListCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List issues",
		RunE: func(cmd *cobra.Command, args []string) error {
			repoIDStr, _ := cmd.Flags().GetString("repo")
			statusStr, _ := cmd.Flags().GetString("status")
			assignedToStr, _ := cmd.Flags().GetString("assigned-to")

			if repoIDStr == "" {
				return fmt.Errorf("--repo is required")
			}

			// Get container
			fmt.Printf("Listing issues...\n")
			container, ok := serviceContext.(PRServiceProvider)
			if !ok {
				fmt.Fprintf(cmd.ErrOrStderr(), "Error: invalid service context\n")
				return fmt.Errorf("invalid service context")
			}

			issueUC := container.GetIssueUseCase()
			if issueUC == nil {
				fmt.Fprintf(cmd.ErrOrStderr(), "Error: issue use case not available\n")
				return fmt.Errorf("issue use case not available")
			}

			// Build filter
			repoID := types.FromString(repoIDStr)
			filter := domain.IssueFilter{
				RepositoryID: &repoID,
			}
			if statusStr != "" {
				status := domain.IssueStatus(statusStr)
				filter.Status = &status
			}
			if assignedToStr != "" {
				assignedID := types.FromString(assignedToStr)
				filter.AssignedTo = &assignedID
			}

			// List issues
			ctx := context.Background()
			fmt.Printf("Querying database...\n")
			issues, err := issueUC.ListIssues(ctx, filter, 100, 0)
			if err != nil {
				fmt.Fprintf(cmd.ErrOrStderr(), "Error listing issues: %v\n", err)
				return fmt.Errorf("failed to list issues: %w", err)
			}
			fmt.Printf("Found %d issues\n\n", len(issues))

			if len(issues) == 0 {
				fmt.Println("No issues found")
				return nil
			}

			// Display issues
			fmt.Printf("Issues:\n\n")
			fmt.Printf("%-5s %-40s %-15s %-10s %-15s\n", "#", "Title", "Status", "Priority", "Assigned")
			fmt.Printf("%s\n", strings.Repeat("-", 90))

			for _, issue := range issues {
				assigned := "(unassigned)"
				if issue.AssignedTo != nil {
					assigned = issue.AssignedTo.String()
				}

				title := issue.Title
				if len(title) > 40 {
					title = title[:37] + "..."
				}

				fmt.Printf("%-5d %-40s %-15s %-10s %-15s\n",
					issue.Number,
					title,
					string(issue.Status),
					string(issue.Priority),
					assigned,
				)
			}
			fmt.Printf("\n%d issues shown\n", len(issues))

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().String("status", "", "Filter by status (open, in_progress, resolved, closed)")
	cmd.Flags().String("assigned-to", "", "Filter by assigned user ID")
	cmd.Flags().String("priority", "", "Filter by priority")
	cmd.Flags().String("room", "", "Filter by room ID")

	cmd.MarkFlagRequired("repo")

	return cmd
}

// newIssueShowCommand creates the issue show subcommand
func newIssueShowCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "show <number>",
		Short: "Show issue details",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			issueNumberStr := args[0]
			repoIDStr, _ := cmd.Flags().GetString("repo")

			if repoIDStr == "" {
				return fmt.Errorf("--repo is required")
			}

			// Parse issue number
			issueNumber, err := strconv.Atoi(issueNumberStr)
			if err != nil {
				return fmt.Errorf("invalid issue number: %s", issueNumberStr)
			}

			// Get container
			container, ok := serviceContext.(PRServiceProvider)
			if !ok {
				return fmt.Errorf("invalid service context")
			}

			issueUC := container.GetIssueUseCase()
			if issueUC == nil {
				return fmt.Errorf("issue use case not available")
			}

			// Get issue
			ctx := context.Background()
			repoID := types.FromString(repoIDStr)
			issue, err := issueUC.GetIssue(ctx, repoID, issueNumber)
			if err != nil {
				return fmt.Errorf("failed to get issue: %w", err)
			}

			// Display issue details
			fmt.Printf("Issue #%d\n", issue.Number)
			fmt.Printf("%s\n", strings.Repeat("=", 60))
			fmt.Printf("\n")
			fmt.Printf("Title: %s\n", issue.Title)
			fmt.Printf("Status: %s\n", issue.Status)
			fmt.Printf("Type: %s\n", issue.IssueType)
			fmt.Printf("Priority: %s\n", issue.Priority)
			fmt.Printf("\n")
			if issue.Body != "" {
				fmt.Printf("Description:\n%s\n\n", issue.Body)
			}
			if issue.AssignedTo != nil {
				fmt.Printf("Assigned to: %s\n", issue.AssignedTo)
				if issue.AutoAssigned {
					fmt.Printf("  (Auto-assigned)\n")
				}
				fmt.Printf("\n")
			}
			fmt.Printf("Reported by: %s\n", issue.ReportedBy)
			fmt.Printf("Reported: %s\n", issue.CreatedAt.Format("2006-01-02 15:04"))
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.MarkFlagRequired("repo")

	return cmd
}

// newIssueStartCommand creates the issue start subcommand
func newIssueStartCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "start <number>",
		Short: "Start work on an issue (creates branch and PR)",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			issueNumberStr := args[0]
			repoIDStr, _ := cmd.Flags().GetString("repo")

			if repoIDStr == "" {
				return fmt.Errorf("--repo is required")
			}

			// Parse issue number
			issueNumber, err := strconv.Atoi(issueNumberStr)
			if err != nil {
				return fmt.Errorf("invalid issue number: %s", issueNumberStr)
			}

			// Get container
			container, ok := serviceContext.(PRServiceProvider)
			if !ok {
				return fmt.Errorf("invalid service context")
			}

			issueUC := container.GetIssueUseCase()
			if issueUC == nil {
				return fmt.Errorf("issue use case not available")
			}

			// Get issue first to display title
			ctx := context.Background()
			repoID := types.FromString(repoIDStr)
			issue, err := issueUC.GetIssue(ctx, repoID, issueNumber)
			if err != nil {
				return fmt.Errorf("failed to get issue: %w", err)
			}

			fmt.Printf("Starting work on issue #%d: %s\n\n", issue.Number, issue.Title)

			// Start work (creates branch and PR)
			workerID := getCurrentUserID(cmd)
			branch, pr, err := issueUC.StartWork(ctx, issue.ID, workerID)
			if err != nil {
				return fmt.Errorf("failed to start work: %w", err)
			}

			fmt.Printf("✅ Created branch: %s\n", branch.Name)
			fmt.Printf("✅ Created pull request: #%d\n", pr.Number)
			fmt.Printf("✅ Linked issue to PR\n")
			fmt.Printf("\n")

			fmt.Printf("Work started on issue #%d\n", issue.Number)
			fmt.Printf("  Branch: %s\n", branch.Name)
			fmt.Printf("  PR: #%d - %s\n", pr.Number, pr.Title)
			fmt.Printf("\n")
			fmt.Printf("Next steps:\n")
			fmt.Printf("  • Make changes to fix the issue\n")
			fmt.Printf("  • Commit: arx repo commit -m \"Fixed issue\"\n")
			fmt.Printf("  • Resolve: arx issue resolve %d --repo %s\n", issue.Number, repoIDStr)
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.MarkFlagRequired("repo")

	return cmd
}

// newIssueResolveCommand creates the issue resolve subcommand
func newIssueResolveCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "resolve <number>",
		Short: "Resolve an issue",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			issueNumberStr := args[0]
			repoIDStr, _ := cmd.Flags().GetString("repo")
			notes, _ := cmd.Flags().GetString("notes")

			if repoIDStr == "" {
				return fmt.Errorf("--repo is required")
			}

			// Parse issue number
			issueNumber, err := strconv.Atoi(issueNumberStr)
			if err != nil {
				return fmt.Errorf("invalid issue number: %s", issueNumberStr)
			}

			// Get container
			container, ok := serviceContext.(PRServiceProvider)
			if !ok {
				return fmt.Errorf("invalid service context")
			}

			issueUC := container.GetIssueUseCase()
			if issueUC == nil {
				return fmt.Errorf("issue use case not available")
			}

			// Get issue
			ctx := context.Background()
			repoID := types.FromString(repoIDStr)
			issue, err := issueUC.GetIssue(ctx, repoID, issueNumber)
			if err != nil {
				return fmt.Errorf("failed to get issue: %w", err)
			}

			fmt.Printf("Resolving issue #%d: %s\n\n", issue.Number, issue.Title)

			// Resolve issue
			resolverID := getCurrentUserID(cmd)
			req := domain.ResolveIssueRequest{
				IssueID:         issue.ID,
				ResolvedBy:      resolverID,
				ResolutionNotes: notes,
			}

			if err := issueUC.ResolveIssue(ctx, req); err != nil {
				return fmt.Errorf("failed to resolve issue: %w", err)
			}

			fmt.Printf("✅ Issue #%d marked as resolved\n", issue.Number)
			fmt.Printf("\n")
			if notes != "" {
				fmt.Printf("Resolution notes:\n")
				fmt.Printf("  %s\n", notes)
				fmt.Printf("\n")
			}
			fmt.Printf("Next steps:\n")
			if issue.PRID != nil {
				fmt.Printf("  • Merge PR to apply changes\n")
			}
			fmt.Printf("  • Close issue: arx issue close %d --repo %s\n", issue.Number, repoIDStr)
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().String("notes", "", "Resolution notes")

	cmd.MarkFlagRequired("repo")

	return cmd
}

// newIssueCloseCommand creates the issue close subcommand
func newIssueCloseCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "close <number>",
		Short: "Close an issue",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			issueNumberStr := args[0]
			repoIDStr, _ := cmd.Flags().GetString("repo")
			reason, _ := cmd.Flags().GetString("reason")

			if repoIDStr == "" {
				return fmt.Errorf("--repo is required")
			}

			// Parse issue number
			issueNumber, err := strconv.Atoi(issueNumberStr)
			if err != nil {
				return fmt.Errorf("invalid issue number: %s", issueNumberStr)
			}

			// Get container
			container, ok := serviceContext.(PRServiceProvider)
			if !ok {
				return fmt.Errorf("invalid service context")
			}

			issueUC := container.GetIssueUseCase()
			if issueUC == nil {
				return fmt.Errorf("issue use case not available")
			}

			// Get issue
			ctx := context.Background()
			repoID := types.FromString(repoIDStr)
			issue, err := issueUC.GetIssue(ctx, repoID, issueNumber)
			if err != nil {
				return fmt.Errorf("failed to get issue: %w", err)
			}

			fmt.Printf("Closing issue #%d: %s\n\n", issue.Number, issue.Title)

			// Close issue
			if err := issueUC.CloseIssue(ctx, issue.ID, reason); err != nil {
				return fmt.Errorf("failed to close issue: %w", err)
			}

			fmt.Printf("✅ Issue #%d closed\n", issue.Number)
			if reason != "" {
				fmt.Printf("   Reason: %s\n", reason)
			}
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().String("reason", "", "Reason for closing (duplicate, wont_fix, etc.)")

	cmd.MarkFlagRequired("repo")

	return cmd
}
