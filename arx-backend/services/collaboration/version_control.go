package collaboration

import (
	"crypto/sha256"
	"fmt"
	"sort"
	"sync"
	"time"
)

// Commit represents a version control commit
type Commit struct {
	ID         string                 `json:"id"`
	Message    string                 `json:"message"`
	Author     string                 `json:"author"`
	Timestamp  time.Time              `json:"timestamp"`
	ParentIDs  []string               `json:"parent_ids"`
	DocumentID string                 `json:"document_id"`
	Content    string                 `json:"content"`
	Operations []Operation            `json:"operations"`
	Vector     map[string]int         `json:"vector"`
	Metadata   map[string]interface{} `json:"metadata,omitempty"`
}

// Branch represents a version control branch
type Branch struct {
	Name        string    `json:"name"`
	CommitID    string    `json:"commit_id"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
	IsDefault   bool      `json:"is_default"`
	IsProtected bool      `json:"is_protected"`
}

// MergeRequest represents a merge request between branches
type MergeRequest struct {
	ID           string    `json:"id"`
	Title        string    `json:"title"`
	Description  string    `json:"description"`
	SourceBranch string    `json:"source_branch"`
	TargetBranch string    `json:"target_branch"`
	Author       string    `json:"author"`
	Status       string    `json:"status"` // open, merged, closed
	CreatedAt    time.Time `json:"created_at"`
	UpdatedAt    time.Time `json:"updated_at"`
	Conflicts    []string  `json:"conflicts,omitempty"`
}

// VersionControlService handles Git-like version control for documents
type VersionControlService struct {
	commits       map[string]*Commit
	branches      map[string]map[string]*Branch // documentID -> branchName -> Branch
	mergeRequests map[string]*MergeRequest
	mu            sync.RWMutex
}

// NewVersionControlService creates a new version control service
func NewVersionControlService() *VersionControlService {
	return &VersionControlService{
		commits:       make(map[string]*Commit),
		branches:      make(map[string]map[string]*Branch),
		mergeRequests: make(map[string]*MergeRequest),
	}
}

// CreateInitialCommit creates the initial commit for a document
func (vcs *VersionControlService) CreateInitialCommit(documentID, content, author, message string) (*Commit, error) {
	vcs.mu.Lock()
	defer vcs.mu.Unlock()

	commit := &Commit{
		ID:         vcs.generateCommitID(),
		Message:    message,
		Author:     author,
		Timestamp:  time.Now(),
		ParentIDs:  []string{},
		DocumentID: documentID,
		Content:    content,
		Operations: []Operation{},
		Vector:     make(map[string]int),
		Metadata:   make(map[string]interface{}),
	}

	// Store commit
	vcs.commits[commit.ID] = commit

	// Create default branch
	if vcs.branches[documentID] == nil {
		vcs.branches[documentID] = make(map[string]*Branch)
	}

	vcs.branches[documentID]["main"] = &Branch{
		Name:        "main",
		CommitID:    commit.ID,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
		IsDefault:   true,
		IsProtected: true,
	}

	return commit, nil
}

// CreateCommit creates a new commit
func (vcs *VersionControlService) CreateCommit(documentID, branchName, author, message string, operations []Operation, content string) (*Commit, error) {
	vcs.mu.Lock()
	defer vcs.mu.Unlock()

	// Get current branch
	branch, exists := vcs.branches[documentID][branchName]
	if !exists {
		return nil, fmt.Errorf("branch not found: %s", branchName)
	}

	// Get parent commit
	parentCommit, exists := vcs.commits[branch.CommitID]
	if !exists {
		return nil, fmt.Errorf("parent commit not found: %s", branch.CommitID)
	}

	// Create new commit
	commit := &Commit{
		ID:         vcs.generateCommitID(),
		Message:    message,
		Author:     author,
		Timestamp:  time.Now(),
		ParentIDs:  []string{parentCommit.ID},
		DocumentID: documentID,
		Content:    content,
		Operations: operations,
		Vector:     make(map[string]int),
		Metadata:   make(map[string]interface{}),
	}

	// Copy vector from parent
	for k, v := range parentCommit.Vector {
		commit.Vector[k] = v
	}

	// Update vector with new operations
	for _, op := range operations {
		commit.Vector[op.UserID]++
	}

	// Store commit
	vcs.commits[commit.ID] = commit

	// Update branch
	branch.CommitID = commit.ID
	branch.UpdatedAt = time.Now()

	return commit, nil
}

// GetCommit retrieves a commit by ID
func (vcs *VersionControlService) GetCommit(commitID string) (*Commit, error) {
	vcs.mu.RLock()
	defer vcs.mu.RUnlock()

	commit, exists := vcs.commits[commitID]
	if !exists {
		return nil, fmt.Errorf("commit not found: %s", commitID)
	}

	return commit, nil
}

// GetCommitHistory returns the commit history for a document
func (vcs *VersionControlService) GetCommitHistory(documentID string, limit int) ([]*Commit, error) {
	vcs.mu.RLock()
	defer vcs.mu.RUnlock()

	var commits []*Commit
	for _, commit := range vcs.commits {
		if commit.DocumentID == documentID {
			commits = append(commits, commit)
		}
	}

	// Sort by timestamp (newest first)
	sort.Slice(commits, func(i, j int) bool {
		return commits[i].Timestamp.After(commits[j].Timestamp)
	})

	// Limit results
	if limit > 0 && len(commits) > limit {
		commits = commits[:limit]
	}

	return commits, nil
}

// CreateBranch creates a new branch
func (vcs *VersionControlService) CreateBranch(documentID, branchName, sourceBranch, author string) (*Branch, error) {
	vcs.mu.Lock()
	defer vcs.mu.Unlock()

	// Check if branch already exists
	if vcs.branches[documentID] == nil {
		vcs.branches[documentID] = make(map[string]*Branch)
	}

	if _, exists := vcs.branches[documentID][branchName]; exists {
		return nil, fmt.Errorf("branch already exists: %s", branchName)
	}

	// Get source branch
	sourceBranchObj, exists := vcs.branches[documentID][sourceBranch]
	if !exists {
		return nil, fmt.Errorf("source branch not found: %s", sourceBranch)
	}

	// Create new branch
	branch := &Branch{
		Name:        branchName,
		CommitID:    sourceBranchObj.CommitID,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
		IsDefault:   false,
		IsProtected: false,
	}

	vcs.branches[documentID][branchName] = branch

	return branch, nil
}

// GetBranches returns all branches for a document
func (vcs *VersionControlService) GetBranches(documentID string) ([]*Branch, error) {
	vcs.mu.RLock()
	defer vcs.mu.RUnlock()

	if vcs.branches[documentID] == nil {
		return []*Branch{}, nil
	}

	branches := make([]*Branch, 0, len(vcs.branches[documentID]))
	for _, branch := range vcs.branches[documentID] {
		branches = append(branches, branch)
	}

	// Sort by name
	sort.Slice(branches, func(i, j int) bool {
		return branches[i].Name < branches[j].Name
	})

	return branches, nil
}

// GetBranch returns a specific branch
func (vcs *VersionControlService) GetBranch(documentID, branchName string) (*Branch, error) {
	vcs.mu.RLock()
	defer vcs.mu.RUnlock()

	if vcs.branches[documentID] == nil {
		return nil, fmt.Errorf("document not found: %s", documentID)
	}

	branch, exists := vcs.branches[documentID][branchName]
	if !exists {
		return nil, fmt.Errorf("branch not found: %s", branchName)
	}

	return branch, nil
}

// DeleteBranch deletes a branch
func (vcs *VersionControlService) DeleteBranch(documentID, branchName string) error {
	vcs.mu.Lock()
	defer vcs.mu.Unlock()

	if vcs.branches[documentID] == nil {
		return fmt.Errorf("document not found: %s", documentID)
	}

	branch, exists := vcs.branches[documentID][branchName]
	if !exists {
		return fmt.Errorf("branch not found: %s", branchName)
	}

	if branch.IsDefault {
		return fmt.Errorf("cannot delete default branch")
	}

	if branch.IsProtected {
		return fmt.Errorf("cannot delete protected branch")
	}

	delete(vcs.branches[documentID], branchName)
	return nil
}

// CreateMergeRequest creates a new merge request
func (vcs *VersionControlService) CreateMergeRequest(documentID, title, description, sourceBranch, targetBranch, author string) (*MergeRequest, error) {
	vcs.mu.Lock()
	defer vcs.mu.Unlock()

	// Validate branches
	if _, err := vcs.GetBranch(documentID, sourceBranch); err != nil {
		return nil, fmt.Errorf("source branch not found: %s", sourceBranch)
	}

	if _, err := vcs.GetBranch(documentID, targetBranch); err != nil {
		return nil, fmt.Errorf("target branch not found: %s", targetBranch)
	}

	// Check for conflicts
	conflicts := vcs.detectConflicts(documentID, sourceBranch, targetBranch)

	mergeRequest := &MergeRequest{
		ID:           vcs.generateMergeRequestID(),
		Title:        title,
		Description:  description,
		SourceBranch: sourceBranch,
		TargetBranch: targetBranch,
		Author:       author,
		Status:       "open",
		CreatedAt:    time.Now(),
		UpdatedAt:    time.Now(),
		Conflicts:    conflicts,
	}

	vcs.mergeRequests[mergeRequest.ID] = mergeRequest

	return mergeRequest, nil
}

// GetMergeRequests returns merge requests for a document
func (vcs *VersionControlService) GetMergeRequests(documentID string) ([]*MergeRequest, error) {
	vcs.mu.RLock()
	defer vcs.mu.RUnlock()

	var requests []*MergeRequest
	for _, request := range vcs.mergeRequests {
		// Check if merge request is for this document
		if sourceBranch, err := vcs.GetBranch(documentID, request.SourceBranch); err == nil {
			if sourceBranch != nil {
				requests = append(requests, request)
			}
		}
	}

	// Sort by creation date (newest first)
	sort.Slice(requests, func(i, j int) bool {
		return requests[i].CreatedAt.After(requests[j].CreatedAt)
	})

	return requests, nil
}

// MergeBranches merges source branch into target branch
func (vcs *VersionControlService) MergeBranches(documentID, sourceBranch, targetBranch, author, message string) (*Commit, error) {
	vcs.mu.Lock()
	defer vcs.mu.Unlock()

	// Get branches
	sourceBranchObj, err := vcs.GetBranch(documentID, sourceBranch)
	if err != nil {
		return nil, err
	}

	targetBranchObj, err := vcs.GetBranch(documentID, targetBranch)
	if err != nil {
		return nil, err
	}

	// Get commits
	sourceCommit, err := vcs.GetCommit(sourceBranchObj.CommitID)
	if err != nil {
		return nil, err
	}

	targetCommit, err := vcs.GetCommit(targetBranchObj.CommitID)
	if err != nil {
		return nil, err
	}

	// Create merge commit
	mergeCommit := &Commit{
		ID:         vcs.generateCommitID(),
		Message:    message,
		Author:     author,
		Timestamp:  time.Now(),
		ParentIDs:  []string{targetCommit.ID, sourceCommit.ID},
		DocumentID: documentID,
		Content:    vcs.mergeContent(targetCommit.Content, sourceCommit.Content),
		Operations: append(targetCommit.Operations, sourceCommit.Operations...),
		Vector:     make(map[string]int),
		Metadata:   make(map[string]interface{}),
	}

	// Merge vectors
	for k, v := range targetCommit.Vector {
		mergeCommit.Vector[k] = v
	}
	for k, v := range sourceCommit.Vector {
		if mergeCommit.Vector[k] < v {
			mergeCommit.Vector[k] = v
		}
	}

	// Store merge commit
	vcs.commits[mergeCommit.ID] = mergeCommit

	// Update target branch
	targetBranchObj.CommitID = mergeCommit.ID
	targetBranchObj.UpdatedAt = time.Now()

	return mergeCommit, nil
}

// detectConflicts detects conflicts between branches
func (vcs *VersionControlService) detectConflicts(documentID, sourceBranch, targetBranch string) []string {
	// This is a simplified conflict detection
	// In a real implementation, you would compare the actual content and operations
	return []string{}
}

// mergeContent merges content from two branches
func (vcs *VersionControlService) mergeContent(targetContent, sourceContent string) string {
	// This is a simplified merge
	// In a real implementation, you would use a proper merge algorithm
	if targetContent == sourceContent {
		return targetContent
	}

	// For now, just concatenate with a separator
	return targetContent + "\n--- MERGED ---\n" + sourceContent
}

// GetDiff returns the difference between two commits
func (vcs *VersionControlService) GetDiff(commitID1, commitID2 string) (map[string]interface{}, error) {
	commit1, err := vcs.GetCommit(commitID1)
	if err != nil {
		return nil, err
	}

	commit2, err := vcs.GetCommit(commitID2)
	if err != nil {
		return nil, err
	}

	// Simple diff implementation
	diff := map[string]interface{}{
		"commit1_id":   commit1.ID,
		"commit2_id":   commit2.ID,
		"content_diff": vcs.simpleDiff(commit1.Content, commit2.Content),
		"operations":   len(commit2.Operations) - len(commit1.Operations),
		"timestamp":    commit2.Timestamp.Sub(commit1.Timestamp),
	}

	return diff, nil
}

// simpleDiff performs a simple diff between two strings
func (vcs *VersionControlService) simpleDiff(content1, content2 string) map[string]interface{} {
	return map[string]interface{}{
		"content1_length": len(content1),
		"content2_length": len(content2),
		"length_diff":     len(content2) - len(content1),
		"is_identical":    content1 == content2,
	}
}

// GetDocumentStatistics returns version control statistics for a document
func (vcs *VersionControlService) GetDocumentStatistics(documentID string) (map[string]interface{}, error) {
	vcs.mu.RLock()
	defer vcs.mu.RUnlock()

	// Count commits
	commitCount := 0
	for _, commit := range vcs.commits {
		if commit.DocumentID == documentID {
			commitCount++
		}
	}

	// Count branches
	branchCount := 0
	if branches, exists := vcs.branches[documentID]; exists {
		branchCount = len(branches)
	}

	// Count merge requests
	mergeRequestCount := 0
	for _, request := range vcs.mergeRequests {
		if sourceBranch, err := vcs.GetBranch(documentID, request.SourceBranch); err == nil {
			if sourceBranch != nil {
				mergeRequestCount++
			}
		}
	}

	return map[string]interface{}{
		"document_id":      documentID,
		"total_commits":    commitCount,
		"total_branches":   branchCount,
		"merge_requests":   mergeRequestCount,
		"created_at":       time.Now(), // This would be the document creation time
		"last_commit_time": time.Now(), // This would be the last commit time
	}, nil
}

// generateCommitID generates a unique commit ID
func (vcs *VersionControlService) generateCommitID() string {
	return fmt.Sprintf("commit_%d_%s", time.Now().UnixNano(), fmt.Sprintf("%x", sha256.Sum256([]byte(time.Now().String())))[:8])
}

// generateMergeRequestID generates a unique merge request ID
func (vcs *VersionControlService) generateMergeRequestID() string {
	return fmt.Sprintf("mr_%d_%s", time.Now().UnixNano(), fmt.Sprintf("%x", sha256.Sum256([]byte(time.Now().String())))[:8])
}
