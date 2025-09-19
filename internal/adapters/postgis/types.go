package postgis

import "time"

// Equipment represents equipment in PostGIS
type Equipment struct {
	ID         string                 `db:"id"`
	Name       string                 `db:"name"`
	Type       string                 `db:"type"`
	Location   Position               `db:"location"`
	Status     string                 `db:"status"`
	BuildingID string                 `db:"building_id"`
	Path       string                 `db:"path"`
	Confidence float64                `db:"confidence"`
	Metadata   map[string]interface{} `db:"metadata"`
	Created    time.Time              `db:"created"`
	Updated    time.Time              `db:"updated"`
}

// Position represents a geographic position
type Position struct {
	Lon float64 `db:"lon"`
	Lat float64 `db:"lat"`
	Alt float64 `db:"alt"`
}