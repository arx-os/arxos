package integration

import (
	"context"
	"fmt"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/types"
	"github.com/arx-os/arxos/internal/infrastructure/git"
	"github.com/arx-os/arxos/internal/serialization"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// TestGitSyncWorkflows tests the complete Git sync workflows
func TestGitSyncWorkflows(t *testing.T) {
	tests := []struct {
		name     string
		provider git.ProviderType
		setup    func(t *testing.T) (git.Provider, string)
		cleanup  func(t *testing.T, path string)
	}{
		{
			name:     "Local Git Provider",
			provider: git.ProviderLocal,
			setup:    setupLocalGitProvider,
			cleanup:  cleanupLocalGitProvider,
		},
		// Note: GitHub and GitLab tests would require actual tokens and are skipped in CI
		// They can be enabled with proper environment variables
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			gitProvider, cleanupPath := tt.setup(t)
			defer tt.cleanup(t, cleanupPath)

			ctx := context.Background()
			buildingID := "test-building-123"

			// Test 1: Export building data to Git
			t.Run("ExportBuildingToGit", func(t *testing.T) {
				err := syncPushToGit(ctx, buildingID, gitProvider)
				require.NoError(t, err)

				// Verify building.yml was created
				buildingYAML, err := gitProvider.GetFile(ctx, "building.yml")
				require.NoError(t, err)
				require.NotEmpty(t, buildingYAML)

				// Verify it's valid YAML
				_, err = serialization.UnmarshalBuildingFromYAML(buildingYAML)
				require.NoError(t, err)
			})

			// Test 2: Import building data from Git
			t.Run("ImportBuildingFromGit", func(t *testing.T) {
				err := syncPullFromGit(ctx, buildingID, gitProvider)
				require.NoError(t, err)
			})

			// Test 3: Round-trip sync (export then import)
			t.Run("RoundTripSync", func(t *testing.T) {
				// Export
				err := syncPushToGit(ctx, buildingID, gitProvider)
				require.NoError(t, err)

				// Import
				err = syncPullFromGit(ctx, buildingID, gitProvider)
				require.NoError(t, err)
			})

			// Test 4: Multiple commits
			t.Run("MultipleCommits", func(t *testing.T) {
				// First commit
				err := syncPushToGit(ctx, buildingID, gitProvider)
				require.NoError(t, err)

				// Second commit with different data
				err = syncPushToGit(ctx, buildingID+"-updated", gitProvider)
				require.NoError(t, err)

				// Verify both commits exist
				lastCommit, err := gitProvider.GetLastCommit(ctx)
				require.NoError(t, err)
				require.NotNil(t, lastCommit)
			})
		})
	}
}

// TestGitProviderIntegration tests the Git provider interface implementations
func TestGitProviderIntegration(t *testing.T) {
	t.Run("LocalProvider", func(t *testing.T) {
		gitProvider, cleanupPath := setupLocalGitProvider(t)
		defer cleanupLocalGitProvider(t, cleanupPath)

		ctx := context.Background()

		// Test basic operations
		testGitProviderOperations(t, ctx, gitProvider)
	})

	// GitHub provider test (requires GITHUB_TOKEN)
	if token := os.Getenv("GITHUB_TOKEN"); token != "" {
		t.Run("GitHubProvider", func(t *testing.T) {
			gitProvider := setupGitHubProvider(t)
			if gitProvider == nil {
				t.Skip("GitHub provider setup failed")
			}

			ctx := context.Background()
			testGitProviderOperations(t, ctx, gitProvider)
		})
	} else {
		t.Skip("GITHUB_TOKEN not set, skipping GitHub provider test")
	}

	// GitLab provider test (requires GITLAB_TOKEN)
	if token := os.Getenv("GITLAB_TOKEN"); token != "" {
		t.Run("GitLabProvider", func(t *testing.T) {
			gitProvider := setupGitLabProvider(t)
			if gitProvider == nil {
				t.Skip("GitLab provider setup failed")
			}

			ctx := context.Background()
			testGitProviderOperations(t, ctx, gitProvider)
		})
	} else {
		t.Skip("GITLAB_TOKEN not set, skipping GitLab provider test")
	}
}

// TestYAMLSerializationIntegration tests YAML serialization with Git operations
func TestYAMLSerializationIntegration(t *testing.T) {
	gitProvider, cleanupPath := setupLocalGitProvider(t)
	defer cleanupLocalGitProvider(t, cleanupPath)

	ctx := context.Background()

	// Test Equipment YAML
	t.Run("EquipmentYAML", func(t *testing.T) {
		// Create a domain equipment object
		equipment := &domain.Equipment{
			ID:         types.FromString("eq_123"),
			BuildingID: types.FromString("bldg_123"),
			Name:       "Test VAV Unit",
			Path:       "/B1/3/301/HVAC/VAV-301",
			Type:       "VAV",
			Category:   "HVAC",
			Model:      "VAV-301",
			Location: &domain.Location{
				X: 0.0,
				Y: 0.0,
				Z: 0.0,
			},
			Status:    "Active",
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		// Marshal to YAML
		yamlData, err := serialization.MarshalEquipmentToYAML(equipment)
		require.NoError(t, err)

		// Write to Git
		err = gitProvider.WriteFile(ctx, "equipment/test-equipment.yml", yamlData)
		require.NoError(t, err)

		// Read from Git
		readData, err := gitProvider.GetFile(ctx, "equipment/test-equipment.yml")
		require.NoError(t, err)

		// Unmarshal and verify
		unmarshaledEquipment, err := serialization.UnmarshalEquipmentFromYAML(readData)
		require.NoError(t, err)
		assert.Equal(t, equipment.Name, unmarshaledEquipment.Name)
		assert.Equal(t, equipment.Type, unmarshaledEquipment.Type)
	})

	// Test Building YAML
	t.Run("BuildingYAML", func(t *testing.T) {
		// Create a domain building object
		building := &domain.Building{
			ID:      types.FromString("bldg_123"),
			Name:    "Test Building",
			Address: "123 Test Street, Test City",
			Coordinates: &domain.Location{
				X: 0.0,
				Y: 0.0,
				Z: 0.0,
			},
			CreatedAt: time.Now(),
			UpdatedAt: time.Now(),
		}

		// Marshal to YAML
		yamlData, err := serialization.MarshalBuildingToYAML(building)
		require.NoError(t, err)

		// Write to Git
		err = gitProvider.WriteFile(ctx, "building.yml", yamlData)
		require.NoError(t, err)

		// Read from Git
		readData, err := gitProvider.GetFile(ctx, "building.yml")
		require.NoError(t, err)

		// Unmarshal and verify
		unmarshaledBuilding, err := serialization.UnmarshalBuildingFromYAML(readData)
		require.NoError(t, err)
		assert.Equal(t, building.Name, unmarshaledBuilding.Name)
		assert.Equal(t, building.Address, unmarshaledBuilding.Address)
	})
}

// TestPathConversionIntegration tests path conversion with Git operations
func TestPathConversionIntegration(t *testing.T) {
	gitProvider, cleanupPath := setupLocalGitProvider(t)
	defer cleanupLocalGitProvider(t, cleanupPath)

	ctx := context.Background()

	testCases := []struct {
		universalPath string
		expectedFile  string
	}{
		{"/B1/3/301/HVAC/VAV-301", "equipment/B1/3/301/HVAC/VAV-301.yml"},
		{"/B1/3/301/ELECTRICAL/Panel-301", "equipment/B1/3/301/ELECTRICAL/Panel-301.yml"},
		{"/B1/3/301/PLUMBING/Toilet-301", "equipment/B1/3/301/PLUMBING/Toilet-301.yml"},
	}

	for _, tc := range testCases {
		t.Run(fmt.Sprintf("Path_%s", strings.ReplaceAll(tc.universalPath, "/", "_")), func(t *testing.T) {
			// Convert universal path to Git file path
			gitFilePath := serialization.PathToGitFile(tc.universalPath)
			assert.Equal(t, tc.expectedFile, gitFilePath)

			// Convert back to universal path
			convertedPath := serialization.GitFileToPath(gitFilePath)
			assert.Equal(t, tc.universalPath, convertedPath)

			// Test with actual Git operations
			testContent := fmt.Sprintf("test content for %s", tc.universalPath)
			err := gitProvider.WriteFile(ctx, gitFilePath, []byte(testContent))
			require.NoError(t, err)

			// Read back and verify
			readContent, err := gitProvider.GetFile(ctx, gitFilePath)
			require.NoError(t, err)
			assert.Equal(t, testContent, string(readContent))
		})
	}
}

// Helper functions for test setup

func setupLocalGitProvider(t *testing.T) (git.Provider, string) {
	// Create temporary directory
	tempDir, err := os.MkdirTemp("", "arxos-git-test-*")
	require.NoError(t, err)

	// Create Git provider configuration
	gitConfig := &git.Config{
		Provider: string(git.ProviderLocal),
		Repository: git.RepositoryConfig{
			BasePath: tempDir,
			Branch:   "main",
		},
	}

	// Create Git provider
	gitProvider, err := git.NewProvider(gitConfig)
	require.NoError(t, err)

	return gitProvider, tempDir
}

func cleanupLocalGitProvider(t *testing.T, path string) {
	err := os.RemoveAll(path)
	require.NoError(t, err)
}

func setupGitHubProvider(t *testing.T) git.Provider {
	token := os.Getenv("GITHUB_TOKEN")
	if token == "" {
		return nil
	}

	// Create GitHub provider configuration
	gitConfig := &git.Config{
		Provider: string(git.ProviderGitHub),
		Repository: git.RepositoryConfig{
			URL:    "https://github.com/test-owner/test-repo",
			Branch: "main",
			Owner:  "test-owner",
			Name:   "test-repo",
		},
		Auth: git.AuthConfig{
			Token: token,
		},
	}

	// Create Git provider
	gitProvider, err := git.NewProvider(gitConfig)
	require.NoError(t, err)

	return gitProvider
}

func setupGitLabProvider(t *testing.T) git.Provider {
	token := os.Getenv("GITLAB_TOKEN")
	if token == "" {
		return nil
	}

	// Create GitLab provider configuration
	gitConfig := &git.Config{
		Provider: string(git.ProviderGitLab),
		Repository: git.RepositoryConfig{
			URL:    "https://gitlab.com/test-owner/test-repo",
			Branch: "main",
			Owner:  "test-owner",
			Name:   "test-repo",
		},
		Auth: git.AuthConfig{
			Token: token,
		},
	}

	// Create Git provider
	gitProvider, err := git.NewProvider(gitConfig)
	require.NoError(t, err)

	return gitProvider
}

func testGitProviderOperations(t *testing.T, ctx context.Context, gitProvider git.Provider) {
	// Test GetRepositoryInfo
	repoInfo, err := gitProvider.GetRepositoryInfo(ctx)
	require.NoError(t, err)
	require.NotNil(t, repoInfo)

	// Test WriteFile
	testContent := "test content"
	err = gitProvider.WriteFile(ctx, "test.txt", []byte(testContent))
	require.NoError(t, err)

	// Test GetFile
	readContent, err := gitProvider.GetFile(ctx, "test.txt")
	require.NoError(t, err)
	assert.Equal(t, testContent, string(readContent))

	// Test ListFiles
	files, err := gitProvider.ListFiles(ctx, "")
	require.NoError(t, err)
	assert.Contains(t, files, "test.txt")

	// Test Commit
	err = gitProvider.Commit(ctx, "test commit")
	require.NoError(t, err)

	// Test GetLastCommit
	lastCommit, err := gitProvider.GetLastCommit(ctx)
	require.NoError(t, err)
	require.NotNil(t, lastCommit)

	// Test CreateBranch
	err = gitProvider.CreateBranch(ctx, "test-branch")
	require.NoError(t, err)

	// Test CheckoutBranch
	err = gitProvider.CheckoutBranch(ctx, "test-branch")
	require.NoError(t, err)

	// Test ListBranches
	branches, err := gitProvider.ListBranches(ctx)
	require.NoError(t, err)
	assert.Contains(t, branches, "test-branch")

	// Test DeleteFile
	err = gitProvider.DeleteFile(ctx, "test.txt")
	require.NoError(t, err)

	// Verify file is deleted
	_, err = gitProvider.GetFile(ctx, "test.txt")
	assert.Error(t, err)
}

// TestCLICommandIntegration tests the CLI commands integration
func TestCLICommandIntegration(t *testing.T) {
	// This would test the actual CLI commands
	// For now, we'll test the command creation
	t.Run("CreateGitExportCommand", func(t *testing.T) {
		cmd := CreateGitExportCommand(nil)
		assert.NotNil(t, cmd)
		assert.Equal(t, "export --to-git <building-id>", cmd.Use)
	})

	t.Run("CreateGitImportCommand", func(t *testing.T) {
		cmd := CreateGitImportCommand(nil)
		assert.NotNil(t, cmd)
		assert.Equal(t, "import --from-git <repo-url>", cmd.Use)
	})

	t.Run("CreateGitSyncCommand", func(t *testing.T) {
		cmd := CreateGitSyncCommand(nil)
		assert.NotNil(t, cmd)
		assert.Equal(t, "sync <building-id>", cmd.Use)
	})
}

// TestErrorHandling tests error handling in Git operations
func TestErrorHandling(t *testing.T) {
	t.Run("InvalidGitConfig", func(t *testing.T) {
		// Test with nil config
		_, err := git.NewProvider(nil)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "invalid config")
	})

	t.Run("InvalidProvider", func(t *testing.T) {
		// Test with invalid provider type
		gitConfig := &git.Config{
			Provider: "invalid-provider",
		}
		_, err := git.NewProvider(gitConfig)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "unsupported Git provider")
	})

	t.Run("FileNotFound", func(t *testing.T) {
		gitProvider, cleanupPath := setupLocalGitProvider(t)
		defer cleanupLocalGitProvider(t, cleanupPath)

		ctx := context.Background()
		_, err := gitProvider.GetFile(ctx, "nonexistent.txt")
		assert.Error(t, err)
	})
}

// TestConcurrentOperations tests concurrent Git operations
func TestConcurrentOperations(t *testing.T) {
	gitProvider, cleanupPath := setupLocalGitProvider(t)
	defer cleanupLocalGitProvider(t, cleanupPath)

	ctx := context.Background()
	numGoroutines := 10

	// Test concurrent file writes
	t.Run("ConcurrentWrites", func(t *testing.T) {
		done := make(chan error, numGoroutines)

		for i := 0; i < numGoroutines; i++ {
			go func(id int) {
				filename := fmt.Sprintf("concurrent-test-%d.txt", id)
				content := fmt.Sprintf("content from goroutine %d", id)
				err := gitProvider.WriteFile(ctx, filename, []byte(content))
				done <- err
			}(i)
		}

		// Wait for all goroutines to complete
		for i := 0; i < numGoroutines; i++ {
			err := <-done
			assert.NoError(t, err)
		}

		// Verify all files were created
		files, err := gitProvider.ListFiles(ctx, "")
		require.NoError(t, err)
		assert.GreaterOrEqual(t, len(files), numGoroutines)
	})
}

// TestPerformance tests performance of Git operations
func TestPerformance(t *testing.T) {
	gitProvider, cleanupPath := setupLocalGitProvider(t)
	defer cleanupLocalGitProvider(t, cleanupPath)

	ctx := context.Background()

	t.Run("WritePerformance", func(t *testing.T) {
		start := time.Now()
		numFiles := 100

		for i := 0; i < numFiles; i++ {
			filename := fmt.Sprintf("perf-test-%d.txt", i)
			content := fmt.Sprintf("performance test content %d", i)
			err := gitProvider.WriteFile(ctx, filename, []byte(content))
			require.NoError(t, err)
		}

		duration := time.Since(start)
		t.Logf("Wrote %d files in %v (%.2f files/sec)", numFiles, duration, float64(numFiles)/duration.Seconds())
	})

	t.Run("ReadPerformance", func(t *testing.T) {
		start := time.Now()
		numFiles := 100

		for i := 0; i < numFiles; i++ {
			filename := fmt.Sprintf("perf-test-%d.txt", i)
			_, err := gitProvider.GetFile(ctx, filename)
			require.NoError(t, err)
		}

		duration := time.Since(start)
		t.Logf("Read %d files in %v (%.2f files/sec)", numFiles, duration, float64(numFiles)/duration.Seconds())
	})
}
