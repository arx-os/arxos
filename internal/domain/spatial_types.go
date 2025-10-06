package domain

import (
	"fmt"
	"time"

	"github.com/arx-os/arxos/pkg/models"
)

// SpatialLocation represents a generic location using the established spatial models
// This provides a bridge to the existing Point3D spatial system
type SpatialLocation struct {
	X float64 `json:"x" yaml:"x"`
	Y float64 `json:"y" yaml:"y"`
	Z float64 `json:"z" yaml:"z"`
}

// NewSpatialLocation creates a new SpatialLocation from Point3D
func NewSpatialLocation(point models.Point3D) SpatialLocation {
	return SpatialLocation{X: point.X, Y: point.Y, Z: point.Z}
}

// ToPoint3D converts SpatialLocation to Point3D
func (l SpatialLocation) ToPoint3D() models.Point3D {
	return models.Point3D{X: l.X, Y: l.Y, Z: l.Z}
}

// Quaternion represents a rotation in 3D space
// Follows the WXYZ convention where W is the scalar component
type Quaternion struct {
	W float64 `json:"w" yaml:"w"` // Scalar component
	X float64 `json:"x" yaml:"x"` // X vector component
	Y float64 `json:"y" yaml:"y"` // Y vector component
	Z float64 `json:"z" yaml:"z"` // Z vector component
}

// NewQuaternion creates a new quaternion
func NewQuaternion(w, x, y, z float64) Quaternion {
	return Quaternion{W: w, X: x, Y: y, Z: z}
}

// Identity returns the identity quaternion (no rotation)
func Identity() Quaternion {
	return Quaternion{W: 1.0, X: 0, Y: 0, Z: 0}
}

// SpatialAnchor represents a persistent spatial reference point for AR
type SpatialAnchor struct {
	ID               string           `json:"id" yaml:"id"`
	Position         *SpatialLocation `json:"position" yaml:"position"`
	Rotation         *Quaternion      `json:"rotation" yaml:"rotation"`
	Confidence       float64          `json:"confidence" yaml:"confidence"`
	Timestamp        time.Time        `json:"timestamp" yaml:"timestamp"`
	BuildingID       string           `json:"building_id" yaml:"building_id"`
	FloorID          string           `json:"floor_id" yaml:"floor_id"`
	RoomID           string           `json:"room_id" yaml:"room_id"`
	EquipmentID      string           `json:"equipment_id" yaml:"equipment_id"`
	ValidationStatus string           `json:"validation_status" yaml:"validation_status"`
	LastUpdated      time.Time        `json:"last_updated" yaml:"last_updated"`
	Platform         string           `json:"platform" yaml:"platform"`   // ARKit, ARCore, etc.
	Stability        float64          `json:"stability" yaml:"stability"` // 0-1 scale
	Range            float64          `json:"range" yaml:"range"`         // Detection range in meters
	Metadata         map[string]any   `json:"metadata" yaml:"metadata"`
}

// SpatialDataUpdate represents a spatial data update from mobile AR
type SpatialDataUpdate struct {
	ID               string         `json:"id" yaml:"id"`
	EquipmentID      string         `json:"equipment_id" yaml:"equipment_id"`
	SpatialAnchor    *SpatialAnchor `json:"spatial_anchor" yaml:"spatial_anchor"`
	ARPlatform       string         `json:"ar_platform" yaml:"ar_platform"`
	Timestamp        time.Time      `json:"timestamp" yaml:"timestamp"`
	TechnicianID     string         `json:"technician_id" yaml:"technician_id"`
	BuildingID       string         `json:"building_id" yaml:"building_id"`
	Confidence       float64        `json:"confidence" yaml:"confidence"`
	ValidationStatus string         `json:"validation_status" yaml:"validation_status"`
	SyncStatus       string         `json:"sync_status" yaml:"sync_status"`
	Source           string         `json:"source" yaml:"source"` // mobile_ar, import, manual
}

// EquipmentAROverlay represents AR overlay information for equipment
type EquipmentAROverlay struct {
	EquipmentID  string              `json:"equipment_id" yaml:"equipment_id"`
	Position     *SpatialLocation    `json:"position" yaml:"position"`
	Rotation     *Quaternion         `json:"rotation" yaml:"rotation"`
	Scale        *SpatialLocation    `json:"scale" yaml:"scale"`
	Status       string              `json:"status" yaml:"status"`
	LastUpdated  time.Time           `json:"last_updated" yaml:"last_updated"`
	ARVisibility ARVisibility        `json:"ar_visibility" yaml:"ar_visibility"`
	ModelType    string              `json:"model_type" yaml:"model_type"`       // 3D, 2D, icon
	ModelPath    string              `json:"model_path" yaml:"model_path"`       // Path to 3D model
	MaterialPath string              `json:"material_path" yaml:"material_path"` // Path to material file
	LOD          int                 `json:"lod" yaml:"lod"`                     // Level of Detail (0-3)
	Metadata     EquipmentARMetadata `json:"metadata" yaml:"metadata"`
}

// ARVisibility represents visibility conditions for AR overlays
type ARVisibility struct {
	IsVisible           bool      `json:"is_visible" yaml:"is_visible"`
	Distance            float64   `json:"distance" yaml:"distance"`                     // Distance in meters
	OcclusionLevel      float64   `json:"occlusion_level" yaml:"occlusion_level"`       // 0-1 scale
	LightingCondition   string    `json:"lighting_condition" yaml:"lighting_condition"` // good, poor, dark
	Contrast            float64   `json:"contrast" yaml:"contrast"`                     // 0-1 scale
	Brightness          float64   `json:"brightness" yaml:"brightness"`                 // 0-1 scale
	LastVisibilityCheck time.Time `json:"last_visibility_check" yaml:"last_visibility_check"`
}

// EquipmentARMetadata represents metadata for AR equipment visualization
type EquipmentARMetadata struct {
	Name         string         `json:"name" yaml:"name"`
	Type         string         `json:"type" yaml:"type"`
	Model        string         `json:"model" yaml:"model"`
	Manufacturer string         `json:"manufacturer" yaml:"manufacturer"`
	Criticality  string         `json:"criticality" yaml:"criticality"` // low, medium, high, critical
	Color        string         `json:"color" yaml:"color"`             // Hex color for visualization
	Tags         []string       `json:"tags" yaml:"tags"`
	Attrs        map[string]any `json:"attributes" yaml:"attributes"`
}

// ARNavigationPath represents a navigation path for AR guidance
type ARNavigationPath struct {
	ID             string             `json:"id" yaml:"id"`
	From           *SpatialLocation   `json:"from" yaml:"from"`
	To             *SpatialLocation   `json:"to" yaml:"to"`
	Waypoints      []*SpatialLocation `json:"waypoints" yaml:"waypoints"`
	Distance       float64            `json:"distance" yaml:"distance"`
	EstimatedTime  float64            `json:"estimated_time" yaml:"estimated_time"` // seconds
	Obstacles      []*SpatialLocation `json:"obstacles" yaml:"obstacles"`
	ARInstructions []ARInstruction    `json:"ar_instructions" yaml:"ar_instructions"`
	Difficulty     string             `json:"difficulty" yaml:"difficulty"` // easy, medium, hard
	Accessibility  bool               `json:"accessibility" yaml:"accessibility"`
	Hazardous      bool               `json:"hazardous" yaml:"hazardous"`
	CreatedAt      time.Time          `json:"created_at" yaml:"created_at"`
}

// ARInstruction represents a single navigation instruction
type ARInstruction struct {
	ID                string           `json:"id" yaml:"id"`
	Type              string           `json:"type" yaml:"type"` // move, turn, stop, wait
	Position          *SpatialLocation `json:"position" yaml:"position"`
	Description       string           `json:"description" yaml:"description"`
	ARVisualization   ARVisualization  `json:"ar_visualization" yaml:"ar_visualization"`
	EstimatedDuration float64          `json:"estimated_duration" yaml:"estimated_duration"` // seconds
	Priority          string           `json:"priority" yaml:"priority"`                     // low, medium, high
}

// ARVisualization represents visual elements for AR instructions
type ARVisualization struct {
	Type      string  `json:"type" yaml:"type"`           // arrow, circle, plane, object
	Color     string  `json:"color" yaml:"color"`         // Hex color
	Size      float64 `json:"size" yaml:"size"`           // Size multiplier
	Animation string  `json:"animation" yaml:"animation"` // pulse, rotate, none
	Opacity   float64 `json:"opacity" yaml:"opacity"`     // 0-1 scale
	Intensity float64 `json:"intensity" yaml:"intensity"` // Brightness/visibility
}

// ARSessionMetrics represents metrics for AR session performance
type ARSessionMetrics struct {
	SessionID                 string    `json:"session_id" yaml:"session_id"`
	StartTime                 time.Time `json:"start_time" yaml:"start_time"`
	EndTime                   time.Time `json:"end_time" yaml:"end_time"`
	Duration                  float64   `json:"duration" yaml:"duration"` // seconds
	AnchorsDetected           int       `json:"anchors_detected" yaml:"anchors_detected"`
	AnchorsCreated            int       `json:"anchors_created" yaml:"anchors_created"`
	AnchorsUpdated            int       `json:"anchors_updated" yaml:"anchors_updated"`
	AnchorsRemoved            int       `json:"anchors_removed" yaml:"anchors_removed"`
	EquipmentOverlaysRendered int       `json:"equipment_overlays_rendered" yaml:"equipment_overlays_rendered"`
	NavigationPathsCalculated int       `json:"navigation_paths_calculated" yaml:"navigation_paths_calculated"`
	ErrorsEncountered         int       `json:"errors_encountered" yaml:"errors_encountered"`
	AverageFrameRate          float64   `json:"average_frame_rate" yaml:"average_frame_rate"`
	AverageTrackingQuality    float64   `json:"average_tracking_quality" yaml:"average_tracking_quality"` // 0-1 scale
	BatteryUsage              float64   `json:"battery_usage" yaml:"battery_usage"`                       // percentage
	MemoryUsage               float64   `json:"memory_usage" yaml:"memory_usage"`                         // MB
	ThermalState              string    `json:"thermal_state" yaml:"thermal_state"`                       // normal, slight, intermediate, critical
}

// IFCImportResult represents the result of importing IFC data
type IFCImportResult struct {
	Success            bool      `json:"success" yaml:"success"`
	RepositoryID       string    `json:"repository_id" yaml:"repository_id"`
	ComponentsImported int       `json:"components_imported" yaml:"components_imported"`
	ComponentsSkipped  int       `json:"components_skipped" yaml:"components_skipped"`
	Errors             []string  `json:"errors" yaml:"errors"`
	Warnings           []string  `json:"warnings" yaml:"warnings"`
	ProcessingTime     float64   `json:"processing_time" yaml:"processing_time"` // seconds
	FileName           string    `json:"file_name" yaml:"file_name"`
	FileSize           int64     `json:"file_size" yaml:"file_size"` // bytes
	ImportDate         time.Time `json:"import_date" yaml:"import_date"`
	IFCVersion         string    `json:"ifc_version" yaml:"ifc_version"`
	SchemaURL          string    `json:"schema_url" yaml:"schema_url"`
}

// Validate performs validation on spatial anchor
func (sa *SpatialAnchor) Validate() error {
	if sa.ID == "" {
		return fmt.Errorf("spatial anchor ID is required")
	}
	if sa.Position == nil {
		return fmt.Errorf("spatial anchor position is required")
	}
	if sa.Confidence < 0 || sa.Confidence > 1 {
		return fmt.Errorf("spatial anchor confidence must be between 0 and 1")
	}
	if sa.BuildingID == "" {
		return fmt.Errorf("spatial anchor building ID is required")
	}
	return nil
}

// DistanceTo calculates distance to another spatial anchor
func (sa *SpatialAnchor) DistanceTo(other *SpatialAnchor) float64 {
	if sa.Position == nil || other == nil || other.Position == nil {
		return -1
	}
	loc1 := sa.Position.ToPoint3D()
	loc2 := other.Position.ToPoint3D()
	return loc1.DistanceTo(loc2)
}

// IsValid checks if the spatial anchor data is valid
func (sa *SpatialAnchor) IsValid() bool {
	return sa.Validate() == nil
}

// String returns a string representation of the spatial anchor
func (sa *SpatialAnchor) String() string {
	if sa.Position == nil {
		return fmt.Sprintf("SpatialAnchor{ID: %s, Position: nil, Confidence: %.3f}",
			sa.ID, sa.Confidence)
	}
	return fmt.Sprintf("SpatialAnchor{ID: %s, Position: (%.3f, %.3f, %.3f), Confidence: %.3f}",
		sa.ID, sa.Position.X, sa.Position.Y, sa.Position.Z, sa.Confidence)
}
