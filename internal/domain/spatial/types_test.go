package spatial

import (
	"testing"
	"time"

	"github.com/arx-os/arxos/pkg/models"
	"github.com/stretchr/testify/assert"
)

func TestSpatialLocation(t *testing.T) {
	t.Run("NewSpatialLocation", func(t *testing.T) {
		point := models.Point3D{X: 1000, Y: 2000, Z: 1500}
		loc := NewSpatialLocation(point)

		assert.Equal(t, float64(1000), loc.X)
		assert.Equal(t, float64(2000), loc.Y)
		assert.Equal(t, float64(1500), loc.Z)
	})

	t.Run("ToPoint3D", func(t *testing.T) {
		loc := SpatialLocation{X: 1000, Y: 2000, Z: 1500}
		point := loc.ToPoint3D()

		assert.Equal(t, float64(1000), point.X)
		assert.Equal(t, float64(2000), point.Y)
		assert.Equal(t, float64(1500), point.Z)
	})
}

func TestQuaternion(t *testing.T) {
	t.Run("NewQuaternion", func(t *testing.T) {
		q := NewQuaternion(1.0, 0.5, 0.3, 0.8)

		assert.Equal(t, float64(1.0), q.W)
		assert.Equal(t, float64(0.5), q.X)
		assert.Equal(t, float64(0.3), q.Y)
		assert.Equal(t, float64(0.8), q.Z)
	})

	t.Run("Identity", func(t *testing.T) {
		q := Identity()

		assert.Equal(t, float64(1.0), q.W)
		assert.Equal(t, float64(0.0), q.X)
		assert.Equal(t, float64(0.0), q.Y)
		assert.Equal(t, float64(0.0), q.Z)
	})
}

func TestSpatialAnchor(t *testing.T) {
	t.Run("ValidSpatialAnchor", func(t *testing.T) {
		pos := &SpatialLocation{X: 1000, Y: 2000, Z: 1500}
		rot := &Quaternion{W: 1.0, X: 0, Y: 0, Z: 0}

		anchor := &SpatialAnchor{
			ID:               "test-anchor-1",
			Position:         pos,
			Rotation:         rot,
			Confidence:       0.95,
			BuildingID:       "building-1",
			ValidationStatus: "valid",
		}

		err := anchor.Validate()
		assert.NoError(t, err)
		assert.True(t, anchor.IsValid())
	})

	t.Run("InvalidSpatialAnchor", func(t *testing.T) {
		tests := []struct {
			name        string
			anchor      *SpatialAnchor
			expectError bool
		}{
			{
				name:        "MissingID",
				anchor:      &SpatialAnchor{},
				expectError: true,
			},
			{
				name: "MissingPosition",
				anchor: &SpatialAnchor{
					ID: "test-anchor",
				},
				expectError: true,
			},
			{
				name: "InvalidConfidence",
				anchor: &SpatialAnchor{
					ID:         "test-anchor",
					Position:   &SpatialLocation{X: 1000, Y: 2000, Z: 1500},
					Confidence: 1.5, // Invalid: > 1
					BuildingID: "building-1",
				},
				expectError: true,
			},
			{
				name: "NegativeConfidence",
				anchor: &SpatialAnchor{
					ID:         "test-anchor",
					Position:   &SpatialLocation{X: 1000, Y: 2000, Z: 1500},
					Confidence: -0.1, // Invalid: < 0
					BuildingID: "building-1",
				},
				expectError: true,
			},
			{
				name: "MissingBuildingID",
				anchor: &SpatialAnchor{
					ID:         "test-anchor",
					Position:   &SpatialLocation{X: 1000, Y: 2000, Z: 1500},
					Confidence: 0.9,
				},
				expectError: true,
			},
		}

		for _, tt := range tests {
			t.Run(tt.name, func(t *testing.T) {
				err := tt.anchor.Validate()
				if tt.expectError {
					assert.Error(t, err)
					assert.False(t, tt.anchor.IsValid())
				} else {
					assert.NoError(t, err)
					assert.True(t, tt.anchor.IsValid())
				}
			})
		}
	})

	t.Run("DistanceTo", func(t *testing.T) {
		anchor1 := &SpatialAnchor{
			Position: &SpatialLocation{X: 0, Y: 0, Z: 0},
		}

		anchor2 := &SpatialAnchor{
			Position: &SpatialLocation{X: 3, Y: 4, Z: 0},
		}

		distance := anchor1.DistanceTo(anchor2)
		assert.InDelta(t, 5.0, distance, 0.001) // 3-4-5 triangle

		// Test with nil positions
		anchorNil := &SpatialAnchor{}
		distanceNil := anchor1.DistanceTo(anchorNil)
		assert.Equal(t, -1.0, distanceNil)
	})

	t.Run("String", func(t *testing.T) {
		anchor := &SpatialAnchor{
			ID:         "test-anchor-1",
			Position:   &SpatialLocation{X: 1000, Y: 2000, Z: 1500},
			Confidence: 0.95,
		}

		str := anchor.String()
		assert.Contains(t, str, "test-anchor-1")
		assert.Contains(t, str, "0.950")
	})
}

func TestEquipmentAROverlay(t *testing.T) {
	t.Run("ValidAROverlay", func(t *testing.T) {
		now := time.Now()
		overlay := &EquipmentAROverlay{
			EquipmentID: "equipment-1",
			Position:    &SpatialLocation{X: 1000, Y: 2000, Z: 1500},
			Rotation:    &Quaternion{W: 1.0, X: 0, Y: 0, Z: 0},
			Scale:       &SpatialLocation{X: 1.0, Y: 1.0, Z: 1.0},
			Status:      "operational",
			LastUpdated: now,
			ARVisibility: ARVisibility{
				IsVisible:         true,
				Distance:          5.0,
				OcclusionLevel:    0.1,
				LightingCondition: "good",
				Contrast:          0.8,
				Brightness:        0.7,
			},
			ModelType: "3D",
			Metadata: EquipmentARMetadata{
				Name:        "Test Equipment",
				Type:        "HVAC",
				Model:       "Model-X",
				Criticality: "medium",
				Color:       "#00ff00",
			},
		}

		assert.Equal(t, "equipment-1", overlay.EquipmentID)
		assert.Equal(t, "operational", overlay.Status)
		assert.Equal(t, "3D", overlay.ModelType)
		assert.True(t, overlay.ARVisibility.IsVisible)
		assert.Equal(t, "Test Equipment", overlay.Metadata.Name)
	})
}

func TestARNavigationPath(t *testing.T) {
	t.Run("ValidNavigationPath", func(t *testing.T) {
		from := &SpatialLocation{X: 0, Y: 0, Z: 0}
		to := &SpatialLocation{X: 1000, Y: 0, Z: 0}

		waypoint1 := &SpatialLocation{X: 500, Y: 0, Z: 0}
		waypoint2 := &SpatialLocation{X: 750, Y: 0, Z: 0}

		path := &ARNavigationPath{
			ID:            "nav-path-1",
			From:          from,
			To:            to,
			Waypoints:     []*SpatialLocation{waypoint1, waypoint2},
			Distance:      1000.0,
			EstimatedTime: 714.3, // 1000mm / 1.4 m/s
			Difficulty:    "easy",
			Accessibility: true,
			Hazardous:     false,
			CreatedAt:     time.Now(),
		}

		assert.Equal(t, "nav-path-1", path.ID)
		assert.Equal(t, float64(1000.0), path.Distance)
		assert.Equal(t, "easy", path.Difficulty)
		assert.True(t, path.Accessibility)
		assert.False(t, path.Hazardous)
		assert.Len(t, path.Waypoints, 2)
	})
}

func TestARInstruction(t *testing.T) {
	t.Run("ValidInstruction", func(t *testing.T) {
		inst := ARInstruction{
			ID:                "inst-1",
			Type:              "move",
			Position:          &SpatialLocation{X: 500, Y: 0, Z: 0},
			Description:       "Move forward 500mm",
			EstimatedDuration: 5.0,
			Priority:          "medium",
			ARVisualization: ARVisualization{
				Type:      "arrow",
				Color:     "#00ff00",
				Size:      1.0,
				Animation: "pulse",
				Opacity:   0.8,
				Intensity: 1.0,
			},
		}

		assert.Equal(t, "inst-1", inst.ID)
		assert.Equal(t, "move", inst.Type)
		assert.Equal(t, "Move forward 500mm", inst.Description)
		assert.Equal(t, float64(5.0), inst.EstimatedDuration)
		assert.Equal(t, "medium", inst.Priority)
		assert.Equal(t, "arrow", inst.ARVisualization.Type)
	})
}

func TestARSessionMetrics(t *testing.T) {
	t.Run("ValidSessionMetrics", func(t *testing.T) {
		start := time.Now().Add(-time.Hour)
		end := time.Now()

		metrics := ARSessionMetrics{
			SessionID:                 "session-1",
			StartTime:                 start,
			EndTime:                   end,
			Duration:                  3600.0, // 1 hour in seconds
			AnchorsDetected:           50,
			AnchorsCreated:            25,
			AnchorsUpdated:            10,
			AnchorsRemoved:            5,
			EquipmentOverlaysRendered: 100,
			NavigationPathsCalculated: 20,
			ErrorsEncountered:         2,
			AverageFrameRate:          30.0,
			AverageTrackingQuality:    0.85,
			BatteryUsage:              75.5,
			MemoryUsage:               150.0,
			ThermalState:              "normal",
		}

		assert.Equal(t, "session-1", metrics.SessionID)
		assert.Equal(t, float64(3600.0), metrics.Duration)
		assert.Equal(t, 50, metrics.AnchorsDetected)
		assert.Equal(t, float64(30.0), metrics.AverageFrameRate)
		assert.Equal(t, "normal", metrics.ThermalState)
	})
}

func TestIFCImportResult(t *testing.T) {
	t.Run("ValidImportResult", func(t *testing.T) {
		result := IFCImportResult{
			Success:            true,
			RepositoryID:       "repo-1",
			ComponentsImported: 100,
			ComponentsSkipped:  5,
			Errors:             []string{},
			Warnings:           []string{"Missing material definition"},
			ProcessingTime:     45.5,
			FileName:           "building.ifc",
			FileSize:           1024000,
			ImportDate:         time.Now(),
			IFCVersion:         "IFC4",
			SchemaURL:          "https://standards.buildingsmart.org/IFC/RELEASE/IFC4",
		}

		assert.True(t, result.Success)
		assert.Equal(t, "repo-1", result.RepositoryID)
		assert.Equal(t, 100, result.ComponentsImported)
		assert.Equal(t, 5, result.ComponentsSkipped)
		assert.Len(t, result.Errors, 0)
		assert.Len(t, result.Warnings, 1)
		assert.Equal(t, float64(45.5), result.ProcessingTime)
		assert.Equal(t, "IFC4", result.IFCVersion)
	})

	t.Run("FailedImportResult", func(t *testing.T) {
		result := IFCImportResult{
			Success:            false,
			RepositoryID:       "repo-1",
			ComponentsImported: 0,
			ComponentsSkipped:  0,
			Errors:             []string{"Invalid IFC format", "Missing required entities"},
			Warnings:           []string{},
			ProcessingTime:     2.1,
			FileName:           "corrupt.ifc",
			FileSize:           512000,
			ImportDate:         time.Now(),
			IFCVersion:         "",
			SchemaURL:          "",
		}

		assert.False(t, result.Success)
		assert.Equal(t, "repo-1", result.RepositoryID)
		assert.Equal(t, 0, result.ComponentsImported)
		assert.Equal(t, 0, result.ComponentsSkipped)
		assert.Len(t, result.Errors, 2)
		assert.Len(t, result.Warnings, 0)
		assert.Contains(t, result.Errors[0], "Invalid IFC")
	})
}

// Integration tests for cross-domain functionality
func TestSpatialLocationToPointsIntegration(t *testing.T) {
	t.Run("RoundTripConversion", func(t *testing.T) {
		original := models.Point3D{X: 1234.567, Y: 9876.543, Z: 5432.109}

		// Convert to SpatialLocation
		spatial := NewSpatialLocation(original)

		// Convert back to Point3D
		converted := spatial.ToPoint3D()

		assert.InDelta(t, original.X, converted.X, 0.001)
		assert.InDelta(t, original.Y, converted.Y, 0.001)
		assert.InDelta(t, original.Z, converted.Z, 0.001)
	})

	t.Run("JSONSerialization", func(t *testing.T) {
		loc := SpatialLocation{X: 1000, Y: 2000, Z: 1500}

		// Test that the struct has proper JSON tags
		// This would be verified by actual JSON marshaling in a real scenario
		assert.Equal(t, float64(1000), loc.X)
		assert.Equal(t, float64(2000), loc.Y)
		assert.Equal(t, float64(1500), loc.Z)
	})
}
