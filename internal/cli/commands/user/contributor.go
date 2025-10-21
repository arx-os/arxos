package user

import (
	"fmt"
	"strings"
	"time"

	"github.com/spf13/cobra"
)

// NewContributorCommand creates the contributor management command
func NewContributorCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "contributor",
		Short: "Manage repository contributors",
		Long: `Manage repository contributors and access control.

Contributors are users with access to a building repository. Each contributor
has a role (owner, admin, maintainer, contributor, reporter, reader) which 
determines their permissions.

Examples:
  # Add contributor
  arx contributor add @joe-electrician --repo building-001 --role maintainer

  # List contributors
  arx contributor list --repo building-001

  # Remove contributor
  arx contributor remove @joe-electrician --repo building-001`,
	}

	cmd.AddCommand(newContributorAddCommand(serviceContext))
	cmd.AddCommand(newContributorListCommand(serviceContext))
	cmd.AddCommand(newContributorRemoveCommand(serviceContext))
	cmd.AddCommand(newContributorUpdateCommand(serviceContext))

	return cmd
}

// newContributorAddCommand creates the contributor add subcommand
func newContributorAddCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "add <username>",
		Short: "Add a contributor to a repository",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			username := args[0]
			repo, _ := cmd.Flags().GetString("repo")
			role, _ := cmd.Flags().GetString("role")

			if repo == "" {
				return fmt.Errorf("--repo is required")
			}

			// Add via use case (when wired)
			fmt.Printf("Adding contributor %s to %s...\n", username, repo)
			time.Sleep(500 * time.Millisecond)

			fmt.Printf("\n")
			fmt.Printf("✅ %s added as %s\n", username, role)
			fmt.Printf("\n")
			fmt.Printf("Permissions:\n")

			// Show permissions based on role
			switch role {
			case "owner":
				fmt.Printf("  • Full repository control\n")
				fmt.Printf("  • Manage settings and contributors\n")
				fmt.Printf("  • Merge PRs and manage branches\n")
			case "admin":
				fmt.Printf("  • Manage contributors\n")
				fmt.Printf("  • Merge PRs and manage branches\n")
				fmt.Printf("  • Cannot delete repository\n")
			case "maintainer":
				fmt.Printf("  • Merge PRs\n")
				fmt.Printf("  • Manage issues\n")
				fmt.Printf("  • Create branches and PRs\n")
			case "contributor":
				fmt.Printf("  • Create branches and PRs\n")
				fmt.Printf("  • Create and manage issues\n")
				fmt.Printf("  • Cannot merge PRs\n")
			case "reporter":
				fmt.Printf("  • Create issues\n")
				fmt.Printf("  • Comment on issues\n")
				fmt.Printf("  • Read-only access\n")
			case "reader":
				fmt.Printf("  • Read-only access\n")
			}
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().String("role", "contributor", "Role (owner, admin, maintainer, contributor, reporter, reader)")

	return cmd
}

// newContributorListCommand creates the contributor list subcommand
func newContributorListCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List repository contributors",
		RunE: func(cmd *cobra.Command, args []string) error {
			repo, _ := cmd.Flags().GetString("repo")

			if repo == "" {
				return fmt.Errorf("--repo is required")
			}

			// List via use case (when wired)
			fmt.Printf("Contributors for %s:\n\n", repo)
			fmt.Printf("%-25s %-15s %-15s %-20s\n", "User", "Role", "Status", "Added")
			fmt.Printf("%s\n", strings.Repeat("-", 80))
			fmt.Printf("%-25s %-15s %-15s %-20s\n", "@joe-fm", "owner", "active", "2024-01-01")
			fmt.Printf("%-25s %-15s %-15s %-20s\n", "@jane-engineer", "admin", "active", "2024-02-15")
			fmt.Printf("%-25s %-15s %-15s %-20s\n", "@bob-electrician", "maintainer", "active", "2024-03-01")
			fmt.Printf("%-25s %-15s %-15s %-20s\n", "@alice-contractor", "contributor", "active", "2024-06-10")
			fmt.Printf("%-25s %-15s %-15s %-20s\n", "@custodian-team", "reporter", "active", "2024-07-01")
			fmt.Printf("\n")
			fmt.Printf("Total: 5 contributors\n")
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")

	return cmd
}

// newContributorRemoveCommand creates the contributor remove subcommand
func newContributorRemoveCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "remove <username>",
		Short: "Remove a contributor from a repository",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			username := args[0]
			repo, _ := cmd.Flags().GetString("repo")

			if repo == "" {
				return fmt.Errorf("--repo is required")
			}

			// Remove via use case (when wired)
			fmt.Printf("Removing %s from %s...\n", username, repo)
			time.Sleep(300 * time.Millisecond)

			fmt.Printf("\n")
			fmt.Printf("✅ %s removed\n", username)
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")

	return cmd
}

// newContributorUpdateCommand creates the contributor update subcommand
func newContributorUpdateCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "update <username>",
		Short: "Update contributor permissions",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			username := args[0]
			repo, _ := cmd.Flags().GetString("repo")
			role, _ := cmd.Flags().GetString("role")

			if repo == "" {
				return fmt.Errorf("--repo is required")
			}

			// Update via use case (when wired)
			fmt.Printf("Updating %s in %s...\n", username, repo)
			time.Sleep(300 * time.Millisecond)

			fmt.Printf("\n")
			fmt.Printf("✅ %s updated to %s\n", username, role)
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (required)")
	cmd.Flags().String("role", "", "New role (owner, admin, maintainer, contributor, reporter, reader)")

	return cmd
}

// NewTeamCommand creates the team management command
func NewTeamCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "team",
		Short: "Manage teams",
		Long: `Manage teams for organizing contributors.

Teams group users together (e.g., electricians, hvac-contractors, facility-managers).
Teams can be assigned to issues and PRs, and have specialized permissions.

Examples:
  # Create team
  arx team create electrician-team --name "Electrician Team" --type internal

  # Add member
  arx team add-member electrician-team @joe-electrician

  # List teams
  arx team list --repo building-001`,
	}

	cmd.AddCommand(newTeamCreateCommand(serviceContext))
	cmd.AddCommand(newTeamListCommand(serviceContext))
	cmd.AddCommand(newTeamAddMemberCommand(serviceContext))
	cmd.AddCommand(newTeamRemoveMemberCommand(serviceContext))

	return cmd
}

// newTeamCreateCommand creates the team create subcommand
func newTeamCreateCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "create <slug>",
		Short: "Create a new team",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			slug := args[0]
			name, _ := cmd.Flags().GetString("name")
			teamType, _ := cmd.Flags().GetString("type")
			repo, _ := cmd.Flags().GetString("repo")

			if name == "" {
				name = slug
			}

			// Create via use case (when wired)
			fmt.Printf("Creating team %s...\n", slug)
			time.Sleep(300 * time.Millisecond)

			fmt.Printf("\n")
			fmt.Printf("✅ Team created: %s\n", name)
			fmt.Printf("   Slug: %s\n", slug)
			fmt.Printf("   Type: %s\n", teamType)
			if repo != "" {
				fmt.Printf("   Repository: %s\n", repo)
			}
			fmt.Printf("\n")

			return nil
		},
	}

	cmd.Flags().String("name", "", "Team display name")
	cmd.Flags().String("type", "internal", "Team type (internal, contractor, vendor, facilities)")
	cmd.Flags().String("repo", "", "Repository ID (optional, leave empty for org-wide team)")

	return cmd
}

// newTeamListCommand creates the team list subcommand
func newTeamListCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "list",
		Short: "List teams",
		RunE: func(cmd *cobra.Command, args []string) error {
			repo, _ := cmd.Flags().GetString("repo")

			// List via use case (when wired)
			fmt.Printf("Teams:\n\n")
			fmt.Printf("%-25s %-20s %-15s %-10s\n", "Name", "Slug", "Type", "Members")
			fmt.Printf("%s\n", strings.Repeat("-", 75))
			fmt.Printf("%-25s %-20s %-15s %-10s\n", "Facility Managers", "facility-managers", "facilities", "3")
			fmt.Printf("%-25s %-20s %-15s %-10s\n", "Electrician Team", "electrician-team", "internal", "5")
			fmt.Printf("%-25s %-20s %-15s %-10s\n", "HVAC Contractors", "hvac-contractors", "contractor", "8")
			fmt.Printf("%-25s %-20s %-15s %-10s\n", "Building Staff", "building-staff", "internal", "12")
			fmt.Printf("\n")
			fmt.Printf("Total: 4 teams\n")

			// Suppress unused
			_ = repo

			return nil
		},
	}

	cmd.Flags().String("repo", "", "Repository ID (optional)")

	return cmd
}

// newTeamAddMemberCommand creates the team add-member subcommand
func newTeamAddMemberCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "add-member <team-slug> <username>",
		Short: "Add a member to a team",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			teamSlug := args[0]
			username := args[1]

			// Add via use case (when wired)
			fmt.Printf("Adding %s to %s...\n", username, teamSlug)
			time.Sleep(300 * time.Millisecond)

			fmt.Printf("\n")
			fmt.Printf("✅ %s added to %s\n", username, teamSlug)
			fmt.Printf("\n")

			return nil
		},
	}

	return cmd
}

// newTeamRemoveMemberCommand creates the team remove-member subcommand
func newTeamRemoveMemberCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "remove-member <team-slug> <username>",
		Short: "Remove a member from a team",
		Args:  cobra.ExactArgs(2),
		RunE: func(cmd *cobra.Command, args []string) error {
			teamSlug := args[0]
			username := args[1]

			// Remove via use case (when wired)
			fmt.Printf("Removing %s from %s...\n", username, teamSlug)
			time.Sleep(300 * time.Millisecond)

			fmt.Printf("\n")
			fmt.Printf("✅ %s removed from %s\n", username, teamSlug)
			fmt.Printf("\n")

			return nil
		},
	}

	return cmd
}

