package vcs

import (
	"fmt"
	"io/ioutil"
	"os"
	"os/exec"
	"path/filepath"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func setupTestRepo(t *testing.T) (string, func()) {
	// Create temporary directory
	tmpDir, err := ioutil.TempDir("", "arxos-git-test")
	require.NoError(t, err)

	// Initialize git repo
	cmd := exec.Command("git", "init")
	cmd.Dir = tmpDir
	err = cmd.Run()
	require.NoError(t, err)

	// Configure git user for the test repo
	cmd = exec.Command("git", "config", "user.email", "test@arxos.io")
	cmd.Dir = tmpDir
	err = cmd.Run()
	require.NoError(t, err)

	cmd = exec.Command("git", "config", "user.name", "Test User")
	cmd.Dir = tmpDir
	err = cmd.Run()
	require.NoError(t, err)

	cleanup := func() {
		os.RemoveAll(tmpDir)
	}

	return tmpDir, cleanup
}

func TestNewGitManager(t *testing.T) {
	manager := NewGitManager("/test/path")
	assert.NotNil(t, manager)
	assert.Equal(t, "/test/path", manager.repoPath)
}

func TestGitManagerInitialize(t *testing.T) {
	t.Run("new repository", func(t *testing.T) {
		tmpDir, err := ioutil.TempDir("", "arxos-git-init")
		require.NoError(t, err)
		defer os.RemoveAll(tmpDir)

		manager := NewGitManager(tmpDir)
		err = manager.Initialize()
		assert.NoError(t, err)

		// Check .git directory exists
		gitDir := filepath.Join(tmpDir, ".git")
		assert.DirExists(t, gitDir)

		// Check .gitignore exists
		gitignore := filepath.Join(tmpDir, ".gitignore")
		assert.FileExists(t, gitignore)
	})

	t.Run("existing repository", func(t *testing.T) {
		tmpDir, cleanup := setupTestRepo(t)
		defer cleanup()

		manager := NewGitManager(tmpDir)
		err := manager.Initialize()
		assert.NoError(t, err)
	})
}

func TestGitManagerAdd(t *testing.T) {
	tmpDir, cleanup := setupTestRepo(t)
	defer cleanup()

	manager := NewGitManager(tmpDir)

	// Create a test file
	testFile := filepath.Join(tmpDir, "test.txt")
	err := ioutil.WriteFile(testFile, []byte("test content"), 0644)
	require.NoError(t, err)

	// Add file
	err = manager.Add("test.txt")
	assert.NoError(t, err)

	// Check status
	cmd := exec.Command("git", "status", "--porcelain")
	cmd.Dir = tmpDir
	output, err := cmd.Output()
	require.NoError(t, err)
	assert.Contains(t, string(output), "A  test.txt")
}

func TestGitManagerCommit(t *testing.T) {
	tmpDir, cleanup := setupTestRepo(t)
	defer cleanup()

	manager := NewGitManager(tmpDir)

	// Create and add a file
	testFile := filepath.Join(tmpDir, "test.txt")
	err := ioutil.WriteFile(testFile, []byte("test content"), 0644)
	require.NoError(t, err)

	err = manager.Add("test.txt")
	require.NoError(t, err)

	// Commit
	err = manager.Commit("Test commit")
	assert.NoError(t, err)

	// Check log
	cmd := exec.Command("git", "log", "--oneline")
	cmd.Dir = tmpDir
	output, err := cmd.Output()
	require.NoError(t, err)
	assert.Contains(t, string(output), "Test commit")
}

func TestGitManagerDiff(t *testing.T) {
	tmpDir, cleanup := setupTestRepo(t)
	defer cleanup()

	manager := NewGitManager(tmpDir)

	// Create initial file and commit
	testFile := filepath.Join(tmpDir, "test.txt")
	err := ioutil.WriteFile(testFile, []byte("initial content"), 0644)
	require.NoError(t, err)

	err = manager.Add("test.txt")
	require.NoError(t, err)

	err = manager.Commit("Initial commit")
	require.NoError(t, err)

	// Modify file
	err = ioutil.WriteFile(testFile, []byte("modified content"), 0644)
	require.NoError(t, err)

	// Get diff
	diff, err := manager.Diff()
	assert.NoError(t, err)
	assert.Contains(t, diff, "initial content")
	assert.Contains(t, diff, "modified content")
}

func TestGitManagerStatus(t *testing.T) {
	tmpDir, cleanup := setupTestRepo(t)
	defer cleanup()

	manager := NewGitManager(tmpDir)

	// Create untracked file
	testFile := filepath.Join(tmpDir, "untracked.txt")
	err := ioutil.WriteFile(testFile, []byte("content"), 0644)
	require.NoError(t, err)

	// Get status
	status, err := manager.Status()
	assert.NoError(t, err)
	assert.Contains(t, status, "untracked.txt")
}

func TestGitManagerLog(t *testing.T) {
	tmpDir, cleanup := setupTestRepo(t)
	defer cleanup()

	manager := NewGitManager(tmpDir)

	// Create multiple commits
	for i := 0; i < 3; i++ {
		fileName := fmt.Sprintf("file%d.txt", i)
		testFile := filepath.Join(tmpDir, fileName)
		err := ioutil.WriteFile(testFile, []byte(fmt.Sprintf("content %d", i)), 0644)
		require.NoError(t, err)

		err = manager.Add(fileName)
		require.NoError(t, err)

		err = manager.Commit(fmt.Sprintf("Commit %d", i))
		require.NoError(t, err)
	}

	// Get log
	log, err := manager.Log(5)
	assert.NoError(t, err)
	assert.Contains(t, log, "Commit 0")
	assert.Contains(t, log, "Commit 1")
	assert.Contains(t, log, "Commit 2")
}

func TestGitManagerGetCommit(t *testing.T) {
	tmpDir, cleanup := setupTestRepo(t)
	defer cleanup()

	manager := NewGitManager(tmpDir)

	// Create a commit
	testFile := filepath.Join(tmpDir, "test.txt")
	err := ioutil.WriteFile(testFile, []byte("test content"), 0644)
	require.NoError(t, err)

	err = manager.Add("test.txt")
	require.NoError(t, err)

	err = manager.Commit("Test commit")
	require.NoError(t, err)

	// Get HEAD commit
	commit, err := manager.GetCommit("HEAD")
	assert.NoError(t, err)
	assert.NotEmpty(t, commit.Hash)
	assert.Equal(t, "Test User", commit.Author)
	assert.Equal(t, "Test commit", commit.Message)
}

func TestGitManagerTag(t *testing.T) {
	tmpDir, cleanup := setupTestRepo(t)
	defer cleanup()

	manager := NewGitManager(tmpDir)

	// Create a commit
	testFile := filepath.Join(tmpDir, "test.txt")
	err := ioutil.WriteFile(testFile, []byte("test content"), 0644)
	require.NoError(t, err)

	err = manager.Add("test.txt")
	require.NoError(t, err)

	err = manager.Commit("Test commit")
	require.NoError(t, err)

	// Create tag
	err = manager.Tag("v1.0.0", "Version 1.0.0")
	assert.NoError(t, err)

	// List tags
	tags, err := manager.ListTags()
	assert.NoError(t, err)
	assert.Contains(t, tags, "v1.0.0")
}

func TestGitManagerBranch(t *testing.T) {
	tmpDir, cleanup := setupTestRepo(t)
	defer cleanup()

	manager := NewGitManager(tmpDir)

	// Create initial commit (required for branching)
	testFile := filepath.Join(tmpDir, "test.txt")
	err := ioutil.WriteFile(testFile, []byte("test content"), 0644)
	require.NoError(t, err)

	err = manager.Add("test.txt")
	require.NoError(t, err)

	err = manager.Commit("Initial commit")
	require.NoError(t, err)

	// Create branch
	err = manager.CreateBranch("feature-test")
	assert.NoError(t, err)

	// List branches
	branches, err := manager.ListBranches()
	assert.NoError(t, err)
	assert.Contains(t, branches, "feature-test")

	// Switch branch
	err = manager.SwitchBranch("feature-test")
	assert.NoError(t, err)

	// Get current branch
	current, err := manager.CurrentBranch()
	assert.NoError(t, err)
	assert.Equal(t, "feature-test", current)
}

func TestGitManagerRevert(t *testing.T) {
	tmpDir, cleanup := setupTestRepo(t)
	defer cleanup()

	manager := NewGitManager(tmpDir)

	// Create initial commit
	testFile := filepath.Join(tmpDir, "test.txt")
	err := ioutil.WriteFile(testFile, []byte("initial content"), 0644)
	require.NoError(t, err)

	err = manager.Add("test.txt")
	require.NoError(t, err)

	err = manager.Commit("Initial commit")
	require.NoError(t, err)

	// Get initial commit hash
	commit1, err := manager.GetCommit("HEAD")
	require.NoError(t, err)

	// Create second commit
	err = ioutil.WriteFile(testFile, []byte("modified content"), 0644)
	require.NoError(t, err)

	err = manager.Add("test.txt")
	require.NoError(t, err)

	err = manager.Commit("Second commit")
	require.NoError(t, err)

	// Revert to first commit
	err = manager.Revert(commit1.Hash)
	assert.NoError(t, err)

	// Check file content is reverted
	content, err := ioutil.ReadFile(testFile)
	require.NoError(t, err)
	assert.Equal(t, "initial content", string(content))
}

func TestGitManagerClean(t *testing.T) {
	tmpDir, cleanup := setupTestRepo(t)
	defer cleanup()

	manager := NewGitManager(tmpDir)

	// Create untracked files
	untracked1 := filepath.Join(tmpDir, "untracked1.txt")
	untracked2 := filepath.Join(tmpDir, "untracked2.txt")
	err := ioutil.WriteFile(untracked1, []byte("content"), 0644)
	require.NoError(t, err)
	err = ioutil.WriteFile(untracked2, []byte("content"), 0644)
	require.NoError(t, err)

	// Clean
	err = manager.Clean()
	assert.NoError(t, err)

	// Check files are removed
	assert.NoFileExists(t, untracked1)
	assert.NoFileExists(t, untracked2)
}

func TestGitManagerIsRepo(t *testing.T) {
	t.Run("valid repo", func(t *testing.T) {
		tmpDir, cleanup := setupTestRepo(t)
		defer cleanup()

		manager := NewGitManager(tmpDir)
		isRepo := manager.IsRepo()
		assert.True(t, isRepo)
	})

	t.Run("not a repo", func(t *testing.T) {
		tmpDir, err := ioutil.TempDir("", "arxos-not-repo")
		require.NoError(t, err)
		defer os.RemoveAll(tmpDir)

		manager := NewGitManager(tmpDir)
		isRepo := manager.IsRepo()
		assert.False(t, isRepo)
	})
}

func TestGitManagerGetFileHistory(t *testing.T) {
	tmpDir, cleanup := setupTestRepo(t)
	defer cleanup()

	manager := NewGitManager(tmpDir)

	testFile := filepath.Join(tmpDir, "test.txt")

	// Create multiple versions of the file
	for i := 0; i < 3; i++ {
		content := fmt.Sprintf("version %d", i)
		err := ioutil.WriteFile(testFile, []byte(content), 0644)
		require.NoError(t, err)

		err = manager.Add("test.txt")
		require.NoError(t, err)

		err = manager.Commit(fmt.Sprintf("Version %d", i))
		require.NoError(t, err)

		time.Sleep(10 * time.Millisecond) // Ensure different timestamps
	}

	// Get file history
	history, err := manager.GetFileHistory("test.txt", 10)
	assert.NoError(t, err)
	assert.Len(t, history, 3)
}