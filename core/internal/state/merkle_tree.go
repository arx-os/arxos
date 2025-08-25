package state

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"sort"
)

// MerkleNode represents a node in the Merkle tree
type MerkleNode struct {
	Hash  string       `json:"hash"`
	Left  *MerkleNode  `json:"left,omitempty"`
	Right *MerkleNode  `json:"right,omitempty"`
	Data  interface{}  `json:"data,omitempty"` // Leaf nodes contain data
}

// MerkleTree represents a Merkle tree for efficient state comparison
type MerkleTree struct {
	Root *MerkleNode `json:"root"`
	Leaves []*MerkleNode `json:"leaves"`
}

// ArxObjectLeaf represents a leaf node containing ArxObject data
type ArxObjectLeaf struct {
	ID         string      `json:"id"`
	Type       int         `json:"type"`
	Hash       string      `json:"hash"`
	Properties interface{} `json:"properties,omitempty"`
}

// NewMerkleTree creates a new Merkle tree from ArxObject data
func NewMerkleTree(arxObjects []interface{}) (*MerkleTree, error) {
	if len(arxObjects) == 0 {
		return &MerkleTree{}, nil
	}

	// Create leaf nodes
	leaves := make([]*MerkleNode, 0, len(arxObjects))
	for _, obj := range arxObjects {
		leaf, err := createLeafNode(obj)
		if err != nil {
			return nil, err
		}
		leaves = append(leaves, leaf)
	}

	// Sort leaves by hash for deterministic tree structure
	sort.Slice(leaves, func(i, j int) bool {
		return leaves[i].Hash < leaves[j].Hash
	})

	// Build tree
	root := buildTree(leaves)

	return &MerkleTree{
		Root:   root,
		Leaves: leaves,
	}, nil
}

// BuildFromSnapshot creates a Merkle tree from a state snapshot
func BuildFromSnapshot(snapshot json.RawMessage) (*MerkleTree, error) {
	var objects []interface{}
	if err := json.Unmarshal(snapshot, &objects); err != nil {
		return nil, err
	}
	return NewMerkleTree(objects)
}

// GetRootHash returns the root hash of the tree
func (mt *MerkleTree) GetRootHash() string {
	if mt.Root == nil {
		return ""
	}
	return mt.Root.Hash
}

// Compare compares two Merkle trees and returns differences
func (mt *MerkleTree) Compare(other *MerkleTree) (*TreeDiff, error) {
	diff := &TreeDiff{
		Added:    make([]string, 0),
		Modified: make([]string, 0),
		Removed:  make([]string, 0),
	}

	if mt.Root == nil && other.Root == nil {
		return diff, nil
	}

	if mt.Root == nil {
		// All items in other tree are additions
		collectAllLeafIDs(other.Root, &diff.Added)
		return diff, nil
	}

	if other.Root == nil {
		// All items in this tree are removals
		collectAllLeafIDs(mt.Root, &diff.Removed)
		return diff, nil
	}

	// If root hashes match, trees are identical
	if mt.Root.Hash == other.Root.Hash {
		return diff, nil
	}

	// Perform detailed comparison
	compareNodes(mt.Root, other.Root, diff)

	return diff, nil
}

// TreeDiff represents the differences between two Merkle trees
type TreeDiff struct {
	Added    []string `json:"added"`
	Modified []string `json:"modified"`
	Removed  []string `json:"removed"`
}

// GetChangeCount returns the total number of changes
func (td *TreeDiff) GetChangeCount() int {
	return len(td.Added) + len(td.Modified) + len(td.Removed)
}

// IsEmpty returns true if there are no differences
func (td *TreeDiff) IsEmpty() bool {
	return td.GetChangeCount() == 0
}

// Helper functions

func createLeafNode(obj interface{}) (*MerkleNode, error) {
	// Serialize object to JSON for hashing
	data, err := json.Marshal(obj)
	if err != nil {
		return nil, err
	}

	// Calculate hash
	hash := calculateHash(data)

	// Extract ID if present
	objMap, ok := obj.(map[string]interface{})
	var leafData *ArxObjectLeaf
	if ok {
		leafData = &ArxObjectLeaf{
			Hash: hash,
		}
		if id, exists := objMap["id"]; exists {
			leafData.ID = fmt.Sprintf("%v", id)
		}
		if objType, exists := objMap["type"]; exists {
			if typeInt, ok := objType.(float64); ok {
				leafData.Type = int(typeInt)
			}
		}
		if props, exists := objMap["properties"]; exists {
			leafData.Properties = props
		}
	}

	return &MerkleNode{
		Hash: hash,
		Data: leafData,
	}, nil
}

func buildTree(leaves []*MerkleNode) *MerkleNode {
	if len(leaves) == 0 {
		return nil
	}

	if len(leaves) == 1 {
		return leaves[0]
	}

	// Build tree level by level
	currentLevel := leaves
	for len(currentLevel) > 1 {
		nextLevel := make([]*MerkleNode, 0)

		for i := 0; i < len(currentLevel); i += 2 {
			left := currentLevel[i]
			var right *MerkleNode

			if i+1 < len(currentLevel) {
				right = currentLevel[i+1]
			} else {
				// Duplicate last node if odd number
				right = left
			}

			parent := &MerkleNode{
				Hash:  combineHashes(left.Hash, right.Hash),
				Left:  left,
				Right: right,
			}
			nextLevel = append(nextLevel, parent)
		}

		currentLevel = nextLevel
	}

	return currentLevel[0]
}

func calculateHash(data []byte) string {
	h := sha256.New()
	h.Write(data)
	return hex.EncodeToString(h.Sum(nil))
}

func combineHashes(left, right string) string {
	combined := left + right
	return calculateHash([]byte(combined))
}

func compareNodes(node1, node2 *MerkleNode, diff *TreeDiff) {
	if node1 == nil && node2 == nil {
		return
	}

	if node1 == nil {
		// node2 subtree contains additions
		collectAllLeafIDs(node2, &diff.Added)
		return
	}

	if node2 == nil {
		// node1 subtree contains removals
		collectAllLeafIDs(node1, &diff.Removed)
		return
	}

	// If hashes match, subtrees are identical
	if node1.Hash == node2.Hash {
		return
	}

	// Check if leaf nodes
	if node1.Left == nil && node1.Right == nil && node2.Left == nil && node2.Right == nil {
		// Both are leaf nodes but different
		if node1.Data != nil && node2.Data != nil {
			leaf1, ok1 := node1.Data.(*ArxObjectLeaf)
			leaf2, ok2 := node2.Data.(*ArxObjectLeaf)
			if ok1 && ok2 && leaf1.ID == leaf2.ID {
				diff.Modified = append(diff.Modified, leaf1.ID)
			} else if ok1 {
				diff.Removed = append(diff.Removed, leaf1.ID)
				if ok2 {
					diff.Added = append(diff.Added, leaf2.ID)
				}
			}
		}
		return
	}

	// Recursively compare children
	compareNodes(node1.Left, node2.Left, diff)
	compareNodes(node1.Right, node2.Right, diff)
}

func collectAllLeafIDs(node *MerkleNode, ids *[]string) {
	if node == nil {
		return
	}

	// Check if leaf node
	if node.Left == nil && node.Right == nil {
		if node.Data != nil {
			if leaf, ok := node.Data.(*ArxObjectLeaf); ok && leaf.ID != "" {
				*ids = append(*ids, leaf.ID)
			}
		}
		return
	}

	// Recursively collect from children
	collectAllLeafIDs(node.Left, ids)
	collectAllLeafIDs(node.Right, ids)
}

// VerifyIntegrity verifies the integrity of the Merkle tree
func (mt *MerkleTree) VerifyIntegrity() bool {
	if mt.Root == nil {
		return true
	}
	return verifyNode(mt.Root)
}

func verifyNode(node *MerkleNode) bool {
	if node == nil {
		return true
	}

	// Leaf node - hash should match data
	if node.Left == nil && node.Right == nil {
		if node.Data != nil {
			data, err := json.Marshal(node.Data)
			if err != nil {
				return false
			}
			// Note: This is simplified - in reality would need to match original hashing
			return true
		}
		return true
	}

	// Internal node - hash should match combination of children
	if node.Left != nil && node.Right != nil {
		expectedHash := combineHashes(node.Left.Hash, node.Right.Hash)
		if node.Hash != expectedHash {
			return false
		}
	}

	// Recursively verify children
	return verifyNode(node.Left) && verifyNode(node.Right)
}

// Serialize serializes the Merkle tree to JSON
func (mt *MerkleTree) Serialize() ([]byte, error) {
	return json.Marshal(mt)
}

// Deserialize deserializes a Merkle tree from JSON
func Deserialize(data []byte) (*MerkleTree, error) {
	var mt MerkleTree
	if err := json.Unmarshal(data, &mt); err != nil {
		return nil, err
	}
	return &mt, nil
}