package api

import (
	"context"
	"net/http"

	"github.com/arx-os/arxos/internal/ecosystem"
	"github.com/go-chi/chi/v5"
)

// TierRouter handles routing for the three-tier ecosystem
type TierRouter struct {
	ecosystemManager *ecosystem.Manager
}

// NewTierRouter creates a new tier-based router
func NewTierRouter(ecosystemManager *ecosystem.Manager) *TierRouter {
	return &TierRouter{
		ecosystemManager: ecosystemManager,
	}
}

// SetupRoutes configures all tier-based routes
func (tr *TierRouter) SetupRoutes(r chi.Router) {
	// Health and info endpoints (public)
	r.Get("/health", tr.handleHealth)
	r.Get("/api/versions", tr.handleVersionInfo)
	r.Get("/api/tiers", tr.handleTierInfo)

	// API v1 routes organized by tier
	r.Route("/api/v1", func(r chi.Router) {
		// Apply common middleware
		r.Use(tr.corsMiddleware)
		r.Use(tr.rateLimitMiddleware)

		// Authentication endpoints (public)
		r.Post("/auth/login", tr.handleLogin)
		r.Post("/auth/logout", tr.handleLogout)
		r.Post("/auth/refresh", tr.handleRefreshToken)
		r.Post("/auth/register", tr.handleRegister)

		// Core Tier Routes (Layer 1 - FREE)
		r.Route("/core", func(r chi.Router) {
			r.Use(tr.tierMiddleware(ecosystem.TierCore))
			r.Use(tr.authMiddleware)

			// Building management
			r.Route("/buildings", func(r chi.Router) {
				r.Get("/", tr.handleListBuildings)
				r.Post("/", tr.handleCreateBuilding)
				r.Route("/{id}", func(r chi.Router) {
					r.Get("/", tr.handleGetBuilding)
					r.Put("/", tr.handleUpdateBuilding)
					r.Delete("/", tr.handleDeleteBuilding)
				})
			})

			// Equipment management
			r.Route("/equipment", func(r chi.Router) {
				r.Get("/", tr.handleListEquipment)
				r.Post("/", tr.handleCreateEquipment)
				r.Route("/{id}", func(r chi.Router) {
					r.Get("/", tr.handleGetEquipment)
					r.Put("/", tr.handleUpdateEquipment)
					r.Delete("/", tr.handleDeleteEquipment)
				})
			})

			// Spatial queries
			r.Route("/spatial", func(r chi.Router) {
				r.Get("/nearby", tr.handleSpatialNearby)
				r.Get("/within", tr.handleSpatialWithin)
				r.Get("/floor", tr.handleSpatialFloor)
			})

			// Import/Export
			r.Post("/import", tr.handleImportData)
			r.Post("/export", tr.handleExportData)
		})

		// Hardware Tier Routes (Layer 2 - FREEMIUM)
		r.Route("/hardware", func(r chi.Router) {
			r.Use(tr.tierMiddleware(ecosystem.TierHardware))
			r.Use(tr.authMiddleware)

			// Device management
			r.Route("/devices", func(r chi.Router) {
				r.Get("/", tr.handleListDevices)
				r.Post("/", tr.handleRegisterDevice)
				r.Route("/{id}", func(r chi.Router) {
					r.Get("/", tr.handleGetDevice)
					r.Put("/", tr.handleUpdateDevice)
					r.Delete("/", tr.handleDeleteDevice)
					r.Post("/firmware", tr.handleUpdateDeviceFirmware)
				})
			})

			// Device templates
			r.Route("/templates", func(r chi.Router) {
				r.Get("/", tr.handleListDeviceTemplates)
				r.Get("/{id}", tr.handleGetDeviceTemplate)
				r.Post("/{id}/create", tr.handleCreateDeviceFromTemplate)
			})

			// Gateway management
			r.Route("/gateway", func(r chi.Router) {
				r.Get("/", tr.handleListGateways)
				r.Post("/", tr.handleDeployGateway)
				r.Route("/{id}", func(r chi.Router) {
					r.Get("/", tr.handleGetGateway)
					r.Put("/", tr.handleUpdateGateway)
					r.Delete("/", tr.handleDeleteGateway)
					r.Post("/configure", tr.handleConfigureGateway)
				})
			})

			// Marketplace
			r.Route("/marketplace", func(r chi.Router) {
				r.Get("/devices", tr.handleListCertifiedDevices)
				r.Post("/purchase", tr.handlePurchaseDevice)
				r.Get("/orders", tr.handleListOrders)
				r.Get("/orders/{id}", tr.handleGetOrder)
			})
		})

		// Workflow Tier Routes (Layer 3 - PAID)
		r.Route("/workflow", func(r chi.Router) {
			r.Use(tr.tierMiddleware(ecosystem.TierWorkflow))
			r.Use(tr.authMiddleware)

			// Workflow management
			r.Route("/workflows", func(r chi.Router) {
				r.Get("/", tr.handleListWorkflows)
				r.Post("/", tr.handleCreateWorkflow)
				r.Route("/{id}", func(r chi.Router) {
					r.Get("/", tr.handleGetWorkflow)
					r.Put("/", tr.handleUpdateWorkflow)
					r.Delete("/", tr.handleDeleteWorkflow)
					r.Post("/execute", tr.handleExecuteWorkflow)
				})
			})

			// CMMS/CAFM features
			r.Route("/cmmc", func(r chi.Router) {
				// Work orders
				r.Route("/work-orders", func(r chi.Router) {
					r.Get("/", tr.handleListWorkOrders)
					r.Post("/", tr.handleCreateWorkOrder)
					r.Route("/{id}", func(r chi.Router) {
						r.Get("/", tr.handleGetWorkOrder)
						r.Put("/", tr.handleUpdateWorkOrder)
						r.Delete("/", tr.handleDeleteWorkOrder)
					})
				})

				// Maintenance scheduling
				r.Route("/maintenance", func(r chi.Router) {
					r.Get("/", tr.handleListMaintenanceSchedules)
					r.Post("/", tr.handleCreateMaintenanceSchedule)
					r.Route("/{id}", func(r chi.Router) {
						r.Get("/", tr.handleGetMaintenanceSchedule)
						r.Put("/", tr.handleUpdateMaintenanceSchedule)
						r.Delete("/", tr.handleDeleteMaintenanceSchedule)
					})
				})

				// Reports
				r.Route("/reports", func(r chi.Router) {
					r.Get("/", tr.handleListReports)
					r.Post("/", tr.handleGenerateReport)
					r.Get("/{id}", tr.handleGetReport)
				})
			})

			// Automation
			r.Route("/automation", func(r chi.Router) {
				r.Get("/", tr.handleListAutomations)
				r.Post("/", tr.handleCreateAutomation)
				r.Route("/{id}", func(r chi.Router) {
					r.Get("/", tr.handleGetAutomation)
					r.Put("/", tr.handleUpdateAutomation)
					r.Delete("/", tr.handleDeleteAutomation)
					r.Post("/trigger", tr.handleTriggerAutomation)
				})
			})

			// Analytics
			r.Route("/analytics", func(r chi.Router) {
				r.Get("/", tr.handleGetAnalytics)
				r.Post("/predictive", tr.handleGetPredictiveInsights)
				r.Get("/dashboard", tr.handleGetDashboard)
			})

			// Enterprise integrations
			r.Route("/integrations", func(r chi.Router) {
				r.Get("/", tr.handleListIntegrations)
				r.Post("/", tr.handleCreateIntegration)
				r.Route("/{id}", func(r chi.Router) {
					r.Get("/", tr.handleGetIntegration)
					r.Put("/", tr.handleUpdateIntegration)
					r.Delete("/", tr.handleDeleteIntegration)
					r.Post("/test", tr.handleTestIntegration)
				})
			})
		})
	})
}

// Middleware functions

// tierMiddleware validates tier access
func (tr *TierRouter) tierMiddleware(tier ecosystem.Tier) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Extract user from context (set by auth middleware)
			userID := r.Context().Value("user_id")
			if userID == nil {
				http.Error(w, "Authentication required", http.StatusUnauthorized)
				return
			}

			// Validate tier access
			err := tr.ecosystemManager.ValidateTierAccess(userID.(string), tier, r.URL.Path)
			if err != nil {
				http.Error(w, "Insufficient tier access", http.StatusForbidden)
				return
			}

			// Add tier to context
			ctx := r.Context()
			ctx = context.WithValue(ctx, "tier", tier)
			r = r.WithContext(ctx)

			next.ServeHTTP(w, r)
		})
	}
}

// authMiddleware validates authentication
func (tr *TierRouter) authMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// TODO: Implement JWT token validation
		// For now, just add a dummy user ID
		ctx := r.Context()
		ctx = context.WithValue(ctx, "user_id", "dummy_user_id")
		r = r.WithContext(ctx)

		next.ServeHTTP(w, r)
	})
}

// corsMiddleware handles CORS
func (tr *TierRouter) corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		w.Header().Set("Access-Control-Allow-Origin", "*")
		w.Header().Set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
		w.Header().Set("Access-Control-Allow-Headers", "Authorization, Content-Type")

		if r.Method == "OPTIONS" {
			w.WriteHeader(http.StatusOK)
			return
		}

		next.ServeHTTP(w, r)
	})
}

// rateLimitMiddleware implements rate limiting
func (tr *TierRouter) rateLimitMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// TODO: Implement rate limiting based on tier
		// For now, just pass through
		next.ServeHTTP(w, r)
	})
}

// Handler functions (stubs for now)

func (tr *TierRouter) handleHealth(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status": "healthy", "ecosystem": "three-tier"}`))
}

func (tr *TierRouter) handleVersionInfo(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	w.Write([]byte(`{
		"version": "1.0.0",
		"ecosystem": "three-tier",
		"tiers": ["core", "hardware", "workflow"]
	}`))
}

func (tr *TierRouter) handleTierInfo(w http.ResponseWriter, r *http.Request) {
	tierParam := r.URL.Query().Get("tier")
	if tierParam != "" {
		tier := ecosystem.Tier(tierParam)
		_ = ecosystem.GetTierInfo(tier) // Get tier info for validation
		w.Header().Set("Content-Type", "application/json")
		// TODO: Marshal tierInfo to JSON
		w.Write([]byte(`{"tier": "` + tierParam + `"}`))
		return
	}

	// Return all tiers
	_ = ecosystem.GetAvailableTiers() // Get tiers for validation

	w.Header().Set("Content-Type", "application/json")
	// TODO: Marshal tierInfos to JSON
	w.Write([]byte(`{"tiers": ["core", "hardware", "workflow"]}`))
}

// Core tier handlers
func (tr *TierRouter) handleListBuildings(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"buildings": []}`))
}

func (tr *TierRouter) handleCreateBuilding(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"id": "building_123", "status": "created"}`))
}

func (tr *TierRouter) handleGetBuilding(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "building_123", "name": "Test Building"}`))
}

func (tr *TierRouter) handleUpdateBuilding(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "building_123", "status": "updated"}`))
}

func (tr *TierRouter) handleDeleteBuilding(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNoContent)
}

func (tr *TierRouter) handleListEquipment(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"equipment": []}`))
}

func (tr *TierRouter) handleCreateEquipment(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"id": "equipment_123", "status": "created"}`))
}

func (tr *TierRouter) handleGetEquipment(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "equipment_123", "name": "Test Equipment"}`))
}

func (tr *TierRouter) handleUpdateEquipment(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "equipment_123", "status": "updated"}`))
}

func (tr *TierRouter) handleDeleteEquipment(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNoContent)
}

func (tr *TierRouter) handleSpatialNearby(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"nearby": []}`))
}

func (tr *TierRouter) handleSpatialWithin(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"within": []}`))
}

func (tr *TierRouter) handleSpatialFloor(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"floor": []}`))
}

func (tr *TierRouter) handleImportData(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusAccepted)
	w.Write([]byte(`{"id": "import_123", "status": "processing"}`))
}

func (tr *TierRouter) handleExportData(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusAccepted)
	w.Write([]byte(`{"id": "export_123", "status": "processing"}`))
}

// Hardware tier handlers
func (tr *TierRouter) handleListDevices(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"devices": []}`))
}

func (tr *TierRouter) handleRegisterDevice(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"id": "device_123", "status": "registered"}`))
}

func (tr *TierRouter) handleGetDevice(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "device_123", "name": "Test Device"}`))
}

func (tr *TierRouter) handleUpdateDevice(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "device_123", "status": "updated"}`))
}

func (tr *TierRouter) handleDeleteDevice(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNoContent)
}

func (tr *TierRouter) handleUpdateDeviceFirmware(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusAccepted)
	w.Write([]byte(`{"id": "device_123", "status": "firmware_update_started"}`))
}

func (tr *TierRouter) handleListDeviceTemplates(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"templates": []}`))
}

func (tr *TierRouter) handleGetDeviceTemplate(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "template_123", "name": "Test Template"}`))
}

func (tr *TierRouter) handleCreateDeviceFromTemplate(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"id": "device_123", "status": "created_from_template"}`))
}

func (tr *TierRouter) handleListGateways(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"gateways": []}`))
}

func (tr *TierRouter) handleDeployGateway(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"id": "gateway_123", "status": "deployed"}`))
}

func (tr *TierRouter) handleGetGateway(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "gateway_123", "name": "Test Gateway"}`))
}

func (tr *TierRouter) handleUpdateGateway(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "gateway_123", "status": "updated"}`))
}

func (tr *TierRouter) handleDeleteGateway(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNoContent)
}

func (tr *TierRouter) handleConfigureGateway(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "gateway_123", "status": "configured"}`))
}

func (tr *TierRouter) handleListCertifiedDevices(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"certified_devices": []}`))
}

func (tr *TierRouter) handlePurchaseDevice(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"id": "order_123", "status": "purchased"}`))
}

func (tr *TierRouter) handleListOrders(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"orders": []}`))
}

func (tr *TierRouter) handleGetOrder(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "order_123", "status": "processing"}`))
}

// Workflow tier handlers
func (tr *TierRouter) handleListWorkflows(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"workflows": []}`))
}

func (tr *TierRouter) handleCreateWorkflow(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"id": "workflow_123", "status": "created"}`))
}

func (tr *TierRouter) handleGetWorkflow(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "workflow_123", "name": "Test Workflow"}`))
}

func (tr *TierRouter) handleUpdateWorkflow(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "workflow_123", "status": "updated"}`))
}

func (tr *TierRouter) handleDeleteWorkflow(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNoContent)
}

func (tr *TierRouter) handleExecuteWorkflow(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusAccepted)
	w.Write([]byte(`{"id": "execution_123", "status": "started"}`))
}

func (tr *TierRouter) handleListWorkOrders(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"work_orders": []}`))
}

func (tr *TierRouter) handleCreateWorkOrder(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"id": "workorder_123", "status": "created"}`))
}

func (tr *TierRouter) handleGetWorkOrder(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "workorder_123", "title": "Test Work Order"}`))
}

func (tr *TierRouter) handleUpdateWorkOrder(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "workorder_123", "status": "updated"}`))
}

func (tr *TierRouter) handleDeleteWorkOrder(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNoContent)
}

func (tr *TierRouter) handleListMaintenanceSchedules(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"maintenance_schedules": []}`))
}

func (tr *TierRouter) handleCreateMaintenanceSchedule(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"id": "schedule_123", "status": "created"}`))
}

func (tr *TierRouter) handleGetMaintenanceSchedule(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "schedule_123", "name": "Test Schedule"}`))
}

func (tr *TierRouter) handleUpdateMaintenanceSchedule(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "schedule_123", "status": "updated"}`))
}

func (tr *TierRouter) handleDeleteMaintenanceSchedule(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNoContent)
}

func (tr *TierRouter) handleListReports(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"reports": []}`))
}

func (tr *TierRouter) handleGenerateReport(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusAccepted)
	w.Write([]byte(`{"id": "report_123", "status": "generating"}`))
}

func (tr *TierRouter) handleGetReport(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "report_123", "name": "Test Report"}`))
}

func (tr *TierRouter) handleListAutomations(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"automations": []}`))
}

func (tr *TierRouter) handleCreateAutomation(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"id": "automation_123", "status": "created"}`))
}

func (tr *TierRouter) handleGetAutomation(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "automation_123", "name": "Test Automation"}`))
}

func (tr *TierRouter) handleUpdateAutomation(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "automation_123", "status": "updated"}`))
}

func (tr *TierRouter) handleDeleteAutomation(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNoContent)
}

func (tr *TierRouter) handleTriggerAutomation(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusAccepted)
	w.Write([]byte(`{"id": "automation_123", "status": "triggered"}`))
}

func (tr *TierRouter) handleGetAnalytics(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"analytics": {}}`))
}

func (tr *TierRouter) handleGetPredictiveInsights(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"insights": []}`))
}

func (tr *TierRouter) handleGetDashboard(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"dashboard": {}}`))
}

func (tr *TierRouter) handleListIntegrations(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"integrations": []}`))
}

func (tr *TierRouter) handleCreateIntegration(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"id": "integration_123", "status": "created"}`))
}

func (tr *TierRouter) handleGetIntegration(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "integration_123", "name": "Test Integration"}`))
}

func (tr *TierRouter) handleUpdateIntegration(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "integration_123", "status": "updated"}`))
}

func (tr *TierRouter) handleDeleteIntegration(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusNoContent)
}

func (tr *TierRouter) handleTestIntegration(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"id": "integration_123", "status": "test_passed"}`))
}

// Authentication handlers
func (tr *TierRouter) handleLogin(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"token": "dummy_token", "user_id": "dummy_user_id"}`))
}

func (tr *TierRouter) handleLogout(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"status": "logged_out"}`))
}

func (tr *TierRouter) handleRefreshToken(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	w.Write([]byte(`{"token": "new_dummy_token"}`))
}

func (tr *TierRouter) handleRegister(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusCreated)
	w.Write([]byte(`{"user_id": "new_dummy_user_id", "status": "registered"}`))
}
