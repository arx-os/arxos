package spatial_test

import (
	"testing"

	"github.com/joelpate/arxos/internal/spatial"
	"github.com/stretchr/testify/assert"
)

func TestPoint3D(t *testing.T) {
	t.Run("DistanceTo", func(t *testing.T) {
		p1 := spatial.NewPoint3D(0, 0, 0)
		p2 := spatial.NewPoint3D(3, 4, 0)

		distance := p1.DistanceTo(p2)
		assert.Equal(t, 5.0, distance)
	})

	t.Run("Add", func(t *testing.T) {
		p1 := spatial.NewPoint3D(1, 2, 3)
		p2 := spatial.NewPoint3D(4, 5, 6)

		result := p1.Add(p2)
		assert.Equal(t, 5.0, result.X)
		assert.Equal(t, 7.0, result.Y)
		assert.Equal(t, 9.0, result.Z)
	})

	t.Run("Sub", func(t *testing.T) {
		p1 := spatial.NewPoint3D(5, 7, 9)
		p2 := spatial.NewPoint3D(1, 2, 3)

		result := p1.Sub(p2)
		assert.Equal(t, 4.0, result.X)
		assert.Equal(t, 5.0, result.Y)
		assert.Equal(t, 6.0, result.Z)
	})

	t.Run("Scale", func(t *testing.T) {
		p := spatial.NewPoint3D(2, 3, 4)
		scaled := p.Scale(2.0)

		assert.Equal(t, 4.0, scaled.X)
		assert.Equal(t, 6.0, scaled.Y)
		assert.Equal(t, 8.0, scaled.Z)
	})
}

func TestBoundingBox(t *testing.T) {
	t.Run("Contains", func(t *testing.T) {
		bbox := spatial.NewBoundingBox(
			spatial.NewPoint3D(0, 0, 0),
			spatial.NewPoint3D(10, 10, 10),
		)

		assert.True(t, bbox.Contains(spatial.NewPoint3D(5, 5, 5)))
		assert.True(t, bbox.Contains(spatial.NewPoint3D(0, 0, 0)))
		assert.True(t, bbox.Contains(spatial.NewPoint3D(10, 10, 10)))
		assert.False(t, bbox.Contains(spatial.NewPoint3D(11, 5, 5)))
		assert.False(t, bbox.Contains(spatial.NewPoint3D(-1, 5, 5)))
	})

	t.Run("Volume", func(t *testing.T) {
		bbox := spatial.NewBoundingBox(
			spatial.NewPoint3D(0, 0, 0),
			spatial.NewPoint3D(2, 3, 4),
		)

		assert.Equal(t, 24.0, bbox.Volume())
	})

	t.Run("Center", func(t *testing.T) {
		bbox := spatial.NewBoundingBox(
			spatial.NewPoint3D(0, 0, 0),
			spatial.NewPoint3D(10, 10, 10),
		)

		center := bbox.Center()
		assert.Equal(t, 5.0, center.X)
		assert.Equal(t, 5.0, center.Y)
		assert.Equal(t, 5.0, center.Z)
	})
}

func TestCoordinateTranslator(t *testing.T) {
	t.Run("GridToWorld and WorldToGrid", func(t *testing.T) {
		translator := spatial.NewCoordinateTranslator("TEST-001")
		translator.SetGridScale(0.5)   // 0.5 meters per grid unit
		translator.SetFloorHeight(3.0) // 3 meters per floor

		// Test round-trip conversion
		gridX, gridY, floor := 10, 20, 2
		world := translator.GridToWorld(gridX, gridY, floor)

		assert.Equal(t, 5.0, world.X)  // 10 * 0.5
		assert.Equal(t, 10.0, world.Y) // 20 * 0.5
		assert.Equal(t, 6.0, world.Z)  // 2 * 3.0

		// Convert back
		resultX, resultY, resultFloor := translator.WorldToGrid(world)
		assert.Equal(t, gridX, resultX)
		assert.Equal(t, gridY, resultY)
		assert.Equal(t, floor, resultFloor)
	})

	t.Run("GridToWorld with Rotation", func(t *testing.T) {
		translator := spatial.NewCoordinateTranslator("TEST-002")
		translator.SetGridScale(1.0)
		translator.SetBuildingOrigin(spatial.GPSCoordinate{}, 90.0) // 90 degree rotation

		world := translator.GridToWorld(1, 0, 0)
		// After 90 degree rotation, (1,0) becomes (0,1)
		assert.InDelta(t, 0.0, world.X, 0.001)
		assert.InDelta(t, 1.0, world.Y, 0.001)
	})

	t.Run("IsSignificantMovement", func(t *testing.T) {
		translator := spatial.NewCoordinateTranslator("TEST-003")
		translator.SetGridScale(0.5)

		oldPos := spatial.NewPoint3D(0, 0, 0)

		// Small movement (less than threshold)
		// 0.2m = less than room change threshold (0.5m) and less than 1 grid unit when grid scale is 0.5
		newPos1 := spatial.NewPoint3D(0.2, 0.0, 0.0)
		assert.False(t, translator.IsSignificantMovement(oldPos, newPos1))

		// Large movement (exceeds room change threshold of 0.5m)
		newPos2 := spatial.NewPoint3D(0.5, 0.0, 0.0)
		assert.True(t, translator.IsSignificantMovement(oldPos, newPos2))

		// Floor change
		newPos3 := spatial.NewPoint3D(0, 0, 3.1)
		assert.True(t, translator.IsSignificantMovement(oldPos, newPos3))
	})

	t.Run("CalculateGridDelta", func(t *testing.T) {
		translator := spatial.NewCoordinateTranslator("TEST-004")
		translator.SetGridScale(0.5)
		translator.SetFloorHeight(3.0)

		from := spatial.NewPoint3D(0, 0, 0)
		to := spatial.NewPoint3D(1.0, 1.5, 3.0)

		delta := translator.CalculateGridDelta(from, to)
		assert.Equal(t, 2, delta.DX) // 1.0 / 0.5
		assert.Equal(t, 3, delta.DY) // 1.5 / 0.5
		assert.Equal(t, 1, delta.DZ) // 3.0 / 3.0 (floor change)

		assert.InDelta(t, 3.74, delta.Magnitude(), 0.01)
	})

	t.Run("GPSToLocal simplified", func(t *testing.T) {
		translator := spatial.NewCoordinateTranslator("TEST-005")
		origin := spatial.GPSCoordinate{
			Latitude:  40.7128,
			Longitude: -74.0060,
			Altitude:  10.0,
		}
		translator.SetBuildingOrigin(origin, 0)

		// GPS point slightly north and east
		gps := spatial.GPSCoordinate{
			Latitude:  40.7129,
			Longitude: -74.0059,
			Altitude:  10.0,
		}

		local := translator.GPSToLocal(gps)
		// Should be positive Y (north) and positive X (east)
		assert.Greater(t, local.Y, 0.0)
		assert.Greater(t, local.X, 0.0)
		assert.InDelta(t, 0.0, local.Z, 0.001)
	})

	t.Run("ARToWorld and WorldToAR", func(t *testing.T) {
		translator := spatial.NewCoordinateTranslator("TEST-006")

		anchor := spatial.SpatialAnchor{
			ID:            "anchor-1",
			WorldPosition: spatial.NewPoint3D(10, 20, 0),
		}

		arCoord := spatial.ARCoordinate{
			Position: spatial.NewPoint3D(1, 2, 3),
			AnchorID: anchor.ID,
		}

		// AR to World
		world := translator.ARToWorld(arCoord, anchor)
		assert.Equal(t, 11.0, world.X)
		assert.Equal(t, 22.0, world.Y)
		assert.Equal(t, 3.0, world.Z)

		// World to AR
		resultAR := translator.WorldToAR(world, anchor)
		assert.Equal(t, arCoord.Position.X, resultAR.Position.X)
		assert.Equal(t, arCoord.Position.Y, resultAR.Position.Y)
		assert.Equal(t, arCoord.Position.Z, resultAR.Position.Z)
		assert.Equal(t, anchor.ID, resultAR.AnchorID)
	})
}

func TestConfidenceLevel(t *testing.T) {
	t.Run("String representation", func(t *testing.T) {
		assert.Equal(t, "ESTIMATED", spatial.ConfidenceEstimated.String())
		assert.Equal(t, "LOW", spatial.ConfidenceLow.String())
		assert.Equal(t, "MEDIUM", spatial.ConfidenceMedium.String())
		assert.Equal(t, "HIGH", spatial.ConfidenceHigh.String())
	})

	t.Run("Confidence ordering", func(t *testing.T) {
		assert.True(t, spatial.ConfidenceEstimated < spatial.ConfidenceLow)
		assert.True(t, spatial.ConfidenceLow < spatial.ConfidenceMedium)
		assert.True(t, spatial.ConfidenceMedium < spatial.ConfidenceHigh)
	})
}

func TestCoverageMap(t *testing.T) {
	t.Run("GetCoveragePercentage", func(t *testing.T) {
		coverage := &spatial.CoverageMap{
			BuildingID: "TEST-001",
			TotalArea:  1000.0,
			ScannedRegions: []spatial.ScannedRegion{
				{
					Region: spatial.SpatialExtent{
						Boundary: []spatial.Point2D{
							{X: 0, Y: 0},
							{X: 10, Y: 0},
							{X: 10, Y: 10},
							{X: 0, Y: 10},
						},
					},
				},
				{
					Region: spatial.SpatialExtent{
						Boundary: []spatial.Point2D{
							{X: 10, Y: 0},
							{X: 20, Y: 0},
							{X: 20, Y: 10},
							{X: 10, Y: 10},
						},
					},
				},
			},
		}

		percentage := coverage.GetCoveragePercentage()
		// Two 10x10 squares = 200 sq units out of 1000
		assert.Equal(t, 20.0, percentage)
	})

	t.Run("Empty coverage", func(t *testing.T) {
		coverage := &spatial.CoverageMap{
			BuildingID:     "TEST-002",
			TotalArea:      1000.0,
			ScannedRegions: []spatial.ScannedRegion{},
		}

		assert.Equal(t, 0.0, coverage.GetCoveragePercentage())
	})

	t.Run("Zero total area", func(t *testing.T) {
		coverage := &spatial.CoverageMap{
			BuildingID: "TEST-003",
			TotalArea:  0,
		}

		assert.Equal(t, 0.0, coverage.GetCoveragePercentage())
	})
}

func TestEstimateAccuracy(t *testing.T) {
	tests := []struct {
		source   string
		expected float64
	}{
		{"lidar", 0.01},
		{"ar_verified", 0.05},
		{"ifc", 0.5},
		{"pdf", 2.0},
		{"unknown", 5.0},
	}

	for _, tt := range tests {
		t.Run(tt.source, func(t *testing.T) {
			accuracy := spatial.EstimateAccuracy(tt.source)
			assert.Equal(t, tt.expected, accuracy)
		})
	}
}

func TestTransform(t *testing.T) {
	t.Run("Apply transform", func(t *testing.T) {
		transform := spatial.Transform{
			Translation: spatial.NewPoint3D(10, 20, 30),
			Rotation:    [3]float64{0, 0, 0}, // No rotation for simplicity
			Scale:       2.0,
		}

		point := spatial.NewPoint3D(1, 2, 3)
		result := transform.Apply(point)

		// Scale first, then translate
		assert.Equal(t, 12.0, result.X) // 1*2 + 10
		assert.Equal(t, 24.0, result.Y) // 2*2 + 20
		assert.Equal(t, 36.0, result.Z) // 3*2 + 30
	})
}

func TestMovementThresholds(t *testing.T) {
	t.Run("Default thresholds", func(t *testing.T) {
		thresholds := spatial.DefaultMovementThresholds()

		assert.Equal(t, 1.0, thresholds.GridUnitThreshold)
		assert.Equal(t, 0.5, thresholds.RoomChangeThreshold)
		assert.Equal(t, 0.1, thresholds.FloorChangeMargin)
		assert.Equal(t, 5.0, thresholds.RotationThreshold)
	})

	t.Run("Custom thresholds", func(t *testing.T) {
		translator := spatial.NewCoordinateTranslator("TEST")
		customThresholds := spatial.MovementThresholds{
			GridUnitThreshold:   2.0,
			RoomChangeThreshold: 1.0,
			FloorChangeMargin:   0.2,
			RotationThreshold:   10.0,
		}
		translator.SetThresholds(customThresholds)

		// Test that custom thresholds are applied
		oldPos := spatial.NewPoint3D(0, 0, 0)
		newPos := spatial.NewPoint3D(0.7, 0, 0) // Less than new threshold

		// With default threshold (0.5), this would be significant
		// With custom threshold (1.0), this is not significant
		assert.False(t, translator.IsSignificantMovement(oldPos, newPos))
	})
}

// Benchmark tests
func BenchmarkCoordinateTranslation(b *testing.B) {
	translator := spatial.NewCoordinateTranslator("BENCH-001")
	translator.SetGridScale(0.5)
	translator.SetFloorHeight(3.0)

	b.Run("GridToWorld", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			_ = translator.GridToWorld(10, 20, 3)
		}
	})

	b.Run("WorldToGrid", func(b *testing.B) {
		world := spatial.NewPoint3D(5.0, 10.0, 9.0)
		for i := 0; i < b.N; i++ {
			_, _, _ = translator.WorldToGrid(world)
		}
	})

	b.Run("IsSignificantMovement", func(b *testing.B) {
		oldPos := spatial.NewPoint3D(0, 0, 0)
		newPos := spatial.NewPoint3D(1, 1, 0)
		for i := 0; i < b.N; i++ {
			_ = translator.IsSignificantMovement(oldPos, newPos)
		}
	})
}

func BenchmarkPoint3DOperations(b *testing.B) {
	p1 := spatial.NewPoint3D(1, 2, 3)
	p2 := spatial.NewPoint3D(4, 5, 6)

	b.Run("DistanceTo", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			_ = p1.DistanceTo(p2)
		}
	})

	b.Run("Add", func(b *testing.B) {
		for i := 0; i < b.N; i++ {
			_ = p1.Add(p2)
		}
	})
}
