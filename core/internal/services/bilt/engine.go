// Package bilt implements the BILT (Building Infrastructure Labor Token) system
// that rewards field workers for contributing building data
package bilt

import (
	"fmt"
	"math"
	"sync"
	"time"
)

// BILTEngine manages token rewards for data contributions
type BILTEngine struct {
	mu              sync.RWMutex
	ledger          *Ledger
	rates           map[string]float64
	qualityWeights  QualityWeights
	minimumQuality  float64
	bonusMultipliers map[string]float64
}

// DataContribution represents a field worker's data submission
type DataContribution struct {
	UserID      string
	Timestamp   time.Time
	ObjectPath  string                 // e.g., /electrical/main-panel/circuit-7/outlet-3
	DataType    string                 // scan, validation, measurement, photo, annotation
	Data        map[string]interface{} // The actual data contributed
	Confidence  float64                // Field worker's confidence in the data
	Duration    time.Duration          // Time spent collecting data
	DeviceType  string                 // mobile, tablet, scanner
	Location    Location               // GPS coordinates if available
}

// QualityScore represents the assessed quality of contributed data
type QualityScore struct {
	Overall      float64   // 0.0 to 1.0 overall quality score
	Accuracy     float64   // How accurate is the data
	Completeness float64   // How complete is the submission
	Consistency  float64   // Consistency with existing data
	Freshness    float64   // How recent/relevant is the data
	Validation   float64   // Validation against known constraints
	Details      string    // Human-readable quality assessment
}

// QualityWeights defines importance of each quality dimension
type QualityWeights struct {
	Accuracy     float64
	Completeness float64
	Consistency  float64
	Freshness    float64
	Validation   float64
}

// Location represents GPS coordinates
type Location struct {
	Latitude  float64
	Longitude float64
	Altitude  float64
	Accuracy  float64 // meters
}

// ArxObject represents building object for quality assessment
type ArxObject struct {
	Path        string
	Type        string
	Properties  map[string]interface{}
	Confidence  float64
	LastUpdated time.Time
	UpdateCount int
	Validators  []string // Users who have validated this data
}

// NewBILTEngine creates a new BILT token reward engine
func NewBILTEngine() *BILTEngine {
	engine := &BILTEngine{
		ledger:         NewLedger(),
		rates:          defaultEarningRates(),
		qualityWeights: defaultQualityWeights(),
		minimumQuality: 0.5, // Minimum quality score to earn tokens
		bonusMultipliers: defaultBonusMultipliers(),
	}
	
	return engine
}

// CalculateReward calculates BILT tokens earned for a contribution
func (be *BILTEngine) CalculateReward(contribution DataContribution) float64 {
	be.mu.RLock()
	defer be.mu.RUnlock()
	
	// Get base rate for this type of contribution
	baseRate := be.GetEarningRate(contribution.DataType)
	if baseRate == 0 {
		return 0
	}
	
	// Create ArxObject from contribution for quality assessment
	obj := ArxObject{
		Path:        contribution.ObjectPath,
		Type:        extractObjectType(contribution.ObjectPath),
		Properties:  contribution.Data,
		Confidence:  contribution.Confidence,
		LastUpdated: contribution.Timestamp,
	}
	
	// Assess quality of the contribution
	quality := be.AssessQuality(obj)
	
	// Don't reward if quality is too low
	if quality.Overall < be.minimumQuality {
		return 0
	}
	
	// Calculate base reward
	reward := baseRate * quality.Overall
	
	// Apply complexity multiplier based on data type and completeness
	complexityMultiplier := be.calculateComplexityMultiplier(contribution)
	reward *= complexityMultiplier
	
	// Apply time-based bonus (reward faster submissions)
	if contribution.Duration > 0 && contribution.Duration < 5*time.Minute {
		speedBonus := 1.0 + (5.0-contribution.Duration.Minutes())/10.0
		reward *= speedBonus
	}
	
	// Apply location accuracy bonus if GPS data is available
	if contribution.Location.Accuracy > 0 && contribution.Location.Accuracy < 5 {
		locationBonus := 1.0 + (5.0-contribution.Location.Accuracy)/20.0
		reward *= locationBonus
	}
	
	// Apply bonus multipliers for special conditions
	reward = be.applyBonuses(contribution, reward)
	
	// Round to 4 decimal places
	return math.Round(reward*10000) / 10000
}

// AssessQuality evaluates the quality of submitted data
func (be *BILTEngine) AssessQuality(data ArxObject) QualityScore {
	be.mu.RLock()
	defer be.mu.RUnlock()
	
	score := QualityScore{
		Accuracy:     be.assessAccuracy(data),
		Completeness: be.assessCompleteness(data),
		Consistency:  be.assessConsistency(data),
		Freshness:    be.assessFreshness(data),
		Validation:   be.assessValidation(data),
	}
	
	// Calculate weighted overall score
	score.Overall = (score.Accuracy * be.qualityWeights.Accuracy +
		score.Completeness * be.qualityWeights.Completeness +
		score.Consistency * be.qualityWeights.Consistency +
		score.Freshness * be.qualityWeights.Freshness +
		score.Validation * be.qualityWeights.Validation)
	
	// Generate quality details
	score.Details = be.generateQualityDetails(score)
	
	return score
}

// RecordEarning records BILT tokens earned by a user
func (be *BILTEngine) RecordEarning(userID string, amount float64, reason string) error {
	be.mu.Lock()
	defer be.mu.Unlock()
	
	if amount <= 0 {
		return fmt.Errorf("earning amount must be positive")
	}
	
	transaction := Transaction{
		ID:        generateTransactionID(),
		UserID:    userID,
		Amount:    amount,
		Type:      "earning",
		Reason:    reason,
		Timestamp: time.Now(),
		Status:    "completed",
	}
	
	return be.ledger.RecordTransaction(transaction)
}

// GetEarningRate returns the BILT token rate for a process type
func (be *BILTEngine) GetEarningRate(processType string) float64 {
	be.mu.RLock()
	defer be.mu.RUnlock()
	
	if rate, exists := be.rates[processType]; exists {
		return rate
	}
	
	// Return default rate for unknown types
	return be.rates["default"]
}

// SetEarningRate updates the earning rate for a process type
func (be *BILTEngine) SetEarningRate(processType string, rate float64) {
	be.mu.Lock()
	defer be.mu.Unlock()
	
	be.rates[processType] = rate
}

// GetUserBalance returns the current BILT token balance for a user
func (be *BILTEngine) GetUserBalance(userID string) (float64, error) {
	be.mu.RLock()
	defer be.mu.RUnlock()
	
	return be.ledger.GetBalance(userID)
}

// GetUserHistory returns the earning history for a user
func (be *BILTEngine) GetUserHistory(userID string, limit int) ([]Transaction, error) {
	be.mu.RLock()
	defer be.mu.RUnlock()
	
	return be.ledger.GetUserHistory(userID, limit)
}

// ProcessContribution handles a complete data contribution workflow
func (be *BILTEngine) ProcessContribution(contribution DataContribution) (*ContributionResult, error) {
	// Calculate reward
	reward := be.CalculateReward(contribution)
	
	if reward > 0 {
		// Record the earning
		reason := fmt.Sprintf("%s contribution at %s", 
			contribution.DataType, contribution.ObjectPath)
		
		err := be.RecordEarning(contribution.UserID, reward, reason)
		if err != nil {
			return nil, fmt.Errorf("failed to record earning: %w", err)
		}
	}
	
	// Create result
	result := &ContributionResult{
		ContributionID: generateContributionID(),
		UserID:         contribution.UserID,
		Timestamp:      contribution.Timestamp,
		ObjectPath:     contribution.ObjectPath,
		DataType:       contribution.DataType,
		TokensEarned:   reward,
		QualityScore:   be.AssessQuality(ArxObject{
			Path:        contribution.ObjectPath,
			Properties:  contribution.Data,
			Confidence:  contribution.Confidence,
			LastUpdated: contribution.Timestamp,
		}),
		Status:         "accepted",
	}
	
	if reward == 0 {
		result.Status = "rejected_low_quality"
	}
	
	return result, nil
}

// Helper functions

func (be *BILTEngine) assessAccuracy(data ArxObject) float64 {
	// Check confidence level
	accuracyScore := data.Confidence
	
	// Check if data falls within expected ranges
	if data.Type == "outlet" {
		if voltage, ok := data.Properties["voltage"].(float64); ok {
			// Voltage should be around 120V or 240V
			if (voltage >= 110 && voltage <= 130) || (voltage >= 230 && voltage <= 250) {
				accuracyScore = (accuracyScore + 1.0) / 2.0
			} else {
				accuracyScore *= 0.5 // Penalize unrealistic values
			}
		}
	}
	
	return math.Min(accuracyScore, 1.0)
}

func (be *BILTEngine) assessCompleteness(data ArxObject) float64 {
	requiredFields := getRequiredFields(data.Type)
	if len(requiredFields) == 0 {
		return 1.0 // No required fields defined
	}
	
	presentCount := 0
	for _, field := range requiredFields {
		if _, exists := data.Properties[field]; exists {
			presentCount++
		}
	}
	
	return float64(presentCount) / float64(len(requiredFields))
}

func (be *BILTEngine) assessConsistency(data ArxObject) float64 {
	// Check internal consistency of data
	consistency := 1.0
	
	// Example: For electrical components, check power calculations
	if data.Type == "outlet" || data.Type == "circuit" {
		voltage, hasVoltage := data.Properties["voltage"].(float64)
		current, hasCurrent := data.Properties["load"].(float64)
		power, hasPower := data.Properties["power"].(float64)
		
		if hasVoltage && hasCurrent && hasPower {
			calculatedPower := voltage * current
			deviation := math.Abs(calculatedPower-power) / power
			if deviation > 0.1 { // More than 10% deviation
				consistency *= (1.0 - deviation)
			}
		}
	}
	
	return math.Max(consistency, 0.0)
}

func (be *BILTEngine) assessFreshness(data ArxObject) float64 {
	age := time.Since(data.LastUpdated)
	
	// Data loses value over time
	if age < 24*time.Hour {
		return 1.0
	} else if age < 7*24*time.Hour {
		return 0.9
	} else if age < 30*24*time.Hour {
		return 0.7
	} else if age < 90*24*time.Hour {
		return 0.5
	}
	
	return 0.3 // Very old data still has some value
}

func (be *BILTEngine) assessValidation(data ArxObject) float64 {
	// Check if data has been validated by others
	validatorCount := len(data.Validators)
	
	switch validatorCount {
	case 0:
		return 0.6 // Unvalidated
	case 1:
		return 0.8 // Single validation
	case 2:
		return 0.9 // Double validation
	default:
		return 1.0 // Triple+ validation
	}
}

func (be *BILTEngine) calculateComplexityMultiplier(contribution DataContribution) float64 {
	multiplier := 1.0
	
	// More complex data types get higher multipliers
	switch contribution.DataType {
	case "scan":
		multiplier = 1.5 // 3D scanning is complex
	case "measurement":
		multiplier = 1.2 // Physical measurements
	case "validation":
		multiplier = 1.0 // Basic validation
	case "photo":
		multiplier = 0.8 // Simple photo
	case "annotation":
		multiplier = 0.6 // Text annotation
	}
	
	// More data fields = higher complexity
	fieldCount := len(contribution.Data)
	if fieldCount > 10 {
		multiplier *= 1.3
	} else if fieldCount > 5 {
		multiplier *= 1.1
	}
	
	return multiplier
}

func (be *BILTEngine) applyBonuses(contribution DataContribution, baseReward float64) float64 {
	reward := baseReward
	
	// Check for special bonuses
	for condition, multiplier := range be.bonusMultipliers {
		switch condition {
		case "first_scan":
			if be.isFirstScan(contribution.ObjectPath) {
				reward *= multiplier
			}
		case "critical_system":
			if isCriticalSystem(contribution.ObjectPath) {
				reward *= multiplier
			}
		case "after_hours":
			if isAfterHours(contribution.Timestamp) {
				reward *= multiplier
			}
		case "high_precision":
			if contribution.Location.Accuracy < 1.0 {
				reward *= multiplier
			}
		}
	}
	
	return reward
}

func (be *BILTEngine) isFirstScan(objectPath string) bool {
	// Check if this is the first time this object has been scanned
	// In production, this would query the database
	return false // Placeholder
}

func (be *BILTEngine) generateQualityDetails(score QualityScore) string {
	details := fmt.Sprintf("Quality Assessment (%.2f):\n", score.Overall)
	details += fmt.Sprintf("  Accuracy: %.2f\n", score.Accuracy)
	details += fmt.Sprintf("  Completeness: %.2f\n", score.Completeness)
	details += fmt.Sprintf("  Consistency: %.2f\n", score.Consistency)
	details += fmt.Sprintf("  Freshness: %.2f\n", score.Freshness)
	details += fmt.Sprintf("  Validation: %.2f\n", score.Validation)
	
	if score.Overall >= 0.9 {
		details += "Rating: Excellent"
	} else if score.Overall >= 0.7 {
		details += "Rating: Good"
	} else if score.Overall >= 0.5 {
		details += "Rating: Acceptable"
	} else {
		details += "Rating: Poor (below minimum threshold)"
	}
	
	return details
}