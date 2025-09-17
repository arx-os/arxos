package vcs

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// GitManager handles version control operations
type GitManager struct {
	repoPath string
}

// NewGitManager creates a new Git manager
func NewGitManager(repoPath string) *GitManager {
	return &GitManager{
		repoPath: repoPath,
	}
}

// Initialize initializes a Git repository if it doesn't exist
func (g *GitManager) Initialize() error {
	// Check if .git directory exists
	gitDir := filepath.Join(g.repoPath, ".git")
	if _, err := os.Stat(gitDir); os.IsNotExist(err) {
		logger.Info("Initializing Git repository in %s", g.repoPath)
		cmd := exec.Command("git", "init")
		cmd.Dir = g.repoPath
		if output, err := cmd.CombinedOutput(); err != nil {
			return fmt.Errorf("failed to initialize git repo: %w\n%s", err, output)
		}
		
		// Set up initial .gitignore
		gitignore := filepath.Join(g.repoPath, ".gitignore")
		ignoreContent := `# Temporary files
*.tmp
*.swp
*~

# OS files
.DS_Store
Thumbs.db

# Build artifacts
/arx
*.exe
`
		if err := os.WriteFile(gitignore, []byte(ignoreContent), 0644); err != nil {
			logger.Warn("Failed to create .gitignore: %v", err)
		}
		
		// Make initial commit
		if err := g.Add(".gitignore"); err != nil {
			logger.Warn("Failed to add .gitignore: %v", err)
		}
		if err := g.Commit("Initial commit - ArxOS floor plan repository"); err != nil {
			logger.Warn("Failed to make initial commit: %v", err)
		}
	}
	
	return nil
}

// Status returns the current Git status
func (g *GitManager) Status() (string, error) {
	cmd := exec.Command("git", "status", "--short")
	cmd.Dir = g.repoPath
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("failed to get git status: %w", err)
	}
	return string(output), nil
}

// Add stages files for commit
func (g *GitManager) Add(files ...string) error {
	args := append([]string{"add"}, files...)
	cmd := exec.Command("git", args...)
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to add files: %w\n%s", err, output)
	}
	return nil
}

// Commit creates a commit with the given message
func (g *GitManager) Commit(message string) error {
	cmd := exec.Command("git", "commit", "-m", message)
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		// Check if there's nothing to commit
		if strings.Contains(string(output), "nothing to commit") {
			return nil
		}
		return fmt.Errorf("failed to commit: %w\n%s", err, output)
	}
	return nil
}

// CreateBranch creates and switches to a new branch
func (g *GitManager) CreateBranch(branchName string) error {
	// Create branch
	cmd := exec.Command("git", "checkout", "-b", branchName)
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		// Try to switch if branch already exists
		cmd = exec.Command("git", "checkout", branchName)
		cmd.Dir = g.repoPath
		if output2, err2 := cmd.CombinedOutput(); err2 != nil {
			return fmt.Errorf("failed to create/switch branch: %w\n%s\n%s", err, output, output2)
		}
	}
	return nil
}

// CurrentBranch returns the current branch name
func (g *GitManager) CurrentBranch() (string, error) {
	cmd := exec.Command("git", "branch", "--show-current")
	cmd.Dir = g.repoPath
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("failed to get current branch: %w", err)
	}
	return strings.TrimSpace(string(output)), nil
}

// Diff returns the diff of unstaged changes
func (g *GitManager) Diff() (string, error) {
	cmd := exec.Command("git", "diff")
	cmd.Dir = g.repoPath
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("failed to get diff: %w", err)
	}
	return string(output), nil
}

// Log returns the commit history
func (g *GitManager) Log(limit int) (string, error) {
	cmd := exec.Command("git", "log", "--oneline", fmt.Sprintf("-%d", limit))
	cmd.Dir = g.repoPath
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("failed to get log: %w", err)
	}
	return string(output), nil
}

// CreateMarkupBranch creates a branch for equipment status changes
func (g *GitManager) CreateMarkupBranch(equipmentID string, user string) (string, error) {
	// Generate branch name
	timestamp := time.Now().Format("20060102-150405")
	branchName := fmt.Sprintf("markup/%s/%s-%s", user, equipmentID, timestamp)
	
	// Create and switch to branch
	if err := g.CreateBranch(branchName); err != nil {
		return "", err
	}
	
	logger.Info("Created markup branch: %s", branchName)
	return branchName, nil
}

// CommitFloorPlanChange commits changes to a floor plan file
func (g *GitManager) CommitFloorPlanChange(floorPlanFile string, message string) error {
	// Stage the floor plan file
	if err := g.Add(floorPlanFile); err != nil {
		return err
	}
	
	// Commit with descriptive message
	fullMessage := fmt.Sprintf("[ArxOS] %s\n\nAutomated commit from ArxOS terminal interface", message)
	if err := g.Commit(fullMessage); err != nil {
		return err
	}
	
	logger.Info("Committed floor plan change: %s", message)
	return nil
}

// MergeBranch merges a branch into the current branch
func (g *GitManager) MergeBranch(branchName string) error {
	cmd := exec.Command("git", "merge", branchName, "--no-ff", "-m", 
		fmt.Sprintf("Merge markup branch '%s'", branchName))
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to merge branch: %w\n%s", err, output)
	}
	return nil
}

// SwitchBranch switches to an existing branch
func (g *GitManager) SwitchBranch(branchName string) error {
	cmd := exec.Command("git", "checkout", branchName)
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to switch branch: %w\n%s", err, output)
	}
	return nil
}

// ListBranches returns a list of all branches
func (g *GitManager) ListBranches() ([]string, string, error) {
	cmd := exec.Command("git", "branch")
	cmd.Dir = g.repoPath
	output, err := cmd.Output()
	if err != nil {
		return nil, "", fmt.Errorf("failed to list branches: %w", err)
	}

	var branches []string
	var current string
	lines := strings.Split(string(output), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "* ") {
			current = strings.TrimPrefix(line, "* ")
			branches = append(branches, current)
		} else {
			branches = append(branches, line)
		}
	}

	return branches, current, nil
}

// DeleteBranch deletes a branch
func (g *GitManager) DeleteBranch(branchName string) error {
	cmd := exec.Command("git", "branch", "-d", branchName)
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		// Try force delete if regular delete fails
		cmd = exec.Command("git", "branch", "-D", branchName)
		cmd.Dir = g.repoPath
		if output2, err2 := cmd.CombinedOutput(); err2 != nil {
			return fmt.Errorf("failed to delete branch: %w\n%s\n%s", err, output, output2)
		}
	}
	return nil
}

// Tag creates a tag
func (g *GitManager) Tag(tagName, message string) error {
	args := []string{"tag", "-a", tagName}
	if message != "" {
		args = append(args, "-m", message)
	}
	cmd := exec.Command("git", args...)
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to create tag: %w\n%s", err, output)
	}
	return nil
}

// ListTags returns a list of all tags
func (g *GitManager) ListTags() ([]string, error) {
	cmd := exec.Command("git", "tag")
	cmd.Dir = g.repoPath
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to list tags: %w", err)
	}

	var tags []string
	lines := strings.Split(string(output), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line != "" {
			tags = append(tags, line)
		}
	}

	return tags, nil
}

// Push pushes changes to remote repository
func (g *GitManager) Push(remote, branch string) error {
	args := []string{"push"}
	if remote != "" {
		args = append(args, remote)
	}
	if branch != "" {
		args = append(args, branch)
	}
	cmd := exec.Command("git", args...)
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to push: %w\n%s", err, output)
	}
	return nil
}

// Pull pulls changes from remote repository
func (g *GitManager) Pull(remote, branch string) error {
	args := []string{"pull"}
	if remote != "" {
		args = append(args, remote)
	}
	if branch != "" {
		args = append(args, branch)
	}
	cmd := exec.Command("git", args...)
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to pull: %w\n%s", err, output)
	}
	return nil
}

// Clone clones a remote repository
func (g *GitManager) Clone(repoURL, targetPath string) error {
	cmd := exec.Command("git", "clone", repoURL, targetPath)
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to clone: %w\n%s", err, output)
	}
	// Update repo path to cloned repository
	g.repoPath = targetPath
	return nil
}

// Reset resets the repository to a specific commit
func (g *GitManager) Reset(commitHash string, hard bool) error {
	args := []string{"reset"}
	if hard {
		args = append(args, "--hard")
	}
	args = append(args, commitHash)
	cmd := exec.Command("git", args...)
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to reset: %w\n%s", err, output)
	}
	return nil
}

// Stash stashes current changes
func (g *GitManager) Stash(message string) error {
	args := []string{"stash", "save"}
	if message != "" {
		args = append(args, message)
	}
	cmd := exec.Command("git", args...)
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to stash: %w\n%s", err, output)
	}
	return nil
}

// StashPop applies and removes the most recent stash
func (g *GitManager) StashPop() error {
	cmd := exec.Command("git", "stash", "pop")
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to pop stash: %w\n%s", err, output)
	}
	return nil
}

// GetRemotes returns a list of configured remotes
func (g *GitManager) GetRemotes() (map[string]string, error) {
	cmd := exec.Command("git", "remote", "-v")
	cmd.Dir = g.repoPath
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to get remotes: %w", err)
	}

	remotes := make(map[string]string)
	lines := strings.Split(string(output), "\n")
	for _, line := range lines {
		parts := strings.Fields(line)
		if len(parts) >= 2 && strings.Contains(line, "(fetch)") {
			remotes[parts[0]] = parts[1]
		}
	}

	return remotes, nil
}

// AddRemote adds a remote repository
func (g *GitManager) AddRemote(name, url string) error {
	cmd := exec.Command("git", "remote", "add", name, url)
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to add remote: %w\n%s", err, output)
	}
	return nil
}

// RemoveRemote removes a remote repository
func (g *GitManager) RemoveRemote(name string) error {
	cmd := exec.Command("git", "remote", "remove", name)
	cmd.Dir = g.repoPath
	if output, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("failed to remove remote: %w\n%s", err, output)
	}
	return nil
}

// IsClean checks if the working directory is clean
func (g *GitManager) IsClean() (bool, error) {
	status, err := g.Status()
	if err != nil {
		return false, err
	}
	return status == "", nil
}

// GetFileHistory returns the commit history for a specific file
func (g *GitManager) GetFileHistory(filePath string, limit int) ([]CommitInfo, error) {
	args := []string{"log", "--pretty=format:%H|%an|%ae|%at|%s", fmt.Sprintf("-%d", limit), "--", filePath}
	cmd := exec.Command("git", args...)
	cmd.Dir = g.repoPath
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to get file history: %w", err)
	}

	var commits []CommitInfo
	lines := strings.Split(string(output), "\n")
	for _, line := range lines {
		if line == "" {
			continue
		}
		parts := strings.Split(line, "|")
		if len(parts) >= 5 {
			unixTime, _ := strconv.ParseInt(parts[3], 10, 64)
			timestamp := time.Unix(unixTime, 0)
			commits = append(commits, CommitInfo{
				Hash:    parts[0],
				Author:  parts[1],
				Email:   parts[2],
				Date:    timestamp,
				Message: parts[4],
			})
		}
	}

	return commits, nil
}

// GetCommitInfo returns information about a specific commit
func (g *GitManager) GetCommitInfo(commitHash string) (*CommitInfo, error) {
	cmd := exec.Command("git", "show", "--pretty=format:%H|%an|%ae|%at|%s", "--no-patch", commitHash)
	cmd.Dir = g.repoPath
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to get commit info: %w", err)
	}

	parts := strings.Split(strings.TrimSpace(string(output)), "|")
	if len(parts) < 5 {
		return nil, fmt.Errorf("invalid commit info format")
	}

	unixTime, _ := strconv.ParseInt(parts[3], 10, 64)
	timestamp := time.Unix(unixTime, 0)
	return &CommitInfo{
		Hash:    parts[0],
		Author:  parts[1],
		Email:   parts[2],
		Date:    timestamp,
		Message: parts[4],
	}, nil
}

// CommitInfo represents information about a commit
type CommitInfo struct {
	Hash    string
	Author  string
	Email   string
	Date    time.Time
	Message string
}

// FileStatus represents the status of a file in the repository
type FileStatus struct {
	Path   string
	Status string // M=modified, A=added, D=deleted, ??=untracked
}

// GetDetailedStatus returns detailed status of all files
func (g *GitManager) GetDetailedStatus() ([]FileStatus, error) {
	cmd := exec.Command("git", "status", "--porcelain")
	cmd.Dir = g.repoPath
	output, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("failed to get detailed status: %w", err)
	}

	var files []FileStatus
	lines := strings.Split(string(output), "\n")
	for _, line := range lines {
		if line == "" {
			continue
		}
		if len(line) >= 3 {
			files = append(files, FileStatus{
				Status: strings.TrimSpace(line[:2]),
				Path:   strings.TrimSpace(line[3:]),
			})
		}
	}

	return files, nil
}

// StatusInfo represents the complete repository status
type StatusInfo struct {
	Branch    string
	Clean     bool
	Modified  []string
	Added     []string
	Deleted   []string
	Untracked []string
}

// GetStatusInfo returns structured status information
func (g *GitManager) GetStatusInfo() (*StatusInfo, error) {
	// Get current branch
	branch, err := g.CurrentBranch()
	if err != nil {
		branch = "unknown"
	}

	// Get file status
	files, err := g.GetDetailedStatus()
	if err != nil {
		return nil, err
	}

	info := &StatusInfo{
		Branch:    branch,
		Clean:     len(files) == 0,
		Modified:  []string{},
		Added:     []string{},
		Deleted:   []string{},
		Untracked: []string{},
	}

	for _, file := range files {
		switch file.Status {
		case "M", " M", "MM":
			info.Modified = append(info.Modified, file.Path)
		case "A", " A", "AM":
			info.Added = append(info.Added, file.Path)
		case "D", " D":
			info.Deleted = append(info.Deleted, file.Path)
		case "??":
			info.Untracked = append(info.Untracked, file.Path)
		}
	}

	return info, nil
}

// Git is an alias for GitManager for backward compatibility
type Git = GitManager

// NewGit creates a new Git manager (alias for NewGitManager)
func NewGit(repoPath string) *Git {
	return NewGitManager(repoPath)
}