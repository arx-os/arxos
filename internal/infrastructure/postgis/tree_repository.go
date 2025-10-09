package postgis

import (
	"context"
	"fmt"

	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/jmoiron/sqlx"
)

// TreeRepository implements building.TreeRepository using the object store
// Trees are stored as objects with type ObjectTypeTree
type TreeRepository struct {
	objectRepo *ObjectRepository
}

// NewTreeRepository creates a new tree repository
func NewTreeRepository(objectRepo *ObjectRepository) *TreeRepository {
	return &TreeRepository{
		objectRepo: objectRepo,
	}
}

// Store stores a tree and returns its hash
func (r *TreeRepository) Store(ctxAny any, tree *building.Tree) (string, error) {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return "", fmt.Errorf("invalid context type")
	}

	// Calculate tree hash
	tree.Hash = building.CalculateTreeHash(tree)
	tree.Type = building.ObjectTypeTree

	// Serialize tree to bytes
	contents, err := building.SerializeObject(tree)
	if err != nil {
		return "", fmt.Errorf("failed to serialize tree: %w", err)
	}

	// Calculate total size
	tree.Size = int64(len(contents))

	// Create object
	obj := &building.Object{
		Hash:     tree.Hash,
		Type:     building.ObjectTypeTree,
		Size:     tree.Size,
		Contents: contents,
	}

	// Store as object
	hash, err := r.objectRepo.Store(ctx, obj)
	if err != nil {
		return "", fmt.Errorf("failed to store tree object: %w", err)
	}

	return hash, nil
}

// Load loads a tree by hash
func (r *TreeRepository) Load(ctxAny any, hash string) (*building.Tree, error) {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return nil, fmt.Errorf("invalid context type")
	}

	// Load object
	obj, err := r.objectRepo.Load(ctx, hash)
	if err != nil {
		return nil, fmt.Errorf("failed to load tree object: %w", err)
	}

	// Verify type
	if obj.Type != building.ObjectTypeTree {
		return nil, fmt.Errorf("object is not a tree: %s (type: %s)", hash, obj.Type)
	}

	// Deserialize tree
	var tree building.Tree
	if err := building.DeserializeObject(obj.Contents, &tree); err != nil {
		return nil, fmt.Errorf("failed to deserialize tree: %w", err)
	}

	return &tree, nil
}

// Exists checks if a tree exists
func (r *TreeRepository) Exists(ctxAny any, hash string) (bool, error) {
	ctx, ok := ctxAny.(context.Context)
	if !ok {
		return false, fmt.Errorf("invalid context type")
	}

	return r.objectRepo.Exists(ctx, hash)
}

// Helper function to create tree repository from database connection
func NewTreeRepositoryFromDB(db *sqlx.DB, storePath string) *TreeRepository {
	objectRepo := NewObjectRepository(db, storePath)
	return NewTreeRepository(objectRepo)
}
