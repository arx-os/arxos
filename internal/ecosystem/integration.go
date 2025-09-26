package ecosystem

import (
	"context"
	"fmt"

	"github.com/arx-os/arxos/internal/database"
)

// EcosystemIntegration integrates all three tiers into a cohesive system
type EcosystemIntegration struct {
	db          *database.PostGISDB
	coreService CoreService
	manager     *Manager
}

// NewEcosystemIntegration creates a new ecosystem integration
func NewEcosystemIntegration(
	db *database.PostGISDB,
	coreService CoreService,
) *EcosystemIntegration {

	// Create ecosystem manager
	manager := NewManager(coreService, nil, nil)

	return &EcosystemIntegration{
		db:          db,
		coreService: coreService,
		manager:     manager,
	}
}

// InitializeEcosystem initializes the three-tier ecosystem
func (ei *EcosystemIntegration) InitializeEcosystem(ctx context.Context) error {
	// Initialize core tier (always available)
	if err := ei.initializeCoreTier(ctx); err != nil {
		return fmt.Errorf("failed to initialize core tier: %w", err)
	}

	// Initialize hardware tier (freemium)
	if err := ei.initializeHardwareTier(ctx); err != nil {
		return fmt.Errorf("failed to initialize hardware tier: %w", err)
	}

	// Initialize workflow tier (paid)
	if err := ei.initializeWorkflowTier(ctx); err != nil {
		return fmt.Errorf("failed to initialize workflow tier: %w", err)
	}

	return nil
}

// initializeCoreTier sets up the core tier (FREE)
func (ei *EcosystemIntegration) initializeCoreTier(ctx context.Context) error {
	// Core tier is always available - no special initialization needed
	// Just ensure the tier exists in the database
	return ei.ensureTierExists(ctx, TierCore)
}

// initializeHardwareTier sets up the hardware tier (FREEMIUM)
func (ei *EcosystemIntegration) initializeHardwareTier(ctx context.Context) error {
	// Ensure hardware tier exists
	if err := ei.ensureTierExists(ctx, TierHardware); err != nil {
		return err
	}

	return nil
}

// initializeWorkflowTier sets up the workflow tier (PAID)
func (ei *EcosystemIntegration) initializeWorkflowTier(ctx context.Context) error {
	// Ensure workflow tier exists
	if err := ei.ensureTierExists(ctx, TierWorkflow); err != nil {
		return err
	}

	return nil
}

// ensureTierExists ensures a tier exists in the database
func (ei *EcosystemIntegration) ensureTierExists(ctx context.Context, tier Tier) error {
	query := `
		INSERT INTO ecosystem_tiers (name, description, price, features, limits, api_endpoints)
		SELECT $1, $2, $3, $4, $5, $6
		WHERE NOT EXISTS (SELECT 1 FROM ecosystem_tiers WHERE name = $1)
	`

	tierInfo := GetTierInfo(tier)

	_, err := ei.db.Exec(ctx, query,
		string(tier),
		tierInfo.Description,
		tierInfo.Price,
		tierInfo.Features,
		tierInfo.Limits,
		tierInfo.APIEndpoints,
	)

	if err != nil {
		return fmt.Errorf("failed to ensure tier exists: %w", err)
	}

	return nil
}

// initializeDefaultTemplates creates default device templates
func (ei *EcosystemIntegration) initializeDefaultTemplates(ctx context.Context) error {
	// TODO: Implement default template creation
	return nil
}

// initializeDefaultWorkflows creates default workflow templates
func (ei *EcosystemIntegration) initializeDefaultWorkflows(ctx context.Context) error {
	// TODO: Implement default workflow creation
	return nil
}

// GetEcosystemStatus returns the current status of the ecosystem
func (ei *EcosystemIntegration) GetEcosystemStatus(ctx context.Context) (*EcosystemStatus, error) {
	status := &EcosystemStatus{
		Tiers: make(map[string]TierStatus),
	}

	// Check core tier status
	coreStatus, err := ei.getTierStatus(ctx, TierCore)
	if err != nil {
		return nil, fmt.Errorf("failed to get core tier status: %w", err)
	}
	status.Tiers["core"] = *coreStatus

	// Check hardware tier status
	hardwareStatus, err := ei.getTierStatus(ctx, TierHardware)
	if err != nil {
		return nil, fmt.Errorf("failed to get hardware tier status: %w", err)
	}
	status.Tiers["hardware"] = *hardwareStatus

	// Check workflow tier status
	workflowStatus, err := ei.getTierStatus(ctx, TierWorkflow)
	if err != nil {
		return nil, fmt.Errorf("failed to get workflow tier status: %w", err)
	}
	status.Tiers["workflow"] = *workflowStatus

	return status, nil
}

// getTierStatus returns the status of a specific tier
func (ei *EcosystemIntegration) getTierStatus(ctx context.Context, tier Tier) (*TierStatus, error) {
	// Get tier info
	tierInfo := GetTierInfo(tier)

	// Get user count for this tier
	userCountQuery := `
		SELECT COUNT(*) 
		FROM user_tiers 
		WHERE tier = $1 AND status = 'active'
	`

	var userCount int
	err := ei.db.QueryRow(ctx, userCountQuery, string(tier)).Scan(&userCount)
	if err != nil {
		return nil, fmt.Errorf("failed to get user count: %w", err)
	}

	// Get resource usage for this tier
	usageQuery := `
		SELECT resource, SUM(usage_count) as total_usage
		FROM tier_usage
		WHERE tier = $1
		AND period_start >= date_trunc('month', NOW())
		GROUP BY resource
	`

	rows, err := ei.db.Query(ctx, usageQuery, string(tier))
	if err != nil {
		return nil, fmt.Errorf("failed to get usage: %w", err)
	}
	defer rows.Close()

	usage := make(map[string]int)
	for rows.Next() {
		var resource string
		var totalUsage int
		if err := rows.Scan(&resource, &totalUsage); err != nil {
			return nil, fmt.Errorf("failed to scan usage: %w", err)
		}
		usage[resource] = totalUsage
	}

	return &TierStatus{
		Tier:      tier,
		Name:      tierInfo.Name,
		Price:     tierInfo.Price,
		UserCount: userCount,
		Usage:     usage,
		Status:    "active",
	}, nil
}

// Data structures for ecosystem status

type EcosystemStatus struct {
	Tiers map[string]TierStatus `json:"tiers"`
}

type TierStatus struct {
	Tier      Tier           `json:"tier"`
	Name      string         `json:"name"`
	Price     string         `json:"price"`
	UserCount int            `json:"user_count"`
	Usage     map[string]int `json:"usage"`
	Status    string         `json:"status"`
}

// Ecosystem factory for creating integrated ecosystem instances
type EcosystemFactory struct {
	db          *database.PostGISDB
	coreService CoreService
}

// NewEcosystemFactory creates a new ecosystem factory
func NewEcosystemFactory(
	db *database.PostGISDB,
	coreService CoreService,
) *EcosystemFactory {
	return &EcosystemFactory{
		db:          db,
		coreService: coreService,
	}
}

// CreateEcosystem creates a new integrated ecosystem
func (ef *EcosystemFactory) CreateEcosystem() *EcosystemIntegration {
	return NewEcosystemIntegration(
		ef.db,
		ef.coreService,
	)
}

// InitializeEcosystem initializes the ecosystem with default data
func (ef *EcosystemFactory) InitializeEcosystem(ctx context.Context) (*EcosystemIntegration, error) {
	ecosystem := ef.CreateEcosystem()

	if err := ecosystem.InitializeEcosystem(ctx); err != nil {
		return nil, fmt.Errorf("failed to initialize ecosystem: %w", err)
	}

	return ecosystem, nil
}
