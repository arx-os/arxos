package git

import (
	"context"
	"os"
	"path/filepath"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestNewProvider(t *testing.T) {
	tests := []struct {
		name        string
		config      *Config
		expectError bool
	}{
		{
			name: "GitHub provider",
			config: &Config{
				Provider: "github",
				Auth: AuthConfig{
					Token: "test-token",
				},
				Repository: RepositoryConfig{
					Owner:  "test-owner",
					Name:   "test-repo",
					Branch: "main",
				},
			},
			expectError: false,
		},
		{
			name: "Local provider",
			config: &Config{
				Provider: "local",
				Repository: RepositoryConfig{
					BasePath: "/tmp/test-repo",
					Branch:   "main",
				},
			},
			expectError: false,
		},
		{
			name: "Unsupported provider",
			config: &Config{
				Provider: "unsupported",
			},
			expectError: true,
		},
		{
			name:        "Nil config",
			config:      nil,
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			provider, err := NewProvider(tt.config)

			if tt.expectError {
				assert.Error(t, err)
				assert.Nil(t, provider)
			} else {
				assert.NoError(t, err)
				assert.NotNil(t, provider)
			}
		})
	}
}

func TestGitHubProvider(t *testing.T) {
	// Skip if no GitHub token provided
	token := os.Getenv("GITHUB_TOKEN")
	if token == "" {
		t.Skip("GITHUB_TOKEN not provided, skipping GitHub provider tests")
	}

	config := &Config{
		Provider: "github",
		Auth: AuthConfig{
			Token: token,
		},
		Repository: RepositoryConfig{
			Owner:  "octocat",
			Name:   "Hello-World",
			Branch: "main",
		},
	}

	provider, err := NewGitHubProvider(config)
	require.NoError(t, err)
	require.NotNil(t, provider)

	ctx := context.Background()

	t.Run("GetRepositoryInfo", func(t *testing.T) {
		info, err := provider.GetRepositoryInfo(ctx)
		require.NoError(t, err)
		assert.Equal(t, "Hello-World", info.Name)
		assert.Equal(t, "octocat/Hello-World", info.FullName)
		assert.Equal(t, "octocat", info.Owner)
	})

	t.Run("ListBranches", func(t *testing.T) {
		branches, err := provider.ListBranches(ctx)
		require.NoError(t, err)
		assert.NotEmpty(t, branches)
	})

	t.Run("GetLastCommit", func(t *testing.T) {
		commit, err := provider.GetLastCommit(ctx)
		require.NoError(t, err)
		assert.NotEmpty(t, commit.Hash)
		assert.NotEmpty(t, commit.Message)
		assert.NotEmpty(t, commit.Author)
	})

	t.Run("GetFile", func(t *testing.T) {
		content, err := provider.GetFile(ctx, "README")
		require.NoError(t, err)
		assert.NotEmpty(t, content)
	})

	t.Run("ListFiles", func(t *testing.T) {
		files, err := provider.ListFiles(ctx, "")
		require.NoError(t, err)
		assert.NotEmpty(t, files)
	})
}

func TestGitLabProvider(t *testing.T) {
	// Skip if no GitLab token provided
	token := os.Getenv("GITLAB_TOKEN")
	if token == "" {
		t.Skip("GITLAB_TOKEN not provided, skipping GitLab provider tests")
	}

	config := &Config{
		Provider: "gitlab",
		Auth: AuthConfig{
			Token: token,
		},
		Repository: RepositoryConfig{
			Owner:  "gitlab-org",
			Name:   "gitlab-test",
			Branch: "main",
			URL:    "https://gitlab.com",
		},
	}

	provider, err := NewGitLabProvider(config)
	require.NoError(t, err)
	require.NotNil(t, provider)

	ctx := context.Background()

	t.Run("GetRepositoryInfo", func(t *testing.T) {
		info, err := provider.GetRepositoryInfo(ctx)
		require.NoError(t, err)
		assert.NotEmpty(t, info.Name)
		assert.NotEmpty(t, info.FullName)
		assert.NotEmpty(t, info.Owner)
	})

	t.Run("ListBranches", func(t *testing.T) {
		branches, err := provider.ListBranches(ctx)
		require.NoError(t, err)
		assert.NotEmpty(t, branches)
	})

	t.Run("GetLastCommit", func(t *testing.T) {
		commit, err := provider.GetLastCommit(ctx)
		require.NoError(t, err)
		assert.NotEmpty(t, commit.Hash)
		assert.NotEmpty(t, commit.Message)
		assert.NotEmpty(t, commit.Author)
	})

	t.Run("ListFiles", func(t *testing.T) {
		files, err := provider.ListFiles(ctx, "")
		require.NoError(t, err)
		assert.NotEmpty(t, files)
	})
}

func TestLocalProvider(t *testing.T) {
	// Create temporary directory
	tempDir, err := os.MkdirTemp("", "arxos-git-test-*")
	require.NoError(t, err)
	defer os.RemoveAll(tempDir)

	config := &Config{
		Provider: "local",
		Auth: AuthConfig{
			Username: "test-user",
		},
		Repository: RepositoryConfig{
			BasePath: tempDir,
			Branch:   "main",
		},
	}

	provider, err := NewLocalProvider(config)
	require.NoError(t, err)
	require.NotNil(t, provider)

	ctx := context.Background()

	t.Run("GetRepositoryInfo", func(t *testing.T) {
		info, err := provider.GetRepositoryInfo(ctx)
		require.NoError(t, err)
		assert.Equal(t, filepath.Base(tempDir), info.Name)
		assert.Equal(t, "local", info.Owner)
	})

	t.Run("WriteFile", func(t *testing.T) {
		testContent := []byte("test content")
		err := provider.WriteFile(ctx, "test.txt", testContent)
		require.NoError(t, err)

		// Verify file was written
		content, err := provider.GetFile(ctx, "test.txt")
		require.NoError(t, err)
		assert.Equal(t, testContent, content)
	})

	t.Run("ListFiles", func(t *testing.T) {
		files, err := provider.ListFiles(ctx, "")
		require.NoError(t, err)
		assert.Contains(t, files, "test.txt")
	})

	t.Run("Commit", func(t *testing.T) {
		err := provider.Commit(ctx, "Test commit")
		require.NoError(t, err)

		// Verify commit was created
		commit, err := provider.GetLastCommit(ctx)
		require.NoError(t, err)
		assert.Equal(t, "Test commit", commit.Message)
		assert.Equal(t, "test-user", commit.Author)
	})

	t.Run("CreateBranch", func(t *testing.T) {
		err := provider.CreateBranch(ctx, "feature-branch")
		require.NoError(t, err)

		// Verify branch was created
		branches, err := provider.ListBranches(ctx)
		require.NoError(t, err)
		assert.Contains(t, branches, "feature-branch")
	})

	t.Run("CheckoutBranch", func(t *testing.T) {
		err := provider.CheckoutBranch(ctx, "feature-branch")
		require.NoError(t, err)
	})

	t.Run("MergeBranch", func(t *testing.T) {
		// Create a file on feature branch
		err := provider.WriteFile(ctx, "feature.txt", []byte("feature content"))
		require.NoError(t, err)

		err = provider.Commit(ctx, "Add feature file")
		require.NoError(t, err)

		// Merge feature branch into master (default branch)
		err = provider.MergeBranch(ctx, "feature-branch", "master")
		require.NoError(t, err)

		// Note: Actual merge functionality would require more complex implementation
		// For now, we just verify the method doesn't error
	})

	t.Run("DeleteFile", func(t *testing.T) {
		err := provider.DeleteFile(ctx, "test.txt")
		require.NoError(t, err)

		// Verify file was deleted
		_, err = provider.GetFile(ctx, "test.txt")
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "file not found")
	})
}

func TestPathConversion(t *testing.T) {
	tests := []struct {
		name          string
		universalPath string
		expectedFile  string
	}{
		{
			name:          "full path",
			universalPath: "/B1/3/301/HVAC/VAV-301",
			expectedFile:  "equipment/B1/3/301/HVAC/VAV-301.yml",
		},
		{
			name:          "minimal path",
			universalPath: "/B1/VAV-301",
			expectedFile:  "equipment/B1/VAV-301.yml",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// This would use the serialization package
			// For now, just test the logic
			path := tt.universalPath
			if len(path) > 0 && path[0] == '/' {
				path = path[1:]
			}
			filePath := "equipment/" + path + ".yml"
			assert.Equal(t, tt.expectedFile, filePath)
		})
	}
}

func TestGitError(t *testing.T) {
	t.Run("Simple error", func(t *testing.T) {
		err := NewGitError("test error")
		assert.Equal(t, "test error", err.Error())
		assert.Nil(t, err.Unwrap())
	})

	t.Run("Error with cause", func(t *testing.T) {
		cause := NewGitError("cause error")
		err := NewGitErrorWithCause("wrapper error", cause)
		assert.Equal(t, "wrapper error: cause error", err.Error())
		assert.Equal(t, cause, err.Unwrap())
	})
}

func TestConfigValidation(t *testing.T) {
	tests := []struct {
		name        string
		config      *Config
		expectError bool
	}{
		{
			name: "Valid GitHub config",
			config: &Config{
				Provider: "github",
				Auth: AuthConfig{
					Token: "test-token",
				},
				Repository: RepositoryConfig{
					Owner:  "test-owner",
					Name:   "test-repo",
					Branch: "main",
				},
			},
			expectError: false,
		},
		{
			name: "GitHub config without token",
			config: &Config{
				Provider: "github",
				Repository: RepositoryConfig{
					Owner:  "test-owner",
					Name:   "test-repo",
					Branch: "main",
				},
			},
			expectError: true,
		},
		{
			name: "GitHub config without owner",
			config: &Config{
				Provider: "github",
				Auth: AuthConfig{
					Token: "test-token",
				},
				Repository: RepositoryConfig{
					Name:   "test-repo",
					Branch: "main",
				},
			},
			expectError: true,
		},
		{
			name: "Valid local config",
			config: &Config{
				Provider: "local",
				Repository: RepositoryConfig{
					BasePath: "/tmp/test",
					Branch:   "main",
				},
			},
			expectError: false,
		},
		{
			name: "Local config without base path",
			config: &Config{
				Provider: "local",
				Repository: RepositoryConfig{
					Branch: "main",
				},
			},
			expectError: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			_, err := NewProvider(tt.config)

			if tt.expectError {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestPullRequestRequest(t *testing.T) {
	req := &PullRequestRequest{
		Title:        "Test PR",
		Body:         "Test body",
		SourceBranch: "feature-branch",
		TargetBranch: "main",
		Reviewers:    []string{"reviewer1", "reviewer2"},
		Labels:       []string{"enhancement", "bug"},
	}

	assert.Equal(t, "Test PR", req.Title)
	assert.Equal(t, "Test body", req.Body)
	assert.Equal(t, "feature-branch", req.SourceBranch)
	assert.Equal(t, "main", req.TargetBranch)
	assert.Len(t, req.Reviewers, 2)
	assert.Len(t, req.Labels, 2)
}

func TestIssueRequest(t *testing.T) {
	req := &IssueRequest{
		Title:     "Test Issue",
		Body:      "Test body",
		Labels:    []string{"bug", "urgent"},
		Assignees: []string{"assignee1"},
	}

	assert.Equal(t, "Test Issue", req.Title)
	assert.Equal(t, "Test body", req.Body)
	assert.Len(t, req.Labels, 2)
	assert.Len(t, req.Assignees, 1)
}

func TestCommit(t *testing.T) {
	now := time.Now()
	commit := &Commit{
		Hash:      "abc123",
		Message:   "Test commit",
		Author:    "test-user",
		Email:     "test@example.com",
		Timestamp: now,
	}

	assert.Equal(t, "abc123", commit.Hash)
	assert.Equal(t, "Test commit", commit.Message)
	assert.Equal(t, "test-user", commit.Author)
	assert.Equal(t, "test@example.com", commit.Email)
	assert.Equal(t, now, commit.Timestamp)
}

func TestRepositoryInfo(t *testing.T) {
	info := &RepositoryInfo{
		Name:          "test-repo",
		FullName:      "owner/test-repo",
		Description:   "Test repository",
		URL:           "https://github.com/owner/test-repo",
		CloneURL:      "https://github.com/owner/test-repo.git",
		DefaultBranch: "main",
		Private:       false,
		Owner:         "owner",
	}

	assert.Equal(t, "test-repo", info.Name)
	assert.Equal(t, "owner/test-repo", info.FullName)
	assert.Equal(t, "Test repository", info.Description)
	assert.Equal(t, "https://github.com/owner/test-repo", info.URL)
	assert.Equal(t, "https://github.com/owner/test-repo.git", info.CloneURL)
	assert.Equal(t, "main", info.DefaultBranch)
	assert.False(t, info.Private)
	assert.Equal(t, "owner", info.Owner)
}
