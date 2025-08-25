package cgo

/*
#cgo CFLAGS: -I../c
#cgo LDFLAGS: -L../lib -larxwallcomposition -larxobject -lm
#include "bridge.h"
*/
import "C"
import (
	"time"
)

// =============================================================================
// ENUMS AND CONSTANTS
// =============================================================================

// Unit represents measurement units
type Unit int

const (
	UnitNanometer Unit = iota
	UnitMicrometer
	UnitMillimeter
	UnitCentimeter
	UnitMeter
	UnitInch
	UnitFoot
)

// ValidationState represents wall validation status
type ValidationState int

const (
	ValidationPending ValidationState = iota
	ValidationPartial
	ValidationComplete
	ValidationConflict
)

// WallType represents different types of walls
type WallType int

const (
	WallTypeInterior WallType = iota
	WallTypeExterior
	WallTypeLoadBearing
	WallTypePartition
	WallTypeFireRated
	WallTypeSoundRated
)

// CurveType represents different types of curved walls
type CurveType int

const (
	CurveTypeLinear CurveType = iota
	CurveTypeArc
	CurveTypeBezierQuadratic
	CurveTypeBezierCubic
	CurveTypeSpline
)

// =============================================================================
// CORE DATA STRUCTURES
// =============================================================================

// SmartPoint3D represents a 3D point with automatic unit conversion
type SmartPoint3D struct {
	X, Y, Z int64 // Stored in nanometers for precision
	Unit    Unit  // What unit this represents
}

// WallSegment represents an individual wall piece within a structure
type WallSegment struct {
	ID          uint64
	StartPoint  SmartPoint3D
	EndPoint    SmartPoint3D
	Length      float64 // Segment length (mm)
	Height      float64 // Segment height (mm)
	Thickness   float64 // Segment thickness (mm)
	Confidence  float64 // Individual segment confidence (0.0 - 1.0)
	Orientation float64 // Wall angle in degrees (0-360)
	WallType    WallType
	Material    string
	FireRating  string
	ArxObjects  []uint64 // IDs of composing ArxObjects
	CreatedAt   time.Time
}

// CurvedWallSegment represents a wall segment with curved geometry support
type CurvedWallSegment struct {
	Base                WallSegment
	CurveType           CurveType
	Radius              float64        // For arcs
	StartAngle          float64        // For arcs (radians)
	EndAngle            float64        // For arcs (radians)
	Center              SmartPoint3D   // For arcs
	ControlPoints       []SmartPoint3D // For Bézier curves
	CurveLength         float64        // Calculated curve length (mm)
	ApproximationPoints uint32         // Number of points for curve approximation
}

// WallConnection represents a connection between wall segments
type WallConnection struct {
	Segment1ID           uint64
	Segment2ID           uint64
	ConnectionConfidence float64
	GapDistance          float64 // mm
	AngleDifference      float64 // degrees
	IsParallel           bool
	IsPerpendicular      bool
	IsConnected          bool
}

// WallStructure represents a composed wall made of multiple segments
type WallStructure struct {
	ID                uint64
	Segments          []WallSegment
	StartPoint        SmartPoint3D
	EndPoint          SmartPoint3D
	TotalLength       float64 // Calculated from start/end points (mm)
	MaxHeight         float64 // Maximum height of all segments (mm)
	AvgThickness      float64 // Average thickness of all segments (mm)
	OverallConfidence float64 // Overall wall confidence (0.0 - 1.0)
	Validation        ValidationState
	ArxObjects        []uint64 // IDs of composing ArxObjects
	BuildingID        string
	FloorID           string
	RoomID            string
	PrimaryWallType   WallType
	Notes             string
	CreatedAt         time.Time
	UpdatedAt         time.Time
}

// CompositionConfig holds configuration parameters for the composition engine
type CompositionConfig struct {
	MaxGapDistance              float64 // Maximum gap distance for wall connections (in mm)
	ParallelThreshold           float64 // Threshold for considering walls parallel (in degrees)
	MinWallLength               float64 // Minimum wall length to consider (in mm)
	MaxWallLength               float64 // Maximum wall length to consider (in mm)
	ConfidenceThreshold         float64 // Minimum confidence threshold for composition
	MaxCurveApproximationPoints uint32
	EnableCurvedWalls           bool
	EnableAdvancedValidation    bool
}

// =============================================================================
// CGO INTEGRATION TYPES
// =============================================================================

// CWallSegment is the C representation of a wall segment
type CWallSegment C.arx_wall_segment_t

// CCurvedWallSegment is the C representation of a curved wall segment
type CCurvedWallSegment C.arx_curved_wall_segment_t

// CWallStructure is the C representation of a wall structure
type CWallStructure C.arx_wall_structure_t

// CWallConnection is the C representation of a wall connection
type CWallConnection C.arx_wall_connection_t

// CWallCompositionEngine is the C representation of the wall composition engine
type CWallCompositionEngine C.arx_wall_composition_engine_t

// CSmartPoint3D is the C representation of a 3D point
type CSmartPoint3D C.arx_smart_point_3d_t

// =============================================================================
// CONVERSION FUNCTIONS
// =============================================================================

// ToCSmartPoint3D converts Go SmartPoint3D to C representation
func (p SmartPoint3D) ToCSmartPoint3D() CSmartPoint3D {
	return CSmartPoint3D{
		x:    C.int64_t(p.X),
		y:    C.int64_t(p.Y),
		z:    C.int64_t(p.Z),
		unit: C.arx_unit_t(p.Unit),
	}
}

// FromCSmartPoint3D converts C SmartPoint3D to Go representation
func FromCSmartPoint3D(cp CSmartPoint3D) SmartPoint3D {
	return SmartPoint3D{
		X:    int64(cp.x),
		Y:    int64(cp.y),
		Z:    int64(cp.z),
		Unit: Unit(cp.unit),
	}
}

// ToCWallSegment converts Go WallSegment to C representation
func (w WallSegment) ToCWallSegment() *CWallSegment {
	cSegment := &CWallSegment{
		id: C.uint64_t(w.ID),
		start_point: C.arx_smart_point_3d_t{
			x:    C.int64_t(w.StartPoint.X),
			y:    C.int64_t(w.StartPoint.Y),
			z:    C.int64_t(w.StartPoint.Z),
			unit: C.arx_unit_t(w.StartPoint.Unit),
		},
		end_point: C.arx_smart_point_3d_t{
			x:    C.int64_t(w.EndPoint.X),
			y:    C.int64_t(w.EndPoint.Y),
			z:    C.int64_t(w.EndPoint.Z),
			unit: C.arx_unit_t(w.EndPoint.Unit),
		},
		length:           C.double(w.Length),
		height:           C.double(w.Height),
		thickness:        C.double(w.Thickness),
		confidence:       C.double(w.Confidence),
		orientation:      C.double(w.Orientation),
		wall_type:        C.arx_wall_type_t(w.WallType),
		arx_object_count: C.uint8_t(len(w.ArxObjects)),
		created_at:       C.time_t(w.CreatedAt.Unix()),
	}

	// Copy ArxObject IDs
	for i, id := range w.ArxObjects {
		if i < 16 { // C struct limit
			cSegment.arx_object_ids[i] = C.uint64_t(id)
		}
	}

	// Copy strings
	copy(cSegment.material[:], w.Material)
	copy(cSegment.fire_rating[:], w.FireRating)

	return cSegment
}

// FromCWallSegment converts C WallSegment to Go representation
func FromCWallSegment(cw *CWallSegment) WallSegment {
	segment := WallSegment{
		ID:          uint64(cw.id),
		Length:      float64(cw.length),
		Height:      float64(cw.height),
		Thickness:   float64(cw.thickness),
		Confidence:  float64(cw.confidence),
		Orientation: float64(cw.orientation),
		WallType:    WallType(cw.wall_type),
		CreatedAt:   time.Unix(int64(cw.created_at), 0),
	}

	// Convert points
	segment.StartPoint = FromCSmartPoint3D(CSmartPoint3D(cw.start_point))
	segment.EndPoint = FromCSmartPoint3D(CSmartPoint3D(cw.end_point))

	// Convert ArxObject IDs
	segment.ArxObjects = make([]uint64, cw.arx_object_count)
	for i := uint8(0); i < cw.arx_object_count; i++ {
		segment.ArxObjects[i] = uint64(cw.arx_object_ids[i])
	}

	// Convert strings
	segment.Material = C.GoString(&cw.material[0])
	segment.FireRating = C.GoString(&cw.fire_rating[0])

	return segment
}

// ToCWallStructure converts Go WallStructure to C representation
func (w WallStructure) ToCWallStructure() *CWallStructure {
	cStructure := &CWallStructure{
		id:                 C.uint64_t(w.ID),
		segment_count:      C.uint32_t(len(w.Segments)),
		total_length:       C.double(w.TotalLength),
		max_height:         C.double(w.MaxHeight),
		avg_thickness:      C.double(w.AvgThickness),
		overall_confidence: C.double(w.OverallConfidence),
		validation_state:   C.arx_validation_state_t(w.Validation),
		arx_object_count:   C.uint8_t(len(w.ArxObjects)),
		primary_wall_type:  C.arx_wall_type_t(w.PrimaryWallType),
		created_at:         C.time_t(w.CreatedAt.Unix()),
		updated_at:         C.time_t(w.UpdatedAt.Unix()),
	}

	// Convert points
	cStructure.start_point = C.arx_smart_point_3d_t{
		x:    C.int64_t(w.StartPoint.X),
		y:    C.int64_t(w.StartPoint.Y),
		z:    C.int64_t(w.StartPoint.Z),
		unit: C.arx_unit_t(w.StartPoint.Unit),
	}
	cStructure.end_point = C.arx_smart_point_3d_t{
		x:    C.int64_t(w.EndPoint.X),
		y:    C.int64_t(w.EndPoint.Y),
		z:    C.int64_t(w.EndPoint.Z),
		unit: C.arx_unit_t(w.EndPoint.Unit),
	}

	// Convert ArxObject IDs
	for i, id := range w.ArxObjects {
		if i < 32 { // C struct limit
			cStructure.arx_object_ids[i] = C.uint64_t(id)
		}
	}

	// Copy strings
	copy(cStructure.building_id[:], w.BuildingID)
	copy(cStructure.floor_id[:], w.FloorID)
	copy(cStructure.room_id[:], w.RoomID)
	copy(cStructure.notes[:], w.Notes)

	return cStructure
}

// FromCWallStructure converts C WallStructure to Go representation
func FromCWallStructure(cw *CWallStructure) WallStructure {
	structure := WallStructure{
		ID:                uint64(cw.id),
		TotalLength:       float64(cw.total_length),
		MaxHeight:         float64(cw.max_height),
		AvgThickness:      float64(cw.avg_thickness),
		OverallConfidence: float64(cw.overall_confidence),
		Validation:        ValidationState(cw.validation_state),
		PrimaryWallType:   WallType(cw.primary_wall_type),
		CreatedAt:         time.Unix(int64(cw.created_at), 0),
		UpdatedAt:         time.Unix(int64(cw.updated_at), 0),
	}

	// Convert points
	structure.StartPoint = FromCSmartPoint3D(CSmartPoint3D(cw.start_point))
	structure.EndPoint = FromCSmartPoint3D(CSmartPoint3D(cw.end_point))

	// Convert ArxObject IDs
	structure.ArxObjects = make([]uint64, cw.arx_object_count)
	for i := uint8(0); i < cw.arx_object_count; i++ {
		structure.ArxObjects[i] = uint64(cw.arx_object_ids[i])
	}

	// Convert strings
	structure.BuildingID = C.GoString(&cw.building_id[0])
	structure.FloorID = C.GoString(&cw.floor_id[0])
	structure.RoomID = C.GoString(&cw.room_id[0])
	structure.Notes = C.GoString(&cw.notes[0])

	return structure
}

// ToCWallConnection converts Go WallConnection to C representation
func (wc WallConnection) ToCWallConnection() *CWallConnection {
	return &CWallConnection{
		segment1_id:           C.uint64_t(wc.Segment1ID),
		segment2_id:           C.uint64_t(wc.Segment2ID),
		connection_confidence: C.double(wc.ConnectionConfidence),
		gap_distance:          C.double(wc.GapDistance),
		angle_difference:      C.double(wc.AngleDifference),
		is_parallel:           C.bool(wc.IsParallel),
		is_perpendicular:      C.bool(wc.IsPerpendicular),
		is_connected:          C.bool(wc.IsConnected),
	}
}

// FromCWallConnection converts C WallConnection to Go representation
func FromCWallConnection(cwc *CWallConnection) WallConnection {
	return WallConnection{
		Segment1ID:           uint64(cwc.segment1_id),
		Segment2ID:           uint64(cwc.segment2_id),
		ConnectionConfidence: float64(cwc.connection_confidence),
		GapDistance:          float64(cwc.gap_distance),
		AngleDifference:      float64(cwc.angle_difference),
		IsParallel:           bool(cwc.is_parallel),
		IsPerpendicular:      bool(cwc.is_perpendicular),
		IsConnected:          bool(cwc.is_connected),
	}
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

// DefaultCompositionConfig returns sensible default configuration values
func DefaultCompositionConfig() CompositionConfig {
	return CompositionConfig{
		MaxGapDistance:              50.0,    // 50mm gap tolerance
		ParallelThreshold:           5.0,     // 5 degrees tolerance for parallel walls
		MinWallLength:               100.0,   // 100mm minimum wall length
		MaxWallLength:               50000.0, // 50m maximum wall length
		ConfidenceThreshold:         0.6,     // 60% confidence threshold
		MaxCurveApproximationPoints: 32,
		EnableCurvedWalls:           true,
		EnableAdvancedValidation:    false,
	}
}

// SetAdvanced enables advanced features in the configuration
func (c *CompositionConfig) SetAdvanced(enable bool) {
	c.EnableAdvancedValidation = enable
	if enable {
		c.MaxCurveApproximationPoints = 64
	} else {
		c.MaxCurveApproximationPoints = 32
	}
}

// String representations for enums
func (u Unit) String() string {
	switch u {
	case UnitNanometer:
		return "nm"
	case UnitMicrometer:
		return "μm"
	case UnitMillimeter:
		return "mm"
	case UnitCentimeter:
		return "cm"
	case UnitMeter:
		return "m"
	case UnitInch:
		return "in"
	case UnitFoot:
		return "ft"
	default:
		return "unknown"
	}
}

func (vs ValidationState) String() string {
	switch vs {
	case ValidationPending:
		return "pending"
	case ValidationPartial:
		return "partial"
	case ValidationComplete:
		return "complete"
	case ValidationConflict:
		return "conflict"
	default:
		return "unknown"
	}
}

func (wt WallType) String() string {
	switch wt {
	case WallTypeInterior:
		return "interior"
	case WallTypeExterior:
		return "exterior"
	case WallTypeLoadBearing:
		return "load-bearing"
	case WallTypePartition:
		return "partition"
	case WallTypeFireRated:
		return "fire-rated"
	case WallTypeSoundRated:
		return "sound-rated"
	default:
		return "unknown"
	}
}

func (ct CurveType) String() string {
	switch ct {
	case CurveTypeLinear:
		return "linear"
	case CurveTypeArc:
		return "arc"
	case CurveTypeBezierQuadratic:
		return "bezier-quadratic"
	case CurveTypeBezierCubic:
		return "bezier-cubic"
	case CurveTypeSpline:
		return "spline"
	default:
		return "unknown"
	}
}
