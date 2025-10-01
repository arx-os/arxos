package app

import (
	"context"
	"fmt"
	"sync"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/infrastructure"
	"github.com/arx-os/arxos/internal/interfaces"
	"github.com/arx-os/arxos/internal/usecase"
)

// Container implements dependency injection container following Go Blueprint standards
type Container struct {
	config *config.Config

	// Infrastructure layer
	db     domain.Database
	cache  domain.Cache
	logger domain.Logger

	// Domain repositories (interfaces)
	userRepo         domain.UserRepository
	buildingRepo     domain.BuildingRepository
	equipmentRepo    domain.EquipmentRepository
	organizationRepo domain.OrganizationRepository

	// Use cases
	userUC         *usecase.UserUseCase
	buildingUC     *usecase.BuildingUseCase
	equipmentUC    *usecase.EquipmentUseCase
	organizationUC *usecase.OrganizationUseCase

	// Interfaces
	httpHandler *interfaces.HTTPHandler

	mu          sync.RWMutex
	initialized bool
}

// NewContainer creates a new dependency injection container
func NewContainer() *Container {
	return &Container{}
}

// Initialize sets up all dependencies following Clean Architecture
func (c *Container) Initialize(ctx context.Context, cfg *config.Config) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if c.initialized {
		return nil
	}

	c.config = cfg

	// Initialize infrastructure layer
	if err := c.initInfrastructure(ctx); err != nil {
		return fmt.Errorf("failed to initialize infrastructure: %w", err)
	}

	// Initialize repositories (implementations)
	if err := c.initRepositories(ctx); err != nil {
		return fmt.Errorf("failed to initialize repositories: %w", err)
	}

	// Initialize use cases
	if err := c.initUseCases(ctx); err != nil {
		return fmt.Errorf("failed to initialize use cases: %w", err)
	}

	// Initialize interfaces
	if err := c.initInterfaces(ctx); err != nil {
		return fmt.Errorf("failed to initialize interfaces: %w", err)
	}

	c.initialized = true
	return nil
}

// initInfrastructure initializes infrastructure dependencies
func (c *Container) initInfrastructure(ctx context.Context) error {
	// Database
	db, err := infrastructure.NewDatabase(c.config)
	if err != nil {
		return fmt.Errorf("failed to create database: %w", err)
	}
	c.db = db

	// Cache
	cache, err := infrastructure.NewCache(c.config)
	if err != nil {
		return fmt.Errorf("failed to create cache: %w", err)
	}
	c.cache = cache

	// Logger
	c.logger = infrastructure.NewLogger(c.config)

	return nil
}

// initRepositories initializes repository implementations
func (c *Container) initRepositories(ctx context.Context) error {
	// User repository
	c.userRepo = infrastructure.NewUserRepository(c.db, c.cache)

	// Building repository
	c.buildingRepo = infrastructure.NewBuildingRepository(c.db, c.cache)

	// Equipment repository
	c.equipmentRepo = infrastructure.NewEquipmentRepository(c.db, c.cache)

	// Organization repository
	c.organizationRepo = infrastructure.NewOrganizationRepository(c.db, c.cache)

	return nil
}

// initUseCases initializes use case layer
func (c *Container) initUseCases(ctx context.Context) error {
	// User use case
	c.userUC = usecase.NewUserUseCase(c.userRepo, c.logger)

	// Building use case
	c.buildingUC = usecase.NewBuildingUseCase(c.buildingRepo, c.equipmentRepo, c.logger)

	// Equipment use case
	c.equipmentUC = usecase.NewEquipmentUseCase(c.equipmentRepo, c.buildingRepo, c.logger)

	// Organization use case
	c.organizationUC = usecase.NewOrganizationUseCase(c.organizationRepo, c.userRepo, c.logger)

	return nil
}

// initInterfaces initializes interface layer
func (c *Container) initInterfaces(ctx context.Context) error {
	// HTTP handler
	c.httpHandler = interfaces.NewHTTPHandler(
		c.userUC,
		c.buildingUC,
		c.equipmentUC,
		c.organizationUC,
		c.logger,
	)

	return nil
}

// Getters for dependencies
func (c *Container) GetConfig() *config.Config {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.config
}

func (c *Container) GetDatabase() domain.Database {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.db
}

func (c *Container) GetCache() domain.Cache {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.cache
}

func (c *Container) GetLogger() domain.Logger {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.logger
}

func (c *Container) GetHTTPHandler() *interfaces.HTTPHandler {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.httpHandler
}

func (c *Container) GetUserUseCase() *usecase.UserUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.userUC
}

func (c *Container) GetBuildingUseCase() *usecase.BuildingUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.buildingUC
}

func (c *Container) GetEquipmentUseCase() *usecase.EquipmentUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.equipmentUC
}

func (c *Container) GetOrganizationUseCase() *usecase.OrganizationUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.organizationUC
}

// Shutdown gracefully shuts down all dependencies
func (c *Container) Shutdown(ctx context.Context) error {
	c.mu.Lock()
	defer c.mu.Unlock()

	if !c.initialized {
		return nil
	}

	// Shutdown in reverse order
	var err error

	// Close database
	if dbErr := c.db.Close(); dbErr != nil {
		err = fmt.Errorf("failed to close database: %w", dbErr)
	}

	// Close cache (cache interface doesn't have Close method, so skip for now)
	// TODO: Add Close method to cache interface if needed

	c.initialized = false
	return err
}
