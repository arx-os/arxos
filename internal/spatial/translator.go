package spatial

import (
	"fmt"
	"math"
	"sync"
)

// CoordinateTranslator handles conversion between different coordinate systems
type CoordinateTranslator struct {
	buildingID     string
	buildingOrigin GPSCoordinate // Real-world GPS origin
	localOrigin    Point3D       // Local coordinate system origin
	gridScale      float64       // Meters per grid unit (default 0.5)
	floorHeight    float64       // Meters between floors (default 3.0)
	rotation       float64       // Building rotation from north in degrees

	// Caching for performance
	transformCache map[string]*Transform
	cacheMutex     sync.RWMutex

	// Movement thresholds
	thresholds MovementThresholds
}

// MovementThresholds defines thresholds for detecting significant movement
type MovementThresholds struct {
	GridUnitThreshold   float64 // Movement to trigger grid update (default: 1.0)
	RoomChangeThreshold float64 // Distance to consider room change (default: 0.5m)
	FloorChangeMargin   float64 // Margin for floor detection (default: 0.1m)
	RotationThreshold   float64 // Rotation change in degrees (default: 5.0)
}

// DefaultMovementThresholds returns default threshold values
func DefaultMovementThresholds() MovementThresholds {
	return MovementThresholds{
		GridUnitThreshold:   1.0,
		RoomChangeThreshold: 0.5,
		FloorChangeMargin:   0.1,
		RotationThreshold:   5.0,
	}
}

// NewCoordinateTranslator creates a new coordinate translator
func NewCoordinateTranslator(buildingID string) *CoordinateTranslator {
	return &CoordinateTranslator{
		buildingID:     buildingID,
		gridScale:      0.5, // 0.5 meters per grid unit
		floorHeight:    3.0, // 3 meters between floors
		rotation:       0.0,
		transformCache: make(map[string]*Transform),
		thresholds:     DefaultMovementThresholds(),
	}
}

// SetBuildingOrigin sets the GPS origin for the building
func (ct *CoordinateTranslator) SetBuildingOrigin(gps GPSCoordinate, rotation float64) {
	ct.buildingOrigin = gps
	ct.rotation = rotation
}

// SetGridScale sets the scale for grid coordinates
func (ct *CoordinateTranslator) SetGridScale(scale float64) {
	if scale > 0 {
		ct.gridScale = scale
		ct.clearCache()
	}
}

// SetFloorHeight sets the height between floors
func (ct *CoordinateTranslator) SetFloorHeight(height float64) {
	if height > 0 {
		ct.floorHeight = height
		ct.clearCache()
	}
}

// SetThresholds sets custom movement thresholds
func (ct *CoordinateTranslator) SetThresholds(thresholds MovementThresholds) {
	ct.thresholds = thresholds
}

// GridToWorld converts grid coordinates to world coordinates
func (ct *CoordinateTranslator) GridToWorld(gridX, gridY int, floor int) Point3D {
	// Convert grid to local meters
	localX := float64(gridX) * ct.gridScale
	localY := float64(gridY) * ct.gridScale
	localZ := float64(floor) * ct.floorHeight

	// Apply rotation if needed
	if ct.rotation != 0 {
		rad := ct.rotation * math.Pi / 180
		cos := math.Cos(rad)
		sin := math.Sin(rad)

		rotX := localX*cos - localY*sin
		rotY := localX*sin + localY*cos

		localX = rotX
		localY = rotY
	}

	// Add building origin offset
	return Point3D{
		X: localX + ct.localOrigin.X,
		Y: localY + ct.localOrigin.Y,
		Z: localZ + ct.localOrigin.Z,
	}
}

// WorldToGrid converts world coordinates to grid coordinates
func (ct *CoordinateTranslator) WorldToGrid(world Point3D) (gridX, gridY, floor int) {
	// Remove building origin offset
	local := Point3D{
		X: world.X - ct.localOrigin.X,
		Y: world.Y - ct.localOrigin.Y,
		Z: world.Z - ct.localOrigin.Z,
	}

	// Apply inverse rotation if needed
	if ct.rotation != 0 {
		rad := -ct.rotation * math.Pi / 180
		cos := math.Cos(rad)
		sin := math.Sin(rad)

		rotX := local.X*cos - local.Y*sin
		rotY := local.X*sin + local.Y*cos

		local.X = rotX
		local.Y = rotY
	}

	// Convert to grid units
	gridX = int(math.Round(local.X / ct.gridScale))
	gridY = int(math.Round(local.Y / ct.gridScale))
	floor = int(math.Round(local.Z / ct.floorHeight))

	return gridX, gridY, floor
}

// GPSToLocal converts GPS coordinates to local building coordinates
func (ct *CoordinateTranslator) GPSToLocal(gps GPSCoordinate) Point3D {
	// Simplified conversion - in production would use proper geodetic calculations
	// Using approximate meter conversion for small areas
	latDiff := gps.Latitude - ct.buildingOrigin.Latitude
	lonDiff := gps.Longitude - ct.buildingOrigin.Longitude

	// Approximate meters per degree at latitude
	metersPerDegreeLat := 111132.92
	metersPerDegreeLon := 111132.92 * math.Cos(ct.buildingOrigin.Latitude*math.Pi/180)

	localX := lonDiff * metersPerDegreeLon
	localY := latDiff * metersPerDegreeLat
	localZ := gps.Altitude - ct.buildingOrigin.Altitude

	return Point3D{X: localX, Y: localY, Z: localZ}
}

// LocalToGPS converts local building coordinates to GPS
func (ct *CoordinateTranslator) LocalToGPS(local Point3D) GPSCoordinate {
	// Simplified conversion - inverse of GPSToLocal
	metersPerDegreeLat := 111132.92
	metersPerDegreeLon := 111132.92 * math.Cos(ct.buildingOrigin.Latitude*math.Pi/180)

	latDiff := local.Y / metersPerDegreeLat
	lonDiff := local.X / metersPerDegreeLon

	return GPSCoordinate{
		Latitude:  ct.buildingOrigin.Latitude + latDiff,
		Longitude: ct.buildingOrigin.Longitude + lonDiff,
		Altitude:  ct.buildingOrigin.Altitude + local.Z,
	}
}

// ARToWorld converts AR coordinates to world coordinates
func (ct *CoordinateTranslator) ARToWorld(arCoord ARCoordinate, anchor SpatialAnchor) Point3D {
	// Apply anchor transform to AR position
	worldPos := anchor.WorldPosition.Add(arCoord.Position)
	return worldPos
}

// WorldToAR converts world coordinates to AR coordinates
func (ct *CoordinateTranslator) WorldToAR(world Point3D, anchor SpatialAnchor) ARCoordinate {
	// Calculate position relative to anchor
	arPos := world.Sub(anchor.WorldPosition)
	return ARCoordinate{
		Position: arPos,
		AnchorID: anchor.ID,
	}
}

// IsSignificantMovement determines if movement requires BIM update
func (ct *CoordinateTranslator) IsSignificantMovement(oldPos, newPos Point3D) bool {
	// Calculate grid delta
	oldX, oldY, oldFloor := ct.WorldToGrid(oldPos)
	newX, newY, newFloor := ct.WorldToGrid(newPos)

	// Check floor change
	if oldFloor != newFloor {
		return true
	}

	// Check grid movement
	gridDelta := math.Sqrt(float64((newX-oldX)*(newX-oldX) + (newY-oldY)*(newY-oldY)))
	if gridDelta >= ct.thresholds.GridUnitThreshold {
		return true
	}

	// Check absolute distance for room change detection
	distance := oldPos.DistanceTo(newPos)
	if distance >= ct.thresholds.RoomChangeThreshold {
		// Additional logic would check room boundaries here
		return true
	}

	return false
}

// CalculateGridDelta calculates the movement in grid units
func (ct *CoordinateTranslator) CalculateGridDelta(from, to Point3D) GridDelta {
	fromX, fromY, fromFloor := ct.WorldToGrid(from)
	toX, toY, toFloor := ct.WorldToGrid(to)

	return GridDelta{
		DX: toX - fromX,
		DY: toY - fromY,
		DZ: toFloor - fromFloor,
	}
}

// GetTransform returns the transformation matrix for the building
func (ct *CoordinateTranslator) GetTransform() Transform {
	return Transform{
		Translation: ct.localOrigin,
		Rotation:    [3]float64{0, 0, ct.rotation},
		Scale:       1.0,
	}
}

// ApplyTransform applies a transformation to a point
func (ct *CoordinateTranslator) ApplyTransform(point Point3D, transform Transform) Point3D {
	return transform.Apply(point)
}

// InverseTransform calculates the inverse of a transformation
func (ct *CoordinateTranslator) InverseTransform(transform Transform) Transform {
	return Transform{
		Translation: Point3D{
			X: -transform.Translation.X,
			Y: -transform.Translation.Y,
			Z: -transform.Translation.Z,
		},
		Rotation: [3]float64{
			-transform.Rotation[0],
			-transform.Rotation[1],
			-transform.Rotation[2],
		},
		Scale: 1.0 / transform.Scale,
	}
}

// clearCache clears the transform cache
func (ct *CoordinateTranslator) clearCache() {
	ct.cacheMutex.Lock()
	defer ct.cacheMutex.Unlock()
	ct.transformCache = make(map[string]*Transform)
}

// GetGridBounds returns the grid bounds for a bounding box
func (ct *CoordinateTranslator) GetGridBounds(bbox BoundingBox) (minGrid, maxGrid GridCoordinate) {
	minX, minY, minFloor := ct.WorldToGrid(bbox.Min)
	maxX, maxY, maxFloor := ct.WorldToGrid(bbox.Max)

	return GridCoordinate{X: minX, Y: minY, Floor: minFloor},
		GridCoordinate{X: maxX, Y: maxY, Floor: maxFloor}
}

// EstimateAccuracy estimates position accuracy based on source
func EstimateAccuracy(source string) float64 {
	switch source {
	case "lidar":
		return 0.01 // 1cm
	case "ar_verified":
		return 0.05 // 5cm
	case "ifc":
		return 0.5 // 50cm
	case "pdf":
		return 2.0 // 2m
	default:
		return 5.0 // 5m
	}
}

// String returns a string representation of the translator configuration
func (ct *CoordinateTranslator) String() string {
	return fmt.Sprintf("CoordinateTranslator[building=%s, gridScale=%.2fm, floorHeight=%.2fm, rotation=%.1f°]",
		ct.buildingID, ct.gridScale, ct.floorHeight, ct.rotation)
}
