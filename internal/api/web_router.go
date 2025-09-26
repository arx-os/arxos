package api

import (
	"html/template"
	"net/http"
	"path/filepath"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/chi/v5/middleware"
)

// WebRouter handles web interface routing for all three tiers
type WebRouter struct {
	templates map[string]*template.Template
}

// NewWebRouter creates a new web router with template loading
func NewWebRouter() *WebRouter {
	wr := &WebRouter{
		templates: make(map[string]*template.Template),
	}
	wr.loadTemplates()
	return wr
}

// RegisterRoutes registers all web interface routes
func (wr *WebRouter) RegisterRoutes(r chi.Router) {
	// Middleware
	r.Use(middleware.Logger)
	r.Use(middleware.Recoverer)
	r.Use(middleware.Compress(5))

	// Static files
	r.Handle("/static/*", http.StripPrefix("/static/", http.FileServer(http.Dir("web/static/"))))

	// Main landing page
	r.Get("/", wr.handleLandingPage)

	// Core Tier Routes (FREE)
	r.Route("/core", func(r chi.Router) {
		r.Get("/", wr.handleCoreDashboard)
		r.Get("/dashboard", wr.handleCoreDashboard)
		r.Get("/buildings", wr.handleCoreBuildings)
		r.Get("/equipment", wr.handleCoreEquipment)
		r.Get("/spatial", wr.handleCoreSpatial)
		r.Get("/docs", wr.handleCoreDocs)
		r.Get("/upgrade", wr.handleCoreUpgrade)
	})

	// Hardware Tier Routes (FREEMIUM)
	r.Route("/hardware", func(r chi.Router) {
		r.Get("/", wr.handleHardwareDashboard)
		r.Get("/dashboard", wr.handleHardwareDashboard)
		r.Get("/devices", wr.handleHardwareDevices)
		r.Get("/gateways", wr.handleHardwareGateways)
		r.Get("/marketplace", wr.handleHardwareMarketplace)
		r.Get("/marketplace/devices/{deviceID}", wr.handleHardwareDeviceDetail)
		r.Get("/templates", wr.handleHardwareTemplates)
		r.Get("/upgrade", wr.handleHardwareUpgrade)
	})

	// Workflow Tier Routes (PAID)
	r.Route("/workflow", func(r chi.Router) {
		r.Get("/", wr.handleWorkflowDashboard)
		r.Get("/dashboard", wr.handleWorkflowDashboard)
		r.Get("/workflows", wr.handleWorkflowList)
		r.Get("/workflows/create", wr.handleWorkflowBuilder)
		r.Get("/workflows/{workflowID}", wr.handleWorkflowDetail)
		r.Get("/workorders", wr.handleWorkflowWorkOrders)
		r.Get("/workorders/create", wr.handleWorkflowCreateWorkOrder)
		r.Get("/maintenance", wr.handleWorkflowMaintenance)
		r.Get("/reports", wr.handleWorkflowReports)
		r.Get("/analytics", wr.handleWorkflowAnalytics)
		r.Get("/n8n", wr.handleWorkflowN8n)
	})

	// Documentation and Support Routes
	r.Route("/docs", func(r chi.Router) {
		r.Get("/", wr.handleDocsIndex)
		r.Get("/core", wr.handleCoreDocs)
		r.Get("/hardware", wr.handleHardwareDocs)
		r.Get("/workflow", wr.handleWorkflowDocs)
		r.Get("/api", wr.handleAPIDocs)
	})

	// Support Routes
	r.Route("/support", func(r chi.Router) {
		r.Get("/", wr.handleSupportIndex)
		r.Get("/contact", wr.handleSupportContact)
		r.Get("/status", wr.handleSupportStatus)
		r.Get("/community", wr.handleSupportCommunity)
	})
}

// Template loading
func (wr *WebRouter) loadTemplates() {
	templateDir := "web/templates"

	// Define template patterns for each tier
	templatePatterns := map[string][]string{
		"landing": {
			filepath.Join(templateDir, "index.html"),
		},
		"core_dashboard": {
			filepath.Join(templateDir, "base.html"),
			filepath.Join(templateDir, "core/dashboard.html"),
		},
		"hardware_dashboard": {
			filepath.Join(templateDir, "base.html"),
			filepath.Join(templateDir, "hardware/dashboard.html"),
		},
		"hardware_marketplace": {
			filepath.Join(templateDir, "base.html"),
			filepath.Join(templateDir, "hardware/marketplace.html"),
		},
		"workflow_dashboard": {
			filepath.Join(templateDir, "base.html"),
			filepath.Join(templateDir, "workflow/dashboard.html"),
		},
		"workflow_builder": {
			filepath.Join(templateDir, "base.html"),
			filepath.Join(templateDir, "workflow/workflow-builder.html"),
		},
	}

	// Load each template
	for name, files := range templatePatterns {
		tmpl, err := template.ParseFiles(files...)
		if err != nil {
			// Log error but continue - templates will be handled gracefully
			continue
		}
		wr.templates[name] = tmpl
	}
}

// Handler functions

func (wr *WebRouter) handleLandingPage(w http.ResponseWriter, r *http.Request) {
	wr.renderTemplate(w, "landing", nil)
}

// Core Tier Handlers
func (wr *WebRouter) handleCoreDashboard(w http.ResponseWriter, r *http.Request) {
	data := map[string]interface{}{
		"Title":       "ArxOS Core Dashboard",
		"Tier":        "core",
		"CurrentPage": "dashboard",
		"Stats": map[string]int{
			"Buildings":       12,
			"Equipment":       45,
			"SpatialFeatures": 128,
			"APICallsToday":   234,
		},
		"RecentBuildings": []map[string]string{
			{"Name": "Main Office Building", "Path": "/buildings/main-office"},
			{"Name": "Warehouse Complex", "Path": "/buildings/warehouse"},
			{"Name": "Research Facility", "Path": "/buildings/research"},
		},
		"RecentEquipment": []map[string]string{
			{"Name": "HVAC Unit A", "Type": "HVAC", "Path": "/buildings/main-office/hvac/unit-a"},
			{"Name": "Lighting System", "Type": "Lighting", "Path": "/buildings/main-office/lighting/main"},
			{"Name": "Security Camera", "Type": "Security", "Path": "/buildings/main-office/security/cam-01"},
		},
	}
	wr.renderTemplate(w, "core_dashboard", data)
}

func (wr *WebRouter) handleCoreBuildings(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement buildings management page
	http.Error(w, "Buildings page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleCoreEquipment(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement equipment management page
	http.Error(w, "Equipment page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleCoreSpatial(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement spatial data page
	http.Error(w, "Spatial page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleCoreDocs(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement core documentation page
	http.Error(w, "Core documentation coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleCoreUpgrade(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement upgrade page
	http.Error(w, "Upgrade page coming soon", http.StatusNotImplemented)
}

// Hardware Tier Handlers
func (wr *WebRouter) handleHardwareDashboard(w http.ResponseWriter, r *http.Request) {
	data := map[string]interface{}{
		"Title": "ArxOS Hardware Platform Dashboard",
		"Tier":  "hardware",
	}
	wr.renderTemplate(w, "hardware_dashboard", data)
}

func (wr *WebRouter) handleHardwareDevices(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement devices management page
	http.Error(w, "Devices page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleHardwareGateways(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement gateways management page
	http.Error(w, "Gateways page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleHardwareMarketplace(w http.ResponseWriter, r *http.Request) {
	data := map[string]interface{}{
		"Title":               "ArxOS Hardware Marketplace",
		"Tier":                "hardware",
		"CurrentPage":         "marketplace",
		"SearchQuery":         r.URL.Query().Get("search"),
		"CategoryFilter":      r.URL.Query().Get("category"),
		"CertificationFilter": r.URL.Query().Get("certification"),
		"FeaturedDevices": []map[string]interface{}{
			{
				"ID":            "1",
				"Name":          "Smart Temperature Sensor",
				"Description":   "High-precision temperature monitoring with wireless connectivity",
				"Certification": "Premium",
				"Rating":        5,
				"ReviewsCount":  128,
				"Availability":  "available",
				"Price":         89.99,
			},
			{
				"ID":            "2",
				"Name":          "Smart Light Switch",
				"Description":   "WiFi-enabled smart switch with energy monitoring",
				"Certification": "Standard",
				"Rating":        4,
				"ReviewsCount":  67,
				"Availability":  "available",
				"Price":         45.99,
			},
		},
		"Devices": []map[string]interface{}{
			{
				"ID":            "1",
				"Name":          "Smart Temperature Sensor",
				"Description":   "High-precision temperature monitoring with wireless connectivity",
				"Certification": "Premium",
				"Rating":        5,
				"ReviewsCount":  128,
				"Availability":  "available",
				"Price":         89.99,
			},
			{
				"ID":            "2",
				"Name":          "Smart Light Switch",
				"Description":   "WiFi-enabled smart switch with energy monitoring",
				"Certification": "Standard",
				"Rating":        4,
				"ReviewsCount":  67,
				"Availability":  "available",
				"Price":         45.99,
			},
			{
				"ID":            "3",
				"Name":          "Motion Detection Sensor",
				"Description":   "PIR motion sensor with configurable sensitivity",
				"Certification": "Basic",
				"Rating":        3,
				"ReviewsCount":  23,
				"Availability":  "available",
				"Price":         29.99,
			},
		},
	}
	wr.renderTemplate(w, "hardware_marketplace", data)
}

func (wr *WebRouter) handleHardwareDeviceDetail(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement device detail page
	deviceID := chi.URLParam(r, "deviceID")
	http.Error(w, "Device detail page for "+deviceID+" coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleHardwareTemplates(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement templates page
	http.Error(w, "Templates page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleHardwareUpgrade(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement upgrade page
	http.Error(w, "Upgrade page coming soon", http.StatusNotImplemented)
}

// Workflow Tier Handlers
func (wr *WebRouter) handleWorkflowDashboard(w http.ResponseWriter, r *http.Request) {
	data := map[string]interface{}{
		"Title": "ArxOS Workflow Platform Dashboard",
		"Tier":  "workflow",
	}
	wr.renderTemplate(w, "workflow_dashboard", data)
}

func (wr *WebRouter) handleWorkflowList(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement workflow list page
	http.Error(w, "Workflow list page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleWorkflowBuilder(w http.ResponseWriter, r *http.Request) {
	data := map[string]interface{}{
		"Title": "ArxOS Workflow Builder",
		"Tier":  "workflow",
	}
	wr.renderTemplate(w, "workflow_builder", data)
}

func (wr *WebRouter) handleWorkflowDetail(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement workflow detail page
	workflowID := chi.URLParam(r, "workflowID")
	http.Error(w, "Workflow detail page for "+workflowID+" coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleWorkflowWorkOrders(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement work orders page
	http.Error(w, "Work orders page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleWorkflowCreateWorkOrder(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement create work order page
	http.Error(w, "Create work order page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleWorkflowMaintenance(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement maintenance page
	http.Error(w, "Maintenance page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleWorkflowReports(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement reports page
	http.Error(w, "Reports page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleWorkflowAnalytics(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement analytics page
	http.Error(w, "Analytics page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleWorkflowN8n(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement n8n integration page
	http.Error(w, "n8n integration page coming soon", http.StatusNotImplemented)
}

// Documentation Handlers
func (wr *WebRouter) handleDocsIndex(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement documentation index page
	http.Error(w, "Documentation index coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleHardwareDocs(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement hardware documentation page
	http.Error(w, "Hardware documentation coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleWorkflowDocs(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement workflow documentation page
	http.Error(w, "Workflow documentation coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleAPIDocs(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement API documentation page
	http.Error(w, "API documentation coming soon", http.StatusNotImplemented)
}

// Support Handlers
func (wr *WebRouter) handleSupportIndex(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement support index page
	http.Error(w, "Support index coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleSupportContact(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement contact page
	http.Error(w, "Contact page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleSupportStatus(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement status page
	http.Error(w, "Status page coming soon", http.StatusNotImplemented)
}

func (wr *WebRouter) handleSupportCommunity(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement community page
	http.Error(w, "Community page coming soon", http.StatusNotImplemented)
}

// Helper function to render templates
func (wr *WebRouter) renderTemplate(w http.ResponseWriter, templateName string, data interface{}) {
	tmpl, exists := wr.templates[templateName]
	if !exists {
		http.Error(w, "Template not found", http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	err := tmpl.Execute(w, data)
	if err != nil {
		http.Error(w, "Template execution error", http.StatusInternalServerError)
		return
	}
}
