// Package storage provides filesystem-based storage for ArxOS building repositories
package storage

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
	"github.com/arx-os/arxos/pkg/models"
)

// FilesystemStorage implements storage for building data as a filesystem tree
type FilesystemStorage struct {
	rootPath string
	mu       sync.RWMutex
	watchers map[string]chan FileEvent
}

// FileEvent represents a change in the filesystem
type FileEvent struct {
	Path      string
	Operation string // create, update, delete, rename
	Timestamp time.Time
	OldPath   string // for rename operations
}

// NewFilesystemStorage creates a new filesystem storage instance
func NewFilesystemStorage(rootPath string) (*FilesystemStorage, error) {
	// Ensure root path exists
	if err := os.MkdirAll(rootPath, 0755); err != nil {
		return nil, fmt.Errorf("failed to create storage root: %w", err)
	}

	return &FilesystemStorage{
		rootPath: rootPath,
		watchers: make(map[string]chan FileEvent),
	}, nil
}

// ArxOS Path Format: /building-id/floor-XX/room-XXX/system/component
// Filesystem Path: rootPath/buildings/building-id/floors/XX/rooms/XXX/systems/type/component.json

// ResolvePath converts an ArxOS path to filesystem path
func (fs *FilesystemStorage) ResolvePath(arxPath string) (string, error) {
	// Parse ArxOS path
	parts := strings.Split(strings.TrimPrefix(arxPath, "/"), "/")
	if len(parts) == 0 {
		return "", fmt.Errorf("invalid ArxOS path: %s", arxPath)
	}

	// Build filesystem path
	fsPath := filepath.Join(fs.rootPath, "buildings", parts[0])

	for i := 1; i < len(parts); i++ {
		part := parts[i]

		// Handle different path components
		if strings.HasPrefix(part, "floor-") {
			fsPath = filepath.Join(fsPath, "floors", strings.TrimPrefix(part, "floor-"))
		} else if strings.HasPrefix(part, "room-") {
			fsPath = filepath.Join(fsPath, "rooms", strings.TrimPrefix(part, "room-"))
		} else if isSystemType(part) {
			fsPath = filepath.Join(fsPath, "systems", part)
		} else {
			// Component or asset
			fsPath = filepath.Join(fsPath, part)
		}
	}

	return fsPath, nil
}

// GetBuilding retrieves a building by ID from filesystem
func (fs *FilesystemStorage) GetBuilding(ctx context.Context, buildingID string) (*models.FloorPlan, error) {
	fs.mu.RLock()
	defer fs.mu.RUnlock()

	buildingPath := filepath.Join(fs.rootPath, "buildings", buildingID)
	metaPath := filepath.Join(buildingPath, "metadata.json")

	// Read metadata
	data, err := os.ReadFile(metaPath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, fmt.Errorf("building not found: %s", buildingID)
		}
		return nil, fmt.Errorf("failed to read building metadata: %w", err)
	}

	var building models.FloorPlan
	if err := json.Unmarshal(data, &building); err != nil {
		return nil, fmt.Errorf("failed to parse building metadata: %w", err)
	}

	// Load rooms
	building.Rooms = fs.loadRooms(buildingPath)

	// Load equipment
	building.Equipment = fs.loadEquipment(buildingPath)

	return &building, nil
}

// SaveBuilding saves a building to filesystem
func (fs *FilesystemStorage) SaveBuilding(ctx context.Context, building *models.FloorPlan) error {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	buildingPath := filepath.Join(fs.rootPath, "buildings", building.ID)

	// Create directory structure
	dirs := []string{
		buildingPath,
		filepath.Join(buildingPath, "floors"),
		filepath.Join(buildingPath, "rooms"),
		filepath.Join(buildingPath, "systems"),
		filepath.Join(buildingPath, "assets"),
		filepath.Join(buildingPath, "docs"),
	}

	for _, dir := range dirs {
		if err := os.MkdirAll(dir, 0755); err != nil {
			return fmt.Errorf("failed to create directory %s: %w", dir, err)
		}
	}

	// Save metadata
	metaPath := filepath.Join(buildingPath, "metadata.json")
	metadata := map[string]interface{}{
		"id":         building.ID,
		"name":       building.Name,
		"building":   building.Building,
		"level":      building.Level,
		"created_at": building.CreatedAt,
		"updated_at": building.UpdatedAt,
		"version":    "1.0.0",
		"arxos_path": fmt.Sprintf("/%s", building.ID),
	}

	data, err := json.MarshalIndent(metadata, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	if err := os.WriteFile(metaPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write metadata: %w", err)
	}

	// Save rooms
	for _, room := range building.Rooms {
		if err := fs.saveRoom(buildingPath, room); err != nil {
			return fmt.Errorf("failed to save room %s: %w", room.ID, err)
		}
	}

	// Save equipment
	for _, equip := range building.Equipment {
		if err := fs.saveEquipment(buildingPath, equip); err != nil {
			return fmt.Errorf("failed to save equipment %s: %w", equip.ID, err)
		}
	}

	// Notify watchers
	fs.notifyWatchers(FileEvent{
		Path:      fmt.Sprintf("/%s", building.ID),
		Operation: "update",
		Timestamp: time.Now(),
	})

	logger.Info("Saved building %s to filesystem", building.ID)
	return nil
}

// GetComponent retrieves a specific component by ArxOS path
func (fs *FilesystemStorage) GetComponent(ctx context.Context, arxPath string) (interface{}, error) {
	fs.mu.RLock()
	defer fs.mu.RUnlock()

	fsPath, err := fs.ResolvePath(arxPath)
	if err != nil {
		return nil, err
	}

	// Check if it's a directory or file
	info, err := os.Stat(fsPath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil, fmt.Errorf("component not found: %s", arxPath)
		}
		return nil, err
	}

	if info.IsDir() {
		// Return directory listing
		return fs.listDirectory(fsPath)
	}

	// Read component data
	data, err := os.ReadFile(fsPath)
	if err != nil {
		return nil, fmt.Errorf("failed to read component: %w", err)
	}

	// Parse based on file extension
	if strings.HasSuffix(fsPath, ".json") {
		var component map[string]interface{}
		if err := json.Unmarshal(data, &component); err != nil {
			return nil, fmt.Errorf("failed to parse component: %w", err)
		}
		return component, nil
	}

	// Return raw data for other formats
	return string(data), nil
}

// SaveComponent saves a component at the specified ArxOS path
func (fs *FilesystemStorage) SaveComponent(ctx context.Context, arxPath string, component interface{}) error {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	fsPath, err := fs.ResolvePath(arxPath)
	if err != nil {
		return err
	}

	// Ensure parent directory exists
	parentDir := filepath.Dir(fsPath)
	if err := os.MkdirAll(parentDir, 0755); err != nil {
		return fmt.Errorf("failed to create parent directory: %w", err)
	}

	// Add .json extension if not present
	if !strings.Contains(filepath.Base(fsPath), ".") {
		fsPath += ".json"
	}

	// Marshal component
	data, err := json.MarshalIndent(component, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to marshal component: %w", err)
	}

	// Write to filesystem
	if err := os.WriteFile(fsPath, data, 0644); err != nil {
		return fmt.Errorf("failed to write component: %w", err)
	}

	// Notify watchers
	fs.notifyWatchers(FileEvent{
		Path:      arxPath,
		Operation: "update",
		Timestamp: time.Now(),
	})

	return nil
}

// DeleteComponent removes a component from the filesystem
func (fs *FilesystemStorage) DeleteComponent(ctx context.Context, arxPath string) error {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	fsPath, err := fs.ResolvePath(arxPath)
	if err != nil {
		return err
	}

	// Remove file or directory
	if err := os.RemoveAll(fsPath); err != nil {
		return fmt.Errorf("failed to delete component: %w", err)
	}

	// Notify watchers
	fs.notifyWatchers(FileEvent{
		Path:      arxPath,
		Operation: "delete",
		Timestamp: time.Now(),
	})

	return nil
}

// Query searches for components matching criteria
func (fs *FilesystemStorage) Query(ctx context.Context, pattern string) ([]string, error) {
	fs.mu.RLock()
	defer fs.mu.RUnlock()

	var results []string

	// Walk the filesystem
	err := filepath.Walk(fs.rootPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return nil // Skip errors
		}

		// Convert to ArxOS path
		relPath, _ := filepath.Rel(fs.rootPath, path)
		arxPath := "/" + strings.ReplaceAll(relPath, string(os.PathSeparator), "/")

		// Check if path matches pattern
		if matched, _ := filepath.Match(pattern, arxPath); matched {
			results = append(results, arxPath)
		}

		return nil
	})

	return results, err
}

// Watch subscribes to changes in the filesystem
func (fs *FilesystemStorage) Watch(ctx context.Context, arxPath string) (<-chan FileEvent, error) {
	fs.mu.Lock()
	defer fs.mu.Unlock()

	// Create channel for this watcher
	ch := make(chan FileEvent, 100)
	watcherID := fmt.Sprintf("%s-%d", arxPath, time.Now().UnixNano())
	fs.watchers[watcherID] = ch

	// Clean up on context cancellation
	go func() {
		<-ctx.Done()
		fs.mu.Lock()
		delete(fs.watchers, watcherID)
		close(ch)
		fs.mu.Unlock()
	}()

	return ch, nil
}

// Helper functions

func (fs *FilesystemStorage) loadRooms(buildingPath string) []*models.Room {
	roomsPath := filepath.Join(buildingPath, "rooms")
	var rooms []*models.Room

	entries, err := os.ReadDir(roomsPath)
	if err != nil {
		return rooms
	}

	for _, entry := range entries {
		if !entry.IsDir() && strings.HasSuffix(entry.Name(), ".json") {
			roomPath := filepath.Join(roomsPath, entry.Name())
			if data, err := os.ReadFile(roomPath); err == nil {
				var room models.Room
				if json.Unmarshal(data, &room) == nil {
					rooms = append(rooms, &room)
				}
			}
		}
	}

	return rooms
}

func (fs *FilesystemStorage) loadEquipment(buildingPath string) []*models.Equipment {
	systemsPath := filepath.Join(buildingPath, "systems")
	var equipment []*models.Equipment

	// Walk through all system directories
	filepath.Walk(systemsPath, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return nil
		}

		if strings.HasSuffix(path, ".json") {
			if data, err := os.ReadFile(path); err == nil {
				var equip models.Equipment
				if json.Unmarshal(data, &equip) == nil {
					equipment = append(equipment, &equip)
				}
			}
		}

		return nil
	})

	return equipment
}

func (fs *FilesystemStorage) saveRoom(buildingPath string, room *models.Room) error {
	roomPath := filepath.Join(buildingPath, "rooms", fmt.Sprintf("%s.json", room.ID))
	data, err := json.MarshalIndent(room, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(roomPath, data, 0644)
}

func (fs *FilesystemStorage) saveEquipment(buildingPath string, equip *models.Equipment) error {
	// Determine system type
	systemType := equip.Type
	if systemType == "" {
		systemType = "general"
	}

	equipPath := filepath.Join(buildingPath, "systems", systemType, fmt.Sprintf("%s.json", equip.ID))

	// Ensure directory exists
	os.MkdirAll(filepath.Dir(equipPath), 0755)

	data, err := json.MarshalIndent(equip, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(equipPath, data, 0644)
}

func (fs *FilesystemStorage) listDirectory(fsPath string) ([]string, error) {
	entries, err := os.ReadDir(fsPath)
	if err != nil {
		return nil, err
	}

	var items []string
	for _, entry := range entries {
		name := entry.Name()
		if entry.IsDir() {
			name += "/"
		}
		items = append(items, name)
	}

	return items, nil
}

func (fs *FilesystemStorage) notifyWatchers(event FileEvent) {
	for _, ch := range fs.watchers {
		select {
		case ch <- event:
		default:
			// Channel full, skip
		}
	}
}

func isSystemType(s string) bool {
	systemTypes := []string{"electrical", "hvac", "plumbing", "structural", "fire", "security", "network"}
	for _, st := range systemTypes {
		if s == st {
			return true
		}
	}
	return false
}