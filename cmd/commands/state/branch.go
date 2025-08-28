package state

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/spf13/cobra"
	// // "github.com/arxos/core/internal/state" // TODO: Fix import
	"github.com/google/uuid"
)

var branchCmd = &cobra.Command{
	Use:   "branch",
	Short: "Manage state branches",
	Long: `Create and manage branches for building state versioning.
	
Branches allow you to experiment with different configurations without
affecting the main state history.`,
}

var branchCreateCmd = &cobra.Command{
	Use:   "create [building-id] [branch-name]",
	Short: "Create a new branch",
	Args:  cobra.ExactArgs(2),
	RunE:  runBranchCreate,
}

var branchListCmd = &cobra.Command{
	Use:     "list [building-id]",
	Short:   "List all branches for a building",
	Aliases: []string{"ls"},
	Args:    cobra.ExactArgs(1),
	RunE:    runBranchList,
}

var branchDeleteCmd = &cobra.Command{
	Use:     "delete [building-id] [branch-name]",
	Short:   "Delete a branch",
	Aliases: []string{"rm"},
	Args:    cobra.ExactArgs(2),
	RunE:    runBranchDelete,
}

var branchSwitchCmd = &cobra.Command{
	Use:     "switch [building-id] [branch-name]",
	Short:   "Switch to a different branch",
	Aliases: []string{"checkout"},
	Args:    cobra.ExactArgs(2),
	RunE:    runBranchSwitch,
}

var (
	branchDescription string
	branchProtected   bool
	branchFrom        string
	branchForceDelete bool
)

func init() {
	// Add subcommands
	branchCmd.AddCommand(branchCreateCmd)
	branchCmd.AddCommand(branchListCmd)
	branchCmd.AddCommand(branchDeleteCmd)
	branchCmd.AddCommand(branchSwitchCmd)

	// Flags for create
	branchCreateCmd.Flags().StringVarP(&branchDescription, "description", "d", "", "Branch description")
	branchCreateCmd.Flags().BoolVar(&branchProtected, "protected", false, "Create as protected branch")
	branchCreateCmd.Flags().StringVar(&branchFrom, "from", "", "Create branch from specific state")

	// Flags for delete
	branchDeleteCmd.Flags().BoolVarP(&branchForceDelete, "force", "f", false, "Force delete even if branch has unique commits")
}

func runBranchCreate(cmd *cobra.Command, args []string) error {
	buildingID := args[0]
	branchName := args[1]

	// Validate branch name
	if branchName == "main" {
		return fmt.Errorf("cannot create branch named 'main'")
	}

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	ctx := context.Background()

	// Check if branch already exists
	var existing int
	err = db.GetContext(ctx, &existing, `
		SELECT COUNT(*) FROM state_branches 
		WHERE building_id = $1 AND branch_name = $2
	`, buildingID, branchName)
	if err != nil {
		return fmt.Errorf("failed to check existing branch: %w", err)
	}
	if existing > 0 {
		return fmt.Errorf("branch '%s' already exists", branchName)
	}

	// Get base state (from main or specified branch/state)
	var baseStateID *string
	if branchFrom != "" {
		// TODO: Resolve branch/state identifier
		baseStateID = &branchFrom
	} else {
		// Get HEAD of main branch
		var mainHead string
		err = db.GetContext(ctx, &mainHead, `
			SELECT head_state_id FROM state_branches
			WHERE building_id = $1 AND branch_name = 'main'
		`, buildingID)
		if err == nil {
			baseStateID = &mainHead
		}
	}

	// Create new branch
	newBranch := state.StateBranch{
		ID:            uuid.New().String(),
		BuildingID:    buildingID,
		BranchName:    branchName,
		BaseStateID:   baseStateID,
		HeadStateID:   baseStateID, // Initially points to same state
		Description:   branchDescription,
		IsProtected:   branchProtected,
		IsDefault:     false,
		CreatedBy:     "cli",
		CreatedByName: authorName,
		CreatedAt:     time.Now(),
		UpdatedAt:     time.Now(),
	}

	_, err = db.NamedExecContext(ctx, `
		INSERT INTO state_branches (
			id, building_id, branch_name, base_state_id, head_state_id,
			description, is_protected, is_default, created_by, created_by_name,
			created_at, updated_at
		) VALUES (
			:id, :building_id, :branch_name, :base_state_id, :head_state_id,
			:description, :is_protected, :is_default, :created_by, :created_by_name,
			:created_at, :updated_at
		)
	`, newBranch)
	if err != nil {
		return fmt.Errorf("failed to create branch: %w", err)
	}

	fmt.Printf("✓ Branch '%s' created successfully\n", branchName)
	if baseStateID != nil {
		fmt.Printf("  Based on state: %s\n", *baseStateID)
	}
	if branchProtected {
		fmt.Printf("  Protected: Yes\n")
	}

	return nil
}

func runBranchList(cmd *cobra.Command, args []string) error {
	buildingID := args[0]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	ctx := context.Background()

	// List all branches
	var branches []state.StateBranch
	err = db.SelectContext(ctx, &branches, `
		SELECT * FROM state_branches
		WHERE building_id = $1
		ORDER BY is_default DESC, created_at DESC
	`, buildingID)
	if err != nil {
		return fmt.Errorf("failed to list branches: %w", err)
	}

	if len(branches) == 0 {
		fmt.Printf("No branches found for building %s\n", buildingID)
		return nil
	}

	// Output JSON if requested
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		jsonData, _ := json.MarshalIndent(branches, "", "  ")
		fmt.Printf("%s\n", jsonData)
		return nil
	}

	// Display branches
	fmt.Printf("Branches for building %s\n", buildingID)
	fmt.Printf("%s\n", strings.Repeat("=", 60))

	for _, branch := range branches {
		marker := "  "
		if branch.IsDefault {
			marker = "* "
		}

		fmt.Printf("\n%s%s", marker, branch.BranchName)
		if branch.IsProtected {
			fmt.Printf(" [protected]")
		}
		fmt.Printf("\n")

		if branch.Description != "" {
			fmt.Printf("    %s\n", branch.Description)
		}

		fmt.Printf("    Created: %s by %s\n",
			branch.CreatedAt.Format("2006-01-02"),
			branch.CreatedByName)

		if branch.HeadStateID != nil {
			fmt.Printf("    HEAD: %s\n", (*branch.HeadStateID)[:8])
		}

		if branch.LastActivityAt != nil {
			fmt.Printf("    Last activity: %s\n",
				branch.LastActivityAt.Format("2006-01-02 15:04"))
		}

		if branch.CommitsAhead > 0 || branch.CommitsBehind > 0 {
			fmt.Printf("    Status: %d ahead, %d behind main\n",
				branch.CommitsAhead, branch.CommitsBehind)
		}
	}

	return nil
}

func runBranchDelete(cmd *cobra.Command, args []string) error {
	buildingID := args[0]
	branchName := args[1]

	if branchName == "main" {
		return fmt.Errorf("cannot delete main branch")
	}

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	ctx := context.Background()

	// Check if branch exists and get details
	var branch state.StateBranch
	err = db.GetContext(ctx, &branch, `
		SELECT * FROM state_branches
		WHERE building_id = $1 AND branch_name = $2
	`, buildingID, branchName)
	if err != nil {
		return fmt.Errorf("branch '%s' not found", branchName)
	}

	// Check if protected
	if branch.IsProtected && !branchForceDelete {
		return fmt.Errorf("branch '%s' is protected. Use --force to delete", branchName)
	}

	// Check for unique commits (simplified - in production would be more thorough)
	var uniqueCommits int
	err = db.GetContext(ctx, &uniqueCommits, `
		SELECT COUNT(*) FROM building_states
		WHERE building_id = $1 AND branch_name = $2
	`, buildingID, branchName)
	if err != nil {
		return fmt.Errorf("failed to check for unique commits: %w", err)
	}

	if uniqueCommits > 0 && !branchForceDelete {
		fmt.Printf("Branch '%s' has %d commits.\n", branchName, uniqueCommits)
		fmt.Printf("Use --force to delete anyway (commits will be preserved but unassociated).\n")
		return nil
	}

	// Delete branch
	_, err = db.ExecContext(ctx, `
		DELETE FROM state_branches
		WHERE building_id = $1 AND branch_name = $2
	`, buildingID, branchName)
	if err != nil {
		return fmt.Errorf("failed to delete branch: %w", err)
	}

	fmt.Printf("✓ Branch '%s' deleted\n", branchName)
	if uniqueCommits > 0 {
		fmt.Printf("  Note: %d commits were preserved but are no longer associated with a branch\n", uniqueCommits)
	}

	return nil
}

func runBranchSwitch(cmd *cobra.Command, args []string) error {
	buildingID := args[0]
	branchName := args[1]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	ctx := context.Background()

	// Check if target branch exists
	var targetBranch state.StateBranch
	err = db.GetContext(ctx, &targetBranch, `
		SELECT * FROM state_branches
		WHERE building_id = $1 AND branch_name = $2
	`, buildingID, branchName)
	if err != nil {
		return fmt.Errorf("branch '%s' not found", branchName)
	}

	// Update default branch
	tx, err := db.BeginTxx(ctx, nil)
	if err != nil {
		return fmt.Errorf("failed to begin transaction: %w", err)
	}
	defer tx.Rollback()

	// Clear current default
	_, err = tx.ExecContext(ctx, `
		UPDATE state_branches
		SET is_default = false
		WHERE building_id = $1 AND is_default = true
	`, buildingID)
	if err != nil {
		return fmt.Errorf("failed to clear current default: %w", err)
	}

	// Set new default
	_, err = tx.ExecContext(ctx, `
		UPDATE state_branches
		SET is_default = true, updated_at = $2
		WHERE building_id = $1 AND branch_name = $3
	`, buildingID, time.Now(), branchName)
	if err != nil {
		return fmt.Errorf("failed to set new default: %w", err)
	}

	// Commit transaction
	if err = tx.Commit(); err != nil {
		return fmt.Errorf("failed to commit: %w", err)
	}

	fmt.Printf("✓ Switched to branch '%s'\n", branchName)

	// Show branch status
	if targetBranch.HeadStateID != nil {
		var headState state.BuildingState
		err = db.GetContext(ctx, &headState, `
			SELECT version, captured_at, message FROM building_states
			WHERE id = $1
		`, *targetBranch.HeadStateID)
		if err == nil {
			fmt.Printf("\nCurrent state: v%s\n", headState.Version)
			fmt.Printf("  Captured: %s\n", headState.CapturedAt.Format("2006-01-02 15:04"))
			if headState.Message != "" {
				fmt.Printf("  Message: %s\n", headState.Message)
			}
		}
	}

	return nil
}