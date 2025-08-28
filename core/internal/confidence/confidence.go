// Package confidence provides a unified confidence scoring system for ArxOS
package confidence

import (
	"fmt"
	"math"
	"sync"
	"time"
)

// Confidence represents the confidence scores for an ArxObject
// This is the single source of truth for confidence in the system
type Confidence struct {
	Overall        float64                `json:"overall"`         // 0.0 to 1.0 overall confidence
	Classification float64                `json:"classification"`  // How confident in object type
	Position       float64                `json:"position"`        // Spatial accuracy confidence
	Properties     float64                `json:"properties"`      // Property data confidence
	Relationships  float64                `json:"relationships"`   // Connection confidence
	
	// Metadata
	LastUpdated    time.Time              `json:"last_updated"`
	UpdateCount    int                    `json:"update_count"`
	Sources        []Source               `json:"sources"`
	History        []HistoryEntry         `json:"history"`
	
	// Validation tracking
	ValidationCount int                   `json:"validation_count"`
	ValidatorCount  int                   `json:"validator_count"`
	LastValidation  time.Time             `json:"last_validation,omitempty"`
	
	// Internal
	mu             sync.RWMutex
}

// Source represents a data source that contributed to confidence
type Source struct {
	Type        SourceType    `json:"type"`
	Method      string        `json:"method"`
	Confidence  float64       `json:"confidence"`
	Timestamp   time.Time     `json:"timestamp"`
	ValidatorID string        `json:"validator_id,omitempty"`
}

// SourceType defines types of data sources
type SourceType string

const (
	SourceManual      SourceType = "manual"
	SourcePhoto       SourceType = "photo"
	SourceLiDAR       SourceType = "lidar"
	SourceBIM         SourceType = "bim"
	SourcePDF         SourceType = "pdf"
	SourceSensor      SourceType = "sensor"
	SourceValidation  SourceType = "validation"
	SourceComputed    SourceType = "computed"
)

// HistoryEntry tracks confidence changes over time
type HistoryEntry struct {
	Timestamp   time.Time `json:"timestamp"`
	OldOverall  float64   `json:"old_overall"`
	NewOverall  float64   `json:"new_overall"`
	Reason      string    `json:"reason"`
	SourceType  SourceType `json:"source_type"`
}

// UpdateParams contains parameters for updating confidence
type UpdateParams struct {
	Source          Source
	Classification  *float64
	Position        *float64
	Properties      *float64
	Relationships   *float64
	Reason          string
}

// NewConfidence creates a new confidence instance with default values
func NewConfidence() *Confidence {
	return &Confidence{
		Overall:        0.5,  // Default neutral confidence
		Classification: 0.5,
		Position:       0.5,
		Properties:     0.5,
		Relationships:  0.5,
		LastUpdated:    time.Now(),
		Sources:        []Source{},
		History:        []HistoryEntry{},
	}
}

// Update updates confidence scores based on new information
func (c *Confidence) Update(params UpdateParams) {
	c.mu.Lock()
	defer c.mu.Unlock()
	
	oldOverall := c.Overall
	
	// Update individual components if provided
	if params.Classification != nil {
		c.Classification = clamp(*params.Classification, 0, 1)
	}
	if params.Position != nil {
		c.Position = clamp(*params.Position, 0, 1)
	}
	if params.Properties != nil {
		c.Properties = clamp(*params.Properties, 0, 1)
	}
	if params.Relationships != nil {
		c.Relationships = clamp(*params.Relationships, 0, 1)
	}
	
	// Add source
	c.Sources = append(c.Sources, params.Source)
	
	// Keep only last 100 sources
	if len(c.Sources) > 100 {
		c.Sources = c.Sources[len(c.Sources)-100:]
	}
	
	// Recalculate overall confidence
	c.recalculateOverall()
	
	// Update metadata
	c.LastUpdated = time.Now()
	c.UpdateCount++
	
	// Track if this is a validation
	if params.Source.Type == SourceValidation {
		c.ValidationCount++
		c.LastValidation = params.Source.Timestamp
		
		// Track unique validators
		if params.Source.ValidatorID != "" {
			uniqueValidators := make(map[string]bool)
			for _, src := range c.Sources {
				if src.Type == SourceValidation && src.ValidatorID != "" {
					uniqueValidators[src.ValidatorID] = true
				}
			}
			c.ValidatorCount = len(uniqueValidators)
		}
	}
	
	// Add to history if significant change
	if math.Abs(oldOverall-c.Overall) > 0.01 {
		entry := HistoryEntry{
			Timestamp:  time.Now(),
			OldOverall: oldOverall,
			NewOverall: c.Overall,
			Reason:     params.Reason,
			SourceType: params.Source.Type,
		}
		c.History = append(c.History, entry)
		
		// Keep only last 50 history entries
		if len(c.History) > 50 {
			c.History = c.History[len(c.History)-50:]
		}
	}
}

// recalculateOverall recalculates the overall confidence score
func (c *Confidence) recalculateOverall() {
	// Weighted average of components
	weights := map[string]float64{
		"classification": 0.25,
		"position":       0.30,
		"properties":     0.25,
		"relationships":  0.20,
	}
	
	weightedSum := c.Classification*weights["classification"] +
		c.Position*weights["position"] +
		c.Properties*weights["properties"] +
		c.Relationships*weights["relationships"]
	
	// Apply source quality multiplier
	sourceMultiplier := c.calculateSourceMultiplier()
	
	// Apply time decay
	timeDecay := c.calculateTimeDecay()
	
	// Apply validation bonus
	validationBonus := c.calculateValidationBonus()
	
	// Combine all factors
	c.Overall = clamp(weightedSum*sourceMultiplier*timeDecay+validationBonus, 0, 1)
}

// calculateSourceMultiplier calculates confidence multiplier based on sources
func (c *Confidence) calculateSourceMultiplier() float64 {
	if len(c.Sources) == 0 {
		return 0.5
	}
	
	// Source type quality weights
	sourceWeights := map[SourceType]float64{
		SourceLiDAR:      1.0,
		SourceBIM:        0.9,
		SourceValidation: 0.85,
		SourcePhoto:      0.7,
		SourceSensor:     0.8,
		SourcePDF:        0.6,
		SourceManual:     0.5,
		SourceComputed:   0.4,
	}
	
	// Calculate average source quality
	totalQuality := 0.0
	for _, source := range c.Sources {
		weight := sourceWeights[source.Type]
		if weight == 0 {
			weight = 0.5
		}
		totalQuality += weight * source.Confidence
	}
	
	avgQuality := totalQuality / float64(len(c.Sources))
	
	// Bonus for multiple source types (diversity)
	sourceTypes := make(map[SourceType]bool)
	for _, source := range c.Sources {
		sourceTypes[source.Type] = true
	}
	diversityBonus := math.Min(float64(len(sourceTypes))*0.05, 0.25)
	
	return math.Min(avgQuality+diversityBonus, 1.2)
}

// calculateTimeDecay calculates confidence decay over time
func (c *Confidence) calculateTimeDecay() float64 {
	if c.LastUpdated.IsZero() {
		return 1.0
	}
	
	daysSinceUpdate := time.Since(c.LastUpdated).Hours() / 24
	
	// Different decay rates based on data type
	decayRate := 90.0 // 90-day half-life by default
	
	// Slower decay if validated recently
	if !c.LastValidation.IsZero() {
		daysSinceValidation := time.Since(c.LastValidation).Hours() / 24
		if daysSinceValidation < 30 {
			decayRate = 180.0 // 180-day half-life for validated data
		}
	}
	
	// Exponential decay
	decay := math.Exp(-daysSinceUpdate / decayRate)
	
	// Minimum confidence retention
	return math.Max(decay, 0.3)
}

// calculateValidationBonus calculates bonus for validated data
func (c *Confidence) calculateValidationBonus() float64 {
	if c.ValidationCount == 0 {
		return 0
	}
	
	// Base bonus for any validation
	bonus := 0.05
	
	// Additional bonus for multiple validations (diminishing returns)
	bonus += math.Min(float64(c.ValidationCount)*0.02, 0.15)
	
	// Bonus for multiple validators (diversity)
	if c.ValidatorCount > 1 {
		bonus += math.Min(float64(c.ValidatorCount)*0.03, 0.10)
	}
	
	return bonus
}

// GetOverall returns the overall confidence score
func (c *Confidence) GetOverall() float64 {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.Overall
}

// GetComponents returns all component confidence scores
func (c *Confidence) GetComponents() (classification, position, properties, relationships float64) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.Classification, c.Position, c.Properties, c.Relationships
}

// IsHighConfidence returns true if overall confidence is high (>0.8)
func (c *Confidence) IsHighConfidence() bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.Overall > 0.8
}

// IsLowConfidence returns true if overall confidence is low (<0.5)
func (c *Confidence) IsLowConfidence() bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.Overall < 0.5
}

// NeedsValidation returns true if the object needs validation
func (c *Confidence) NeedsValidation() bool {
	c.mu.RLock()
	defer c.mu.RUnlock()
	
	// Needs validation if:
	// 1. Never validated
	if c.ValidationCount == 0 {
		return true
	}
	
	// 2. Low confidence
	if c.Overall < 0.6 {
		return true
	}
	
	// 3. Old validation (>60 days)
	if !c.LastValidation.IsZero() {
		daysSinceValidation := time.Since(c.LastValidation).Hours() / 24
		if daysSinceValidation > 60 {
			return true
		}
	}
	
	return false
}

// GetValidationStats returns validation statistics
func (c *Confidence) GetValidationStats() (count int, validators int, lastValidation time.Time) {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.ValidationCount, c.ValidatorCount, c.LastValidation
}

// String returns a string representation of confidence
func (c *Confidence) String() string {
	c.mu.RLock()
	defer c.mu.RUnlock()
	
	return fmt.Sprintf("Confidence{Overall:%.2f, Class:%.2f, Pos:%.2f, Props:%.2f, Rels:%.2f, Updates:%d, Validations:%d}",
		c.Overall, c.Classification, c.Position, c.Properties, c.Relationships,
		c.UpdateCount, c.ValidationCount)
}

// Clone creates a deep copy of the confidence
func (c *Confidence) Clone() *Confidence {
	c.mu.RLock()
	defer c.mu.RUnlock()
	
	clone := &Confidence{
		Overall:        c.Overall,
		Classification: c.Classification,
		Position:       c.Position,
		Properties:     c.Properties,
		Relationships:  c.Relationships,
		LastUpdated:    c.LastUpdated,
		UpdateCount:    c.UpdateCount,
		ValidationCount: c.ValidationCount,
		ValidatorCount:  c.ValidatorCount,
		LastValidation:  c.LastValidation,
	}
	
	// Clone sources
	clone.Sources = make([]Source, len(c.Sources))
	copy(clone.Sources, c.Sources)
	
	// Clone history
	clone.History = make([]HistoryEntry, len(c.History))
	copy(clone.History, c.History)
	
	return clone
}

// Merge merges confidence from another source
func (c *Confidence) Merge(other *Confidence) {
	if other == nil {
		return
	}
	
	c.mu.Lock()
	defer c.mu.Unlock()
	other.mu.RLock()
	defer other.mu.RUnlock()
	
	// Weighted average based on update counts
	totalUpdates := float64(c.UpdateCount + other.UpdateCount)
	if totalUpdates == 0 {
		return
	}
	
	w1 := float64(c.UpdateCount) / totalUpdates
	w2 := float64(other.UpdateCount) / totalUpdates
	
	// Merge components
	c.Classification = w1*c.Classification + w2*other.Classification
	c.Position = w1*c.Position + w2*other.Position
	c.Properties = w1*c.Properties + w2*other.Properties
	c.Relationships = w1*c.Relationships + w2*other.Relationships
	
	// Merge metadata
	c.UpdateCount += other.UpdateCount
	c.ValidationCount += other.ValidationCount
	
	// Merge sources (keep unique)
	c.Sources = append(c.Sources, other.Sources...)
	if len(c.Sources) > 100 {
		c.Sources = c.Sources[len(c.Sources)-100:]
	}
	
	// Recalculate
	c.recalculateOverall()
}

// Helper functions

func clamp(value, min, max float64) float64 {
	if value < min {
		return min
	}
	if value > max {
		return max
	}
	return value
}

// ConfidenceLevel returns a human-readable confidence level
func (c *Confidence) ConfidenceLevel() string {
	overall := c.GetOverall()
	
	switch {
	case overall >= 0.9:
		return "Very High"
	case overall >= 0.75:
		return "High"
	case overall >= 0.6:
		return "Medium"
	case overall >= 0.4:
		return "Low"
	default:
		return "Very Low"
	}
}

// Color returns a color code for the confidence level (for UI)
func (c *Confidence) Color() string {
	overall := c.GetOverall()
	
	switch {
	case overall >= 0.8:
		return "green"
	case overall >= 0.6:
		return "yellow"
	case overall >= 0.4:
		return "orange"
	default:
		return "red"
	}
}