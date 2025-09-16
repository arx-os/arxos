package spatial

import (
	"fmt"
	"sync"
	"time"
)

// ConfidenceManager manages confidence tracking for equipment
type ConfidenceManager struct {
	records         map[string]*ConfidenceRecord
	mu              sync.RWMutex
	decayRate       float64       // Confidence decay per month
	verifyThreshold time.Duration // Time before reverification needed
}

// ConfidenceRecord tracks confidence for a piece of equipment
type ConfidenceRecord struct {
	EquipmentID string `json:"equipment_id"`

	// Position confidence
	PositionConfidence ConfidenceLevel `json:"position_confidence"`
	PositionSource     string          `json:"position_source"`
	PositionUpdated    time.Time       `json:"position_updated"`
	PositionAccuracy   float64         `json:"position_accuracy"` // meters

	// Semantic confidence
	SemanticConfidence   ConfidenceLevel `json:"semantic_confidence"`
	SemanticSource       string          `json:"semantic_source"`
	SemanticUpdated      time.Time       `json:"semantic_updated"`
	SemanticCompleteness float64         `json:"semantic_completeness"` // 0-1

	// Verification
	LastFieldVerified   *time.Time          `json:"last_field_verified,omitempty"`
	VerificationCount   int                 `json:"verification_count"`
	VerificationHistory []VerificationEvent `json:"verification_history,omitempty"`
}

// VerificationEvent represents a verification event
type VerificationEvent struct {
	Timestamp  time.Time       `json:"timestamp"`
	Method     string          `json:"method"` // "ar", "lidar", "manual"
	UserID     string          `json:"user_id,omitempty"`
	Notes      string          `json:"notes,omitempty"`
	Confidence ConfidenceLevel `json:"confidence"`
}

// AspectType represents the aspect of confidence being updated
type AspectType string

const (
	AspectPosition AspectType = "position"
	AspectSemantic AspectType = "semantic"
)

// NewConfidenceManager creates a new confidence manager
func NewConfidenceManager() *ConfidenceManager {
	return &ConfidenceManager{
		records:         make(map[string]*ConfidenceRecord),
		decayRate:       0.1,                 // 10% decay per month
		verifyThreshold: 90 * 24 * time.Hour, // 90 days
	}
}

// SetDecayRate sets the confidence decay rate
func (cm *ConfidenceManager) SetDecayRate(rate float64) {
	cm.decayRate = rate
}

// SetVerifyThreshold sets the verification threshold
func (cm *ConfidenceManager) SetVerifyThreshold(threshold time.Duration) {
	cm.verifyThreshold = threshold
}

// UpdateConfidence updates confidence for equipment
func (cm *ConfidenceManager) UpdateConfidence(
	equipmentID string,
	aspect AspectType,
	level ConfidenceLevel,
	source string,
) error {
	if equipmentID == "" {
		return fmt.Errorf("equipment ID cannot be empty")
	}

	cm.mu.Lock()
	defer cm.mu.Unlock()

	record := cm.getOrCreateRecordLocked(equipmentID)

	switch aspect {
	case AspectPosition:
		if cm.shouldUpdatePosition(record, level, source) {
			record.PositionConfidence = level
			record.PositionSource = source
			record.PositionUpdated = time.Now()
			record.PositionAccuracy = EstimateAccuracy(source)
		}
	case AspectSemantic:
		if cm.shouldUpdateSemantic(record, level, source) {
			record.SemanticConfidence = level
			record.SemanticSource = source
			record.SemanticUpdated = time.Now()
		}
	default:
		return fmt.Errorf("unknown aspect type: %s", aspect)
	}

	return nil
}

// GetConfidenceRecord retrieves confidence for equipment
func (cm *ConfidenceManager) GetConfidenceRecord(equipmentID string) (*ConfidenceRecord, error) {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	record, exists := cm.records[equipmentID]
	if !exists {
		return nil, fmt.Errorf("no confidence record for equipment %s", equipmentID)
	}

	// Apply time decay
	decayed := cm.applyTimeDecay(record)
	return decayed, nil
}

// RecordVerification records a field verification event
func (cm *ConfidenceManager) RecordVerification(
	equipmentID string,
	method string,
	userID string,
	notes string,
) error {
	cm.mu.Lock()
	defer cm.mu.Unlock()

	record := cm.getOrCreateRecordLocked(equipmentID)

	now := time.Now()
	record.LastFieldVerified = &now
	record.VerificationCount++

	event := VerificationEvent{
		Timestamp:  now,
		Method:     method,
		UserID:     userID,
		Notes:      notes,
		Confidence: ConfidenceHigh,
	}

	record.VerificationHistory = append(record.VerificationHistory, event)

	// Update confidence based on verification
	if method == "lidar" {
		record.PositionConfidence = ConfidenceHigh
		record.PositionSource = "lidar_verified"
		record.PositionUpdated = now
	} else if method == "ar" {
		record.PositionConfidence = ConfidenceHigh
		record.PositionSource = "ar_verified"
		record.PositionUpdated = now
	}

	return nil
}

// GetEquipmentNeedingVerification returns equipment that needs verification
func (cm *ConfidenceManager) GetEquipmentNeedingVerification() []string {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var needsVerification []string
	now := time.Now()

	for id, record := range cm.records {
		if cm.needsVerification(record, now) {
			needsVerification = append(needsVerification, id)
		}
	}

	return needsVerification
}

// CalculateOverallConfidence calculates weighted confidence score (0-1)
func (cm *ConfidenceManager) CalculateOverallConfidence(equipmentID string) (float64, error) {
	record, err := cm.GetConfidenceRecord(equipmentID)
	if err != nil {
		return 0, err
	}

	// Weight position confidence more heavily
	posWeight := 0.6
	semWeight := 0.4

	posScore := float64(record.PositionConfidence) / 3.0
	semScore := float64(record.SemanticConfidence) / 3.0

	baseScore := posScore*posWeight + semScore*semWeight

	// Apply time-based decay
	if record.LastFieldVerified != nil {
		daysSince := time.Since(*record.LastFieldVerified).Hours() / 24
		decayFactor := 1.0 - (daysSince / 365.0 * cm.decayRate)
		if decayFactor < 0.5 {
			decayFactor = 0.5 // Minimum 50% confidence
		}
		baseScore *= decayFactor
	}

	return baseScore, nil
}

// Helper methods

func (cm *ConfidenceManager) getOrCreateRecordLocked(equipmentID string) *ConfidenceRecord {
	if record, exists := cm.records[equipmentID]; exists {
		return record
	}

	record := &ConfidenceRecord{
		EquipmentID:         equipmentID,
		PositionConfidence:  ConfidenceEstimated,
		SemanticConfidence:  ConfidenceEstimated,
		VerificationHistory: make([]VerificationEvent, 0),
	}
	cm.records[equipmentID] = record
	return record
}

func (cm *ConfidenceManager) shouldUpdatePosition(record *ConfidenceRecord, newLevel ConfidenceLevel, newSource string) bool {
	// Always update if new confidence is higher
	if newLevel > record.PositionConfidence {
		return true
	}

	// Update if same level but from better source
	if newLevel == record.PositionConfidence {
		return cm.isSourceUpgrade(newSource, record.PositionSource)
	}

	return false
}

func (cm *ConfidenceManager) shouldUpdateSemantic(record *ConfidenceRecord, newLevel ConfidenceLevel, newSource string) bool {
	if newLevel > record.SemanticConfidence {
		return true
	}

	if newLevel == record.SemanticConfidence {
		return cm.isSourceUpgrade(newSource, record.SemanticSource)
	}

	return false
}

func (cm *ConfidenceManager) isSourceUpgrade(newSource, oldSource string) bool {
	// Define source priority
	priority := map[string]int{
		"lidar":       5,
		"ar_verified": 4,
		"ifc":         3,
		"pdf":         2,
		"manual":      1,
		"estimated":   0,
	}

	newPriority, newOK := priority[newSource]
	oldPriority, oldOK := priority[oldSource]

	if !newOK {
		newPriority = 0
	}
	if !oldOK {
		oldPriority = 0
	}

	return newPriority > oldPriority
}

func (cm *ConfidenceManager) applyTimeDecay(record *ConfidenceRecord) *ConfidenceRecord {
	// Create a copy to avoid modifying original
	decayed := *record

	// Apply decay only if there's been verification
	if record.LastFieldVerified != nil {
		monthsSince := time.Since(*record.LastFieldVerified).Hours() / (24 * 30)
		if monthsSince > 1 {
			// Simple decay model - could be more sophisticated
			decayFactor := 1.0 - (monthsSince * cm.decayRate / 12)
			if decayFactor < 0.5 {
				decayFactor = 0.5
			}

			// Don't actually modify confidence level, just track decay
			// This could be enhanced to actually downgrade confidence after threshold
		}
	}

	return &decayed
}

func (cm *ConfidenceManager) needsVerification(record *ConfidenceRecord, now time.Time) bool {
	// Never been verified
	if record.LastFieldVerified == nil {
		return true
	}

	// Check if past verification threshold
	timeSince := now.Sub(*record.LastFieldVerified)
	if timeSince > cm.verifyThreshold {
		return true
	}

	// Low confidence items always need verification
	if record.PositionConfidence <= ConfidenceLow {
		return true
	}

	return false
}

// ConfidenceQuery represents a query for equipment by confidence
type ConfidenceQuery struct {
	MinPositionConfidence ConfidenceLevel
	MinSemanticConfidence ConfidenceLevel
	VerifiedWithinDays    int
	RequiredSources       []string
}

// QueryWithConfidence returns equipment matching confidence criteria
func (cm *ConfidenceManager) QueryWithConfidence(query ConfidenceQuery) []string {
	cm.mu.RLock()
	defer cm.mu.RUnlock()

	var results []string
	now := time.Now()

	for id, record := range cm.records {
		// Check position confidence
		if record.PositionConfidence < query.MinPositionConfidence {
			continue
		}

		// Check semantic confidence
		if record.SemanticConfidence < query.MinSemanticConfidence {
			continue
		}

		// Check verification recency
		if query.VerifiedWithinDays > 0 && record.LastFieldVerified != nil {
			daysSince := now.Sub(*record.LastFieldVerified).Hours() / 24
			if daysSince > float64(query.VerifiedWithinDays) {
				continue
			}
		}

		// Check required sources
		if len(query.RequiredSources) > 0 {
			hasSource := false
			for _, required := range query.RequiredSources {
				if record.PositionSource == required || record.SemanticSource == required {
					hasSource = true
					break
				}
			}
			if !hasSource {
				continue
			}
		}

		results = append(results, id)
	}

	return results
}
