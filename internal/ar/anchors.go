package ar

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/spatial"
)

// AnchorType represents the type of spatial anchor
type AnchorType string

const (
	AnchorTypeUser      AnchorType = "user"      // User-placed anchor
	AnchorTypeAutomatic AnchorType = "automatic" // System-generated anchor
	AnchorTypeReference AnchorType = "reference" // Reference/calibration anchor
	AnchorTypeShared    AnchorType = "shared"    // Shared between devices
)

// AnchorState represents the state of an anchor
type AnchorState string

const (
	AnchorStateActive    AnchorState = "active"
	AnchorStatePending   AnchorState = "pending"
	AnchorStateLost      AnchorState = "lost"
	AnchorStateRecovered AnchorState = "recovered"
	AnchorStateExpired   AnchorState = "expired"
)

// SpatialAnchor represents a persistent AR anchor
type SpatialAnchor struct {
	ID              string          `json:"id"`
	Type            AnchorType      `json:"type"`
	State           AnchorState     `json:"state"`
	ARPosition      ARPoint3D       `json:"ar_position"`
	WorldPosition   spatial.Point3D `json:"world_position"`
	Rotation        ARRotation      `json:"rotation"`
	CreatedBy       string          `json:"created_by"`
	CreatedAt       time.Time       `json:"created_at"`
	LastSeen        time.Time       `json:"last_seen"`
	UpdateCount     int             `json:"update_count"`
	Confidence      float32         `json:"confidence"`
	DriftCorrection ARPoint3D       `json:"drift_correction"`
	Metadata        map[string]interface{} `json:"metadata"`
}

// AnchorStore manages spatial anchors
type AnchorStore struct {
	anchors        map[string]*SpatialAnchor
	deviceAnchors  map[string][]string // device ID -> anchor IDs
	sharedAnchors  map[string][]string // building ID -> shared anchor IDs
	mu             sync.RWMutex
	persistence    AnchorPersistence
	driftThreshold float64
}

// AnchorPersistence interface for anchor storage
type AnchorPersistence interface {
	SaveAnchor(anchor *SpatialAnchor) error
	LoadAnchor(id string) (*SpatialAnchor, error)
	LoadAnchorsForBuilding(buildingID string) ([]*SpatialAnchor, error)
	DeleteAnchor(id string) error
}

// NewAnchorStore creates a new anchor store
func NewAnchorStore(persistence AnchorPersistence) *AnchorStore {
	return &AnchorStore{
		anchors:        make(map[string]*SpatialAnchor),
		deviceAnchors:  make(map[string][]string),
		sharedAnchors:  make(map[string][]string),
		persistence:    persistence,
		driftThreshold: 0.1, // 10cm drift threshold
	}
}

// CreateAnchor creates a new spatial anchor
func (as *AnchorStore) CreateAnchor(
	deviceID string,
	arPos ARPoint3D,
	worldPos spatial.Point3D,
	rotation ARRotation,
	anchorType AnchorType,
) (*SpatialAnchor, error) {

	anchor := &SpatialAnchor{
		ID:            fmt.Sprintf("anchor_%d", time.Now().UnixNano()),
		Type:          anchorType,
		State:         AnchorStateActive,
		ARPosition:    arPos,
		WorldPosition: worldPos,
		Rotation:      rotation,
		CreatedBy:     deviceID,
		CreatedAt:     time.Now(),
		LastSeen:      time.Now(),
		UpdateCount:   0,
		Confidence:    1.0,
		Metadata:      make(map[string]interface{}),
	}

	as.mu.Lock()
	defer as.mu.Unlock()

	// Store in memory
	as.anchors[anchor.ID] = anchor

	// Track device anchors
	as.deviceAnchors[deviceID] = append(as.deviceAnchors[deviceID], anchor.ID)

	// Track shared anchors
	if anchorType == AnchorTypeShared || anchorType == AnchorTypeReference {
		buildingID := as.extractBuildingID(anchor)
		as.sharedAnchors[buildingID] = append(as.sharedAnchors[buildingID], anchor.ID)
	}

	// Persist if available
	if as.persistence != nil {
		if err := as.persistence.SaveAnchor(anchor); err != nil {
			return nil, fmt.Errorf("failed to persist anchor: %w", err)
		}
	}

	return anchor, nil
}

// UpdateAnchor updates an existing anchor
func (as *AnchorStore) UpdateAnchor(id string, arPos ARPoint3D, confidence float32) error {
	as.mu.Lock()
	defer as.mu.Unlock()

	anchor, exists := as.anchors[id]
	if !exists {
		return fmt.Errorf("anchor %s not found", id)
	}

	// Check for drift
	drift := anchor.ARPosition.Distance(arPos)
	if drift > as.driftThreshold {
		// Calculate drift correction
		anchor.DriftCorrection = ARPoint3D{
			X: arPos.X - anchor.ARPosition.X,
			Y: arPos.Y - anchor.ARPosition.Y,
			Z: arPos.Z - anchor.ARPosition.Z,
		}
	}

	// Update position and metadata
	anchor.ARPosition = arPos
	anchor.Confidence = confidence
	anchor.LastSeen = time.Now()
	anchor.UpdateCount++

	// Update state based on confidence
	if confidence < 0.3 {
		anchor.State = AnchorStateLost
	} else if anchor.State == AnchorStateLost && confidence > 0.5 {
		anchor.State = AnchorStateRecovered
	} else if confidence > 0.7 {
		anchor.State = AnchorStateActive
	}

	// Persist update
	if as.persistence != nil {
		return as.persistence.SaveAnchor(anchor)
	}

	return nil
}

// GetAnchor retrieves an anchor by ID
func (as *AnchorStore) GetAnchor(id string) (*SpatialAnchor, error) {
	as.mu.RLock()
	defer as.mu.RUnlock()

	anchor, exists := as.anchors[id]
	if !exists {
		// Try loading from persistence
		if as.persistence != nil {
			loadedAnchor, err := as.persistence.LoadAnchor(id)
			if err == nil {
				as.mu.RUnlock()
				as.mu.Lock()
				as.anchors[id] = loadedAnchor
				as.mu.Unlock()
				as.mu.RLock()
				return loadedAnchor, nil
			}
		}
		return nil, fmt.Errorf("anchor %s not found", id)
	}

	return anchor, nil
}

// GetDeviceAnchors returns all anchors for a device
func (as *AnchorStore) GetDeviceAnchors(deviceID string) []*SpatialAnchor {
	as.mu.RLock()
	defer as.mu.RUnlock()

	anchorIDs := as.deviceAnchors[deviceID]
	anchors := make([]*SpatialAnchor, 0, len(anchorIDs))

	for _, id := range anchorIDs {
		if anchor, exists := as.anchors[id]; exists {
			anchors = append(anchors, anchor)
		}
	}

	return anchors
}

// GetSharedAnchors returns shared anchors for a building
func (as *AnchorStore) GetSharedAnchors(buildingID string) []*SpatialAnchor {
	as.mu.RLock()
	defer as.mu.RUnlock()

	anchorIDs := as.sharedAnchors[buildingID]
	anchors := make([]*SpatialAnchor, 0, len(anchorIDs))

	for _, id := range anchorIDs {
		if anchor, exists := as.anchors[id]; exists {
			if anchor.Type == AnchorTypeShared || anchor.Type == AnchorTypeReference {
				anchors = append(anchors, anchor)
			}
		}
	}

	return anchors
}

// FindNearbyAnchors finds anchors within a distance from a point
func (as *AnchorStore) FindNearbyAnchors(position ARPoint3D, maxDistance float64) []*SpatialAnchor {
	as.mu.RLock()
	defer as.mu.RUnlock()

	nearby := make([]*SpatialAnchor, 0)

	for _, anchor := range as.anchors {
		if anchor.State == AnchorStateActive || anchor.State == AnchorStateRecovered {
			distance := anchor.ARPosition.Distance(position)
			if distance <= maxDistance {
				nearby = append(nearby, anchor)
			}
		}
	}

	return nearby
}

// RecoverLostAnchors attempts to recover lost anchors
func (as *AnchorStore) RecoverLostAnchors(currentPosition ARPoint3D, visibleAnchors []string) []string {
	as.mu.Lock()
	defer as.mu.Unlock()

	recovered := make([]string, 0)

	for _, anchor := range as.anchors {
		if anchor.State == AnchorStateLost {
			// Check if anchor should be visible
			distance := anchor.ARPosition.Distance(currentPosition)
			if distance < 5.0 { // Within 5 meters
				// Check if anchor is in visible list
				for _, visibleID := range visibleAnchors {
					if visibleID == anchor.ID {
						anchor.State = AnchorStateRecovered
						anchor.LastSeen = time.Now()
						recovered = append(recovered, anchor.ID)
						break
					}
				}
			}
		}
	}

	return recovered
}

// CleanupExpiredAnchors removes expired anchors
func (as *AnchorStore) CleanupExpiredAnchors(maxAge time.Duration) int {
	as.mu.Lock()
	defer as.mu.Unlock()

	expiredCount := 0
	cutoff := time.Now().Add(-maxAge)

	for id, anchor := range as.anchors {
		if anchor.LastSeen.Before(cutoff) && anchor.Type != AnchorTypeReference {
			anchor.State = AnchorStateExpired

			// Remove from device anchors
			if deviceAnchors, exists := as.deviceAnchors[anchor.CreatedBy]; exists {
				filtered := make([]string, 0, len(deviceAnchors))
				for _, anchorID := range deviceAnchors {
					if anchorID != id {
						filtered = append(filtered, anchorID)
					}
				}
				as.deviceAnchors[anchor.CreatedBy] = filtered
			}

			// Remove from memory
			delete(as.anchors, id)
			expiredCount++

			// Delete from persistence
			if as.persistence != nil {
				as.persistence.DeleteAnchor(id)
			}
		}
	}

	return expiredCount
}

// extractBuildingID extracts building ID from anchor metadata
func (as *AnchorStore) extractBuildingID(anchor *SpatialAnchor) string {
	if buildingID, ok := anchor.Metadata["building_id"].(string); ok {
		return buildingID
	}
	return "default"
}

// AnchorCloud represents a cloud of related anchors for localization
type AnchorCloud struct {
	ID          string           `json:"id"`
	BuildingID  string           `json:"building_id"`
	Anchors     []*SpatialAnchor `json:"anchors"`
	Centroid    ARPoint3D        `json:"centroid"`
	Radius      float64          `json:"radius"`
	LastUpdated time.Time        `json:"last_updated"`
}

// BuildAnchorCloud creates an anchor cloud from nearby anchors
func BuildAnchorCloud(anchors []*SpatialAnchor) *AnchorCloud {
	if len(anchors) == 0 {
		return nil
	}

	// Calculate centroid
	var sumX, sumY, sumZ float64
	for _, anchor := range anchors {
		sumX += anchor.ARPosition.X
		sumY += anchor.ARPosition.Y
		sumZ += anchor.ARPosition.Z
	}

	count := float64(len(anchors))
	centroid := ARPoint3D{
		X: sumX / count,
		Y: sumY / count,
		Z: sumZ / count,
	}

	// Calculate radius
	var maxDistance float64
	for _, anchor := range anchors {
		distance := centroid.Distance(anchor.ARPosition)
		if distance > maxDistance {
			maxDistance = distance
		}
	}

	return &AnchorCloud{
		ID:          fmt.Sprintf("cloud_%d", time.Now().UnixNano()),
		Anchors:     anchors,
		Centroid:    centroid,
		Radius:      maxDistance,
		LastUpdated: time.Now(),
	}
}

// LocalizeWithAnchors performs localization using multiple anchors
func LocalizeWithAnchors(
	visibleAnchors map[string]ARPoint3D, // anchor ID -> observed position
	knownAnchors map[string]*SpatialAnchor, // anchor ID -> known anchor
) (*ARTransform, error) {

	if len(visibleAnchors) < 3 {
		return nil, fmt.Errorf("need at least 3 anchors for localization")
	}

	// Simple averaging approach - could be improved with RANSAC or similar
	var sumDriftX, sumDriftY, sumDriftZ float64
	var validCount int

	for anchorID, observedPos := range visibleAnchors {
		if knownAnchor, exists := knownAnchors[anchorID]; exists {
			// Calculate drift
			driftX := knownAnchor.ARPosition.X - observedPos.X
			driftY := knownAnchor.ARPosition.Y - observedPos.Y
			driftZ := knownAnchor.ARPosition.Z - observedPos.Z

			sumDriftX += driftX
			sumDriftY += driftY
			sumDriftZ += driftZ
			validCount++
		}
	}

	if validCount == 0 {
		return nil, fmt.Errorf("no valid anchor matches")
	}

	// Average drift correction
	avgDrift := ARPoint3D{
		X: sumDriftX / float64(validCount),
		Y: sumDriftY / float64(validCount),
		Z: sumDriftZ / float64(validCount),
	}

	// Build transform with drift correction
	transform := &ARTransform{
		Position:   avgDrift,
		Rotation:   ARRotation{X: 0, Y: 0, Z: 0, W: 1}, // Identity rotation for now
		Scale:      1.0,
		Timestamp:  time.Now(),
		Confidence: float32(validCount) / float32(len(visibleAnchors)),
	}

	return transform, nil
}

// MemoryAnchorPersistence is an in-memory implementation of AnchorPersistence
type MemoryAnchorPersistence struct {
	anchors map[string]*SpatialAnchor
	mu      sync.RWMutex
}

// NewMemoryAnchorPersistence creates a new in-memory anchor persistence
func NewMemoryAnchorPersistence() *MemoryAnchorPersistence {
	return &MemoryAnchorPersistence{
		anchors: make(map[string]*SpatialAnchor),
	}
}

// SaveAnchor saves an anchor to memory
func (m *MemoryAnchorPersistence) SaveAnchor(anchor *SpatialAnchor) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	// Deep copy to avoid reference issues
	anchorCopy := *anchor
	m.anchors[anchor.ID] = &anchorCopy
	return nil
}

// LoadAnchor loads an anchor from memory
func (m *MemoryAnchorPersistence) LoadAnchor(id string) (*SpatialAnchor, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	anchor, exists := m.anchors[id]
	if !exists {
		return nil, fmt.Errorf("anchor %s not found", id)
	}

	// Return a copy
	anchorCopy := *anchor
	return &anchorCopy, nil
}

// LoadAnchorsForBuilding loads all anchors for a building
func (m *MemoryAnchorPersistence) LoadAnchorsForBuilding(buildingID string) ([]*SpatialAnchor, error) {
	m.mu.RLock()
	defer m.mu.RUnlock()

	anchors := make([]*SpatialAnchor, 0)
	for _, anchor := range m.anchors {
		if bid, ok := anchor.Metadata["building_id"].(string); ok && bid == buildingID {
			anchorCopy := *anchor
			anchors = append(anchors, &anchorCopy)
		}
	}

	return anchors, nil
}

// DeleteAnchor deletes an anchor from memory
func (m *MemoryAnchorPersistence) DeleteAnchor(id string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	delete(m.anchors, id)
	return nil
}

// AnchorSharingData represents data for sharing anchors between devices
type AnchorSharingData struct {
	AnchorID      string          `json:"anchor_id"`
	ARPosition    ARPoint3D       `json:"ar_position"`
	WorldPosition spatial.Point3D `json:"world_position"`
	Rotation      ARRotation      `json:"rotation"`
	CloudMap      []byte          `json:"cloud_map"` // Platform-specific cloud anchor data
	CreatedBy     string          `json:"created_by"`
	Timestamp     time.Time       `json:"timestamp"`
}

// SerializeForSharing serializes an anchor for sharing
func (anchor *SpatialAnchor) SerializeForSharing() ([]byte, error) {
	sharingData := AnchorSharingData{
		AnchorID:      anchor.ID,
		ARPosition:    anchor.ARPosition,
		WorldPosition: anchor.WorldPosition,
		Rotation:      anchor.Rotation,
		CreatedBy:     anchor.CreatedBy,
		Timestamp:     anchor.CreatedAt,
	}

	return json.Marshal(sharingData)
}

// DeserializeSharedAnchor deserializes a shared anchor
func DeserializeSharedAnchor(data []byte) (*SpatialAnchor, error) {
	var sharingData AnchorSharingData
	if err := json.Unmarshal(data, &sharingData); err != nil {
		return nil, err
	}

	return &SpatialAnchor{
		ID:            sharingData.AnchorID,
		Type:          AnchorTypeShared,
		State:         AnchorStatePending,
		ARPosition:    sharingData.ARPosition,
		WorldPosition: sharingData.WorldPosition,
		Rotation:      sharingData.Rotation,
		CreatedBy:     sharingData.CreatedBy,
		CreatedAt:     sharingData.Timestamp,
		LastSeen:      time.Now(),
		Confidence:    0.5, // Initial confidence for shared anchors
		Metadata:      make(map[string]interface{}),
	}, nil
}