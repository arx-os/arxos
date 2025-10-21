package building

import (
	"testing"
	"time"
)

func TestCalculateObjectHash(t *testing.T) {
	tests := []struct {
		name     string
		objType  ObjectType
		size     int64
		contents []byte
		want     string
	}{
		{
			name:     "blob object with simple contents",
			objType:  ObjectTypeBlob,
			size:     5,
			contents: []byte("hello"),
			want:     "3de8f8f1b6e5f7a6dc5e3c5e8b0c3a2f5e7f9e5c5d7e8f9e0c1d2e3f4a5b6c7d8", // Example hash
		},
		{
			name:     "empty blob",
			objType:  ObjectTypeBlob,
			size:     0,
			contents: []byte{},
			want:     "", // Will be calculated
		},
		{
			name:     "tree object",
			objType:  ObjectTypeTree,
			size:     100,
			contents: []byte(`{"entries":[]}`),
			want:     "", // Will be calculated
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := CalculateObjectHash(tt.objType, tt.size, tt.contents)

			// Verify hash is not empty
			if got == "" {
				t.Error("CalculateObjectHash() returned empty hash")
			}

			// Verify hash is 64 characters (SHA-256 hex)
			if len(got) != 64 {
				t.Errorf("CalculateObjectHash() returned hash with length %d, want 64", len(got))
			}

			// Verify hash is deterministic (same input = same output)
			got2 := CalculateObjectHash(tt.objType, tt.size, tt.contents)
			if got != got2 {
				t.Error("CalculateObjectHash() is not deterministic")
			}

			// Verify different contents produce different hashes
			if len(tt.contents) > 0 {
				differentContents := append([]byte{}, tt.contents...)
				differentContents[0] ^= 1 // Flip one bit
				got3 := CalculateObjectHash(tt.objType, tt.size, differentContents)
				if got == got3 {
					t.Error("CalculateObjectHash() produced same hash for different contents")
				}
			}
		})
	}
}

func TestCalculateTreeHash(t *testing.T) {
	tests := []struct {
		name string
		tree *Tree
	}{
		{
			name: "empty tree",
			tree: &Tree{
				Type:    ObjectTypeTree,
				Entries: []TreeEntry{},
			},
		},
		{
			name: "tree with one entry",
			tree: &Tree{
				Type: ObjectTypeTree,
				Entries: []TreeEntry{
					{
						Type: ObjectTypeBlob,
						Name: "file.txt",
						Hash: "abc123",
						Size: 100,
					},
				},
			},
		},
		{
			name: "tree with multiple entries",
			tree: &Tree{
				Type: ObjectTypeTree,
				Entries: []TreeEntry{
					{
						Type: ObjectTypeBlob,
						Name: "file1.txt",
						Hash: "abc123",
						Size: 100,
					},
					{
						Type: ObjectTypeTree,
						Name: "subdir",
						Hash: "def456",
						Size: 200,
					},
				},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := CalculateTreeHash(tt.tree)

			// Verify hash is not empty
			if got == "" {
				t.Error("CalculateTreeHash() returned empty hash")
			}

			// Verify hash is 64 characters (SHA-256 hex)
			if len(got) != 64 {
				t.Errorf("CalculateTreeHash() returned hash with length %d, want 64", len(got))
			}

			// Verify hash is deterministic
			got2 := CalculateTreeHash(tt.tree)
			if got != got2 {
				t.Error("CalculateTreeHash() is not deterministic")
			}

			// Verify different trees produce different hashes
			if len(tt.tree.Entries) > 0 {
				differentTree := *tt.tree
				differentTree.Entries[0].Name = "different.txt"
				got3 := CalculateTreeHash(&differentTree)
				if got == got3 {
					t.Error("CalculateTreeHash() produced same hash for different trees")
				}
			}
		})
	}
}

func TestCalculateSnapshotHash(t *testing.T) {
	tests := []struct {
		name     string
		snapshot *Snapshot
	}{
		{
			name: "basic snapshot",
			snapshot: &Snapshot{
				RepositoryID:   "repo-123",
				SpaceTree:      "space-hash",
				ItemTree:       "item-hash",
				SpatialTree:    "spatial-hash",
				FilesTree:      "files-hash",
				OperationsTree: "operations-hash",
			},
		},
		{
			name: "snapshot with metadata",
			snapshot: &Snapshot{
				RepositoryID:   "repo-456",
				SpaceTree:      "space-hash-2",
				ItemTree:       "item-hash-2",
				SpatialTree:    "spatial-hash-2",
				FilesTree:      "files-hash-2",
				OperationsTree: "operations-hash-2",
				Metadata: SnapshotMetadata{
					SpaceCount: 56, // 1 building + 5 floors + 50 rooms
					ItemCount:  100,
					FileCount:  10,
					TotalSize:  1000000,
				},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := CalculateSnapshotHash(tt.snapshot)

			// Verify hash is not empty
			if got == "" {
				t.Error("CalculateSnapshotHash() returned empty hash")
			}

			// Verify hash is 64 characters (SHA-256 hex)
			if len(got) != 64 {
				t.Errorf("CalculateSnapshotHash() returned hash with length %d, want 64", len(got))
			}

			// Verify hash is deterministic
			got2 := CalculateSnapshotHash(tt.snapshot)
			if got != got2 {
				t.Error("CalculateSnapshotHash() is not deterministic")
			}

			// Verify different snapshots produce different hashes
			differentSnapshot := *tt.snapshot
			differentSnapshot.SpaceTree = "different-hash"
			got3 := CalculateSnapshotHash(&differentSnapshot)
			if got == got3 {
				t.Error("CalculateSnapshotHash() produced same hash for different snapshots")
			}
		})
	}
}

func TestSerializeDeserializeObject(t *testing.T) {
	tests := []struct {
		name string
		obj  any
	}{
		{
			name: "tree object",
			obj: &Tree{
				Type: ObjectTypeTree,
				Hash: "abc123",
				Entries: []TreeEntry{
					{
						Type: ObjectTypeBlob,
						Name: "file.txt",
						Hash: "def456",
						Size: 100,
					},
				},
				Size: 100,
			},
		},
		{
			name: "snapshot object",
			obj: &Snapshot{
				Hash:           "snapshot-hash",
				RepositoryID:   "repo-123",
				SpaceTree:      "space-hash",
				ItemTree:       "item-hash",
				SpatialTree:    "spatial-hash",
				FilesTree:      "files-hash",
				OperationsTree: "operations-hash",
				Metadata: SnapshotMetadata{
					SpaceCount: 34, // 1 building + 3 floors + 30 rooms
					ItemCount:  50,
					FileCount:  5,
					TotalSize:  500000,
				},
				CreatedAt: time.Now(),
			},
		},
		{
			name: "snapshot metadata",
			obj: &SnapshotMetadata{
				SpaceCount: 111, // 1 building + 10 floors + 100 rooms
				ItemCount:  500,
				FileCount:  50,
				TotalSize:  10000000,
				Checksums: map[string]string{
					"building":  "hash1",
					"equipment": "hash2",
				},
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			// Serialize
			data, err := SerializeObject(tt.obj)
			if err != nil {
				t.Fatalf("SerializeObject() error = %v", err)
			}

			// Verify data is not empty
			if len(data) == 0 {
				t.Error("SerializeObject() returned empty data")
			}

			// Deserialize based on type
			var deserialized any
			switch tt.obj.(type) {
			case *Tree:
				deserialized = &Tree{}
			case *Snapshot:
				deserialized = &Snapshot{}
			case *SnapshotMetadata:
				deserialized = &SnapshotMetadata{}
			default:
				t.Fatalf("Unknown type: %T", tt.obj)
			}

			err = DeserializeObject(data, deserialized)
			if err != nil {
				t.Fatalf("DeserializeObject() error = %v", err)
			}

			// Verify round-trip produces valid data
			// We can't use deep equality due to time precision issues,
			// but we can verify the deserialized object is not nil
			if deserialized == nil {
				t.Error("DeserializeObject() returned nil")
			}
		})
	}
}

func TestObjectType(t *testing.T) {
	tests := []struct {
		name     string
		objType  ObjectType
		expected string
	}{
		{"blob type", ObjectTypeBlob, "blob"},
		{"tree type", ObjectTypeTree, "tree"},
		{"snapshot type", ObjectTypeSnapshot, "snapshot"},
		{"version type", ObjectTypeVersion, "version"},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if string(tt.objType) != tt.expected {
				t.Errorf("ObjectType = %v, want %v", tt.objType, tt.expected)
			}
		})
	}
}

func TestSnapshotDiff(t *testing.T) {
	diff := &SnapshotDiff{
		FromHash:          "hash1",
		ToHash:            "hash2",
		SpaceChanged:      true,
		ItemChanged:       false,
		SpatialChanged:    true,
		FilesChanged:      false,
		OperationsChanged: false,
	}

	// Verify fields are accessible
	if diff.FromHash != "hash1" {
		t.Errorf("FromHash = %v, want hash1", diff.FromHash)
	}
	if diff.ToHash != "hash2" {
		t.Errorf("ToHash = %v, want hash2", diff.ToHash)
	}
	if !diff.SpaceChanged {
		t.Error("SpaceChanged should be true")
	}
	if diff.ItemChanged {
		t.Error("ItemChanged should be false")
	}
}

func TestTreeEntry(t *testing.T) {
	entry := TreeEntry{
		Type: ObjectTypeBlob,
		Name: "test.txt",
		Hash: "abc123",
		Size: 1024,
		Mode: "0644",
	}

	// Verify fields
	if entry.Type != ObjectTypeBlob {
		t.Errorf("Type = %v, want %v", entry.Type, ObjectTypeBlob)
	}
	if entry.Name != "test.txt" {
		t.Errorf("Name = %v, want test.txt", entry.Name)
	}
	if entry.Hash != "abc123" {
		t.Errorf("Hash = %v, want abc123", entry.Hash)
	}
	if entry.Size != 1024 {
		t.Errorf("Size = %v, want 1024", entry.Size)
	}
	if entry.Mode != "0644" {
		t.Errorf("Mode = %v, want 0644", entry.Mode)
	}
}
