package database

import (
	"time"

	"github.com/arx-os/arxos/internal/spatial"
	"github.com/arx-os/arxos/pkg/models"
)

// SpatialDB defines the interface for spatial database operations
type SpatialDB interface {
	// Equipment position operations
	UpdateEquipmentPosition(equipmentID string, pos spatial.Point3D, confidence spatial.ConfidenceLevel, source string) error
	GetEquipmentPosition(equipmentID string) (*SpatialEquipment, error)
	QueryBySpatialProximity(center spatial.Point3D, radiusMeters float64) ([]*SpatialEquipment, error)
	QueryByBoundingBox(bbox spatial.BoundingBox) ([]*SpatialEquipment, error)
	GetEquipmentInRoom(buildingID string, floor int, roomBounds spatial.BoundingBox) ([]*SpatialEquipment, error)

	// Building coordinate system
	SetBuildingOrigin(buildingID string, gps spatial.GPSCoordinate, rotation float64, gridScale float64) error
	GetBuildingTransform(buildingID string) (*spatial.Transform, error)
	GetBuildingOrigin(buildingID string) (*spatial.GPSCoordinate, error)

	// Coverage operations
	AddScannedRegion(region spatial.ScannedRegion) error
	GetCoverageMap(buildingID string) (*spatial.CoverageMap, error)
	CalculateCoveragePercentage(buildingID string) (float64, error)
	GetRegionConfidence(buildingID string, point spatial.Point3D) (spatial.ConfidenceLevel, error)
	GetUnscannedAreas(buildingID string) ([]spatial.SpatialExtent, error)

	// Point cloud operations
	StorePointCloud(scanID string, points []spatial.Point3D, metadata map[string]interface{}) error
	GetPointCloud(scanID string) ([]spatial.Point3D, error)
	QueryPointsInRegion(boundary spatial.SpatialExtent) ([]spatial.Point3D, error)
	GetPointCloudMetadata(scanID string) (map[string]interface{}, error)

	// Confidence tracking
	UpdateConfidence(equipmentID string, aspect string, level spatial.ConfidenceLevel, source string) error
	GetConfidenceRecord(equipmentID string) (*ConfidenceRecord, error)
	QueryByConfidence(minConfidence spatial.ConfidenceLevel) ([]*SpatialEquipment, error)
	GetEquipmentNeedingVerification(daysSinceLastVerification int) ([]*models.Equipment, error)

	// Spatial anchor operations (for AR)
	CreateSpatialAnchor(anchor spatial.SpatialAnchor) error
	GetSpatialAnchor(anchorID string) (*spatial.SpatialAnchor, error)
	GetAnchorsNearPosition(position spatial.Point3D, radiusMeters float64) ([]*spatial.SpatialAnchor, error)
	UpdateAnchorConfidence(anchorID string, confidence float64) error

	// Utility operations
	CalculateDistance(id1, id2 string) (float64, error)
	FindNearestEquipment(position spatial.Point3D, equipmentType string) (*SpatialEquipment, error)
	GetFloorBounds(buildingID string, floor int) (*spatial.BoundingBox, error)

	// Maintenance operations
	Vacuum() error
	GetStatistics() (*SpatialDBStats, error)
}

// SpatialEquipment represents equipment with spatial data
type SpatialEquipment struct {
	*models.Equipment
	SpatialData *spatial.SpatialMetadata `json:"spatial_data,omitempty"`
}

// ConfidenceRecord tracks confidence for equipment
type ConfidenceRecord struct {
	EquipmentID string `json:"equipment_id"`

	// Position confidence
	PositionConfidence spatial.ConfidenceLevel `json:"position_confidence"`
	PositionSource     string                  `json:"position_source"`
	PositionUpdated    time.Time               `json:"position_updated"`
	PositionAccuracy   float64                 `json:"position_accuracy"`

	// Semantic confidence
	SemanticConfidence   spatial.ConfidenceLevel `json:"semantic_confidence"`
	SemanticSource       string                  `json:"semantic_source"`
	SemanticUpdated      time.Time               `json:"semantic_updated"`
	SemanticCompleteness float64                 `json:"semantic_completeness"`

	// Verification
	LastFieldVerified   *time.Time          `json:"last_field_verified,omitempty"`
	VerificationCount   int                 `json:"verification_count"`
	VerificationHistory []VerificationEvent `json:"verification_history,omitempty"`
}

// VerificationEvent represents a single verification event
type VerificationEvent struct {
	Timestamp time.Time `json:"timestamp"`
	Method    string    `json:"method"` // "ar", "lidar", "manual"
	UserID    string    `json:"user_id,omitempty"`
	Notes     string    `json:"notes,omitempty"`
}

// SpatialDBStats provides statistics about the spatial database
type SpatialDBStats struct {
	TotalEquipment       int        `json:"total_equipment"`
	EquipmentWithSpatial int        `json:"equipment_with_spatial"`
	TotalScans           int        `json:"total_scans"`
	TotalPointClouds     int        `json:"total_point_clouds"`
	TotalPoints          int64      `json:"total_points"`
	AverageCoverage      float64    `json:"average_coverage"`
	LastScanDate         *time.Time `json:"last_scan_date,omitempty"`
}

// SpatialQuery represents a spatial database query
type SpatialQuery struct {
	BuildingID         string
	Floor              *int
	BoundingBox        *spatial.BoundingBox
	Center             *spatial.Point3D
	Radius             float64
	MinConfidence      *spatial.ConfidenceLevel
	EquipmentType      string
	LastVerifiedWithin *time.Duration
	Limit              int
	Offset             int
}

// SpatialUpdate represents an update to spatial data
type SpatialUpdate struct {
	EquipmentID string
	Position    *spatial.Point3D
	Confidence  *spatial.ConfidenceLevel
	Source      string
	Timestamp   time.Time
	UserID      string
	Notes       string
}

// SpatialConflict represents a conflict in spatial data
type SpatialConflict struct {
	EquipmentID   string                  `json:"equipment_id"`
	OldPosition   spatial.Point3D         `json:"old_position"`
	NewPosition   spatial.Point3D         `json:"new_position"`
	OldConfidence spatial.ConfidenceLevel `json:"old_confidence"`
	NewConfidence spatial.ConfidenceLevel `json:"new_confidence"`
	Distance      float64                 `json:"distance"`
	Resolution    string                  `json:"resolution"`
}
