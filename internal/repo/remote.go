package repo

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// RemoteProtocol defines the interface for remote operations
type RemoteProtocol interface {
	ListRefs() ([]Ref, error)
	FetchObjects(ids []string) ([]Object, error)
	PushObjects(objects []Object) error
	GetInfo() (*RemoteInfo, error)
}

// HTTPRemote implements RemoteProtocol over HTTP
type HTTPRemote struct {
	url    string
	auth   AuthMethod
	client *http.Client
}

// AuthMethod represents authentication method
type AuthMethod interface {
	Apply(req *http.Request)
}

// TokenAuth implements token-based authentication
type TokenAuth struct {
	Token string
}

// Apply adds token to request
func (t *TokenAuth) Apply(req *http.Request) {
	req.Header.Set("Authorization", fmt.Sprintf("Bearer %s", t.Token))
}

// BasicAuth implements basic authentication
type BasicAuth struct {
	Username string
	Password string
}

// Apply adds basic auth to request
func (b *BasicAuth) Apply(req *http.Request) {
	req.SetBasicAuth(b.Username, b.Password)
}

// Ref represents a remote reference
type Ref struct {
	Name   string `json:"name"`
	Target string `json:"target"`
	Type   string `json:"type"` // branch, tag
}

// RemoteInfo represents remote repository information
type RemoteInfo struct {
	Name        string    `json:"name"`
	Description string    `json:"description"`
	Version     string    `json:"version"`
	Updated     time.Time `json:"updated"`
}

// NewHTTPRemote creates a new HTTP remote
func NewHTTPRemote(url string, auth AuthMethod) *HTTPRemote {
	return &HTTPRemote{
		url:  url,
		auth: auth,
		client: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

// ListRefs lists all references on the remote
func (r *HTTPRemote) ListRefs() ([]Ref, error) {
	endpoint := fmt.Sprintf("%s/refs", r.url)

	req, err := http.NewRequest("GET", endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	if r.auth != nil {
		r.auth.Apply(req)
	}

	resp, err := r.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to list refs: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("server returned %d: %s", resp.StatusCode, body)
	}

	var refs []Ref
	if err := json.NewDecoder(resp.Body).Decode(&refs); err != nil {
		return nil, fmt.Errorf("failed to decode refs: %w", err)
	}

	return refs, nil
}

// FetchObjects fetches objects from remote
func (r *HTTPRemote) FetchObjects(ids []string) ([]Object, error) {
	endpoint := fmt.Sprintf("%s/objects/batch", r.url)

	request := struct {
		IDs []string `json:"ids"`
	}{
		IDs: ids,
	}

	data, err := json.Marshal(request)
	if err != nil {
		return nil, fmt.Errorf("failed to marshal request: %w", err)
	}

	req, err := http.NewRequest("POST", endpoint, bytes.NewBuffer(data))
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if r.auth != nil {
		r.auth.Apply(req)
	}

	resp, err := r.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch objects: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("server returned %d: %s", resp.StatusCode, body)
	}

	var objects []Object
	if err := json.NewDecoder(resp.Body).Decode(&objects); err != nil {
		return nil, fmt.Errorf("failed to decode objects: %w", err)
	}

	return objects, nil
}

// PushObjects pushes objects to remote
func (r *HTTPRemote) PushObjects(objects []Object) error {
	endpoint := fmt.Sprintf("%s/objects/batch", r.url)

	data, err := json.Marshal(objects)
	if err != nil {
		return fmt.Errorf("failed to marshal objects: %w", err)
	}

	req, err := http.NewRequest("PUT", endpoint, bytes.NewBuffer(data))
	if err != nil {
		return fmt.Errorf("failed to create request: %w", err)
	}

	req.Header.Set("Content-Type", "application/json")
	if r.auth != nil {
		r.auth.Apply(req)
	}

	resp, err := r.client.Do(req)
	if err != nil {
		return fmt.Errorf("failed to push objects: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK && resp.StatusCode != http.StatusCreated {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("server returned %d: %s", resp.StatusCode, body)
	}

	return nil
}

// GetInfo gets remote repository information
func (r *HTTPRemote) GetInfo() (*RemoteInfo, error) {
	endpoint := fmt.Sprintf("%s/info", r.url)

	req, err := http.NewRequest("GET", endpoint, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	if r.auth != nil {
		r.auth.Apply(req)
	}

	resp, err := r.client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to get info: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("server returned %d: %s", resp.StatusCode, body)
	}

	var info RemoteInfo
	if err := json.NewDecoder(resp.Body).Decode(&info); err != nil {
		return nil, fmt.Errorf("failed to decode info: %w", err)
	}

	return &info, nil
}

// Push pushes changes to remote
func Push(local *Repository, remote RemoteProtocol) error {
	logger.Info("Pushing to remote")

	// Get local refs
	localRefs, err := local.RefStore.ListRefs("refs/heads/*")
	if err != nil {
		return fmt.Errorf("failed to list local refs: %w", err)
	}

	// Get remote refs
	remoteRefs, err := remote.ListRefs()
	if err != nil {
		return fmt.Errorf("failed to list remote refs: %w", err)
	}

	// Build ref map
	remoteRefMap := make(map[string]string)
	for _, ref := range remoteRefs {
		remoteRefMap[ref.Name] = ref.Target
	}

	// Collect objects to push
	var objectsToPush []string
	for _, localRef := range localRefs {
		localTarget, err := local.RefStore.ResolveRef(localRef)
		if err != nil {
			logger.Warn("Failed to resolve ref %s: %v", localRef, err)
			continue
		}

		remoteTarget, exists := remoteRefMap[localRef]
		if !exists || remoteTarget != localTarget {
			// Need to push this ref and its objects
			objects, err := collectObjects(local, localTarget, remoteTarget)
			if err != nil {
				logger.Warn("Failed to collect objects for %s: %v", localRef, err)
				continue
			}
			objectsToPush = append(objectsToPush, objects...)
		}
	}

	if len(objectsToPush) == 0 {
		logger.Info("Everything up-to-date")
		return nil
	}

	// Read objects
	var objects []Object
	for _, id := range objectsToPush {
		obj, err := local.ObjectStore.ReadObject(id)
		if err != nil {
			logger.Warn("Failed to read object %s: %v", id, err)
			continue
		}
		objects = append(objects, *obj)
	}

	// Push objects
	if err := remote.PushObjects(objects); err != nil {
		return fmt.Errorf("failed to push objects: %w", err)
	}

	logger.Info("Pushed %d objects", len(objects))
	return nil
}

// Pull pulls changes from remote
func Pull(local *Repository, remote RemoteProtocol) error {
	logger.Info("Pulling from remote")

	// Get remote refs
	remoteRefs, err := remote.ListRefs()
	if err != nil {
		return fmt.Errorf("failed to list remote refs: %w", err)
	}

	// Get local refs
	localRefs, err := local.RefStore.ListRefs("")
	if err != nil {
		return fmt.Errorf("failed to list local refs: %w", err)
	}

	// Build local ref map
	localRefMap := make(map[string]string)
	for _, ref := range localRefs {
		target, _ := local.RefStore.ResolveRef(ref)
		localRefMap[ref] = target
	}

	// Collect objects to fetch
	var objectsToFetch []string
	for _, remoteRef := range remoteRefs {
		localTarget, exists := localRefMap[remoteRef.Name]
		if !exists || localTarget != remoteRef.Target {
			// Need to fetch this ref's objects
			if !local.ObjectStore.ExistsObject(remoteRef.Target) {
				objectsToFetch = append(objectsToFetch, remoteRef.Target)
			}
		}
	}

	if len(objectsToFetch) == 0 {
		logger.Info("Already up-to-date")
		return nil
	}

	// Fetch objects
	objects, err := remote.FetchObjects(objectsToFetch)
	if err != nil {
		return fmt.Errorf("failed to fetch objects: %w", err)
	}

	// Store objects locally
	for _, obj := range objects {
		if _, err := local.ObjectStore.WriteObject(&obj); err != nil {
			logger.Warn("Failed to store object %s: %v", obj.ID, err)
		}
	}

	// Update refs
	for _, remoteRef := range remoteRefs {
		if err := local.RefStore.UpdateRef(remoteRef.Name, remoteRef.Target); err != nil {
			logger.Warn("Failed to update ref %s: %v", remoteRef.Name, err)
		}
	}

	logger.Info("Pulled %d objects", len(objects))
	return nil
}

// collectObjects collects all objects needed to push a ref
func collectObjects(repo *Repository, localTarget, remoteTarget string) ([]string, error) {
	var objects []string

	// Simple implementation - just return the commit object
	// A full implementation would walk the commit graph and tree objects
	if !repo.ObjectStore.ExistsObject(localTarget) {
		return objects, fmt.Errorf("object %s not found", localTarget)
	}

	objects = append(objects, localTarget)

	// TODO: Walk commit history and collect all referenced objects
	// This would include:
	// - Parent commits up to remoteTarget
	// - Tree objects
	// - Blob objects

	return objects, nil
}