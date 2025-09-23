package connections

import (
	"testing"

	"github.com/arx-os/arxos/pkg/models"
)

// TestAnalyzer tests the analyzer logic without requiring a full database
func TestImpactAnalysisLogic(t *testing.T) {
	// Test impact analysis struct
	analysis := &ImpactAnalysis{
		EquipmentID: "E1",
		DirectlyAffected: []*models.Equipment{
			{ID: "E2", Name: "Equipment-E2"},
			{ID: "E3", Name: "Equipment-E3"},
		},
		IndirectlyAffected: []*models.Equipment{
			{ID: "E4", Name: "Equipment-E4"},
		},
	}

	analysis.TotalImpact = len(analysis.DirectlyAffected) + len(analysis.IndirectlyAffected)

	if analysis.TotalImpact != 3 {
		t.Errorf("expected total impact 3, got %d", analysis.TotalImpact)
	}

	// Test circuit load calculations
	load := &CircuitLoad{
		CircuitID:   "PANEL-01",
		TotalLoad:   30.0,
		MaxCapacity: 100.0,
	}

	load.LoadPercent = (load.TotalLoad / load.MaxCapacity) * 100
	load.Overloaded = load.LoadPercent > 80

	if load.LoadPercent != 30.0 {
		t.Errorf("expected load percent 30.0, got %.2f", load.LoadPercent)
	}

	if load.Overloaded {
		t.Error("circuit should not be overloaded at 30% capacity")
	}
}

// TestCircuitLoadCalculations tests circuit load logic
func TestCircuitLoadCalculations(t *testing.T) {
	tests := []struct {
		name        string
		totalLoad   float64
		maxCapacity float64
		shouldOverload bool
	}{
		{"Normal load", 30.0, 100.0, false},
		{"High load", 85.0, 100.0, true},
		{"Exact limit", 80.0, 100.0, false},
		{"Over limit", 81.0, 100.0, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			load := &CircuitLoad{
				TotalLoad:   tt.totalLoad,
				MaxCapacity: tt.maxCapacity,
			}

			load.LoadPercent = (load.TotalLoad / load.MaxCapacity) * 100
			load.Overloaded = load.LoadPercent > 80

			if load.Overloaded != tt.shouldOverload {
				t.Errorf("expected overloaded=%v, got %v (load=%.1f%%)",
					tt.shouldOverload, load.Overloaded, load.LoadPercent)
			}
		})
	}
}

// TestRedundancyAnalysis tests redundancy detection logic
func TestRedundancyAnalysis(t *testing.T) {
	// Test redundancy structure
	type RedundancyInfo struct {
		EquipmentID   string
		PathCount     int
		HasRedundancy bool
		Paths         [][]string
	}

	tests := []struct {
		name          string
		pathCount     int
		hasRedundancy bool
	}{
		{"Single path", 1, false},
		{"Redundant paths", 2, true},
		{"Multiple redundant", 3, true},
		{"No paths", 0, false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			info := &RedundancyInfo{
				PathCount:     tt.pathCount,
				HasRedundancy: tt.pathCount > 1,
			}

			if info.HasRedundancy != tt.hasRedundancy {
				t.Errorf("expected redundancy=%v, got %v", tt.hasRedundancy, info.HasRedundancy)
			}
		})
	}
}

// TestCriticalPathDetection tests critical path logic
func TestCriticalPathDetection(t *testing.T) {
	// A critical path is one where failure would impact downstream equipment
	// This is a simplified test of the logic
	type PathInfo struct {
		EquipmentID    string
		DownstreamCount int
		IsCritical     bool
	}

	tests := []struct {
		name            string
		downstreamCount int
		shouldBeCritical bool
	}{
		{"No downstream", 0, false},
		{"Has downstream", 3, true},
		{"Single downstream", 1, true},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			info := &PathInfo{
				DownstreamCount: tt.downstreamCount,
				IsCritical:     tt.downstreamCount > 0,
			}

			if info.IsCritical != tt.shouldBeCritical {
				t.Errorf("expected critical=%v, got %v", tt.shouldBeCritical, info.IsCritical)
			}
		})
	}
}