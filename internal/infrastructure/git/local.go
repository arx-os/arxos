package git

import (
	"context"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/go-git/go-git/v5"
	"github.com/go-git/go-git/v5/plumbing"
	"github.com/go-git/go-git/v5/plumbing/object"
	"github.com/go-git/go-git/v5/plumbing/transport"
	"github.com/go-git/go-git/v5/plumbing/transport/http"
	"github.com/go-git/go-git/v5/plumbing/transport/ssh"
)

// LocalProvider implements the Provider interface for local Git operations
type LocalProvider struct {
	repo   *git.Repository
	config *Config
	path   string
}

// NewLocalProvider creates a new local Git provider
func NewLocalProvider(config *Config) (*LocalProvider, error) {
	if config == nil {
		return nil, NewGitErrorWithCause("config is required", ErrInvalidConfig)
	}

	if config.Repository.BasePath == "" {
		return nil, NewGitErrorWithCause("base path is required for local provider", ErrInvalidConfig)
	}

	// Ensure the base path exists
	if err := os.MkdirAll(config.Repository.BasePath, 0755); err != nil {
		return nil, NewGitErrorWithCause("failed to create base path", err)
	}

	// Open or initialize repository
	repo, err := git.PlainOpen(config.Repository.BasePath)
	if err != nil {
		if err == git.ErrRepositoryNotExists {
			// Initialize new repository
			repo, err = git.PlainInit(config.Repository.BasePath, false)
			if err != nil {
				return nil, NewGitErrorWithCause("failed to initialize repository", err)
			}
		} else {
			return nil, NewGitErrorWithCause("failed to open repository", err)
		}
	}

	return &LocalProvider{
		repo:   repo,
		config: config,
		path:   config.Repository.BasePath,
	}, nil
}

// Clone clones the repository to the specified destination
func (p *LocalProvider) Clone(ctx context.Context, url string, dest string) error {
	// Create authentication
	auth, err := p.createAuth()
	if err != nil {
		return err
	}

	// Clone repository
	_, err = git.PlainClone(dest, false, &git.CloneOptions{
		URL:      url,
		Auth:     auth,
		Progress: os.Stdout,
	})

	if err != nil {
		return NewGitErrorWithCause("failed to clone repository", err)
	}

	return nil
}

// Pull pulls the latest changes from the remote repository
func (p *LocalProvider) Pull(ctx context.Context) error {
	// Get worktree
	worktree, err := p.repo.Worktree()
	if err != nil {
		return NewGitErrorWithCause("failed to get worktree", err)
	}

	// Create authentication
	auth, err := p.createAuth()
	if err != nil {
		return err
	}

	// Pull changes
	err = worktree.Pull(&git.PullOptions{
		RemoteName: "origin",
		Auth:       auth,
	})

	if err != nil && err != git.NoErrAlreadyUpToDate {
		return NewGitErrorWithCause("failed to pull changes", err)
	}

	return nil
}

// Push pushes changes to the remote repository
func (p *LocalProvider) Push(ctx context.Context) error {
	// Create authentication
	auth, err := p.createAuth()
	if err != nil {
		return err
	}

	// Push changes
	err = p.repo.Push(&git.PushOptions{
		Auth: auth,
	})

	if err != nil {
		return NewGitErrorWithCause("failed to push changes", err)
	}

	return nil
}

// GetFile retrieves a file from the repository
func (p *LocalProvider) GetFile(ctx context.Context, path string) ([]byte, error) {
	// Read file directly from filesystem
	fullPath := filepath.Join(p.path, path)
	content, err := os.ReadFile(fullPath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, NewGitErrorWithCause("file not found", ErrFileNotFound)
		}
		return nil, NewGitErrorWithCause("failed to read file", err)
	}

	return content, nil
}

// WriteFile writes a file to the repository
func (p *LocalProvider) WriteFile(ctx context.Context, path string, data []byte) error {
	// Get worktree
	worktree, err := p.repo.Worktree()
	if err != nil {
		return NewGitErrorWithCause("failed to get worktree", err)
	}

	// Ensure directory exists
	fullPath := filepath.Join(p.path, path)
	dir := filepath.Dir(fullPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return NewGitErrorWithCause("failed to create directory", err)
	}

	// Write file
	if err := os.WriteFile(fullPath, data, 0644); err != nil {
		return NewGitErrorWithCause("failed to write file", err)
	}

	// Add file to Git
	_, err = worktree.Add(path)
	if err != nil {
		return NewGitErrorWithCause("failed to add file to Git", err)
	}

	return nil
}

// ListFiles lists files in the repository with the given prefix
func (p *LocalProvider) ListFiles(ctx context.Context, prefix string) ([]string, error) {
	var files []string

	err := filepath.Walk(filepath.Join(p.path, prefix), func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() {
			// Get relative path
			relPath, err := filepath.Rel(p.path, path)
			if err != nil {
				return err
			}
			files = append(files, relPath)
		}

		return nil
	})

	if err != nil {
		return nil, NewGitErrorWithCause("failed to list files", err)
	}

	return files, nil
}

// DeleteFile deletes a file from the repository
func (p *LocalProvider) DeleteFile(ctx context.Context, path string) error {
	// Get worktree
	worktree, err := p.repo.Worktree()
	if err != nil {
		return NewGitErrorWithCause("failed to get worktree", err)
	}

	// Delete file
	fullPath := filepath.Join(p.path, path)
	if err := os.Remove(fullPath); err != nil {
		if os.IsNotExist(err) {
			return NewGitErrorWithCause("file not found", ErrFileNotFound)
		}
		return NewGitErrorWithCause("failed to delete file", err)
	}

	// Remove from Git
	_, err = worktree.Remove(path)
	if err != nil {
		return NewGitErrorWithCause("failed to remove file from Git", err)
	}

	return nil
}

// Commit creates a commit
func (p *LocalProvider) Commit(ctx context.Context, message string) error {
	// Get worktree
	worktree, err := p.repo.Worktree()
	if err != nil {
		return NewGitErrorWithCause("failed to get worktree", err)
	}

	// Commit changes
	_, err = worktree.Commit(message, &git.CommitOptions{
		Author: &object.Signature{
			Name:  p.config.Auth.Username,
			Email: p.config.Auth.Username + "@arxos.io", // Default email
			When:  time.Now(),
		},
	})

	if err != nil {
		return NewGitErrorWithCause("failed to create commit", err)
	}

	return nil
}

// GetLastCommit gets the last commit information
func (p *LocalProvider) GetLastCommit(ctx context.Context) (*Commit, error) {
	// Get HEAD reference
	ref, err := p.repo.Head()
	if err != nil {
		return nil, NewGitErrorWithCause("failed to get HEAD", err)
	}

	// Get commit
	commit, err := p.repo.CommitObject(ref.Hash())
	if err != nil {
		return nil, NewGitErrorWithCause("failed to get commit", err)
	}

	return &Commit{
		Hash:      commit.Hash.String(),
		Message:   commit.Message,
		Author:    commit.Author.Name,
		Email:     commit.Author.Email,
		Timestamp: commit.Author.When,
	}, nil
}

// CreateBranch creates a new branch
func (p *LocalProvider) CreateBranch(ctx context.Context, name string) error {
	// Get HEAD reference
	headRef, err := p.repo.Head()
	if err != nil {
		return NewGitErrorWithCause("failed to get HEAD", err)
	}

	// Create new branch reference
	branchRef := plumbing.NewBranchReferenceName(name)
	ref := plumbing.NewHashReference(branchRef, headRef.Hash())

	err = p.repo.Storer.SetReference(ref)
	if err != nil {
		return NewGitErrorWithCause("failed to create branch", err)
	}

	return nil
}

// CheckoutBranch checks out a branch
func (p *LocalProvider) CheckoutBranch(ctx context.Context, name string) error {
	// Get worktree
	worktree, err := p.repo.Worktree()
	if err != nil {
		return NewGitErrorWithCause("failed to get worktree", err)
	}

	// Checkout branch
	err = worktree.Checkout(&git.CheckoutOptions{
		Branch: plumbing.NewBranchReferenceName(name),
	})

	if err != nil {
		return NewGitErrorWithCause("failed to checkout branch", err)
	}

	return nil
}

// MergeBranch merges a branch into another branch
func (p *LocalProvider) MergeBranch(ctx context.Context, source, target string) error {
	// Get worktree
	worktree, err := p.repo.Worktree()
	if err != nil {
		return NewGitErrorWithCause("failed to get worktree", err)
	}

	// Checkout target branch
	err = worktree.Checkout(&git.CheckoutOptions{
		Branch: plumbing.NewBranchReferenceName(target),
	})
	if err != nil {
		return NewGitErrorWithCause("failed to checkout target branch", err)
	}

	// Get the source branch reference
	sourceRefName := plumbing.NewBranchReferenceName(source)
	sourceRef, err := p.repo.Reference(sourceRefName, true)
	if err != nil {
		return NewGitErrorWithCause("failed to get source branch reference", err)
	}

	// Perform the merge using the Repository.Merge method
	err = p.repo.Merge(*sourceRef, git.MergeOptions{
		Strategy: git.FastForwardMerge,
	})
	if err != nil {
		return NewGitErrorWithCause("failed to merge branch", err)
	}

	return nil
}

// ListBranches lists all branches in the repository
func (p *LocalProvider) ListBranches(ctx context.Context) ([]string, error) {
	branches, err := p.repo.Branches()
	if err != nil {
		return nil, NewGitErrorWithCause("failed to list branches", err)
	}

	var branchNames []string
	err = branches.ForEach(func(ref *plumbing.Reference) error {
		if ref.Name().IsBranch() {
			branchNames = append(branchNames, ref.Name().Short())
		}
		return nil
	})

	if err != nil {
		return nil, NewGitErrorWithCause("failed to iterate branches", err)
	}

	return branchNames, nil
}

// CreatePullRequest creates a pull request (not supported by local provider)
func (p *LocalProvider) CreatePullRequest(ctx context.Context, req *PullRequestRequest) (*PullRequest, error) {
	return nil, NewGitError("pull request creation not supported by local provider")
}

// CreateIssue creates an issue (not supported by local provider)
func (p *LocalProvider) CreateIssue(ctx context.Context, req *IssueRequest) (*Issue, error) {
	return nil, NewGitError("issue creation not supported by local provider")
}

// TriggerWorkflow triggers a workflow (not supported by local provider)
func (p *LocalProvider) TriggerWorkflow(ctx context.Context, workflowName string) error {
	return NewGitError("workflow triggering not supported by local provider")
}

// GetRepositoryInfo gets repository information
func (p *LocalProvider) GetRepositoryInfo(ctx context.Context) (*RepositoryInfo, error) {
	// Get remote origin
	remote, err := p.repo.Remote("origin")
	if err != nil {
		// No remote configured
		return &RepositoryInfo{
			Name:          filepath.Base(p.path),
			FullName:      filepath.Base(p.path),
			Description:   "Local Git repository",
			URL:           "",
			CloneURL:      "",
			DefaultBranch: "main",
			Private:       true,
			Owner:         "local",
		}, nil
	}

	// Parse remote URL
	urls := remote.Config().URLs
	if len(urls) == 0 {
		return nil, NewGitErrorWithCause("no remote URLs configured", ErrRepositoryNotFound)
	}

	url := urls[0]
	owner, name := parseGitURL(url)

	return &RepositoryInfo{
		Name:          name,
		FullName:      fmt.Sprintf("%s/%s", owner, name),
		Description:   "Local Git repository",
		URL:           url,
		CloneURL:      url,
		DefaultBranch: "main",
		Private:       true,
		Owner:         owner,
	}, nil
}

// Helper functions

func (p *LocalProvider) createAuth() (transport.AuthMethod, error) {
	if p.config.Auth.Token != "" {
		return &http.BasicAuth{
			Username: p.config.Auth.Username,
			Password: p.config.Auth.Token,
		}, nil
	}

	if p.config.Auth.SSHKey != "" {
		auth, err := ssh.NewPublicKeys("git", []byte(p.config.Auth.SSHKey), "")
		if err != nil {
			return nil, NewGitErrorWithCause("failed to create SSH auth", err)
		}
		return auth, nil
	}

	return nil, nil // No authentication
}

func parseGitURL(url string) (owner, name string) {
	// Parse GitHub/GitLab URLs
	// Examples:
	// https://github.com/owner/repo.git
	// git@github.com:owner/repo.git

	if strings.Contains(url, "github.com") {
		parts := strings.Split(url, "/")
		if len(parts) >= 2 {
			owner = parts[len(parts)-2]
			name = strings.TrimSuffix(parts[len(parts)-1], ".git")
		}
	} else if strings.Contains(url, "gitlab.com") {
		parts := strings.Split(url, "/")
		if len(parts) >= 2 {
			owner = parts[len(parts)-2]
			name = strings.TrimSuffix(parts[len(parts)-1], ".git")
		}
	}

	return owner, name
}
