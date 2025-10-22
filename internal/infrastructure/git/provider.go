package git

import (
	"context"
	"time"
)

// Provider defines the interface for Git operations
// This abstraction allows switching between GitHub, GitLab, local Git, etc.
type Provider interface {
	// Repository operations
	Clone(ctx context.Context, url string, dest string) error
	Pull(ctx context.Context) error
	Push(ctx context.Context) error

	// File operations
	GetFile(ctx context.Context, path string) ([]byte, error)
	WriteFile(ctx context.Context, path string, data []byte) error
	ListFiles(ctx context.Context, prefix string) ([]string, error)
	DeleteFile(ctx context.Context, path string) error

	// Commit operations
	Commit(ctx context.Context, message string) error
	GetLastCommit(ctx context.Context) (*Commit, error)

	// Branch operations
	CreateBranch(ctx context.Context, name string) error
	CheckoutBranch(ctx context.Context, name string) error
	MergeBranch(ctx context.Context, source, target string) error
	ListBranches(ctx context.Context) ([]string, error)

	// Platform-specific operations (optional)
	CreatePullRequest(ctx context.Context, req *PullRequestRequest) (*PullRequest, error)
	CreateIssue(ctx context.Context, req *IssueRequest) (*Issue, error)
	TriggerWorkflow(ctx context.Context, workflowName string) error

	// Repository metadata
	GetRepositoryInfo(ctx context.Context) (*RepositoryInfo, error)
}

// Commit represents a Git commit
type Commit struct {
	Hash      string    `json:"hash"`
	Message   string    `json:"message"`
	Author    string    `json:"author"`
	Email     string    `json:"email"`
	Timestamp time.Time `json:"timestamp"`
}

// PullRequestRequest represents a request to create a pull request
type PullRequestRequest struct {
	Title        string   `json:"title"`
	Body         string   `json:"body"`
	SourceBranch string   `json:"source_branch"`
	TargetBranch string   `json:"target_branch"`
	Reviewers    []string `json:"reviewers,omitempty"`
	Labels       []string `json:"labels,omitempty"`
}

// PullRequest represents a pull request
type PullRequest struct {
	Number       int       `json:"number"`
	Title        string    `json:"title"`
	Body         string    `json:"body"`
	State        string    `json:"state"`
	URL          string    `json:"url"`
	CreatedAt    time.Time `json:"created_at"`
	UpdatedAt    time.Time `json:"updated_at"`
	Author       string    `json:"author"`
	SourceBranch string    `json:"source_branch"`
	TargetBranch string    `json:"target_branch"`
}

// IssueRequest represents a request to create an issue
type IssueRequest struct {
	Title     string   `json:"title"`
	Body      string   `json:"body"`
	Labels    []string `json:"labels,omitempty"`
	Assignees []string `json:"assignees,omitempty"`
}

// Issue represents an issue
type Issue struct {
	Number    int       `json:"number"`
	Title     string    `json:"title"`
	Body      string    `json:"body"`
	State     string    `json:"state"`
	URL       string    `json:"url"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
	Author    string    `json:"author"`
	Labels    []string  `json:"labels"`
	Assignees []string  `json:"assignees"`
}

// RepositoryInfo contains repository metadata
type RepositoryInfo struct {
	Name          string `json:"name"`
	FullName      string `json:"full_name"`
	Description   string `json:"description"`
	URL           string `json:"url"`
	CloneURL      string `json:"clone_url"`
	DefaultBranch string `json:"default_branch"`
	Private       bool   `json:"private"`
	Owner         string `json:"owner"`
}

// Config represents Git provider configuration
type Config struct {
	Provider   string           `yaml:"provider"` // github, gitlab, local
	Auth       AuthConfig       `yaml:"auth"`
	Repository RepositoryConfig `yaml:"repository"`
}

// AuthConfig represents authentication configuration
type AuthConfig struct {
	Token    string `yaml:"token,omitempty"`
	Username string `yaml:"username,omitempty"`
	Password string `yaml:"password,omitempty"`
	SSHKey   string `yaml:"ssh_key,omitempty"`
}

// RepositoryConfig represents repository configuration
type RepositoryConfig struct {
	URL      string `yaml:"url"`
	Owner    string `yaml:"owner"`
	Name     string `yaml:"name"`
	Branch   string `yaml:"branch"`
	BasePath string `yaml:"base_path,omitempty"` // For local Git
}

// ProviderType represents supported Git providers
type ProviderType string

const (
	ProviderGitHub ProviderType = "github"
	ProviderGitLab ProviderType = "gitlab"
	ProviderLocal  ProviderType = "local"
)

// NewProvider creates a new Git provider based on configuration
func NewProvider(config *Config) (Provider, error) {
	if config == nil {
		return nil, ErrInvalidConfig
	}

	switch ProviderType(config.Provider) {
	case ProviderGitHub:
		return NewGitHubProvider(config)
	case ProviderGitLab:
		return NewGitLabProvider(config)
	case ProviderLocal:
		return NewLocalProvider(config)
	default:
		return nil, ErrUnsupportedProvider
	}
}

// Common errors
var (
	ErrUnsupportedProvider  = NewGitError("unsupported Git provider")
	ErrRepositoryNotFound   = NewGitError("repository not found")
	ErrFileNotFound         = NewGitError("file not found")
	ErrBranchNotFound       = NewGitError("branch not found")
	ErrAuthenticationFailed = NewGitError("authentication failed")
	ErrPermissionDenied     = NewGitError("permission denied")
	ErrInvalidConfig        = NewGitError("invalid configuration")
)

// GitError represents a Git operation error
type GitError struct {
	Message string
	Cause   error
}

func (e *GitError) Error() string {
	if e.Cause != nil {
		return e.Message + ": " + e.Cause.Error()
	}
	return e.Message
}

func (e *GitError) Unwrap() error {
	return e.Cause
}

func NewGitError(message string) *GitError {
	return &GitError{Message: message}
}

func NewGitErrorWithCause(message string, cause error) *GitError {
	return &GitError{Message: message, Cause: cause}
}
