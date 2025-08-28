package validation

import (
	"fmt"
	"testing"
	"time"

	"github.com/arxos/arxos/core/internal/services/bilt"
)

// TestValidationEngineCreation tests creating a validation engine
func TestValidationEngineCreation(t *testing.T) {
	biltEngine := bilt.NewBILTEngine()
	engine := NewValidationEngine(biltEngine)
	
	if engine == nil {
		t.Fatal("Failed to create validation engine")
	}
	
	// Check default rates
	if engine.rewardRates[ValidationPhoto] != 10.0 {
		t.Errorf("Expected photo rate 10.0, got %f", engine.rewardRates[ValidationPhoto])
	}
	
	if engine.rewardRates[ValidationLiDAR] != 50.0 {
		t.Errorf("Expected LiDAR rate 50.0, got %f", engine.rewardRates[ValidationLiDAR])
	}
	
	if engine.rewardRates[ValidationManualMeasure] != 5.0 {
		t.Errorf("Expected manual measure rate 5.0, got %f", engine.rewardRates[ValidationManualMeasure])
	}
}

// TestPhotoValidation tests photo validation submission
func TestPhotoValidation(t *testing.T) {
	biltEngine := bilt.NewBILTEngine()
	engine := NewValidationEngine(biltEngine)
	
	validation := &Validation{
		ObjectID:    "test-object-1",
		ObjectPath:  "/electrical/panel/main",
		ValidatorID: "user1",
		Type:        ValidationPhoto,
		Method:      MethodMobile,
		PhotoURLs:   []string{"photo1.jpg", "photo2.jpg", "photo3.jpg"},
		Confidence:  0.85,
		Notes:       "Panel in good condition, all breakers labeled",
		Data: map[string]interface{}{
			"condition": "good",
			"labels":    "present",
		},
	}
	
	result, err := engine.SubmitValidation(validation)
	if err != nil {
		t.Fatalf("Failed to submit validation: %v", err)
	}
	
	// Check result
	if result.Status != StatusAccepted {
		t.Errorf("Expected validation to be accepted, got %s", result.Status)
	}
	
	// Check tokens earned (should be around 10 BILT base * multipliers)
	if result.TokensEarned < 5.0 || result.TokensEarned > 30.0 {
		t.Errorf("Unexpected tokens earned: %f", result.TokensEarned)
	}
	
	// Check confidence update
	if result.NewConfidence.ValidationCount != 1 {
		t.Errorf("Expected 1 validation, got %d", result.NewConfidence.ValidationCount)
	}
}

// TestLiDARValidation tests LiDAR validation with high reward
func TestLiDARValidation(t *testing.T) {
	biltEngine := bilt.NewBILTEngine()
	engine := NewValidationEngine(biltEngine)
	
	validation := &Validation{
		ObjectID:    "test-object-2",
		ObjectPath:  "/hvac/chiller/ch-1", // Critical system
		ValidatorID: "user2",
		Type:        ValidationLiDAR,
		Method:      MethodLiDARPro,
		Confidence:  0.95,
		LiDARData: &LiDARScan{
			PointCount:   1500000,
			Accuracy:     0.5, // Sub-mm accuracy
			DeviceModel:  "iPhone 15 Pro",
			ScanDuration: 45 * time.Second,
			Features: []DetectedFeature{
				{Type: "pipe", Confidence: 0.9},
				{Type: "valve", Confidence: 0.85},
			},
		},
		Data: map[string]interface{}{
			"scan_complete": true,
			"coverage":      "full",
		},
	}
	
	result, err := engine.SubmitValidation(validation)
	if err != nil {
		t.Fatalf("Failed to submit LiDAR validation: %v", err)
	}
	
	// Check higher reward for LiDAR (base 50 BILT)
	if result.TokensEarned < 40.0 || result.TokensEarned > 150.0 {
		t.Errorf("Unexpected LiDAR tokens earned: %f", result.TokensEarned)
	}
	
	// Should earn more than photo validation
	if result.TokensEarned < 30.0 {
		t.Errorf("LiDAR should earn more than photo validation: %f", result.TokensEarned)
	}
}

// TestProgressiveValidation tests progressive confidence building
func TestProgressiveValidation(t *testing.T) {
	biltEngine := bilt.NewBILTEngine()
	engine := NewValidationEngine(biltEngine)
	
	objectID := "test-object-3"
	objectPath := "/electrical/outlet-3"
	
	// First validation - should get bonus
	val1 := &Validation{
		ObjectID:    objectID,
		ObjectPath:  objectPath,
		ValidatorID: "user1",
		Type:        ValidationPhoto,
		Method:      MethodMobile,
		PhotoURLs:   []string{"photo1.jpg"},
		Confidence:  0.8,
	}
	
	result1, _ := engine.SubmitValidation(val1)
	firstReward := result1.TokensEarned
	
	// Second validation - different validator
	val2 := &Validation{
		ObjectID:    objectID,
		ObjectPath:  objectPath,
		ValidatorID: "user2", // Different validator
		Type:        ValidationManualMeasure,
		Method:      MethodManual,
		Measurements: []Measurement{
			{Type: "length", Value: 100, Accuracy: 2.0},
		},
		Confidence: 0.75,
	}
	
	result2, _ := engine.SubmitValidation(val2)
	
	// Check confidence increases
	if result2.NewConfidence.Overall <= result1.NewConfidence.Overall {
		t.Error("Confidence should increase with more validations")
	}
	
	// Check validator diversity
	if result2.NewConfidence.ValidatorCount != 2 {
		t.Errorf("Expected 2 validators, got %d", result2.NewConfidence.ValidatorCount)
	}
	
	// Third validation - same validator, should get less reward
	val3 := &Validation{
		ObjectID:    objectID,
		ObjectPath:  objectPath,
		ValidatorID: "user1", // Same as first
		Type:        ValidationPhoto,
		Method:      MethodMobile,
		PhotoURLs:   []string{"photo2.jpg"},
		Confidence:  0.8,
	}
	
	result3, _ := engine.SubmitValidation(val3)
	
	// Progressive bonus should decrease as confidence increases
	if result3.TokensEarned >= firstReward {
		t.Error("Progressive bonus should decrease as confidence increases")
	}
}

// TestValidatorProfile tests validator profile tracking
func TestValidatorProfile(t *testing.T) {
	biltEngine := bilt.NewBILTEngine()
	engine := NewValidationEngine(biltEngine)
	
	validatorID := "expert-validator"
	
	// Submit multiple validations to build profile
	for i := 0; i < 10; i++ {
		validation := &Validation{
			ObjectID:    fmt.Sprintf("object-%d", i),
			ObjectPath:  fmt.Sprintf("/test/object-%d", i),
			ValidatorID: validatorID,
			Type:        ValidationPhoto,
			Method:      MethodMobile,
			PhotoURLs:   []string{"photo.jpg"},
			Confidence:  0.85,
			Data:        map[string]interface{}{"test": true},
		}
		
		engine.SubmitValidation(validation)
	}
	
	// Check profile
	profile, exists := engine.GetValidatorProfile(validatorID)
	if !exists {
		t.Fatal("Validator profile not found")
	}
	
	if profile.TotalValidations != 10 {
		t.Errorf("Expected 10 validations, got %d", profile.TotalValidations)
	}
	
	// Should have certification level
	if profile.CertificationLevel < 1 {
		t.Error("Should have certification level after 10 validations")
	}
	
	// Should have accuracy score
	if profile.AccuracyScore == 0 {
		t.Error("Should have accuracy score")
	}
}

// TestCriticalSystemBonus tests bonus for critical systems
func TestCriticalSystemBonus(t *testing.T) {
	biltEngine := bilt.NewBILTEngine()
	engine := NewValidationEngine(biltEngine)
	
	// Normal system validation
	normalVal := &Validation{
		ObjectID:    "normal-1",
		ObjectPath:  "/lighting/fixture-1",
		ValidatorID: "user1",
		Type:        ValidationPhoto,
		Method:      MethodMobile,
		PhotoURLs:   []string{"photo.jpg"},
		Confidence:  0.8,
	}
	
	normalResult, _ := engine.SubmitValidation(normalVal)
	
	// Critical system validation (same type, different path)
	criticalVal := &Validation{
		ObjectID:    "critical-1",
		ObjectPath:  "/fire/alarm/fa-1", // Fire alarm is critical
		ValidatorID: "user1",
		Type:        ValidationPhoto,
		Method:      MethodMobile,
		PhotoURLs:   []string{"photo.jpg"},
		Confidence:  0.8,
	}
	
	criticalResult, _ := engine.SubmitValidation(criticalVal)
	
	// Critical system should earn more
	if criticalResult.TokensEarned <= normalResult.TokensEarned {
		t.Errorf("Critical system should earn more: normal=%f, critical=%f",
			normalResult.TokensEarned, criticalResult.TokensEarned)
	}
}

// TestLowQualityRejection tests that low quality validations are rejected
func TestLowQualityRejection(t *testing.T) {
	biltEngine := bilt.NewBILTEngine()
	engine := NewValidationEngine(biltEngine)
	
	// Very low quality validation
	validation := &Validation{
		ObjectID:    "low-quality-1",
		ObjectPath:  "/test/object",
		ValidatorID: "user1",
		Type:        ValidationPhoto,
		Method:      MethodMobile,
		PhotoURLs:   []string{}, // No photos!
		Confidence:  0.2,        // Very low confidence
		Data:        nil,         // No data
		Notes:       "",          // No notes
	}
	
	result, _ := engine.SubmitValidation(validation)
	
	// Should be rejected
	if result.Status != StatusRejected {
		t.Errorf("Low quality validation should be rejected, got %s", result.Status)
	}
	
	// Should not earn tokens
	if result.TokensEarned > 0 {
		t.Errorf("Rejected validation should not earn tokens, got %f", result.TokensEarned)
	}
	
	// Should get improvement tips
	if len(result.ImprovementTips) == 0 {
		t.Error("Should provide improvement tips for rejected validation")
	}
}

// TestMultiMethodBonus tests bonus for using multiple validation methods
func TestMultiMethodBonus(t *testing.T) {
	biltEngine := bilt.NewBILTEngine()
	engine := NewValidationEngine(biltEngine)
	
	// Single method validation
	singleMethod := &Validation{
		ObjectID:    "single-method",
		ObjectPath:  "/test/object",
		ValidatorID: "user1",
		Type:        ValidationPhoto,
		Method:      MethodMobile,
		PhotoURLs:   []string{"photo1.jpg", "photo2.jpg"},
		Confidence:  0.8,
	}
	
	singleResult, _ := engine.SubmitValidation(singleMethod)
	
	// Multi-method validation (photos + measurements)
	multiMethod := &Validation{
		ObjectID:    "multi-method",
		ObjectPath:  "/test/object2",
		ValidatorID: "user1",
		Type:        ValidationManualMeasure,
		Method:      MethodMobile,
		PhotoURLs:   []string{"photo1.jpg", "photo2.jpg"}, // Has photos
		Measurements: []Measurement{ // AND measurements
			{Type: "length", Value: 100, Accuracy: 2.0},
			{Type: "width", Value: 50, Accuracy: 2.0},
		},
		Confidence: 0.8,
	}
	
	multiResult, _ := engine.SubmitValidation(multiMethod)
	
	// Multi-method should earn more
	if multiResult.TokensEarned <= singleResult.TokensEarned {
		t.Errorf("Multi-method should earn more: single=%f, multi=%f",
			singleResult.TokensEarned, multiResult.TokensEarned)
	}
}

// BenchmarkValidationSubmission benchmarks validation processing
func BenchmarkValidationSubmission(b *testing.B) {
	biltEngine := bilt.NewBILTEngine()
	engine := NewValidationEngine(biltEngine)
	
	validation := &Validation{
		ObjectID:    "bench-object",
		ObjectPath:  "/test/benchmark",
		ValidatorID: "bench-user",
		Type:        ValidationPhoto,
		Method:      MethodMobile,
		PhotoURLs:   []string{"photo1.jpg", "photo2.jpg", "photo3.jpg"},
		Confidence:  0.85,
		Data: map[string]interface{}{
			"test": true,
			"benchmark": true,
		},
	}
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		validation.ObjectID = fmt.Sprintf("bench-%d", i)
		engine.SubmitValidation(validation)
	}
}