package spatial

import (
	"math"
)

// Transformer handles coordinate transformations between different systems
type Transformer struct {
	// Building origin in WGS84 coordinates
	Origin WGS84Coordinate

	// Building rotation from north (degrees)
	Rotation float64

	// Grid scale in meters per grid unit
	GridScale float64

	// Floor height in meters
	FloorHeight float64
}

// NewTransformer creates a new coordinate transformer for a building
func NewTransformer(originLat, originLon, originAlt, rotation float64) *Transformer {
	return &Transformer{
		Origin: WGS84Coordinate{
			Latitude:  originLat,
			Longitude: originLon,
			Altitude:  originAlt,
		},
		Rotation:    rotation,
		GridScale:   0.5, // Default 0.5m per grid unit
		FloorHeight: 3.0, // Default 3m between floors
	}
}

// WGS84ToLocal converts WGS84 coordinates to building-local millimeters
func (t *Transformer) WGS84ToLocal(wgs84 WGS84Coordinate) LocalCoordinate {
	// Calculate distance from origin using equirectangular approximation
	// This is accurate enough for building-scale distances

	// Convert to radians
	lat1 := t.Origin.Latitude * math.Pi / 180
	lon1 := t.Origin.Longitude * math.Pi / 180
	lat2 := wgs84.Latitude * math.Pi / 180
	lon2 := wgs84.Longitude * math.Pi / 180

	// Calculate x and y distances in meters
	x := (lon2 - lon1) * math.Cos((lat1+lat2)/2) * 6371000
	y := (lat2 - lat1) * 6371000
	z := wgs84.Altitude - t.Origin.Altitude

	// Apply building rotation
	rotRad := t.Rotation * math.Pi / 180
	xRotated := x*math.Cos(rotRad) - y*math.Sin(rotRad)
	yRotated := x*math.Sin(rotRad) + y*math.Cos(rotRad)

	// Convert to millimeters
	return LocalCoordinate{
		X: xRotated * 1000,
		Y: yRotated * 1000,
		Z: z * 1000,
	}
}

// LocalToWGS84 converts building-local millimeters to WGS84 coordinates
func (t *Transformer) LocalToWGS84(local LocalCoordinate) WGS84Coordinate {
	// Convert from millimeters to meters
	x := local.X / 1000
	y := local.Y / 1000
	z := local.Z / 1000

	// Apply inverse rotation
	rotRad := -t.Rotation * math.Pi / 180
	xRotated := x*math.Cos(rotRad) - y*math.Sin(rotRad)
	yRotated := x*math.Sin(rotRad) + y*math.Cos(rotRad)

	// Convert to lat/lon deltas
	latDelta := yRotated / 6371000
	lonDelta := xRotated / (6371000 * math.Cos(t.Origin.Latitude*math.Pi/180))

	// Convert from radians to degrees and add to origin
	return WGS84Coordinate{
		Latitude:  t.Origin.Latitude + (latDelta * 180 / math.Pi),
		Longitude: t.Origin.Longitude + (lonDelta * 180 / math.Pi),
		Altitude:  t.Origin.Altitude + z,
	}
}

// LocalToGrid converts local coordinates to grid position for display
func (t *Transformer) LocalToGrid(local LocalCoordinate) GridCoordinate {
	// Convert millimeters to grid units
	gridX := int(local.X / (t.GridScale * 1000))
	gridY := int(local.Y / (t.GridScale * 1000))
	floor := int(local.Z / (t.FloorHeight * 1000))

	return GridCoordinate{
		X:     gridX,
		Y:     gridY,
		Floor: floor,
	}
}

// GridToLocal converts grid coordinates to local millimeters (approximate)
func (t *Transformer) GridToLocal(grid GridCoordinate) LocalCoordinate {
	// This is approximate since grid coordinates are lossy
	return LocalCoordinate{
		X: float64(grid.X) * t.GridScale * 1000,
		Y: float64(grid.Y) * t.GridScale * 1000,
		Z: float64(grid.Floor) * t.FloorHeight * 1000,
	}
}

// IsSignificantMovement determines if movement requires .bim.txt update
// Only significant movements (>1 grid unit) should trigger file updates
func (t *Transformer) IsSignificantMovement(oldLocal, newLocal LocalCoordinate) bool {
	// Calculate grid positions
	oldGrid := t.LocalToGrid(oldLocal)
	newGrid := t.LocalToGrid(newLocal)

	// Check if grid position changed
	return oldGrid.X != newGrid.X ||
		oldGrid.Y != newGrid.Y ||
		oldGrid.Floor != newGrid.Floor
}

// Transform creates a complete coordinate system from WGS84
func (t *Transformer) Transform(wgs84 WGS84Coordinate) *CoordinateSystem {
	local := t.WGS84ToLocal(wgs84)
	grid := t.LocalToGrid(local)

	return &CoordinateSystem{
		WGS84: wgs84,
		Local: &local,
		Grid:  &grid,
	}
}

// TransformFromLocal creates a complete coordinate system from local coordinates
func (t *Transformer) TransformFromLocal(local LocalCoordinate) *CoordinateSystem {
	wgs84 := t.LocalToWGS84(local)
	grid := t.LocalToGrid(local)

	return &CoordinateSystem{
		WGS84: wgs84,
		Local: &local,
		Grid:  &grid,
	}
}
