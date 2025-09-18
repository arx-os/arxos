package ar

import (
	"fmt"
	"math"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/spatial"
)

// CoordinateSystem represents an AR coordinate system
type CoordinateSystem string

const (
	// ARKit uses a right-handed coordinate system
	// +X: right, +Y: up, +Z: toward viewer
	CoordinateSystemARKit CoordinateSystem = "arkit"

	// ARCore uses a right-handed coordinate system
	// +X: right, +Y: up, +Z: toward viewer (similar to ARKit)
	CoordinateSystemARCore CoordinateSystem = "arcore"

	// World coordinates in our building model
	// +X: east, +Y: north, +Z: up
	CoordinateSystemWorld CoordinateSystem = "world"
)

// ARTransform represents a transformation in AR space
type ARTransform struct {
	Position   ARPoint3D  `json:"position"`
	Rotation   ARRotation `json:"rotation"`
	Scale      float64    `json:"scale"`
	Timestamp  time.Time  `json:"timestamp"`
	Confidence float32    `json:"confidence"`
}

// ARPoint3D represents a point in AR coordinate space
type ARPoint3D struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// ARRotation represents rotation using quaternion
type ARRotation struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
	W float64 `json:"w"`
}

// ARCoordinateConverter handles coordinate system conversions
type ARCoordinateConverter struct {
	worldOrigin     spatial.Point3D
	arOrigin        ARPoint3D
	alignmentMatrix Matrix4x4
	system          CoordinateSystem
	calibrated      bool
	mu              sync.RWMutex
}

// Matrix4x4 represents a 4x4 transformation matrix
type Matrix4x4 [16]float64

// NewARCoordinateConverter creates a new AR coordinate converter
func NewARCoordinateConverter(system CoordinateSystem) *ARCoordinateConverter {
	return &ARCoordinateConverter{
		system:          system,
		alignmentMatrix: IdentityMatrix(),
		calibrated:      false,
	}
}

// Calibrate calibrates the AR coordinate system with world coordinates
func (acc *ARCoordinateConverter) Calibrate(arAnchor ARPoint3D, worldAnchor spatial.Point3D, rotation ARRotation) error {
	acc.mu.Lock()
	defer acc.mu.Unlock()

	acc.arOrigin = arAnchor
	acc.worldOrigin = worldAnchor

	// Build alignment matrix from rotation and translation
	acc.alignmentMatrix = BuildTransformMatrix(
		worldAnchor.X-arAnchor.X,
		worldAnchor.Y-arAnchor.Y,
		worldAnchor.Z-arAnchor.Z,
		rotation,
	)

	acc.calibrated = true
	return nil
}

// ARToWorld converts AR coordinates to world coordinates
func (acc *ARCoordinateConverter) ARToWorld(arPoint ARPoint3D) (spatial.Point3D, error) {
	acc.mu.RLock()
	defer acc.mu.RUnlock()

	if !acc.calibrated {
		return spatial.Point3D{}, fmt.Errorf("coordinate converter not calibrated")
	}

	// Convert coordinate system conventions first
	var converted ARPoint3D
	switch acc.system {
	case CoordinateSystemARKit, CoordinateSystemARCore:
		// ARKit/ARCore: +Y is up, +Z is toward viewer
		// World: +Z is up, +Y is north
		// So AR(X,Y,Z) -> World(X,-Z,Y)
		converted = ARPoint3D{
			X: arPoint.X,
			Y: -arPoint.Z, // AR's -Z becomes world's +Y (north)
			Z: arPoint.Y,  // AR's +Y becomes world's +Z (up)
		}
	default:
		converted = arPoint
	}

	// Apply transformation matrix
	transformed := acc.alignmentMatrix.Transform(converted)

	return spatial.Point3D{
		X: transformed.X,
		Y: transformed.Y,
		Z: transformed.Z,
	}, nil
}

// WorldToAR converts world coordinates to AR coordinates
func (acc *ARCoordinateConverter) WorldToAR(worldPoint spatial.Point3D) (ARPoint3D, error) {
	acc.mu.RLock()
	defer acc.mu.RUnlock()

	if !acc.calibrated {
		return ARPoint3D{}, fmt.Errorf("coordinate converter not calibrated")
	}

	// Apply inverse transformation matrix first
	inverseMatrix := acc.alignmentMatrix.Inverse()
	worldAsAR := ARPoint3D{X: worldPoint.X, Y: worldPoint.Y, Z: worldPoint.Z}
	transformed := inverseMatrix.Transform(worldAsAR)

	// Convert coordinate system conventions
	var arPoint ARPoint3D
	switch acc.system {
	case CoordinateSystemARKit, CoordinateSystemARCore:
		// World to AR coordinate conversion
		// World(X,Y,Z) -> AR(X,Z,-Y)
		arPoint = ARPoint3D{
			X: transformed.X,
			Y: transformed.Z,  // World's +Z (up) becomes AR's +Y
			Z: -transformed.Y, // World's +Y (north) becomes AR's -Z
		}
	default:
		arPoint = transformed
	}

	return arPoint, nil
}

// TrackingState represents the AR tracking state
type TrackingState int

const (
	TrackingStateNone TrackingState = iota
	TrackingStateLimited
	TrackingStateNormal
	TrackingStateExcessive // Too much movement
)

// TrackingQuality provides information about AR tracking quality
type TrackingQuality struct {
	State           TrackingState `json:"state"`
	Confidence      float32       `json:"confidence"`
	LightEstimate   float32       `json:"light_estimate"`
	PlaneCount      int           `json:"plane_count"`
	FeatureCount    int           `json:"feature_count"`
	LastUpdate      time.Time     `json:"last_update"`
	DriftCorrection ARPoint3D     `json:"drift_correction"`
}

// ARSession represents an active AR session
type ARSession struct {
	ID              string                 `json:"id"`
	DeviceID        string                 `json:"device_id"`
	BuildingID      string                 `json:"building_id"`
	StartTime       time.Time              `json:"start_time"`
	System          CoordinateSystem       `json:"system"`
	Converter       *ARCoordinateConverter `json:"-"`
	TrackingQuality TrackingQuality        `json:"tracking_quality"`
	ActiveAnchors   []string               `json:"active_anchors"`
	mu              sync.RWMutex
}

// NewARSession creates a new AR session
func NewARSession(deviceID, buildingID string, system CoordinateSystem) *ARSession {
	return &ARSession{
		ID:         fmt.Sprintf("ar_session_%d", time.Now().UnixNano()),
		DeviceID:   deviceID,
		BuildingID: buildingID,
		StartTime:  time.Now(),
		System:     system,
		Converter:  NewARCoordinateConverter(system),
		TrackingQuality: TrackingQuality{
			State:      TrackingStateNone,
			Confidence: 0,
			LastUpdate: time.Now(),
		},
		ActiveAnchors: make([]string, 0),
	}
}

// UpdateTracking updates the tracking quality information
func (session *ARSession) UpdateTracking(quality TrackingQuality) {
	session.mu.Lock()
	defer session.mu.Unlock()

	session.TrackingQuality = quality
	session.TrackingQuality.LastUpdate = time.Now()
}

// AddAnchor adds an anchor to the session
func (session *ARSession) AddAnchor(anchorID string) {
	session.mu.Lock()
	defer session.mu.Unlock()

	session.ActiveAnchors = append(session.ActiveAnchors, anchorID)
}

// RemoveAnchor removes an anchor from the session
func (session *ARSession) RemoveAnchor(anchorID string) {
	session.mu.Lock()
	defer session.mu.Unlock()

	filtered := make([]string, 0, len(session.ActiveAnchors))
	for _, id := range session.ActiveAnchors {
		if id != anchorID {
			filtered = append(filtered, id)
		}
	}
	session.ActiveAnchors = filtered
}

// IsTrackingStable returns whether tracking is stable enough for operations
func (session *ARSession) IsTrackingStable() bool {
	session.mu.RLock()
	defer session.mu.RUnlock()

	return session.TrackingQuality.State == TrackingStateNormal &&
		session.TrackingQuality.Confidence > 0.7
}

// Matrix operations

// IdentityMatrix returns an identity matrix
func IdentityMatrix() Matrix4x4 {
	return Matrix4x4{
		1, 0, 0, 0,
		0, 1, 0, 0,
		0, 0, 1, 0,
		0, 0, 0, 1,
	}
}

// BuildTransformMatrix builds a transformation matrix
func BuildTransformMatrix(tx, ty, tz float64, rotation ARRotation) Matrix4x4 {
	// Convert quaternion to rotation matrix
	q := rotation
	qxx := q.X * q.X
	qyy := q.Y * q.Y
	qzz := q.Z * q.Z
	qxy := q.X * q.Y
	qxz := q.X * q.Z
	qyz := q.Y * q.Z
	qwx := q.W * q.X
	qwy := q.W * q.Y
	qwz := q.W * q.Z

	return Matrix4x4{
		1 - 2*(qyy+qzz), 2 * (qxy - qwz), 2 * (qxz + qwy), tx,
		2 * (qxy + qwz), 1 - 2*(qxx+qzz), 2 * (qyz - qwx), ty,
		2 * (qxz - qwy), 2 * (qyz + qwx), 1 - 2*(qxx+qyy), tz,
		0, 0, 0, 1,
	}
}

// Transform applies the matrix transformation to a point
func (m Matrix4x4) Transform(p ARPoint3D) ARPoint3D {
	return ARPoint3D{
		X: m[0]*p.X + m[1]*p.Y + m[2]*p.Z + m[3],
		Y: m[4]*p.X + m[5]*p.Y + m[6]*p.Z + m[7],
		Z: m[8]*p.X + m[9]*p.Y + m[10]*p.Z + m[11],
	}
}

// Inverse calculates the inverse of the matrix
func (m Matrix4x4) Inverse() Matrix4x4 {
	// Simplified inverse for transformation matrix
	// Extract rotation part (3x3)
	// For orthogonal rotation matrices, inverse = transpose
	inv := Matrix4x4{}

	// Transpose rotation part
	inv[0], inv[1], inv[2] = m[0], m[4], m[8]
	inv[4], inv[5], inv[6] = m[1], m[5], m[9]
	inv[8], inv[9], inv[10] = m[2], m[6], m[10]

	// Invert translation
	tx, ty, tz := m[3], m[7], m[11]
	inv[3] = -(inv[0]*tx + inv[1]*ty + inv[2]*tz)
	inv[7] = -(inv[4]*tx + inv[5]*ty + inv[6]*tz)
	inv[11] = -(inv[8]*tx + inv[9]*ty + inv[10]*tz)

	// Set bottom row
	inv[12], inv[13], inv[14], inv[15] = 0, 0, 0, 1

	return inv
}

// ToSpatialPoint converts ARPoint3D to spatial.Point3D
func (p ARPoint3D) ToSpatialPoint() spatial.Point3D {
	return spatial.Point3D{X: p.X, Y: p.Y, Z: p.Z}
}

// FromSpatialPoint creates ARPoint3D from spatial.Point3D
func FromSpatialPoint(p spatial.Point3D) ARPoint3D {
	return ARPoint3D{X: p.X, Y: p.Y, Z: p.Z}
}

// Distance calculates the distance between two AR points
func (p ARPoint3D) Distance(other ARPoint3D) float64 {
	dx := p.X - other.X
	dy := p.Y - other.Y
	dz := p.Z - other.Z
	return math.Sqrt(dx*dx + dy*dy + dz*dz)
}

// String returns string representation of tracking state
func (ts TrackingState) String() string {
	switch ts {
	case TrackingStateNone:
		return "none"
	case TrackingStateLimited:
		return "limited"
	case TrackingStateNormal:
		return "normal"
	case TrackingStateExcessive:
		return "excessive"
	default:
		return "unknown"
	}
}
