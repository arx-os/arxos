package http

import (
	"time"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"

	"github.com/arx-os/arxos/internal/app"
	"github.com/arx-os/arxos/internal/interfaces/http/handlers"
	httpmiddleware "github.com/arx-os/arxos/internal/interfaces/http/middleware"
	"github.com/arx-os/arxos/internal/interfaces/http/types"
	"github.com/arx-os/arxos/pkg/auth"
)

// RouterConfig holds configuration for HTTP routing
type RouterConfig struct {
	Server     *types.Server
	Container  *app.Container
	JWTManager *auth.JWTManager
}

// NewRouter creates a fully configured HTTP router with mobile endpoints
func NewRouter(config *RouterConfig) chi.Router {
	// Create Chi router
	router := chi.NewRouter()

	// Apply common middleware
	router.Use(middleware.RequestID)
	router.Use(middleware.RealIP)
	router.Use(middleware.Logger)
	router.Use(middleware.Recoverer)
	router.Use(middleware.Timeout(60 * time.Second))

	// Create handlers with dependencies
	mobileHandlers := createMobileHandlers(config)
	publicHandlers := createPublicHandlers(config)
	apiHandlers := createAPIHandlers(config)

	// Health and status endpoints (public)
	router.Get("/health", publicHandlers.apiHandler.HandleHealth)
	router.Get("/ready", publicHandlers.apiHandler.HandleHealth)

	// API v1 routes
	router.Route("/api/v1", func(r chi.Router) {
		// Public API routes (rate-limited but no auth required)
		r.Route("/public", func(r chi.Router) {
			r.Use(httpmiddleware.RateLimit(1000, time.Hour))
			r.Get("/info", publicHandlers.apiHandler.HandleAPIInfo)
		})

		// Core API routes (requires authentication)
		r.Route("/buildings", func(r chi.Router) {
			r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
			r.Use(httpmiddleware.RateLimit(100, time.Hour))

			rbac := config.Container.GetRBACManager()

			// List and Get require read permission
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/", apiHandlers.buildingHandler.ListBuildings)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/{id}", apiHandlers.buildingHandler.GetBuilding)

			// Create and Update require write permission
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/", apiHandlers.buildingHandler.CreateBuilding)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Put("/{id}", apiHandlers.buildingHandler.UpdateBuilding)
		})

		// Floor management endpoints
		r.Route("/floors", func(r chi.Router) {
			r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
			r.Use(httpmiddleware.RateLimit(100, time.Hour))

			rbac := config.Container.GetRBACManager()

			// CRUD operations
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/", apiHandlers.floorHandler.ListFloors)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/{id}", apiHandlers.floorHandler.GetFloor)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/", apiHandlers.floorHandler.CreateFloor)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Put("/{id}", apiHandlers.floorHandler.UpdateFloor)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Delete("/{id}", apiHandlers.floorHandler.DeleteFloor)

			// Floor relationships
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/{id}/rooms", apiHandlers.floorHandler.GetFloorRooms)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/{id}/equipment", apiHandlers.floorHandler.GetFloorEquipment)
		})

		// Room management endpoints
		r.Route("/rooms", func(r chi.Router) {
			r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
			r.Use(httpmiddleware.RateLimit(100, time.Hour))

			rbac := config.Container.GetRBACManager()

			// CRUD operations
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/", apiHandlers.roomHandler.ListRooms)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/{id}", apiHandlers.roomHandler.GetRoom)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/", apiHandlers.roomHandler.CreateRoom)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Put("/{id}", apiHandlers.roomHandler.UpdateRoom)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Delete("/{id}", apiHandlers.roomHandler.DeleteRoom)

			// Room relationships
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/{id}/equipment", apiHandlers.roomHandler.GetRoomEquipment)
		})

		// Version Control endpoints (Git-like workflow)
		r.Route("/vc", func(r chi.Router) {
			r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
			r.Use(httpmiddleware.RateLimit(100, time.Hour))

			rbac := config.Container.GetRBACManager()

			// Status and log (read operations)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/status", apiHandlers.vcHandler.GetStatus)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/log", apiHandlers.vcHandler.GetLog)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/diff", apiHandlers.vcHandler.GetDiff)

			// Commit (write operation)
			r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/commit", apiHandlers.vcHandler.CreateCommit)
		})

		// Mobile API routes (mobile-optimized with AR/spatial features)
		r.Route("/mobile", func(r chi.Router) {
			// Mobile authentication endpoints (public)
			r.Route("/auth", func(r chi.Router) {
				r.Use(httpmiddleware.RateLimit(100, time.Hour))
				r.Post("/login", mobileHandlers.authHandler.HandleMobileLogin)
				r.Post("/register", mobileHandlers.authHandler.HandleMobileRegister)
				r.Post("/refresh", mobileHandlers.authHandler.HandleMobileRefreshToken)

				// Protected profile endpoints
				r.Group(func(r chi.Router) {
					r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
					r.Get("/profile", mobileHandlers.authHandler.HandleMobileProfile)
					r.Post("/logout", mobileHandlers.authHandler.HandleMobileLogout)
				})
			})

			// Mobile equipment endpoints (spatial/AR enabled)
			r.Route("/equipment", func(r chi.Router) {
				r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
				r.Use(httpmiddleware.RateLimit(200, time.Hour))
				r.Get("/building/{buildingId}", mobileHandlers.mobileHandler.HandleMobileEquipment)
				r.Get("/{equipmentId}", mobileHandlers.mobileHandler.HandleMobileEquipmentDetail)
			})

			// Mobile spatial/AR endpoints (ARKit/ARCore enabled)
			r.Route("/spatial", func(r chi.Router) {
				r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
				r.Use(httpmiddleware.RateLimit(300, time.Hour))

				// AR anchors and spatial mapping - using available methods
				r.Route("/anchors", func(r chi.Router) {
					r.Post("/", mobileHandlers.spatialHandler.HandleCreateSpaticialAnchor)
					r.Get("/building/{buildingId}", mobileHandlers.spatialHandler.HandleGetSpatialAnchors)
				})

				// Spatial queries and nearby equipment
				r.Route("/nearby", func(r chi.Router) {
					r.Get("/equipment", mobileHandlers.spatialHandler.HandleNearbyEquipment)
				})

				// AR session and mapping data
				r.Post("/mapping", mobileHandlers.spatialHandler.HandleSpatialMapping)

				// Building spatial data
				r.Get("/buildings", mobileHandlers.spatialHandler.HandleBuildingsList)
			})
		})

		// Legacy equipment routes (maintained for backward compatibility)
		r.Route("/equipment", func(r chi.Router) {
			if apiHandlers.equipmentHandler != nil {
				r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
				r.Use(httpmiddleware.RateLimit(100, time.Hour))

				rbac := config.Container.GetRBACManager()

				// Read operations
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionEquipmentRead)).Get("/", apiHandlers.equipmentHandler.ListEquipment)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionEquipmentRead)).Get("/{id}", apiHandlers.equipmentHandler.GetEquipment)

				// Write operations
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionEquipmentWrite)).Post("/", apiHandlers.equipmentHandler.CreateEquipment)

				// Relationship endpoints (graph topology)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionEquipmentRead)).Get("/{id}/relationships", apiHandlers.equipmentHandler.ListRelationships)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionEquipmentRead)).Get("/{id}/hierarchy", apiHandlers.equipmentHandler.GetHierarchy)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionEquipmentWrite)).Post("/{id}/relationships", apiHandlers.equipmentHandler.CreateRelationship)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionEquipmentWrite)).Delete("/{id}/relationships/{rel_id}", apiHandlers.equipmentHandler.DeleteRelationship)

				// Path-based query endpoints (universal naming convention)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionEquipmentRead)).Get("/path/{path}", apiHandlers.equipmentHandler.GetByPath)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionEquipmentRead)).Get("/path-pattern", apiHandlers.equipmentHandler.FindByPath)
			}
		})

		// Organization management (admin only)
		r.Route("/organizations", func(r chi.Router) {
			if apiHandlers.organizationHandler != nil {
				r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
				r.Use(httpmiddleware.RateLimit(100, time.Hour))

				rbac := config.Container.GetRBACManager()

				// Read operations (admin/manager can view)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionOrgRead)).Get("/", apiHandlers.organizationHandler.ListOrganizations)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionOrgRead)).Get("/{id}", apiHandlers.organizationHandler.GetOrganization)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionOrgRead)).Get("/{id}/users", apiHandlers.organizationHandler.GetOrganizationUsers)

				// Write operations (admin only)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionOrgWrite)).Post("/", apiHandlers.organizationHandler.CreateOrganization)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionOrgWrite)).Put("/{id}", apiHandlers.organizationHandler.UpdateOrganization)

				// Delete operations (super admin only)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionOrgDelete)).Delete("/{id}", apiHandlers.organizationHandler.DeleteOrganization)
			}
		})

		// BAS (Building Automation System) endpoints
		r.Route("/bas", func(r chi.Router) {
			if apiHandlers.basHandler != nil {
				r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
				r.Use(httpmiddleware.RateLimit(100, time.Hour))

				rbac := config.Container.GetRBACManager()

				// Import endpoint (write permission required)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/import", apiHandlers.basHandler.HandleImport)

				// Read operations (read permission required)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/systems", apiHandlers.basHandler.HandleListSystems)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/points", apiHandlers.basHandler.HandleListPoints)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/points/{id}", apiHandlers.basHandler.HandleGetPoint)

				// Map operation (write permission required)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/points/{id}/map", apiHandlers.basHandler.HandleMapPoint)

				// Path-based query endpoints (universal naming convention)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/points/path/{path}", apiHandlers.basHandler.HandleGetByPath)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/points/path-pattern", apiHandlers.basHandler.HandleFindByPath)
			}
		})

		// Pull Request endpoints (CMMS/Work Order workflow)
		r.Route("/pr", func(r chi.Router) {
			if apiHandlers.prHandler != nil {
				r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
				r.Use(httpmiddleware.RateLimit(100, time.Hour))

				rbac := config.Container.GetRBACManager()

				// Create and list operations
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/", apiHandlers.prHandler.HandleCreatePR)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/", apiHandlers.prHandler.HandleListPRs)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/{id}", apiHandlers.prHandler.HandleGetPR)

				// PR workflow operations
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/{id}/approve", apiHandlers.prHandler.HandleApprovePR)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/{id}/merge", apiHandlers.prHandler.HandleMergePR)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/{id}/close", apiHandlers.prHandler.HandleClosePR)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Post("/{id}/comments", apiHandlers.prHandler.HandleAddComment)
			}
		})

		// Issue endpoints (Issue tracking)
		r.Route("/issues", func(r chi.Router) {
			if apiHandlers.issueHandler != nil {
				r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
				r.Use(httpmiddleware.RateLimit(100, time.Hour))

				rbac := config.Container.GetRBACManager()

				// Create and list operations
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/", apiHandlers.issueHandler.HandleCreateIssue)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/", apiHandlers.issueHandler.HandleListIssues)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/{id}", apiHandlers.issueHandler.HandleGetIssue)

				// Issue workflow operations
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/{id}/assign", apiHandlers.issueHandler.HandleAssignIssue)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/{id}/close", apiHandlers.issueHandler.HandleCloseIssue)
			}
		})

		// IFC Import/Export endpoints (Building data import/export)
		r.Route("/ifc", func(r chi.Router) {
			if apiHandlers.ifcHandler != nil {
				r.Use(httpmiddleware.AuthMiddleware(config.JWTManager))
				r.Use(httpmiddleware.RateLimit(10, time.Hour)) // Lower rate limit for file uploads

				rbac := config.Container.GetRBACManager()

				// IFC import (multipart file upload or JSON)
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingWrite)).Post("/import", apiHandlers.ifcHandler.ImportIFC)

				// IFC validation
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Post("/validate", apiHandlers.ifcHandler.ValidateIFC)

				// IFC export
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Post("/export/{id}", apiHandlers.ifcHandler.ExportIFC)

				// Service status
				r.With(httpmiddleware.RequirePermission(rbac, auth.PermissionBuildingRead)).Get("/status", apiHandlers.ifcHandler.GetServiceStatus)
			}
		})
	})

	return router
}

// mobileHandlers holds all mobile-specific handlers
type mobileHandlers struct {
	authHandler    *handlers.AuthHandler
	mobileHandler  *handlers.MobileHandler
	spatialHandler *handlers.SpatialHandler
}

// publicHandlers holds public handlers
type publicHandlers struct {
	apiHandler *handlers.APIHandler
}

// apiHandlers holds authenticated API handlers
type apiHandlers struct {
	buildingHandler     *handlers.BuildingHandler
	floorHandler        *handlers.FloorHandler
	roomHandler         *handlers.RoomHandler
	equipmentHandler    *handlers.EquipmentHandler
	userHandler         *handlers.UserHandler
	organizationHandler *handlers.OrganizationHandler
	basHandler          *handlers.BASHandler
	prHandler           *handlers.PRHandler
	issueHandler        *handlers.IssueHandler
	ifcHandler          *handlers.IFCHandler
	vcHandler           *handlers.VersionControlHandler
}

// NewRouterConfig creates a router configuration from existing dependencies
func NewRouterConfig(server *types.Server, container *app.Container, jwtConfig *auth.JWTConfig) (*RouterConfig, error) {
	jwtManager, err := auth.NewJWTManager(jwtConfig)
	if err != nil {
		return nil, err
	}

	return &RouterConfig{
		Server:     server,
		Container:  container,
		JWTManager: jwtManager,
	}, nil
}

// createMobileHandlers creates mobile-specific handlers with proper dependencies
func createMobileHandlers(config *RouterConfig) *mobileHandlers {
	logger := config.Container.GetLogger()
	buildingUC := config.Container.GetBuildingUseCase()
	equipmentUC := config.Container.GetEquipmentUseCase()
	spatialRepo := config.Container.GetSpatialRepository()

	return &mobileHandlers{
		authHandler:    config.Container.GetAuthHandler(),
		mobileHandler:  handlers.NewMobileHandler(config.Server, buildingUC, equipmentUC, logger),
		spatialHandler: handlers.NewSpatialHandler(config.Server, buildingUC, equipmentUC, spatialRepo, logger),
	}
}

// createPublicHandlers creates public handlers for unauthenticated endpoints
func createPublicHandlers(config *RouterConfig) *publicHandlers {
	return &publicHandlers{
		apiHandler: config.Container.GetAPIHandler(),
	}
}

// createAPIHandlers creates authenticated API handlers
func createAPIHandlers(config *RouterConfig) *apiHandlers {
	logger := config.Container.GetLogger()
	userUC := config.Container.GetUserUseCase()
	floorUC := config.Container.GetFloorUseCase()
	roomUC := config.Container.GetRoomUseCase()
	equipmentUC := config.Container.GetEquipmentUseCase()
	ifcUC := config.Container.GetIFCUseCase()
	branchUC := config.Container.GetBranchUseCase()
	commitUC := config.Container.GetCommitUseCase()
	diffSvc := config.Container.GetDiffService() // May be nil

	// Create BaseHandler for handlers not yet in Container
	// NOTE: Handlers are wired via Container in createAPIHandlers()
	baseHandler := handlers.NewBaseHandler(logger, nil) // No JWT manager needed for these for now

	relationshipRepo := config.Container.GetRelationshipRepository()

	return &apiHandlers{
		buildingHandler:     config.Container.GetBuildingHandler(),
		floorHandler:        handlers.NewFloorHandler(config.Server, floorUC, logger),
		roomHandler:         handlers.NewRoomHandler(config.Server, roomUC, logger),
		equipmentHandler:    handlers.NewEquipmentHandler(config.Server, equipmentUC, relationshipRepo, logger),
		userHandler:         handlers.NewUserHandler(baseHandler, userUC, logger),
		organizationHandler: config.Container.GetOrganizationHandler(),
		basHandler:          config.Container.GetBASHandler(),
		prHandler:           config.Container.GetPRHandler(),
		issueHandler:        config.Container.GetIssueHandler(),
		ifcHandler:          handlers.NewIFCHandler(config.Server, ifcUC, logger),
		vcHandler:           handlers.NewVersionControlHandler(config.Server, branchUC, commitUC, diffSvc, logger), // diff service may be nil
	}
}
