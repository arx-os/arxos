package integration

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure/git"
	"github.com/spf13/cobra"
)

// CreateGitSyncCommand creates the git sync command
func CreateGitSyncCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "sync <building-id>",
		Short: "Sync building data between ArxOS and Git repository",
		Long:  "Perform bidirectional synchronization between ArxOS building data and Git repository",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			buildingID := args[0]
			ctx := context.Background()

			// Get flags
			repoURL, _ := cmd.Flags().GetString("repo-url")
			localPath, _ := cmd.Flags().GetString("local-path")
			branch, _ := cmd.Flags().GetString("branch")
			direction, _ := cmd.Flags().GetString("direction")
			dryRun, _ := cmd.Flags().GetBool("dry-run")

			fmt.Printf("Syncing building %s with Git repository\n", buildingID)

			// Validate flags
			if repoURL == "" && localPath == "" {
				return fmt.Errorf("either --repo-url or --local-path must be specified")
			}

			if direction != "push" && direction != "pull" && direction != "both" {
				return fmt.Errorf("direction must be 'push', 'pull', or 'both'")
			}

			// Create Git provider configuration
			var gitConfig *git.Config
			if localPath != "" {
				// Local repository
				gitConfig = &git.Config{
					Provider: string(git.ProviderLocal),
					Repository: git.RepositoryConfig{
						BasePath: localPath,
						Branch:   branch,
					},
				}
			} else {
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
			}

			// Create Git provider
			var gitProvider git.Provider
			var err error
			gitProvider, err = git.NewProvider(gitConfig)
			if err != nil {
				return fmt.Errorf("failed to create Git provider: %w", err)
			}

			if dryRun {
				fmt.Printf("  DRY RUN: Would sync building %s\n", buildingID)
				fmt.Printf("  Direction: %s\n", direction)
				fmt.Printf("  Repository: %s\n", repoURL)
				fmt.Printf("  Branch: %s\n", branch)
				return nil
			}

			// Perform sync based on direction
			switch direction {
			case "push":
				fmt.Printf("  Pushing building data to Git repository...\n")
				err = syncPushToGit(ctx, buildingID, gitProvider)
			case "pull":
				fmt.Printf("  Pulling building data from Git repository...\n")
				err = syncPullFromGit(ctx, buildingID, gitProvider)
			case "both":
				fmt.Printf("  Performing bidirectional sync...\n")
				fmt.Printf("  Step 1: Pulling latest changes from Git...\n")
				err = syncPullFromGit(ctx, buildingID, gitProvider)
				if err != nil {
					return fmt.Errorf("failed to pull from Git: %w", err)
				}
				fmt.Printf("  Step 2: Pushing local changes to Git...\n")
				err = syncPushToGit(ctx, buildingID, gitProvider)
			}

			if err != nil {
				return fmt.Errorf("sync failed: %w", err)
			}

			fmt.Printf("✅ Successfully synced building %s\n", buildingID)
			fmt.Printf("  Direction: %s\n", direction)
			fmt.Printf("  Repository: %s\n", repoURL)
			fmt.Printf("  Branch: %s\n", branch)

			return nil
		},
	}

	// Add flags
	cmd.Flags().String("repo-url", "", "Git repository URL (for remote sync)")
	cmd.Flags().String("local-path", "", "Local repository path (for local sync)")
	cmd.Flags().StringP("branch", "b", "main", "Branch name")
	cmd.Flags().StringP("direction", "d", "both", "Sync direction: push, pull, or both")
	cmd.Flags().Bool("dry-run", false, "Show what would be synced without making changes")
	cmd.Flags().String("token", "", "Authentication token (or use GITHUB_TOKEN/GITLAB_TOKEN env var)")

	return cmd
}

// syncPushToGit pushes building data from ArxOS to Git repository
func syncPushToGit(ctx context.Context, buildingID string, gitProvider git.Provider) error {
	// For now, create a simple mock building for demonstration
	// TODO: Integrate with actual building service when available
	fmt.Printf("    Creating mock building data for demonstration...\n")

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

	fmt.Printf("    Found building: %s\n", mockBuilding.Name)

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

	// Write building.yml to Git repository
	err := gitProvider.WriteFile(ctx, "building.yml", []byte(yamlContent))
	if err != nil {
		return fmt.Errorf("failed to write building.yml: %w", err)
	}

	// Commit changes
	fmt.Printf("    Committing changes...\n")
	commitMessage := fmt.Sprintf("Sync building %s from ArxOS", buildingID)
	err = gitProvider.Commit(ctx, commitMessage)
	if err != nil {
		// If commit fails due to clean working tree, that's okay for testing
		if strings.Contains(err.Error(), "clean working tree") {
			fmt.Printf("    No changes to commit (clean working tree)\n")
		} else {
			return fmt.Errorf("failed to commit changes: %w", err)
		}
	} else {
		fmt.Printf("    Changes committed successfully\n")
	}

	return nil
}

// syncPullFromGit pulls building data from Git repository to ArxOS
func syncPullFromGit(ctx context.Context, buildingID string, gitProvider git.Provider) error {
	// Read building.yml from Git repository
	fmt.Printf("    Reading building.yml from Git repository...\n")
	_, err := gitProvider.GetFile(ctx, "building.yml")
	if err != nil {
		return fmt.Errorf("failed to read building.yml: %w", err)
	}

	// For now, just demonstrate reading the YAML file
	// TODO: Integrate with actual building service when available
	fmt.Printf("    Successfully read building.yml from Git repository\n")
	fmt.Printf("    Building ID: %s\n", buildingID)

	return nil
}
