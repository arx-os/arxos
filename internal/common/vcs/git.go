package vcs

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
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