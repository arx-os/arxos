package database

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"github.com/joelpate/arxos/internal/common/logger"
)

// SpatialAnchor represents an AR anchor in 3D space
type SpatialAnchor struct {
	ID            string
	BuildingUUID  string
	EquipmentPath string
	X             float64 // meters from origin
	Y             float64
	Z             float64
	Floor         int
	Rotation      Quaternion
	Platform      string    // ARKit, ARCore
	AnchorData    []byte    // Raw platform-specific data
	CreatedAt     time.Time
	UpdatedAt     time.Time
	CreatedBy     string
}

// Quaternion represents a rotation in 3D space
type Quaternion struct {
	X, Y, Z, W float64
}

// SpatialZone represents a bounded area in a building
type SpatialZone struct {
	ID           string
	BuildingUUID string
	Name         string
	Type         string // room, floor, area, zone
	MinX, MinY   float64
	MaxX, MaxY   float64
	Floor        int
}

// SaveSpatialAnchor saves or updates an AR anchor
func (s *SQLiteDB) SaveSpatialAnchor(ctx context.Context, anchor *SpatialAnchor) error {
	query := `
		INSERT INTO spatial_anchors (
			id, building_uuid, equipment_path,
			x_meters, y_meters, z_meters, floor,
			rotation_x, rotation_y, rotation_z, rotation_w,
			platform, anchor_data, created_by
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
		ON CONFLICT(building_uuid, equipment_path) DO UPDATE SET
			x_meters = excluded.x_meters,
			y_meters = excluded.y_meters,
			z_meters = excluded.z_meters,
			floor = excluded.floor,
			rotation_x = excluded.rotation_x,
			rotation_y = excluded.rotation_y,
			rotation_z = excluded.rotation_z,
			rotation_w = excluded.rotation_w,
			platform = excluded.platform,
			anchor_data = excluded.anchor_data,
			updated_at = CURRENT_TIMESTAMP
	`

	_, err := s.db.ExecContext(ctx, query,
		anchor.ID, anchor.BuildingUUID, anchor.EquipmentPath,
		anchor.X, anchor.Y, anchor.Z, anchor.Floor,
		anchor.Rotation.X, anchor.Rotation.Y, anchor.Rotation.Z, anchor.Rotation.W,
		anchor.Platform, anchor.AnchorData, anchor.CreatedBy,
	)

	if err != nil {
		return fmt.Errorf("failed to save spatial anchor: %w", err)
	}

	logger.Debug("Saved spatial anchor for %s at (%.2f, %.2f) floor %d",
		anchor.EquipmentPath, anchor.X, anchor.Y, anchor.Floor)

	return nil
}

// GetSpatialAnchor retrieves an anchor by equipment path
func (s *SQLiteDB) GetSpatialAnchor(ctx context.Context, buildingUUID, equipmentPath string) (*SpatialAnchor, error) {
	query := `
		SELECT id, building_uuid, equipment_path,
			x_meters, y_meters, z_meters, floor,
			rotation_x, rotation_y, rotation_z, rotation_w,
			platform, anchor_data, created_at, updated_at, created_by
		FROM spatial_anchors
		WHERE building_uuid = ? AND equipment_path = ?
	`

	anchor := &SpatialAnchor{}
	err := s.db.QueryRowContext(ctx, query, buildingUUID, equipmentPath).Scan(
		&anchor.ID, &anchor.BuildingUUID, &anchor.EquipmentPath,
		&anchor.X, &anchor.Y, &anchor.Z, &anchor.Floor,
		&anchor.Rotation.X, &anchor.Rotation.Y, &anchor.Rotation.Z, &anchor.Rotation.W,
		&anchor.Platform, &anchor.AnchorData,
		&anchor.CreatedAt, &anchor.UpdatedAt, &anchor.CreatedBy,
	)

	if err == sql.ErrNoRows {
		return nil, fmt.Errorf("anchor not found")
	}
	if err != nil {
		return nil, fmt.Errorf("failed to get anchor: %w", err)
	}

	return anchor, nil
}

// FindNearbyAnchors finds anchors within a radius (simple 2D for SQLite)
func (s *SQLiteDB) FindNearbyAnchors(ctx context.Context, buildingUUID string, x, y float64, floor int, radiusMeters float64) ([]*SpatialAnchor, error) {
	// Simple Euclidean distance for SQLite
	// When migrating to PostGIS, use ST_DWithin
	query := `
		SELECT id, building_uuid, equipment_path,
			x_meters, y_meters, z_meters, floor,
			rotation_x, rotation_y, rotation_z, rotation_w,
			platform, anchor_data, created_at, updated_at, created_by
		FROM spatial_anchors
		WHERE building_uuid = ?
			AND floor = ?
			AND ((x_meters - ?) * (x_meters - ?) + (y_meters - ?) * (y_meters - ?)) <= (? * ?)
	`

	rows, err := s.db.QueryContext(ctx, query,
		buildingUUID, floor, x, x, y, y, radiusMeters, radiusMeters)
	if err != nil {
		return nil, fmt.Errorf("failed to query nearby anchors: %w", err)
	}
	defer rows.Close()

	var anchors []*SpatialAnchor
	for rows.Next() {
		anchor := &SpatialAnchor{}
		err := rows.Scan(
			&anchor.ID, &anchor.BuildingUUID, &anchor.EquipmentPath,
			&anchor.X, &anchor.Y, &anchor.Z, &anchor.Floor,
			&anchor.Rotation.X, &anchor.Rotation.Y, &anchor.Rotation.Z, &anchor.Rotation.W,
			&anchor.Platform, &anchor.AnchorData,
			&anchor.CreatedAt, &anchor.UpdatedAt, &anchor.CreatedBy,
		)
		if err != nil {
			logger.Warn("Failed to scan anchor: %v", err)
			continue
		}
		anchors = append(anchors, anchor)
	}

	return anchors, nil
}

// GetAnchorsInZone retrieves all anchors within a spatial zone
func (s *SQLiteDB) GetAnchorsInZone(ctx context.Context, zone *SpatialZone) ([]*SpatialAnchor, error) {
	query := `
		SELECT id, building_uuid, equipment_path,
			x_meters, y_meters, z_meters, floor,
			rotation_x, rotation_y, rotation_z, rotation_w,
			platform, anchor_data, created_at, updated_at, created_by
		FROM spatial_anchors
		WHERE building_uuid = ?
			AND floor = ?
			AND x_meters BETWEEN ? AND ?
			AND y_meters BETWEEN ? AND ?
	`

	rows, err := s.db.QueryContext(ctx, query,
		zone.BuildingUUID, zone.Floor,
		zone.MinX, zone.MaxX,
		zone.MinY, zone.MaxY)
	if err != nil {
		return nil, fmt.Errorf("failed to query zone anchors: %w", err)
	}
	defer rows.Close()

	var anchors []*SpatialAnchor
	for rows.Next() {
		anchor := &SpatialAnchor{}
		err := rows.Scan(
			&anchor.ID, &anchor.BuildingUUID, &anchor.EquipmentPath,
			&anchor.X, &anchor.Y, &anchor.Z, &anchor.Floor,
			&anchor.Rotation.X, &anchor.Rotation.Y, &anchor.Rotation.Z, &anchor.Rotation.W,
			&anchor.Platform, &anchor.AnchorData,
			&anchor.CreatedAt, &anchor.UpdatedAt, &anchor.CreatedBy,
		)
		if err != nil {
			logger.Warn("Failed to scan anchor: %v", err)
			continue
		}
		anchors = append(anchors, anchor)
	}

	return anchors, nil
}

// DeleteSpatialAnchor removes an anchor
func (s *SQLiteDB) DeleteSpatialAnchor(ctx context.Context, buildingUUID, equipmentPath string) error {
	query := `DELETE FROM spatial_anchors WHERE building_uuid = ? AND equipment_path = ?`

	result, err := s.db.ExecContext(ctx, query, buildingUUID, equipmentPath)
	if err != nil {
		return fmt.Errorf("failed to delete anchor: %w", err)
	}

	rows, _ := result.RowsAffected()
	if rows == 0 {
		return fmt.Errorf("anchor not found")
	}

	return nil
}