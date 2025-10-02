package app

import (
	"context"
	"fmt"
	"sync"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/domain/component"
	"github.com/arx-os/arxos/internal/domain/design"
	"github.com/arx-os/arxos/internal/infrastructure"
	"github.com/arx-os/arxos/internal/infrastructure/filesystem"
	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	"github.com/arx-os/arxos/internal/infrastructure/repository"
	"github.com/arx-os/arxos/internal/interfaces"
	"github.com/arx-os/arxos/internal/usecase"
)

// Container implements dependency injection container following Go Blueprint standards
type Container struct {
	config *config.Config

	// Infrastructure layer
	db      domain.Database
	postgis *postgis.PostGIS
	cache   domain.Cache
	logger  domain.Logger

	// Domain repositories (interfaces)
	userRepo         domain.UserRepository
	buildingRepo     domain.BuildingRepository
	equipmentRepo    domain.EquipmentRepository
	organizationRepo domain.OrganizationRepository

	// Building repository domain repositories
	repositoryRepo building.RepositoryRepository
	versionRepo    building.VersionRepository
	ifcRepo        building.IFCRepository

	// Component domain repository
	componentRepo component.ComponentRepository

	// Infrastructure services
	filesystemService *filesystem.RepositoryFilesystemService
	dataManager       *filesystem.DataManager

	// Use cases
	userUC         *usecase.UserUseCase
	buildingUC     *usecase.BuildingUseCase
	equipmentUC    *usecase.EquipmentUseCase
	organizationUC *usecase.OrganizationUseCase

	// Building repository use cases
	repositoryUC *usecase.RepositoryUseCase
	ifcUC        *usecase.IFCUseCase
	versionUC    *usecase.VersionUseCase

	// Component use case
	componentUC component.ComponentService

	// Design use case
	designUC design.DesignInterface

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

	// Initialize infrastructure services
	if err := c.initInfrastructureServices(ctx); err != nil {
		return fmt.Errorf("failed to initialize infrastructure services: %w", err)
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
	// Logger first (needed for other services)
	c.logger = infrastructure.NewLogger(c.config)

	// Database
	db, err := infrastructure.NewDatabase(c.config)
	if err != nil {
		return fmt.Errorf("failed to create database: %w", err)
	}
	c.db = db

	// PostGIS connection
	postgisConfig := &postgis.PostGISConfig{
		Host:            c.config.PostGIS.Host,
		Port:            c.config.PostGIS.Port,
		Database:        c.config.PostGIS.Database,
		User:            c.config.PostGIS.User,
		Password:        c.config.PostGIS.Password,
		SSLMode:         c.config.PostGIS.SSLMode,
		MaxConnections:  c.config.Database.MaxOpenConns,
		MaxIdleConns:    c.config.Database.MaxIdleConns,
		ConnMaxLifetime: c.config.Database.ConnLifetime,
		ConnMaxIdleTime: c.config.Database.ConnLifetime,
	}

	c.postgis, err = postgis.NewPostGIS(postgisConfig, c.logger)
	if err != nil {
		return fmt.Errorf("failed to create PostGIS connection: %w", err)
	}

	// Cache
	cache, err := infrastructure.NewCache(c.config)
	if err != nil {
		return fmt.Errorf("failed to create cache: %w", err)
	}
	c.cache = cache

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

	// Building repository domain repositories
	// Initialize with PostGIS implementations
	c.repositoryRepo = repository.NewPostGISRepositoryRepository(c.postgis.GetDB())
	c.versionRepo = repository.NewPostGISVersionRepository(c.postgis.GetDB())
	c.ifcRepo = repository.NewPostGISIFCRepository(c.postgis.GetDB())

	// Component repository
	c.componentRepo = repository.NewPostGISComponentRepository(c.postgis.GetDB())

	return nil
}

// initInfrastructureServices initializes infrastructure services
func (c *Container) initInfrastructureServices(ctx context.Context) error {
	// Data manager
	c.dataManager = filesystem.NewDataManager(c.config)

	// Ensure data directories exist
	if err := c.dataManager.EnsureDataDirectories(ctx); err != nil {
		return fmt.Errorf("failed to ensure data directories: %w", err)
	}

	// Filesystem service with proper data path
	repositoriesPath := c.dataManager.GetRepositoriesPath()
	c.filesystemService = filesystem.NewRepositoryFilesystemService(repositoriesPath)

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

	// Building repository use cases
	c.repositoryUC = usecase.NewRepositoryUseCase(c.repositoryRepo, c.versionRepo, c.ifcRepo, nil, c.logger)
	c.ifcUC = usecase.NewIFCUseCase(c.repositoryRepo, c.ifcRepo, nil, c.logger)
	c.versionUC = usecase.NewVersionUseCase(c.repositoryRepo, c.versionRepo, c.logger)

	// Component use case
	c.componentUC = usecase.NewComponentUseCase(c.componentRepo)

	// Design use case
	c.designUC = usecase.NewDesignUseCase(c.componentUC)

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

func (c *Container) GetPostGIS() *postgis.PostGIS {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.postgis
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

// Building repository getters
func (c *Container) GetRepositoryUseCase() *usecase.RepositoryUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.repositoryUC
}

func (c *Container) GetIFCUseCase() *usecase.IFCUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.ifcUC
}

func (c *Container) GetVersionUseCase() *usecase.VersionUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.versionUC
}

// GetComponentUseCase returns the component use case
func (c *Container) GetComponentUseCase() component.ComponentService {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.componentUC
}

// GetDesignUseCase returns the design use case
func (c *Container) GetDesignUseCase() design.DesignInterface {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.designUC
}

func (c *Container) GetFilesystemService() *filesystem.RepositoryFilesystemService {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.filesystemService
}

// GetDataManager returns the data manager
func (c *Container) GetDataManager() *filesystem.DataManager {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.dataManager
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
