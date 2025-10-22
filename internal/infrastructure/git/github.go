package git

import (
	"context"
	"fmt"
	"net/http"

	"github.com/google/go-github/v58/github"
	"golang.org/x/oauth2"
)

// GitHubProvider implements the Provider interface for GitHub
type GitHubProvider struct {
	client     *github.Client
	config     *Config
	httpClient *http.Client
}

// NewGitHubProvider creates a new GitHub provider
func NewGitHubProvider(config *Config) (*GitHubProvider, error) {
	if config == nil {
		return nil, NewGitErrorWithCause("config is required", ErrInvalidConfig)
	}

	if config.Auth.Token == "" {
		return nil, NewGitErrorWithCause("GitHub token is required", ErrInvalidConfig)
	}

	if config.Repository.Owner == "" || config.Repository.Name == "" {
		return nil, NewGitErrorWithCause("repository owner and name are required", ErrInvalidConfig)
	}

	// Create OAuth2 client
	ctx := context.Background()
	ts := oauth2.StaticTokenSource(
		&oauth2.Token{AccessToken: config.Auth.Token},
	)
	httpClient := oauth2.NewClient(ctx, ts)

	// Create GitHub client
	client := github.NewClient(httpClient)

	return &GitHubProvider{
		client:     client,
		config:     config,
		httpClient: httpClient,
	}, nil
}

// Clone clones the repository to the specified destination
func (p *GitHubProvider) Clone(ctx context.Context, url string, dest string) error {
	// GitHub provider doesn't handle local cloning
	// This would typically be handled by the local Git provider
	return NewGitError("clone operation not supported by GitHub provider - use local Git provider")
}

// Pull pulls the latest changes from the remote repository
func (p *GitHubProvider) Pull(ctx context.Context) error {
	// GitHub provider doesn't handle local Git operations
	// This would typically be handled by the local Git provider
	return NewGitError("pull operation not supported by GitHub provider - use local Git provider")
}

// Push pushes changes to the remote repository
func (p *GitHubProvider) Push(ctx context.Context) error {
	// GitHub provider doesn't handle local Git operations
	// This would typically be handled by the local Git provider
	return NewGitError("push operation not supported by GitHub provider - use local Git provider")
}

// GetFile retrieves a file from the repository
func (p *GitHubProvider) GetFile(ctx context.Context, path string) ([]byte, error) {
	file, _, resp, err := p.client.Repositories.GetContents(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		path,
		&github.RepositoryContentGetOptions{
			Ref: p.config.Repository.Branch,
		},
	)

	if err != nil {
		if resp != nil && resp.StatusCode == http.StatusNotFound {
			return nil, NewGitErrorWithCause("file not found", ErrFileNotFound)
		}
		return nil, NewGitErrorWithCause("failed to get file", err)
	}

	if file == nil {
		return nil, NewGitErrorWithCause("file not found", ErrFileNotFound)
	}

	content, err := file.GetContent()
	if err != nil {
		return nil, NewGitErrorWithCause("failed to decode file content", err)
	}

	return []byte(content), nil
}

// WriteFile writes a file to the repository
func (p *GitHubProvider) WriteFile(ctx context.Context, path string, data []byte) error {
	// Get current file to get SHA (required for updates)
	file, _, _, err := p.client.Repositories.GetContents(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		path,
		&github.RepositoryContentGetOptions{
			Ref: p.config.Repository.Branch,
		},
	)

	var sha *string
	if err == nil && file != nil {
		sha = file.SHA
	}

	// Create commit message
	message := fmt.Sprintf("Update %s", path)
	if sha == nil {
		message = fmt.Sprintf("Add %s", path)
	}

	// Create file content
	content := &github.RepositoryContentFileOptions{
		Message: github.String(message),
		Content: data,
		Branch:  github.String(p.config.Repository.Branch),
	}

	if sha != nil {
		content.SHA = sha
	}

	_, _, err = p.client.Repositories.CreateFile(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		path,
		content,
	)

	if err != nil {
		return NewGitErrorWithCause("failed to write file", err)
	}

	return nil
}

// ListFiles lists files in the repository with the given prefix
func (p *GitHubProvider) ListFiles(ctx context.Context, prefix string) ([]string, error) {
	_, contents, _, err := p.client.Repositories.GetContents(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		prefix,
		&github.RepositoryContentGetOptions{
			Ref: p.config.Repository.Branch,
		},
	)

	if err != nil {
		return nil, NewGitErrorWithCause("failed to list files", err)
	}

	var files []string
	for _, content := range contents {
		if content.Type != nil && *content.Type == "file" {
			files = append(files, *content.Path)
		}
	}

	return files, nil
}

// DeleteFile deletes a file from the repository
func (p *GitHubProvider) DeleteFile(ctx context.Context, path string) error {
	// Get current file to get SHA (required for deletion)
	file, _, _, err := p.client.Repositories.GetContents(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		path,
		&github.RepositoryContentGetOptions{
			Ref: p.config.Repository.Branch,
		},
	)

	if err != nil {
		return NewGitErrorWithCause("failed to get file for deletion", err)
	}

	if file == nil {
		return NewGitErrorWithCause("file not found", ErrFileNotFound)
	}

	// Delete file
	_, _, err = p.client.Repositories.DeleteFile(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		path,
		&github.RepositoryContentFileOptions{
			Message: github.String(fmt.Sprintf("Delete %s", path)),
			SHA:     file.SHA,
			Branch:  github.String(p.config.Repository.Branch),
		},
	)

	if err != nil {
		return NewGitErrorWithCause("failed to delete file", err)
	}

	return nil
}

// Commit creates a commit (not directly supported by GitHub API)
func (p *GitHubProvider) Commit(ctx context.Context, message string) error {
	// GitHub API doesn't support direct commit creation
	// Commits are created through file operations
	return NewGitError("commit operation not supported by GitHub provider - commits are created through file operations")
}

// GetLastCommit gets the last commit information
func (p *GitHubProvider) GetLastCommit(ctx context.Context) (*Commit, error) {
	commits, _, err := p.client.Repositories.ListCommits(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		&github.CommitsListOptions{
			ListOptions: github.ListOptions{PerPage: 1},
		},
	)

	if err != nil {
		return nil, NewGitErrorWithCause("failed to get commits", err)
	}

	if len(commits) == 0 {
		return nil, NewGitErrorWithCause("no commits found", ErrRepositoryNotFound)
	}

	commit := commits[0]
	return &Commit{
		Hash:      commit.GetSHA(),
		Message:   commit.GetCommit().GetMessage(),
		Author:    commit.GetCommit().GetAuthor().GetName(),
		Email:     commit.GetCommit().GetAuthor().GetEmail(),
		Timestamp: commit.GetCommit().GetAuthor().GetDate().Time,
	}, nil
}

// CreateBranch creates a new branch
func (p *GitHubProvider) CreateBranch(ctx context.Context, name string) error {
	// Get the SHA of the current branch
	ref, _, err := p.client.Git.GetRef(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		fmt.Sprintf("heads/%s", p.config.Repository.Branch),
	)

	if err != nil {
		return NewGitErrorWithCause("failed to get current branch", err)
	}

	// Create new branch
	_, _, err = p.client.Git.CreateRef(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		&github.Reference{
			Ref: github.String(fmt.Sprintf("refs/heads/%s", name)),
			Object: &github.GitObject{
				SHA: ref.Object.SHA,
			},
		},
	)

	if err != nil {
		return NewGitErrorWithCause("failed to create branch", err)
	}

	return nil
}

// CheckoutBranch checks out a branch (not directly supported by GitHub API)
func (p *GitHubProvider) CheckoutBranch(ctx context.Context, name string) error {
	// GitHub API doesn't support direct branch checkout
	// This would typically be handled by the local Git provider
	return NewGitError("checkout operation not supported by GitHub provider - use local Git provider")
}

// MergeBranch merges a branch into another branch
func (p *GitHubProvider) MergeBranch(ctx context.Context, source, target string) error {
	// Create merge request
	_, _, err := p.client.Repositories.Merge(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		&github.RepositoryMergeRequest{
			Base:          github.String(target),
			Head:          github.String(source),
			CommitMessage: github.String(fmt.Sprintf("Merge %s into %s", source, target)),
		},
	)

	if err != nil {
		return NewGitErrorWithCause("failed to merge branch", err)
	}

	return nil
}

// ListBranches lists all branches in the repository
func (p *GitHubProvider) ListBranches(ctx context.Context) ([]string, error) {
	branches, _, err := p.client.Repositories.ListBranches(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		&github.BranchListOptions{},
	)

	if err != nil {
		return nil, NewGitErrorWithCause("failed to list branches", err)
	}

	var branchNames []string
	for _, branch := range branches {
		branchNames = append(branchNames, branch.GetName())
	}

	return branchNames, nil
}

// CreatePullRequest creates a pull request
func (p *GitHubProvider) CreatePullRequest(ctx context.Context, req *PullRequestRequest) (*PullRequest, error) {
	pr, _, err := p.client.PullRequests.Create(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		&github.NewPullRequest{
			Title: github.String(req.Title),
			Head:  github.String(req.SourceBranch),
			Base:  github.String(req.TargetBranch),
			Body:  github.String(req.Body),
		},
	)

	if err != nil {
		return nil, NewGitErrorWithCause("failed to create pull request", err)
	}

	return &PullRequest{
		Number:       pr.GetNumber(),
		Title:        pr.GetTitle(),
		Body:         pr.GetBody(),
		State:        pr.GetState(),
		URL:          pr.GetHTMLURL(),
		CreatedAt:    pr.GetCreatedAt().Time,
		UpdatedAt:    pr.GetUpdatedAt().Time,
		Author:       pr.GetUser().GetLogin(),
		SourceBranch: pr.GetHead().GetRef(),
		TargetBranch: pr.GetBase().GetRef(),
	}, nil
}

// CreateIssue creates an issue
func (p *GitHubProvider) CreateIssue(ctx context.Context, req *IssueRequest) (*Issue, error) {
	issue, _, err := p.client.Issues.Create(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		&github.IssueRequest{
			Title:     github.String(req.Title),
			Body:      github.String(req.Body),
			Labels:    &req.Labels,
			Assignees: &req.Assignees,
		},
	)

	if err != nil {
		return nil, NewGitErrorWithCause("failed to create issue", err)
	}

	return &Issue{
		Number:    issue.GetNumber(),
		Title:     issue.GetTitle(),
		Body:      issue.GetBody(),
		State:     issue.GetState(),
		URL:       issue.GetHTMLURL(),
		CreatedAt: issue.GetCreatedAt().Time,
		UpdatedAt: issue.GetUpdatedAt().Time,
		Author:    issue.GetUser().GetLogin(),
		Labels:    extractLabels(issue.Labels),
		Assignees: extractAssignees(issue.Assignees),
	}, nil
}

// TriggerWorkflow triggers a GitHub Actions workflow
func (p *GitHubProvider) TriggerWorkflow(ctx context.Context, workflowName string) error {
	// Get workflow ID
	workflows, _, err := p.client.Actions.ListWorkflows(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		&github.ListOptions{},
	)

	if err != nil {
		return NewGitErrorWithCause("failed to list workflows", err)
	}

	var workflowID int64
	for _, workflow := range workflows.Workflows {
		if workflow.GetName() == workflowName {
			workflowID = workflow.GetID()
			break
		}
	}

	if workflowID == 0 {
		return NewGitErrorWithCause("workflow not found", ErrRepositoryNotFound)
	}

	// Trigger workflow dispatch event
	_, err = p.client.Actions.CreateWorkflowDispatchEventByFileName(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
		workflowName,
		github.CreateWorkflowDispatchEventRequest{
			Ref: p.config.Repository.Branch,
		},
	)

	if err != nil {
		return NewGitErrorWithCause("failed to trigger workflow", err)
	}

	return nil
}

// GetRepositoryInfo gets repository information
func (p *GitHubProvider) GetRepositoryInfo(ctx context.Context) (*RepositoryInfo, error) {
	repo, _, err := p.client.Repositories.Get(
		ctx,
		p.config.Repository.Owner,
		p.config.Repository.Name,
	)

	if err != nil {
		return nil, NewGitErrorWithCause("failed to get repository info", err)
	}

	return &RepositoryInfo{
		Name:          repo.GetName(),
		FullName:      repo.GetFullName(),
		Description:   repo.GetDescription(),
		URL:           repo.GetHTMLURL(),
		CloneURL:      repo.GetCloneURL(),
		DefaultBranch: repo.GetDefaultBranch(),
		Private:       repo.GetPrivate(),
		Owner:         repo.GetOwner().GetLogin(),
	}, nil
}

// Helper functions

func extractLabels(labels []*github.Label) []string {
	var result []string
	for _, label := range labels {
		result = append(result, label.GetName())
	}
	return result
}

func extractAssignees(assignees []*github.User) []string {
	var result []string
	for _, assignee := range assignees {
		result = append(result, assignee.GetLogin())
	}
	return result
}
