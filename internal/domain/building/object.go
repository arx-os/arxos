package building

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"time"
)

// ObjectType represents the type of object in the content-addressable store
type ObjectType string

const (
	ObjectTypeBlob     ObjectType = "blob"     // File contents
	ObjectTypeTree     ObjectType = "tree"     // Directory structure
	ObjectTypeSnapshot ObjectType = "snapshot" // Building state snapshot
	ObjectTypeVersion  ObjectType = "version"  // Version metadata
)

// Object represents a content-addressable object in the version control system
// Objects are stored by their SHA-256 hash
type Object struct {
	Hash       string     `json:"hash"`       // SHA-256 hash of contents
	Type       ObjectType `json:"type"`       // Object type
	Size       int64      `json:"size"`       // Size in bytes
	Contents   []byte     `json:"contents"`   // Actual data (for small objects < 1KB)
	StorePath  string     `json:"store_path"` // File path (for large objects)
	Compressed bool       `json:"compressed"` // Whether contents are compressed
	CreatedAt  time.Time  `json:"created_at"` // When object was created
	RefCount   int        `json:"ref_count"`  // Reference count for GC
}

// Tree represents a tree object (similar to Git trees)
// Trees organize objects into a hierarchical structure
type Tree struct {
	Type    ObjectType  `json:"type"`    // Always ObjectTypeTree
	Hash    string      `json:"hash"`    // Content hash
	Entries []TreeEntry `json:"entries"` // Tree entries
	Size    int64       `json:"size"`    // Total size
}

// TreeEntry represents an entry in a tree
type TreeEntry struct {
	Type ObjectType `json:"type"` // blob or tree
	Name string     `json:"name"` // Entry name
	Hash string     `json:"hash"` // Content hash
	Size int64      `json:"size"` // Size in bytes
	Mode string     `json:"mode"` // File mode (for compatibility)
}

// Snapshot represents a complete spatial structure state at a point in time
// Snapshots use Merkle trees for efficient comparison
// Domain-agnostic: works for buildings, ships, warehouses, or any spatial hierarchy
type Snapshot struct {
	Hash           string           `json:"hash"`            // Content hash of snapshot
	RepositoryID   string           `json:"repository_id"`   // Which spatial repository
	SpaceTree      string           `json:"space_tree"`      // Hash of spatial hierarchy tree (was: building_tree)
	ItemTree       string           `json:"item_tree"`       // Hash of items tree (was: equipment_tree)
	SpatialTree    string           `json:"spatial_tree"`    // Hash of spatial data tree (AR anchors, point clouds)
	FilesTree      string           `json:"files_tree"`      // Hash of files tree (IFC, photos, documents)
	OperationsTree string           `json:"operations_tree"` // Hash of operations tree (BAS, sensors)
	Metadata       SnapshotMetadata `json:"metadata"`        // Additional metadata
	CreatedAt      time.Time        `json:"created_at"`      // Snapshot creation time
}

// SnapshotMetadata provides high-level statistics about a snapshot
// Counts are domain-agnostic (spaces and items, not buildings and equipment)
type SnapshotMetadata struct {
	SpaceCount int               `json:"space_count"` // Number of spaces (buildings, floors, rooms, decks, etc.)
	ItemCount  int               `json:"item_count"`  // Number of items (equipment, cargo, etc.)
	FileCount  int               `json:"file_count"`  // Number of files
	TotalSize  int64             `json:"total_size"`  // Total data size
	Checksums  map[string]string `json:"checksums"`   // Component checksums
}

// SnapshotDiff represents the high-level differences between two snapshots
type SnapshotDiff struct {
	FromHash          string `json:"from_hash"`
	ToHash            string `json:"to_hash"`
	SpaceChanged      bool   `json:"space_changed"`      // Spatial hierarchy changed
	ItemChanged       bool   `json:"item_changed"`       // Items changed
	SpatialChanged    bool   `json:"spatial_changed"`    // AR anchors/point clouds changed
	FilesChanged      bool   `json:"files_changed"`      // Files changed
	OperationsChanged bool   `json:"operations_changed"` // BAS/sensor data changed
}

// ObjectRepository defines the contract for object storage operations
type ObjectRepository interface {
	// Store an object and return its hash
	Store(ctx any, obj *Object) (string, error)

	// Load an object by hash
	Load(ctx any, hash string) (*Object, error)

	// Check if object exists
	Exists(ctx any, hash string) (bool, error)

	// Increment reference count
	IncrementRef(ctx any, hash string) error

	// Decrement reference count
	DecrementRef(ctx any, hash string) error

	// List objects by type
	ListByType(ctx any, objType ObjectType, limit, offset int) ([]*Object, error)

	// Delete unreferenced objects (garbage collection)
	DeleteUnreferenced(ctx any, olderThan time.Time) (int, error)
}

// SnapshotRepository defines the contract for snapshot operations
type SnapshotRepository interface {
	// Create a new snapshot
	Create(ctx any, snapshot *Snapshot) error

	// Get snapshot by hash
	GetByHash(ctx any, hash string) (*Snapshot, error)

	// List snapshots for a repository
	ListByRepository(ctx any, repoID string) ([]*Snapshot, error)

	// Get latest snapshot for a repository
	GetLatest(ctx any, repoID string) (*Snapshot, error)

	// Delete snapshot
	Delete(ctx any, hash string) error
}

// TreeRepository defines the contract for tree operations
type TreeRepository interface {
	// Store a tree and return its hash
	Store(ctx any, tree *Tree) (string, error)

	// Load a tree by hash
	Load(ctx any, hash string) (*Tree, error)

	// Check if tree exists
	Exists(ctx any, hash string) (bool, error)
}

// Hash calculation functions

// CalculateObjectHash calculates the SHA-256 hash for an object
func CalculateObjectHash(objType ObjectType, size int64, contents []byte) string {
	hasher := sha256.New()

	// Hash format: type + size + contents
	hasher.Write([]byte(objType))
	hasher.Write([]byte(fmt.Sprintf("%d", size)))
	hasher.Write(contents)

	return hex.EncodeToString(hasher.Sum(nil))
}

// CalculateTreeHash calculates the SHA-256 hash for a tree
func CalculateTreeHash(tree *Tree) string {
	hasher := sha256.New()

	// Hash format: type + entries (sorted by name)
	hasher.Write([]byte(tree.Type))

	for _, entry := range tree.Entries {
		hasher.Write([]byte(entry.Type))
		hasher.Write([]byte(entry.Name))
		hasher.Write([]byte(entry.Hash))
	}

	return hex.EncodeToString(hasher.Sum(nil))
}

// CalculateSnapshotHash calculates the SHA-256 hash for a snapshot
func CalculateSnapshotHash(snapshot *Snapshot) string {
	hasher := sha256.New()

	// Hash format: repository_id + all tree hashes
	hasher.Write([]byte(snapshot.RepositoryID))
	hasher.Write([]byte(snapshot.SpaceTree))
	hasher.Write([]byte(snapshot.ItemTree))
	hasher.Write([]byte(snapshot.SpatialTree))
	hasher.Write([]byte(snapshot.FilesTree))
	hasher.Write([]byte(snapshot.OperationsTree))

	return hex.EncodeToString(hasher.Sum(nil))
}

// SerializeObject serializes an object to bytes (for storage)
func SerializeObject(obj any) ([]byte, error) {
	return json.Marshal(obj)
}

// DeserializeObject deserializes bytes to an object
func DeserializeObject(data []byte, obj any) error {
	return json.Unmarshal(data, obj)
}
