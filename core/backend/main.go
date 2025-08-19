// main.go
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/arxos/arxos/core/arxobject"
	"github.com/arxos/arxos/core/backend/db"
	"github.com/arxos/arxos/core/backend/handlers"
	securityMiddleware "github.com/arxos/arxos/core/backend/middleware"
	"github.com/arxos/arxos/core/backend/middleware/auth"
	"github.com/arxos/arxos/core/backend/models"
	"github.com/arxos/arxos/core/backend/services"
	// Temporarily comment out until module structure is fixed
	// "github.com/arxos/arxos/core/backend/api"
	// "github.com/arxos/arxos/core/backend/ingestion"

	"github.com/joho/godotenv"

	"github.com/go-chi/chi/v5"
	chimiddleware "github.com/go-chi/chi/v5/middleware"
	"github.com/rs/cors"
)

func main() {
	godotenv.Load() // Load .env file
	// Initialize database
	db.Connect()
	db.Migrate()
	models.SeedCategories(db.DB)

	// Initialize logging service
	loggingService, err := services.NewLoggingService(db.DB, "./logs")
	if err != nil {
		log.Fatalf("Failed to initialize logging service: %v", err)
	}
	defer loggingService.Close()

	// Initialize monitoring service
	monitoringService := services.NewMonitoringService(db.DB)


	// Initialize Redis service
	redisService, err := services.NewRedisService(nil, nil)
	if err != nil {
		log.Printf("Warning: Failed to initialize Redis service: %v", err)
		log.Println("Caching will be disabled")
		redisService = nil
	}

	// Initialize cache service
	var cacheService *services.CacheService
	if redisService != nil {
		cacheService = services.NewCacheService(redisService, nil, nil)
		log.Println("✅ Cache service initialized successfully")
	} else {
		log.Println("⚠️  Cache service disabled - Redis not available")
	}

	// Make cache service available globally
	services.SetCacheService(cacheService)

	// Initialize CMMS client
	handlers.InitCMMSClient()

	// Initialize Export Activity handler
	exportActivityHandler := handlers.NewExportActivityHandler(db.DB)

	// Initialize Security handler
	securityHandler := handlers.NewSecurityHandler()

	// Initialize Monitoring handler
	monitoringHandler := handlers.NewMonitoringHandler(monitoringService, loggingService)

	// Initialize Data Vendor handler
	dataVendorHandler := handlers.NewDataVendorHandler(db.DB, loggingService, monitoringService)

	// Initialize Data Vendor Admin handler
	dataVendorAdminHandler := handlers.NewDataVendorAdminHandler(db.DB, loggingService, monitoringService)

	// Initialize Validation Service and Handler
	validationService := services.NewValidationService(db.DB)
	arxEngine := arxobject.NewEngine(10000) // Initialize with capacity for 10000 objects
	validationHandler := handlers.NewValidationHandler(validationService, arxEngine)

	// Initialize PDF Upload handler
	// TODO: Uncomment when module structure is fixed
	/*
	uploadConfig := api.UploadConfig{
		MaxFileSize:      50 * 1024 * 1024, // 50MB
		AllowedFormats:   []string{".pdf"},
		ProcessTimeout:   30 * time.Second,
		EnableOCR:        true,
		EnableValidation: true,
		StorageBackend:   "postgres",
	}
	uploadHandler, err := api.NewUploadHandler(uploadConfig, logger)
	if err != nil {
		log.Printf("Warning: Failed to initialize upload handler: %v", err)
		uploadHandler = nil
	}
	*/
	_ = logger // Use logger to avoid unused variable error
	// var uploadHandler interface{} = nil // Placeholder (removed to fix compilation)

	// Set up router
	r := chi.NewRouter()
	r.Use(chimiddleware.Logger)
	r.Use(cors.AllowAll().Handler)

	// Apply security middleware globally
	r.Use(securityMiddleware.SecurityHeadersMiddleware)
	r.Use(securityMiddleware.AuditLoggingMiddleware)
	r.Use(securityMiddleware.RateLimitMiddleware(100, 200)) // 100 requests per second, burst of 200

	// Add request logging middleware
	r.Use(func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			start := time.Now()

			// Create log context
			ctx := &services.LogContext{
				RequestID: r.Header.Get("X-Request-ID"),
				IPAddress: r.RemoteAddr,
				Endpoint:  r.URL.Path,
				Method:    r.Method,
				UserAgent: r.UserAgent(),
			}

			// Call next handler
			next.ServeHTTP(w, r)

			// Log request
			duration := time.Since(start)
			loggingService.LogAPIRequest(ctx, 200, duration, 0) // Status code will be updated in handlers
		})
	})

	r.Route("/api", func(r chi.Router) {
		r.Post("/register", handlers.Register)
		r.Post("/login", handlers.Login)

		// Public health check endpoint
		r.Get("/health", handlers.HealthCheck)

		r.Group(func(r chi.Router) {
			r.Use(auth.RequireAuth)
			r.Use(securityMiddleware.RateLimitMiddleware(50, 100)) // Stricter rate limiting for authenticated users
			r.Get("/floor/svg", handlers.ServeFloorSVG)
			r.Get("/object/{objectId}/info", handlers.ServeObjectInfo)
			r.Post("/object/{objectId}/comment", handlers.PostObjectComment)

			r.Get("/projects", handlers.ListProjects)
			r.Post("/projects", handlers.CreateProject)
			r.Get("/projects/{id}", handlers.GetProject)

			// New endpoints (stubs to be implemented)
			r.Get("/buildings", handlers.ListBuildings)
			r.Post("/buildings", handlers.CreateBuilding)
			r.Get("/buildings/{id}", handlers.GetBuilding)
			r.Put("/buildings/{id}", handlers.UpdateBuilding)
			r.Get("/buildings/{id}/floors", handlers.ListFloors)
			r.Post("/markup", handlers.SubmitMarkup)
			r.Get("/logs/{building_id}", handlers.GetLogs)
			r.Get("/me", handlers.Me)
			r.Get("/markups", handlers.ListMarkups)
			r.Delete("/markup/{id}", handlers.DeleteMarkup)

			// HTMX endpoints for dynamic select loading
			r.Get("/buildings", handlers.HTMXListBuildings)
			r.Get("/buildings/{id}/floors", handlers.HTMXListFloors)

			r.Post("/drawings", handlers.CreateDrawing)
			r.Get("/drawings/{drawingID}/last_modified", handlers.GetDrawingLastModified)

			r.Put("/comment/{id}", handlers.EditComment)
			r.Delete("/comment/{id}", handlers.DeleteComment)

			// BIM Object endpoints (edit)
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin", "editor"))

				// Wall CRUD operations
				r.Post("/walls", handlers.CreateWall)
				r.Get("/walls/{id}", handlers.GetWall)
				r.Patch("/wall/{id}", handlers.UpdateWall)
				r.Delete("/walls/{id}", handlers.DeleteWall)
				r.Post("/wall/{id}/lock", handlers.LockWall)
				r.Post("/wall/{id}/unlock", handlers.UnlockWall)
				r.Post("/wall/{id}/assign", handlers.AssignWall)
				r.Post("/wall/{id}/status", handlers.UpdateWallStatus)

				// Door CRUD operations
				r.Post("/doors", handlers.CreateDoor)
				r.Get("/doors/{id}", handlers.GetDoor)
				r.Patch("/doors/{id}", handlers.UpdateDoor)
				r.Delete("/doors/{id}", handlers.DeleteDoor)

				// Window CRUD operations
				r.Post("/windows", handlers.CreateWindow)
				r.Get("/windows/{id}", handlers.GetWindow)
				r.Patch("/windows/{id}", handlers.UpdateWindow)
				r.Delete("/windows/{id}", handlers.DeleteWindow)

				// Room CRUD operations
				r.Post("/rooms", handlers.CreateRoom)
				r.Get("/rooms/{id}", handlers.GetRoom)
				r.Patch("/room/{id}", handlers.UpdateRoom)
				r.Delete("/rooms/{id}", handlers.DeleteRoom)
				r.Post("/room/{id}/lock", handlers.LockRoom)
				r.Post("/room/{id}/unlock", handlers.UnlockRoom)
				r.Post("/room/{id}/assign", handlers.AssignRoom)
				r.Post("/room/{id}/status", handlers.UpdateRoomStatus)

				// Device CRUD operations
				r.Post("/devices", handlers.CreateDevice)
				r.Get("/devices/{id}", handlers.GetDevice)
				r.Patch("/device/{id}", handlers.UpdateDeviceDetails)
				r.Delete("/devices/{id}", handlers.DeleteDevice)
				r.Post("/device/{id}/lock", handlers.LockDevice)
				r.Post("/device/{id}/unlock", handlers.UnlockDevice)
				r.Post("/device/{id}/assign", handlers.AssignDevice)
				r.Post("/device/{id}/status", handlers.UpdateDeviceStatus)

				// Label CRUD operations
				r.Post("/labels", handlers.CreateLabel)
				r.Get("/labels/{id}", handlers.GetLabel)
				r.Patch("/label/{id}", handlers.UpdateLabel)
				r.Delete("/labels/{id}", handlers.DeleteLabel)
				r.Post("/label/{id}/lock", handlers.LockLabel)
				r.Post("/label/{id}/unlock", handlers.UnlockLabel)
				r.Post("/label/{id}/assign", handlers.AssignLabel)
				r.Post("/label/{id}/status", handlers.UpdateLabelStatus)

				// Zone CRUD operations
				r.Post("/zones", handlers.CreateZone)
				r.Get("/zones/{id}", handlers.GetZone)
				r.Patch("/zone/{id}", handlers.UpdateZone)
				r.Delete("/zones/{id}", handlers.DeleteZone)
				r.Post("/zone/{id}/lock", handlers.LockZone)
				r.Post("/zone/{id}/unlock", handlers.UnlockZone)
				r.Post("/zone/{id}/assign", handlers.AssignZone)
				r.Post("/zone/{id}/status", handlers.UpdateZoneStatus)
			})

			// Paginated list endpoints for BIM objects
			r.Get("/walls", handlers.ListWalls)
			r.Get("/rooms", handlers.ListRooms)
			r.Get("/devices", handlers.ListDevices)
			r.Get("/labels", handlers.ListLabels)
			r.Get("/zones", handlers.ListZones)

			// PDF Upload and Building endpoints
			// Simple upload endpoint for testing
			r.Post("/buildings/upload", handlers.SimplePDFUpload)
			
			// TODO: Enable full upload handler when module structure is fixed
			/*
			if uploadHandler != nil {
				r.Post("/buildings/upload", uploadHandler.HandlePDFUpload)
				r.Get("/buildings/{id}", uploadHandler.GetBuilding)
				r.Get("/buildings/{id}/objects", uploadHandler.GetBuildingObjects)
				r.Get("/buildings/{id}/tiles/{z}/{x}/{y}", uploadHandler.GetTile)
			}
			*/

			// BIM Export endpoints
			r.Get("/bim/export/json", handlers.ExportBIMAsJSON)
			// r.Get("/bim/export/geojson", handlers.ExportBIMAsGeoJSON)
			r.Get("/bim/export/ifc", handlers.ExportBIMAsIFC)
			r.Get("/bim/export/dxf", handlers.ExportBIMAsDXF)
			r.Get("/bim/export/svg", handlers.ExportBIMAsSVG)

			// Category admin endpoints (admin only)
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin"))
				r.Post("/categories", handlers.CreateCategory)
				r.Get("/categories", handlers.ListCategories)
				r.Put("/categories/{id}", handlers.UpdateCategory)
				r.Delete("/categories/{id}", handlers.DeleteCategory)
				// User-category permission admin endpoints
				r.Post("/user-category-permissions", handlers.AssignUserCategoryPermission)
				r.Get("/user-category-permissions", handlers.ListUserCategoryPermissions)
				r.Delete("/user-category-permissions/{id}", handlers.RevokeUserCategoryPermission)
			})

			r.Get("/audit-logs", handlers.ListAuditLogs)

			r.Post("/buildings/{id}/chat", handlers.PostChatMessage)
			r.Get("/buildings/{id}/chat", handlers.ListChatMessages)

			r.Get("/svg-objects", handlers.ListSVGObjects)

			r.Get("/api/properties", handlers.HTMXListBuildingsSidebar)

			r.Get("/api/device-catalog", handlers.HTMXDeviceCatalog)

			r.Get("/device/{id}", handlers.GetDevice)

			r.Post("/routes", handlers.CreateRoute)
			// TODO: Implement these handlers
			// r.Get("/route/{id}", handlers.GetRoute)
			// r.Patch("/route/{id}", handlers.UpdateRoute)

			r.Get("/api/object-types", handlers.GetObjectTypesRegistry)
			r.Get("/api/behavior-profiles", handlers.GetBehaviorProfilesRegistry)

			// Floor version control endpoints (legacy - replaced by optimized version control)
			// r.Post("/floor/{floorId}/snapshot", handlers.SaveFloorSnapshot)
			// r.Get("/floor/{floorId}/history", handlers.GetVersionHistory)
			// r.Get("/floor/{floorId}/diff", handlers.GetVersionDiff)
			// r.Get("/floor/{floorId}/branch", handlers.GetBranchInformation)
			// r.Post("/floor/{floorId}/restore/{version}", handlers.RestoreFloorVersion)

			// Symbol library endpoints
			// List all symbols with optional search/filter
			r.Get("/symbols", handlers.ListSymbols)
			// Get a specific symbol by ID
			r.Get("/symbols/{symbol_id}", handlers.GetSymbol)
			// Advanced search (POST)
			r.Post("/symbols/search", handlers.SearchSymbols)
			// Get available symbol categories
			r.Get("/symbols/categories", handlers.GetSymbolCategories)
			// Clear symbol cache (admin only, but for now public)
			r.Delete("/symbols/cache", handlers.ClearSymbolCache)

			// Asset Inventory endpoints (with audit logging and role-based access)
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin", "editor", "maintenance"))

				r.Post("/buildings/{buildingId}/assets", handlers.CreateBuildingAssetWithAudit)
				r.Get("/buildings/{buildingId}/assets", handlers.GetBuildingAssets)
				r.Get("/assets/{assetId}", handlers.GetBuildingAsset)
				r.Put("/assets/{assetId}", handlers.UpdateBuildingAssetWithAudit)
				r.Delete("/assets/{assetId}", handlers.DeleteBuildingAssetWithAudit)

				// Asset History and Maintenance
				r.Post("/assets/{assetId}/history", handlers.AddAssetHistory)
				r.Post("/assets/{assetId}/maintenance", handlers.AddAssetMaintenance)
				r.Post("/assets/{assetId}/valuations", handlers.AddAssetValuation)

				// Asset Inventory Export and Summary (with audit logging)
				r.Get("/buildings/{buildingId}/inventory/export", handlers.ExportBuildingInventoryWithAudit)
				r.Get("/buildings/{buildingId}/inventory/summary", handlers.GetBuildingInventorySummary)

				// Industry Benchmarks
				r.Get("/industry-benchmarks", handlers.GetIndustryBenchmarks)
			})

			// Enhanced Audit Logs endpoints (admin/auditor only)
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin", "auditor"))

				r.Get("/audit-logs", handlers.ListAuditLogs)
				r.Get("/audit-logs/asset/{asset_id}", handlers.GetAssetAuditLogs)
				r.Get("/audit-logs/export/{export_id}", handlers.GetExportAuditLogs)
				r.Get("/audit-logs/user/{user_id}", handlers.GetUserAuditLogs)
			})

			// Version Control endpoints (optimized queries and lazy loading)
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin", "editor", "viewer"))

				// Version history with optimized queries
				r.Get("/versions/{floorId}", handlers.GetVersionHistory)
				// Version diff with efficient diff generation
				r.Get("/versions/diff/{versionId1}/{versionId2}", handlers.GetVersionDiff)
				// Version data with lazy loading
				r.Get("/versions/data/{versionId}", handlers.GetVersionData)
				// Create new version
				r.Post("/versions", handlers.CreateVersion)
				// Restore version
				r.Post("/versions/{versionId}/restore", handlers.RestoreVersion)
			})

			// CMMS Integration endpoints
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin", "maintenance"))

				// CMMS Connection management
				r.Get("/cmms/connections", handlers.GetCMMSConnections)
				r.Post("/cmms/connections", handlers.CreateCMMSConnection)
				r.Get("/cmms/connections/{id}", handlers.GetCMMSConnection)
				r.Put("/cmms/connections/{id}", handlers.UpdateCMMSConnection)
				r.Delete("/cmms/connections/{id}", handlers.DeleteCMMSConnection)

				// CMMS Field mappings
				r.Get("/cmms/connections/{connectionId}/mappings", handlers.GetCMMSMappings)
				r.Post("/cmms/connections/{connectionId}/mappings", handlers.CreateCMMSMapping)

				// CMMS Data synchronization
				r.Post("/cmms/connections/{connectionId}/sync", handlers.SyncCMMSData)
				r.Get("/cmms/connections/{connectionId}/sync-logs", handlers.GetCMMSSyncLogs)

				// CMMS Connection testing and manual sync
				r.Post("/cmms/connections/{id}/test", handlers.TestCMMSConnection)
				r.Post("/cmms/connections/{id}/sync", handlers.ManualCMMSSync)

				// Maintenance schedules
				r.Get("/cmms/maintenance-schedules", handlers.GetMaintenanceSchedules)

				// Work orders
				r.Get("/cmms/work-orders", handlers.GetWorkOrders)

				// Equipment specifications
				r.Get("/cmms/equipment-specifications", handlers.GetEquipmentSpecifications)
			})

			// Maintenance Workflow endpoints
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin", "maintenance", "technician"))

				// Maintenance Tasks
				r.Get("/maintenance/tasks", handlers.GetMaintenanceTasks)
				r.Post("/maintenance/tasks", handlers.CreateMaintenanceTask)
				r.Put("/maintenance/tasks/{id}", handlers.UpdateMaintenanceTask)

				// Asset Lifecycle
				r.Get("/assets/{assetId}/lifecycle", handlers.GetAssetLifecycle)
				r.Post("/assets/lifecycle", handlers.CreateAssetLifecycle)

				// Warranties
				r.Get("/assets/{assetId}/warranties", handlers.GetAssetWarranties)
				r.Post("/warranties", handlers.CreateWarranty)

				// Replacement Plans
				r.Get("/maintenance/replacement-plans", handlers.GetReplacementPlans)

				// Maintenance Costs
				r.Get("/maintenance/costs", handlers.GetMaintenanceCosts)

				// Maintenance Notifications
				r.Get("/maintenance/notifications", handlers.GetMaintenanceNotifications)
				r.Put("/maintenance/notifications/{id}/read", handlers.MarkNotificationAsRead)

				// Maintenance Dashboard
				r.Get("/maintenance/dashboard", handlers.GetMaintenanceDashboard)
			})

			// Export Activity Tracking endpoints
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin", "analyst"))

				// Export Activity Management
				r.Post("/export-activities", exportActivityHandler.CreateExportActivity)
				r.Put("/export-activities/{id}", exportActivityHandler.UpdateExportActivity)
				r.Post("/export-activities/{id}/download", exportActivityHandler.IncrementDownloadCount)
				r.Get("/export-activities", exportActivityHandler.GetExportActivities)

				// Export Analytics Dashboard
				r.Get("/export-analytics/dashboard", exportActivityHandler.GetExportDashboard)
				r.Get("/export-analytics", exportActivityHandler.GetExportAnalytics)

				// Data Vendor Usage Tracking
				r.Post("/data-vendor-usage", exportActivityHandler.CreateDataVendorUsage)
				r.Get("/data-vendor-usage", exportActivityHandler.GetDataVendorUsage)
			})

			// Validation endpoints for confidence system
			r.Group(func(r chi.Router) {
				// Public validation endpoints (any authenticated user can validate)
				r.Get("/validations/pending", validationHandler.GetPendingValidations)
				r.Post("/validations/flag", validationHandler.FlagForValidation)
				r.Post("/validations/submit", validationHandler.SubmitValidation)
				r.Get("/validations/history", validationHandler.GetValidationHistory)
				r.Get("/validations/leaderboard", validationHandler.GetValidationLeaderboard)
				
				// WebSocket for real-time validation updates
				r.Get("/ws/validation", validationHandler.WebSocketHandler)
			})

			// Compliance and Reporting endpoints
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin", "auditor"))

				// Initialize Compliance Reporting handler
				complianceHandler := handlers.NewComplianceReportingHandler(db.DB)

				// Data Access Logs
				r.Get("/compliance/data-access-logs", complianceHandler.GetDataAccessLogs)

				// Change History
				r.Get("/compliance/change-history/{object_type}/{object_id}", complianceHandler.GetChangeHistory)

				// Export Activity Summary
				r.Get("/compliance/export-activity-summary", complianceHandler.GetExportActivitySummary)

				// Data Retention Policies
				r.Get("/compliance/data-retention-policies", complianceHandler.GetDataRetentionPolicies)
				r.Post("/compliance/data-retention-policies", complianceHandler.CreateDataRetentionPolicy)
				r.Put("/compliance/data-retention-policies/{id}", complianceHandler.UpdateDataRetentionPolicy)

				// Data Retention Operations
				r.Post("/compliance/archive-old-logs", complianceHandler.ArchiveOldLogs)
				r.Post("/compliance/process-retention-policies", func(w http.ResponseWriter, r *http.Request) {
					// Initialize retention service and process policies
					retentionService := services.NewDataRetentionService(db.DB)
					stats, err := retentionService.ProcessRetentionPolicies()
					if err != nil {
						http.Error(w, err.Error(), http.StatusInternalServerError)
						return
					}
					w.Header().Set("Content-Type", "application/json")
					json.NewEncoder(w).Encode(map[string]interface{}{
						"stats":  stats,
						"status": "completed",
					})
				})

				// Retention Statistics
				r.Get("/compliance/retention-stats", func(w http.ResponseWriter, r *http.Request) {
					retentionService := services.NewDataRetentionService(db.DB)
					stats, err := retentionService.GetRetentionStats()
					if err != nil {
						http.Error(w, err.Error(), http.StatusInternalServerError)
						return
					}
					w.Header().Set("Content-Type", "application/json")
					json.NewEncoder(w).Encode(stats)
				})
			})

			// Security Management endpoints
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin", "security"))

				// Register security routes
				securityHandler.RegisterSecurityRoutes(r)
			})

			// Data Vendor Admin endpoints
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin"))

				// Register data vendor admin routes
				dataVendorAdminHandler.RegisterDataVendorAdminRoutes(r)
			})

			// Monitoring endpoints
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin", "monitor"))

				// Register monitoring routes
				monitoringHandler.RegisterMonitoringRoutes(r)
			})

			// Database monitoring endpoints (admin/monitor only)
			r.Group(func(r chi.Router) {
				r.Use(auth.RequireRole("admin", "monitor"))

				// Database health check
				r.Get("/db/health", db.HealthCheckHandler)
				// Connection pool statistics
				r.Get("/db/pool-stats", db.GetConnectionPoolStatsHandler)
			})
		})
	})

	// Data Vendor API routes (separate from authenticated routes)
	r.Route("/api/vendor", func(r chi.Router) {
		dataVendorHandler.RegisterDataVendorRoutes(r)
	})

	// Start metrics server in background
	go func() {
		log.Println("📊 Starting metrics server on :9090")
		monitoringService.StartMetricsServer(":9090")
	}()

	// Graceful shutdown
	go func() {
		log.Println("🚀 Server running on :8080")
		if err := http.ListenAndServe(":8080", r); err != nil {
			log.Fatalf("Server failed: %v", err)
		}
	}()

	// Wait for termination signal
	sig := make(chan os.Signal, 1)
	signal.Notify(sig, os.Interrupt, syscall.SIGTERM)
	<-sig

	log.Println("Shutting down server...")

	// Log system shutdown event
	loggingService.LogSystemEvent(&services.LogContext{
		RequestID: "shutdown",
		IPAddress: "system",
		Endpoint:  "/shutdown",
		Method:    "SYSTEM",
	}, "system_shutdown", "Server shutting down gracefully", map[string]interface{}{
		"reason": "signal_received",
	})

	db.Close()
	log.Println("Server stopped")
}
