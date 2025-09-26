package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/hardware"
)

// GatewayService implements gateway management for the hardware platform
type GatewayService struct {
	db *database.PostGISDB
}

// NewGatewayService creates a new GatewayService
func NewGatewayService(db *database.PostGISDB) *GatewayService {
	return &GatewayService{db: db}
}

// DeployGateway deploys a new gateway
func (gs *GatewayService) DeployGateway(ctx context.Context, req hardware.DeployGatewayRequest) (*hardware.Gateway, error) {
	// Validate request
	if req.Name == "" {
		return nil, fmt.Errorf("gateway name is required")
	}
	if req.Type == "" {
		return nil, fmt.Errorf("gateway type is required")
	}

	// Create gateway
	query := `
		INSERT INTO gateways (id, name, type, status, config, devices, location, user_id, tier, created_at, updated_at)
		VALUES ($1, $2, $3, 'active', $4, $5, $6, $7, 'hardware', NOW(), NOW())
		RETURNING id, name, type, status, config, devices, location, user_id, created_at, updated_at`

	var gateway hardware.Gateway
	gatewayID := generateGatewayID()

	var configJSON, devicesJSON, locationJSON []byte
	err := gs.db.QueryRow(ctx, query,
		gatewayID,
		req.Name,
		req.Type,
		req.Config,
		req.Devices,
		req.Location,
		common.GetUserIDFromContextSafe(ctx), // Get from context
	).Scan(
		&gateway.ID,
		&gateway.Name,
		&gateway.Type,
		&gateway.Status,
		&configJSON,
		&devicesJSON,
		&locationJSON,
		&gateway.UserID,
		&gateway.CreatedAt,
		&gateway.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to deploy gateway: %w", err)
	}

	// Parse JSON fields
	if err := json.Unmarshal(configJSON, &gateway.Config); err != nil {
		gateway.Config = hardware.GatewayConfig{}
	}
	if err := json.Unmarshal(devicesJSON, &gateway.Devices); err != nil {
		gateway.Devices = []string{}
	}
	if err := json.Unmarshal(locationJSON, &gateway.Location); err != nil {
		gateway.Location = hardware.DeviceLocation{}
	}

	return &gateway, nil
}

// GetGateway retrieves a gateway by ID
func (gs *GatewayService) GetGateway(ctx context.Context, gatewayID string) (*hardware.Gateway, error) {
	query := `
		SELECT id, name, type, status, config, devices, location, user_id, created_at, updated_at
		FROM gateways
		WHERE id = $1 AND tier = 'hardware'
	`

	var gateway hardware.Gateway
	var configJSON, devicesJSON, locationJSON []byte
	err := gs.db.QueryRow(ctx, query, gatewayID).Scan(
		&gateway.ID,
		&gateway.Name,
		&gateway.Type,
		&gateway.Status,
		&configJSON,
		&devicesJSON,
		&locationJSON,
		&gateway.UserID,
		&gateway.CreatedAt,
		&gateway.UpdatedAt,
	)

	if err != nil {
		if err.Error() == "no rows in result set" {
			return nil, fmt.Errorf("gateway not found")
		}
		return nil, fmt.Errorf("failed to get gateway: %w", err)
	}

	// Parse JSON fields
	if err := json.Unmarshal(configJSON, &gateway.Config); err != nil {
		gateway.Config = hardware.GatewayConfig{}
	}
	if err := json.Unmarshal(devicesJSON, &gateway.Devices); err != nil {
		gateway.Devices = []string{}
	}
	if err := json.Unmarshal(locationJSON, &gateway.Location); err != nil {
		gateway.Location = hardware.DeviceLocation{}
	}

	return &gateway, nil
}

// ListGateways lists gateways for a user
func (gs *GatewayService) ListGateways(ctx context.Context, userID string) ([]*hardware.Gateway, error) {
	query := `
		SELECT id, name, type, status, config, devices, location, user_id, created_at, updated_at
		FROM gateways
		WHERE tier = 'hardware'
		ORDER BY created_at DESC
	`

	rows, err := gs.db.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to list gateways: %w", err)
	}
	defer rows.Close()

	var gateways []*hardware.Gateway
	for rows.Next() {
		var gateway hardware.Gateway
		var configJSON, devicesJSON, locationJSON []byte
		err := rows.Scan(
			&gateway.ID,
			&gateway.Name,
			&gateway.Type,
			&gateway.Status,
			&configJSON,
			&devicesJSON,
			&locationJSON,
			&gateway.UserID,
			&gateway.CreatedAt,
			&gateway.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan gateway: %w", err)
		}

		// Parse JSON fields
		if err := json.Unmarshal(configJSON, &gateway.Config); err != nil {
			gateway.Config = hardware.GatewayConfig{}
		}
		if err := json.Unmarshal(devicesJSON, &gateway.Devices); err != nil {
			gateway.Devices = []string{}
		}
		if err := json.Unmarshal(locationJSON, &gateway.Location); err != nil {
			gateway.Location = hardware.DeviceLocation{}
		}

		gateways = append(gateways, &gateway)
	}

	return gateways, nil
}

// UpdateGateway updates gateway configuration
func (gs *GatewayService) UpdateGateway(ctx context.Context, gatewayID string, config hardware.GatewayConfig) (*hardware.Gateway, error) {
	// Get existing gateway
	gateway, err := gs.GetGateway(ctx, gatewayID)
	if err != nil {
		return nil, fmt.Errorf("failed to get existing gateway: %w", err)
	}

	// Update configuration
	gateway.Config = config

	// Update in database
	query := `
		UPDATE gateways 
		SET config = $1, updated_at = NOW()
		WHERE id = $2 AND tier = 'hardware'
	`

	_, err = gs.db.Exec(ctx, query, config, gatewayID)
	if err != nil {
		return nil, fmt.Errorf("failed to update gateway: %w", err)
	}

	return gateway, nil
}

// ConfigureGateway configures gateway settings
func (gs *GatewayService) ConfigureGateway(ctx context.Context, gatewayID string, config hardware.GatewayConfig) error {
	// Validate gateway exists
	_, err := gs.GetGateway(ctx, gatewayID)
	if err != nil {
		return fmt.Errorf("gateway not found: %w", err)
	}

	// Update configuration
	query := `
		UPDATE gateways 
		SET config = $1, updated_at = NOW()
		WHERE id = $2 AND tier = 'hardware'
	`

	_, err = gs.db.Exec(ctx, query, config, gatewayID)
	if err != nil {
		return fmt.Errorf("failed to configure gateway: %w", err)
	}

	return nil
}

// DeleteGateway removes a gateway
func (gs *GatewayService) DeleteGateway(ctx context.Context, gatewayID string) error {
	_, err := gs.db.Exec(ctx, "DELETE FROM gateways WHERE id = $1 AND tier = 'hardware'", gatewayID)
	if err != nil {
		return fmt.Errorf("failed to delete gateway: %w", err)
	}
	return nil
}

// GetGatewayStatus retrieves gateway status information
func (gs *GatewayService) GetGatewayStatus(ctx context.Context, gatewayID string) (*hardware.GatewayStatus, error) {
	// Validate gateway exists
	gateway, err := gs.GetGateway(ctx, gatewayID)
	if err != nil {
		return nil, fmt.Errorf("gateway not found: %w", err)
	}

	// Count connected devices
	var connectedDevices int
	err = gs.db.QueryRow(ctx, "SELECT COUNT(*) FROM hardware_devices WHERE id = ANY($1)", gateway.Devices).Scan(&connectedDevices)
	if err != nil {
		connectedDevices = 0
	}

	// Create gateway status
	status := &hardware.GatewayStatus{
		GatewayID:        gateway.ID,
		Status:           gateway.Status,
		LastSeen:         time.Now(),
		ConnectedDevices: connectedDevices,
		Health:           "healthy",
		Metrics:          make(map[string]interface{}),
		Errors:           []string{},
		LastUpdated:      time.Now(),
	}

	// Add some sample metrics
	status.Metrics["uptime"] = "48h"
	status.Metrics["cpu_usage"] = 25.5
	status.Metrics["memory_usage"] = 60.0
	status.Metrics["network_latency"] = 15
	status.Metrics["data_throughput"] = 1024

	return status, nil
}

// Helper functions

func generateGatewayID() string {
	return fmt.Sprintf("gw_%d", time.Now().UnixNano())
}
