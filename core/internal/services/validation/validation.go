// Package validation implements field validation rewards and confidence scoring
package validation

import (
	"fmt"
	"math"
	"strings"
	"sync"
	"time"

	"github.com/arxos/arxos/core/internal/arxobject"
	"github.com/arxos/arxos/core/internal/services/bilt"
)

// ValidationEngine manages field validations and confidence scoring
type ValidationEngine struct {
	mu              sync.RWMutex
	biltEngine      *bilt.BILTEngine
	validations     map[string][]Validation      // Object ID -> validations
	confidence      map[string]ConfidenceScore   // Object ID -> confidence
	validators      map[string]ValidatorProfile  // User ID -> profile
	importanceMap   map[string]float64          // Object type -> importance weight
	rewardRates     map[ValidationType]float64  // Validation type -> base BILT rate
}

// Validation represents a field validation contribution
type Validation struct {
	ID             string                 `json:"id"`
	ObjectID       string                 `json:"object_id"`
	ObjectPath     string                 `json:"object_path"`
	ValidatorID    string                 `json:"validator_id"`
	Type           ValidationType         `json:"type"`
	Method         ValidationMethod       `json:"method"`
	Timestamp      time.Time             `json:"timestamp"`
	Data           map[string]interface{} `json:"data"`
	Confidence     float64               `json:"confidence"`      // Individual confidence
	Quality        float64               `json:"quality"`         // Quality score
	PhotoURLs      []string              `json:"photo_urls,omitempty"`
	LiDARData      *LiDARScan           `json:"lidar_data,omitempty"`
	Measurements   []Measurement         `json:"measurements,omitempty"`
	Notes          string                `json:"notes,omitempty"`
	TokensEarned   float64               `json:"tokens_earned"`
	Status         ValidationStatus      `json:"status"`
}

// ValidationType defines types of validation
type ValidationType string

const (
	ValidationPhoto          ValidationType = "photo"
	ValidationLiDAR          ValidationType = "lidar"
	ValidationManualMeasure  ValidationType = "manual_measure"
	ValidationVisualInspect  ValidationType = "visual_inspect"
	ValidationFunctionalTest ValidationType = "functional_test"
	ValidationThermographic  ValidationType = "thermographic"
	ValidationAcoustic       ValidationType = "acoustic"
	ValidationVibration      ValidationType = "vibration"
)

// ValidationMethod defines the method used
type ValidationMethod string

const (
	MethodMobile      ValidationMethod = "mobile_app"
	MethodARKit       ValidationMethod = "arkit"
	MethodLiDARPro    ValidationMethod = "lidar_pro"
	MethodManual      ValidationMethod = "manual_tools"
	MethodDrone       ValidationMethod = "drone"
	MethodRobot       ValidationMethod = "robot"
)

// ValidationStatus represents validation status
type ValidationStatus string

const (
	StatusPending   ValidationStatus = "pending"
	StatusAccepted  ValidationStatus = "accepted"
	StatusRejected  ValidationStatus = "rejected"
	StatusDisputed  ValidationStatus = "disputed"
)

// ConfidenceScore represents aggregated confidence for an object
type ConfidenceScore struct {
	Overall          float64              `json:"overall"`           // 0.0 to 1.0
	Dimensional      float64              `json:"dimensional"`       // Physical dimensions
	Functional       float64              `json:"functional"`        // Operational status
	Visual           float64              `json:"visual"`           // Visual appearance
	Location         float64              `json:"location"`         // Spatial position
	LastValidation   time.Time           `json:"last_validation"`
	ValidationCount  int                 `json:"validation_count"`
	ValidatorCount   int                 `json:"validator_count"`   // Unique validators
	MethodCoverage   map[string]bool     `json:"method_coverage"`   // Methods used
	ConsensusData    map[string]interface{} `json:"consensus_data"` // Agreed upon values
}

// ValidatorProfile tracks validator statistics
type ValidatorProfile struct {
	UserID           string              `json:"user_id"`
	TotalValidations int                 `json:"total_validations"`
	AccuracyScore    float64             `json:"accuracy_score"`
	Specializations  []string            `json:"specializations"`
	CertificationLevel int               `json:"certification_level"` // 0-5
	TrustedValidator bool                `json:"trusted_validator"`
	TokensEarned     float64             `json:"tokens_earned"`
	Streak           int                 `json:"streak"`            // Consecutive days
	LastValidation   time.Time           `json:"last_validation"`
}

// LiDARScan represents LiDAR scan data
type LiDARScan struct {
	PointCount      int                    `json:"point_count"`
	Accuracy        float64                `json:"accuracy_mm"`
	ScanDuration    time.Duration          `json:"scan_duration"`
	DeviceModel     string                 `json:"device_model"`
	PointCloud      []Point3D              `json:"-"` // Large data, stored separately
	BoundingBox     BoundingBox            `json:"bounding_box"`
	Features        []DetectedFeature      `json:"features"`
	ProcessingTime  time.Duration          `json:"processing_time"`
}

// Measurement represents a manual measurement
type Measurement struct {
	Type      string  `json:"type"`      // length, width, height, diameter, etc.
	Value     float64 `json:"value"`      // In millimeters
	Unit      string  `json:"unit"`       // mm, cm, m
	Tool      string  `json:"tool"`       // tape_measure, laser_distance, caliper
	Accuracy  float64 `json:"accuracy"`   // ± mm
	Timestamp time.Time `json:"timestamp"`
}

// Point3D represents a 3D point
type Point3D struct {
	X, Y, Z float64
	R, G, B uint8 // Color if available
}

// BoundingBox represents 3D bounding box
type BoundingBox struct {
	MinX, MinY, MinZ float64
	MaxX, MaxY, MaxZ float64
}

// DetectedFeature represents a feature detected in scan
type DetectedFeature struct {
	Type       string      `json:"type"`       // outlet, pipe, duct, etc.
	Confidence float64     `json:"confidence"`
	Location   Point3D     `json:"location"`
	Dimensions BoundingBox `json:"dimensions"`
}

// NewValidationEngine creates a new validation engine
func NewValidationEngine(biltEngine *bilt.BILTEngine) *ValidationEngine {
	engine := &ValidationEngine{
		biltEngine:    biltEngine,
		validations:   make(map[string][]Validation),
		confidence:    make(map[string]ConfidenceScore),
		validators:    make(map[string]ValidatorProfile),
		importanceMap: defaultImportanceWeights(),
		rewardRates:   defaultValidationRates(),
	}
	
	return engine
}

// SubmitValidation processes a new field validation
func (e *ValidationEngine) SubmitValidation(validation *Validation) (*ValidationResult, error) {
	e.mu.Lock()
	defer e.mu.Unlock()
	
	// Generate ID if not set
	if validation.ID == "" {
		validation.ID = generateValidationID()
	}
	
	// Set timestamp
	validation.Timestamp = time.Now()
	validation.Status = StatusPending
	
	// Calculate quality score
	quality := e.assessValidationQuality(validation)
	validation.Quality = quality
	
	// Calculate reward
	reward := e.calculateValidationReward(validation)
	validation.TokensEarned = reward
	
	// Update validator profile
	e.updateValidatorProfile(validation.ValidatorID, validation)
	
	// Process validation based on quality
	if quality >= 0.5 {
		validation.Status = StatusAccepted
		
		// Record BILT earning
		if reward > 0 {
			reason := fmt.Sprintf("%s validation of %s", validation.Type, validation.ObjectPath)
			e.biltEngine.RecordEarning(validation.ValidatorID, reward, reason)
		}
		
		// Update object confidence
		e.updateObjectConfidence(validation.ObjectID, validation)
		
		// Store validation
		e.validations[validation.ObjectID] = append(e.validations[validation.ObjectID], *validation)
	} else {
		validation.Status = StatusRejected
	}
	
	// Create result
	result := &ValidationResult{
		ValidationID:   validation.ID,
		Status:         validation.Status,
		TokensEarned:   validation.TokensEarned,
		QualityScore:   quality,
		NewConfidence:  e.confidence[validation.ObjectID],
		ImprovementTips: e.generateImprovementTips(validation),
	}
	
	return result, nil
}

// calculateValidationReward calculates BILT tokens for validation
func (e *ValidationEngine) calculateValidationReward(validation *Validation) float64 {
	// Base rate from validation type
	baseRate := e.rewardRates[validation.Type]
	
	// Quality multiplier (0.5 to 1.5)
	qualityMultiplier := 0.5 + validation.Quality
	
	// Importance weight based on object type
	importanceWeight := e.getImportanceWeight(validation.ObjectPath)
	
	// Progressive validation bonus
	progressiveBonus := e.calculateProgressiveBonus(validation.ObjectID)
	
	// Validator level bonus
	validatorBonus := e.getValidatorBonus(validation.ValidatorID)
	
	// Calculate total reward
	reward := baseRate * qualityMultiplier * importanceWeight * progressiveBonus * validatorBonus
	
	// Apply special bonuses
	reward = e.applySpecialBonuses(validation, reward)
	
	// Round to 2 decimal places
	return math.Round(reward*100) / 100
}

// assessValidationQuality evaluates the quality of a validation
func (e *ValidationEngine) assessValidationQuality(validation *Validation) float64 {
	quality := 0.0
	weights := 0.0
	
	// Type-specific quality assessment
	switch validation.Type {
	case ValidationLiDAR:
		quality += e.assessLiDARQuality(validation.LiDARData) * 3.0
		weights += 3.0
		
	case ValidationPhoto:
		quality += e.assessPhotoQuality(validation.PhotoURLs) * 2.0
		weights += 2.0
		
	case ValidationManualMeasure:
		quality += e.assessMeasurementQuality(validation.Measurements) * 1.5
		weights += 1.5
		
	case ValidationFunctionalTest:
		quality += e.assessFunctionalTestQuality(validation.Data) * 2.5
		weights += 2.5
	}
	
	// Common quality factors
	
	// Completeness of data
	if validation.Data != nil && len(validation.Data) > 0 {
		completeness := float64(len(validation.Data)) / 10.0 // Expect ~10 fields
		if completeness > 1.0 {
			completeness = 1.0
		}
		quality += completeness * 1.0
		weights += 1.0
	}
	
	// Notes and documentation
	if validation.Notes != "" && len(validation.Notes) > 50 {
		quality += 0.8
		weights += 0.8
	}
	
	// Method quality
	methodQuality := e.getMethodQuality(validation.Method)
	quality += methodQuality * 1.0
	weights += 1.0
	
	// Validator reputation
	if profile, exists := e.validators[validation.ValidatorID]; exists {
		quality += profile.AccuracyScore * 0.5
		weights += 0.5
	}
	
	// Normalize to 0-1
	if weights > 0 {
		return math.Min(quality/weights, 1.0)
	}
	
	return 0.5 // Default quality
}

// updateObjectConfidence updates confidence score for an object
func (e *ValidationEngine) updateObjectConfidence(objectID string, validation *Validation) {
	confidence, exists := e.confidence[objectID]
	if !exists {
		confidence = ConfidenceScore{
			MethodCoverage: make(map[string]bool),
			ConsensusData:  make(map[string]interface{}),
		}
	}
	
	// Get all validations for this object
	objectValidations := e.validations[objectID]
	
	// Count unique validators
	validators := make(map[string]bool)
	for _, v := range objectValidations {
		validators[v.ValidatorID] = true
	}
	validators[validation.ValidatorID] = true
	
	// Update counts
	confidence.ValidationCount = len(objectValidations) + 1
	confidence.ValidatorCount = len(validators)
	confidence.LastValidation = validation.Timestamp
	
	// Update method coverage
	confidence.MethodCoverage[string(validation.Type)] = true
	
	// Calculate dimension confidence (based on measurements and LiDAR)
	dimensionalValidations := 0
	dimensionalScore := 0.0
	
	for _, v := range append(objectValidations, *validation) {
		if v.Type == ValidationLiDAR || v.Type == ValidationManualMeasure {
			dimensionalValidations++
			dimensionalScore += v.Quality * v.Confidence
		}
	}
	
	if dimensionalValidations > 0 {
		confidence.Dimensional = math.Min(dimensionalScore/float64(dimensionalValidations), 1.0)
	}
	
	// Calculate functional confidence
	functionalValidations := 0
	functionalScore := 0.0
	
	for _, v := range append(objectValidations, *validation) {
		if v.Type == ValidationFunctionalTest {
			functionalValidations++
			functionalScore += v.Quality * v.Confidence
		}
	}
	
	if functionalValidations > 0 {
		confidence.Functional = math.Min(functionalScore/float64(functionalValidations), 1.0)
	}
	
	// Calculate visual confidence
	visualValidations := 0
	visualScore := 0.0
	
	for _, v := range append(objectValidations, *validation) {
		if v.Type == ValidationPhoto || v.Type == ValidationVisualInspect {
			visualValidations++
			visualScore += v.Quality * v.Confidence
		}
	}
	
	if visualValidations > 0 {
		confidence.Visual = math.Min(visualScore/float64(visualValidations), 1.0)
	}
	
	// Calculate overall confidence using progressive formula
	confidence.Overall = e.calculateProgressiveConfidence(confidence)
	
	// Update consensus data
	e.updateConsensusData(&confidence, validation)
	
	// Store updated confidence
	e.confidence[objectID] = confidence
}

// calculateProgressiveConfidence uses progressive validation formula
func (e *ValidationEngine) calculateProgressiveConfidence(conf ConfidenceScore) float64 {
	// Base confidence from validation count
	countConfidence := math.Min(float64(conf.ValidationCount)*0.1, 0.5) // Max 0.5 from count
	
	// Validator diversity bonus
	diversityBonus := math.Min(float64(conf.ValidatorCount)*0.05, 0.2) // Max 0.2 from diversity
	
	// Method coverage bonus
	methodBonus := float64(len(conf.MethodCoverage)) * 0.05 // 0.05 per method type
	if methodBonus > 0.2 {
		methodBonus = 0.2
	}
	
	// Component scores weighted average
	componentScore := (conf.Dimensional*0.4 + conf.Functional*0.3 + 
	                  conf.Visual*0.2 + conf.Location*0.1)
	
	// Time decay factor (confidence decreases over time)
	daysSinceValidation := time.Since(conf.LastValidation).Hours() / 24
	timeFactor := math.Exp(-daysSinceValidation / 90) // 90-day half-life
	
	// Combine all factors
	overall := (countConfidence + diversityBonus + methodBonus + componentScore*0.5) * timeFactor
	
	return math.Min(overall, 1.0)
}

// calculateProgressiveBonus calculates bonus for progressive validation
func (e *ValidationEngine) calculateProgressiveBonus(objectID string) float64 {
	confidence, exists := e.confidence[objectID]
	if !exists {
		return 1.5 // First validation bonus
	}
	
	// Bonus decreases as confidence increases (encourage early validation)
	// Low confidence = high bonus, high confidence = low bonus
	return 1.0 + (1.0-confidence.Overall)*0.5
}

// getValidatorBonus returns bonus multiplier based on validator profile
func (e *ValidationEngine) getValidatorBonus(validatorID string) float64 {
	profile, exists := e.validators[validatorID]
	if !exists {
		return 1.0
	}
	
	bonus := 1.0
	
	// Certification level bonus (0-5 levels)
	bonus += float64(profile.CertificationLevel) * 0.1
	
	// Trusted validator bonus
	if profile.TrustedValidator {
		bonus += 0.2
	}
	
	// Streak bonus (consecutive days)
	if profile.Streak > 0 {
		streakBonus := math.Min(float64(profile.Streak)*0.02, 0.3) // Max 30% for 15+ day streak
		bonus += streakBonus
	}
	
	// Accuracy bonus
	if profile.AccuracyScore > 0.9 {
		bonus += 0.15
	} else if profile.AccuracyScore > 0.8 {
		bonus += 0.1
	}
	
	return bonus
}

// applySpecialBonuses applies special circumstance bonuses
func (e *ValidationEngine) applySpecialBonuses(validation *Validation, baseReward float64) float64 {
	reward := baseReward
	
	// Critical system bonus
	if e.isCriticalSystem(validation.ObjectPath) {
		reward *= 1.5
	}
	
	// After-hours bonus
	hour := validation.Timestamp.Hour()
	if hour < 6 || hour > 18 {
		reward *= 1.2
	}
	
	// Weekend bonus
	if validation.Timestamp.Weekday() == time.Saturday || 
	   validation.Timestamp.Weekday() == time.Sunday {
		reward *= 1.3
	}
	
	// High-precision bonus (for measurements)
	if validation.Type == ValidationManualMeasure && len(validation.Measurements) > 0 {
		avgAccuracy := 0.0
		for _, m := range validation.Measurements {
			avgAccuracy += m.Accuracy
		}
		avgAccuracy /= float64(len(validation.Measurements))
		
		if avgAccuracy < 1.0 { // Sub-millimeter accuracy
			reward *= 1.4
		} else if avgAccuracy < 5.0 { // High accuracy
			reward *= 1.2
		}
	}
	
	// Multiple validation types in one submission
	methodCount := 0
	if len(validation.PhotoURLs) > 0 {
		methodCount++
	}
	if validation.LiDARData != nil {
		methodCount++
	}
	if len(validation.Measurements) > 0 {
		methodCount++
	}
	if methodCount > 1 {
		reward *= (1.0 + float64(methodCount-1)*0.15) // 15% per additional method
	}
	
	return reward
}

// Helper assessment functions

func (e *ValidationEngine) assessLiDARQuality(lidar *LiDARScan) float64 {
	if lidar == nil {
		return 0
	}
	
	quality := 0.5 // Base quality
	
	// Point density
	if lidar.PointCount > 1000000 {
		quality += 0.2
	} else if lidar.PointCount > 100000 {
		quality += 0.1
	}
	
	// Accuracy
	if lidar.Accuracy < 1.0 { // Sub-mm accuracy
		quality += 0.2
	} else if lidar.Accuracy < 5.0 {
		quality += 0.1
	}
	
	// Feature detection
	if len(lidar.Features) > 5 {
		quality += 0.1
	}
	
	return math.Min(quality, 1.0)
}

func (e *ValidationEngine) assessPhotoQuality(photos []string) float64 {
	if len(photos) == 0 {
		return 0
	}
	
	quality := 0.5 // Base quality
	
	// Multiple angles
	if len(photos) >= 4 {
		quality += 0.3
	} else if len(photos) >= 2 {
		quality += 0.15
	}
	
	// Assume photos are high-res if URLs are provided
	// In production, would analyze actual image quality
	quality += 0.2
	
	return math.Min(quality, 1.0)
}

func (e *ValidationEngine) assessMeasurementQuality(measurements []Measurement) float64 {
	if len(measurements) == 0 {
		return 0
	}
	
	quality := 0.5 // Base quality
	
	// Number of measurements
	if len(measurements) >= 5 {
		quality += 0.2
	} else if len(measurements) >= 3 {
		quality += 0.1
	}
	
	// Tool quality
	hasLaser := false
	for _, m := range measurements {
		if m.Tool == "laser_distance" {
			hasLaser = true
			break
		}
	}
	if hasLaser {
		quality += 0.15
	}
	
	// Accuracy
	totalAccuracy := 0.0
	for _, m := range measurements {
		totalAccuracy += m.Accuracy
	}
	avgAccuracy := totalAccuracy / float64(len(measurements))
	
	if avgAccuracy < 2.0 {
		quality += 0.15
	} else if avgAccuracy < 5.0 {
		quality += 0.1
	}
	
	return math.Min(quality, 1.0)
}

func (e *ValidationEngine) assessFunctionalTestQuality(data map[string]interface{}) float64 {
	if data == nil || len(data) == 0 {
		return 0
	}
	
	quality := 0.6 // Base for functional test
	
	// Check for key test results
	if _, hasStatus := data["operational_status"]; hasStatus {
		quality += 0.1
	}
	if _, hasPerformance := data["performance_metrics"]; hasPerformance {
		quality += 0.1
	}
	if _, hasSafety := data["safety_checks"]; hasSafety {
		quality += 0.15
	}
	
	// More data points = higher quality
	if len(data) > 10 {
		quality += 0.15
	} else if len(data) > 5 {
		quality += 0.1
	}
	
	return math.Min(quality, 1.0)
}

func (e *ValidationEngine) getMethodQuality(method ValidationMethod) float64 {
	methodQualities := map[ValidationMethod]float64{
		MethodLiDARPro: 0.95,
		MethodARKit:    0.85,
		MethodDrone:    0.80,
		MethodRobot:    0.85,
		MethodMobile:   0.70,
		MethodManual:   0.60,
	}
	
	if quality, exists := methodQualities[method]; exists {
		return quality
	}
	return 0.5
}

func (e *ValidationEngine) getImportanceWeight(objectPath string) float64 {
	// Extract object type from path
	if weight, exists := e.importanceMap[extractObjectType(objectPath)]; exists {
		return weight
	}
	return 1.0
}

func (e *ValidationEngine) isCriticalSystem(path string) bool {
	critical := []string{
		"/electrical/main-panel",
		"/fire/",
		"/emergency/",
		"/hvac/chillers",
		"/security/access-control",
		"/elevator/",
	}
	
	for _, c := range critical {
		if contains(path, c) {
			return true
		}
	}
	return false
}

func (e *ValidationEngine) updateValidatorProfile(validatorID string, validation *Validation) {
	profile, exists := e.validators[validatorID]
	if !exists {
		profile = ValidatorProfile{
			UserID: validatorID,
		}
	}
	
	// Update counts
	profile.TotalValidations++
	
	// Update accuracy (simplified - in production would compare to consensus)
	if validation.Quality > 0.7 {
		profile.AccuracyScore = (profile.AccuracyScore*float64(profile.TotalValidations-1) + 1.0) / 
		                       float64(profile.TotalValidations)
	} else {
		profile.AccuracyScore = (profile.AccuracyScore*float64(profile.TotalValidations-1) + validation.Quality) / 
		                       float64(profile.TotalValidations)
	}
	
	// Update streak
	if profile.LastValidation.IsZero() || 
	   time.Since(profile.LastValidation).Hours() < 48 {
		profile.Streak++
	} else {
		profile.Streak = 1
	}
	
	profile.LastValidation = validation.Timestamp
	profile.TokensEarned += validation.TokensEarned
	
	// Update certifications based on experience
	if profile.TotalValidations > 100 && profile.AccuracyScore > 0.9 {
		profile.CertificationLevel = 5
		profile.TrustedValidator = true
	} else if profile.TotalValidations > 50 && profile.AccuracyScore > 0.85 {
		profile.CertificationLevel = 4
	} else if profile.TotalValidations > 25 && profile.AccuracyScore > 0.8 {
		profile.CertificationLevel = 3
	} else if profile.TotalValidations > 10 {
		profile.CertificationLevel = 2
	} else if profile.TotalValidations > 5 {
		profile.CertificationLevel = 1
	}
	
	e.validators[validatorID] = profile
}

func (e *ValidationEngine) updateConsensusData(confidence *ConfidenceScore, validation *Validation) {
	// Update consensus data with validated values
	// In production, would use voting/averaging across multiple validations
	if validation.Data != nil {
		for key, value := range validation.Data {
			confidence.ConsensusData[key] = value
		}
	}
}

func (e *ValidationEngine) generateImprovementTips(validation *Validation) []string {
	tips := []string{}
	
	if validation.Quality < 0.7 {
		switch validation.Type {
		case ValidationPhoto:
			if len(validation.PhotoURLs) < 3 {
				tips = append(tips, "Take photos from at least 3 different angles")
			}
			tips = append(tips, "Ensure good lighting and focus")
			
		case ValidationManualMeasure:
			if len(validation.Measurements) < 3 {
				tips = append(tips, "Take at least 3 measurements for accuracy")
			}
			tips = append(tips, "Use laser distance meter for better accuracy")
			
		case ValidationLiDAR:
			tips = append(tips, "Ensure complete coverage of the object")
			tips = append(tips, "Scan from multiple positions to reduce occlusion")
		}
		
		if validation.Notes == "" {
			tips = append(tips, "Add detailed notes about observations")
		}
	}
	
	return tips
}

// ValidationResult represents the result of a validation submission
type ValidationResult struct {
	ValidationID    string           `json:"validation_id"`
	Status          ValidationStatus `json:"status"`
	TokensEarned    float64          `json:"tokens_earned"`
	QualityScore    float64          `json:"quality_score"`
	NewConfidence   ConfidenceScore  `json:"new_confidence"`
	ImprovementTips []string         `json:"improvement_tips"`
}

// GetObjectConfidence returns confidence score for an object
func (e *ValidationEngine) GetObjectConfidence(objectID string) (ConfidenceScore, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	confidence, exists := e.confidence[objectID]
	return confidence, exists
}

// GetValidatorProfile returns a validator's profile
func (e *ValidationEngine) GetValidatorProfile(validatorID string) (ValidatorProfile, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	profile, exists := e.validators[validatorID]
	return profile, exists
}

// GetObjectValidations returns all validations for an object
func (e *ValidationEngine) GetObjectValidations(objectID string) []Validation {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	return e.validations[objectID]
}

// Default configuration functions

func defaultValidationRates() map[ValidationType]float64 {
	return map[ValidationType]float64{
		ValidationPhoto:          10.0,  // 10 BILT base
		ValidationLiDAR:          50.0,  // 50 BILT base
		ValidationManualMeasure:  5.0,   // 5 BILT base
		ValidationVisualInspect:  3.0,   // 3 BILT base
		ValidationFunctionalTest: 25.0,  // 25 BILT base
		ValidationThermographic:  30.0,  // 30 BILT base
		ValidationAcoustic:       20.0,  // 20 BILT base
		ValidationVibration:      20.0,  // 20 BILT base
	}
}

func defaultImportanceWeights() map[string]float64 {
	return map[string]float64{
		"electrical_panel":    2.0,  // Critical infrastructure
		"main_breaker":        2.0,
		"fire_alarm":          2.5,  // Safety critical
		"emergency_exit":      2.5,
		"sprinkler":           2.0,
		"hvac_chiller":        1.8,  // Major equipment
		"hvac_boiler":         1.8,
		"elevator":            2.0,
		"transformer":         1.8,
		"outlet":              1.0,  // Standard equipment
		"thermostat":          1.0,
		"light_fixture":       0.8,
		"duct":                0.9,
		"pipe":                0.9,
		"door":                0.7,
		"window":              0.6,
	}
}

// Helper functions

func generateValidationID() string {
	return fmt.Sprintf("val_%d", time.Now().UnixNano())
}

func extractObjectType(path string) string {
	// Extract object type from path
	parts := strings.Split(path, "/")
	if len(parts) > 0 {
		return parts[len(parts)-1]
	}
	return "unknown"
}

func contains(str, substr string) bool {
	return strings.Contains(strings.ToLower(str), strings.ToLower(substr))
}