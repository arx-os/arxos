package services

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/hardware"
)

// MarketplaceManager orchestrates all marketplace operations
type MarketplaceManager struct {
	db                   *database.PostGISDB
	marketplaceService   *MarketplaceService
	enhancedMarketplace  *EnhancedMarketplaceService
	certificationService *CertificationService
}

// NewMarketplaceManager creates a new marketplace manager
func NewMarketplaceManager(db *database.PostGISDB) *MarketplaceManager {
	return &MarketplaceManager{
		db:                   db,
		marketplaceService:   NewMarketplaceService(db),
		enhancedMarketplace:  NewEnhancedMarketplaceService(db),
		certificationService: NewCertificationService(db),
	}
}

// DeviceCertificationWorkflow manages the complete device certification workflow
func (mm *MarketplaceManager) DeviceCertificationWorkflow(ctx context.Context, req CertificationRequest) (*CertificationResult, error) {
	// Step 1: Submit certification request
	certificationResult, err := mm.certificationService.SubmitCertificationRequest(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to submit certification request: %w", err)
	}

	// Step 2: Process certification (in a real system, this would be automated or manual)
	// For now, we'll simulate automatic processing
	approved := true // This would be determined by actual certification logic
	notes := "Automated certification processing completed"

	// Step 3: Process the certification request
	finalResult, err := mm.certificationService.ProcessCertificationRequest(ctx, certificationResult.ID, approved, notes)
	if err != nil {
		return nil, fmt.Errorf("failed to process certification request: %w", err)
	}

	return finalResult, nil
}

// GetMarketplaceCatalog returns a comprehensive marketplace catalog
func (mm *MarketplaceManager) GetMarketplaceCatalog(ctx context.Context) (map[string]interface{}, error) {
	catalog := make(map[string]interface{})

	// Get certified devices
	devices, err := mm.marketplaceService.ListCertifiedDevices(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get certified devices: %w", err)
	}
	catalog["devices"] = devices

	// Get vendors
	vendors, err := mm.enhancedMarketplace.ListVendors(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get vendors: %w", err)
	}
	catalog["vendors"] = vendors

	// Get marketplace stats
	stats, err := mm.enhancedMarketplace.GetMarketplaceStats(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get marketplace stats: %w", err)
	}
	catalog["stats"] = stats

	return catalog, nil
}

// PurchaseDeviceWithAnalytics handles device purchase with analytics tracking
func (mm *MarketplaceManager) PurchaseDeviceWithAnalytics(ctx context.Context, req hardware.PurchaseDeviceRequest, userID, sessionID string) (*hardware.PurchaseResult, error) {
	// Track purchase intent analytics
	analytics := MarketplaceAnalytics{
		DeviceID:  req.DeviceID,
		EventType: "purchase_intent",
		EventData: map[string]interface{}{
			"quantity": req.Quantity,
			"user_id":  userID,
		},
		UserID:    userID,
		SessionID: sessionID,
	}

	err := mm.enhancedMarketplace.TrackAnalytics(ctx, analytics)
	if err != nil {
		// Log error but don't fail the purchase
		fmt.Printf("Warning: failed to track purchase intent analytics: %v\n", err)
	}

	// Process the purchase
	result, err := mm.marketplaceService.PurchaseDevice(ctx, req)
	if err != nil {
		return nil, fmt.Errorf("failed to purchase device: %w", err)
	}

	// Track successful purchase analytics
	purchaseAnalytics := MarketplaceAnalytics{
		DeviceID:  req.DeviceID,
		EventType: "purchase_completed",
		EventData: map[string]interface{}{
			"order_id":    result.ID,
			"total_price": result.TotalPrice,
			"quantity":    req.Quantity,
		},
		UserID:    userID,
		SessionID: sessionID,
	}

	err = mm.enhancedMarketplace.TrackAnalytics(ctx, purchaseAnalytics)
	if err != nil {
		// Log error but don't fail the purchase
		fmt.Printf("Warning: failed to track purchase analytics: %v\n", err)
	}

	return result, nil
}

// GetDeviceWithReviews returns device information with reviews
func (mm *MarketplaceManager) GetDeviceWithReviews(ctx context.Context, deviceID string) (map[string]interface{}, error) {
	// Get device information
	device, err := mm.marketplaceService.GetCertifiedDevice(ctx, deviceID)
	if err != nil {
		return nil, fmt.Errorf("failed to get device: %w", err)
	}

	// Get device reviews
	reviews, err := mm.enhancedMarketplace.GetDeviceReviews(ctx, deviceID)
	if err != nil {
		return nil, fmt.Errorf("failed to get device reviews: %w", err)
	}

	// Calculate review statistics
	var totalReviews int
	var avgRating float64
	if len(reviews) > 0 {
		totalReviews = len(reviews)
		var totalRating int
		for _, review := range reviews {
			totalRating += review.Rating
		}
		avgRating = float64(totalRating) / float64(totalReviews)
	}

	// Combine device info with reviews
	result := map[string]interface{}{
		"device": device,
		"reviews": map[string]interface{}{
			"reviews":        reviews,
			"total_count":    totalReviews,
			"average_rating": avgRating,
		},
	}

	return result, nil
}

// TrackDeviceView tracks when a user views a device
func (mm *MarketplaceManager) TrackDeviceView(ctx context.Context, deviceID, userID, sessionID string) error {
	analytics := MarketplaceAnalytics{
		DeviceID:  deviceID,
		EventType: "device_view",
		EventData: map[string]interface{}{
			"timestamp": "now",
		},
		UserID:    userID,
		SessionID: sessionID,
	}

	return mm.enhancedMarketplace.TrackAnalytics(ctx, analytics)
}

// GetCertificationRequests returns certification requests for admin review
func (mm *MarketplaceManager) GetCertificationRequests(ctx context.Context, status string) ([]*CertificationRequest, error) {
	return mm.certificationService.ListCertificationRequests(ctx, status)
}

// ProcessCertificationRequest processes a certification request (admin function)
func (mm *MarketplaceManager) ProcessCertificationRequest(ctx context.Context, requestID string, approved bool, notes string) (*CertificationResult, error) {
	return mm.certificationService.ProcessCertificationRequest(ctx, requestID, approved, notes)
}

// GetMarketplaceAnalytics returns comprehensive marketplace analytics
func (mm *MarketplaceManager) GetMarketplaceAnalytics(ctx context.Context, timeRange string) (map[string]interface{}, error) {
	analytics := make(map[string]interface{})

	// Get basic marketplace stats
	stats, err := mm.enhancedMarketplace.GetMarketplaceStats(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get marketplace stats: %w", err)
	}
	analytics["stats"] = stats

	// Get certification statistics
	pendingRequests, err := mm.certificationService.ListCertificationRequests(ctx, "pending")
	if err != nil {
		return nil, fmt.Errorf("failed to get pending certification requests: %w", err)
	}
	analytics["pending_certifications"] = len(pendingRequests)

	certifiedRequests, err := mm.certificationService.ListCertificationRequests(ctx, "certified")
	if err != nil {
		return nil, fmt.Errorf("failed to get certified requests: %w", err)
	}
	analytics["certified_devices"] = len(certifiedRequests)

	// Get vendor performance
	vendors, err := mm.enhancedMarketplace.ListVendors(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to get vendors: %w", err)
	}
	analytics["active_vendors"] = len(vendors)

	return analytics, nil
}

// Public accessors for router
func (mm *MarketplaceManager) GetMarketplaceService() *MarketplaceService {
	return mm.marketplaceService
}

func (mm *MarketplaceManager) GetEnhancedMarketplace() *EnhancedMarketplaceService {
	return mm.enhancedMarketplace
}

func (mm *MarketplaceManager) GetCertificationService() *CertificationService {
	return mm.certificationService
}

// InitializeMarketplace initializes the marketplace with default data
func (mm *MarketplaceManager) InitializeMarketplace(ctx context.Context) error {
	// Create some sample certified devices for the marketplace
	sampleDevices := []hardware.CreateTemplateRequest{
		{
			Name:        "ArxOS Smart Sensor Pro",
			Type:        "sensor",
			Description: "Professional-grade environmental sensor with ArxOS Premium certification",
			Schema: map[string]interface{}{
				"properties": map[string]interface{}{
					"temperature": map[string]interface{}{
						"type":        "number",
						"description": "Temperature in Celsius",
						"unit":        "°C",
						"range":       "-40 to 85",
					},
					"humidity": map[string]interface{}{
						"type":        "number",
						"description": "Humidity percentage",
						"unit":        "%",
						"range":       "0 to 100",
					},
					"pressure": map[string]interface{}{
						"type":        "number",
						"description": "Atmospheric pressure",
						"unit":        "hPa",
						"range":       "300 to 1100",
					},
				},
			},
			Firmware: []byte("premium_firmware_v2.1"),
			SDK: hardware.SDKInfo{
				Version:       "2.1.0",
				Language:      "C++",
				Documentation: "https://docs.arxos.dev/sensors/pro",
				Examples:      []string{"environmental_monitoring", "data_logging", "alerts", "calibration"},
				ReleasedAt:    ctx.Value("timestamp").(time.Time),
			},
		},
		{
			Name:        "ArxOS Gateway Hub",
			Type:        "gateway",
			Description: "Multi-protocol gateway for seamless device integration",
			Schema: map[string]interface{}{
				"properties": map[string]interface{}{
					"supported_protocols": map[string]interface{}{
						"type":        "array",
						"description": "Supported communication protocols",
						"items":       []string{"MQTT", "CoAP", "HTTP", "WebSocket"},
					},
					"max_devices": map[string]interface{}{
						"type":        "number",
						"description": "Maximum number of connected devices",
						"value":       1000,
					},
					"security_level": map[string]interface{}{
						"type":        "string",
						"description": "Security certification level",
						"value":       "Enterprise",
					},
				},
			},
			Firmware: []byte("gateway_firmware_v1.5"),
			SDK: hardware.SDKInfo{
				Version:       "1.5.0",
				Language:      "C++",
				Documentation: "https://docs.arxos.dev/gateways/hub",
				Examples:      []string{"device_management", "protocol_translation", "data_routing", "security"},
				ReleasedAt:    ctx.Value("timestamp").(time.Time),
			},
		},
	}

	// Create templates and then submit them for certification
	for _, templateReq := range sampleDevices {
		// Create template first using TemplateService
		templateService := NewTemplateService(mm.db)
		template, err := templateService.CreateTemplate(ctx, templateReq)
		if err != nil {
			return fmt.Errorf("failed to create sample template: %w", err)
		}

		// Submit for certification
		certReq := CertificationRequest{
			DeviceID:       template.ID,
			DeviceName:     template.Name,
			DeviceType:     template.Type,
			Manufacturer:   "ArxOS Official",
			Model:          template.Name,
			Specifications: template.Schema,
			Documentation:  []string{"user_manual.pdf", "api_docs.pdf", "safety_guide.pdf"},
			TestResults: map[string]interface{}{
				"safety_tests":        "passed",
				"performance_tests":   "passed",
				"security_tests":      "passed",
				"compatibility_tests": "passed",
			},
			ComplianceDocs:     []string{"ce_certificate.pdf", "fcc_certificate.pdf"},
			CertificationLevel: "Premium",
			RequestedBy:        "system",
			Notes:              "Automated certification for sample device",
		}

		_, err = mm.certificationService.SubmitCertificationRequest(ctx, certReq)
		if err != nil {
			return fmt.Errorf("failed to submit sample certification request: %w", err)
		}
	}

	return nil
}
