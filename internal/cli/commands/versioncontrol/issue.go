package versioncontrol

import (
	"context"
	"fmt"
	"strconv"
	"strings"

	domainvc "github.com/arx-os/arxos/internal/domain/versioncontrol"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/spf13/cobra"
)

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
			req := domainvc.CreateIssueRequest{
				RepositoryID: types.FromString(repoIDStr),
				Title:        title,
				Body:         body,
				IssueType:    domainvc.IssueType(issueTypeStr),
				Priority:     domainvc.IssuePriority(priorityStr),
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
			filter := domainvc.IssueFilter{
				RepositoryID: &repoID,
			}
			if statusStr != "" {
				status := domainvc.IssueStatus(statusStr)
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
			req := domainvc.ResolveIssueRequest{
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
