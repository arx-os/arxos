package gitops

import (
	"context"
	"encoding/json"
	"fmt"
	"strings"

	"github.com/google/uuid"
	"github.com/jmoiron/sqlx"
	"github.com/spf13/cobra"
)

var protectCmd = &cobra.Command{
	Use:   "protect",
	Short: "Manage branch protection rules",
	Long:  `Configure and manage branch protection rules for building configurations.`,
}

var protectAddCmd = &cobra.Command{
	Use:   "add [building-id] [branch-pattern]",
	Short: "Add a branch protection rule",
	Args:  cobra.ExactArgs(2),
	RunE:  runProtectAdd,
}

var protectListCmd = &cobra.Command{
	Use:   "list [building-id]",
	Short: "List branch protection rules",
	Args:  cobra.ExactArgs(1),
	RunE:  runProtectList,
}

var protectRemoveCmd = &cobra.Command{
	Use:   "remove [building-id] [rule-id]",
	Short: "Remove a branch protection rule",
	Args:  cobra.ExactArgs(2),
	RunE:  runProtectRemove,
}

var protectUpdateCmd = &cobra.Command{
	Use:   "update [building-id] [rule-id]",
	Short: "Update a branch protection rule",
	Args:  cobra.ExactArgs(2),
	RunE:  runProtectUpdate,
}

var (
	protectRequireApprovals   int
	protectRequireStatusChecks bool
	protectRequireUpToDate    bool
	protectDismissStale       bool
	protectRestrictPush       bool
	protectRestrictMerge      bool
	protectAllowForcePush     bool
	protectAllowDeletions     bool
	protectEnforceAdmins      bool
	protectStatusChecks       []string
	protectPushAllowlist      []string
	protectMergeAllowlist     []string
)

func init() {
	protectCmd.AddCommand(
		protectAddCmd,
		protectListCmd,
		protectRemoveCmd,
		protectUpdateCmd,
	)

	// Add flags
	protectAddCmd.Flags().IntVar(&protectRequireApprovals, "require-approvals", 1, "Number of required approvals")
	protectAddCmd.Flags().BoolVar(&protectRequireStatusChecks, "require-status-checks", true, "Require status checks to pass")
	protectAddCmd.Flags().BoolVar(&protectRequireUpToDate, "require-up-to-date", true, "Require branch to be up to date")
	protectAddCmd.Flags().BoolVar(&protectDismissStale, "dismiss-stale", true, "Dismiss stale reviews on new commits")
	protectAddCmd.Flags().BoolVar(&protectRestrictPush, "restrict-push", false, "Restrict who can push")
	protectAddCmd.Flags().BoolVar(&protectRestrictMerge, "restrict-merge", false, "Restrict who can merge")
	protectAddCmd.Flags().BoolVar(&protectAllowForcePush, "allow-force-push", false, "Allow force push")
	protectAddCmd.Flags().BoolVar(&protectAllowDeletions, "allow-deletions", false, "Allow branch deletion")
	protectAddCmd.Flags().BoolVar(&protectEnforceAdmins, "enforce-admins", false, "Enforce rules for admins")
	protectAddCmd.Flags().StringSliceVar(&protectStatusChecks, "status-checks", []string{}, "Required status check names")
	protectAddCmd.Flags().StringSliceVar(&protectPushAllowlist, "push-allowlist", []string{}, "Users allowed to push")
	protectAddCmd.Flags().StringSliceVar(&protectMergeAllowlist, "merge-allowlist", []string{}, "Users allowed to merge")

	// Update has same flags
	protectUpdateCmd.Flags().IntVar(&protectRequireApprovals, "require-approvals", -1, "Number of required approvals")
	protectUpdateCmd.Flags().BoolVar(&protectRequireStatusChecks, "require-status-checks", false, "Require status checks to pass")
	protectUpdateCmd.Flags().BoolVar(&protectRequireUpToDate, "require-up-to-date", false, "Require branch to be up to date")
	protectUpdateCmd.Flags().BoolVar(&protectDismissStale, "dismiss-stale", false, "Dismiss stale reviews on new commits")
	protectUpdateCmd.Flags().BoolVar(&protectEnforceAdmins, "enforce-admins", false, "Enforce rules for admins")
}

type BranchProtectionRule struct {
	ID                     string   `json:"id" db:"id"`
	BuildingID             string   `json:"building_id" db:"building_id"`
	BranchPattern          string   `json:"branch_pattern" db:"branch_pattern"`
	RequirePR              bool     `json:"require_pr" db:"require_pr"`
	RequireApprovals       int      `json:"require_approvals" db:"require_approvals"`
	DismissStaleReviews    bool     `json:"dismiss_stale_reviews" db:"dismiss_stale_reviews"`
	RequireStatusChecks    bool     `json:"require_status_checks" db:"require_status_checks"`
	RequiredStatusChecks   []string `json:"required_status_check_names"`
	RequireUpToDate        bool     `json:"require_up_to_date" db:"require_up_to_date"`
	RestrictPush           bool     `json:"restrict_push" db:"restrict_push"`
	PushAllowlist          []string `json:"push_allowlist"`
	RestrictMerge          bool     `json:"restrict_merge" db:"restrict_merge"`
	MergeAllowlist         []string `json:"merge_allowlist"`
	AllowForcePush         bool     `json:"allow_force_push" db:"allow_force_push"`
	AllowDeletions         bool     `json:"allow_deletions" db:"allow_deletions"`
	EnforceAdmins          bool     `json:"enforce_admins" db:"enforce_admins"`
	IsActive               bool     `json:"is_active" db:"is_active"`
}

func runProtectAdd(cmd *cobra.Command, args []string) error {
	buildingID := args[0]
	branchPattern := args[1]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	ctx := context.Background()

	// Create protection rule
	ruleID := uuid.New().String()
	
	query := `
		INSERT INTO branch_protection_rules (
			id, building_id, branch_pattern,
			require_pr, require_approvals, dismiss_stale_reviews,
			require_status_checks, required_status_check_names, require_up_to_date,
			restrict_push, push_allowlist, restrict_merge, merge_allowlist,
			allow_force_push, allow_deletions, enforce_admins, is_active
		) VALUES (
			$1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, true
		)`

	_, err = db.ExecContext(ctx, query,
		ruleID, buildingID, branchPattern,
		true, protectRequireApprovals, protectDismissStale,
		protectRequireStatusChecks, pq.Array(protectStatusChecks), protectRequireUpToDate,
		protectRestrictPush, pq.Array(protectPushAllowlist),
		protectRestrictMerge, pq.Array(protectMergeAllowlist),
		protectAllowForcePush, protectAllowDeletions, protectEnforceAdmins)
	if err != nil {
		return fmt.Errorf("failed to create protection rule: %w", err)
	}

	fmt.Printf("Branch protection rule created successfully\n")
	fmt.Printf("ID: %s\n", ruleID)
	fmt.Printf("Pattern: %s\n", branchPattern)
	fmt.Printf("Required approvals: %d\n", protectRequireApprovals)
	
	if len(protectStatusChecks) > 0 {
		fmt.Printf("Required status checks: %s\n", strings.Join(protectStatusChecks, ", "))
	}

	return nil
}

func runProtectList(cmd *cobra.Command, args []string) error {
	buildingID := args[0]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	ctx := context.Background()

	// List protection rules
	var rules []BranchProtectionRule
	query := `
		SELECT 
			id, building_id, branch_pattern,
			require_pr, require_approvals, dismiss_stale_reviews,
			require_status_checks, require_up_to_date,
			restrict_push, restrict_merge,
			allow_force_push, allow_deletions, enforce_admins, is_active
		FROM branch_protection_rules
		WHERE building_id = $1 AND is_active = true
		ORDER BY branch_pattern`

	err = db.SelectContext(ctx, &rules, query, buildingID)
	if err != nil {
		return fmt.Errorf("failed to list protection rules: %w", err)
	}

	// Output result
	if outputJSON, _ := cmd.Flags().GetBool("json"); outputJSON {
		jsonData, _ := json.MarshalIndent(rules, "", "  ")
		fmt.Printf("%s\n", jsonData)
	} else {
		fmt.Printf("Branch Protection Rules for building %s:\n", buildingID)
		fmt.Printf("%s\n", strings.Repeat("=", 80))

		if len(rules) == 0 {
			fmt.Println("No protection rules configured")
			return nil
		}

		for _, rule := range rules {
			fmt.Printf("\nPattern: %s\n", rule.BranchPattern)
			fmt.Printf("ID: %s\n", rule.ID[:8])
			
			if rule.RequireApprovals > 0 {
				fmt.Printf("  ✓ Require %d approval(s)\n", rule.RequireApprovals)
			}
			if rule.RequireStatusChecks {
				fmt.Printf("  ✓ Require status checks\n")
			}
			if rule.RequireUpToDate {
				fmt.Printf("  ✓ Require up-to-date branch\n")
			}
			if rule.DismissStaleReviews {
				fmt.Printf("  ✓ Dismiss stale reviews\n")
			}
			if rule.RestrictPush {
				fmt.Printf("  ✓ Restrict push access\n")
			}
			if rule.RestrictMerge {
				fmt.Printf("  ✓ Restrict merge access\n")
			}
			if rule.EnforceAdmins {
				fmt.Printf("  ✓ Enforce for admins\n")
			}
			if rule.AllowForcePush {
				fmt.Printf("  ⚠ Allow force push\n")
			}
			if rule.AllowDeletions {
				fmt.Printf("  ⚠ Allow deletions\n")
			}
		}
	}

	return nil
}

func runProtectRemove(cmd *cobra.Command, args []string) error {
	buildingID := args[0]
	ruleID := args[1]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	ctx := context.Background()

	// Deactivate protection rule
	query := `
		UPDATE branch_protection_rules 
		SET is_active = false, updated_at = NOW()
		WHERE id = $1 AND building_id = $2`

	result, err := db.ExecContext(ctx, query, ruleID, buildingID)
	if err != nil {
		return fmt.Errorf("failed to remove protection rule: %w", err)
	}

	rows, _ := result.RowsAffected()
	if rows == 0 {
		return fmt.Errorf("protection rule not found")
	}

	fmt.Printf("Branch protection rule removed successfully\n")
	return nil
}

func runProtectUpdate(cmd *cobra.Command, args []string) error {
	buildingID := args[0]
	ruleID := args[1]

	// Get database connection
	db, err := getDB()
	if err != nil {
		return fmt.Errorf("failed to connect to database: %w", err)
	}
	defer db.Close()

	ctx := context.Background()

	// Build update query dynamically based on provided flags
	updates := []string{}
	params := []interface{}{}
	paramCount := 1

	if cmd.Flags().Changed("require-approvals") {
		updates = append(updates, fmt.Sprintf("require_approvals = $%d", paramCount))
		params = append(params, protectRequireApprovals)
		paramCount++
	}

	if cmd.Flags().Changed("require-status-checks") {
		updates = append(updates, fmt.Sprintf("require_status_checks = $%d", paramCount))
		params = append(params, protectRequireStatusChecks)
		paramCount++
	}

	if cmd.Flags().Changed("require-up-to-date") {
		updates = append(updates, fmt.Sprintf("require_up_to_date = $%d", paramCount))
		params = append(params, protectRequireUpToDate)
		paramCount++
	}

	if cmd.Flags().Changed("dismiss-stale") {
		updates = append(updates, fmt.Sprintf("dismiss_stale_reviews = $%d", paramCount))
		params = append(params, protectDismissStale)
		paramCount++
	}

	if cmd.Flags().Changed("enforce-admins") {
		updates = append(updates, fmt.Sprintf("enforce_admins = $%d", paramCount))
		params = append(params, protectEnforceAdmins)
		paramCount++
	}

	if len(updates) == 0 {
		return fmt.Errorf("no updates specified")
	}

	// Add updated_at
	updates = append(updates, fmt.Sprintf("updated_at = $%d", paramCount))
	params = append(params, "NOW()")
	paramCount++

	// Add WHERE conditions
	params = append(params, ruleID, buildingID)

	query := fmt.Sprintf(`
		UPDATE branch_protection_rules 
		SET %s
		WHERE id = $%d AND building_id = $%d`,
		strings.Join(updates, ", "), paramCount, paramCount+1)

	result, err := db.ExecContext(ctx, query, params...)
	if err != nil {
		return fmt.Errorf("failed to update protection rule: %w", err)
	}

	rows, _ := result.RowsAffected()
	if rows == 0 {
		return fmt.Errorf("protection rule not found")
	}

	fmt.Printf("Branch protection rule updated successfully\n")
	return nil
}

// Helper for PostgreSQL arrays
type pq struct{}

func (pq) Array(a interface{}) interface{} {
	// Would use lib/pq in production
	return a
}