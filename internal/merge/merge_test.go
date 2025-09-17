package merge

import (
	"testing"
	"time"

	"github.com/arx-os/arxos/internal/spatial"
)

func TestSmartMerger_MergeEquipmentData(t *testing.T) {
	confidenceManager := spatial.NewConfidenceManager()
	coverageTracker := spatial.NewCoverageTracker("test-building")
	merger := NewSmartMerger(confidenceManager, coverageTracker)

	tests := []struct {
		name      string
		strategy  MergeStrategy
		sources   []DataSource
		wantError bool
		validate  func(*testing.T, *MergedEquipment)
	}{
		{
			name:     "Merge with highest confidence strategy",
			strategy: StrategyHighestConfidence,
			sources: []DataSource{
				{
					ID:         "source1",
					Type:       "lidar",
					Confidence: spatial.ConfidenceHigh,
					Timestamp:  time.Now().Add(-time.Hour),
					Data: map[string]interface{}{
						"position": spatial.Point3D{X: 10, Y: 20, Z: 3},
						"type":     "HVAC",
					},
				},
				{
					ID:         "source2",
					Type:       "manual",
					Confidence: spatial.ConfidenceLow,
					Timestamp:  time.Now(),
					Data: map[string]interface{}{
						"position": spatial.Point3D{X: 11, Y: 21, Z: 3},
						"type":     "HVAC",
					},
				},
			},
			wantError: false,
			validate: func(t *testing.T, result *MergedEquipment) {
				if result.Position.X != 10 {
					t.Errorf("Expected X=10 from highest confidence source, got %f", result.Position.X)
				}
				if result.Confidence != spatial.ConfidenceHigh {
					t.Errorf("Expected HIGH confidence, got %v", result.Confidence)
				}
			},
		},
		{
			name:     "Merge with most recent strategy",
			strategy: StrategyMostRecent,
			sources: []DataSource{
				{
					ID:         "source1",
					Type:       "lidar",
					Confidence: spatial.ConfidenceHigh,
					Timestamp:  time.Now().Add(-time.Hour),
					Data: map[string]interface{}{
						"position": spatial.Point3D{X: 10, Y: 20, Z: 3},
						"type":     "HVAC",
					},
				},
				{
					ID:         "source2",
					Type:       "manual",
					Confidence: spatial.ConfidenceLow,
					Timestamp:  time.Now(),
					Data: map[string]interface{}{
						"position": spatial.Point3D{X: 11, Y: 21, Z: 3},
						"type":     "HVAC",
					},
				},
			},
			wantError: false,
			validate: func(t *testing.T, result *MergedEquipment) {
				if result.Position.X != 11 {
					t.Errorf("Expected X=11 from most recent source, got %f", result.Position.X)
				}
			},
		},
		{
			name:     "Merge with weighted average",
			strategy: StrategyWeightedAverage,
			sources: []DataSource{
				{
					ID:         "source1",
					Type:       "lidar",
					Confidence: spatial.ConfidenceHigh,
					Timestamp:  time.Now(),
					Data: map[string]interface{}{
						"position": spatial.Point3D{X: 10, Y: 20, Z: 3},
						"dimensions": Dimensions{Length: 2, Width: 1, Height: 0.5},
						"type":     "HVAC",
					},
				},
				{
					ID:         "source2",
					Type:       "manual",
					Confidence: spatial.ConfidenceHigh,
					Timestamp:  time.Now(),
					Data: map[string]interface{}{
						"position": spatial.Point3D{X: 12, Y: 22, Z: 3},
						"dimensions": Dimensions{Length: 2.2, Width: 1.1, Height: 0.6},
						"type":     "HVAC",
					},
				},
			},
			wantError: false,
			validate: func(t *testing.T, result *MergedEquipment) {
				// Should average positions
				expectedX := 11.0
				if result.Position.X != expectedX {
					t.Errorf("Expected averaged X=%f, got %f", expectedX, result.Position.X)
				}
				// Should average dimensions
				expectedLength := 2.1
				if result.Dimensions.Length != expectedLength {
					t.Errorf("Expected averaged Length=%f, got %f", expectedLength, result.Dimensions.Length)
				}
			},
		},
		{
			name:     "Detect position conflict",
			strategy: StrategyHighestConfidence,
			sources: []DataSource{
				{
					ID:         "source1",
					Type:       "lidar",
					Confidence: spatial.ConfidenceHigh,
					Timestamp:  time.Now(),
					Data: map[string]interface{}{
						"position": spatial.Point3D{X: 10, Y: 20, Z: 3},
						"type":     "HVAC",
					},
				},
				{
					ID:         "source2",
					Type:       "manual",
					Confidence: spatial.ConfidenceHigh,
					Timestamp:  time.Now(),
					Data: map[string]interface{}{
						"position": spatial.Point3D{X: 15, Y: 25, Z: 3},
						"type":     "HVAC",
					},
				},
			},
			wantError: false,
			validate: func(t *testing.T, result *MergedEquipment) {
				if len(result.Conflicts) == 0 {
					t.Error("Expected position conflict to be detected")
				}
				found := false
				for _, c := range result.Conflicts {
					if c.Type == "position" {
						found = true
						break
					}
				}
				if !found {
					t.Error("Expected position conflict type")
				}
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			merger.SetStrategy(tt.strategy)
			result, err := merger.MergeEquipmentData("test-equipment", tt.sources)

			if (err != nil) != tt.wantError {
				t.Errorf("MergeEquipmentData() error = %v, wantError %v", err, tt.wantError)
				return
			}

			if !tt.wantError && tt.validate != nil {
				tt.validate(t, result)
			}
		})
	}
}

func TestConflictResolver_ResolveConflict(t *testing.T) {
	confidenceManager := spatial.NewConfidenceManager()
	resolver := NewConflictResolver(confidenceManager)

	tests := []struct {
		name     string
		conflict Conflict
		validate func(*testing.T, *ResolutionResult)
	}{
		{
			name: "Resolve small position difference automatically",
			conflict: Conflict{
				ID:          "conflict1",
				EquipmentID: "equip1",
				Type:        "position",
				Source1: DataSource{
					Type:       "lidar",
					Confidence: spatial.ConfidenceHigh,
					Timestamp:  time.Now(),
				},
				Source2: DataSource{
					Type:       "manual",
					Confidence: spatial.ConfidenceMedium,
					Timestamp:  time.Now(),
				},
				Value1:     spatial.Point3D{X: 10, Y: 20, Z: 3},
				Value2:     spatial.Point3D{X: 10.2, Y: 20.1, Z: 3},
				Difference: 0.2236, // ~22cm
			},
			validate: func(t *testing.T, result *ResolutionResult) {
				if result.Method != MethodAutomatic {
					t.Errorf("Expected automatic resolution, got %v", result.Method)
				}
				if result.RuleApplied == nil {
					t.Error("Expected rule to be applied")
				} else if result.RuleApplied.ID != "pos_small_diff_high_conf" {
					t.Errorf("Expected pos_small_diff_high_conf rule, got %s", result.RuleApplied.ID)
				}
			},
		},
		{
			name: "Require verification for large position difference",
			conflict: Conflict{
				ID:          "conflict2",
				EquipmentID: "equip2",
				Type:        "position",
				Source1: DataSource{
					Type:       "lidar",
					Confidence: spatial.ConfidenceHigh,
					Timestamp:  time.Now(),
				},
				Source2: DataSource{
					Type:       "manual",
					Confidence: spatial.ConfidenceHigh,
					Timestamp:  time.Now(),
				},
				Value1:     spatial.Point3D{X: 10, Y: 20, Z: 3},
				Value2:     spatial.Point3D{X: 15, Y: 25, Z: 3},
				Difference: 7.07, // ~7 meters
			},
			validate: func(t *testing.T, result *ResolutionResult) {
				if result.Method != MethodFieldVerify {
					t.Errorf("Expected field verification requirement, got %v", result.Method)
				}
				if !result.RequiresAction {
					t.Error("Expected action to be required")
				}
			},
		},
		{
			name: "Prefer LiDAR for dimension conflicts",
			conflict: Conflict{
				ID:          "conflict3",
				EquipmentID: "equip3",
				Type:        "dimension",
				Source1: DataSource{
					Type:       "lidar",
					Confidence: spatial.ConfidenceHigh,
					Timestamp:  time.Now(),
				},
				Source2: DataSource{
					Type:       "manual",
					Confidence: spatial.ConfidenceHigh,
					Timestamp:  time.Now(),
				},
				Value1:     Dimensions{Length: 2.0, Width: 1.0, Height: 0.5},
				Value2:     Dimensions{Length: 2.2, Width: 1.1, Height: 0.6},
				Difference: 0.1,
			},
			validate: func(t *testing.T, result *ResolutionResult) {
				if result.Method != MethodAutomatic {
					t.Errorf("Expected automatic resolution, got %v", result.Method)
				}
				if result.RuleApplied == nil || result.RuleApplied.ID != "dim_prefer_lidar" {
					t.Error("Expected dim_prefer_lidar rule to be applied")
				}
				// Should prefer LiDAR dimensions
				dims, ok := result.ResolvedValue.(Dimensions)
				if !ok {
					t.Fatal("Expected Dimensions type in resolved value")
				}
				if dims.Length != 2.0 {
					t.Errorf("Expected LiDAR length 2.0, got %f", dims.Length)
				}
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result, err := resolver.ResolveConflict(tt.conflict)
			if err != nil {
				t.Fatalf("ResolveConflict() error = %v", err)
			}

			if tt.validate != nil {
				tt.validate(t, result)
			}
		})
	}
}

func TestChangeDetector_DetectChanges(t *testing.T) {
	detector := NewChangeDetector()

	oldEquipment := &MergedEquipment{
		EquipmentID: "equip1",
		Type:        "HVAC",
		Position:    spatial.Point3D{X: 10, Y: 20, Z: 3},
		Dimensions:  Dimensions{Length: 2, Width: 1, Height: 0.5},
		Attributes: map[string]interface{}{
			"model":  "ABC123",
			"status": "active",
		},
		Confidence: spatial.ConfidenceHigh,
	}

	tests := []struct {
		name         string
		newEquipment *MergedEquipment
		wantChanges  []ChangeType
	}{
		{
			name: "Detect position change",
			newEquipment: &MergedEquipment{
				EquipmentID: "equip1",
				Type:        "HVAC",
				Position:    spatial.Point3D{X: 11, Y: 21, Z: 3},
				Dimensions:  Dimensions{Length: 2, Width: 1, Height: 0.5},
				Attributes:  oldEquipment.Attributes,
				Confidence:  spatial.ConfidenceHigh,
			},
			wantChanges: []ChangeType{ChangeTypePosition},
		},
		{
			name: "Detect dimension change",
			newEquipment: &MergedEquipment{
				EquipmentID: "equip1",
				Type:        "HVAC",
				Position:    spatial.Point3D{X: 10, Y: 20, Z: 3},
				Dimensions:  Dimensions{Length: 2.5, Width: 1.2, Height: 0.6},
				Attributes:  oldEquipment.Attributes,
				Confidence:  spatial.ConfidenceHigh,
			},
			wantChanges: []ChangeType{ChangeTypeDimension},
		},
		{
			name: "Detect type change",
			newEquipment: &MergedEquipment{
				EquipmentID: "equip1",
				Type:        "Electrical",
				Position:    spatial.Point3D{X: 10, Y: 20, Z: 3},
				Dimensions:  Dimensions{Length: 2, Width: 1, Height: 0.5},
				Attributes:  oldEquipment.Attributes,
				Confidence:  spatial.ConfidenceHigh,
			},
			wantChanges: []ChangeType{ChangeTypeType},
		},
		{
			name: "Detect attribute change",
			newEquipment: &MergedEquipment{
				EquipmentID: "equip1",
				Type:        "HVAC",
				Position:    spatial.Point3D{X: 10, Y: 20, Z: 3},
				Dimensions:  Dimensions{Length: 2, Width: 1, Height: 0.5},
				Attributes: map[string]interface{}{
					"model":  "XYZ789",  // Changed
					"status": "inactive", // Changed
					"new_field": "value", // Added
				},
				Confidence: spatial.ConfidenceHigh,
			},
			wantChanges: []ChangeType{ChangeTypeAttribute},
		},
		{
			name: "No significant changes",
			newEquipment: &MergedEquipment{
				EquipmentID: "equip1",
				Type:        "HVAC",
				Position:    spatial.Point3D{X: 10.05, Y: 20.05, Z: 3}, // Small change below threshold
				Dimensions:  Dimensions{Length: 2.01, Width: 1.005, Height: 0.502}, // Small changes
				Attributes:  oldEquipment.Attributes,
				Confidence:  spatial.ConfidenceHigh,
			},
			wantChanges: []ChangeType{},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			changes := detector.DetectChanges(oldEquipment, tt.newEquipment)

			// Check if expected change types are detected
			changeTypes := make(map[ChangeType]bool)
			for _, change := range changes {
				changeTypes[change.Type] = true
			}

			for _, wantType := range tt.wantChanges {
				if !changeTypes[wantType] {
					t.Errorf("Expected change type %v not detected", wantType)
				}
			}

			// For attribute changes, we expect multiple individual changes
			// So just verify that the expected change type exists
			if tt.name != "Detect attribute change" && len(changes) != len(tt.wantChanges) {
				t.Errorf("Expected %d changes, got %d", len(tt.wantChanges), len(changes))
			}
		})
	}
}

func TestDataFusion_FuseBuilding(t *testing.T) {
	confidenceManager := spatial.NewConfidenceManager()
	coverageTracker := spatial.NewCoverageTracker("test-building")
	fusion := NewDataFusion(confidenceManager, coverageTracker)

	// Mock building model
	existingModel := &mockBuildingModel{
		equipment: map[string]*MergedEquipment{
			"equip1": {
				EquipmentID: "equip1",
				Type:        "HVAC",
				Position:    spatial.Point3D{X: 10, Y: 20, Z: 3},
				Dimensions:  Dimensions{Length: 2, Width: 1, Height: 0.5},
				Confidence:  spatial.ConfidenceMedium,
			},
		},
	}

	sources := []DataSource{
		{
			ID:         "source1",
			Type:       "lidar",
			Confidence: spatial.ConfidenceHigh,
			Timestamp:  time.Now(),
			Data: map[string]interface{}{
				"position": spatial.Point3D{X: 10.5, Y: 20.5, Z: 3},
				"type":     "HVAC",
			},
			Metadata: map[string]interface{}{
				"equipment_id": "equip1",
			},
		},
		{
			ID:         "source2",
			Type:       "manual",
			Confidence: spatial.ConfidenceLow,
			Timestamp:  time.Now().Add(-time.Hour),
			Data: map[string]interface{}{
				"position": spatial.Point3D{X: 11, Y: 21, Z: 3},
				"type":     "HVAC",
			},
			Metadata: map[string]interface{}{
				"equipment_id": "equip1",
			},
		},
	}

	result, err := fusion.FuseBuilding("test-building", sources, existingModel)
	if err != nil {
		t.Fatalf("FuseBuilding() error = %v", err)
	}

	// Validate result
	if result.BuildingID != "test-building" {
		t.Errorf("Expected building ID 'test-building', got %s", result.BuildingID)
	}

	if len(result.MergedEquipment) == 0 {
		t.Error("Expected merged equipment in result")
	}

	// Should detect changes from existing model
	if len(result.Changes) == 0 {
		t.Error("Expected changes to be detected")
	}

	// Check statistics
	if result.Statistics.TotalSources != 2 {
		t.Errorf("Expected 2 sources, got %d", result.Statistics.TotalSources)
	}

	if result.Statistics.EquipmentProcessed != 1 {
		t.Errorf("Expected 1 equipment processed, got %d", result.Statistics.EquipmentProcessed)
	}
}

func TestMergeVisualizer_GenerateVisualization(t *testing.T) {
	confidenceManager := spatial.NewConfidenceManager()
	coverageTracker := spatial.NewCoverageTracker("test-building")
	merger := NewSmartMerger(confidenceManager, coverageTracker)
	resolver := NewConflictResolver(confidenceManager)
	detector := NewChangeDetector()
	fusion := NewDataFusion(confidenceManager, coverageTracker)

	visualizer := NewMergeVisualizer(merger, resolver, detector, fusion)

	result := &FusionResult{
		BuildingID: "test-building",
		Timestamp:  time.Now(),
		MergedEquipment: []*MergedEquipment{
			{
				EquipmentID: "equip1",
				Type:        "HVAC",
				Position:    spatial.Point3D{X: 10, Y: 20, Z: 3},
				Confidence:  spatial.ConfidenceHigh,
			},
		},
		Changes: []Change{
			{
				ID:          "change1",
				EquipmentID: "equip1",
				Type:        ChangeTypePosition,
				Field:       "position",
				Magnitude:   1.5,
				Timestamp:   time.Now(),
			},
		},
		Conflicts: []Conflict{
			{
				ID:          "conflict1",
				EquipmentID: "equip1",
				Type:        "position",
				Difference:  2.0,
			},
		},
		Coverage:        75.5,
		ConfidenceScore: 0.85,
		Statistics: FusionStatistics{
			TotalSources:       5,
			EquipmentProcessed: 1,
			ConflictsDetected:  1,
			ChangesDetected:    1,
			ProcessingTime:     100 * time.Millisecond,
		},
	}

	tests := []struct {
		name    string
		format  string
		options VisualizationOptions
	}{
		{
			name:   "Generate JSON visualization",
			format: "json",
			options: VisualizationOptions{
				Format:         "json",
				ShowStatistics: true,
				ShowChanges:    true,
				ShowConflicts:  true,
			},
		},
		{
			name:   "Generate text visualization",
			format: "text",
			options: VisualizationOptions{
				Format:         "text",
				ShowStatistics: true,
				ShowChanges:    true,
			},
		},
		{
			name:   "Generate HTML visualization",
			format: "html",
			options: VisualizationOptions{
				Format:        "html",
				ShowStatistics: true,
			},
		},
		{
			name:   "Generate SVG visualization",
			format: "svg",
			options: VisualizationOptions{
				Format:        "svg",
				ShowConfidence: true,
			},
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			output, err := visualizer.GenerateVisualization(result, tt.options)
			if err != nil {
				t.Fatalf("GenerateVisualization() error = %v", err)
			}

			if output == "" {
				t.Error("Expected non-empty visualization output")
			}

			// Basic validation based on format
			switch tt.format {
			case "json":
				if output[0] != '{' {
					t.Error("Expected JSON output to start with '{'")
				}
			case "html":
				if len(output) < 100 || !testContains([]string{"<html>"}, output[:100]) {
					t.Error("Expected HTML output")
				}
			case "svg":
				if len(output) < 100 || !testContains([]string{"<svg"}, output[:100]) {
					t.Error("Expected SVG output")
				}
			}
		})
	}
}

func TestMergeDiagnostics_Operations(t *testing.T) {
	diagnostics := NewMergeDiagnostics()

	// Test merge operation tracking
	operationID := diagnostics.RecordMergeStart("test-building", 3)
	if operationID == "" {
		t.Error("Expected operation ID to be returned")
	}

	result := &FusionResult{
		BuildingID: "test-building",
		MergedEquipment: []*MergedEquipment{
			{EquipmentID: "equip1"},
		},
		Conflicts: []Conflict{{ID: "c1"}},
		Resolutions: []*ResolutionResult{{Method: MethodAutomatic}},
		Changes: []Change{{ID: "ch1"}},
		Statistics: FusionStatistics{
			SourceBreakdown: map[string]int{"lidar": 2, "manual": 1},
		},
	}

	diagnostics.RecordMergeComplete(operationID, result, 100*time.Millisecond)

	// Get metrics
	metrics := diagnostics.GetMetrics()
	if metrics.TotalMerges != 1 {
		t.Errorf("Expected 1 total merge, got %d", metrics.TotalMerges)
	}
	if metrics.SuccessfulMerges != 1 {
		t.Errorf("Expected 1 successful merge, got %d", metrics.SuccessfulMerges)
	}

	// Test error recording
	diagnostics.RecordMergeError("op2", &testError{})
	metrics = diagnostics.GetMetrics()
	if metrics.FailedMerges != 1 {
		t.Errorf("Expected 1 failed merge, got %d", metrics.FailedMerges)
	}

	// Test performance tracking
	stopFunc := diagnostics.StartOperation("test_operation")
	time.Sleep(10 * time.Millisecond)
	stopFunc()

	perfStats := diagnostics.GetPerformanceStats()
	if _, exists := perfStats["test_operation"]; !exists {
		t.Error("Expected test_operation in performance stats")
	}

	// Test health report - with 1 success and 1 failure (50% error rate),
	// status should be unhealthy or degraded
	report := diagnostics.GenerateHealthReport()
	if report.Status == HealthStatusHealthy {
		t.Errorf("Expected non-healthy status with 50%% error rate, got %v", report.Status)
	}

	// Test summary generation
	summary := diagnostics.GetSummary()
	if summary == "" {
		t.Error("Expected non-empty summary")
	}
}

// Mock implementations for testing

type mockBuildingModel struct {
	equipment map[string]*MergedEquipment
}

func (m *mockBuildingModel) GetEquipment(id string) *MergedEquipment {
	return m.equipment[id]
}

func (m *mockBuildingModel) GetAllEquipment() []*MergedEquipment {
	result := make([]*MergedEquipment, 0, len(m.equipment))
	for _, eq := range m.equipment {
		result = append(result, eq)
	}
	return result
}

func (m *mockBuildingModel) GetFloorPlan(floor int) interface{} {
	return nil
}

type testError struct{}

func (e *testError) Error() string {
	return "test error"
}

// testContains checks if a slice contains any of the strings
func testContains(needles []string, haystack string) bool {
	for _, needle := range needles {
		if len(haystack) >= len(needle) {
			for i := 0; i <= len(haystack)-len(needle); i++ {
				if haystack[i:i+len(needle)] == needle {
					return true
				}
			}
		}
	}
	return false
}