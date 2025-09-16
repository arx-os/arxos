package lidar_test

import (
	"testing"

	"github.com/joelpate/arxos/internal/lidar"
	"github.com/joelpate/arxos/internal/spatial"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// Helper function to create test point cloud
func createTestPointCloud(numPoints int) *lidar.PointCloud {
	points := make([]lidar.Point, numPoints)
	for i := 0; i < numPoints; i++ {
		points[i] = lidar.Point{
			X: float64(i % 10),
			Y: float64(i / 10),
			Z: float64(i%3) * 0.1,
		}
	}

	return &lidar.PointCloud{
		Points: points,
		Metadata: lidar.PointCloudMetadata{
			ScanID:     "test_scan",
			BuildingID: "TEST-001",
			PointCount: numPoints,
		},
	}
}

func TestProcessor_ProcessPointCloud(t *testing.T) {
	t.Run("Process valid point cloud", func(t *testing.T) {
		processor := lidar.NewDefaultProcessor()
		pc := createTestPointCloud(1000)

		processed, err := processor.ProcessPointCloud(pc)
		require.NoError(t, err)
		assert.NotNil(t, processed)
		assert.True(t, processed.Filtered)
		assert.True(t, processed.Downsampled)
	})

	t.Run("Handle empty point cloud", func(t *testing.T) {
		processor := lidar.NewDefaultProcessor()
		pc := &lidar.PointCloud{
			Points: []lidar.Point{},
			Metadata: lidar.PointCloudMetadata{
				ScanID: "empty_scan",
			},
		}

		_, err := processor.ProcessPointCloud(pc)
		assert.Error(t, err)
	})

	t.Run("Noise filtering", func(t *testing.T) {
		params := lidar.DefaultProcessingParams()
		params.NoiseFilterEnabled = true
		processor := lidar.NewProcessor(params)

		// Create point cloud with outliers
		pc := createTestPointCloud(100)
		// Add outlier
		pc.Points = append(pc.Points, lidar.Point{X: 100, Y: 100, Z: 100})
		initialCount := len(pc.Points)

		processed, err := processor.ProcessPointCloud(pc)
		require.NoError(t, err)

		// Should have removed outliers
		assert.Less(t, len(processed.Points), initialCount)
		assert.Greater(t, processed.OutliersRemoved, 0)
	})

	t.Run("Downsampling", func(t *testing.T) {
		params := lidar.DefaultProcessingParams()
		params.DownsampleEnabled = true
		params.VoxelSize = 0.5
		processor := lidar.NewProcessor(params)

		pc := createTestPointCloud(10000)
		initialCount := len(pc.Points)

		processed, err := processor.ProcessPointCloud(pc)
		require.NoError(t, err)

		// Should have fewer points after downsampling
		assert.Less(t, len(processed.Points), initialCount)
		assert.Equal(t, 0.5, processed.VoxelSize)
	})
}

func TestProcessor_AlignToBuilding(t *testing.T) {
	t.Run("Align processed cloud", func(t *testing.T) {
		processor := lidar.NewDefaultProcessor()
		pc := createTestPointCloud(1000)
		processed, err := processor.ProcessPointCloud(pc)
		require.NoError(t, err)

		aligned, err := processor.AlignToBuilding(processed, "TEST-001")
		require.NoError(t, err)
		assert.NotNil(t, aligned)
		assert.NotNil(t, aligned.Transform)
		assert.Greater(t, aligned.Confidence, 0.0)
	})

	t.Run("Ground plane detection", func(t *testing.T) {
		processor := lidar.NewDefaultProcessor()

		// Create point cloud with clear ground plane
		points := make([]lidar.Point, 0)
		// Add ground points at Z=0
		for x := 0.0; x < 10.0; x++ {
			for y := 0.0; y < 10.0; y++ {
				points = append(points, lidar.Point{X: x, Y: y, Z: 0.0})
			}
		}
		// Add some elevated points
		for x := 2.0; x < 4.0; x++ {
			for y := 2.0; y < 4.0; y++ {
				points = append(points, lidar.Point{X: x, Y: y, Z: 2.0})
			}
		}

		pc := &lidar.PointCloud{
			Points: points,
			Metadata: lidar.PointCloudMetadata{
				ScanID:     "ground_test",
				PointCount: len(points),
			},
		}

		processed := &lidar.ProcessedCloud{PointCloud: pc}
		aligned, err := processor.AlignToBuilding(processed, "TEST-001")
		require.NoError(t, err)

		// Should detect horizontal ground plane
		assert.NotNil(t, aligned.GroundPlane)
		assert.Greater(t, aligned.GroundPlane.InlierCount, 50)
	})
}

func TestSegmenter_SegmentObjects(t *testing.T) {
	t.Run("Segment objects from point cloud", func(t *testing.T) {
		params := lidar.DefaultProcessingParams()
		params.MinClusterSize = 10
		params.ClusterTolerance = 1.0
		segmenter := lidar.NewSegmenter(params)

		// Create point cloud with distinct clusters
		points := make([]lidar.Point, 0)

		// Cluster 1 at origin
		for i := 0; i < 20; i++ {
			points = append(points, lidar.Point{
				X: float64(i%5) * 0.1,
				Y: float64(i/5) * 0.1,
				Z: 1.0,
			})
		}

		// Cluster 2 at offset
		for i := 0; i < 20; i++ {
			points = append(points, lidar.Point{
				X: 5.0 + float64(i%5)*0.1,
				Y: 5.0 + float64(i/5)*0.1,
				Z: 1.0,
			})
		}

		pc := &lidar.PointCloud{
			Points:   points,
			Metadata: lidar.PointCloudMetadata{PointCount: len(points)},
		}

		clusters, err := segmenter.SegmentObjects(pc)
		require.NoError(t, err)
		assert.GreaterOrEqual(t, len(clusters), 2)
	})

	t.Run("Filter by size constraints", func(t *testing.T) {
		params := lidar.DefaultProcessingParams()
		params.MinClusterSize = 5
		params.MaxClusterSize = 15
		segmenter := lidar.NewSegmenter(params)

		// Create clusters of different sizes
		points := make([]lidar.Point, 0)

		// Small cluster (3 points - should be filtered)
		for i := 0; i < 3; i++ {
			points = append(points, lidar.Point{X: float64(i), Y: 0, Z: 1})
		}

		// Medium cluster (10 points - should pass)
		for i := 0; i < 10; i++ {
			points = append(points, lidar.Point{X: float64(i), Y: 5, Z: 1})
		}

		// Large cluster (20 points - should be filtered)
		for i := 0; i < 20; i++ {
			points = append(points, lidar.Point{X: float64(i), Y: 10, Z: 1})
		}

		pc := &lidar.PointCloud{
			Points:   points,
			Metadata: lidar.PointCloudMetadata{PointCount: len(points)},
		}

		clusters, err := segmenter.SegmentObjects(pc)
		require.NoError(t, err)
		// Should only have the medium cluster
		assert.Equal(t, 1, len(clusters))
	})
}

func TestSegmenter_ClassifyObject(t *testing.T) {
	segmenter := lidar.NewSegmenter(lidar.DefaultProcessingParams())

	t.Run("Classify pipe-like object", func(t *testing.T) {
		// Create elongated cluster
		points := make([]lidar.Point, 0)
		for i := 0; i < 100; i++ {
			points = append(points, lidar.Point{
				X: float64(i) * 0.1, // 10m long
				Y: 0.0,
				Z: 1.0,
			})
		}

		cluster := &lidar.PointCluster{
			ID:         "test_cluster",
			Points:     points,
			PointCount: len(points),
			Centroid:   spatial.Point3D{X: 5, Y: 0, Z: 1},
			BoundingBox: spatial.NewBoundingBox(
				spatial.Point3D{X: 0, Y: -0.1, Z: 0.9},
				spatial.Point3D{X: 10, Y: 0.1, Z: 1.1},
			),
		}

		object := segmenter.ClassifyObject(cluster)
		assert.NotNil(t, object)
		assert.Equal(t, "pipe", object.ObjectClass)
		assert.Greater(t, object.Features.Linearity, 0.5)
	})

	t.Run("Classify wall-like object", func(t *testing.T) {
		// Create planar cluster
		points := make([]lidar.Point, 0)
		for x := 0.0; x < 5.0; x += 0.1 {
			for z := 0.0; z < 3.0; z += 0.1 {
				points = append(points, lidar.Point{
					X: x,
					Y: 0.0,
					Z: z,
				})
			}
		}

		cluster := &lidar.PointCluster{
			ID:         "wall_cluster",
			Points:     points,
			PointCount: len(points),
			Centroid:   spatial.Point3D{X: 2.5, Y: 0, Z: 1.5},
			BoundingBox: spatial.NewBoundingBox(
				spatial.Point3D{X: 0, Y: -0.1, Z: 0},
				spatial.Point3D{X: 5, Y: 0.1, Z: 3},
			),
		}

		object := segmenter.ClassifyObject(cluster)
		assert.NotNil(t, object)
		assert.Contains(t, []string{"wall_segment", "unknown"}, object.ObjectClass)
	})
}

func TestEquipmentMatcher_MatchDetectedObjects(t *testing.T) {
	matcher := lidar.NewDefaultMatcher()

	t.Run("Match objects to equipment", func(t *testing.T) {
		// Create detected objects
		detected := []*lidar.DetectedObject{
			{
				ID:          "obj_1",
				ObjectClass: "hvac_unit",
				Centroid:    spatial.Point3D{X: 10, Y: 10, Z: 1},
				Confidence:  0.8,
				Features: lidar.ObjectFeatures{
					Dimensions: lidar.Dimensions{
						Length: 2.0,
						Width:  1.5,
						Height: 1.0,
					},
					Volume: 3.0,
					Shape:  "irregular",
				},
				BoundingBox: spatial.NewBoundingBox(
					spatial.Point3D{X: 9, Y: 9.25, Z: 0.5},
					spatial.Point3D{X: 11, Y: 10.75, Z: 1.5},
				),
			},
		}

		// Create known equipment
		known := []lidar.KnownEquipment{
			{
				ID:       "HVAC-001",
				Type:     "hvac_unit",
				Position: spatial.Point3D{X: 10.1, Y: 10.1, Z: 1.0},
				Dimensions: lidar.Dimensions{
					Length: 2.1,
					Width:  1.4,
					Height: 0.9,
				},
			},
		}

		matches, err := matcher.MatchDetectedObjects(detected, known)
		require.NoError(t, err)
		assert.Len(t, matches, 1)
		assert.Equal(t, "HVAC-001", matches[0].EquipmentID)
		assert.Greater(t, matches[0].MatchScore, 0.7)
	})

	t.Run("No match for distant objects", func(t *testing.T) {
		detected := []*lidar.DetectedObject{
			{
				ID:          "obj_far",
				ObjectClass: "hvac_unit",
				Centroid:    spatial.Point3D{X: 100, Y: 100, Z: 1},
				Features: lidar.ObjectFeatures{
					Dimensions: lidar.Dimensions{Length: 2, Width: 1.5, Height: 1},
				},
			},
		}

		known := []lidar.KnownEquipment{
			{
				ID:         "HVAC-002",
				Type:       "hvac_unit",
				Position:   spatial.Point3D{X: 10, Y: 10, Z: 1},
				Dimensions: lidar.Dimensions{Length: 2, Width: 1.5, Height: 1},
			},
		}

		matches, err := matcher.MatchDetectedObjects(detected, known)
		require.NoError(t, err)
		assert.Empty(t, matches)
	})

	t.Run("Match with size tolerance", func(t *testing.T) {
		detected := []*lidar.DetectedObject{
			{
				ID:          "obj_sized",
				ObjectClass: "pipe",
				Centroid:    spatial.Point3D{X: 5, Y: 5, Z: 2},
				Features: lidar.ObjectFeatures{
					Dimensions: lidar.Dimensions{
						Length: 10.0,
						Width:  0.28, // Slightly different from known
						Height: 0.28,
					},
					Volume:    0.784,
					Shape:     "linear",
					Linearity: 0.9,
				},
			},
		}

		known := []lidar.KnownEquipment{
			{
				ID:       "PIPE-001",
				Type:     "pipe",
				Position: spatial.Point3D{X: 5, Y: 5, Z: 2},
				Dimensions: lidar.Dimensions{
					Length: 10.0,
					Width:  0.3,
					Height: 0.3,
				},
			},
		}

		matches, err := matcher.MatchDetectedObjects(detected, known)
		require.NoError(t, err)
		assert.Len(t, matches, 1)
		assert.Equal(t, "PIPE-001", matches[0].EquipmentID)
	})
}

func TestEquipmentMatcher_GenerateReport(t *testing.T) {
	matcher := lidar.NewDefaultMatcher()

	detected := []*lidar.DetectedObject{
		{ID: "obj_1", ObjectClass: "hvac_unit"},
		{ID: "obj_2", ObjectClass: "pipe"},
		{ID: "obj_3", ObjectClass: "unknown"},
	}

	known := []lidar.KnownEquipment{
		{ID: "HVAC-001", Type: "hvac_unit"},
		{ID: "PIPE-001", Type: "pipe"},
		{ID: "PUMP-001", Type: "pump"},
	}

	matches := []*lidar.EquipmentMatch{
		{
			DetectedObject: detected[0],
			EquipmentID:    "HVAC-001",
			MatchScore:     0.85,
			Confidence:     spatial.ConfidenceHigh,
		},
		{
			DetectedObject: detected[1],
			EquipmentID:    "PIPE-001",
			MatchScore:     0.75,
			Confidence:     spatial.ConfidenceMedium,
		},
	}

	report := matcher.GenerateMatchReport(detected, known, matches)

	assert.Equal(t, 3, report.TotalDetected)
	assert.Equal(t, 3, report.TotalKnownEquipment)
	assert.Equal(t, 2, report.SuccessfulMatches)
	assert.Equal(t, 1, report.UnmatchedObjects)
	assert.Equal(t, 1, report.MissingEquipment)
	assert.InDelta(t, 0.667, report.MatchRate, 0.01)

	// Check confidence distribution
	assert.Equal(t, 1, report.ConfidenceDistribution[spatial.ConfidenceHigh])
	assert.Equal(t, 1, report.ConfidenceDistribution[spatial.ConfidenceMedium])

	// Check lists
	assert.Len(t, report.UnmatchedObjectsList, 1)
	assert.Equal(t, "obj_3", report.UnmatchedObjectsList[0].ID)
	assert.Len(t, report.MissingEquipmentList, 1)
	assert.Equal(t, "PUMP-001", report.MissingEquipmentList[0].ID)
}

// Benchmark tests
func BenchmarkProcessor_ProcessPointCloud(b *testing.B) {
	processor := lidar.NewDefaultProcessor()
	pc := createTestPointCloud(10000)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = processor.ProcessPointCloud(pc)
	}
}

func BenchmarkSegmenter_SegmentObjects(b *testing.B) {
	segmenter := lidar.NewSegmenter(lidar.DefaultProcessingParams())
	pc := createTestPointCloud(5000)

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = segmenter.SegmentObjects(pc)
	}
}

func BenchmarkMatcher_MatchObjects(b *testing.B) {
	matcher := lidar.NewDefaultMatcher()

	// Create test data
	detected := make([]*lidar.DetectedObject, 50)
	for i := range detected {
		detected[i] = &lidar.DetectedObject{
			ID:       "obj_" + string(rune(i)),
			Centroid: spatial.Point3D{X: float64(i), Y: float64(i), Z: 1},
			Features: lidar.ObjectFeatures{
				Dimensions: lidar.Dimensions{Length: 1, Width: 1, Height: 1},
			},
		}
	}

	known := make([]lidar.KnownEquipment, 50)
	for i := range known {
		known[i] = lidar.KnownEquipment{
			ID:         "EQ-" + string(rune(i)),
			Position:   spatial.Point3D{X: float64(i), Y: float64(i), Z: 1},
			Dimensions: lidar.Dimensions{Length: 1, Width: 1, Height: 1},
		}
	}

	b.ResetTimer()
	for i := 0; i < b.N; i++ {
		_, _ = matcher.MatchDetectedObjects(detected, known)
	}
}
