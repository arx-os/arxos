package repo

import (
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// RefStore manages references (branches, tags, HEAD)
type RefStore struct {
	root string // .arxos/refs
}

// NewRefStore creates a new reference store
func NewRefStore(repoPath string) *RefStore {
	return &RefStore{
		root: filepath.Join(repoPath, ".arxos"),
	}
}

// Initialize creates the refs directory structure
func (r *RefStore) Initialize() error {
	// Create refs directories
	dirs := []string{
		filepath.Join(r.root, "refs"),
		filepath.Join(r.root, "refs", "heads"),
		filepath.Join(r.root, "refs", "tags"),
		filepath.Join(r.root, "refs", "remotes"),
	}

	for _, dir := range dirs {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	// Create HEAD pointing to main
	headPath := filepath.Join(r.root, "HEAD")
	if err := os.WriteFile(headPath, []byte("ref: refs/heads/main\n"), 0644); err != nil {
		return fmt.Errorf("failed to create HEAD: %w", err)
	}

	return nil
}

// ReadRef reads a reference value
func (r *RefStore) ReadRef(ref string) (string, error) {
	path := r.refPath(ref)

	data, err := os.ReadFile(path)
	if err != nil {
		return "", fmt.Errorf("failed to read ref %s: %w", ref, err)
	}

	value := strings.TrimSpace(string(data))
	logger.Debug("Read ref %s: %s", ref, value)
	return value, nil
}

// UpdateRef updates a reference to point to a new value
func (r *RefStore) UpdateRef(ref, value string) error {
	path := r.refPath(ref)

	// Ensure parent directory exists
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("failed to create directory: %w", err)
	}

	// Write ref value
	if err := os.WriteFile(path, []byte(value+"\n"), 0644); err != nil {
		return fmt.Errorf("failed to write ref %s: %w", ref, err)
	}

	// Log ref update
	if err := r.logRefUpdate(ref, value); err != nil {
		logger.Warn("Failed to log ref update: %v", err)
	}

	logger.Debug("Updated ref %s to %s", ref, value)
	return nil
}

// DeleteRef deletes a reference
func (r *RefStore) DeleteRef(ref string) error {
	path := r.refPath(ref)

	if err := os.Remove(path); err != nil {
		if os.IsNotExist(err) {
			return fmt.Errorf("ref %s does not exist", ref)
		}
		return fmt.Errorf("failed to delete ref %s: %w", ref, err)
	}

	logger.Debug("Deleted ref %s", ref)
	return nil
}

// ListRefs returns all references matching a pattern
func (r *RefStore) ListRefs(pattern string) ([]string, error) {
	var refs []string

	refsDir := filepath.Join(r.root, "refs")
	err := filepath.Walk(refsDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() {
			// Get relative path from refs directory
			relPath, err := filepath.Rel(r.root, path)
			if err != nil {
				return err
			}

			// Check if matches pattern
			if pattern == "" || matchesPattern(relPath, pattern) {
				refs = append(refs, relPath)
			}
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to list refs: %w", err)
	}

	return refs, nil
}

// ResolveRef resolves a reference to its final value (following symbolic refs)
func (r *RefStore) ResolveRef(ref string) (string, error) {
	maxDepth := 10 // Prevent infinite loops
	currentRef := ref

	for i := 0; i < maxDepth; i++ {
		value, err := r.ReadRef(currentRef)
		if err != nil {
			return "", err
		}

		// Check if it's a symbolic ref
		if strings.HasPrefix(value, "ref: ") {
			currentRef = strings.TrimPrefix(value, "ref: ")
			continue
		}

		// It's a direct object ID
		return value, nil
	}

	return "", fmt.Errorf("too many symbolic ref levels")
}

// CreateBranch creates a new branch
func (r *RefStore) CreateBranch(name string, target string) error {
	ref := fmt.Sprintf("refs/heads/%s", name)

	// Check if branch already exists
	if r.RefExists(ref) {
		return fmt.Errorf("branch %s already exists", name)
	}

	// Resolve target if it's a ref
	resolved, err := r.ResolveRef(target)
	if err != nil {
		// Target might be a direct object ID
		resolved = target
	}

	return r.UpdateRef(ref, resolved)
}

// DeleteBranch deletes a branch
func (r *RefStore) DeleteBranch(name string) error {
	ref := fmt.Sprintf("refs/heads/%s", name)
	return r.DeleteRef(ref)
}

// CreateTag creates a new tag
func (r *RefStore) CreateTag(name string, target string, message string) error {
	ref := fmt.Sprintf("refs/tags/%s", name)

	// Check if tag already exists
	if r.RefExists(ref) {
		return fmt.Errorf("tag %s already exists", name)
	}

	// For lightweight tags, just point to the target
	// For annotated tags, we would create a tag object
	resolved, err := r.ResolveRef(target)
	if err != nil {
		resolved = target
	}

	return r.UpdateRef(ref, resolved)
}

// DeleteTag deletes a tag
func (r *RefStore) DeleteTag(name string) error {
	ref := fmt.Sprintf("refs/tags/%s", name)
	return r.DeleteRef(ref)
}

// RefExists checks if a reference exists
func (r *RefStore) RefExists(ref string) bool {
	path := r.refPath(ref)
	_, err := os.Stat(path)
	return err == nil
}

// GetCurrentBranch returns the name of the current branch
func (r *RefStore) GetCurrentBranch() (string, error) {
	head, err := r.ReadRef("HEAD")
	if err != nil {
		return "", err
	}

	if !strings.HasPrefix(head, "ref: refs/heads/") {
		return "", fmt.Errorf("HEAD is detached")
	}

	branch := strings.TrimPrefix(head, "ref: refs/heads/")
	return branch, nil
}

// SetCurrentBranch switches to a different branch
func (r *RefStore) SetCurrentBranch(name string) error {
	ref := fmt.Sprintf("refs/heads/%s", name)

	// Check if branch exists
	if !r.RefExists(ref) {
		return fmt.Errorf("branch %s does not exist", name)
	}

	// Update HEAD to point to the branch
	return r.UpdateRef("HEAD", fmt.Sprintf("ref: %s", ref))
}

// Helper functions

// refPath returns the filesystem path for a reference
func (r *RefStore) refPath(ref string) string {
	return filepath.Join(r.root, ref)
}

// logRefUpdate logs a reference update to the reflog
func (r *RefStore) logRefUpdate(ref, value string) error {
	logDir := filepath.Join(r.root, "logs")
	if err := os.MkdirAll(logDir, 0755); err != nil {
		return err
	}

	logFile := filepath.Join(logDir, ref)
	logDir = filepath.Dir(logFile)
	if err := os.MkdirAll(logDir, 0755); err != nil {
		return err
	}

	// Append log entry
	// Format: old_value new_value author timestamp message
	entry := fmt.Sprintf("%s %s %d update: %s\n",
		"0000000000000000000000000000000000000000", // TODO: track old value
		value,
		time.Now().Unix(),
		ref,
	)

	f, err := os.OpenFile(logFile, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0644)
	if err != nil {
		return err
	}
	defer f.Close()

	_, err = f.WriteString(entry)
	return err
}

// matchesPattern checks if a path matches a pattern
func matchesPattern(path, pattern string) bool {
	// Simple pattern matching (could be enhanced with glob patterns)
	if pattern == "" {
		return true
	}

	if strings.Contains(pattern, "*") {
		// Convert simple wildcards to work with filepath.Match
		matched, _ := filepath.Match(pattern, path)
		return matched
	}

	return strings.Contains(path, pattern)
}
