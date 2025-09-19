package spatial

import (
	"fmt"
	"math"
)

// CoordinateSystem represents the unified spatial coordinate system
// All coordinates are stored in WGS84 (SRID 4326) in PostGIS
type CoordinateSystem struct {
	// WGS84 coordinates (source of truth in database)
	WGS84 WGS84Coordinate `json:"wgs84"`

	// Building-relative coordinates in millimeters
	Local *LocalCoordinate `json:"local,omitempty"`

	// Display-only grid coordinates (generated on demand)
	Grid *GridCoordinate `json:"grid,omitempty"`
}

// WGS84Coordinate represents GPS coordinates (SRID 4326)
// This is the source of truth stored in PostGIS
type WGS84Coordinate struct {
	Longitude float64 `json:"longitude"` // X in PostGIS
	Latitude  float64 `json:"latitude"`  // Y in PostGIS
	Altitude  float64 `json:"altitude"`  // Z in PostGIS (meters above sea level)
}

// LocalCoordinate represents building-relative position in millimeters
// Used for AR/field work precision
type LocalCoordinate struct {
	X float64 `json:"x"` // millimeters from building origin
	Y float64 `json:"y"` // millimeters from building origin
	Z float64 `json:"z"` // millimeters above floor level
}

// GridCoordinate is for terminal display only (not stored)
// Generated on demand for ASCII visualization
type GridCoordinate struct {
	X     int `json:"x"`     // Grid column
	Y     int `json:"y"`     // Grid row
	Floor int `json:"floor"` // Floor number
}

// ToPostGIS converts to PostGIS geometry string
func (cs *CoordinateSystem) ToPostGIS() string {
	return fmt.Sprintf("ST_SetSRID(ST_MakePoint(%f, %f, %f), 4326)",
		cs.WGS84.Longitude, cs.WGS84.Latitude, cs.WGS84.Altitude)
}

// ToGeoJSON converts to GeoJSON Point
func (cs *CoordinateSystem) ToGeoJSON() map[string]interface{} {
	return map[string]interface{}{
		"type": "Point",
		"coordinates": []float64{
			cs.WGS84.Longitude,
			cs.WGS84.Latitude,
			cs.WGS84.Altitude,
		},
	}
}

// Validate checks if coordinates are valid
func (cs *CoordinateSystem) Validate() error {
	if cs.WGS84.Latitude < -90 || cs.WGS84.Latitude > 90 {
		return fmt.Errorf("invalid latitude: %f", cs.WGS84.Latitude)
	}

	if cs.WGS84.Longitude < -180 || cs.WGS84.Longitude > 180 {
		return fmt.Errorf("invalid longitude: %f", cs.WGS84.Longitude)
	}

	// Altitude can be negative (below sea level) but should be reasonable
	if cs.WGS84.Altitude < -1000 || cs.WGS84.Altitude > 10000 {
		return fmt.Errorf("invalid altitude: %f", cs.WGS84.Altitude)
	}

	return nil
}

// DistanceTo calculates the distance to another coordinate in meters
// Uses Haversine formula for spherical distance
func (cs *CoordinateSystem) DistanceTo(other *CoordinateSystem) float64 {
	const earthRadius = 6371000 // meters

	lat1 := cs.WGS84.Latitude * math.Pi / 180
	lat2 := other.WGS84.Latitude * math.Pi / 180
	deltaLat := (other.WGS84.Latitude - cs.WGS84.Latitude) * math.Pi / 180
	deltaLon := (other.WGS84.Longitude - cs.WGS84.Longitude) * math.Pi / 180

	a := math.Sin(deltaLat/2)*math.Sin(deltaLat/2) +
		math.Cos(lat1)*math.Cos(lat2)*
			math.Sin(deltaLon/2)*math.Sin(deltaLon/2)

	c := 2 * math.Atan2(math.Sqrt(a), math.Sqrt(1-a))

	horizontalDistance := earthRadius * c

	// Add vertical distance
	verticalDistance := math.Abs(other.WGS84.Altitude - cs.WGS84.Altitude)

	return math.Sqrt(horizontalDistance*horizontalDistance + verticalDistance*verticalDistance)
}

// NewCoordinateSystem creates a new coordinate system from WGS84 coordinates
func NewCoordinateSystem(lon, lat, alt float64) *CoordinateSystem {
	return &CoordinateSystem{
		WGS84: WGS84Coordinate{
			Longitude: lon,
			Latitude:  lat,
			Altitude:  alt,
		},
	}
}

// SetLocalPosition sets the building-relative position
func (cs *CoordinateSystem) SetLocalPosition(x, y, z float64) {
	cs.Local = &LocalCoordinate{
		X: x,
		Y: y,
		Z: z,
	}
}

// GenerateGridPosition generates grid coordinates for display
// This is computed on demand and not stored
func (cs *CoordinateSystem) GenerateGridPosition(gridScale float64, floorHeight float64) {
	if cs.Local == nil {
		return
	}

	// Convert millimeters to grid units
	gridX := int(cs.Local.X / (gridScale * 1000))
	gridY := int(cs.Local.Y / (gridScale * 1000))
	floor := int(cs.Local.Z / (floorHeight * 1000))

	cs.Grid = &GridCoordinate{
		X:     gridX,
		Y:     gridY,
		Floor: floor,
	}
}