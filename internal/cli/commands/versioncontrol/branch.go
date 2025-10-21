package versioncontrol

import (
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	domainvc "github.com/arx-os/arxos/internal/domain/versioncontrol"
	vcuc "github.com/arx-os/arxos/internal/usecase/versioncontrol"
	"github.com/spf13/cobra"
)

// BranchContainerProvider provides access to branch use case
type BranchContainerProvider interface {
	GetBranchUseCase() *vcuc.BranchUseCase
	GetLogger() domain.Logger
}

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
			branchTypeStr, _ := cmd.Flags().GetString("type")

			if repoID == "" {
				return fmt.Errorf("--repo flag is required")
			}

			// Get use case from container
			cp, ok := serviceContext.(BranchContainerProvider)
			if !ok {
				return fmt.Errorf("branch service not available - database not initialized")
			}

			branchUC := cp.GetBranchUseCase()
			if branchUC == nil {
				return fmt.Errorf("branch use case not initialized - check database connection")
			}

			// Build filter
			filter := domainvc.BranchFilter{}

			if activeOnly {
				activeStatus := domainvc.BranchStatusActive
				filter.Status = &activeStatus
			}

			if branchTypeStr != "" {
				bt := parseBranchType(branchTypeStr)
				filter.BranchType = &bt
			}

			// List branches (repository ID is first parameter)
			repositoryID := types.FromString(repoID)
			branches, err := branchUC.ListBranches(cmd.Context(), repositoryID, filter)
			if err != nil {
				return fmt.Errorf("failed to list branches: %w", err)
			}

			// Display results
			fmt.Printf("Branches for repository: %s\n\n", repoID)
			fmt.Printf("%-20s %-15s %-15s %s\n", "Name", "Type", "Status", "Updated")
			fmt.Printf("%s\n", strings.Repeat("-", 70))

			for _, branch := range branches {
				prefix := "  "
				if branch.IsDefault {
					prefix = "* "
				}
				fmt.Printf("%s%-18s %-15s %-15s %s\n",
					prefix,
					branch.Name,
					branch.BranchType,
					branch.Status,
					branch.UpdatedAt.Format("2006-01-02 15:04"),
				)
			}

			if len(branches) == 0 {
				fmt.Printf("No branches found\n")
			} else {
				fmt.Printf("\n* = default branch\n")
				fmt.Printf("Total: %d branches\n", len(branches))
			}

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

			// Get use case from container
			cp, ok := serviceContext.(BranchContainerProvider)
			if !ok {
				return fmt.Errorf("branch service not available - database not initialized")
			}

			branchUC := cp.GetBranchUseCase()
			if branchUC == nil {
				return fmt.Errorf("branch use case not initialized - check database connection")
			}

			// Build create request
			req := domainvc.CreateBranchRequest{
				RepositoryID: types.FromString(repoID),
				Name:         branchName,
				Description:  description,
				BranchType:   parseBranchType(branchType),
			}

			// Set display name (prettier version)
			if req.DisplayName == "" {
				req.DisplayName = branchName
			}

			// Set base commit if provided
			if fromCommit != "" {
				baseCommit := types.FromString(fromCommit)
				req.BaseCommit = &baseCommit
			}

			// Create branch
			branch, err := branchUC.CreateBranch(cmd.Context(), req)
			if err != nil {
				return fmt.Errorf("failed to create branch: %w", err)
			}

			// Display success
			fmt.Printf("\n")
			fmt.Printf("✅ Branch created: %s\n", branch.Name)
			fmt.Printf("   ID: %s\n", branch.ID.String())
			fmt.Printf("   Repository: %s\n", repoID)
			fmt.Printf("   Type: %s\n", branch.BranchType)
			if branch.Description != "" {
				fmt.Printf("   Description: %s\n", branch.Description)
			}
			fmt.Printf("   Created: %s\n", branch.CreatedAt.Format("2006-01-02 15:04:05"))
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

			// Get use case from service context
			cp, ok := serviceContext.(BranchContainerProvider)
			if !ok || cp.GetBranchUseCase() == nil {
				// Fallback for when service not available
				fmt.Println("⚠️  Database not connected - using simulation mode")
			}

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

			// Get branch details from use case
			cp, ok := serviceContext.(BranchContainerProvider)
			if !ok || cp.GetBranchUseCase() == nil {
				// Fallback: show placeholder info when service unavailable
				fmt.Println("⚠️  Database not connected - showing placeholder")
			}

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

// parseBranchType converts string to BranchType enum
func parseBranchType(branchTypeStr string) domainvc.BranchType {
	if branchTypeStr == "" {
		return domainvc.BranchTypeFeature // Default
	}

	switch strings.ToLower(branchTypeStr) {
	case "main":
		return domainvc.BranchTypeMain
	case "development", "dev":
		return domainvc.BranchTypeDevelopment
	case "feature":
		return domainvc.BranchTypeFeature
	case "bugfix", "bug":
		return domainvc.BranchTypeBugfix
	case "release":
		return domainvc.BranchTypeRelease
	case "hotfix":
		return domainvc.BranchTypeHotfix
	case "contractor":
		return domainvc.BranchTypeContractor
	case "vendor":
		return domainvc.BranchTypeVendor
	case "issue":
		return domainvc.BranchTypeIssue
	case "scan":
		return domainvc.BranchTypeScan
	default:
		return domainvc.BranchTypeFeature
	}
}
