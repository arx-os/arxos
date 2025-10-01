package database

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/domain/analytics"
)

// PostGISAnalyticsRepository implements analytics data persistence using PostGIS
type PostGISAnalyticsRepository struct {
	db *sql.DB
}

// NewPostGISAnalyticsRepository creates a new PostGIS analytics repository
func NewPostGISAnalyticsRepository(db *sql.DB) *PostGISAnalyticsRepository {
	return &PostGISAnalyticsRepository{
		db: db,
	}
}

// SaveEnergyDataPoint saves an energy data point to the database
func (r *PostGISAnalyticsRepository) SaveEnergyDataPoint(ctx context.Context, dataPoint analytics.EnergyDataPoint) error {
	query := `
		INSERT INTO energy_data_points (
			timestamp, building_id, space_id, asset_id, energy_type,
			consumption, cost, efficiency, temperature, humidity, occupancy,
			weather_data, metadata
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
	`

	weatherDataJSON, err := json.Marshal(dataPoint.WeatherData)
	if err != nil {
		return fmt.Errorf("failed to marshal weather data: %w", err)
	}

	metadataJSON, err := json.Marshal(dataPoint.Metadata)
	if err != nil {
		return fmt.Errorf("failed to marshal metadata: %w", err)
	}

	_, err = r.db.ExecContext(ctx, query,
		dataPoint.Timestamp,
		dataPoint.BuildingID,
		dataPoint.SpaceID,
		dataPoint.AssetID,
		dataPoint.EnergyType,
		dataPoint.Consumption,
		dataPoint.Cost,
		dataPoint.Efficiency,
		dataPoint.Temperature,
		dataPoint.Humidity,
		dataPoint.Occupancy,
		weatherDataJSON,
		metadataJSON,
	)

	if err != nil {
		return fmt.Errorf("failed to save energy data point: %w", err)
	}

	return nil
}

// GetEnergyDataPoints retrieves energy data points for a building
func (r *PostGISAnalyticsRepository) GetEnergyDataPoints(ctx context.Context, buildingID string, startTime, endTime time.Time) ([]analytics.EnergyDataPoint, error) {
	query := `
		SELECT timestamp, building_id, space_id, asset_id, energy_type,
			   consumption, cost, efficiency, temperature, humidity, occupancy,
			   weather_data, metadata
		FROM energy_data_points
		WHERE building_id = $1 AND timestamp BETWEEN $2 AND $3
		ORDER BY timestamp DESC
	`

	rows, err := r.db.QueryContext(ctx, query, buildingID, startTime, endTime)
	if err != nil {
		return nil, fmt.Errorf("failed to query energy data points: %w", err)
	}
	defer rows.Close()

	var dataPoints []analytics.EnergyDataPoint
	for rows.Next() {
		var dp analytics.EnergyDataPoint
		var weatherDataJSON, metadataJSON []byte

		err := rows.Scan(
			&dp.Timestamp,
			&dp.BuildingID,
			&dp.SpaceID,
			&dp.AssetID,
			&dp.EnergyType,
			&dp.Consumption,
			&dp.Cost,
			&dp.Efficiency,
			&dp.Temperature,
			&dp.Humidity,
			&dp.Occupancy,
			&weatherDataJSON,
			&metadataJSON,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan energy data point: %w", err)
		}

		// Unmarshal JSON fields
		if err := json.Unmarshal(weatherDataJSON, &dp.WeatherData); err != nil {
			return nil, fmt.Errorf("failed to unmarshal weather data: %w", err)
		}

		if err := json.Unmarshal(metadataJSON, &dp.Metadata); err != nil {
			return nil, fmt.Errorf("failed to unmarshal metadata: %w", err)
		}

		dataPoints = append(dataPoints, dp)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating energy data points: %w", err)
	}

	return dataPoints, nil
}

// SaveBaselineData saves baseline energy consumption data
func (r *PostGISAnalyticsRepository) SaveBaselineData(ctx context.Context, baseline analytics.BaselineData) error {
	query := `
		INSERT INTO baseline_data (
			building_id, space_id, asset_id, energy_type,
			baseline_value, variance, confidence_level, last_updated, data_points
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
		ON CONFLICT (building_id, space_id, asset_id, energy_type)
		DO UPDATE SET
			baseline_value = EXCLUDED.baseline_value,
			variance = EXCLUDED.variance,
			confidence_level = EXCLUDED.confidence_level,
			last_updated = EXCLUDED.last_updated,
			data_points = EXCLUDED.data_points
	`

	_, err := r.db.ExecContext(ctx, query,
		baseline.BuildingID,
		baseline.SpaceID,
		baseline.AssetID,
		baseline.EnergyType,
		baseline.BaselineValue,
		baseline.Variance,
		baseline.ConfidenceLevel,
		baseline.LastUpdated,
		baseline.DataPoints,
	)

	if err != nil {
		return fmt.Errorf("failed to save baseline data: %w", err)
	}

	return nil
}

// GetBaselineData retrieves baseline data for a building
func (r *PostGISAnalyticsRepository) GetBaselineData(ctx context.Context, buildingID string) ([]analytics.BaselineData, error) {
	query := `
		SELECT building_id, space_id, asset_id, energy_type,
			   baseline_value, variance, confidence_level, last_updated, data_points
		FROM baseline_data
		WHERE building_id = $1
		ORDER BY last_updated DESC
	`

	rows, err := r.db.QueryContext(ctx, query, buildingID)
	if err != nil {
		return nil, fmt.Errorf("failed to query baseline data: %w", err)
	}
	defer rows.Close()

	var baselines []analytics.BaselineData
	for rows.Next() {
		var baseline analytics.BaselineData

		err := rows.Scan(
			&baseline.BuildingID,
			&baseline.SpaceID,
			&baseline.AssetID,
			&baseline.EnergyType,
			&baseline.BaselineValue,
			&baseline.Variance,
			&baseline.ConfidenceLevel,
			&baseline.LastUpdated,
			&baseline.DataPoints,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan baseline data: %w", err)
		}

		baselines = append(baselines, baseline)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating baseline data: %w", err)
	}

	return baselines, nil
}

// SaveOptimizationRule saves an optimization rule
func (r *PostGISAnalyticsRepository) SaveOptimizationRule(ctx context.Context, rule analytics.OptimizationRule) error {
	query := `
		INSERT INTO optimization_rules (
			id, name, description, condition, action, priority, enabled, created_at, updated_at
		) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
		ON CONFLICT (id)
		DO UPDATE SET
			name = EXCLUDED.name,
			description = EXCLUDED.description,
			condition = EXCLUDED.condition,
			action = EXCLUDED.action,
			priority = EXCLUDED.priority,
			enabled = EXCLUDED.enabled,
			updated_at = EXCLUDED.updated_at
	`

	conditionJSON, err := json.Marshal(rule.Condition)
	if err != nil {
		return fmt.Errorf("failed to marshal condition: %w", err)
	}

	actionJSON, err := json.Marshal(rule.Action)
	if err != nil {
		return fmt.Errorf("failed to marshal action: %w", err)
	}

	_, err = r.db.ExecContext(ctx, query,
		rule.ID,
		rule.Name,
		rule.Description,
		conditionJSON,
		actionJSON,
		rule.Priority,
		rule.Enabled,
		rule.CreatedAt,
		rule.UpdatedAt,
	)

	if err != nil {
		return fmt.Errorf("failed to save optimization rule: %w", err)
	}

	return nil
}

// GetOptimizationRules retrieves optimization rules for a building
func (r *PostGISAnalyticsRepository) GetOptimizationRules(ctx context.Context, buildingID string) ([]analytics.OptimizationRule, error) {
	query := `
		SELECT id, name, description, condition, action, priority, enabled, created_at, updated_at
		FROM optimization_rules
		WHERE enabled = true
		ORDER BY priority ASC
	`

	rows, err := r.db.QueryContext(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to query optimization rules: %w", err)
	}
	defer rows.Close()

	var rules []analytics.OptimizationRule
	for rows.Next() {
		var rule analytics.OptimizationRule
		var conditionJSON, actionJSON []byte

		err := rows.Scan(
			&rule.ID,
			&rule.Name,
			&rule.Description,
			&conditionJSON,
			&actionJSON,
			&rule.Priority,
			&rule.Enabled,
			&rule.CreatedAt,
			&rule.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan optimization rule: %w", err)
		}

		// Unmarshal JSON fields
		if err := json.Unmarshal(conditionJSON, &rule.Condition); err != nil {
			return nil, fmt.Errorf("failed to unmarshal condition: %w", err)
		}

		if err := json.Unmarshal(actionJSON, &rule.Action); err != nil {
			return nil, fmt.Errorf("failed to unmarshal action: %w", err)
		}

		rules = append(rules, rule)
	}

	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("error iterating optimization rules: %w", err)
	}

	return rules, nil
}
