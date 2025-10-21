package app

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/jmoiron/sqlx"

	"github.com/arx-os/arxos/internal/config"
	"github.com/arx-os/arxos/internal/domain"
	"github.com/arx-os/arxos/internal/domain/bas"
	"github.com/arx-os/arxos/internal/domain/spatial"
	"github.com/arx-os/arxos/internal/domain/versioncontrol"
	"github.com/arx-os/arxos/internal/domain/building"
	"github.com/arx-os/arxos/internal/domain/component"
	"github.com/arx-os/arxos/internal/domain/design"
	"github.com/arx-os/arxos/internal/infrastructure"
	"github.com/arx-os/arxos/internal/infrastructure/cache"
	"github.com/arx-os/arxos/internal/infrastructure/filesystem"
	"github.com/arx-os/arxos/internal/infrastructure/ifc"
	"github.com/arx-os/arxos/internal/infrastructure/postgis"
	"github.com/arx-os/arxos/internal/infrastructure/repository"
	"github.com/arx-os/arxos/internal/interfaces/http/handlers"
	authuc "github.com/arx-os/arxos/internal/usecase/auth"
	buildinguc "github.com/arx-os/arxos/internal/usecase/building"
	designuc "github.com/arx-os/arxos/internal/usecase/design"
	"github.com/arx-os/arxos/internal/usecase/integration"
	"github.com/arx-os/arxos/internal/usecase/services"
	vcuc "github.com/arx-os/arxos/internal/usecase/versioncontrol"
	"github.com/arx-os/arxos/pkg/auth"
)

// Container implements dependency injection container following Go Blueprint standards
type Container struct {
	config *config.Config

	// Infrastructure layer
	db          domain.Database
	postgis     *postgis.PostGIS
	cache       domain.Cache
	logger      domain.Logger
	jwtManager  *auth.JWTManager
	rbacManager *auth.RBACManager

	// Domain repositories (interfaces)
	userRepo         domain.UserRepository
	buildingRepo     domain.BuildingRepository
	floorRepo        domain.FloorRepository
	roomRepo         domain.RoomRepository
	equipmentRepo    domain.EquipmentRepository
	organizationRepo domain.OrganizationRepository
	spatialRepo      spatial.SpatialRepository
	relationshipRepo domain.RelationshipRepository

	// BAS repositories
	basPointRepo  bas.BASPointRepository
	basSystemRepo bas.BASSystemRepository

	// Git workflow repositories
	branchRepo      versioncontrol.BranchRepository
	commitRepo      versioncontrol.CommitRepository
	pullRequestRepo versioncontrol.PullRequestRepository
	issueRepo       versioncontrol.IssueRepository

	// Building repository domain repositories
	repositoryRepo building.RepositoryRepository
	versionRepo    building.VersionRepository
	ifcRepo        building.IFCRepository

	// Component domain repository
	componentRepo component.ComponentRepository

	// Infrastructure services
	filesystemService *filesystem.RepositoryFilesystemService
	dataManager       *filesystem.DataManager

	// IFC services
	ifcOpenShellClient *ifc.IfcOpenShellClient
	nativeParser       *ifc.NativeParser
	ifcService         *ifc.EnhancedIFCService

	// Use cases
	userUC         *authuc.UserUseCase
	buildingUC     *buildinguc.BuildingUseCase
	floorUC        *buildinguc.FloorUseCase
	roomUC         *buildinguc.RoomUseCase
	equipmentUC    *buildinguc.EquipmentUseCase
	organizationUC *authuc.OrganizationUseCase

	// BAS use cases
	basImportUC *integration.BASImportUseCase

	// Git workflow use cases
	branchUC      *vcuc.BranchUseCase
	commitUC      *vcuc.CommitUseCase
	pullRequestUC *vcuc.PullRequestUseCase
	issueUC       *vcuc.IssueUseCase

	// Building repository use cases
	repositoryUC *vcuc.RepositoryUseCase
	ifcUC        *integration.IFCUseCase
	versionUC    *vcuc.VersionUseCase

	// Component use case
	componentUC component.ComponentService

	// Design use case
	designUC design.DesignInterface

	// Interfaces
	apiHandler *handlers.APIHandler

	// HTTP Handlers (Following Clean Architecture)
	buildingHandler     *handlers.BuildingHandler
	authHandler         *handlers.AuthHandler
	organizationHandler *handlers.OrganizationHandler
	basHandler          *handlers.BASHandler
	prHandler           *handlers.PRHandler
	issueHandler        *handlers.IssueHandler

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

	// Cache - Use unified cache implementation
	cache, err := cache.NewUnifiedCache(c.config, c.logger)
	if err != nil {
		return fmt.Errorf("failed to create unified cache: %w", err)
	}
	c.cache = cache

	// RBAC Manager - Initialize with default configuration
	rbacConfig := auth.DefaultRBACConfig()
	c.rbacManager = auth.NewRBACManager(rbacConfig)
	c.logger.Info("RBAC manager initialized with role-based access control")

	return nil
}

// initRepositories initializes repository implementations
func (c *Container) initRepositories(ctx context.Context) error {
	// Use PostGIS implementations for all repositories
	db := c.postgis.GetDB()

	// Core repositories - PostGIS implementation
	c.userRepo = postgis.NewUserRepository(db)
	c.buildingRepo = postgis.NewBuildingRepository(db)
	c.floorRepo = postgis.NewFloorRepository(db)
	c.roomRepo = postgis.NewRoomRepository(db)
	c.equipmentRepo = postgis.NewEquipmentRepository(db)
	c.organizationRepo = postgis.NewOrganizationRepository(db)
	c.relationshipRepo = postgis.NewRelationshipRepository(db)

	// BAS repositories - PostGIS implementation
	c.basPointRepo = postgis.NewBASPointRepository(db)
	c.basSystemRepo = postgis.NewBASSystemRepository(db)

	// Git workflow repositories - PostGIS implementation
	c.branchRepo = postgis.NewBranchRepository(db)
	c.commitRepo = postgis.NewCommitRepository(db)
	c.pullRequestRepo = postgis.NewPullRequestRepository(db)
	c.issueRepo = postgis.NewIssueRepository(db)

	// Building repository domain repositories
	// Initialize with PostGIS implementations
	c.repositoryRepo = repository.NewPostGISRepositoryRepository(db)
	c.versionRepo = repository.NewPostGISVersionRepository(db)
	c.ifcRepo = repository.NewPostGISIFCRepository(db)

	// Component repository
	c.componentRepo = repository.NewPostGISComponentRepository(db)

	// Create sqlx.DB from the PostGIS sql.DB
	sqlxDB := sqlx.NewDb(db, "postgres")
	c.spatialRepo = postgis.NewSpatialRepository(sqlxDB, c.logger)

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

	// JWT Manager
	jwtConfig := &auth.JWTConfig{
		SecretKey:          c.config.Security.JWTSecret,
		AccessTokenExpiry:  c.config.Security.JWTExpiry,
		RefreshTokenExpiry: c.config.Security.JWTExpiry * 7, // Refresh valid for 7x longer
		Issuer:             "arxos",
		Audience:           "arxos-users",
		Algorithm:          "HS256", // Default algorithm
	}
	jwtManager, err := auth.NewJWTManager(jwtConfig)
	if err != nil {
		return fmt.Errorf("failed to create JWT manager: %w", err)
	}
	c.jwtManager = jwtManager

	// Initialize IFC services
	if err := c.initIFCServices(ctx); err != nil {
		return fmt.Errorf("failed to initialize IFC services: %w", err)
	}

	return nil
}

// initIFCServices initializes IFC-related services
func (c *Container) initIFCServices(ctx context.Context) error {
	// Parse timeout from config
	timeout := 30 * time.Second // default
	if c.config.IFC.Service.Timeout != "" {
		if parsed, err := time.ParseDuration(c.config.IFC.Service.Timeout); err == nil {
			timeout = parsed
		}
	}

	// Create IfcOpenShell client
	c.ifcOpenShellClient = ifc.NewIfcOpenShellClient(
		c.config.IFC.Service.URL,
		timeout,
		3, // retries
	)

	// Create native parser as fallback
	c.nativeParser = ifc.NewNativeParser(100 * 1024 * 1024) // 100MB

	// Create enhanced IFC service with logging
	logger := ifc.NewDefaultLogger()
	c.ifcService = ifc.NewEnhancedIFCService(
		c.ifcOpenShellClient,
		c.nativeParser,
		c.config.IFC.Service.Enabled,
		c.config.IFC.Fallback.Enabled,
		5,              // failure threshold
		60*time.Second, // recovery timeout
		logger,
	)

	return nil
}

// initUseCases initializes use case layer
func (c *Container) initUseCases(ctx context.Context) error {
	// Core use cases
	c.userUC = authuc.NewUserUseCase(c.userRepo, c.logger)
	c.buildingUC = buildinguc.NewBuildingUseCase(c.buildingRepo, c.equipmentRepo, c.logger)
	c.floorUC = buildinguc.NewFloorUseCase(c.floorRepo, c.buildingRepo, c.logger)
	c.roomUC = buildinguc.NewRoomUseCase(c.roomRepo, c.floorRepo, c.buildingRepo, c.logger)
	c.equipmentUC = buildinguc.NewEquipmentUseCase(c.equipmentRepo, c.buildingRepo, c.floorRepo, c.roomRepo, c.logger)
	c.organizationUC = authuc.NewOrganizationUseCase(c.organizationRepo, c.userRepo, c.logger)

	// Inject additional repositories (avoids circular dependencies)
	c.floorUC.SetRoomRepository(c.roomRepo)
	c.floorUC.SetEquipmentRepository(c.equipmentRepo)
	c.roomUC.SetEquipmentRepository(c.equipmentRepo)

	// BAS use case - Wire with all dependencies
	c.basImportUC = integration.NewBASImportUseCase(
		c.basPointRepo,
		c.basSystemRepo,
		c.roomRepo,
		c.floorRepo,
		c.equipmentRepo,
		c.logger,
	)

	// Git workflow use cases
	c.branchUC = vcuc.NewBranchUseCase(
		c.branchRepo,
		c.commitRepo,
		c.logger,
	)

	c.commitUC = vcuc.NewCommitUseCase(
		c.commitRepo,
		c.branchRepo,
		c.logger,
	)

	c.pullRequestUC = vcuc.NewPullRequestUseCase(
		c.pullRequestRepo,
		c.branchRepo,
		c.commitRepo,
		nil, // Assignment repo - will implement when needed
		c.logger,
	)

	c.issueUC = vcuc.NewIssueUseCase(
		c.issueRepo,
		c.branchUC,
		c.pullRequestUC,
		c.logger,
	)

	// Building repository use cases
	c.repositoryUC = vcuc.NewRepositoryUseCase(c.repositoryRepo, c.versionRepo, c.ifcRepo, nil, c.logger)
	c.ifcUC = integration.NewIFCUseCase(
		c.repositoryRepo,
		c.ifcRepo,
		nil, // validator - will be wired later
		c.ifcService,
		c.buildingRepo,
		c.floorRepo,
		c.roomRepo,
		c.equipmentRepo,
		c.logger,
	)
	c.versionUC = vcuc.NewVersionUseCase(c.repositoryRepo, c.versionRepo, c.logger)

	// Component use case
	c.componentUC = buildinguc.NewComponentUseCase(c.componentRepo)

	// Design use case
	c.designUC = designuc.NewDesignUseCase(c.componentUC)

	return nil
}

// initInterfaces initializes interface layer following Clean Architecture
func (c *Container) initInterfaces(ctx context.Context) error {
	// Create BaseHandler implementation
	baseHandler := handlers.NewBaseHandler(c.logger, c.jwtManager)

	// API handler
	c.apiHandler = handlers.NewAPIHandler(baseHandler, c.logger)

	// Building handler with use case dependency
	// Access fields directly to avoid deadlock (we already hold the write lock)
	c.buildingHandler = handlers.NewBuildingHandler(
		baseHandler,
		c.buildingUC, // Direct field access instead of c.GetBuildingUseCase()
		c.ifcUC,      // Direct field access for IFC use case
		c.logger,
	)

	// Auth handler with use case and JWT manager dependencies
	// Access fields directly to avoid deadlock (we already hold the write lock)
	c.authHandler = handlers.NewAuthHandler(
		baseHandler,
		c.userUC, // Direct field access instead of c.GetUserUseCase()
		c.jwtManager,
		c.logger,
	)

	// Organization handler with use case dependency
	c.organizationHandler = handlers.NewOrganizationHandler(
		baseHandler,
		c.organizationUC, // Direct field access
		c.logger,
	)

	// BAS handler with BAS use case and repository dependencies
	c.basHandler = handlers.NewBASHandler(
		baseHandler,
		c.basImportUC,   // BAS import use case
		c.basPointRepo,  // BAS point repository
		c.basSystemRepo, // BAS system repository
		c.logger,
	)

	// PR handler with PR and branch use cases
	c.prHandler = handlers.NewPRHandler(
		baseHandler,
		c.pullRequestUC, // Pull request use case
		c.branchUC,      // Branch use case
		c.logger,
	)

	// Issue handler with issue use case
	c.issueHandler = handlers.NewIssueHandler(
		baseHandler,
		c.issueUC, // Issue use case
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

// GetContainer returns the container itself (for interface satisfaction)
func (c *Container) GetContainer() *Container {
	return c
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

func (c *Container) GetJWTManager() *auth.JWTManager {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.jwtManager
}

func (c *Container) GetRBACManager() *auth.RBACManager {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.rbacManager
}

func (c *Container) GetAPIHandler() *handlers.APIHandler {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.apiHandler
}

// GetBuildingHandler returns the building handler
func (c *Container) GetBuildingHandler() *handlers.BuildingHandler {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.buildingHandler
}

// GetAuthHandler returns the auth handler
func (c *Container) GetAuthHandler() *handlers.AuthHandler {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.authHandler
}

// GetBASHandler returns the BAS handler
func (c *Container) GetBASHandler() *handlers.BASHandler {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.basHandler
}

// GetPRHandler returns the PR handler
func (c *Container) GetPRHandler() *handlers.PRHandler {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.prHandler
}

// GetIssueHandler returns the issue handler
func (c *Container) GetIssueHandler() *handlers.IssueHandler {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.issueHandler
}

func (c *Container) GetOrganizationHandler() *handlers.OrganizationHandler {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.organizationHandler
}

func (c *Container) GetUserUseCase() *authuc.UserUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.userUC
}

func (c *Container) GetBuildingUseCase() *buildinguc.BuildingUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.buildingUC
}

func (c *Container) GetEquipmentUseCase() *buildinguc.EquipmentUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.equipmentUC
}

func (c *Container) GetOrganizationUseCase() *authuc.OrganizationUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.organizationUC
}

func (c *Container) GetSpatialRepository() spatial.SpatialRepository {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.spatialRepo
}

func (c *Container) GetRelationshipRepository() domain.RelationshipRepository {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.relationshipRepo
}

// Building repository getters
func (c *Container) GetRepositoryUseCase() *vcuc.RepositoryUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.repositoryUC
}

func (c *Container) GetIFCUseCase() *integration.IFCUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.ifcUC
}

func (c *Container) GetIfcOpenShellClient() *ifc.IfcOpenShellClient {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.ifcOpenShellClient
}

func (c *Container) GetNativeParser() *ifc.NativeParser {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.nativeParser
}

func (c *Container) GetIFCService() *integration.IFCUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.ifcUC
}

func (c *Container) GetIFCServiceLayer() *ifc.EnhancedIFCService {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.ifcService
}

func (c *Container) GetVersionUseCase() *vcuc.VersionUseCase {
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

// GetDesignService returns the design service (implements DesignServiceProvider interface)
func (c *Container) GetDesignService() design.DesignInterface {
	return c.GetDesignUseCase()
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

// BAS use case getters
func (c *Container) GetBASImportUseCase() *integration.BASImportUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.basImportUC
}

// Git workflow use case getters
func (c *Container) GetBranchUseCase() *vcuc.BranchUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.branchUC
}

func (c *Container) GetCommitUseCase() *vcuc.CommitUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.commitUC
}

// GetDiffService returns the diff service
// TODO: Implement full DiffService with snapshot, object, and tree repositories
func (c *Container) GetDiffService() *services.DiffService {
	// For now, return nil - diff functionality requires additional repo wiring
	// The VC handler has placeholder response for diff endpoint
	return nil
}

func (c *Container) GetPullRequestUseCase() *vcuc.PullRequestUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.pullRequestUC
}

func (c *Container) GetIssueUseCase() *vcuc.IssueUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.issueUC
}

// Repository getters
func (c *Container) GetBASPointRepository() bas.BASPointRepository {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.basPointRepo
}

func (c *Container) GetBASSystemRepository() bas.BASSystemRepository {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.basSystemRepo
}

func (c *Container) GetBranchRepository() versioncontrol.BranchRepository {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.branchRepo
}

func (c *Container) GetFloorRepository() domain.FloorRepository {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.floorRepo
}

func (c *Container) GetRoomRepository() domain.RoomRepository {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.roomRepo
}

// GetFloorUseCase returns the floor use case
func (c *Container) GetFloorUseCase() *buildinguc.FloorUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.floorUC
}

// GetRoomUseCase returns the room use case
func (c *Container) GetRoomUseCase() *buildinguc.RoomUseCase {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.roomUC
}

// GetBuildingRepository returns the building repository
func (c *Container) GetBuildingRepository() domain.BuildingRepository {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.buildingRepo
}

// GetEquipmentRepository returns the equipment repository
func (c *Container) GetEquipmentRepository() domain.EquipmentRepository {
	c.mu.RLock()
	defer c.mu.RUnlock()
	return c.equipmentRepo
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

	// Close cache
	if c.cache != nil {
		if cacheErr := c.cache.Close(); cacheErr != nil {
			err = fmt.Errorf("failed to close cache: %w", cacheErr)
		}
	}

	c.initialized = false
	return err
}
