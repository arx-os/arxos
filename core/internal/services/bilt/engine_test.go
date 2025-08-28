package bilt

import (
	"testing"
	"time"
)

// TestBILTEngineCreation tests creating a new BILT engine
func TestBILTEngineCreation(t *testing.T) {
	engine := NewBILTEngine()
	
	if engine == nil {
		t.Fatal("Failed to create BILT engine")
	}
	
	// Check default rates are loaded
	rate := engine.GetEarningRate("scan")
	if rate != 10.0 {
		t.Errorf("Expected scan rate 10.0, got %f", rate)
	}
	
	// Check default rate for unknown type
	rate = engine.GetEarningRate("unknown_type")
	if rate != 1.0 {
		t.Errorf("Expected default rate 1.0, got %f", rate)
	}
}

// TestCalculateReward tests reward calculation for various contributions
func TestCalculateReward(t *testing.T) {
	engine := NewBILTEngine()
	
	testCases := []struct {
		name           string
		contribution   DataContribution
		expectedMin    float64
		expectedMax    float64
	}{
		{
			name: "High quality outlet scan",
			contribution: DataContribution{
				UserID:     "user1",
				Timestamp:  time.Now(),
				ObjectPath: "/electrical/main-panel/circuit-7/outlet-3",
				DataType:   "scan",
				Data: map[string]interface{}{
					"voltage":    120.0,
					"load":       12.5,
					"type":       "NEMA 5-15R",
					"location":   "North wall",
					"confidence": 0.95,
				},
				Confidence: 0.95,
				Duration:   2 * time.Minute,
				Location:   Location{Accuracy: 2.0},
			},
			expectedMin: 8.0,  // Base rate 10 * quality
			expectedMax: 15.0, // With bonuses
		},
		{
			name: "Basic validation",
			contribution: DataContribution{
				UserID:     "user2",
				Timestamp:  time.Now(),
				ObjectPath: "/hvac/thermostats/t-101",
				DataType:   "validation",
				Data: map[string]interface{}{
					"setpoint":     72.0,
					"current_temp": 71.0,
					"status":       "active",
				},
				Confidence: 0.8,
				Duration:   1 * time.Minute,
			},
			expectedMin: 1.5, // Base rate 3 * quality
			expectedMax: 4.0,
		},
		{
			name: "Low quality contribution",
			contribution: DataContribution{
				UserID:     "user3",
				Timestamp:  time.Now(),
				ObjectPath: "/floors/1/room-101",
				DataType:   "annotation",
				Data: map[string]interface{}{
					"note": "Room needs cleaning",
				},
				Confidence: 0.3, // Low confidence
				Duration:   30 * time.Second,
			},
			expectedMin: 0.0, // Below quality threshold
			expectedMax: 0.0,
		},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			reward := engine.CalculateReward(tc.contribution)
			
			if reward < tc.expectedMin || reward > tc.expectedMax {
				t.Errorf("Expected reward between %.2f and %.2f, got %.2f",
					tc.expectedMin, tc.expectedMax, reward)
			}
		})
	}
}

// TestAssessQuality tests quality assessment of data
func TestAssessQuality(t *testing.T) {
	engine := NewBILTEngine()
	
	testCases := []struct {
		name            string
		data            ArxObject
		expectedQuality float64
		tolerance       float64
	}{
		{
			name: "Complete outlet data",
			data: ArxObject{
				Path: "/electrical/main-panel/circuit-7/outlet-3",
				Type: "outlet",
				Properties: map[string]interface{}{
					"voltage":  120.0,
					"load":     12.5,
					"type":     "NEMA 5-15R",
					"location": "North wall",
				},
				Confidence:  0.95,
				LastUpdated: time.Now(),
			},
			expectedQuality: 0.85,
			tolerance:       0.15,
		},
		{
			name: "Incomplete data",
			data: ArxObject{
				Path: "/electrical/main-panel/circuit-7/outlet-4",
				Type: "outlet",
				Properties: map[string]interface{}{
					"voltage": 120.0,
					// Missing required fields
				},
				Confidence:  0.6,
				LastUpdated: time.Now().Add(-48 * time.Hour),
			},
			expectedQuality: 0.4,
			tolerance:       0.1,
		},
		{
			name: "Old but validated data",
			data: ArxObject{
				Path: "/hvac/thermostats/t-101",
				Type: "thermostat",
				Properties: map[string]interface{}{
					"model":        "Nest T3",
					"setpoint":     72.0,
					"current_temp": 71.0,
					"zone":         "Zone 1",
				},
				Confidence:  0.9,
				LastUpdated: time.Now().Add(-60 * 24 * time.Hour), // 60 days old
				Validators:  []string{"user1", "user2"},           // Validated by 2 users
			},
			expectedQuality: 0.7,
			tolerance:       0.15,
		},
	}
	
	for _, tc := range testCases {
		t.Run(tc.name, func(t *testing.T) {
			score := engine.AssessQuality(tc.data)
			
			diff := score.Overall - tc.expectedQuality
			if diff < -tc.tolerance || diff > tc.tolerance {
				t.Errorf("Expected quality %.2f±%.2f, got %.2f\nDetails: %s",
					tc.expectedQuality, tc.tolerance, score.Overall, score.Details)
			}
			
			// Verify all quality dimensions are calculated
			if score.Accuracy == 0 && score.Completeness == 0 {
				t.Error("Quality dimensions not calculated")
			}
		})
	}
}

// TestRecordEarning tests recording earnings to the ledger
func TestRecordEarning(t *testing.T) {
	engine := NewBILTEngine()
	
	// Record earning
	err := engine.RecordEarning("user1", 10.5, "Scanned outlet")
	if err != nil {
		t.Fatalf("Failed to record earning: %v", err)
	}
	
	// Check balance
	balance, err := engine.GetUserBalance("user1")
	if err != nil {
		t.Fatalf("Failed to get balance: %v", err)
	}
	
	if balance != 10.5 {
		t.Errorf("Expected balance 10.5, got %f", balance)
	}
	
	// Record another earning
	err = engine.RecordEarning("user1", 5.25, "Validated circuit")
	if err != nil {
		t.Fatalf("Failed to record second earning: %v", err)
	}
	
	// Check updated balance
	balance, err = engine.GetUserBalance("user1")
	if err != nil {
		t.Fatalf("Failed to get updated balance: %v", err)
	}
	
	if balance != 15.75 {
		t.Errorf("Expected balance 15.75, got %f", balance)
	}
	
	// Test invalid earning
	err = engine.RecordEarning("user1", -5.0, "Invalid amount")
	if err == nil {
		t.Error("Should reject negative earning amount")
	}
}

// TestGetUserHistory tests retrieving user earning history
func TestGetUserHistory(t *testing.T) {
	engine := NewBILTEngine()
	
	// Record multiple earnings
	engine.RecordEarning("user1", 10.0, "Scan 1")
	engine.RecordEarning("user1", 5.0, "Scan 2")
	engine.RecordEarning("user1", 3.0, "Validation")
	
	// Get history
	history, err := engine.GetUserHistory("user1", 10)
	if err != nil {
		t.Fatalf("Failed to get history: %v", err)
	}
	
	if len(history) != 3 {
		t.Errorf("Expected 3 transactions, got %d", len(history))
	}
	
	// Verify most recent first
	if history[0].Amount != 3.0 {
		t.Error("History should return most recent transaction first")
	}
}

// TestProcessContribution tests the complete contribution workflow
func TestProcessContribution(t *testing.T) {
	engine := NewBILTEngine()
	
	contribution := DataContribution{
		UserID:     "fieldworker1",
		Timestamp:  time.Now(),
		ObjectPath: "/electrical/main-panel/circuit-7/outlet-3",
		DataType:   "measurement",
		Data: map[string]interface{}{
			"voltage":    119.5,
			"load":       14.2,
			"type":       "NEMA 5-15R",
			"location":   "Room 201, North Wall",
			"height":     "18 inches",
			"confidence": 0.92,
		},
		Confidence: 0.92,
		Duration:   3 * time.Minute,
		DeviceType: "tablet",
		Location: Location{
			Latitude:  37.7749,
			Longitude: -122.4194,
			Altitude:  50.0,
			Accuracy:  3.5,
		},
	}
	
	result, err := engine.ProcessContribution(contribution)
	if err != nil {
		t.Fatalf("Failed to process contribution: %v", err)
	}
	
	// Verify result
	if result.Status != "accepted" {
		t.Errorf("Expected contribution to be accepted, got %s", result.Status)
	}
	
	if result.TokensEarned <= 0 {
		t.Error("Should earn tokens for quality contribution")
	}
	
	// Verify tokens were credited
	balance, _ := engine.GetUserBalance("fieldworker1")
	if balance != result.TokensEarned {
		t.Errorf("Balance mismatch: expected %f, got %f", result.TokensEarned, balance)
	}
}

// TestEarningRates tests getting and setting earning rates
func TestEarningRates(t *testing.T) {
	engine := NewBILTEngine()
	
	// Test default rates
	rates := map[string]float64{
		"scan":             10.0,
		"measurement":      5.0,
		"validation":       3.0,
		"electrical_trace": 15.0,
	}
	
	for processType, expectedRate := range rates {
		rate := engine.GetEarningRate(processType)
		if rate != expectedRate {
			t.Errorf("Expected %s rate %.1f, got %.1f", processType, expectedRate, rate)
		}
	}
	
	// Test setting custom rate
	engine.SetEarningRate("custom_process", 25.0)
	rate := engine.GetEarningRate("custom_process")
	if rate != 25.0 {
		t.Errorf("Expected custom rate 25.0, got %.1f", rate)
	}
}

// TestQualityThreshold tests minimum quality threshold
func TestQualityThreshold(t *testing.T) {
	engine := NewBILTEngine()
	
	// Low quality contribution
	contribution := DataContribution{
		UserID:     "user1",
		Timestamp:  time.Now(),
		ObjectPath: "/test/object",
		DataType:   "scan",
		Data:       map[string]interface{}{"incomplete": "data"},
		Confidence: 0.2, // Very low confidence
		Duration:   1 * time.Second,
	}
	
	reward := engine.CalculateReward(contribution)
	
	if reward > 0 {
		t.Error("Should not reward contribution below quality threshold")
	}
}

// BenchmarkCalculateReward benchmarks reward calculation performance
func BenchmarkCalculateReward(b *testing.B) {
	engine := NewBILTEngine()
	
	contribution := DataContribution{
		UserID:     "bench_user",
		Timestamp:  time.Now(),
		ObjectPath: "/electrical/main-panel/circuit-7/outlet-3",
		DataType:   "scan",
		Data: map[string]interface{}{
			"voltage": 120.0,
			"load":    12.5,
			"type":    "NEMA 5-15R",
		},
		Confidence: 0.85,
		Duration:   2 * time.Minute,
	}
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		_ = engine.CalculateReward(contribution)
	}
}

// BenchmarkAssessQuality benchmarks quality assessment performance
func BenchmarkAssessQuality(b *testing.B) {
	engine := NewBILTEngine()
	
	data := ArxObject{
		Path: "/test/object",
		Type: "outlet",
		Properties: map[string]interface{}{
			"voltage":  120.0,
			"load":     12.5,
			"type":     "NEMA 5-15R",
			"location": "Test location",
		},
		Confidence:  0.9,
		LastUpdated: time.Now(),
	}
	
	b.ResetTimer()
	
	for i := 0; i < b.N; i++ {
		_ = engine.AssessQuality(data)
	}
}