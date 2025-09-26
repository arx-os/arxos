package api

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/arx-os/arxos/internal/hardware"
	"github.com/go-chi/chi/v5"
)

// HardwareHandlers handles Hardware tier API endpoints
type HardwareHandlers struct {
	hardwarePlatform *hardware.Platform
}

// NewHardwareHandlers creates a new HardwareHandlers instance
func NewHardwareHandlers(hardwarePlatform *hardware.Platform) *HardwareHandlers {
	return &HardwareHandlers{
		hardwarePlatform: hardwarePlatform,
	}
}

// MarketplaceDevice represents a device in the marketplace
type MarketplaceDevice struct {
	ID            string  `json:"id"`
	Name          string  `json:"name"`
	Description   string  `json:"description"`
	Type          string  `json:"type"`
	Certification string  `json:"certification"`
	Rating        float64 `json:"rating"`
	ReviewsCount  int     `json:"reviews_count"`
	Availability  string  `json:"availability"`
	Price         float64 `json:"price"`
	Vendor        string  `json:"vendor"`
	ImageURL      string  `json:"image_url"`
	CreatedAt     string  `json:"created_at"`
}

// RegisterHardwareRoutes registers Hardware tier API routes
func (hh *HardwareHandlers) RegisterHardwareRoutes(r chi.Router) {
	r.Route("/api/v1/hardware", func(r chi.Router) {
		// Device management
		r.Get("/devices", hh.handleListDevices)
		r.Post("/devices", hh.handleRegisterDevice)
		r.Get("/devices/{id}", hh.handleGetDevice)
		r.Put("/devices/{id}", hh.handleUpdateDevice)
		r.Delete("/devices/{id}", hh.handleDeleteDevice)

		// Gateway management
		r.Get("/gateways", hh.handleListGateways)
		r.Post("/gateways", hh.handleDeployGateway)
		r.Get("/gateways/{id}", hh.handleGetGateway)
		r.Put("/gateways/{id}", hh.handleUpdateGateway)
		r.Delete("/gateways/{id}", hh.handleDeleteGateway)

		// Template management
		r.Get("/templates", hh.handleListTemplates)
		r.Get("/templates/{id}", hh.handleGetTemplate)
		r.Post("/templates", hh.handleCreateTemplate)
	})

	r.Route("/api/v1/marketplace", func(r chi.Router) {
		// Marketplace endpoints
		r.Get("/devices", hh.handleMarketplaceDevices)
		r.Get("/devices/featured", hh.handleFeaturedDevices)
		r.Get("/devices/{id}", hh.handleGetMarketplaceDevice)
		r.Post("/cart/add", hh.handleAddToCart)
		r.Get("/cart", hh.handleGetCart)
		r.Delete("/cart/{id}", hh.handleRemoveFromCart)

		// Vendor management
		r.Get("/vendors", hh.handleListVendors)
		r.Post("/vendors", hh.handleCreateVendor)
		r.Get("/vendors/{id}", hh.handleGetVendor)

		// Reviews
		r.Get("/devices/{id}/reviews", hh.handleGetDeviceReviews)
		r.Post("/devices/{id}/reviews", hh.handleAddReview)
	})
}

// Marketplace Devices Handler
func (hh *HardwareHandlers) handleMarketplaceDevices(w http.ResponseWriter, r *http.Request) {
	// Get query parameters
	search := r.URL.Query().Get("search")
	category := r.URL.Query().Get("category")
	certification := r.URL.Query().Get("certification")
	sort := r.URL.Query().Get("sort")
	limitStr := r.URL.Query().Get("limit")

	limit := 20
	if limitStr != "" {
		if l, err := strconv.Atoi(limitStr); err == nil {
			limit = l
		}
	}

	// Mock data for now - in production, this would query the database
	devices := []MarketplaceDevice{
		{
			ID:            "1",
			Name:          "Smart Temperature Sensor",
			Description:   "High-precision temperature monitoring with wireless connectivity",
			Type:          "sensor",
			Certification: "Premium",
			Rating:        4.8,
			ReviewsCount:  128,
			Availability:  "available",
			Price:         89.99,
			Vendor:        "TechCorp Sensors",
			ImageURL:      "/static/images/temp-sensor.jpg",
			CreatedAt:     "2024-01-15",
		},
		{
			ID:            "2",
			Name:          "Smart Light Switch",
			Description:   "WiFi-enabled smart switch with energy monitoring",
			Type:          "actuator",
			Certification: "Standard",
			Rating:        4.2,
			ReviewsCount:  67,
			Availability:  "available",
			Price:         45.99,
			Vendor:        "LightTech Solutions",
			ImageURL:      "/static/images/light-switch.jpg",
			CreatedAt:     "2024-01-10",
		},
		{
			ID:            "3",
			Name:          "Motion Detection Sensor",
			Description:   "PIR motion sensor with configurable sensitivity",
			Type:          "sensor",
			Certification: "Basic",
			Rating:        3.9,
			ReviewsCount:  23,
			Availability:  "available",
			Price:         29.99,
			Vendor:        "MotionTech",
			ImageURL:      "/static/images/motion-sensor.jpg",
			CreatedAt:     "2024-01-05",
		},
		{
			ID:            "4",
			Name:          "Smart Gateway Hub",
			Description:   "Central hub for managing multiple IoT devices",
			Type:          "gateway",
			Certification: "Premium",
			Rating:        4.6,
			ReviewsCount:  89,
			Availability:  "available",
			Price:         199.99,
			Vendor:        "HubTech Pro",
			ImageURL:      "/static/images/gateway.jpg",
			CreatedAt:     "2024-01-12",
		},
	}

	// Apply filters
	filteredDevices := []MarketplaceDevice{}
	for _, device := range devices {
		// Search filter
		if search != "" {
			if !contains(device.Name, search) && !contains(device.Description, search) {
				continue
			}
		}

		// Category filter
		if category != "" && device.Type != category {
			continue
		}

		// Certification filter
		if certification != "" && device.Certification != certification {
			continue
		}

		filteredDevices = append(filteredDevices, device)
	}

	// Apply sorting
	switch sort {
	case "price_low":
		// Sort by price ascending
		for i := 0; i < len(filteredDevices)-1; i++ {
			for j := i + 1; j < len(filteredDevices); j++ {
				if filteredDevices[i].Price > filteredDevices[j].Price {
					filteredDevices[i], filteredDevices[j] = filteredDevices[j], filteredDevices[i]
				}
			}
		}
	case "price_high":
		// Sort by price descending
		for i := 0; i < len(filteredDevices)-1; i++ {
			for j := i + 1; j < len(filteredDevices); j++ {
				if filteredDevices[i].Price < filteredDevices[j].Price {
					filteredDevices[i], filteredDevices[j] = filteredDevices[j], filteredDevices[i]
				}
			}
		}
	case "rating":
		// Sort by rating descending
		for i := 0; i < len(filteredDevices)-1; i++ {
			for j := i + 1; j < len(filteredDevices); j++ {
				if filteredDevices[i].Rating < filteredDevices[j].Rating {
					filteredDevices[i], filteredDevices[j] = filteredDevices[j], filteredDevices[i]
				}
			}
		}
	}

	// Limit results
	if len(filteredDevices) > limit {
		filteredDevices = filteredDevices[:limit]
	}

	// If this is an HTMX request, return HTML fragment
	if r.Header.Get("HX-Request") == "true" {
		w.Header().Set("Content-Type", "text/html")
		html := ""
		for _, device := range filteredDevices {
			html += `
				<div class="device-card" hx-get="/hardware/marketplace/devices/` + device.ID + `" hx-target="body" hx-push-url="true">
					<div class="relative">
						<div class="device-image">
							<i class="fas fa-microchip"></i>
						</div>
						<div class="certification-badge ` + device.Certification + `">` + device.Certification + `</div>
					</div>
					<div class="p-4">
						<h3 class="font-semibold text-lg mb-2">` + device.Name + `</h3>
						<p class="text-sm text-gray-600 mb-2">` + device.Description + `</p>
						<div class="flex items-center justify-between mb-3">
							<div class="flex items-center gap-1">
								` + generateStars(device.Rating) + `
								<span class="text-sm text-gray-600 ml-1">(` + strconv.Itoa(device.ReviewsCount) + `)</span>
							</div>
							<span class="tier-status ` + device.Availability + `">` + device.Availability + `</span>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-lg font-bold text-green-600">$` + strconv.FormatFloat(device.Price, 'f', 2, 64) + `</span>
							<button class="tier-btn tier-btn-primary hardware" 
									hx-post="/api/v1/marketplace/cart/add" 
									hx-vals='{"device_id": "` + device.ID + `"}'
									hx-target="#cart-notification">
								<i class="fas fa-shopping-cart"></i>
								Add to Cart
							</button>
						</div>
					</div>
				</div>
			`
		}
		if html == "" {
			html = `
				<div class="text-center py-8 col-span-3">
					<i class="fas fa-search text-4xl text-gray-400 mb-4"></i>
					<h3 class="text-lg font-semibold text-gray-600">No devices found</h3>
					<p class="text-gray-500">Try adjusting your search criteria</p>
				</div>
			`
		}
		w.Write([]byte(html))
		return
	}

	// Regular JSON API response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(filteredDevices)
}

// Featured Devices Handler
func (hh *HardwareHandlers) handleFeaturedDevices(w http.ResponseWriter, r *http.Request) {
	// Mock featured devices - in production, this would query the database
	featuredDevices := []MarketplaceDevice{
		{
			ID:            "1",
			Name:          "Smart Temperature Sensor",
			Description:   "High-precision temperature monitoring with wireless connectivity",
			Type:          "sensor",
			Certification: "Premium",
			Rating:        4.8,
			ReviewsCount:  128,
			Availability:  "available",
			Price:         89.99,
			Vendor:        "TechCorp Sensors",
			ImageURL:      "/static/images/temp-sensor.jpg",
			CreatedAt:     "2024-01-15",
		},
		{
			ID:            "2",
			Name:          "Smart Light Switch",
			Description:   "WiFi-enabled smart switch with energy monitoring",
			Type:          "actuator",
			Certification: "Standard",
			Rating:        4.2,
			ReviewsCount:  67,
			Availability:  "available",
			Price:         45.99,
			Vendor:        "LightTech Solutions",
			ImageURL:      "/static/images/light-switch.jpg",
			CreatedAt:     "2024-01-10",
		},
	}

	// If this is an HTMX request, return HTML fragment
	if r.Header.Get("HX-Request") == "true" {
		w.Header().Set("Content-Type", "text/html")
		html := ""
		for _, device := range featuredDevices {
			html += `
				<div class="device-card" hx-get="/hardware/marketplace/devices/` + device.ID + `" hx-target="body" hx-push-url="true">
					<div class="relative">
						<div class="device-image">
							<i class="fas fa-microchip"></i>
						</div>
						<div class="certification-badge ` + device.Certification + `">` + device.Certification + `</div>
					</div>
					<div class="p-4">
						<h3 class="font-semibold text-lg mb-2">` + device.Name + `</h3>
						<p class="text-sm text-gray-600 mb-2">` + device.Description + `</p>
						<div class="flex items-center justify-between mb-3">
							<div class="flex items-center gap-1">
								` + generateStars(device.Rating) + `
								<span class="text-sm text-gray-600 ml-1">(` + strconv.Itoa(device.ReviewsCount) + `)</span>
							</div>
							<span class="tier-status ` + device.Availability + `">` + device.Availability + `</span>
						</div>
						<div class="flex items-center justify-between">
							<span class="text-lg font-bold text-green-600">$` + strconv.FormatFloat(device.Price, 'f', 2, 64) + `</span>
							<button class="tier-btn tier-btn-primary hardware" 
									hx-post="/api/v1/marketplace/cart/add" 
									hx-vals='{"device_id": "` + device.ID + `"}'
									hx-target="#cart-notification">
								<i class="fas fa-shopping-cart"></i>
								Add to Cart
							</button>
						</div>
					</div>
				</div>
			`
		}
		w.Write([]byte(html))
		return
	}

	// Regular JSON API response
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(featuredDevices)
}

// Cart Handlers
func (hh *HardwareHandlers) handleAddToCart(w http.ResponseWriter, r *http.Request) {
	// TODO: Implement cart functionality
	w.Header().Set("Content-Type", "text/html")
	w.Write([]byte(`
		<div id="cart-notification" class="fixed top-4 right-4 bg-green-600 text-white px-4 py-2 rounded-lg shadow-lg">
			<i class="fas fa-check mr-2"></i>
			Added to cart successfully!
		</div>
		<script>
			setTimeout(() => {
				document.getElementById('cart-notification').remove();
			}, 3000);
		</script>
	`))
}

// Device Management Handlers (Placeholder implementations)
func (hh *HardwareHandlers) handleListDevices(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleRegisterDevice(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleGetDevice(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleUpdateDevice(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleDeleteDevice(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

// Gateway Management Handlers (Placeholder implementations)
func (hh *HardwareHandlers) handleListGateways(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleDeployGateway(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleGetGateway(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleUpdateGateway(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleDeleteGateway(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

// Template Management Handlers (Placeholder implementations)
func (hh *HardwareHandlers) handleListTemplates(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleGetTemplate(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleCreateTemplate(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

// Marketplace Handlers (Placeholder implementations)
func (hh *HardwareHandlers) handleGetMarketplaceDevice(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleGetCart(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleRemoveFromCart(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleListVendors(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleCreateVendor(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleGetVendor(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleGetDeviceReviews(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

func (hh *HardwareHandlers) handleAddReview(w http.ResponseWriter, r *http.Request) {
	http.Error(w, "Not implemented", http.StatusNotImplemented)
}

// Helper functions
func contains(s, substr string) bool {
	return len(s) >= len(substr) && s[:len(substr)] == substr
}

func generateStars(rating float64) string {
	stars := ""
	for i := 1; i <= 5; i++ {
		if float64(i) <= rating {
			stars += `<i class="fas fa-star text-yellow-400"></i>`
		} else {
			stars += `<i class="fas fa-star text-gray-300"></i>`
		}
	}
	return stars
}
