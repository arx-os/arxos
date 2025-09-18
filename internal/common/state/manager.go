package state

import (
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

// Manager handles the application state and persistence
type Manager struct {
	mu          sync.RWMutex
	currentPlan *models.FloorPlan
	stateDir    string
	currentFile string
	dirty       bool
}

// NewManager creates a new state manager
func NewManager(stateDir string) (*Manager, error) {
	// Create state directory if it doesn't exist
	if err := os.MkdirAll(stateDir, 0755); err != nil {
		return nil, fmt.Errorf("failed to create state directory: %w", err)
	}

	return &Manager{
		stateDir: stateDir,
	}, nil
}

// LoadFloorPlan loads a floor plan from a JSON file
func (m *Manager) LoadFloorPlan(filename string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	filepath := filepath.Join(m.stateDir, filename)

	data, err := os.ReadFile(filepath)
	if err != nil {
		if os.IsNotExist(err) {
			logger.Info("Floor plan file not found, will create new: %s", filename)
			m.currentPlan = &models.FloorPlan{
				Name:      filename,
				Building:  "Default Building",
				Level:     1,
				Rooms:     []*models.Room{},
				Equipment: []*models.Equipment{},
				CreatedAt: func() *time.Time { t := time.Now(); return &t }(),
				UpdatedAt: func() *time.Time { t := time.Now(); return &t }(),
			}
			m.currentFile = filename
			return nil
		}
		return fmt.Errorf("failed to read floor plan: %w", err)
	}

	var plan models.FloorPlan
	if err := json.Unmarshal(data, &plan); err != nil {
		return fmt.Errorf("failed to parse floor plan: %w", err)
	}

	m.currentPlan = &plan
	m.currentFile = filename
	m.dirty = false

	logger.Info("Loaded floor plan: %s", filename)
	return nil
}

// SaveFloorPlan saves the current floor plan to disk
func (m *Manager) SaveFloorPlan() error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.currentPlan == nil {
		return fmt.Errorf("no floor plan loaded")
	}

	if m.currentFile == "" {
		return fmt.Errorf("no file specified")
	}

	now := time.Now()
	m.currentPlan.UpdatedAt = &now

	data, err := json.MarshalIndent(m.currentPlan, "", "  ")
	if err != nil {
		return fmt.Errorf("failed to serialize floor plan: %w", err)
	}

	filepath := filepath.Join(m.stateDir, m.currentFile)

	// Write to temp file first, then rename (atomic operation)
	tempFile := filepath + ".tmp"
	if err := os.WriteFile(tempFile, data, 0644); err != nil {
		return fmt.Errorf("failed to write floor plan: %w", err)
	}

	if err := os.Rename(tempFile, filepath); err != nil {
		os.Remove(tempFile) // Clean up temp file
		return fmt.Errorf("failed to save floor plan: %w", err)
	}

	m.dirty = false
	logger.Info("Saved floor plan: %s", m.currentFile)
	return nil
}

// GetFloorPlan returns the current floor plan
func (m *Manager) GetFloorPlan() *models.FloorPlan {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.currentPlan
}

// SetFloorPlan sets the current floor plan
func (m *Manager) SetFloorPlan(plan *models.FloorPlan) {
	m.mu.Lock()
	defer m.mu.Unlock()
	m.currentPlan = plan
	m.dirty = true
}

// MarkEquipment updates the status of equipment
func (m *Manager) MarkEquipment(equipmentID string, status string, notes string, user string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.currentPlan == nil {
		return fmt.Errorf("no floor plan loaded")
	}

	// Find the equipment (case-insensitive search)
	var equipment *models.Equipment
	equipmentIDLower := strings.ToLower(equipmentID)
	for i := range m.currentPlan.Equipment {
		if strings.ToLower(m.currentPlan.Equipment[i].ID) == equipmentIDLower ||
			strings.ToLower(m.currentPlan.Equipment[i].Name) == equipmentIDLower {
			equipment = m.currentPlan.Equipment[i]
			break
		}
	}

	if equipment == nil {
		return fmt.Errorf("equipment not found: %s", equipmentID)
	}

	// Update equipment
	oldStatus := equipment.Status
	equipment.Status = status
	if notes != "" {
		equipment.Notes = notes
	}
	equipment.MarkedBy = user
	now := time.Now()
	equipment.MarkedAt = &now

	m.dirty = true

	logger.Info("Marked equipment %s: %s -> %s (by %s)",
		equipmentID, oldStatus, status, user)

	return nil
}

// AddEquipment adds new equipment to the floor plan
func (m *Manager) AddEquipment(name, eqType, roomID string, x, y float64, notes string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.currentPlan == nil {
		return fmt.Errorf("no floor plan loaded")
	}

	// Generate ID from name
	equipmentID := strings.ToLower(name)
	equipmentID = strings.ReplaceAll(equipmentID, " ", "_")
	equipmentID = strings.ReplaceAll(equipmentID, "-", "_")

	// Check for duplicate ID
	for _, e := range m.currentPlan.Equipment {
		if strings.EqualFold(e.ID, equipmentID) {
			return fmt.Errorf("equipment with ID %s already exists", equipmentID)
		}
	}

	equipment := &models.Equipment{
		ID:       equipmentID,
		Name:     name,
		Type:     eqType,
		Location: &models.Point3D{X: x, Y: y, Z: 0},
		RoomID:   roomID,
		Status:   models.StatusOperational,
		Notes:    notes,
	}

	m.currentPlan.Equipment = append(m.currentPlan.Equipment, equipment)

	// Add to room if specified
	if roomID != "" {
		roomFound := false
		for i := range m.currentPlan.Rooms {
			if strings.EqualFold(m.currentPlan.Rooms[i].ID, roomID) {
				m.currentPlan.Rooms[i].Equipment = append(
					m.currentPlan.Rooms[i].Equipment,
					equipmentID,
				)
				roomFound = true
				break
			}
		}
		if !roomFound {
			return fmt.Errorf("room %s not found", roomID)
		}
	}

	m.dirty = true
	logger.Info("Added equipment: %s", equipment.ID)

	return nil
}

// RemoveEquipment removes equipment from the floor plan
func (m *Manager) RemoveEquipment(equipmentID string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.currentPlan == nil {
		return fmt.Errorf("no floor plan loaded")
	}

	// Find and remove equipment
	found := false
	var removedEquip *models.Equipment
	newEquipment := []*models.Equipment{}

	for _, e := range m.currentPlan.Equipment {
		if strings.EqualFold(e.ID, equipmentID) {
			found = true
			removedEquip = e
		} else {
			newEquipment = append(newEquipment, e)
		}
	}

	if !found {
		return fmt.Errorf("equipment %s not found", equipmentID)
	}

	m.currentPlan.Equipment = newEquipment

	// Remove from room if it was in one
	if removedEquip.RoomID != "" {
		for i := range m.currentPlan.Rooms {
			if m.currentPlan.Rooms[i].ID == removedEquip.RoomID {
				newRoomEquipment := []string{}
				for _, eID := range m.currentPlan.Rooms[i].Equipment {
					if !strings.EqualFold(eID, equipmentID) {
						newRoomEquipment = append(newRoomEquipment, eID)
					}
				}
				m.currentPlan.Rooms[i].Equipment = newRoomEquipment
				break
			}
		}
	}

	m.dirty = true
	logger.Info("Removed equipment: %s", equipmentID)

	return nil
}

// CreateRoom creates a new room in the floor plan
func (m *Manager) CreateRoom(name string, minX, minY, maxX, maxY float64) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if m.currentPlan == nil {
		return fmt.Errorf("no floor plan loaded")
	}

	// Generate ID from name
	roomID := strings.ToLower(name)
	roomID = strings.ReplaceAll(roomID, " ", "_")
	roomID = strings.ReplaceAll(roomID, "-", "_")

	// Check for duplicate ID
	for _, r := range m.currentPlan.Rooms {
		if strings.EqualFold(r.ID, roomID) {
			return fmt.Errorf("room with ID %s already exists", roomID)
		}
	}

	room := &models.Room{
		ID:   roomID,
		Name: name,
		Bounds: models.Bounds{
			MinX: minX,
			MinY: minY,
			MaxX: maxX,
			MaxY: maxY,
		},
		Equipment: []string{},
	}

	m.currentPlan.Rooms = append(m.currentPlan.Rooms, room)

	m.dirty = true
	logger.Info("Created room: %s", room.ID)

	return nil
}

// FindEquipment searches for equipment by various criteria
func (m *Manager) FindEquipment(query string) []models.Equipment {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if m.currentPlan == nil {
		return nil
	}

	var results []models.Equipment

	for _, equip := range m.currentPlan.Equipment {
		// Match by ID, name, or type
		if equip.ID == query ||
			equip.Name == query ||
			equip.Type == query {
			results = append(results, *equip)
		}
	}

	return results
}

// GetEquipmentByStatus returns all equipment with a specific status
func (m *Manager) GetEquipmentByStatus(status string) []*models.Equipment {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if m.currentPlan == nil {
		return nil
	}

	var results []*models.Equipment

	for _, equip := range m.currentPlan.Equipment {
		if equip.Status == status {
			results = append(results, equip)
		}
	}

	return results
}

// GetRoom returns a room by ID
func (m *Manager) GetRoom(roomID string) *models.Room {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if m.currentPlan == nil {
		return nil
	}

	for _, room := range m.currentPlan.Rooms {
		if room.ID == roomID || room.Name == roomID {
			return room
		}
	}

	return nil
}

// IsDirty returns whether the state has unsaved changes
func (m *Manager) IsDirty() bool {
	m.mu.RLock()
	defer m.mu.RUnlock()
	return m.dirty
}

// ListFloorPlans returns all floor plan files in the state directory
func (m *Manager) ListFloorPlans() ([]string, error) {
	entries, err := os.ReadDir(m.stateDir)
	if err != nil {
		return nil, fmt.Errorf("failed to read state directory: %w", err)
	}

	var plans []string
	for _, entry := range entries {
		if !entry.IsDir() && filepath.Ext(entry.Name()) == ".json" {
			plans = append(plans, entry.Name())
		}
	}

	return plans, nil
}

// ExportForGit exports the current state in a Git-friendly format
func (m *Manager) ExportForGit() (map[string]interface{}, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	if m.currentPlan == nil {
		return nil, fmt.Errorf("no floor plan loaded")
	}

	// Create a simplified export for Git commits
	export := map[string]interface{}{
		"building": m.currentPlan.Building,
		"floor":    m.currentPlan.Name,
		"level":    m.currentPlan.Level,
		"summary": map[string]int{
			"total_rooms":     len(m.currentPlan.Rooms),
			"total_equipment": len(m.currentPlan.Equipment),
			"needs_repair":    0,
			"failed":          0,
		},
		"changes": []string{},
	}

	// Count equipment by status
	for _, equip := range m.currentPlan.Equipment {
		switch equip.Status {
		case models.StatusDegraded:
			export["summary"].(map[string]int)["needs_repair"]++
		case models.StatusFailed:
			export["summary"].(map[string]int)["failed"]++
		}
	}

	return export, nil
}
