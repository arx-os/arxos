// Package topology provides core building topology structures for BIM conversion
package topology

import (
	"math"
	"time"
)

// Point2D represents a 2D coordinate in nanometer precision
type Point2D struct {
	X int64 // Nanometers
	Y int64
}

// Point3D represents a 3D coordinate in nanometer precision  
type Point3D struct {
	X int64 // Nanometers
	Y int64
	Z int64
}

// LineSegment represents a detected wall segment before processing
type LineSegment struct {
	ID        uint64
	Start     Point2D
	End       Point2D
	Thickness int64 // Nanometers
	Confidence float64
	Source    string // "pdf_vector", "image_raster", "manual"
}

// Wall represents a processed wall with connections and metadata
type Wall struct {
	ID             uint64
	StartPoint     Point3D
	EndPoint       Point3D
	Thickness      int64    // Nanometers
	Height         int64    // Nanometers (standard ceiling height)
	ConnectedWalls []uint64 // IDs of connected walls
	BoundedRooms   []uint64 // IDs of adjacent rooms
	Openings       []Opening
	Type           WallType
	Confidence     float64
	ValidationStatus ValidationStatus
}

// WallType categorizes wall function
type WallType uint8

const (
	WallTypeUnknown WallType = iota
	WallTypeExterior
	WallTypeInterior
	WallTypeStructural
	WallTypePartition
	WallTypeCurtain
)

// Opening represents doors, windows, or other wall openings
type Opening struct {
	ID       uint64
	Position int64 // Distance from wall start in nanometers
	Width    int64
	Height   int64
	Type     OpeningType
}

// OpeningType categorizes openings
type OpeningType uint8

const (
	OpeningTypeDoor OpeningType = iota
	OpeningTypeWindow
	OpeningTypeArchway
	OpeningTypeService
)

// Room represents a closed space bounded by walls
type Room struct {
	ID            uint64
	BoundaryWalls []uint64  // Ordered list of wall IDs
	Footprint     []Point2D // Closed polygon in nanometers
	Centroid      Point3D
	Area          int64 // Square nanometers
	FloorHeight   int64
	CeilingHeight int64
	Name          string
	Number        string // Room number from OCR
	Function      RoomFunction
	AdjacentRooms []uint64
	Confidence    float64
	ValidationStatus ValidationStatus
}

// RoomFunction categorizes room usage
type RoomFunction uint8

const (
	RoomFunctionUnknown RoomFunction = iota
	RoomFunctionClassroom
	RoomFunctionOffice
	RoomFunctionCorridor
	RoomFunctionBathroom
	RoomFunctionStorage
	RoomFunctionMechanical
	RoomFunctionCafeteria
	RoomFunctionGymnasium
	RoomFunctionLibrary
	RoomFunctionLaboratory
	RoomFunctionAuditorium
	RoomFunctionLobby
)

// Building represents the complete topology
type Building struct {
	ID           uint64
	Name         string
	Address      string
	Walls        map[uint64]*Wall
	Rooms        map[uint64]*Room
	RoomGraph    *Graph // Adjacency between rooms
	WallGraph    *Graph // Connectivity between walls
	SpatialIndex *SpatialIndex
	Metadata     BuildingMetadata
	ProcessingResult ProcessingResult
}

// BuildingMetadata contains building-specific information
type BuildingMetadata struct {
	BuildingType    BuildingType
	YearBuilt       int
	TotalArea       int64 // Square nanometers
	NumFloors       int
	SchoolLevel     string // "elementary", "middle", "high"
	DistrictID      string
	PrototypeID     string // For standardized designs
}

// BuildingType categorizes building usage
type BuildingType uint8

const (
	BuildingTypeUnknown BuildingType = iota
	BuildingTypeEducational
	BuildingTypeHealthcare
	BuildingTypeOffice
	BuildingTypeResidential
	BuildingTypeIndustrial
	BuildingTypeRetail
)

// ProcessingResult tracks conversion quality
type ProcessingResult struct {
	TotalSegments      int
	MergedEndpoints    int
	DetectedRooms      int
	Confidence         float64
	Issues             []ValidationIssue
	RequiresReview     bool
	ProcessingTime     time.Duration
	AlgorithmsApplied  []string
	ManualCorrections  []ManualCorrection
}

// ValidationStatus tracks review state
type ValidationStatus uint8

const (
	ValidationPending ValidationStatus = iota
	ValidationAutomatic
	ValidationManual
	ValidationApproved
	ValidationRejected
)

// ValidationIssue represents a detected problem
type ValidationIssue struct {
	ID          uint64
	Type        IssueType
	Severity    IssueSeverity
	Description string
	Location    Point2D
	AffectedIDs []uint64 // Wall or Room IDs
	SuggestedFix string
}

// IssueType categorizes validation problems
type IssueType uint8

const (
	IssueTypeDisconnectedWall IssueType = iota
	IssueTypeUnclosedRoom
	IssueTypeOverlappingWalls
	IssueTypeMissingDoor
	IssueTypeInvalidDimensions
	IssueTypeSemanticViolation
)

// IssueSeverity indicates problem importance
type IssueSeverity uint8

const (
	SeverityInfo IssueSeverity = iota
	SeverityWarning
	SeverityError
	SeverityCritical
)

// ManualCorrection records human interventions
type ManualCorrection struct {
	ID          uint64
	Timestamp   time.Time
	UserID      string
	Type        CorrectionType
	Before      interface{} // Original state
	After       interface{} // Corrected state
	Reason      string
	Confidence  float64 // User's confidence in correction
}

// CorrectionType categorizes manual fixes
type CorrectionType uint8

const (
	CorrectionTypeWallConnection CorrectionType = iota
	CorrectionTypeRoomBoundary
	CorrectionTypeRoomLabel
	CorrectionTypeWallRemoval
	CorrectionTypeWallAddition
	CorrectionTypeDoorPlacement
)

// Graph represents adjacency relationships
type Graph struct {
	Nodes map[uint64]*GraphNode
	Edges map[uint64]*GraphEdge
}

// GraphNode represents a vertex in the graph
type GraphNode struct {
	ID       uint64
	Type     string // "room", "wall_intersection"
	Data     interface{}
	Adjacent []uint64
}

// GraphEdge represents a connection
type GraphEdge struct {
	ID     uint64
	Source uint64
	Target uint64
	Weight float64
	Type   string // "wall", "door", "opening"
}

// SpatialIndex provides efficient geometric queries
type SpatialIndex struct {
	RTree    *RTree
	GridHash *GridHash
	KDTree   *KDTree
}

// Placeholder structures for spatial indexing
type RTree struct{}
type GridHash struct{}
type KDTree struct{}

// BoundingBox for spatial queries
type BoundingBox struct {
	Min Point2D
	Max Point2D
}

// Helper functions for unit conversions

// MetersToNano converts meters to nanometers
func MetersToNano(meters float64) int64 {
	return int64(meters * 1e9)
}

// NanoToMeters converts nanometers to meters
func NanoToMeters(nano int64) float64 {
	return float64(nano) / 1e9
}

// Distance calculates Euclidean distance between points
func Distance(p1, p2 Point2D) float64 {
	dx := float64(p2.X - p1.X)
	dy := float64(p2.Y - p1.Y)
	return math.Sqrt(dx*dx + dy*dy)
}

// Area calculates polygon area using shoelace formula
func Area(polygon []Point2D) int64 {
	if len(polygon) < 3 {
		return 0
	}
	
	var area int64
	n := len(polygon)
	
	for i := 0; i < n; i++ {
		j := (i + 1) % n
		area += polygon[i].X * polygon[j].Y
		area -= polygon[j].X * polygon[i].Y
	}
	
	return int64(math.Abs(float64(area) / 2))
}

// Centroid calculates polygon center point
func Centroid(polygon []Point2D) Point2D {
	if len(polygon) == 0 {
		return Point2D{}
	}
	
	var sumX, sumY int64
	for _, p := range polygon {
		sumX += p.X
		sumY += p.Y
	}
	
	n := int64(len(polygon))
	return Point2D{
		X: sumX / n,
		Y: sumY / n,
	}
}