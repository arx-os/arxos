package integration

import (
	"context"
	"fmt"
	"os"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure/git"
	"github.com/spf13/cobra"
)

// GitServiceProvider provides access to Git services
type GitServiceProvider interface {
	GetGitProvider() git.Provider
}

// BuildingServiceProvider provides access to building services
type BuildingServiceProvider interface {
	GetBuildingUseCase() interface{} // Using interface{} to avoid import issues
}

// CreateGitExportCommand creates the git export command
func CreateGitExportCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "export --to-git <building-id>",
		Short: "Export building data to Git repository",
		Long: `Export building data from PostGIS to a Git repository in YAML format.
This command converts building data to YAML files and commits them to a Git repository.

Examples:
  arx export --to-git BLD-001 --repo-url https://github.com/company/building-bld-001
  arx export --to-git BLD-002 --repo-url https://gitlab.com/company/building-bld-002 --branch main
  arx export --to-git BLD-003 --local-path ./building-repo --commit-message "Export building data"`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			buildingID := args[0]
			ctx := context.Background()

			// Get flags
			repoURL, _ := cmd.Flags().GetString("repo-url")
			localPath, _ := cmd.Flags().GetString("local-path")
			branch, _ := cmd.Flags().GetString("branch")
			commitMessage, _ := cmd.Flags().GetString("commit-message")
			dryRun, _ := cmd.Flags().GetBool("dry-run")

			// Validate inputs
			if repoURL == "" && localPath == "" {
				return fmt.Errorf("either --repo-url or --local-path must be specified")
			}

			if branch == "" {
				branch = "main"
			}

			if commitMessage == "" {
				commitMessage = fmt.Sprintf("Export building data for %s", buildingID)
			}

			fmt.Printf("Exporting building %s to Git repository\n", buildingID)
			fmt.Printf("  Repository: %s\n", repoURL)
			fmt.Printf("  Local Path: %s\n", localPath)
			fmt.Printf("  Branch: %s\n", branch)
			fmt.Printf("  Commit Message: %s\n", commitMessage)
			fmt.Printf("  Dry Run: %v\n", dryRun)

			// For now, create a mock building for demonstration
			// TODO: Integrate with actual building service when available
			fmt.Printf("  Creating mock building data for demonstration...\n")

			// Create a simple mock building
			mockBuilding := &struct {
				ID          types.ID
				Name        string
				Address     string
				Coordinates *struct {
					X float64
					Y float64
					Z float64
				}
				CreatedAt time.Time
				UpdatedAt time.Time
			}{
				ID:      types.FromString(buildingID),
				Name:    "Mock Building " + buildingID,
				Address: "123 Demo Street, Demo City",
				Coordinates: &struct {
					X float64
					Y float64
					Z float64
				}{X: 0, Y: 0, Z: 0},
				CreatedAt: time.Now(),
				UpdatedAt: time.Now(),
			}

			fmt.Printf("  Found building: %s\n", mockBuilding.Name)

			// Create Git provider configuration
			var gitConfig *git.Config
			if repoURL != "" {
				// Remote repository
				gitConfig = &git.Config{
					Provider: string(git.ProviderGitHub), // Default to GitHub, could be detected from URL
					Repository: git.RepositoryConfig{
						URL:    repoURL,
						Branch: branch,
						Owner:  extractOwnerFromURL(repoURL),
						Name:   extractRepoNameFromURL(repoURL),
					},
					Auth: git.AuthConfig{
						Token: getTokenFromEnv(),
					},
				}
			} else {
				// Local repository
				gitConfig = &git.Config{
					Provider: string(git.ProviderLocal),
					Repository: git.RepositoryConfig{
						BasePath: localPath,
						Branch:   branch,
					},
				}
			}

			// Create Git provider
			var gitProvider git.Provider
			var err error
			gitProvider, err = git.NewProvider(gitConfig)
			if err != nil {
				return fmt.Errorf("failed to create Git provider: %w", err)
			}

			if dryRun {
				fmt.Printf("  DRY RUN: Would export the following files:\n")
				fmt.Printf("    building.yml\n")
				fmt.Printf("  DRY RUN: Would commit with message: %s\n", commitMessage)
				return nil
			}

			// Export building data
			fmt.Printf("  Exporting building data to YAML...\n")

			// Create simple YAML content for demonstration
			yamlContent := fmt.Sprintf(`apiVersion: arxos.io/v1
kind: Building
metadata:
  name: "%s"
  id: "%s"
  createdAt: "%s"
  updatedAt: "%s"
spec:
  address: "%s"
  coordinates:
    x: %.2f
    y: %.2f
    z: %.2f
status:
  phase: Active
`, mockBuilding.Name, mockBuilding.ID.String(),
				mockBuilding.CreatedAt.Format(time.RFC3339),
				mockBuilding.UpdatedAt.Format(time.RFC3339),
				mockBuilding.Address,
				mockBuilding.Coordinates.X, mockBuilding.Coordinates.Y, mockBuilding.Coordinates.Z)

			err = gitProvider.WriteFile(ctx, "building.yml", []byte(yamlContent))
			if err != nil {
				return fmt.Errorf("failed to write building.yml: %w", err)
			}

			// Commit changes
			fmt.Printf("  Committing changes...\n")
			err = gitProvider.Commit(ctx, commitMessage)
			if err != nil {
				return fmt.Errorf("failed to commit changes: %w", err)
			}

			// Push to remote if applicable
			if repoURL != "" {
				fmt.Printf("  Pushing to remote repository...\n")
				err = gitProvider.Push(ctx)
				if err != nil {
					return fmt.Errorf("failed to push to remote: %w", err)
				}
			}

			fmt.Printf("✅ Successfully exported building %s to Git repository\n", buildingID)
			fmt.Printf("  Files exported: 1\n")
			fmt.Printf("  Repository: %s\n", repoURL)
			fmt.Printf("  Branch: %s\n", branch)

			return nil
		},
	}

	// Add flags
	cmd.Flags().String("repo-url", "", "Remote repository URL (GitHub, GitLab, etc.)")
	cmd.Flags().String("local-path", "", "Local repository path")
	cmd.Flags().StringP("branch", "b", "main", "Target branch name")
	cmd.Flags().StringP("commit-message", "m", "", "Commit message (default: auto-generated)")
	cmd.Flags().Bool("dry-run", false, "Show what would be exported without making changes")
	cmd.Flags().String("token", "", "Authentication token (or use GITHUB_TOKEN/GITLAB_TOKEN env var)")

	return cmd
}

// Helper functions

func extractOwnerFromURL(url string) string {
	// Extract owner from URLs like https://github.com/owner/repo
	parts := strings.Split(url, "/")
	if len(parts) >= 4 {
		return parts[3]
	}
	return ""
}

func extractRepoNameFromURL(url string) string {
	// Extract repo name from URLs like https://github.com/owner/repo
	parts := strings.Split(url, "/")
	if len(parts) >= 5 {
		return strings.TrimSuffix(parts[4], ".git")
	}
	return ""
}

func getTokenFromEnv() string {
	// Check for GitHub token first, then GitLab
	if token := os.Getenv("GITHUB_TOKEN"); token != "" {
		return token
	}
	if token := os.Getenv("GITLAB_TOKEN"); token != "" {
		return token
	}
	return ""
}
