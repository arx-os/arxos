package database

import "time"

// SpatialAnchor represents a spatial reference point for equipment or features
type SpatialAnchor struct {
	ID           string
	BuildingID   string
	EquipmentID  string
	Position     Point3D
	Confidence   float64
	LastScanned  time.Time
	ScanMetadata map[string]interface{}
}

// Point3D represents a 3D point in space
type Point3D struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}