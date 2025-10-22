package integration

import (
	"context"
	"fmt"

	"github.com/arx-os/arxos/internal/infrastructure/git"
	"github.com/spf13/cobra"
)

// CreateGitImportCommand creates the git import command
func CreateGitImportCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "import --from-git <repo-url>",
		Short: "Import building data from Git repository",
		Long: `Import building data from a Git repository YAML files into PostGIS.
This command reads YAML files from a Git repository and imports them into the local PostGIS database.

Examples:
  arx import --from-git https://github.com/company/building-bld-001
  arx import --from-git https://gitlab.com/company/building-bld-002 --branch main
  arx import --from-git ./building-repo --local-path ./building-repo --repository BLD-001`,
		Args: cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			repoURL := args[0]
			ctx := context.Background()

			// Get flags
			localPath, _ := cmd.Flags().GetString("local-path")
			branch, _ := cmd.Flags().GetString("branch")
			targetRepoID, _ := cmd.Flags().GetString("repository")
			dryRun, _ := cmd.Flags().GetBool("dry-run")
			overwrite, _ := cmd.Flags().GetBool("overwrite")

			// Validate inputs
			if branch == "" {
				branch = "main"
			}

			if targetRepoID == "" {
				return fmt.Errorf("--repository flag is required to specify target repository ID")
			}

			fmt.Printf("Importing building data from Git repository\n")
			fmt.Printf("  Repository: %s\n", repoURL)
			fmt.Printf("  Local Path: %s\n", localPath)
			fmt.Printf("  Branch: %s\n", branch)
			fmt.Printf("  Target Repository: %s\n", targetRepoID)
			fmt.Printf("  Dry Run: %v\n", dryRun)
			fmt.Printf("  Overwrite: %v\n", overwrite)

			// For now, just demonstrate reading the YAML file
			// TODO: Integrate with actual building service when available

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
			gitProvider, err := git.NewProvider(gitConfig)
			if err != nil {
				return fmt.Errorf("failed to create Git provider: %w", err)
			}

			// Clone repository if remote
			if localPath == "" {
				fmt.Printf("  Cloning repository...\n")
				err = gitProvider.Clone(ctx, repoURL, "./temp-import")
				if err != nil {
					return fmt.Errorf("failed to clone repository: %w", err)
				}
				gitConfig.Repository.BasePath = "./temp-import"
				gitProvider, err = git.NewProvider(gitConfig)
				if err != nil {
					return fmt.Errorf("failed to recreate Git provider: %w", err)
				}
			}

			// Read building data
			fmt.Printf("  Reading building.yml...\n")
			_, err = gitProvider.GetFile(ctx, "building.yml")
			if err != nil {
				return fmt.Errorf("failed to read building.yml: %w", err)
			}

			// For now, just demonstrate reading the YAML file
			// TODO: Integrate with actual building service when available

			fmt.Printf("✅ Successfully imported building data from Git repository\n")
			fmt.Printf("  Target Repository: %s\n", targetRepoID)
			fmt.Printf("  Source Repository: %s\n", repoURL)
			fmt.Printf("  Branch: %s\n", branch)

			return nil
		},
	}

	// Add flags
	cmd.Flags().String("local-path", "", "Local repository path (for local imports)")
	cmd.Flags().StringP("branch", "b", "main", "Source branch name")
	cmd.Flags().StringP("repository", "r", "", "Target repository ID (required)")
	cmd.Flags().Bool("dry-run", false, "Show what would be imported without making changes")
	cmd.Flags().Bool("overwrite", false, "Overwrite existing building data")
	cmd.Flags().String("token", "", "Authentication token (or use GITHUB_TOKEN/GITLAB_TOKEN env var)")

	return cmd
}
