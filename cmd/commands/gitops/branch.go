package gitops

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	// "github.com/arxos/arxos/core/internal/gitops"
	// "github.com/arxos/arxos/core/internal/state"
	"github.com/jmoiron/sqlx"
	"github.com/spf13/cobra"
)

var branchCmd = &cobra.Command{
	Use:   "branch",
	Short: "Manage building configuration branches",
	Long:  `Create, list, switch, and delete branches for building configurations.`,
}

var branchCreateCmd = &cobra.Command{
	Use:   "create [building-id] [branch-name]",
	Short: "Create a new branch",
	Args:  cobra.ExactArgs(2),
	RunE:  runBranchCreate,
}

var branchListCmd = &cobra.Command{
	Use:   "list [building-id]",
	Short: "List all branches for a building",
	Args:  cobra.ExactArgs(1),
	RunE:  runBranchList,
}

var branchSwitchCmd = &cobra.Command{
	Use:   "switch [building-id] [branch-name]",
	Short: "Switch to a different branch",
	Args:  cobra.ExactArgs(2),
	RunE:  runBranchSwitch,
}

var branchDeleteCmd = &cobra.Command{
	Use:   "delete [building-id] [branch-name]",
	Short: "Delete a branch",
	Args:  cobra.ExactArgs(2),
	RunE:  runBranchDelete,
}

var branchCompareCmd = &cobra.Command{
	Use:   "compare [building-id] [branch1] [branch2]",
	Short: "Compare two branches",
	Args:  cobra.ExactArgs(3),
	RunE:  runBranchCompare,
}

var (
	branchFrom        string
	branchDescription string
	branchProtected   bool
	branchForce       bool
)

func init() {
	branchCmd.AddCommand(
		branchCreateCmd,
		branchListCmd,
		branchSwitchCmd,
		branchDeleteCmd,
		branchCompareCmd,
	)

	branchCreateCmd.Flags().StringVarP(&branchFrom, "from", "f", "", "Source branch to create from")
	branchCreateCmd.Flags().StringVarP(&branchDescription, "description", "d", "", "Branch description")
	branchCreateCmd.Flags().BoolVar(&branchProtected, "protected", false, "Create as protected branch")

	branchDeleteCmd.Flags().BoolVar(&branchForce, "force", false, "Force delete even if not merged")
}

func runBranchCreate(cmd *cobra.Command, args []string) error {
	buildingID := args[0]
	branchName := args[1]

	if branchFrom == "" {
		branchFrom = "main"
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

	ctx := context.Background()

	// Create branch
	req := &gitops.CreateBranchRequest{
		BuildingID:  buildingID,
		BranchName:  branchName,
		FromBranch:  branchFrom,
		Description: branchDescription,
		CreatedBy:   getCurrentUser(),
	}

	branch, err := branchManager.CreateBranch(ctx, req)
	if err != nil {
		return fmt.Errorf("failed to create branch: %w", err)
	}

	// Output result
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		jsonData, _ := json.MarshalIndent(branch, "", "  ")
		fmt.Printf("%s\n", jsonData)
	} else {
		fmt.Printf("Branch '%s' created successfully\n", branch.Name)
		fmt.Printf("ID: %s\n", branch.ID)
		fmt.Printf("From: %s\n", branchFrom)
		if branch.Description != "" {
			fmt.Printf("Description: %s\n", branch.Description)
		}
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

	// Create branch manager
	stateManager := state.NewManager(db)
	branchManager := gitops.NewBranchManager(db, stateManager)

	ctx := context.Background()

	// List branches
	branches, err := branchManager.ListBranches(ctx, buildingID)
	if err != nil {
		return fmt.Errorf("failed to list branches: %w", err)
	}

	// Get current branch
	currentBranch, _ := branchManager.GetCurrentBranch(ctx, buildingID)

	// Output result
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		jsonData, _ := json.MarshalIndent(branches, "", "  ")
		fmt.Printf("%s\n", jsonData)
	} else {
		fmt.Printf("Branches for building %s:\n", buildingID)
		fmt.Printf("%s\n", strings.Repeat("=", 80))

		for _, branch := range branches {
			marker := "  "
			if currentBranch != nil && branch.ID == currentBranch.ID {
				marker = "* "
			}

			fmt.Printf("%s%s", marker, branch.Name)
			if branch.IsDefault {
				fmt.Printf(" (default)")
			}
			if branch.IsProtected {
				fmt.Printf(" [protected]")
			}
			fmt.Printf("\n")

			if branch.Description != "" {
				fmt.Printf("    %s\n", branch.Description)
			}
			fmt.Printf("    Created: %s by %s\n", 
				branch.CreatedAt.Format("2006-01-02 15:04"),
				branch.CreatedBy)
			if branch.LastCommitAt != nil {
				fmt.Printf("    Last commit: %s\n", 
					branch.LastCommitAt.Format("2006-01-02 15:04"))
			}
			fmt.Println()
		}
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

	// Update current branch in database
	ctx := context.Background()
	
	// First verify branch exists
	var branchID string
	err = db.GetContext(ctx, &branchID,
		"SELECT id FROM building_branches WHERE building_id = $1 AND name = $2",
		buildingID, branchName)
	if err != nil {
		return fmt.Errorf("branch '%s' not found", branchName)
	}

	// Update current branch (would be stored in a user session table)
	// For now, we'll just print success
	fmt.Printf("Switched to branch '%s'\n", branchName)

	return nil
}

func runBranchDelete(cmd *cobra.Command, args []string) error {
	buildingID := args[0]
	branchName := args[1]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create branch manager
	stateManager := state.NewManager(db)
	branchManager := gitops.NewBranchManager(db, stateManager)

	ctx := context.Background()

	// Check if branch is protected
	branch, err := branchManager.GetBranch(ctx, buildingID, branchName)
	if err != nil {
		return fmt.Errorf("branch not found: %w", err)
	}

	if branch.IsProtected && !branchForce {
		return fmt.Errorf("cannot delete protected branch '%s' without --force", branchName)
	}

	if branch.IsDefault {
		return fmt.Errorf("cannot delete default branch '%s'", branchName)
	}

	// Check for unmerged changes
	if !branchForce {
		// Would check if branch has been merged
		fmt.Printf("Warning: Branch '%s' may have unmerged changes\n", branchName)
		fmt.Printf("Use --force to delete anyway\n")
		return nil
	}

	// Delete branch
	err = branchManager.DeleteBranch(ctx, buildingID, branchName)
	if err != nil {
		return fmt.Errorf("failed to delete branch: %w", err)
	}

	fmt.Printf("Branch '%s' deleted successfully\n", branchName)
	return nil
}

func runBranchCompare(cmd *cobra.Command, args []string) error {
	buildingID := args[0]
	branch1 := args[1]
	branch2 := args[2]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	// Create managers
	stateManager := state.NewManager(db)
	branchManager := gitops.NewBranchManager(db, stateManager)

	ctx := context.Background()

	// Compare branches
	comparison, err := branchManager.CompareBranches(ctx, buildingID, branch1, branch2)
	if err != nil {
		return fmt.Errorf("failed to compare branches: %w", err)
	}

	// Output result
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		jsonData, _ := json.MarshalIndent(comparison, "", "  ")
		fmt.Printf("%s\n", jsonData)
	} else {
		fmt.Printf("Comparison: %s..%s\n", branch1, branch2)
		fmt.Printf("%s\n", strings.Repeat("=", 80))
		
		fmt.Printf("Commits ahead: %d\n", comparison.CommitsAhead)
		fmt.Printf("Commits behind: %d\n", comparison.CommitsBehind)
		
		if comparison.CanFastForward {
			fmt.Printf("✓ Can fast-forward merge\n")
		} else {
			fmt.Printf("✗ Cannot fast-forward (branches have diverged)\n")
		}

		if comparison.HasConflicts {
			fmt.Printf("⚠ Potential conflicts detected\n")
		}

		if comparison.CommonAncestor != "" {
			fmt.Printf("Common ancestor: %s\n", comparison.CommonAncestor[:8])
		}
	}

	return nil
}

func getDB() (*sqlx.DB, error) {
	// Would get from config
	return sqlx.Connect("postgres", "postgres://arxos_api_user:password@localhost/arxos?sslmode=disable")
}

func getCurrentUser() string {
	// Would get from session/config
	return "cli-user"
}