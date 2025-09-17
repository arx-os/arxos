package lidar

import (
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/spatial"
)

// PointCloud represents a 3D point cloud
type PointCloud struct {
	Points      []Point            `json:"points"`
	Colors      []Color            `json:"colors,omitempty"`      // Optional RGB colors
	Intensities []float32          `json:"intensities,omitempty"` // Optional LiDAR intensities
	Normals     []Normal           `json:"normals,omitempty"`     // Optional surface normals
	Metadata    PointCloudMetadata `json:"metadata"`
}

// Point represents a single 3D point
type Point struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// Color represents RGB color values
type Color struct {
	R uint8 `json:"r"`
	G uint8 `json:"g"`
	B uint8 `json:"b"`
}

// Normal represents a surface normal vector
type Normal struct {
	NX float32 `json:"nx"`
	NY float32 `json:"ny"`
	NZ float32 `json:"nz"`
}

// PointCloudMetadata contains metadata about the point cloud
type PointCloudMetadata struct {
	ScanID           string                 `json:"scan_id"`
	BuildingID       string                 `json:"building_id"`
	ScanDate         time.Time              `json:"scan_date"`
	Scanner          string                 `json:"scanner"`
	PointCount       int                    `json:"point_count"`
	Bounds           spatial.BoundingBox    `json:"bounds"`
	Resolution       float64                `json:"resolution"` // Average point spacing
	CoordinateSystem string                 `json:"coordinate_system"`
	Properties       map[string]interface{} `json:"properties,omitempty"`
}

// ProcessedCloud represents a point cloud after preprocessing
type ProcessedCloud struct {
	*PointCloud
	Filtered        bool    `json:"filtered"`
	Downsampled     bool    `json:"downsampled"`
	VoxelSize       float64 `json:"voxel_size,omitempty"`
	OutliersRemoved int     `json:"outliers_removed"`
}

// AlignedCloud represents a point cloud aligned to building coordinates
type AlignedCloud struct {
	*ProcessedCloud
	Transform      spatial.Transform `json:"transform"`
	GroundPlane    *Plane            `json:"ground_plane,omitempty"`
	AlignmentError float64           `json:"alignment_error"`
	Confidence     float64           `json:"confidence"`
}

// Plane represents a 3D plane (for ground detection, walls, etc.)
type Plane struct {
	A           float64 `json:"a"` // Ax + By + Cz + D = 0
	B           float64 `json:"b"`
	C           float64 `json:"c"`
	D           float64 `json:"d"`
	InlierCount int     `json:"inlier_count"`
	Error       float64 `json:"error"`
}

// PointCluster represents a cluster of points (potential object)
type PointCluster struct {
	ID          string              `json:"id"`
	Points      []Point             `json:"points"`
	Centroid    spatial.Point3D     `json:"centroid"`
	BoundingBox spatial.BoundingBox `json:"bounding_box"`
	PointCount  int                 `json:"point_count"`
	Label       string              `json:"label,omitempty"`
	Confidence  float64             `json:"confidence"`
}

// DetectedObject represents an object detected in the point cloud
type DetectedObject struct {
	ID            string              `json:"id"`
	Cluster       *PointCluster       `json:"cluster"`
	ObjectClass   string              `json:"object_class"`
	Confidence    float64             `json:"confidence"`
	BoundingBox   spatial.BoundingBox `json:"bounding_box"`
	Centroid      spatial.Point3D     `json:"centroid"`
	Features      ObjectFeatures      `json:"features"`
	PossibleTypes []string            `json:"possible_types,omitempty"`
}

// ObjectFeatures represents extracted features for object classification
type ObjectFeatures struct {
	Volume      float64            `json:"volume"`
	SurfaceArea float64            `json:"surface_area"`
	Dimensions  Dimensions         `json:"dimensions"`
	Shape       string             `json:"shape,omitempty"`
	Color       *Color             `json:"color,omitempty"`
	Planarity   float64            `json:"planarity"`
	Linearity   float64            `json:"linearity"`
	Sphericity  float64            `json:"sphericity"`
	Properties  map[string]float64 `json:"properties,omitempty"`
}

// Dimensions represents object dimensions
type Dimensions struct {
	Length float64 `json:"length"`
	Width  float64 `json:"width"`
	Height float64 `json:"height"`
}

// EquipmentMatch represents a potential match between detected object and equipment
type EquipmentMatch struct {
	DetectedObject *DetectedObject         `json:"detected_object"`
	EquipmentID    string                  `json:"equipment_id"`
	EquipmentType  string                  `json:"equipment_type"`
	MatchScore     float64                 `json:"match_score"`
	ShapeScore     float64                 `json:"shape_score"`
	SizeScore      float64                 `json:"size_score"`
	LocationScore  float64                 `json:"location_score"`
	Confidence     spatial.ConfidenceLevel `json:"confidence"`
}

// ProcessingParams contains parameters for point cloud processing
type ProcessingParams struct {
	// Noise filtering
	NoiseFilterEnabled bool    `json:"noise_filter_enabled"`
	StatisticalK       int     `json:"statistical_k"` // Neighbors for statistical filter
	StdDevMultiplier   float64 `json:"std_dev_multiplier"`

	// Downsampling
	DownsampleEnabled bool    `json:"downsample_enabled"`
	VoxelSize         float64 `json:"voxel_size"`    // Voxel size for downsampling
	TargetPoints      int     `json:"target_points"` // Target number of points

	// Segmentation
	MinClusterSize   int     `json:"min_cluster_size"`
	ClusterTolerance float64 `json:"cluster_tolerance"`
	MaxClusterSize   int     `json:"max_cluster_size"`

	// Object detection
	MinObjectVolume float64 `json:"min_object_volume"`
	MaxObjectVolume float64 `json:"max_object_volume"`
}

// DefaultProcessingParams returns default processing parameters
func DefaultProcessingParams() ProcessingParams {
	return ProcessingParams{
		NoiseFilterEnabled: true,
		StatisticalK:       50,
		StdDevMultiplier:   1.0,
		DownsampleEnabled:  true,
		VoxelSize:          0.01, // 1cm
		TargetPoints:       1000000,
		MinClusterSize:     100,
		ClusterTolerance:   0.05, // 5cm
		MaxClusterSize:     100000,
		MinObjectVolume:    0.001, // 1 liter
		MaxObjectVolume:    100.0, // 100 cubic meters
	}
}

// MergeResult represents the result of merging a partial scan
type MergeResult struct {
	MatchedEquipment int             `json:"matched_equipment"`
	UnknownObjects   int             `json:"unknown_objects"`
	CoverageIncrease float64         `json:"coverage_increase"`
	UpdatedPositions int             `json:"updated_positions"`
	Conflicts        []MergeConflict `json:"conflicts,omitempty"`
	ProcessingTime   time.Duration   `json:"processing_time"`
}

// MergeConflict represents a conflict during merge
type MergeConflict struct {
	ObjectID     string          `json:"object_id"`
	ConflictType string          `json:"conflict_type"`
	OldPosition  spatial.Point3D `json:"old_position"`
	NewPosition  spatial.Point3D `json:"new_position"`
	Distance     float64         `json:"distance"`
	Resolution   string          `json:"resolution"`
}

// MatchThresholds contains thresholds for equipment matching
type MatchThresholds struct {
	ShapeSimilarity float64 `json:"shape_similarity"` // 0-1
	SizeDeviation   float64 `json:"size_deviation"`   // Percentage
	LocationRadius  float64 `json:"location_radius"`  // Meters
	MinConfidence   float64 `json:"min_confidence"`   // 0-1
}

// DefaultMatchThresholds returns default matching thresholds
func DefaultMatchThresholds() MatchThresholds {
	return MatchThresholds{
		ShapeSimilarity: 0.8,
		SizeDeviation:   0.15, // 15% size variation
		LocationRadius:  1.0,  // 1 meter
		MinConfidence:   0.7,
	}
}

// Statistics represents point cloud statistics
type Statistics struct {
	PointCount        int     `json:"point_count"`
	MinBounds         Point   `json:"min_bounds"`
	MaxBounds         Point   `json:"max_bounds"`
	CenterOfMass      Point   `json:"center_of_mass"`
	AverageSpacing    float64 `json:"average_spacing"`
	StandardDeviation float64 `json:"standard_deviation"`
	Density           float64 `json:"density"` // points per cubic meter
}

// CalculateStatistics computes statistics for a point cloud
func (pc *PointCloud) CalculateStatistics() Statistics {
	if len(pc.Points) == 0 {
		return Statistics{}
	}

	stats := Statistics{
		PointCount: len(pc.Points),
		MinBounds:  pc.Points[0],
		MaxBounds:  pc.Points[0],
	}

	// Calculate bounds and center of mass
	var sumX, sumY, sumZ float64
	for _, p := range pc.Points {
		sumX += p.X
		sumY += p.Y
		sumZ += p.Z

		// Update bounds
		if p.X < stats.MinBounds.X {
			stats.MinBounds.X = p.X
		}
		if p.Y < stats.MinBounds.Y {
			stats.MinBounds.Y = p.Y
		}
		if p.Z < stats.MinBounds.Z {
			stats.MinBounds.Z = p.Z
		}
		if p.X > stats.MaxBounds.X {
			stats.MaxBounds.X = p.X
		}
		if p.Y > stats.MaxBounds.Y {
			stats.MaxBounds.Y = p.Y
		}
		if p.Z > stats.MaxBounds.Z {
			stats.MaxBounds.Z = p.Z
		}
	}

	count := float64(len(pc.Points))
	stats.CenterOfMass = Point{
		X: sumX / count,
		Y: sumY / count,
		Z: sumZ / count,
	}

	// Calculate volume for density
	volume := (stats.MaxBounds.X - stats.MinBounds.X) *
		(stats.MaxBounds.Y - stats.MinBounds.Y) *
		(stats.MaxBounds.Z - stats.MinBounds.Z)

	if volume > 0 {
		stats.Density = count / volume
	}

	return stats
}

// ToSpatialPoint3D converts a Point to spatial.Point3D
func (p Point) ToSpatialPoint3D() spatial.Point3D {
	return spatial.Point3D{
		X: p.X,
		Y: p.Y,
		Z: p.Z,
	}
}

// FromSpatialPoint3D creates a Point from spatial.Point3D
func FromSpatialPoint3D(sp spatial.Point3D) Point {
	return Point{
		X: sp.X,
		Y: sp.Y,
		Z: sp.Z,
	}
}

// GetBoundingBox returns the bounding box of a point cloud
func (pc *PointCloud) GetBoundingBox() spatial.BoundingBox {
	if len(pc.Points) == 0 {
		return spatial.BoundingBox{}
	}

	min := pc.Points[0].ToSpatialPoint3D()
	max := pc.Points[0].ToSpatialPoint3D()

	for _, p := range pc.Points {
		sp := p.ToSpatialPoint3D()
		if sp.X < min.X {
			min.X = sp.X
		}
		if sp.Y < min.Y {
			min.Y = sp.Y
		}
		if sp.Z < min.Z {
			min.Z = sp.Z
		}
		if sp.X > max.X {
			max.X = sp.X
		}
		if sp.Y > max.Y {
			max.Y = sp.Y
		}
		if sp.Z > max.Z {
			max.Z = sp.Z
		}
	}

	return spatial.NewBoundingBox(min, max)
}

// Validate checks if the point cloud is valid
func (pc *PointCloud) Validate() error {
	if len(pc.Points) == 0 {
		return fmt.Errorf("point cloud has no points")
	}

	if len(pc.Colors) > 0 && len(pc.Colors) != len(pc.Points) {
		return fmt.Errorf("color count (%d) doesn't match point count (%d)",
			len(pc.Colors), len(pc.Points))
	}

	if len(pc.Intensities) > 0 && len(pc.Intensities) != len(pc.Points) {
		return fmt.Errorf("intensity count (%d) doesn't match point count (%d)",
			len(pc.Intensities), len(pc.Points))
	}

	if len(pc.Normals) > 0 && len(pc.Normals) != len(pc.Points) {
		return fmt.Errorf("normal count (%d) doesn't match point count (%d)",
			len(pc.Normals), len(pc.Points))
	}

	return nil
}
