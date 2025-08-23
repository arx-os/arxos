package types

// ConnectionType represents how two walls connect
type ConnectionType int

const (
	ConnectionNone ConnectionType = iota
	ConnectionEndToEnd
	ConnectionOverlapping
	ConnectionIntersecting
	ConnectionAdjacent
)

// String representation of connection type
func (ct ConnectionType) String() string {
	switch ct {
	case ConnectionNone:
		return "none"
	case ConnectionEndToEnd:
		return "end-to-end"
	case ConnectionOverlapping:
		return "overlapping"
	case ConnectionIntersecting:
		return "intersecting"
	case ConnectionAdjacent:
		return "adjacent"
	default:
		return "unknown"
	}
}

// WallConnection represents a connection between two walls
type WallConnection struct {
	Wall1ID         uint64
	Wall2ID         uint64
	Type            ConnectionType
	ConnectionPoint SmartPoint3D
	Confidence      float32
	Distance        float64 // Distance between walls (mm)
	Angle           float64 // Angle between walls (degrees)
}

// NewWallConnection creates a new wall connection
func NewWallConnection(wall1ID, wall2ID uint64, connType ConnectionType) *WallConnection {
	return &WallConnection{
		Wall1ID:    wall1ID,
		Wall2ID:    wall2ID,
		Type:       connType,
		Confidence: 0.0,
		Distance:   0.0,
		Angle:      0.0,
	}
}
