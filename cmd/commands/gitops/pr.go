package gitops

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	// "github.com/arxos/arxos/core/internal/gitops"
	// "github.com/arxos/arxos/core/internal/state"
	"github.com/spf13/cobra"
)

var prCmd = &cobra.Command{
	Use:   "pr",
	Short: "Manage pull requests",
	Long:  `Create, list, review, and merge pull requests for building configurations.`,
}

var prCreateCmd = &cobra.Command{
	Use:   "create [building-id]",
	Short: "Create a new pull request",
	Args:  cobra.ExactArgs(1),
	RunE:  runPRCreate,
}

var prListCmd = &cobra.Command{
	Use:   "list [building-id]",
	Short: "List pull requests",
	Args:  cobra.ExactArgs(1),
	RunE:  runPRList,
}

var prViewCmd = &cobra.Command{
	Use:   "view [pr-id]",
	Short: "View pull request details",
	Args:  cobra.ExactArgs(1),
	RunE:  runPRView,
}

var prReviewCmd = &cobra.Command{
	Use:   "review [pr-id]",
	Short: "Review a pull request",
	Args:  cobra.ExactArgs(1),
	RunE:  runPRReview,
}

var prMergeCmd = &cobra.Command{
	Use:   "merge [pr-id]",
	Short: "Merge a pull request",
	Args:  cobra.ExactArgs(1),
	RunE:  runPRMerge,
}

var prCloseCmd = &cobra.Command{
	Use:   "close [pr-id]",
	Short: "Close a pull request without merging",
	Args:  cobra.ExactArgs(1),
	RunE:  runPRClose,
}

var (
	prTitle           string
	prDescription     string
	prSourceBranch    string
	prTargetBranch    string
	prType            string
	prPriority        string
	prLabels          []string
	prDraft           bool
	prAutoMerge       bool
	
	prStatus          string
	prReviewStatus    string
	prReviewBody      string
	prMergeStrategy   string
	prSquash          bool
)

func init() {
	prCmd.AddCommand(
		prCreateCmd,
		prListCmd,
		prViewCmd,
		prReviewCmd,
		prMergeCmd,
		prCloseCmd,
	)

	// Create flags
	prCreateCmd.Flags().StringVarP(&prTitle, "title", "t", "", "PR title (required)")
	prCreateCmd.Flags().StringVarP(&prDescription, "description", "d", "", "PR description")
	prCreateCmd.Flags().StringVarP(&prSourceBranch, "source", "s", "", "Source branch")
	prCreateCmd.Flags().StringVarP(&prTargetBranch, "target", "b", "main", "Target branch")
	prCreateCmd.Flags().StringVar(&prType, "type", "standard", "PR type (standard/hotfix/release)")
	prCreateCmd.Flags().StringVar(&prPriority, "priority", "normal", "Priority (low/normal/high/critical)")
	prCreateCmd.Flags().StringSliceVar(&prLabels, "labels", []string{}, "PR labels")
	prCreateCmd.Flags().BoolVar(&prDraft, "draft", false, "Create as draft PR")
	prCreateCmd.Flags().BoolVar(&prAutoMerge, "auto-merge", false, "Enable auto-merge when approved")
	prCreateCmd.MarkFlagRequired("title")

	// List flags
	prListCmd.Flags().StringVar(&prStatus, "status", "", "Filter by status")

	// Review flags
	prReviewCmd.Flags().StringVar(&prReviewStatus, "status", "", "Review status (approve/request-changes/comment)")
	prReviewCmd.Flags().StringVar(&prReviewBody, "body", "", "Review comment")

	// Merge flags
	prMergeCmd.Flags().StringVar(&prMergeStrategy, "strategy", "merge", "Merge strategy (merge/squash/rebase)")
	prMergeCmd.Flags().BoolVar(&prSquash, "squash", false, "Squash commits")
}

func runPRCreate(cmd *cobra.Command, args []string) error {
	buildingID := args[0]

	if prTitle == "" {
		return fmt.Errorf("title is required")
	}

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
	prManager := gitops.NewPullRequestManager(db, mergeEngine, branchManager)

	ctx := context.Background()

	// Get current branch if source not specified
	if prSourceBranch == "" {
		current, err := branchManager.GetCurrentBranch(ctx, buildingID)
		if err != nil {
			return fmt.Errorf("failed to get current branch: %w", err)
		}
		prSourceBranch = current.Name
	}

	// Create PR request
	req := &gitops.CreatePullRequestRequest{
		BuildingID:   buildingID,
		SourceBranch: prSourceBranch,
		TargetBranch: prTargetBranch,
		Title:        prTitle,
		Description:  prDescription,
		PRType:       prType,
		Priority:     prPriority,
		AuthorID:     getCurrentUser(),
		AuthorName:   getCurrentUser(),
		Labels:       prLabels,
	}

	// Create pull request
	pr, err := prManager.CreatePullRequest(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to create pull request: %w", err)
	}

	// Update status if not draft
	if !prDraft {
		err = prManager.UpdatePullRequestStatus(ctx, pr.ID, "open")
		if err != nil {
			fmt.Printf("Warning: failed to open PR: %v\n", err)
		}
	}

	// Output result
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		jsonData, _ := json.MarshalIndent(pr, "", "  ")
		fmt.Printf("%s\n", jsonData)
	} else {
		fmt.Printf("Pull request #%d created successfully\n", pr.PRNumber)
		fmt.Printf("Title: %s\n", pr.Title)
		fmt.Printf("Source: %s → Target: %s\n", pr.SourceBranch, pr.TargetBranch)
		
		if pr.HasConflicts {
			fmt.Printf("⚠ Warning: This PR has conflicts that must be resolved\n")
		} else {
			fmt.Printf("✓ No conflicts detected\n")
		}
		
		fmt.Printf("\nView: arxos gitops pr view %d\n", pr.PRNumber)
	}

	return nil
}

func runPRList(cmd *cobra.Command, args []string) error {
	buildingID := args[0]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create PR manager
	stateManager := state.NewManager(db)
	branchManager := gitops.NewBranchManager(db, stateManager)
	mergeEngine := gitops.NewMergeEngine(db, stateManager, branchManager)
	prManager := gitops.NewPullRequestManager(db, mergeEngine, branchManager)

	ctx := context.Background()

	// List pull requests
	prs, err := prManager.ListPullRequests(ctx, buildingID, prStatus)
	if err != nil {
		return fmt.Errorf("failed to list pull requests: %w", err)
	}

	// Output result
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		jsonData, _ := json.MarshalIndent(prs, "", "  ")
		fmt.Printf("%s\n", jsonData)
	} else {
		fmt.Printf("Pull Requests for building %s:\n", buildingID)
		fmt.Printf("%s\n", strings.Repeat("=", 80))

		if len(prs) == 0 {
			fmt.Println("No pull requests found")
			return nil
		}

		for _, pr := range prs {
			statusIcon := getPRStatusIcon(pr.Status)
			conflictIcon := ""
			if pr.HasConflicts {
				conflictIcon = " ⚠"
			}
			
			fmt.Printf("#%d %s %s%s\n", pr.PRNumber, statusIcon, pr.Title, conflictIcon)
			fmt.Printf("   %s → %s\n", pr.SourceBranch, pr.TargetBranch)
			fmt.Printf("   Status: %s | Author: %s | Created: %s\n",
				pr.Status, pr.AuthorName, pr.CreatedAt.Format("2006-01-02"))
			fmt.Println()
		}
	}

	return nil
}

func runPRView(cmd *cobra.Command, args []string) error {
	prID := args[0]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create PR manager
	stateManager := state.NewManager(db)
	branchManager := gitops.NewBranchManager(db, stateManager)
	mergeEngine := gitops.NewMergeEngine(db, stateManager, branchManager)
	prManager := gitops.NewPullRequestManager(db, mergeEngine, branchManager)

	ctx := context.Background()

	// Get pull request
	pr, err := prManager.GetPullRequest(ctx, prID)
	if err != nil {
		return fmt.Errorf("failed to get pull request: %w", err)
	}

	// Get conflicts if any
	var conflicts []gitops.Conflict
	if pr.HasConflicts {
		conflicts, _ = mergeEngine.GetConflicts(ctx, pr.ID)
	}

	// Output result
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		output := map[string]interface{}{
			"pr":        pr,
			"conflicts": conflicts,
		}
		jsonData, _ := json.MarshalIndent(output, "", "  ")
		fmt.Printf("%s\n", jsonData)
	} else {
		fmt.Printf("Pull Request #%d\n", pr.PRNumber)
		fmt.Printf("%s\n", strings.Repeat("=", 80))
		fmt.Printf("Title:  %s\n", pr.Title)
		fmt.Printf("Status: %s %s\n", getPRStatusIcon(pr.Status), pr.Status)
		fmt.Printf("Author: %s\n", pr.AuthorName)
		fmt.Printf("Source: %s → Target: %s\n", pr.SourceBranch, pr.TargetBranch)
		
		if pr.Description != "" {
			fmt.Printf("\nDescription:\n%s\n", pr.Description)
		}
		
		fmt.Printf("\nChanges:\n")
		fmt.Printf("  Files changed: %d\n", pr.FilesChanged)
		fmt.Printf("  Lines added:   +%d\n", pr.LinesAdded)
		fmt.Printf("  Lines removed: -%d\n", pr.LinesRemoved)
		fmt.Printf("  Commits:       %d\n", pr.CommitsCount)
		
		if pr.HasConflicts {
			fmt.Printf("\n⚠ Conflicts (%d):\n", len(conflicts))
			for _, conflict := range conflicts {
				fmt.Printf("  - %s: %s\n", conflict.ObjectID, conflict.Description)
			}
		}
		
		fmt.Printf("\nTimeline:\n")
		fmt.Printf("  Created:  %s\n", pr.CreatedAt.Format("2006-01-02 15:04"))
		if pr.ReadyForReviewAt != nil {
			fmt.Printf("  Ready:    %s\n", pr.ReadyForReviewAt.Format("2006-01-02 15:04"))
		}
		if pr.ApprovedAt != nil {
			fmt.Printf("  Approved: %s\n", pr.ApprovedAt.Format("2006-01-02 15:04"))
		}
		if pr.MergedAt != nil {
			fmt.Printf("  Merged:   %s by %s\n", 
				pr.MergedAt.Format("2006-01-02 15:04"), *pr.MergerName)
		}
	}

	return nil
}

func runPRReview(cmd *cobra.Command, args []string) error {
	prID := args[0]

	if prReviewStatus == "" {
		return fmt.Errorf("review status required (--status approve|request-changes|comment)")
	}

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create PR manager
	stateManager := state.NewManager(db)
	branchManager := gitops.NewBranchManager(db, stateManager)
	mergeEngine := gitops.NewMergeEngine(db, stateManager, branchManager)
	prManager := gitops.NewPullRequestManager(db, mergeEngine, branchManager)

	ctx := context.Background()

	// Get PR to get current state
	pr, err := prManager.GetPullRequest(ctx, prID)
	if err != nil {
		return fmt.Errorf("failed to get pull request: %w", err)
	}

	// Map review status
	reviewStatusMap := map[string]string{
		"approve":          "approved",
		"request-changes":  "changes_requested",
		"comment":          "commented",
	}

	status, ok := reviewStatusMap[prReviewStatus]
	if !ok {
		return fmt.Errorf("invalid review status: %s", prReviewStatus)
	}

	// Add review
	review := &gitops.PRReview{
		ReviewerID:   getCurrentUser(),
		ReviewerName: getCurrentUser(),
		Status:       status,
		Body:         prReviewBody,
		CommitID:     *pr.SourceStateID,
	}

	err = prManager.AddReview(ctx, prID, review)
	if err != nil {
		return fmt.Errorf("failed to add review: %w", err)
	}

	fmt.Printf("Review submitted successfully\n")
	fmt.Printf("Status: %s\n", status)
	if prReviewBody != "" {
		fmt.Printf("Comment: %s\n", prReviewBody)
	}

	return nil
}

func runPRMerge(cmd *cobra.Command, args []string) error {
	prID := args[0]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create PR manager
	stateManager := state.NewManager(db)
	branchManager := gitops.NewBranchManager(db, stateManager)
	mergeEngine := gitops.NewMergeEngine(db, stateManager, branchManager)
	prManager := gitops.NewPullRequestManager(db, mergeEngine, branchManager)

	ctx := context.Background()

	// Map strategy
	strategyMap := map[string]gitops.MergeStrategy{
		"merge":   gitops.MergeStrategyMerge,
		"squash":  gitops.MergeStrategySquash,
		"rebase":  gitops.MergeStrategyRebase,
	}

	strategy, ok := strategyMap[prMergeStrategy]
	if !ok {
		strategy = gitops.MergeStrategyMerge
	}

	// Merge PR
	err = prManager.MergePullRequest(ctx, prID, getCurrentUser(), getCurrentUser(), strategy)
	if err != nil {
		return fmt.Errorf("failed to merge pull request: %w", err)
	}

	fmt.Printf("Pull request #%s merged successfully\n", prID)
	fmt.Printf("Strategy: %s\n", strategy)

	return nil
}

func runPRClose(cmd *cobra.Command, args []string) error {
	prID := args[0]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create PR manager
	stateManager := state.NewManager(db)
	branchManager := gitops.NewBranchManager(db, stateManager)
	mergeEngine := gitops.NewMergeEngine(db, stateManager, branchManager)
	prManager := gitops.NewPullRequestManager(db, mergeEngine, branchManager)

	ctx := context.Background()

	// Close PR
	err = prManager.UpdatePullRequestStatus(ctx, prID, "closed")
	if err != nil {
		return fmt.Errorf("failed to close pull request: %w", err)
	}

	fmt.Printf("Pull request #%s closed\n", prID)
	return nil
}

func getPRStatusIcon(status string) string {
	switch status {
	case "draft":
		return "📝"
	case "open":
		return "🟢"
	case "review_required":
		return "🔍"
	case "changes_requested":
		return "🔴"
	case "approved":
		return "✅"
	case "merged":
		return "🟣"
	case "closed":
		return "⚫"
	default:
		return "⚪"
	}
}