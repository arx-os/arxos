package repo

import (
	"bytes"
	"compress/gzip"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ObjectType represents the type of object stored
type ObjectType string

const (
	ObjectTypeCommit   ObjectType = "commit"
	ObjectTypeTree     ObjectType = "tree"
	ObjectTypeBlob     ObjectType = "blob"
	ObjectTypeTag      ObjectType = "tag"
	ObjectTypeSnapshot ObjectType = "snapshot"
)

// Object represents a stored object in the repository
type Object struct {
	ID        string                 `json:"id"`
	Type      ObjectType             `json:"type"`
	Size      int64                  `json:"size"`
	Timestamp time.Time              `json:"timestamp"`
	Content   []byte                 `json:"-"` // Not serialized directly
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// ObjectStore manages content-addressable storage
type ObjectStore struct {
	root string // .arxos/objects
}

// NewObjectStore creates a new object store
func NewObjectStore(repoPath string) *ObjectStore {
	return &ObjectStore{
		root: filepath.Join(repoPath, ".arxos", "objects"),
	}
}

// Initialize creates the object store directory structure
func (s *ObjectStore) Initialize() error {
	// Create objects directory
	if err := os.MkdirAll(s.root, 0755); err != nil {
		return fmt.Errorf("failed to create objects directory: %w", err)
	}

	// Create subdirectories for sharding (00-ff)
	for i := 0; i < 256; i++ {
		dir := filepath.Join(s.root, fmt.Sprintf("%02x", i))
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create shard directory %02x: %w", i, err)
		}
	}

	return nil
}

// WriteObject stores an object and returns its ID
func (s *ObjectStore) WriteObject(obj *Object) (string, error) {
	// Serialize object metadata
	metadata := ObjectMetadata{
		Type:      obj.Type,
		Size:      obj.Size,
		Timestamp: obj.Timestamp,
		Metadata:  obj.Metadata,
	}

	metadataJSON, err := json.Marshal(metadata)
	if err != nil {
		return "", fmt.Errorf("failed to marshal metadata: %w", err)
	}

	// Combine metadata and content
	var buffer bytes.Buffer
	buffer.Write(metadataJSON)
	buffer.Write([]byte("\n---\n"))
	buffer.Write(obj.Content)

	// Calculate hash
	hash := sha256.Sum256(buffer.Bytes())
	id := hex.EncodeToString(hash[:])

	// Determine storage path (shard by first 2 characters)
	dir := filepath.Join(s.root, id[:2])
	path := filepath.Join(dir, id[2:])

	// Check if object already exists
	if _, err := os.Stat(path); err == nil {
		logger.Debug("Object %s already exists", id)
		return id, nil
	}

	// Ensure directory exists
	if err := os.MkdirAll(dir, 0755); err != nil {
		return "", fmt.Errorf("failed to create directory: %w", err)
	}

	// Write compressed object
	if err := s.writeCompressed(path, buffer.Bytes()); err != nil {
		return "", fmt.Errorf("failed to write object: %w", err)
	}

	logger.Debug("Wrote object %s (type=%s, size=%d)", id, obj.Type, obj.Size)
	return id, nil
}

// ReadObject retrieves an object by ID
func (s *ObjectStore) ReadObject(id string) (*Object, error) {
	// Validate ID
	if len(id) < 3 {
		return nil, fmt.Errorf("invalid object ID: %s", id)
	}

	// Determine storage path
	path := filepath.Join(s.root, id[:2], id[2:])

	// Read compressed object
	data, err := s.readCompressed(path)
	if err != nil {
		return nil, fmt.Errorf("failed to read object %s: %w", id, err)
	}

	// Split metadata and content
	parts := bytes.SplitN(data, []byte("\n---\n"), 2)
	if len(parts) != 2 {
		return nil, fmt.Errorf("invalid object format")
	}

	// Parse metadata
	var metadata ObjectMetadata
	if err := json.Unmarshal(parts[0], &metadata); err != nil {
		return nil, fmt.Errorf("failed to parse metadata: %w", err)
	}

	obj := &Object{
		ID:        id,
		Type:      metadata.Type,
		Size:      metadata.Size,
		Timestamp: metadata.Timestamp,
		Content:   parts[1],
		Metadata:  metadata.Metadata,
	}

	logger.Debug("Read object %s (type=%s, size=%d)", id, obj.Type, obj.Size)
	return obj, nil
}

// ExistsObject checks if an object exists
func (s *ObjectStore) ExistsObject(id string) bool {
	if len(id) < 3 {
		return false
	}

	path := filepath.Join(s.root, id[:2], id[2:])
	_, err := os.Stat(path)
	return err == nil
}

// ListObjects returns a list of all object IDs
func (s *ObjectStore) ListObjects() ([]string, error) {
	var objects []string

	err := filepath.Walk(s.root, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() && len(info.Name()) > 0 {
			// Reconstruct object ID from path
			dir := filepath.Base(filepath.Dir(path))
			name := info.Name()
			if len(dir) == 2 { // Shard directory
				objects = append(objects, dir+name)
			}
		}

		return nil
	})

	if err != nil {
		return nil, fmt.Errorf("failed to list objects: %w", err)
	}

	return objects, nil
}

// GarbageCollect removes unreferenced objects
func (s *ObjectStore) GarbageCollect() (int, error) {
	// TODO: Implement mark-and-sweep garbage collection
	// 1. Mark all objects referenced from refs
	// 2. Sweep unreferenced objects
	logger.Warn("Garbage collection not yet implemented")
	return 0, nil
}

// writeCompressed writes gzip-compressed data to a file
func (s *ObjectStore) writeCompressed(path string, data []byte) error {
	file, err := os.Create(path)
	if err != nil {
		return err
	}
	defer file.Close()

	gz := gzip.NewWriter(file)
	defer gz.Close()

	if _, err := gz.Write(data); err != nil {
		return err
	}

	return gz.Close()
}

// readCompressed reads gzip-compressed data from a file
func (s *ObjectStore) readCompressed(path string) ([]byte, error) {
	file, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer file.Close()

	gz, err := gzip.NewReader(file)
	if err != nil {
		return nil, err
	}
	defer gz.Close()

	return io.ReadAll(gz)
}

// ObjectMetadata represents metadata for an object
type ObjectMetadata struct {
	Type      ObjectType             `json:"type"`
	Size      int64                  `json:"size"`
	Timestamp time.Time              `json:"timestamp"`
	Metadata  map[string]interface{} `json:"metadata,omitempty"`
}

// CreateBlob creates a blob object from raw data
func (s *ObjectStore) CreateBlob(data []byte) (string, error) {
	obj := &Object{
		Type:      ObjectTypeBlob,
		Size:      int64(len(data)),
		Timestamp: time.Now(),
		Content:   data,
	}
	return s.WriteObject(obj)
}

// CreateTree creates a tree object from entries
func (s *ObjectStore) CreateTree(entries []TreeEntry) (string, error) {
	data, err := json.Marshal(entries)
	if err != nil {
		return "", fmt.Errorf("failed to marshal tree: %w", err)
	}

	obj := &Object{
		Type:      ObjectTypeTree,
		Size:      int64(len(data)),
		Timestamp: time.Now(),
		Content:   data,
	}
	return s.WriteObject(obj)
}

// TreeEntry represents an entry in a tree object
type TreeEntry struct {
	Name string     `json:"name"`
	Type ObjectType `json:"type"`
	ID   string     `json:"id"`
	Mode string     `json:"mode,omitempty"`
}