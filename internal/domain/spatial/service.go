package spatial

import (
	"context"
	"time"

	"github.com/google/uuid"
)

// Service defines the interface for spatial business logic following Clean Architecture principles
type Service interface {
	// Spatial queries
	FindNearby(ctx context.Context, req FindNearbyRequest) ([]*SpatialResult, error)
	FindWithinBounds(ctx context.Context, req FindWithinBoundsRequest) ([]*SpatialResult, error)
	FindByFloor(ctx context.Context, buildingID uuid.UUID, floor int) ([]*SpatialResult, error)

	// Spatial operations
	CalculateDistance(ctx context.Context, from, to *Point) (float64, error)
	CalculateArea(ctx context.Context, points []*Point) (float64, error)
	CalculatePerimeter(ctx context.Context, points []*Point) (float64, error)

	// Spatial indexing
	RebuildSpatialIndex(ctx context.Context, buildingID uuid.UUID) error
	GetSpatialStats(ctx context.Context, buildingID uuid.UUID) (*SpatialStats, error)
}

// Point represents a 3D point in space
type Point struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// SpatialResult represents a spatial query result
type SpatialResult struct {
	ID       uuid.UUID              `json:"id"`
	Type     string                 `json:"type"`
	Name     string                 `json:"name"`
	Location *Point                 `json:"location"`
	Distance float64                `json:"distance,omitempty"`
	Metadata map[string]interface{} `json:"metadata"`
}

// FindNearbyRequest represents a request to find nearby items
type FindNearbyRequest struct {
	Center   *Point  `json:"center" validate:"required"`
	Radius   float64 `json:"radius" validate:"required,min=0"`
	ItemType string  `json:"item_type,omitempty"`
	Limit    int     `json:"limit" validate:"min=1,max=100"`
}

// FindWithinBoundsRequest represents a request to find items within bounds
type FindWithinBoundsRequest struct {
	MinPoint *Point `json:"min_point" validate:"required"`
	MaxPoint *Point `json:"max_point" validate:"required"`
	ItemType string `json:"item_type,omitempty"`
	Limit    int    `json:"limit" validate:"min=1,max=100"`
}

// SpatialStats represents spatial statistics
type SpatialStats struct {
	TotalItems     int       `json:"total_items"`
	TotalArea      float64   `json:"total_area"`
	AverageDensity float64   `json:"average_density"`
	LastIndexed    time.Time `json:"last_indexed"`
}
