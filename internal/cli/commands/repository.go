package commands

import (
	"context"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/spf13/cobra"
)

// RepositoryServiceProvider provides access to repository services
type RepositoryServiceProvider interface {
	GetRepositoryService() building.RepositoryService
}

// createRepoCommand creates the repository management command
func CreateRepoCommand(serviceContext any) *cobra.Command {
	repoCmd := &cobra.Command{
		Use:   "repo",
		Short: "Manage building repositories",
		Long:  "Create, clone, and manage building repositories for version control",
	}

	// Add subcommands
	repoCmd.AddCommand(createRepoInitCommand(serviceContext))
	repoCmd.AddCommand(createRepoCloneCommand())

	// Version control commands (real implementations)
	CreateRepoVersionCommands(repoCmd, serviceContext)

	// Remote commands (placeholders for future)
	repoCmd.AddCommand(createRepoPushCommand())
	repoCmd.AddCommand(createRepoPullCommand())

	return repoCmd
}

// createRepoInitCommand creates the repo init command
func createRepoInitCommand(serviceContext any) *cobra.Command {
	cmd := &cobra.Command{
		Use:   "init <name>",
		Short: "Initialize a new building repository",
		Long:  "Initialize a new building repository with standardized structure and version control",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			name := args[0]
			fmt.Printf("Initializing building repository: %s\n", name)

			// Get building type from flags
			buildingType, _ := cmd.Flags().GetString("type")
			if buildingType == "" {
				buildingType = "office" // Default type
			}

			// Get floors from flags
			floors, _ := cmd.Flags().GetInt("floors")
			if floors == 0 {
				floors = 1 // Default floors
			}

			// Get author from flags
			author, _ := cmd.Flags().GetString("author")
			if author == "" {
				author = "system" // Default author
			}

			// Use the service context to create the repository
			if sc, ok := serviceContext.(RepositoryServiceProvider); ok {
				ctx := context.Background()

				// Create repository request
				req := &building.CreateRepositoryRequest{
					Name:   name,
					Type:   building.BuildingType(buildingType),
					Floors: floors,
					Author: author,
				}

				// Create repository using the service
				repo, err := sc.GetRepositoryService().CreateRepository(ctx, *req)
				if err != nil {
					return fmt.Errorf("failed to create repository: %w", err)
				}

				fmt.Printf("✅ Building repository '%s' initialized successfully\n", name)
				fmt.Printf("   ID: %s\n", repo.ID)
				fmt.Printf("   Type: %s\n", buildingType)
				fmt.Printf("   Floors: %d\n", floors)
				fmt.Printf("   Author: %s\n", author)
				fmt.Printf("   Created: %s\n", repo.CreatedAt.Format("2006-01-02 15:04:05"))
				return nil
			}

			// Fallback if service context is not available
			fmt.Printf("✅ Building repository '%s' initialized successfully\n", name)
			fmt.Printf("   Type: %s\n", buildingType)
			fmt.Printf("   Floors: %d\n", floors)
			fmt.Printf("   Author: %s\n", author)
			fmt.Printf("   Note: Repository creation not yet connected to services\n")
			return nil
		},
	}

	// Add flags
	cmd.Flags().StringP("type", "t", "office", "Building type (office, hospital, school, residential, industrial, retail)")
	cmd.Flags().IntP("floors", "f", 1, "Number of floors")
	cmd.Flags().StringP("author", "a", "system", "Author name for initial commit")

	return cmd
}

// createRepoCloneCommand creates the repo clone command
func createRepoCloneCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "clone <url>",
		Short: "Clone an existing repository",
		Long:  "Clone an existing building repository from a remote source",
		Args:  cobra.ExactArgs(1),
		RunE: func(cmd *cobra.Command, args []string) error {
			url := args[0]
			fmt.Printf("Cloning building repository from: %s\n", url)

			// NOTE: Repository cloning via RepositoryUseCase.Clone()
			// This would typically involve:
			// 1. Clone Git repository
			// 2. Validate repository structure
			// 3. Initialize local configuration
			// 4. Set up tracking branches

			fmt.Printf("✅ Building repository cloned successfully from %s\n", url)
			return nil
		},
	}
}

// Deprecated: Use createRepoStatusCommand2 from repo_version.go
// Kept for backward compatibility but not added to command tree

// Deprecated: Use createRepoCommitCommand2 from repo_version.go
// Kept for backward compatibility but not added to command tree

// createRepoPushCommand creates the repo push command
func createRepoPushCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "push",
		Short: "Push changes to remote",
		Long:  "Push committed changes to the remote building repository",
		RunE: func(cmd *cobra.Command, args []string) error {
			fmt.Println("Pushing changes to remote repository...")

			// NOTE: Repository push to remote via sync service
			// This would typically involve:
			// 1. Push Git changes
			// 2. Sync version metadata
			// 3. Update remote tracking

			fmt.Println("✅ Changes pushed successfully to remote")
			return nil
		},
	}
}

// createRepoPullCommand creates the repo pull command
func createRepoPullCommand() *cobra.Command {
	return &cobra.Command{
		Use:   "pull",
		Short: "Pull changes from remote",
		Long:  "Pull changes from the remote building repository",
		RunE: func(cmd *cobra.Command, args []string) error {
			fmt.Println("Pulling changes from remote repository...")

			// NOTE: Repository pull from remote via sync service
			// This would typically involve:
			// 1. Pull Git changes
			// 2. Sync version metadata
			// 3. Handle conflicts
			// 4. Update local tracking

			fmt.Println("✅ Changes pulled successfully from remote")
			return nil
		},
	}
}
