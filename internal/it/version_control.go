package it

import (
	"crypto/sha256"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/internal/security"
)

// VersionControlManager manages Git-like operations for room configurations
type VersionControlManager struct {
	mu           sync.RWMutex
	commits      map[string]*RoomCommit
	branches     map[string]map[string]*RoomCommit // branch -> room -> commit
	pullRequests map[string]*PullRequest
	security     *security.VersionControlSecurity
}

// RoomCommit represents a commit in the room configuration history
type RoomCommit struct {
	ID        string                 `json:"id"`
	RoomPath  string                 `json:"room_path"`
	Message   string                 `json:"message"`
	Author    string                 `json:"author"`
	Timestamp time.Time              `json:"timestamp"`
	Changes   []*HardwareChange      `json:"changes"`
	ParentID  string                 `json:"parent_id,omitempty"`
	Hash      string                 `json:"hash"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// HardwareChange represents a change to hardware configuration
type HardwareChange struct {
	Type     string                 `json:"type"` // add, remove, modify, replace
	AssetID  string                 `json:"asset_id,omitempty"`
	OldValue interface{}            `json:"old_value,omitempty"`
	NewValue interface{}            `json:"new_value,omitempty"`
	Position *HardwarePosition      `json:"position,omitempty"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// HardwarePosition represents the physical position of hardware
type HardwarePosition struct {
	X         float64 `json:"x"`
	Y         float64 `json:"y"`
	Z         float64 `json:"z"`
	Rotation  float64 `json:"rotation"`
	MountType string  `json:"mount_type"` // ceiling, wall, floor, desk
}

// PullRequest represents a pull request for room configuration changes
type PullRequest struct {
	ID          string                 `json:"id"`
	RoomPath    string                 `json:"room_path"`
	Title       string                 `json:"title"`
	Description string                 `json:"description"`
	Status      PullRequestStatus      `json:"status"`
	CreatedBy   string                 `json:"created_by"`
	AssignedTo  string                 `json:"assigned_to,omitempty"`
	Changes     []*HardwareChange      `json:"changes"`
	BaseBranch  string                 `json:"base_branch"`
	HeadBranch  string                 `json:"head_branch"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
	MergedAt    *time.Time             `json:"merged_at,omitempty"`
	Metadata    map[string]interface{} `json:"metadata"`
}

// PullRequestStatus represents the status of a pull request
type PullRequestStatus string

const (
	PullRequestStatusOpen     PullRequestStatus = "open"
	PullRequestStatusApproved PullRequestStatus = "approved"
	PullRequestStatusMerged   PullRequestStatus = "merged"
	PullRequestStatusClosed   PullRequestStatus = "closed"
	PullRequestStatusRejected PullRequestStatus = "rejected"
)

// NewVersionControlManager creates a new version control manager
func NewVersionControlManager() *VersionControlManager {
	// Generate encryption key (in production, this should be from secure key management)
	encryptionKey := []byte("arxos-version-control-key-32-bytes")
	
	return &VersionControlManager{
		commits:      make(map[string]*RoomCommit),
		branches:     make(map[string]map[string]*RoomCommit),
		pullRequests: make(map[string]*PullRequest),
		security:     security.NewVersionControlSecurity(encryptionKey),
	}
}

// CreateBranch creates a new branch for a room configuration
func (vcm *VersionControlManager) CreateBranch(roomPath, branchName, template string) error {
	vcm.mu.Lock()
	defer vcm.mu.Unlock()

	// Initialize branch if it doesn't exist
	if vcm.branches[branchName] == nil {
		vcm.branches[branchName] = make(map[string]*RoomCommit)
	}

	// Check if branch already exists for this room
	if _, exists := vcm.branches[branchName][roomPath]; exists {
		return fmt.Errorf("branch %s already exists for room %s", branchName, roomPath)
	}

	// Create initial commit from template
	commit := &RoomCommit{
		ID:        vcm.generateCommitID(),
		RoomPath:  roomPath,
		Message:   fmt.Sprintf("Initial commit from template: %s", template),
		Author:    "system",
		Timestamp: time.Now(),
		Changes:   []*HardwareChange{},
		Hash:      vcm.calculateHash(roomPath, template),
		Metadata: map[string]interface{}{
			"template": template,
			"branch":   branchName,
		},
	}

	vcm.commits[commit.ID] = commit
	vcm.branches[branchName][roomPath] = commit

	logger.Info("Version control: created branch %s for room %s from template %s (commit: %s)",
		branchName, roomPath, template, commit.ID)

	return nil
}

// CommitChanges commits changes to a room configuration
func (vcm *VersionControlManager) CommitChanges(roomPath, branch, message, author string, changes []*HardwareChange) (*RoomCommit, error) {
	vcm.mu.Lock()
	defer vcm.mu.Unlock()

	// Get parent commit
	var parentID string
	if vcm.branches[branch] != nil {
		if parent, exists := vcm.branches[branch][roomPath]; exists {
			parentID = parent.ID
		}
	}

	// Create new commit
	commit := &RoomCommit{
		ID:        vcm.generateCommitID(),
		RoomPath:  roomPath,
		Message:   message,
		Author:    author,
		Timestamp: time.Now(),
		Changes:   changes,
		ParentID:  parentID,
		Hash:      vcm.calculateHash(roomPath, message),
		Metadata: map[string]interface{}{
			"branch": branch,
		},
	}

	// Store commit
	vcm.commits[commit.ID] = commit

	// Update branch
	if vcm.branches[branch] == nil {
		vcm.branches[branch] = make(map[string]*RoomCommit)
	}
	vcm.branches[branch][roomPath] = commit

	logger.Info("Version control: committed changes %s for room %s (branch: %s, author: %s, changes: %d)",
		commit.ID, roomPath, branch, author, len(changes))

	return commit, nil
}

// PushChanges pushes changes to the remote repository (syncs with physical reality)
func (vcm *VersionControlManager) PushChanges(roomPath, branch string) error {
	vcm.mu.RLock()
	defer vcm.mu.RUnlock()

	// Get latest commit for the room
	if vcm.branches[branch] == nil {
		return fmt.Errorf("branch %s does not exist", branch)
	}

	commit, exists := vcm.branches[branch][roomPath]
	if !exists {
		return fmt.Errorf("no commits found for room %s in branch %s", roomPath, branch)
	}

	// This would trigger the n8n workflow for physical deployment
	logger.Info("Version control: pushing changes to physical deployment %s for room %s (branch: %s, changes: %d)",
		commit.ID, roomPath, branch, len(commit.Changes))

	// TODO: Trigger n8n workflow for hardware deployment
	// This would be implemented in the workflow integration

	return nil
}

// PullChanges pulls the latest changes from the remote repository
func (vcm *VersionControlManager) PullChanges(roomPath, branch string) error {
	vcm.mu.Lock()
	defer vcm.mu.Unlock()

	// This would sync with the physical reality
	// For now, we'll just log the operation
	logger.Info("Version control: pulling changes from physical deployment for room %s (branch: %s)",
		roomPath, branch)

	// TODO: Implement sync with physical hardware status
	// This would query the actual hardware and update the configuration

	return nil
}

// GetRoomHistory returns the commit history for a room
func (vcm *VersionControlManager) GetRoomHistory(roomPath, branch string) ([]*RoomCommit, error) {
	vcm.mu.RLock()
	defer vcm.mu.RUnlock()

	var history []*RoomCommit
	currentCommitID := ""

	// Get the latest commit for the room
	if vcm.branches[branch] != nil {
		if commit, exists := vcm.branches[branch][roomPath]; exists {
			currentCommitID = commit.ID
		}
	}

	// Walk the commit history
	for currentCommitID != "" {
		commit, exists := vcm.commits[currentCommitID]
		if !exists {
			break
		}

		history = append(history, commit)
		currentCommitID = commit.ParentID
	}

	return history, nil
}

// RollbackRoom rolls back a room to a specific commit
func (vcm *VersionControlManager) RollbackRoom(roomPath, branch, commitID string) error {
	vcm.mu.Lock()
	defer vcm.mu.Unlock()

	// Verify commit exists
	commit, exists := vcm.commits[commitID]
	if !exists {
		return fmt.Errorf("commit %s not found", commitID)
	}

	// Verify commit is for the correct room
	if commit.RoomPath != roomPath {
		return fmt.Errorf("commit %s is not for room %s", commitID, roomPath)
	}

	// Create rollback commit
	rollbackCommit := &RoomCommit{
		ID:        vcm.generateCommitID(),
		RoomPath:  roomPath,
		Message:   fmt.Sprintf("Rollback to commit %s", commitID),
		Author:    "system",
		Timestamp: time.Now(),
		Changes:   vcm.calculateRollbackChanges(commit),
		ParentID:  vcm.branches[branch][roomPath].ID,
		Hash:      vcm.calculateHash(roomPath, fmt.Sprintf("rollback-%s", commitID)),
		Metadata: map[string]interface{}{
			"branch":      branch,
			"rollback_to": commitID,
		},
	}

	// Store rollback commit
	vcm.commits[rollbackCommit.ID] = rollbackCommit
	vcm.branches[branch][roomPath] = rollbackCommit

	logger.Info("Version control: rolled back room %s (branch: %s, rollback_to: %s, rollback_commit: %s)",
		roomPath, branch, commitID, rollbackCommit.ID)

	return nil
}

// CreatePullRequest creates a pull request for room configuration changes
func (vcm *VersionControlManager) CreatePullRequest(roomPath, title, description, createdBy, baseBranch, headBranch string) (*PullRequest, error) {
	vcm.mu.Lock()
	defer vcm.mu.Unlock()

	// Generate PR ID
	prID := vcm.generatePRID()

	// Create pull request
	pr := &PullRequest{
		ID:          prID,
		RoomPath:    roomPath,
		Title:       title,
		Description: description,
		Status:      PullRequestStatusOpen,
		CreatedBy:   createdBy,
		BaseBranch:  baseBranch,
		HeadBranch:  headBranch,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
		Metadata:    make(map[string]interface{}),
	}

	// Calculate changes between branches
	changes, err := vcm.calculateBranchChanges(roomPath, baseBranch, headBranch)
	if err != nil {
		return nil, fmt.Errorf("failed to calculate branch changes: %w", err)
	}
	pr.Changes = changes

	// Store pull request
	vcm.pullRequests[prID] = pr

	logger.Info("Version control: created pull request %s for room %s (title: %s, created_by: %s, base: %s, head: %s)",
		prID, roomPath, title, createdBy, baseBranch, headBranch)

	return pr, nil
}

// ReviewPullRequest reviews a pull request
func (vcm *VersionControlManager) ReviewPullRequest(prID string, approved bool, reviewer string) error {
	vcm.mu.Lock()
	defer vcm.mu.Unlock()

	pr, exists := vcm.pullRequests[prID]
	if !exists {
		return fmt.Errorf("pull request %s not found", prID)
	}

	if approved {
		pr.Status = PullRequestStatusApproved
	} else {
		pr.Status = PullRequestStatusRejected
	}

	pr.AssignedTo = reviewer
	pr.UpdatedAt = time.Now()

	logger.Info("Version control: reviewed pull request %s (approved: %t, reviewer: %s)",
		prID, approved, reviewer)

	return nil
}

// MergePullRequest merges a pull request
func (vcm *VersionControlManager) MergePullRequest(prID string, deploy bool) error {
	vcm.mu.Lock()
	defer vcm.mu.Unlock()

	pr, exists := vcm.pullRequests[prID]
	if !exists {
		return fmt.Errorf("pull request %s not found", prID)
	}

	if pr.Status != PullRequestStatusApproved {
		return fmt.Errorf("pull request %s is not approved", prID)
	}

	// Merge the changes
	pr.Status = PullRequestStatusMerged
	pr.MergedAt = &time.Time{}
	*pr.MergedAt = time.Now()
	pr.UpdatedAt = time.Now()

	// If deploy is true, trigger physical deployment
	if deploy {
		logger.Info("Version control: merging pull request %s with deployment for room %s",
			prID, pr.RoomPath)
		// TODO: Trigger n8n workflow for hardware deployment
	}

	logger.Info("Version control: merged pull request %s for room %s (deploy: %t)",
		prID, pr.RoomPath, deploy)

	return nil
}

// Helper methods

func (vcm *VersionControlManager) generateCommitID() string {
	return fmt.Sprintf("commit_%d", time.Now().UnixNano())
}

func (vcm *VersionControlManager) generatePRID() string {
	return fmt.Sprintf("pr_%d", time.Now().UnixNano())
}

func (vcm *VersionControlManager) calculateHash(roomPath, content string) string {
	h := sha256.New()
	h.Write([]byte(roomPath + content))
	return fmt.Sprintf("%x", h.Sum(nil))[:16]
}

func (vcm *VersionControlManager) calculateRollbackChanges(commit *RoomCommit) []*HardwareChange {
	// Calculate the inverse changes needed to rollback
	var rollbackChanges []*HardwareChange

	for _, change := range commit.Changes {
		rollbackChange := &HardwareChange{
			Type:     change.Type,
			AssetID:  change.AssetID,
			OldValue: change.NewValue,
			NewValue: change.OldValue,
			Position: change.Position,
			Metadata: change.Metadata,
		}

		// Invert the change type
		switch change.Type {
		case "add":
			rollbackChange.Type = "remove"
		case "remove":
			rollbackChange.Type = "add"
		case "modify", "replace":
			// Keep the same type but swap old/new values
		}

		rollbackChanges = append(rollbackChanges, rollbackChange)
	}

	return rollbackChanges
}

func (vcm *VersionControlManager) calculateBranchChanges(roomPath, baseBranch, headBranch string) ([]*HardwareChange, error) {
	// Get commits from both branches
	baseCommits, err := vcm.GetRoomHistory(roomPath, baseBranch)
	if err != nil {
		return nil, err
	}

	headCommits, err := vcm.GetRoomHistory(roomPath, headBranch)
	if err != nil {
		return nil, err
	}

	// Find the common ancestor
	commonAncestor := vcm.findCommonAncestor(baseCommits, headCommits)

	// Calculate changes from common ancestor to head
	var changes []*HardwareChange
	for _, commit := range headCommits {
		if commit.ID == commonAncestor {
			break
		}
		changes = append(changes, commit.Changes...)
	}

	return changes, nil
}

func (vcm *VersionControlManager) findCommonAncestor(baseCommits, headCommits []*RoomCommit) string {
	// Simple implementation - find the first common commit
	baseMap := make(map[string]bool)
	for _, commit := range baseCommits {
		baseMap[commit.ID] = true
	}

	for _, commit := range headCommits {
		if baseMap[commit.ID] {
			return commit.ID
		}
	}

	return ""
}

// Security Methods

// SetUserPermissions sets permissions for a user
func (vcm *VersionControlManager) SetUserPermissions(userID string, permissions *security.UserPermissions) error {
	return vcm.security.SetUserPermissions(userID, permissions)
}

// GetUserPermissions gets permissions for a user
func (vcm *VersionControlManager) GetUserPermissions(userID string) (*security.UserPermissions, error) {
	return vcm.security.GetUserPermissions(userID)
}

// GenerateSignatureKey generates a new signature key for a user
func (vcm *VersionControlManager) GenerateSignatureKey(userID string) (*security.SignatureKey, error) {
	return vcm.security.GenerateSignatureKey(userID)
}

// SignCommit signs a commit with the user's private key
func (vcm *VersionControlManager) SignCommit(commitID, userID string, commitData []byte) (*security.CommitSignature, error) {
	return vcm.security.SignCommit(commitID, userID, commitData)
}

// VerifyCommitSignature verifies a commit signature
func (vcm *VersionControlManager) VerifyCommitSignature(signature *security.CommitSignature, commitData []byte) error {
	return vcm.security.VerifyCommitSignature(signature, commitData)
}

// EncryptSensitiveData encrypts sensitive configuration data
func (vcm *VersionControlManager) EncryptSensitiveData(data []byte) ([]byte, error) {
	return vcm.security.EncryptSensitiveData(data)
}

// DecryptSensitiveData decrypts sensitive configuration data
func (vcm *VersionControlManager) DecryptSensitiveData(encryptedData []byte) ([]byte, error) {
	return vcm.security.DecryptSensitiveData(encryptedData)
}

// GetAuditLogs retrieves audit logs with filtering
func (vcm *VersionControlManager) GetAuditLogs(filter *security.AuditLogFilter) ([]*security.AuditLogEntry, error) {
	return vcm.security.GetAuditLogs(filter)
}

// GetSecurityManager returns the security manager
func (vcm *VersionControlManager) GetSecurityManager() *security.VersionControlSecurity {
	return vcm.security
}
