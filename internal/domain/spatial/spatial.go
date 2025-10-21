package spatial

import (
	"context"
	"time"
)

// SpatialPosition represents a 3D spatial position
type SpatialPosition struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// SpatialRotation represents 3D rotation (quaternion)
type SpatialRotation struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
	W float64 `json:"w"`
}

// SpatialScale represents 3D scale
type SpatialScale struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// MobileSpatialAnchor represents an AR spatial anchor for mobile API responses
type MobileSpatialAnchor struct {
	ID          string          `json:"id"`
	BuildingID  string          `json:"building_id"`
	EquipmentID string          `json:"equipment_id,omitempty"`
	Position    SpatialPosition `json:"position"`
	Rotation    SpatialRotation `json:"rotation,omitempty"`
	Scale       SpatialScale    `json:"scale,omitempty"`
	Confidence  float64         `json:"confidence"`
	AnchorType  string          `json:"anchor_type"`
	Metadata    map[string]any  `json:"metadata,omitempty"`
	CreatedAt   time.Time       `json:"created_at"`
	UpdatedAt   time.Time       `json:"updated_at"`
	CreatedBy   string          `json:"created_by,omitempty"`
}

// CreateSpatialAnchorRequest represents a request to create a spatial anchor
type CreateSpatialAnchorRequest struct {
	BuildingID  string           `json:"building_id" validate:"required"`
	EquipmentID string           `json:"equipment_id,omitempty"`
	Position    SpatialPosition  `json:"position" validate:"required"`
	Rotation    *SpatialRotation `json:"rotation,omitempty"`
	Scale       *SpatialScale    `json:"scale,omitempty"`
	Confidence  float64          `json:"confidence"`
	AnchorType  string           `json:"anchor_type"`
	Metadata    map[string]any   `json:"metadata,omitempty"`
	CreatedBy   string           `json:"created_by,omitempty"`
}

// SpatialAnchorFilter represents filters for spatial anchor queries
type SpatialAnchorFilter struct {
	AnchorType    *string  `json:"anchor_type,omitempty"`
	HasEquipment  *bool    `json:"has_equipment,omitempty"`
	MinConfidence *float64 `json:"min_confidence,omitempty"`
	Limit         *int     `json:"limit,omitempty"`
	Offset        int      `json:"offset"`
}

// NearbyEquipmentRequest represents a request to find nearby equipment
type NearbyEquipmentRequest struct {
	BuildingID string  `json:"building_id" validate:"required"`
	CenterX    float64 `json:"center_x" validate:"required"`
	CenterY    float64 `json:"center_y" validate:"required"`
	CenterZ    float64 `json:"center_z"`
	Radius     float64 `json:"radius"`
	Limit      *int    `json:"limit,omitempty"`
}

// NearbyEquipmentResult represents a nearby equipment result
type NearbyEquipmentResult struct {
	EquipmentID     string  `json:"equipment_id"`
	EquipmentName   string  `json:"equipment_name"`
	EquipmentType   string  `json:"equipment_type"`
	EquipmentStatus string  `json:"equipment_status"`
	Distance        float64 `json:"distance_meters"`
	Bearing         float64 `json:"bearing_degrees"`
}

// PointCloudUploadRequest represents a request to upload point cloud data
type PointCloudUploadRequest struct {
	BuildingID string           `json:"building_id" validate:"required"`
	SessionID  string           `json:"session_id" validate:"required"`
	Points     []PointCloudData `json:"points" validate:"required"`
	UserID     string           `json:"user_id"`
}

// PointCloudData represents a point in point cloud data
type PointCloudData struct {
	X       float64 `json:"x"`
	Y       float64 `json:"y"`
	Z       float64 `json:"z"`
	Color   []int   `json:"color,omitempty"` // RGB values
	Density float64 `json:"density,omitempty"`
}

// BuildingSpatialSummary represents spatial summary for a building
type BuildingSpatialSummary struct {
	BuildingID          string    `json:"building_id"`
	TotalEquipment      int       `json:"total_equipment"`
	PositionedEquipment int       `json:"positioned_equipment"`
	PositioningCoverage float64   `json:"positioning_coverage"`
	SpatialCoverage     float64   `json:"spatial_coverage"`
	LastPositionUpdate  time.Time `json:"last_position_update,omitempty"`
}

// SpatialRepository defines the interface for spatial operations
type SpatialRepository interface {
	// Create schema
	CreateSpatialSchema(ctx context.Context) error

	// Spatial Anchor operations
	CreateSpatialAnchor(ctx context.Context, req *CreateSpatialAnchorRequest) (*MobileSpatialAnchor, error)
	GetSpatialAnchorsByBuilding(ctx context.Context, buildingID string, filter *SpatialAnchorFilter) ([]*MobileSpatialAnchor, error)
	UpdateSpatialAnchor(ctx context.Context, anchorID string, req *UpdateSpatialAnchorRequest) (*MobileSpatialAnchor, error)
	DeleteSpatialAnchor(ctx context.Context, anchorID string) error

	// Equipment spatial operations
	FindNearbyEquipment(ctx context.Context, req *NearbyEquipmentRequest) ([]*NearbyEquipmentResult, error)
	UpdateEquipmentPosition(ctx context.Context, equipmentID string, position *SpatialPosition) error

	// Mapping operations
	UploadPointCloud(ctx context.Context, req *PointCloudUploadRequest) error
	GetBuildingSpatialSummary(ctx context.Context, buildingID string) (*BuildingSpatialSummary, error)

	// Analytics
	GetSpatialAnalytics(ctx context.Context, buildingID string) (*SpatialAnalytics, error)
}

// UpdateSpatialAnchorRequest represents a request to update a spatial anchor
type UpdateSpatialAnchorRequest struct {
	Position   *SpatialPosition `json:"position,omitempty"`
	Rotation   *SpatialRotation `json:"rotation,omitempty"`
	Scale      *SpatialScale    `json:"scale,omitempty"`
	Confidence *float64         `json:"confidence,omitempty"`
	Metadata   map[string]any   `json:"metadata,omitempty"`
}

// SpatialAnalytics represents spatial analytics data
type SpatialAnalytics struct {
	BuildingID            string                `json:"building_id"`
	CoverageMetrics       CoverageMetrics       `json:"coverage_metrics"`
	AnchorDensityMetrics  AnchorDensityMetrics  `json:"anchor_density_metrics"`
	EquipmentDistribution EquipmentDistribution `json:"equipment_distribution"`
	ScanHistory           []ScanHistoryEntry    `json:"scan_history"`
}

// CoverageMetrics represents coverage analysis
type CoverageMetrics struct {
	TotalArea          float64   `json:"total_area"`
	ScannedArea        float64   `json:"scanned_area"`
	CoveragePercentage float64   `json:"coverage_percentage"`
	FloorLevels        int       `json:"floor_levels"`
	LastScanDate       time.Time `json:"last_scan_date"`
}

// AnchorDensityMetrics represents anchor density analysis
type AnchorDensityMetrics struct {
	TotalAnchors          int     `json:"total_anchors"`
	AnchorsPerSquareMeter float64 `json:"anchors_per_square_meter"`
	EquipmentAnchors      int     `json:"equipment_anchors"`
	ReferenceAnchors      int     `json:"reference_anchors"`
}

// EquipmentDistribution represents equipment spatial distribution
type EquipmentDistribution struct {
	TotalEquipment      int            `json:"total_equipment"`
	PositionedEquipment int            `json:"positioned_equipment"`
	PositioningAccuracy float64        `json:"positioning_accuracy"`
	DensityMap          map[string]int `json:"density_map"` // Floor/area density
}

// ScanHistoryEntry represents a scan history entry
type ScanHistoryEntry struct {
	ScanID        string        `json:"scan_id"`
	SessionID     string        `json:"session_id"`
	ScanMethod    string        `json:"scan_method"`
	PointsScanned int           `json:"points_scanned"`
	AreaScanned   float64       `json:"area_scanned"`
	Duration      time.Duration `json:"duration"`
	Quality       float64       `json:"quality"`
	CreatedAt     time.Time     `json:"created_at"`
	CreatedBy     string        `json:"created_by"`
}
