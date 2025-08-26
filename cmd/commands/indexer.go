package commands

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// DirectoryEntry models a node in the virtual building filesystem
// Centralized here so all commands share the same type
// Type examples: "directory", "floor", "system", "zone", "asset", "file"
type DirectoryEntry struct {
	Name     string                 `json:"name"`
	Type     string                 `json:"type"`
	Path     string                 `json:"path"`
	IsDir    bool                   `json:"is_dir"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// TreeEntry represents a recursive view for the tree command
type TreeEntry struct {
	Name     string                 `json:"name"`
	Type     string                 `json:"type"`
	Path     string                 `json:"path"`
	IsDir    bool                   `json:"is_dir"`
	Children []TreeEntry            `json:"children,omitempty"`
	Metadata map[string]interface{} `json:"metadata,omitempty"`
}

// Index contains a map of virtual path -> entries
// and metadata about when/how it was built
type Index struct {
	BuiltAt          time.Time                   `json:"built_at"`
	BuildingID       string                      `json:"building_id"`
	PathToEntries    map[string][]DirectoryEntry `json:"path_to_entries"`
	KnownDirectories map[string]bool             `json:"known_directories"`
}

func indexCachePath(buildingRoot string) string {
	return filepath.Join(buildingRoot, ".arxos", "cache", "index.json")
}

// LoadIndex tries to read the JSON cache; returns nil if not found
func LoadIndex(buildingRoot string) (*Index, error) {
	p := indexCachePath(buildingRoot)
	data, err := os.ReadFile(p)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, nil
		}
		return nil, fmt.Errorf("read index cache: %w", err)
	}
	var idx Index
	if err := json.Unmarshal(data, &idx); err != nil {
		return nil, fmt.Errorf("parse index cache: %w", err)
	}
	return &idx, nil
}

// SaveIndex writes the index to cache atomically
func SaveIndex(buildingRoot string, idx *Index) error {
	p := indexCachePath(buildingRoot)
	if err := os.MkdirAll(filepath.Dir(p), 0755); err != nil {
		return fmt.Errorf("ensure cache dir: %w", err)
	}
	b, err := json.MarshalIndent(idx, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal index: %w", err)
	}
	tmp := p + ".tmp"
	if err := os.WriteFile(tmp, b, 0644); err != nil {
		return fmt.Errorf("write temp index: %w", err)
	}
	if err := os.Rename(tmp, p); err != nil {
		return fmt.Errorf("commit index: %w", err)
	}
	return nil
}

// GetAllObjects retrieves all ArxObject metadata from the index
func (idx *Index) GetAllObjects() ([]*ArxObjectMetadata, error) {
	var objects []*ArxObjectMetadata
	
	// Convert DirectoryEntry objects to ArxObjectMetadata
	for _, entries := range idx.PathToEntries {
		for _, entry := range entries {
			// Create ArxObjectMetadata from DirectoryEntry
			obj := &ArxObjectMetadata{
				ID:          entry.Path,
				Name:        entry.Name,
				Type:        entry.Type,
				Description: fmt.Sprintf("%s at %s", entry.Type, entry.Path),
				Properties:  entry.Metadata,
				Children:    []string{},
				Created:     idx.BuiltAt,
				Updated:     idx.BuiltAt,
			}
			
			// Add children if this is a directory
			if entry.IsDir {
				if childEntries, exists := idx.PathToEntries[entry.Path]; exists {
					for _, child := range childEntries {
						obj.Children = append(obj.Children, child.Path)
					}
				}
			}
			
			objects = append(objects, obj)
		}
	}
	
	return objects, nil
}

// BuildIndex scans the building workspace to construct a virtual directory index
// This placeholder implementation infers a standard structure from real directories
func BuildIndex(buildingRoot, buildingID string) (*Index, error) {
	idx := &Index{
		BuiltAt:          time.Now(),
		BuildingID:       buildingID,
		PathToEntries:    make(map[string][]DirectoryEntry),
		KnownDirectories: make(map[string]bool),
	}

	// Ensure canonical root
	rootVirt := "/"
	idx.KnownDirectories[rootVirt] = true

	// Seed top-level dirs if they exist or as conventional placeholders
	topDirs := []struct {
		name     string
		typeName string
	}{
		{"floors", "directory"},
		{"systems", "directory"},
		{"zones", "directory"},
		{"assets", "directory"},
		{"config", "directory"},
	}

	for _, td := range topDirs {
		virt := "/" + td.name
		idx.addDirEntry(rootVirt, DirectoryEntry{Name: td.name, Type: td.typeName, Path: virt, IsDir: true})
		idx.KnownDirectories[virt] = true
	}

	// Populate floors if a directory exists under building root
	floorsFs := filepath.Join(buildingRoot, "floors")
	if entries, err := os.ReadDir(floorsFs); err == nil {
		for _, e := range entries {
			name := e.Name()
			virt := "/floors/" + name
			idx.addDirEntry("/floors", DirectoryEntry{Name: name, Type: "floor", Path: virt, IsDir: true})
			idx.KnownDirectories[virt] = true
		}
	}

	// Populate systems if exists
	systemsFs := filepath.Join(buildingRoot, "systems")
	if entries, err := os.ReadDir(systemsFs); err == nil {
		for _, e := range entries {
			name := e.Name()
			virt := "/systems/" + name
			idx.addDirEntry("/systems", DirectoryEntry{Name: name, Type: "system", Path: virt, IsDir: true})
			idx.KnownDirectories[virt] = true
		}
	}

	// Zones, assets, config as generic directories if exist
	for _, dir := range []string{"zones", "assets", "config"} {
		fs := filepath.Join(buildingRoot, dir)
		virtParent := "/" + dir
		if entries, err := os.ReadDir(fs); err == nil {
			for _, e := range entries {
				name := e.Name()
				virt := virtParent + "/" + name
				isDir := e.IsDir()
				etype := "file"
				if isDir {
					etype = "directory"
				}
				idx.addDirEntry(virtParent, DirectoryEntry{Name: name, Type: etype, Path: virt, IsDir: isDir})
				if isDir {
					idx.KnownDirectories[virt] = true
				}
			}
		}
	}

	// Sort entries for determinism
	for p := range idx.PathToEntries {
		entries := idx.PathToEntries[p]
		sort.Slice(entries, func(i, j int) bool { return entries[i].Name < entries[j].Name })
		idx.PathToEntries[p] = entries
	}

	return idx, nil
}

func (idx *Index) addDirEntry(parentVirt string, entry DirectoryEntry) {
	idx.PathToEntries[parentVirt] = append(idx.PathToEntries[parentVirt], entry)
}

// Exists reports whether a virtual directory path is known
func (idx *Index) Exists(virtualPath string) bool {
	virtualPath = normalizeVirtualPath(virtualPath)
	if virtualPath == "/" {
		return true
	}
	return idx.KnownDirectories[virtualPath]
}

// List returns entries under a virtual directory
func (idx *Index) List(virtualPath string) []DirectoryEntry {
	virtualPath = normalizeVirtualPath(virtualPath)
	return idx.PathToEntries[virtualPath]
}

// BuildTree builds a recursive tree starting at virtualPath, limited by depth (0 = unlimited)
func (idx *Index) BuildTree(virtualPath string, depth int) TreeEntry {
	virtualPath = normalizeVirtualPath(virtualPath)
	name := "building"
	etype := "building"
	isDir := true
	if virtualPath != "/" {
		parts := strings.Split(strings.TrimPrefix(virtualPath, "/"), "/")
		name = parts[len(parts)-1]
		etype = "directory"
	}
	entry := TreeEntry{Name: name, Type: etype, Path: virtualPath, IsDir: isDir}
	if depth == 1 {
		return entry
	}
	children := idx.PathToEntries[virtualPath]
	for _, ch := range children {
		if !ch.IsDir {
			continue
		}
		nextDepth := 0
		if depth > 1 {
			nextDepth = depth - 1
		}
		entry.Children = append(entry.Children, idx.BuildTree(ch.Path, nextDepth))
	}
	return entry
}

// GetOrBuildIndex loads the cache if present; otherwise builds and saves a fresh index
func GetOrBuildIndex(buildingRoot, buildingID string) (*Index, error) {
	idx, err := LoadIndex(buildingRoot)
	if err != nil {
		return nil, err
	}
	if idx != nil && idx.BuildingID == buildingID {
		return idx, nil
	}
	newIdx, err := BuildIndex(buildingRoot, buildingID)
	if err != nil {
		return nil, err
	}
	if err := SaveIndex(buildingRoot, newIdx); err != nil {
		return nil, err
	}
	return newIdx, nil
}

// RefreshIndex forces a rebuild and cache save
func RefreshIndex(buildingRoot, buildingID string) (*Index, error) {
	idx, err := BuildIndex(buildingRoot, buildingID)
	if err != nil {
		return nil, err
	}
	if err := SaveIndex(buildingRoot, idx); err != nil {
		return nil, err
	}
	return idx, nil
}
