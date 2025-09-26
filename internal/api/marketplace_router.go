package api

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/arx-os/arxos/internal/hardware"
	"github.com/arx-os/arxos/internal/services"
	"github.com/go-chi/chi/v5"
)

// MarketplaceRouter handles marketplace-related API routes
type MarketplaceRouter struct {
	marketplaceManager *services.MarketplaceManager
}

// NewMarketplaceRouter creates a new marketplace router
func NewMarketplaceRouter(marketplaceManager *services.MarketplaceManager) *MarketplaceRouter {
	return &MarketplaceRouter{
		marketplaceManager: marketplaceManager,
	}
}

// RegisterRoutes registers all marketplace API routes
func (mr *MarketplaceRouter) RegisterRoutes(r chi.Router) {
	r.Route("/api/v1/marketplace", func(r chi.Router) {
		// Marketplace catalog
		r.Get("/catalog", mr.handleGetCatalog)
		r.Get("/stats", mr.handleGetStats)
		r.Get("/analytics", mr.handleGetAnalytics)

		// Device management
		r.Get("/devices", mr.handleListDevices)
		r.Get("/devices/{deviceID}", mr.handleGetDevice)
		r.Get("/devices/{deviceID}/reviews", mr.handleGetDeviceReviews)
		r.Post("/devices/{deviceID}/reviews", mr.handleAddReview)
		r.Post("/devices/{deviceID}/view", mr.handleTrackDeviceView)

		// Purchase management
		r.Post("/purchase", mr.handlePurchaseDevice)
		r.Get("/orders", mr.handleListOrders)
		r.Get("/orders/{orderID}", mr.handleGetOrder)
		r.Post("/orders/{orderID}/cancel", mr.handleCancelOrder)

		// Certification management (admin)
		r.Post("/certification/submit", mr.handleSubmitCertification)
		r.Get("/certification/requests", mr.handleGetCertificationRequests)
		r.Post("/certification/{requestID}/process", mr.handleProcessCertification)

		// Vendor management
		r.Get("/vendors", mr.handleListVendors)
		r.Get("/vendors/{vendorID}", mr.handleGetVendor)
		r.Post("/vendors", mr.handleCreateVendor)
	})
}

// Handler functions

func (mr *MarketplaceRouter) handleGetCatalog(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	catalog, err := mr.marketplaceManager.GetMarketplaceCatalog(ctx)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(catalog)
}

func (mr *MarketplaceRouter) handleGetStats(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	stats, err := mr.marketplaceManager.GetMarketplaceAnalytics(ctx, "all")
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(stats)
}

func (mr *MarketplaceRouter) handleGetAnalytics(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	timeRange := r.URL.Query().Get("range")
	if timeRange == "" {
		timeRange = "30d"
	}

	analytics, err := mr.marketplaceManager.GetMarketplaceAnalytics(ctx, timeRange)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(analytics)
}

func (mr *MarketplaceRouter) handleListDevices(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// Get devices from marketplace service
	devices, err := mr.marketplaceManager.GetMarketplaceService().ListCertifiedDevices(ctx)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(devices)
}

func (mr *MarketplaceRouter) handleGetDevice(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	deviceID := chi.URLParam(r, "deviceID")

	device, err := mr.marketplaceManager.GetDeviceWithReviews(ctx, deviceID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(device)
}

func (mr *MarketplaceRouter) handleGetDeviceReviews(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	deviceID := chi.URLParam(r, "deviceID")

	reviews, err := mr.marketplaceManager.GetEnhancedMarketplace().GetDeviceReviews(ctx, deviceID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(reviews)
}

func (mr *MarketplaceRouter) handleAddReview(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	deviceID := chi.URLParam(r, "deviceID")

	var review services.MarketplaceReview
	if err := json.NewDecoder(r.Body).Decode(&review); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	review.DeviceID = deviceID
	// TODO: Get userID from authentication context
	review.UserID = "current_user"

	createdReview, err := mr.marketplaceManager.GetEnhancedMarketplace().AddReview(ctx, review)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(createdReview)
}

func (mr *MarketplaceRouter) handleTrackDeviceView(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	deviceID := chi.URLParam(r, "deviceID")

	// TODO: Get userID and sessionID from authentication context
	userID := "current_user"
	sessionID := "session_123"

	err := mr.marketplaceManager.TrackDeviceView(ctx, deviceID, userID, sessionID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
}

func (mr *MarketplaceRouter) handlePurchaseDevice(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var purchaseReq struct {
		DeviceID string                 `json:"device_id"`
		Quantity int                    `json:"quantity"`
		Shipping map[string]interface{} `json:"shipping"`
		Payment  map[string]interface{} `json:"payment"`
	}

	if err := json.NewDecoder(r.Body).Decode(&purchaseReq); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// TODO: Get userID and sessionID from authentication context
	userID := "current_user"
	sessionID := "session_123"

	// Convert to hardware.PurchaseDeviceRequest
	hardwareReq := hardware.PurchaseDeviceRequest{
		DeviceID: purchaseReq.DeviceID,
		Quantity: purchaseReq.Quantity,
		Shipping: hardware.ShippingInfo{
			Address: hardware.AddressInfo{
				Name:    "Default Address",
				Street:  "123 Main St",
				City:    "Default City",
				State:   "Default State",
				ZipCode: "12345",
				Country: "Default Country",
			},
			Method:            "standard",
			Tracking:          "",
			EstimatedDelivery: time.Now().AddDate(0, 0, 7),
		},
		Payment: hardware.PaymentInfo{
			Method:      "credit_card",
			Status:      "pending",
			Amount:      0.0, // Will be calculated
			Currency:    "USD",
			ProcessedAt: time.Now(),
		},
	}

	result, err := mr.marketplaceManager.PurchaseDeviceWithAnalytics(ctx, hardwareReq, userID, sessionID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(result)
}

func (mr *MarketplaceRouter) handleListOrders(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	// TODO: Get userID from authentication context
	userID := "current_user"

	orders, err := mr.marketplaceManager.GetMarketplaceService().ListOrders(ctx, userID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(orders)
}

func (mr *MarketplaceRouter) handleGetOrder(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	orderID := chi.URLParam(r, "orderID")

	order, err := mr.marketplaceManager.GetMarketplaceService().GetOrder(ctx, orderID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(order)
}

func (mr *MarketplaceRouter) handleCancelOrder(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	orderID := chi.URLParam(r, "orderID")

	err := mr.marketplaceManager.GetMarketplaceService().CancelOrder(ctx, orderID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.WriteHeader(http.StatusOK)
}

func (mr *MarketplaceRouter) handleSubmitCertification(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var certReq services.CertificationRequest
	if err := json.NewDecoder(r.Body).Decode(&certReq); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// TODO: Get userID from authentication context
	certReq.RequestedBy = "current_user"

	result, err := mr.marketplaceManager.DeviceCertificationWorkflow(ctx, certReq)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(result)
}

func (mr *MarketplaceRouter) handleGetCertificationRequests(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	status := r.URL.Query().Get("status")

	requests, err := mr.marketplaceManager.GetCertificationRequests(ctx, status)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(requests)
}

func (mr *MarketplaceRouter) handleProcessCertification(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	requestID := chi.URLParam(r, "requestID")

	var req struct {
		Approved bool   `json:"approved"`
		Notes    string `json:"notes"`
	}

	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	result, err := mr.marketplaceManager.ProcessCertificationRequest(ctx, requestID, req.Approved, req.Notes)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(result)
}

func (mr *MarketplaceRouter) handleListVendors(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	vendors, err := mr.marketplaceManager.GetEnhancedMarketplace().ListVendors(ctx)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(vendors)
}

func (mr *MarketplaceRouter) handleGetVendor(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	vendorID := chi.URLParam(r, "vendorID")

	vendor, err := mr.marketplaceManager.GetEnhancedMarketplace().GetVendor(ctx, vendorID)
	if err != nil {
		http.Error(w, err.Error(), http.StatusNotFound)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(vendor)
}

func (mr *MarketplaceRouter) handleCreateVendor(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()

	var vendor services.MarketplaceVendor
	if err := json.NewDecoder(r.Body).Decode(&vendor); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	createdVendor, err := mr.marketplaceManager.GetEnhancedMarketplace().CreateVendor(ctx, vendor)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusCreated)
	json.NewEncoder(w).Encode(createdVendor)
}
