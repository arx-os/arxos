package state_test

import (
	"encoding/json"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
	
	"github.com/arxos/core/internal/state"
)

func TestNewMerkleTree(t *testing.T) {
	t.Run("empty tree", func(t *testing.T) {
		tree, err := state.NewMerkleTree([]interface{}{})
		
		assert.NoError(t, err)
		assert.NotNil(t, tree)
		assert.Nil(t, tree.Root)
		assert.Empty(t, tree.Leaves)
	})

	t.Run("single object tree", func(t *testing.T) {
		objects := []interface{}{
			map[string]interface{}{
				"id":   "obj1",
				"type": 1,
				"x":    100,
			},
		}

		tree, err := state.NewMerkleTree(objects)
		
		assert.NoError(t, err)
		assert.NotNil(t, tree)
		assert.NotNil(t, tree.Root)
		assert.Len(t, tree.Leaves, 1)
		assert.NotEmpty(t, tree.Root.Hash)
	})

	t.Run("multiple objects tree", func(t *testing.T) {
		objects := []interface{}{
			map[string]interface{}{"id": "obj1", "type": 1},
			map[string]interface{}{"id": "obj2", "type": 2},
			map[string]interface{}{"id": "obj3", "type": 3},
		}

		tree, err := state.NewMerkleTree(objects)
		
		assert.NoError(t, err)
		assert.NotNil(t, tree)
		assert.NotNil(t, tree.Root)
		assert.Len(t, tree.Leaves, 3)
		assert.NotEmpty(t, tree.GetRootHash())
	})
}

func TestBuildFromSnapshot(t *testing.T) {
	snapshot := json.RawMessage(`[
		{"id": "obj1", "type": 1, "x": 100},
		{"id": "obj2", "type": 2, "x": 200}
	]`)

	tree, err := state.BuildFromSnapshot(snapshot)
	
	assert.NoError(t, err)
	assert.NotNil(t, tree)
	assert.NotNil(t, tree.Root)
	assert.Len(t, tree.Leaves, 2)
}

func TestMerkleTreeCompare(t *testing.T) {
	t.Run("identical trees", func(t *testing.T) {
		objects := []interface{}{
			map[string]interface{}{"id": "obj1", "type": 1, "value": 100},
			map[string]interface{}{"id": "obj2", "type": 2, "value": 200},
		}

		tree1, _ := state.NewMerkleTree(objects)
		tree2, _ := state.NewMerkleTree(objects)

		diff, err := tree1.Compare(tree2)
		
		assert.NoError(t, err)
		assert.NotNil(t, diff)
		assert.True(t, diff.IsEmpty())
		assert.Equal(t, 0, diff.GetChangeCount())
	})

	t.Run("added objects", func(t *testing.T) {
		objects1 := []interface{}{
			map[string]interface{}{"id": "obj1", "type": 1},
		}
		objects2 := []interface{}{
			map[string]interface{}{"id": "obj1", "type": 1},
			map[string]interface{}{"id": "obj2", "type": 2},
		}

		tree1, _ := state.NewMerkleTree(objects1)
		tree2, _ := state.NewMerkleTree(objects2)

		diff, err := tree1.Compare(tree2)
		
		assert.NoError(t, err)
		assert.False(t, diff.IsEmpty())
		assert.Greater(t, len(diff.Added), 0)
	})

	t.Run("removed objects", func(t *testing.T) {
		objects1 := []interface{}{
			map[string]interface{}{"id": "obj1", "type": 1},
			map[string]interface{}{"id": "obj2", "type": 2},
		}
		objects2 := []interface{}{
			map[string]interface{}{"id": "obj1", "type": 1},
		}

		tree1, _ := state.NewMerkleTree(objects1)
		tree2, _ := state.NewMerkleTree(objects2)

		diff, err := tree1.Compare(tree2)
		
		assert.NoError(t, err)
		assert.False(t, diff.IsEmpty())
		assert.Greater(t, len(diff.Removed), 0)
	})

	t.Run("modified objects", func(t *testing.T) {
		objects1 := []interface{}{
			map[string]interface{}{"id": "obj1", "type": 1, "value": 100},
		}
		objects2 := []interface{}{
			map[string]interface{}{"id": "obj1", "type": 1, "value": 200},
		}

		tree1, _ := state.NewMerkleTree(objects1)
		tree2, _ := state.NewMerkleTree(objects2)

		diff, err := tree1.Compare(tree2)
		
		assert.NoError(t, err)
		assert.False(t, diff.IsEmpty())
		// Note: Simple comparison might show as removed+added rather than modified
		assert.Greater(t, diff.GetChangeCount(), 0)
	})

	t.Run("compare with empty tree", func(t *testing.T) {
		objects := []interface{}{
			map[string]interface{}{"id": "obj1", "type": 1},
		}

		tree1, _ := state.NewMerkleTree(objects)
		tree2, _ := state.NewMerkleTree([]interface{}{})

		diff, err := tree1.Compare(tree2)
		
		assert.NoError(t, err)
		assert.False(t, diff.IsEmpty())
		assert.Equal(t, 1, len(diff.Removed))
		assert.Equal(t, 0, len(diff.Added))
	})

	t.Run("compare empty with non-empty", func(t *testing.T) {
		objects := []interface{}{
			map[string]interface{}{"id": "obj1", "type": 1},
		}

		tree1, _ := state.NewMerkleTree([]interface{}{})
		tree2, _ := state.NewMerkleTree(objects)

		diff, err := tree1.Compare(tree2)
		
		assert.NoError(t, err)
		assert.False(t, diff.IsEmpty())
		assert.Equal(t, 0, len(diff.Removed))
		assert.Equal(t, 1, len(diff.Added))
	})
}

func TestMerkleTreeIntegrity(t *testing.T) {
	objects := []interface{}{
		map[string]interface{}{"id": "obj1", "type": 1},
		map[string]interface{}{"id": "obj2", "type": 2},
		map[string]interface{}{"id": "obj3", "type": 3},
		map[string]interface{}{"id": "obj4", "type": 4},
	}

	tree, err := state.NewMerkleTree(objects)
	
	require.NoError(t, err)
	assert.True(t, tree.VerifyIntegrity())
}

func TestMerkleTreeSerialization(t *testing.T) {
	objects := []interface{}{
		map[string]interface{}{"id": "obj1", "type": 1, "value": 100},
		map[string]interface{}{"id": "obj2", "type": 2, "value": 200},
	}

	originalTree, err := state.NewMerkleTree(objects)
	require.NoError(t, err)

	// Serialize
	data, err := originalTree.Serialize()
	assert.NoError(t, err)
	assert.NotEmpty(t, data)

	// Deserialize
	deserializedTree, err := state.Deserialize(data)
	assert.NoError(t, err)
	assert.NotNil(t, deserializedTree)

	// Compare root hashes
	assert.Equal(t, originalTree.GetRootHash(), deserializedTree.GetRootHash())
}

func TestMerkleTreeDeterministic(t *testing.T) {
	// Same objects in different order should produce same tree
	objects1 := []interface{}{
		map[string]interface{}{"id": "obj1", "type": 1},
		map[string]interface{}{"id": "obj2", "type": 2},
		map[string]interface{}{"id": "obj3", "type": 3},
	}

	objects2 := []interface{}{
		map[string]interface{}{"id": "obj3", "type": 3},
		map[string]interface{}{"id": "obj1", "type": 1},
		map[string]interface{}{"id": "obj2", "type": 2},
	}

	tree1, err := state.NewMerkleTree(objects1)
	require.NoError(t, err)

	tree2, err := state.NewMerkleTree(objects2)
	require.NoError(t, err)

	// Trees should be identical due to sorting
	assert.Equal(t, tree1.GetRootHash(), tree2.GetRootHash())
}

func BenchmarkMerkleTreeCreation(b *testing.B) {
	// Create test objects
	objects := make([]interface{}, 1000)
	for i := 0; i < 1000; i++ {
		objects[i] = map[string]interface{}{
			"id":    fmt.Sprintf("obj%d", i),
			"type":  i % 10,
			"value": i * 100,
		}
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = state.NewMerkleTree(objects)
	}
}

func BenchmarkMerkleTreeCompare(b *testing.B) {
	// Create two slightly different sets of objects
	objects1 := make([]interface{}, 1000)
	objects2 := make([]interface{}, 1000)
	
	for i := 0; i < 1000; i++ {
		objects1[i] = map[string]interface{}{
			"id":    fmt.Sprintf("obj%d", i),
			"type":  i % 10,
			"value": i * 100,
		}
		objects2[i] = map[string]interface{}{
			"id":    fmt.Sprintf("obj%d", i),
			"type":  i % 10,
			"value": i * 100,
		}
	}
	
	// Modify some objects in tree2
	for i := 0; i < 100; i++ {
		objects2[i] = map[string]interface{}{
			"id":    fmt.Sprintf("obj%d", i),
			"type":  i % 10,
			"value": i * 200, // Different value
		}
	}

	tree1, _ := state.NewMerkleTree(objects1)
	tree2, _ := state.NewMerkleTree(objects2)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = tree1.Compare(tree2)
	}
}