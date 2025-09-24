package vcs

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestNewGitManager(t *testing.T) {
	tmpDir := t.TempDir()
	
	manager := NewGitManager(tmpDir)
	if manager == nil {
		t.Fatal("NewGitManager returned nil")
	}
	if manager.repoPath != tmpDir {
		t.Errorf("Expected repoPath=%s, got %s", tmpDir, manager.repoPath)
	}
}

func TestNewGit(t *testing.T) {
	tmpDir := t.TempDir()
	
	manager := NewGit(tmpDir)
	if manager == nil {
		t.Fatal("NewGit returned nil")
	}
	if manager.repoPath != tmpDir {
		t.Errorf("Expected repoPath=%s, got %s", tmpDir, manager.repoPath)
	}
}

func TestInitialize_NewRepository(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Check that .git directory was created
	gitDir := filepath.Join(tmpDir, ".git")
	if _, err := os.Stat(gitDir); os.IsNotExist(err) {
		t.Error(".git directory was not created")
	}
	
	// Check that .gitignore was created
	gitignorePath := filepath.Join(tmpDir, ".gitignore")
	if _, err := os.Stat(gitignorePath); os.IsNotExist(err) {
		t.Error(".gitignore file was not created")
	}
	
	// Check .gitignore content
	content, err := os.ReadFile(gitignorePath)
	if err != nil {
		t.Fatalf("Failed to read .gitignore: %v", err)
	}
	
	expectedContent := []string{
		"*.tmp",
		"*.swp",
		"*~",
		".DS_Store",
		"Thumbs.db",
		"/arx",
		"*.exe",
	}
	
	contentStr := string(content)
	for _, expected := range expectedContent {
		if !strings.Contains(contentStr, expected) {
			t.Errorf(".gitignore missing expected content: %s", expected)
		}
	}
}

func TestInitialize_ExistingRepository(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize first time
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("First Initialize failed: %v", err)
	}
	
	// Initialize second time (should not fail)
	err = manager.Initialize()
	if err != nil {
		t.Fatalf("Second Initialize failed: %v", err)
	}
}

func TestStatus(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Get status
	status, err := manager.Status()
	if err != nil {
		t.Fatalf("Status failed: %v", err)
	}
	
	// Should be empty initially (only .gitignore is committed)
	if status != "" {
		t.Errorf("Expected empty status, got: %s", status)
	}
	
	// Create a test file
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	// Get status again
	status, err = manager.Status()
	if err != nil {
		t.Fatalf("Status failed: %v", err)
	}
	
	// Should show untracked file
	if !strings.Contains(status, "test.txt") {
		t.Errorf("Expected status to contain 'test.txt', got: %s", status)
	}
}

func TestAdd(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	// Add file
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	// Check status
	status, err := manager.Status()
	if err != nil {
		t.Fatalf("Status failed: %v", err)
	}
	
	// Should show staged file
	if !strings.Contains(status, "A  test.txt") && !strings.Contains(status, "A test.txt") {
		t.Errorf("Expected status to show staged file, got: %s", status)
	}
}

func TestAdd_MultipleFiles(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create multiple test files
	files := []string{"test1.txt", "test2.txt", "test3.txt"}
	for _, filename := range files {
		filePath := filepath.Join(tmpDir, filename)
		err = os.WriteFile(filePath, []byte("test content"), 0644)
		if err != nil {
			t.Fatalf("Failed to create test file %s: %v", filename, err)
		}
	}
	
	// Add all files
	err = manager.Add(files...)
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	// Check status
	status, err := manager.Status()
	if err != nil {
		t.Fatalf("Status failed: %v", err)
	}
	
	// Should show all staged files
	for _, filename := range files {
		if !strings.Contains(status, filename) {
			t.Errorf("Expected status to contain '%s', got: %s", filename, status)
		}
	}
}

func TestCommit(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	// Add and commit file
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Test commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Check that file is committed
	status, err := manager.Status()
	if err != nil {
		t.Fatalf("Status failed: %v", err)
	}
	
	if status != "" {
		t.Errorf("Expected clean status after commit, got: %s", status)
	}
}

func TestCommit_NothingToCommit(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Try to commit without changes
	err = manager.Commit("Empty commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
}

func TestCreateBranch(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Create branch
	err = manager.CreateBranch("feature-branch")
	if err != nil {
		t.Fatalf("CreateBranch failed: %v", err)
	}
	
	// Check current branch
	branch, err := manager.CurrentBranch()
	if err != nil {
		t.Fatalf("CurrentBranch failed: %v", err)
	}
	
	if branch != "feature-branch" {
		t.Errorf("Expected current branch='feature-branch', got '%s'", branch)
	}
}

func TestCreateBranch_ExistingBranch(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Create branch
	err = manager.CreateBranch("feature-branch")
	if err != nil {
		t.Fatalf("CreateBranch failed: %v", err)
	}
	
	// Switch back to main
	err = manager.SwitchBranch("main")
	if err != nil {
		t.Fatalf("SwitchBranch failed: %v", err)
	}
	
	// Try to create same branch again (should switch to it)
	err = manager.CreateBranch("feature-branch")
	if err != nil {
		t.Fatalf("CreateBranch failed: %v", err)
	}
	
	// Should be on feature-branch
	branch, err := manager.CurrentBranch()
	if err != nil {
		t.Fatalf("CurrentBranch failed: %v", err)
	}
	
	if branch != "feature-branch" {
		t.Errorf("Expected current branch='feature-branch', got '%s'", branch)
	}
}

func TestCurrentBranch(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Check current branch (should be main or master)
	branch, err := manager.CurrentBranch()
	if err != nil {
		t.Fatalf("CurrentBranch failed: %v", err)
	}
	
	if branch != "main" && branch != "master" {
		t.Errorf("Expected branch to be 'main' or 'master', got '%s'", branch)
	}
}

func TestDiff(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Modify the file
	err = os.WriteFile(testFile, []byte("modified content"), 0644)
	if err != nil {
		t.Fatalf("Failed to modify test file: %v", err)
	}
	
	// Get diff
	diff, err := manager.Diff()
	if err != nil {
		t.Fatalf("Diff failed: %v", err)
	}
	
	// Should show the modification
	if !strings.Contains(diff, "modified content") {
		t.Errorf("Expected diff to contain 'modified content', got: %s", diff)
	}
}

func TestLog(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Test commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Get log
	log, err := manager.Log(5)
	if err != nil {
		t.Fatalf("Log failed: %v", err)
	}
	
	// Should contain the commit
	if !strings.Contains(log, "Test commit") {
		t.Errorf("Expected log to contain 'Test commit', got: %s", log)
	}
}

func TestCreateMarkupBranch(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Create markup branch
	branchName, err := manager.CreateMarkupBranch("eq1", "user1")
	if err != nil {
		t.Fatalf("CreateMarkupBranch failed: %v", err)
	}
	
	// Check branch name format
	expectedPrefix := "markup/user1/eq1-"
	if !strings.HasPrefix(branchName, expectedPrefix) {
		t.Errorf("Expected branch name to start with '%s', got '%s'", expectedPrefix, branchName)
	}
	
	// Check current branch
	currentBranch, err := manager.CurrentBranch()
	if err != nil {
		t.Fatalf("CurrentBranch failed: %v", err)
	}
	
	if currentBranch != branchName {
		t.Errorf("Expected current branch='%s', got '%s'", branchName, currentBranch)
	}
}

func TestCommitFloorPlanChange(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a floor plan file
	floorPlanFile := filepath.Join(tmpDir, "floor-plan.json")
	err = os.WriteFile(floorPlanFile, []byte(`{"name": "test floor"}`), 0644)
	if err != nil {
		t.Fatalf("Failed to create floor plan file: %v", err)
	}
	
	// Commit floor plan change
	err = manager.CommitFloorPlanChange("floor-plan.json", "Updated floor plan")
	if err != nil {
		t.Fatalf("CommitFloorPlanChange failed: %v", err)
	}
	
	// Check log
	log, err := manager.Log(5)
	if err != nil {
		t.Fatalf("Log failed: %v", err)
	}
	
	// Should contain the commit message
	if !strings.Contains(log, "[ArxOS] Updated floor plan") {
		t.Errorf("Expected log to contain '[ArxOS] Updated floor plan', got: %s", log)
	}
}

func TestMergeBranch(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Create and switch to feature branch
	err = manager.CreateBranch("feature-branch")
	if err != nil {
		t.Fatalf("CreateBranch failed: %v", err)
	}
	
	// Modify file in feature branch
	err = os.WriteFile(testFile, []byte("feature content"), 0644)
	if err != nil {
		t.Fatalf("Failed to modify test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Feature commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Switch back to main
	err = manager.SwitchBranch("main")
	if err != nil {
		t.Fatalf("SwitchBranch failed: %v", err)
	}
	
	// Merge feature branch
	err = manager.MergeBranch("feature-branch")
	if err != nil {
		t.Fatalf("MergeBranch failed: %v", err)
	}
	
	// Check that file was merged
	content, err := os.ReadFile(testFile)
	if err != nil {
		t.Fatalf("Failed to read test file: %v", err)
	}
	
	if string(content) != "feature content" {
		t.Errorf("Expected file content='feature content', got '%s'", string(content))
	}
}

func TestSwitchBranch(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Create feature branch
	err = manager.CreateBranch("feature-branch")
	if err != nil {
		t.Fatalf("CreateBranch failed: %v", err)
	}
	
	// Switch back to main
	err = manager.SwitchBranch("main")
	if err != nil {
		t.Fatalf("SwitchBranch failed: %v", err)
	}
	
	// Check current branch
	branch, err := manager.CurrentBranch()
	if err != nil {
		t.Fatalf("CurrentBranch failed: %v", err)
	}
	
	if branch != "main" && branch != "master" {
		t.Errorf("Expected current branch to be 'main' or 'master', got '%s'", branch)
	}
}

func TestListBranches(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Create feature branch
	err = manager.CreateBranch("feature-branch")
	if err != nil {
		t.Fatalf("CreateBranch failed: %v", err)
	}
	
	// List branches
	branches, current, err := manager.ListBranches()
	if err != nil {
		t.Fatalf("ListBranches failed: %v", err)
	}
	
	// Should have at least 2 branches
	if len(branches) < 2 {
		t.Errorf("Expected at least 2 branches, got %d", len(branches))
	}
	
	// Current should be feature-branch
	if current != "feature-branch" {
		t.Errorf("Expected current branch='feature-branch', got '%s'", current)
	}
	
	// Should contain both branches
	foundMain := false
	foundFeature := false
	for _, branch := range branches {
		if branch == "main" || branch == "master" {
			foundMain = true
		}
		if branch == "feature-branch" {
			foundFeature = true
		}
	}
	
	if !foundMain {
		t.Error("Expected to find main/master branch")
	}
	if !foundFeature {
		t.Error("Expected to find feature-branch")
	}
}

func TestDeleteBranch(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Create feature branch
	err = manager.CreateBranch("feature-branch")
	if err != nil {
		t.Fatalf("CreateBranch failed: %v", err)
	}
	
	// Switch back to main
	err = manager.SwitchBranch("main")
	if err != nil {
		t.Fatalf("SwitchBranch failed: %v", err)
	}
	
	// Delete feature branch
	err = manager.DeleteBranch("feature-branch")
	if err != nil {
		t.Fatalf("DeleteBranch failed: %v", err)
	}
	
	// List branches
	branches, _, err := manager.ListBranches()
	if err != nil {
		t.Fatalf("ListBranches failed: %v", err)
	}
	
	// Should not contain feature-branch
	for _, branch := range branches {
		if branch == "feature-branch" {
			t.Error("Expected feature-branch to be deleted")
		}
	}
}

func TestTag(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Create tag
	err = manager.Tag("v1.0.0", "Version 1.0.0")
	if err != nil {
		t.Fatalf("Tag failed: %v", err)
	}
	
	// List tags
	tags, err := manager.ListTags()
	if err != nil {
		t.Fatalf("ListTags failed: %v", err)
	}
	
	// Should contain the tag
	if len(tags) != 1 {
		t.Errorf("Expected 1 tag, got %d", len(tags))
	}
	if tags[0] != "v1.0.0" {
		t.Errorf("Expected tag='v1.0.0', got '%s'", tags[0])
	}
}

func TestTag_WithoutMessage(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Create tag without message
	err = manager.Tag("v1.0.0", "")
	if err != nil {
		t.Fatalf("Tag failed: %v", err)
	}
	
	// List tags
	tags, err := manager.ListTags()
	if err != nil {
		t.Fatalf("ListTags failed: %v", err)
	}
	
	// Should contain the tag
	if len(tags) != 1 {
		t.Errorf("Expected 1 tag, got %d", len(tags))
	}
	if tags[0] != "v1.0.0" {
		t.Errorf("Expected tag='v1.0.0', got '%s'", tags[0])
	}
}

func TestListTags(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Initially should have no tags
	tags, err := manager.ListTags()
	if err != nil {
		t.Fatalf("ListTags failed: %v", err)
	}
	
	if len(tags) != 0 {
		t.Errorf("Expected 0 tags initially, got %d", len(tags))
	}
	
	// Create multiple tags
	tagNames := []string{"v1.0.0", "v1.1.0", "v2.0.0"}
	for _, tagName := range tagNames {
		err = manager.Tag(tagName, "Version "+tagName)
		if err != nil {
			t.Fatalf("Tag failed for %s: %v", tagName, err)
		}
	}
	
	// List tags
	tags, err = manager.ListTags()
	if err != nil {
		t.Fatalf("ListTags failed: %v", err)
	}
	
	// Should contain all tags
	if len(tags) != len(tagNames) {
		t.Errorf("Expected %d tags, got %d", len(tagNames), len(tags))
	}
	
	for _, expectedTag := range tagNames {
		found := false
		for _, tag := range tags {
			if tag == expectedTag {
				found = true
				break
			}
		}
		if !found {
			t.Errorf("Expected to find tag '%s'", expectedTag)
		}
	}
}

func TestIsClean(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Should be clean initially
	clean, err := manager.IsClean()
	if err != nil {
		t.Fatalf("IsClean failed: %v", err)
	}
	
	if !clean {
		t.Error("Expected repository to be clean initially")
	}
	
	// Create a test file
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	// Should not be clean now
	clean, err = manager.IsClean()
	if err != nil {
		t.Fatalf("IsClean failed: %v", err)
	}
	
	if clean {
		t.Error("Expected repository to not be clean after adding file")
	}
	
	// Add and commit file
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Test commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Should be clean again
	clean, err = manager.IsClean()
	if err != nil {
		t.Fatalf("IsClean failed: %v", err)
	}
	
	if !clean {
		t.Error("Expected repository to be clean after commit")
	}
}

func TestGetFileHistory(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Get file history
	history, err := manager.GetFileHistory("test.txt", 5)
	if err != nil {
		t.Fatalf("GetFileHistory failed: %v", err)
	}
	
	// Should have one commit
	if len(history) != 1 {
		t.Errorf("Expected 1 commit in history, got %d", len(history))
	}
	
	commit := history[0]
	if commit.Message != "Initial commit" {
		t.Errorf("Expected commit message='Initial commit', got '%s'", commit.Message)
	}
	if commit.Hash == "" {
		t.Error("Expected commit hash to be set")
	}
	if commit.Author == "" {
		t.Error("Expected commit author to be set")
	}
	if commit.Email == "" {
		t.Error("Expected commit email to be set")
	}
	if commit.Date.IsZero() {
		t.Error("Expected commit date to be set")
	}
}

func TestGetCommitInfo(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Test commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Get commit info
	history, err := manager.GetFileHistory("test.txt", 1)
	if err != nil {
		t.Fatalf("GetFileHistory failed: %v", err)
	}
	
	if len(history) == 0 {
		t.Fatal("Expected at least one commit")
	}
	
	commitHash := history[0].Hash
	commitInfo, err := manager.GetCommitInfo(commitHash)
	if err != nil {
		t.Fatalf("GetCommitInfo failed: %v", err)
	}
	
	if commitInfo.Hash != commitHash {
		t.Errorf("Expected hash='%s', got '%s'", commitHash, commitInfo.Hash)
	}
	if commitInfo.Message != "Test commit" {
		t.Errorf("Expected message='Test commit', got '%s'", commitInfo.Message)
	}
	if commitInfo.Author == "" {
		t.Error("Expected author to be set")
	}
	if commitInfo.Email == "" {
		t.Error("Expected email to be set")
	}
	if commitInfo.Date.IsZero() {
		t.Error("Expected date to be set")
	}
}

func TestGetDetailedStatus(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Modify file
	err = os.WriteFile(testFile, []byte("modified content"), 0644)
	if err != nil {
		t.Fatalf("Failed to modify test file: %v", err)
	}
	
	// Create new file
	newFile := filepath.Join(tmpDir, "new.txt")
	err = os.WriteFile(newFile, []byte("new content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create new file: %v", err)
	}
	
	// Get detailed status
	files, err := manager.GetDetailedStatus()
	if err != nil {
		t.Fatalf("GetDetailedStatus failed: %v", err)
	}
	
	// Should have 2 files
	if len(files) != 2 {
		t.Errorf("Expected 2 files in status, got %d", len(files))
	}
	
	// Check file statuses
	foundModified := false
	foundUntracked := false
	
	for _, file := range files {
		if file.Path == "test.txt" && (file.Status == "M" || file.Status == " M") {
			foundModified = true
		}
		if file.Path == "new.txt" && file.Status == "??" {
			foundUntracked = true
		}
	}
	
	if !foundModified {
		t.Error("Expected to find modified file")
	}
	if !foundUntracked {
		t.Error("Expected to find untracked file")
	}
}

func TestGetStatusInfo(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		t.Fatalf("Initialize failed: %v", err)
	}
	
	// Create a test file and commit it
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create test file: %v", err)
	}
	
	err = manager.Add("test.txt")
	if err != nil {
		t.Fatalf("Add failed: %v", err)
	}
	
	err = manager.Commit("Initial commit")
	if err != nil {
		t.Fatalf("Commit failed: %v", err)
	}
	
	// Modify file
	err = os.WriteFile(testFile, []byte("modified content"), 0644)
	if err != nil {
		t.Fatalf("Failed to modify test file: %v", err)
	}
	
	// Create new file
	newFile := filepath.Join(tmpDir, "new.txt")
	err = os.WriteFile(newFile, []byte("new content"), 0644)
	if err != nil {
		t.Fatalf("Failed to create new file: %v", err)
	}
	
	// Get status info
	statusInfo, err := manager.GetStatusInfo()
	if err != nil {
		t.Fatalf("GetStatusInfo failed: %v", err)
	}
	
	// Should not be clean
	if statusInfo.Clean {
		t.Error("Expected repository to not be clean")
	}
	
	// Should have modified and untracked files
	if len(statusInfo.Modified) != 1 {
		t.Errorf("Expected 1 modified file, got %d", len(statusInfo.Modified))
	}
	if len(statusInfo.Untracked) != 1 {
		t.Errorf("Expected 1 untracked file, got %d", len(statusInfo.Untracked))
	}
	
	if statusInfo.Modified[0] != "test.txt" {
		t.Errorf("Expected modified file='test.txt', got '%s'", statusInfo.Modified[0])
	}
	if statusInfo.Untracked[0] != "new.txt" {
		t.Errorf("Expected untracked file='new.txt', got '%s'", statusInfo.Untracked[0])
	}
}

// Test error cases
func TestGitManager_NonExistentDirectory(t *testing.T) {
	// Test with non-existent directory
	manager := NewGitManager("/non/existent/directory")
	
	// Most operations should fail
	_, err := manager.Status()
	if err == nil {
		t.Error("Expected error for non-existent directory")
	}
}

func TestGitManager_NotAGitRepository(t *testing.T) {
	tmpDir := t.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Try to use Git operations without initializing
	_, err := manager.Status()
	if err == nil {
		t.Error("Expected error for non-Git directory")
	}
}

// Benchmark tests
func BenchmarkInitialize(b *testing.B) {
	for i := 0; i < b.N; i++ {
		tmpDir := b.TempDir()
		manager := NewGitManager(tmpDir)
		manager.Initialize()
	}
}

func BenchmarkStatus(b *testing.B) {
	tmpDir := b.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		b.Fatalf("Initialize failed: %v", err)
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		manager.Status()
	}
}

func BenchmarkAdd(b *testing.B) {
	tmpDir := b.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		b.Fatalf("Initialize failed: %v", err)
	}
	
	// Create test file
	testFile := filepath.Join(tmpDir, "test.txt")
	err = os.WriteFile(testFile, []byte("test content"), 0644)
	if err != nil {
		b.Fatalf("Failed to create test file: %v", err)
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		manager.Add("test.txt")
	}
}

func BenchmarkCommit(b *testing.B) {
	tmpDir := b.TempDir()
	manager := NewGitManager(tmpDir)
	
	// Initialize repository
	err := manager.Initialize()
	if err != nil {
		b.Fatalf("Initialize failed: %v", err)
	}
	
	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		// Create unique file for each commit
		testFile := filepath.Join(tmpDir, fmt.Sprintf("test%d.txt", i))
		err = os.WriteFile(testFile, []byte("test content"), 0644)
		if err != nil {
			b.Fatalf("Failed to create test file: %v", err)
		}
		
		manager.Add(testFile)
		manager.Commit(fmt.Sprintf("Commit %d", i))
	}
}