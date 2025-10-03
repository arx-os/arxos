package domain

import (
	"math"
	"testing"
	"time"

	"github.com/stretchr/testify/assert"
)

func TestSpatialValidator_ValidateSpatialLocation(t *testing.T) {
	validator := NewSpatialValidator()

	tests := []struct {
		name     string
		location *SpatialLocation
		wantErr  bool
		errMsg   string
	}{
		{
			name:     "Valid location",
			location: &SpatialLocation{X: 100, Y: 200, Z: 300},
			wantErr:  false,
		},
		{
			name:     "Nil location",
			location: nil,
			wantErr:  true,
			errMsg:   "spatial location cannot be nil",
		},
		{
			name:     "NaN coordinates",
			location: &SpatialLocation{X: math.NaN(), Y: 200, Z: 300},
			wantErr:  true,
			errMsg:   "spatial location coordinates cannot be NaN",
		},
		{
			name:     "Infinite coordinates",
			location: &SpatialLocation{X: math.Inf(1), Y: math.Inf(1), Z: math.Inf(1)},
			wantErr:  true,
			errMsg:   "spatial location coordinates cannot be infinite",
		},
		{
			name:     "Coordinates exceed range",
			location: &SpatialLocation{X: 2000000, Y: 2000000, Z: 2000000},
			wantErr:  true,
			errMsg:   "spatial location coordinates exceed maximum range",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validator.ValidateSpatialLocation(tt.location)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), tt.errMsg)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestSpatialValidator_ValidateQuaternion(t *testing.T) {
	validator := NewSpatialValidator()

	tests := []struct {
		name    string
		quat    *Quaternion
		wantErr bool
		errMsg  string
	}{
		{
			name:    "Valid normalized quaternion",
			quat:    &Quaternion{W: 1, X: 0, Y: 0, Z: 0},
			wantErr: false,
		},
		{
			name:    "Nil quaternion",
			quat:    nil,
			wantErr: true,
			errMsg:  "quaternion cannot be nil",
		},
		{
			name:    "NaN components",
			quat:    &Quaternion{W: math.NaN(), X: 0, Y: 0, Z: 0},
			wantErr: true,
			errMsg:  "quaternion components cannot be NaN",
		},
		{
			name:    "Infinite components",
			quat:  &Quaternion{W: math.Inf(1), X: math.Inf(1), Y: math.Inf(1), Z: math.Inf(1)},
			wantErr: true,
			errMsg:  "quaternion components cannot be infinite",
		},
		{
			name:    "Not normalized",
			quat:    &Quaternion{W: 2, X: 0, Y: 0, Z: 0},
			wantErr: true,
			errMsg:  "quaternion is not normalized",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validator.ValidateQuaternion(tt.quat)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), tt.errMsg)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestSpatialValidator_ValidateSpatialAnchor(t *testing.T) {
	validator := NewSpatialValidator()

	tests := []struct {
		name    string
		anchor  *SpatialAnchor
		wantErr bool
		errMsg  string
	}{
		{
			name: "Valid anchor",
			anchor: &SpatialAnchor{
				ID:          "anchor-001",
				Position:    &SpatialLocation{X: 100, Y: 200, Z: 300},
				Rotation:    &Quaternion{W: 1, X: 0, Y: 0, Z: 0},
				Confidence:  0.9,
				Timestamp:   time.Now(),
				BuildingID:  "building-001",
				FloorID:     "floor-001",
				RoomID:      "room-001",
				EquipmentID: "equipment-001",
				Platform:    "ARKit",
				Stability:    0.8,
				Range:       10.0,
			},
			wantErr: false,
		},
		{
			name:    "Nil anchor",
			anchor:  nil,
			wantErr: true,
			errMsg:  "spatial anchor cannot be nil",
		},
		{
			name: "Empty ID",
			anchor: &SpatialAnchor{
				ID:       "",
				Position: &SpatialLocation{X: 100, Y: 200, Z: 300},
				Rotation: &Quaternion{W: 1, X: 0, Y: 0, Z: 0},
				BuildingID: "building-001",
			},
			wantErr: true,
			errMsg:  "spatial anchor ID cannot be empty",
		},
		{
			name: "Invalid confidence",
			anchor: &SpatialAnchor{
				ID:         "anchor-001",
				Position:   &SpatialLocation{X: 100, Y: 200, Z: 300},
				Rotation:   &Quaternion{W: 1, X: 0, Y: 0, Z: 0},
				Confidence: 1.5, // Invalid: > 1
				BuildingID: "building-001",
			},
			wantErr: true,
			errMsg:  "spatial anchor confidence must be between 0 and 1",
		},
		{
			name: "Low confidence",
			anchor: &SpatialAnchor{
				ID:         "anchor-001",
				Position:   &SpatialLocation{X: 100, Y: 200, Z: 300},
				Rotation:   &Quaternion{W: 1, X: 0, Y: 0, Z: 0},
				Confidence: 0.3, // Below minimum threshold
				BuildingID: "building-001",
			},
			wantErr: true,
			errMsg:  "spatial anchor confidence .* is below minimum threshold",
		},
		{
			name: "Invalid platform",
			anchor: &SpatialAnchor{
				ID:         "anchor-001",
				Position:   &SpatialLocation{X: 100, Y: 200, Z: 300},
				Rotation:   &Quaternion{W: 1, X: 0, Y: 0, Z: 0},
				Confidence: 0.9,
				Timestamp: time.Now(), // Use current time
				Platform:  "InvalidPlatform",
				BuildingID: "building-001",
			},
			wantErr: true,
			errMsg:  "invalid AR platform",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validator.ValidateSpatialAnchor(tt.anchor)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Regexp(t, tt.errMsg, err.Error())
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestSpatialValidator_ValidateARNavigationPath(t *testing.T) {
	validator := NewSpatialValidator()

	waypoints := []*SpatialLocation{
		{X: 0, Y: 0, Z: 0},
		{X: 100, Y: 100, Z: 0},
		{X: 200, Y: 200, Z: 0},
	}

	instructions := []ARInstruction{
		{
			ID:       "inst-1",
			Type:     "move",
			Position: waypoints[1],
			Priority: "medium",
			ARVisualization: ARVisualization{
				Type:  "arrow",
				Color: "#00ff00",
				Size:  1.0,
				Opacity: 0.8,
				Intensity: 1.0,
				Animation: "pulse",
			},
		},
	}

	tests := []struct {
		name string
		path *ARNavigationPath
		wantErr bool
		errMsg string
	}{
		{
			name: "Valid navigation path",
			path: &ARNavigationPath{
				ID:             "path-001",
				Waypoints:      waypoints,
				Distance:       141.42, // Approximate distance
				EstimatedTime:  100,    // seconds
				Difficulty:     "easy",
				Accessibility:  true,
				ARInstructions: instructions,
			},
			wantErr: false,
		},
		{
			name:    "Nil path",
			path:    nil,
			wantErr: true,
			errMsg:  "AR navigation path cannot be nil",
		},
		{
			name: "Empty ID",
			path: &ARNavigationPath{
				ID:        "",
				Waypoints: waypoints,
			},
			wantErr: true,
			errMsg:  "AR navigation path ID cannot be empty",
		},
		{
			name: "Negative distance",
			path: &ARNavigationPath{
				ID:        "path-001",
				Distance:  -10,
				Waypoints: waypoints,
			},
			wantErr: true,
			errMsg:  "AR navigation path distance cannot be negative",
		},
		{
			name: "Invalid difficulty",
			path: &ARNavigationPath{
				ID:        "path-001",
				Distance:  100,
				Waypoints: waypoints,
				Difficulty: "invalid",
			},
			wantErr: true,
			errMsg:  "invalid difficulty level",
		},
		{
			name: "Distance exceeds maximum",
			path: &ARNavigationPath{
				ID:       "path-001",
				Distance: 20000.0, // Exceeds default max distance
				Waypoints: waypoints,
			},
			wantErr: true,
			errMsg:  "exceeds maximum",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validator.ValidateARNavigationPath(tt.path)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), tt.errMsg)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestSpatialValidator_ValidateARInstruction(t *testing.T) {
	validator := NewSpatialValidator()
	
	position := &SpatialLocation{X: 100, Y: 200, Z: 300}
	visualization := ARVisualization{
		Type:     "arrow",
		Color:    "#00ff00",
		Size:     1.0,
		Opacity:  0.8,
		Intensity: 1.0,
		Animation: "pulse",
	}

	tests := []struct {
		name       string
		instruction *ARInstruction
		wantErr    bool
		errMsg     string
	}{
		{
			name: "Valid instruction",
			instruction: &ARInstruction{
				ID:                "inst-1",
				Type:              "move",
				Position:          position,
				Description:       "Move forward",
				EstimatedDuration: 5.0,
				Priority:          "medium",
				ARVisualization:   visualization,
			},
			wantErr: false,
		},
		{
			name:       "Nil instruction",
			instruction: nil,
			wantErr:    true,
			errMsg:     "AR instruction cannot be nil",
		},
		{
			name: "Empty ID",
			instruction: &ARInstruction{
				ID:    "",
				Type:  "move",
			},
			wantErr: true,
			errMsg:  "AR instruction ID cannot be empty",
		},
		{
			name: "Invalid type",
			instruction: &ARInstruction{
				ID:   "inst-1",
				Type: "invalid",
			},
			wantErr: true,
			errMsg:  "invalid instruction type",
		},
		{
			name: "Negative duration",
			instruction: &ARInstruction{
				ID:                "inst-1",
				Type:              "move",
				EstimatedDuration: -5.0,
			},
			wantErr: true,
			errMsg:  "AR instruction estimated duration cannot be negative",
		},
		{
			name: "Invalid priority",
			instruction: &ARInstruction{
				ID:       "inst-1",
				Type:     "move",
				Priority: "extra_high", // Invalid priority
			},
			wantErr: true,
			errMsg:  "invalid instruction priority",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validator.ValidateARInstruction(tt.instruction)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), tt.errMsg)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestSpatialValidator_ValidateARVisualization(t *testing.T) {
	validator := NewSpatialValidator()

	tests := []struct {
		name         string
		visualization *ARVisualization
		wantErr      bool
		errMsg       string
	}{
		{
			name: "Valid visualization",
			visualization: &ARVisualization{
				Type:      "arrow",
				Color:     "#00ff00",
				Size:      1.5,
				Opacity:   0.8,
				Intensity: 1.0,
				Animation: "pulse",
			},
			wantErr: false,
		},
		{
			name:         "Nil visualization",
			visualization: nil,
			wantErr:      true,
			errMsg:       "AR visualization cannot be nil",
		},
		{
			name: "Invalid type",
			visualization: &ARVisualization{
				Type: "invalid",
			},
			wantErr: true,
			errMsg:  "invalid visualization type",
		},
		{
			name: "Invalid color format",
			visualization: &ARVisualization{
				Type:  "arrow",
				Color: "rgb(255,0,0)", // Invalid format, should be hex
			},
			wantErr: true,
			errMsg:  "invalid visualization color format",
		},
		{
			name: "Negative size",
			visualization: &ARVisualization{
				Type: "arrow",
				Size: -1.0,
			},
			wantErr: true,
			errMsg:  "visualization size must be positive",
		},
		{
			name: "Size exceeds maximum",
			visualization: &ARVisualization{
				Type: "arrow",
				Size: 15.0, // Exceeds maximum of 10.0
			},
			wantErr: true,
			errMsg:  "visualization size .* exceeds maximum",
		},
		{
			name: "Invalid opacity",
			visualization: &ARVisualization{
				Type:    "arrow",
				Size:    1.0, // Add size field
				Opacity: 1.5, // > 1
			},
			wantErr: true,
			errMsg:  "visualization opacity must be between 0 and 1",
		},
		{
			name: "Invalid intensity",
			visualization: &ARVisualization{
				Type:      "arrow",
				Size:      1.0, // Add size field
				Intensity: -0.5, // < 0
			},
			wantErr: true,
			errMsg:  "visualization intensity must be between 0 and 1",
		},
		{
			name: "Invalid animation",
			visualization: &ARVisualization{
				Type:      "arrow",
				Size:      1.0, // Add size field
				Animation: "invalid",
			},
			wantErr: true,
			errMsg:  "invalid visualization animation",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validator.ValidateARVisualization(tt.visualization)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Regexp(t, tt.errMsg, err.Error())
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestSpatialValidator_ValidateARSessionMetrics(t *testing.T) {
	validator := NewSpatialValidator()

	startTime := time.Now().Add(-time.Hour)
	endTime := time.Now()

	tests := []struct {
		name    string
		metrics *ARSessionMetrics
		wantErr bool
		errMsg  string
	}{
		{
			name: "Valid session metrics",
			metrics: &ARSessionMetrics{
				SessionID:                 "session-001",
				StartTime:                 startTime,
				EndTime:                   endTime,
				Duration:                  3600.0, // 1 hour in seconds
				AnchorsDetected:           10,
				AnchorsCreated:           5,
				EquipmentOverlaysRendered: 20,
				AverageFrameRate:          30.0,
				AverageTrackingQuality:    0.9,
				BatteryUsage:              50.0,
				MemoryUsage:               200.0,
				ThermalState:              "normal",
			},
			wantErr: false,
		},
		{
			name:    "Nil metrics",
			metrics: nil,
			wantErr: true,
			errMsg:  "AR session metrics cannot be nil",
		},
		{
			name: "Empty session ID",
			metrics: &ARSessionMetrics{
				SessionID: "",
				StartTime: startTime,
				EndTime:   endTime,
			},
			wantErr: true,
			errMsg:  "AR session metrics session ID cannot be empty",
		},
		{
			name: "End time before start time",
			metrics: &ARSessionMetrics{
				SessionID: "session-001",
				StartTime: endTime,
				EndTime:   startTime,
			},
			wantErr: true,
			errMsg:  "AR session end time cannot be before start time",
		},
		{
			name: "Negative frame rate",
			metrics: &ARSessionMetrics{
				SessionID:        "session-001",
				StartTime:        startTime,
				EndTime:          endTime,
				Duration:         3600.0, // Add duration
				AverageFrameRate: -10.0,
			},
			wantErr: true,
			errMsg:  "AR session average frame rate cannot be negative",
		},
		{
			name: "Invalid tracking quality",
			metrics: &ARSessionMetrics{
				SessionID:               "session-001",
				StartTime:               startTime,
				EndTime:                 endTime,
				Duration:                3600.0, // Add duration
				AverageTrackingQuality: 1.5, // > 1
			},
			wantErr: true,
			errMsg:  "AR session tracking quality must be between 0 and 1",
		},
		{
			name: "Invalid battery usage",
			metrics: &ARSessionMetrics{
				SessionID:    "session-001",
				StartTime:    startTime,
				EndTime:      endTime,
				Duration:    3600.0, // Add duration
				BatteryUsage: 150.0, // > 100%
			},
			wantErr: true,
			errMsg:  "AR session battery usage must be between 0 and 100 percent",
		},
		{
			name: "Invalid thermal state",
			metrics: &ARSessionMetrics{
				SessionID:   "session-001",
				StartTime:   startTime,
				EndTime:     endTime,
				Duration:    3600.0, // Add duration
				ThermalState: "overheated", // Invalid state
			},
			wantErr: true,
			errMsg:  "invalid AR session thermal state",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validator.ValidateARSessionMetrics(tt.metrics)
			if tt.wantErr {
				assert.Error(t, err)
				assert.Contains(t, err.Error(), tt.errMsg)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestSpatialValidator_ValidateDistance(t *testing.T) {
	validator := NewSpatialValidator()

	tests := []struct {
		name            string
		from            *SpatialLocation
		to              *SpatialLocation
		expectedDistance float64
		wantErr         bool
	}{
		{
			name:            "Valid distance within tolerance",
			from:            &SpatialLocation{X: 0, Y: 0, Z: 0},
			to:              &SpatialLocation{X: 100, Y: 100, Z: 0},
			expectedDistance: 141.42,
			wantErr:         false,
		},
		{
			name:            "Distance outside tolerance",
			from:            &SpatialLocation{X: 0, Y: 0, Z: 0},
			to:              &SpatialLocation{X: 100, Y: 100, Z: 0},
			expectedDistance: 200.0, // Too far from actual distance
			wantErr:         true,
		},
		{
			name:             "Nil locations",
			from:             nil,
			to:               &SpatialLocation{X: 100, Y: 100, Z: 0},
			expectedDistance: 100.0,
			wantErr:          true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			err := validator.ValidateDistance(tt.from, tt.to, tt.expectedDistance)
			if tt.wantErr {
				assert.Error(t, err)
			} else {
				assert.NoError(t, err)
			}
		})
	}
}

func TestSpatialLocation_String(t *testing.T) {
	tests := []struct {
		name     string
		location *SpatialLocation
		expected string
	}{
		{
			name:     "Valid location",
			location: &SpatialLocation{X: 123.456, Y: 789.012, Z: 345.678},
			expected: "(123.456, 789.012, 345.678)",
		},
		{
			name:     "Nil location",
			location: nil,
			expected: "nil",
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.location.String()
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestSpatialLocation_DistanceTo(t *testing.T) {
	tests := []struct {
		name     string
		from     *SpatialLocation
		to       *SpatialLocation
		expected float64
	}{
		{
			name:     "Same location",
			from:     &SpatialLocation{X: 0, Y: 0, Z: 0},
			to:       &SpatialLocation{X: 0, Y: 0, Z: 0},
			expected: 0,
		},
		{
			name:     "Different location",
			from:     &SpatialLocation{X: 0, Y: 0, Z: 0},
			to:       &SpatialLocation{X: 3, Y: 4, Z: 0},
			expected: 5, // Pythagorean theorem: sqrt(3^2 + 4^2)
		},
		{
			name:     "Nil locations",
			from:     nil,
			to:       &SpatialLocation{X: 3, Y: 4, Z: 0},
			expected: -1,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.from.DistanceTo(tt.to)
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestSpatialLocation_IsValid(t *testing.T) {
	tests := []struct {
		name     string
		location *SpatialLocation
		expected bool
	}{
		{
			name:     "Valid coordinates",
			location: &SpatialLocation{X: 123.456, Y: 789.012, Z: 345.678},
			expected: true,
		},
		{
			name:     "NaN coordinates",
			location: &SpatialLocation{X: math.NaN(), Y: 789.012, Z: 345.678},
			expected: false,
		},
		{
			name:     "Infinite coordinates",
			location: &SpatialLocation{X: math.Inf(1), Y: math.Inf(1), Z: math.Inf(1)},
			expected: false,
		},
		{
			name:     "Nil location",
			location: nil,
			expected: false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			result := tt.location.IsValid()
			assert.Equal(t, tt.expected, result)
		})
	}
}

func TestSpatialValidator_Configuration(t *testing.T) {
	tests := []struct {
		name             string
		maxDistance      float64
		minConfidence    float64
		maxAge          time.Duration
		expectConfigErr bool
	}{
		{
			name:             "Valid configuration",
			maxDistance:      5000.0,
			minConfidence:    0.7,
			maxAge:          12 * time.Hour,
			expectConfigErr: false,
		},
		{
			name:             "High confidence threshold",
			maxDistance:      10000.0,
			minConfidence:    1.5, // Invalid: > 1
			maxAge:          24 * time.Hour,
			expectConfigErr: true,
		},
		{
			name:             "Negative distance",
			maxDistance:      -1000.0,
			minConfidence:    0.5,
			maxAge:          24 * time.Hour,
			expectConfigErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			validator := NewSpatialValidator().
				WithMaxDistance(tt.maxDistance).
				WithMinConfidence(tt.minConfidence).
				WithMaxAge(tt.maxAge)

			// Test that configuration is applied correctly
			assert.Equal(t, tt.maxDistance, validator.maxDistance)
			assert.Equal(t, tt.minConfidence, validator.minConfidence)
			assert.Equal(t, tt.maxAge, validator.maxAge)

			// Test that configuration affects validation
			anchor := &SpatialAnchor{
				ID:         "test-anchor",
				Position:   &SpatialLocation{X: 100, Y: 200, Z: 300},
				Rotation:   &Quaternion{W: 1, X: 0, Y: 0, Z: 0},
				Confidence: tt.minConfidence - 0.1, // Below threshold
				Timestamp:  time.Now(),
				BuildingID: "building-001",
			}

			err := validator.ValidateSpatialAnchor(anchor)
			if tt.expectConfigErr {
				assert.Error(t, err, "Should fail due to invalid configuration")
			} else {
				assert.Error(t, err, "Should fail due to low confidence")
			}
		})
	}
}
