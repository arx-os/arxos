package merge

import (
	"fmt"
	"math"
	"time"

	"github.com/arx-os/arxos/internal/spatial"
)

// ChangeDetector detects changes in equipment over time
type ChangeDetector struct {
	history          []Change
	thresholds       ChangeThresholds
	trackingEnabled  bool
	maxHistorySize   int
}

// Change represents a detected change in equipment
type Change struct {
	ID           string          `json:"id"`
	EquipmentID  string          `json:"equipment_id"`
	Type         ChangeType      `json:"type"`
	Field        string          `json:"field"` // Which field changed
	OldValue     interface{}     `json:"old_value"`
	NewValue     interface{}     `json:"new_value"`
	Magnitude    float64         `json:"magnitude"` // Magnitude of change
	Timestamp    time.Time       `json:"timestamp"`
	Source       string          `json:"source"` // Source that detected the change
	Confidence   spatial.ConfidenceLevel `json:"confidence"`
	Verified     bool            `json:"verified"`
	ActionTaken  string          `json:"action_taken,omitempty"`
}

// ChangeType represents the type of change
type ChangeType string

const (
	ChangeTypePosition   ChangeType = "position"
	ChangeTypeDimension  ChangeType = "dimension"
	ChangeTypeType       ChangeType = "type"
	ChangeTypeAdded      ChangeType = "added"
	ChangeTypeRemoved    ChangeType = "removed"
	ChangeTypeAttribute  ChangeType = "attribute"
)

// ChangeThresholds defines thresholds for change detection
type ChangeThresholds struct {
	PositionThreshold  float64 `json:"position_threshold"` // meters
	DimensionThreshold float64 `json:"dimension_threshold"` // percentage
	TimeWindow         time.Duration `json:"time_window"` // Time window for related changes
}

// NewChangeDetector creates a new change detector
func NewChangeDetector() *ChangeDetector {
	return &ChangeDetector{
		history:         make([]Change, 0),
		trackingEnabled: true,
		maxHistorySize:  10000,
		thresholds: ChangeThresholds{
			PositionThreshold:  0.1, // 10cm
			DimensionThreshold: 0.05, // 5%
			TimeWindow:         24 * time.Hour,
		},
	}
}

// SetThresholds sets change detection thresholds
func (cd *ChangeDetector) SetThresholds(thresholds ChangeThresholds) {
	cd.thresholds = thresholds
}

// DetectChanges detects changes between old and new equipment data
func (cd *ChangeDetector) DetectChanges(
	oldEquipment *MergedEquipment,
	newEquipment *MergedEquipment,
) []Change {

	if !cd.trackingEnabled {
		return nil
	}

	changes := make([]Change, 0)

	// Check position changes
	if posChange := cd.detectPositionChange(oldEquipment, newEquipment); posChange != nil {
		changes = append(changes, *posChange)
	}

	// Check dimension changes
	if dimChanges := cd.detectDimensionChanges(oldEquipment, newEquipment); len(dimChanges) > 0 {
		changes = append(changes, dimChanges...)
	}

	// Check type change
	if typeChange := cd.detectTypeChange(oldEquipment, newEquipment); typeChange != nil {
		changes = append(changes, *typeChange)
	}

	// Check attribute changes
	if attrChanges := cd.detectAttributeChanges(oldEquipment, newEquipment); len(attrChanges) > 0 {
		changes = append(changes, attrChanges...)
	}

	// Record changes in history
	cd.recordChanges(changes)

	return changes
}

// detectPositionChange detects position changes
func (cd *ChangeDetector) detectPositionChange(
	oldEquipment *MergedEquipment,
	newEquipment *MergedEquipment,
) *Change {

	distance := oldEquipment.Position.DistanceTo(newEquipment.Position)
	if distance < cd.thresholds.PositionThreshold {
		return nil // Change too small
	}

	return &Change{
		ID:          fmt.Sprintf("change_%d", time.Now().UnixNano()),
		EquipmentID: oldEquipment.EquipmentID,
		Type:        ChangeTypePosition,
		Field:       "position",
		OldValue:    oldEquipment.Position,
		NewValue:    newEquipment.Position,
		Magnitude:   distance,
		Timestamp:   time.Now(),
		Confidence:  newEquipment.Confidence,
	}
}

// detectDimensionChanges detects dimension changes
func (cd *ChangeDetector) detectDimensionChanges(
	oldEquipment *MergedEquipment,
	newEquipment *MergedEquipment,
) []Change {

	changes := make([]Change, 0)

	// Check if any dimension has changed significantly
	lengthDiff := math.Abs(newEquipment.Dimensions.Length - oldEquipment.Dimensions.Length)
	widthDiff := math.Abs(newEquipment.Dimensions.Width - oldEquipment.Dimensions.Width)
	heightDiff := math.Abs(newEquipment.Dimensions.Height - oldEquipment.Dimensions.Height)

	// Calculate percentage changes (avoid division by zero)
	var lengthPct, widthPct, heightPct float64
	if oldEquipment.Dimensions.Length > 0 {
		lengthPct = lengthDiff / oldEquipment.Dimensions.Length
	}
	if oldEquipment.Dimensions.Width > 0 {
		widthPct = widthDiff / oldEquipment.Dimensions.Width
	}
	if oldEquipment.Dimensions.Height > 0 {
		heightPct = heightDiff / oldEquipment.Dimensions.Height
	}

	// If any dimension changed significantly, record a single dimensions change
	if lengthPct > cd.thresholds.DimensionThreshold ||
		widthPct > cd.thresholds.DimensionThreshold ||
		heightPct > cd.thresholds.DimensionThreshold {

		// Calculate overall magnitude as average of changes
		totalMagnitude := (lengthPct + widthPct + heightPct) / 3.0

		changes = append(changes, Change{
			ID:          fmt.Sprintf("change_%d", time.Now().UnixNano()),
			EquipmentID: oldEquipment.EquipmentID,
			Type:        ChangeTypeDimension,
			Field:       "dimensions",
			OldValue:    oldEquipment.Dimensions,
			NewValue:    newEquipment.Dimensions,
			Magnitude:   totalMagnitude,
			Timestamp:   time.Now(),
			Confidence:  newEquipment.Confidence,
		})
	}

	return changes
}

// detectTypeChange detects equipment type changes
func (cd *ChangeDetector) detectTypeChange(
	oldEquipment *MergedEquipment,
	newEquipment *MergedEquipment,
) *Change {

	if oldEquipment.Type == newEquipment.Type {
		return nil
	}

	return &Change{
		ID:          fmt.Sprintf("change_%d", time.Now().UnixNano()),
		EquipmentID: oldEquipment.EquipmentID,
		Type:        ChangeTypeType,
		Field:       "type",
		OldValue:    oldEquipment.Type,
		NewValue:    newEquipment.Type,
		Magnitude:   1.0, // Binary change
		Timestamp:   time.Now(),
		Confidence:  newEquipment.Confidence,
	}
}

// detectAttributeChanges detects attribute changes
func (cd *ChangeDetector) detectAttributeChanges(
	oldEquipment *MergedEquipment,
	newEquipment *MergedEquipment,
) []Change {

	changes := make([]Change, 0)

	// Check for new attributes
	for key, newValue := range newEquipment.Attributes {
		if oldValue, exists := oldEquipment.Attributes[key]; !exists {
			// New attribute
			changes = append(changes, Change{
				ID:          fmt.Sprintf("change_%d", time.Now().UnixNano()),
				EquipmentID: oldEquipment.EquipmentID,
				Type:        ChangeTypeAttribute,
				Field:       key,
				OldValue:    nil,
				NewValue:    newValue,
				Magnitude:   1.0,
				Timestamp:   time.Now(),
				Confidence:  newEquipment.Confidence,
			})
		} else if !cd.valuesEqual(oldValue, newValue) {
			// Changed attribute
			changes = append(changes, Change{
				ID:          fmt.Sprintf("change_%d", time.Now().UnixNano()),
				EquipmentID: oldEquipment.EquipmentID,
				Type:        ChangeTypeAttribute,
				Field:       key,
				OldValue:    oldValue,
				NewValue:    newValue,
				Magnitude:   cd.calculateAttributeChangeMagnitude(oldValue, newValue),
				Timestamp:   time.Now(),
				Confidence:  newEquipment.Confidence,
			})
		}
	}

	// Check for removed attributes
	for key, oldValue := range oldEquipment.Attributes {
		if _, exists := newEquipment.Attributes[key]; !exists {
			changes = append(changes, Change{
				ID:          fmt.Sprintf("change_%d", time.Now().UnixNano()),
				EquipmentID: oldEquipment.EquipmentID,
				Type:        ChangeTypeAttribute,
				Field:       key,
				OldValue:    oldValue,
				NewValue:    nil,
				Magnitude:   1.0,
				Timestamp:   time.Now(),
				Confidence:  newEquipment.Confidence,
			})
		}
	}

	return changes
}

// valuesEqual checks if two values are equal
func (cd *ChangeDetector) valuesEqual(v1, v2 interface{}) bool {
	// Simple equality check - could be enhanced for complex types
	return fmt.Sprintf("%v", v1) == fmt.Sprintf("%v", v2)
}

// calculateAttributeChangeMagnitude calculates magnitude of attribute change
func (cd *ChangeDetector) calculateAttributeChangeMagnitude(oldValue, newValue interface{}) float64 {
	// Try to calculate numeric difference
	if oldNum, ok1 := oldValue.(float64); ok1 {
		if newNum, ok2 := newValue.(float64); ok2 {
			if oldNum != 0 {
				return math.Abs(newNum-oldNum) / oldNum
			}
		}
	}
	// Default to binary change
	return 1.0
}

// recordChanges records changes in history
func (cd *ChangeDetector) recordChanges(changes []Change) {
	cd.history = append(cd.history, changes...)

	// Trim history if too large
	if len(cd.history) > cd.maxHistorySize {
		// Keep most recent changes
		cd.history = cd.history[len(cd.history)-cd.maxHistorySize:]
	}
}

// DetectAddition detects new equipment addition
func (cd *ChangeDetector) DetectAddition(equipment *MergedEquipment) Change {
	change := Change{
		ID:          fmt.Sprintf("change_%d", time.Now().UnixNano()),
		EquipmentID: equipment.EquipmentID,
		Type:        ChangeTypeAdded,
		Field:       "equipment",
		OldValue:    nil,
		NewValue:    equipment,
		Magnitude:   1.0,
		Timestamp:   time.Now(),
		Confidence:  equipment.Confidence,
	}

	cd.recordChanges([]Change{change})
	return change
}

// DetectRemoval detects equipment removal
func (cd *ChangeDetector) DetectRemoval(equipmentID string) Change {
	change := Change{
		ID:          fmt.Sprintf("change_%d", time.Now().UnixNano()),
		EquipmentID: equipmentID,
		Type:        ChangeTypeRemoved,
		Field:       "equipment",
		OldValue:    equipmentID,
		NewValue:    nil,
		Magnitude:   1.0,
		Timestamp:   time.Now(),
		Confidence:  spatial.ConfidenceMedium, // Can't be certain without verification
	}

	cd.recordChanges([]Change{change})
	return change
}

// GetRecentChanges returns changes within a time window
func (cd *ChangeDetector) GetRecentChanges(since time.Duration) []Change {
	cutoff := time.Now().Add(-since)
	recent := make([]Change, 0)

	for _, change := range cd.history {
		if change.Timestamp.After(cutoff) {
			recent = append(recent, change)
		}
	}

	return recent
}

// GetChangesForEquipment returns all changes for specific equipment
func (cd *ChangeDetector) GetChangesForEquipment(equipmentID string) []Change {
	changes := make([]Change, 0)

	for _, change := range cd.history {
		if change.EquipmentID == equipmentID {
			changes = append(changes, change)
		}
	}

	return changes
}

// GetRelatedChanges finds changes that might be related
func (cd *ChangeDetector) GetRelatedChanges(change Change) []Change {
	related := make([]Change, 0)

	for _, other := range cd.history {
		if other.ID == change.ID {
			continue // Skip self
		}

		// Check if changes are related
		if cd.areChangesRelated(change, other) {
			related = append(related, other)
		}
	}

	return related
}

// areChangesRelated determines if two changes are related
func (cd *ChangeDetector) areChangesRelated(c1, c2 Change) bool {
	// Same equipment
	if c1.EquipmentID == c2.EquipmentID {
		// Within time window
		timeDiff := math.Abs(c1.Timestamp.Sub(c2.Timestamp).Seconds())
		if timeDiff < cd.thresholds.TimeWindow.Seconds() {
			return true
		}
	}

	// Could check spatial proximity for different equipment
	// if positions are available

	return false
}

// VerifyChange marks a change as verified
func (cd *ChangeDetector) VerifyChange(changeID string, verified bool, action string) error {
	for i := range cd.history {
		if cd.history[i].ID == changeID {
			cd.history[i].Verified = verified
			cd.history[i].ActionTaken = action
			return nil
		}
	}
	return fmt.Errorf("change %s not found", changeID)
}

// GetStatistics returns change detection statistics
func (cd *ChangeDetector) GetStatistics() ChangeStatistics {
	stats := ChangeStatistics{
		TotalChanges: len(cd.history),
		ChangesByType: make(map[ChangeType]int),
		VerifiedChanges: 0,
	}

	for _, change := range cd.history {
		stats.ChangesByType[change.Type]++
		if change.Verified {
			stats.VerifiedChanges++
		}
	}

	if stats.TotalChanges > 0 {
		stats.VerificationRate = float64(stats.VerifiedChanges) / float64(stats.TotalChanges)
	}

	// Calculate average magnitude by type
	stats.AverageMagnitude = make(map[ChangeType]float64)
	counts := make(map[ChangeType]int)
	for _, change := range cd.history {
		stats.AverageMagnitude[change.Type] += change.Magnitude
		counts[change.Type]++
	}
	for changeType, sum := range stats.AverageMagnitude {
		if count := counts[changeType]; count > 0 {
			stats.AverageMagnitude[changeType] = sum / float64(count)
		}
	}

	return stats
}

// ChangeStatistics contains statistics about detected changes
type ChangeStatistics struct {
	TotalChanges     int                    `json:"total_changes"`
	ChangesByType    map[ChangeType]int     `json:"changes_by_type"`
	VerifiedChanges  int                    `json:"verified_changes"`
	VerificationRate float64                `json:"verification_rate"`
	AverageMagnitude map[ChangeType]float64 `json:"average_magnitude"`
}

// EnableTracking enables or disables change tracking
func (cd *ChangeDetector) EnableTracking(enabled bool) {
	cd.trackingEnabled = enabled
}

// ClearHistory clears the change history
func (cd *ChangeDetector) ClearHistory() {
	cd.history = make([]Change, 0)
}

// SetMaxHistorySize sets the maximum history size
func (cd *ChangeDetector) SetMaxHistorySize(size int) {
	cd.maxHistorySize = size
	if len(cd.history) > size {
		cd.history = cd.history[len(cd.history)-size:]
	}
}