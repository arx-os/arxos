package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/database"
)

// EnhancedMarketplaceService provides advanced marketplace functionality
type EnhancedMarketplaceService struct {
	db                   *database.PostGISDB
	certificationService *CertificationService
}

// NewEnhancedMarketplaceService creates a new enhanced marketplace service
func NewEnhancedMarketplaceService(db *database.PostGISDB) *EnhancedMarketplaceService {
	return &EnhancedMarketplaceService{
		db:                   db,
		certificationService: NewCertificationService(db),
	}
}

// MarketplaceVendor represents a marketplace vendor
type MarketplaceVendor struct {
	ID          string                 `json:"id"`
	Name        string                 `json:"name"`
	Email       string                 `json:"email"`
	Website     string                 `json:"website"`
	Description string                 `json:"description"`
	ContactInfo map[string]interface{} `json:"contact_info"`
	Status      string                 `json:"status"`
	Rating      float64                `json:"rating"`
	TotalSales  int                    `json:"total_sales"`
	CreatedAt   time.Time              `json:"created_at"`
	UpdatedAt   time.Time              `json:"updated_at"`
}

// MarketplaceReview represents a device review
type MarketplaceReview struct {
	ID               string    `json:"id"`
	DeviceID         string    `json:"device_id"`
	UserID           string    `json:"user_id"`
	Rating           int       `json:"rating"`
	Title            string    `json:"title"`
	ReviewText       string    `json:"review_text"`
	HelpfulCount     int       `json:"helpful_count"`
	VerifiedPurchase bool      `json:"verified_purchase"`
	CreatedAt        time.Time `json:"created_at"`
	UpdatedAt        time.Time `json:"updated_at"`
}

// MarketplaceAnalytics represents marketplace analytics data
type MarketplaceAnalytics struct {
	DeviceID  string                 `json:"device_id"`
	EventType string                 `json:"event_type"`
	EventData map[string]interface{} `json:"event_data"`
	UserID    string                 `json:"user_id"`
	SessionID string                 `json:"session_id"`
	CreatedAt time.Time              `json:"created_at"`
}

// CreateVendor creates a new marketplace vendor
func (ems *EnhancedMarketplaceService) CreateVendor(ctx context.Context, vendor MarketplaceVendor) (*MarketplaceVendor, error) {
	// Validate vendor
	if vendor.Name == "" {
		return nil, fmt.Errorf("vendor name is required")
	}
	if vendor.Email == "" {
		return nil, fmt.Errorf("vendor email is required")
	}

	// Generate vendor ID
	vendorID := generateVendorID()

	// Insert vendor
	query := `
		INSERT INTO marketplace_vendors (id, name, email, website, description, contact_info, status, rating, total_sales, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
		RETURNING id, name, email, website, description, contact_info, status, rating, total_sales, created_at, updated_at`

	var createdVendor MarketplaceVendor
	var contactJSON []byte
	err := ems.db.QueryRow(ctx, query,
		vendorID,
		vendor.Name,
		vendor.Email,
		vendor.Website,
		vendor.Description,
		vendor.ContactInfo,
		vendor.Status,
		vendor.Rating,
		vendor.TotalSales,
	).Scan(
		&createdVendor.ID,
		&createdVendor.Name,
		&createdVendor.Email,
		&createdVendor.Website,
		&createdVendor.Description,
		&contactJSON,
		&createdVendor.Status,
		&createdVendor.Rating,
		&createdVendor.TotalSales,
		&createdVendor.CreatedAt,
		&createdVendor.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create vendor: %w", err)
	}

	// Parse contact info
	if err := json.Unmarshal(contactJSON, &createdVendor.ContactInfo); err != nil {
		createdVendor.ContactInfo = make(map[string]interface{})
	}

	return &createdVendor, nil
}

// GetVendor retrieves a vendor by ID
func (ems *EnhancedMarketplaceService) GetVendor(ctx context.Context, vendorID string) (*MarketplaceVendor, error) {
	query := `
		SELECT id, name, email, website, description, contact_info, status, rating, total_sales, created_at, updated_at
		FROM marketplace_vendors
		WHERE id = $1
	`

	var vendor MarketplaceVendor
	var contactJSON []byte
	err := ems.db.QueryRow(ctx, query, vendorID).Scan(
		&vendor.ID,
		&vendor.Name,
		&vendor.Email,
		&vendor.Website,
		&vendor.Description,
		&contactJSON,
		&vendor.Status,
		&vendor.Rating,
		&vendor.TotalSales,
		&vendor.CreatedAt,
		&vendor.UpdatedAt,
	)

	if err != nil {
		if err.Error() == "no rows in result set" {
			return nil, fmt.Errorf("vendor not found")
		}
		return nil, fmt.Errorf("failed to get vendor: %w", err)
	}

	// Parse contact info
	if err := json.Unmarshal(contactJSON, &vendor.ContactInfo); err != nil {
		vendor.ContactInfo = make(map[string]interface{})
	}

	return &vendor, nil
}

// ListVendors lists all active vendors
func (ems *EnhancedMarketplaceService) ListVendors(ctx context.Context) ([]*MarketplaceVendor, error) {
	query := `
		SELECT id, name, email, website, description, contact_info, status, rating, total_sales, created_at, updated_at
		FROM marketplace_vendors
		WHERE status = 'active'
		ORDER BY rating DESC, total_sales DESC
	`

	rows, err := ems.db.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to list vendors: %w", err)
	}
	defer rows.Close()

	var vendors []*MarketplaceVendor
	for rows.Next() {
		var vendor MarketplaceVendor
		var contactJSON []byte
		err := rows.Scan(
			&vendor.ID,
			&vendor.Name,
			&vendor.Email,
			&vendor.Website,
			&vendor.Description,
			&contactJSON,
			&vendor.Status,
			&vendor.Rating,
			&vendor.TotalSales,
			&vendor.CreatedAt,
			&vendor.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan vendor: %w", err)
		}

		// Parse contact info
		if err := json.Unmarshal(contactJSON, &vendor.ContactInfo); err != nil {
			vendor.ContactInfo = make(map[string]interface{})
		}

		vendors = append(vendors, &vendor)
	}

	return vendors, nil
}

// AddReview adds a review for a device
func (ems *EnhancedMarketplaceService) AddReview(ctx context.Context, review MarketplaceReview) (*MarketplaceReview, error) {
	// Validate review
	if review.DeviceID == "" {
		return nil, fmt.Errorf("device ID is required")
	}
	if review.UserID == "" {
		return nil, fmt.Errorf("user ID is required")
	}
	if review.Rating < 1 || review.Rating > 5 {
		return nil, fmt.Errorf("rating must be between 1 and 5")
	}

	// Generate review ID
	reviewID := generateReviewID()

	// Insert review
	query := `
		INSERT INTO marketplace_reviews (id, device_id, user_id, rating, title, review_text, helpful_count, verified_purchase, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
		RETURNING id, device_id, user_id, rating, title, review_text, helpful_count, verified_purchase, created_at, updated_at`

	var createdReview MarketplaceReview
	err := ems.db.QueryRow(ctx, query,
		reviewID,
		review.DeviceID,
		review.UserID,
		review.Rating,
		review.Title,
		review.ReviewText,
		review.HelpfulCount,
		review.VerifiedPurchase,
	).Scan(
		&createdReview.ID,
		&createdReview.DeviceID,
		&createdReview.UserID,
		&createdReview.Rating,
		&createdReview.Title,
		&createdReview.ReviewText,
		&createdReview.HelpfulCount,
		&createdReview.VerifiedPurchase,
		&createdReview.CreatedAt,
		&createdReview.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to add review: %w", err)
	}

	// Update device rating
	err = ems.updateDeviceRating(ctx, review.DeviceID)
	if err != nil {
		// Log error but don't fail the review creation
		fmt.Printf("Warning: failed to update device rating: %v\n", err)
	}

	return &createdReview, nil
}

// GetDeviceReviews retrieves reviews for a device
func (ems *EnhancedMarketplaceService) GetDeviceReviews(ctx context.Context, deviceID string) ([]*MarketplaceReview, error) {
	query := `
		SELECT id, device_id, user_id, rating, title, review_text, helpful_count, verified_purchase, created_at, updated_at
		FROM marketplace_reviews
		WHERE device_id = $1
		ORDER BY helpful_count DESC, created_at DESC
	`

	rows, err := ems.db.Query(ctx, query, deviceID)
	if err != nil {
		return nil, fmt.Errorf("failed to get device reviews: %w", err)
	}
	defer rows.Close()

	var reviews []*MarketplaceReview
	for rows.Next() {
		var review MarketplaceReview
		err := rows.Scan(
			&review.ID,
			&review.DeviceID,
			&review.UserID,
			&review.Rating,
			&review.Title,
			&review.ReviewText,
			&review.HelpfulCount,
			&review.VerifiedPurchase,
			&review.CreatedAt,
			&review.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan review: %w", err)
		}

		reviews = append(reviews, &review)
	}

	return reviews, nil
}

// TrackAnalytics tracks marketplace analytics
func (ems *EnhancedMarketplaceService) TrackAnalytics(ctx context.Context, analytics MarketplaceAnalytics) error {
	// Validate analytics
	if analytics.DeviceID == "" {
		return fmt.Errorf("device ID is required")
	}
	if analytics.EventType == "" {
		return fmt.Errorf("event type is required")
	}

	// Generate analytics ID
	analyticsID := generateAnalyticsID()

	// Insert analytics
	query := `
		INSERT INTO marketplace_analytics (id, device_id, event_type, event_data, user_id, session_id, created_at)
		VALUES ($1, $2, $3, $4, $5, $6, NOW())
	`

	_, err := ems.db.Exec(ctx, query,
		analyticsID,
		analytics.DeviceID,
		analytics.EventType,
		analytics.EventData,
		analytics.UserID,
		analytics.SessionID,
	)

	if err != nil {
		return fmt.Errorf("failed to track analytics: %w", err)
	}

	return nil
}

// GetMarketplaceStats retrieves marketplace statistics
func (ems *EnhancedMarketplaceService) GetMarketplaceStats(ctx context.Context) (map[string]interface{}, error) {
	stats := make(map[string]interface{})

	// Get total devices
	var totalDevices int
	err := ems.db.QueryRow(ctx, "SELECT COUNT(*) FROM certified_devices WHERE availability = 'available'").Scan(&totalDevices)
	if err != nil {
		return nil, fmt.Errorf("failed to get total devices: %w", err)
	}
	stats["total_devices"] = totalDevices

	// Get total vendors
	var totalVendors int
	err = ems.db.QueryRow(ctx, "SELECT COUNT(*) FROM marketplace_vendors WHERE status = 'active'").Scan(&totalVendors)
	if err != nil {
		return nil, fmt.Errorf("failed to get total vendors: %w", err)
	}
	stats["total_vendors"] = totalVendors

	// Get total orders
	var totalOrders int
	err = ems.db.QueryRow(ctx, "SELECT COUNT(*) FROM marketplace_orders WHERE status != 'cancelled'").Scan(&totalOrders)
	if err != nil {
		return nil, fmt.Errorf("failed to get total orders: %w", err)
	}
	stats["total_orders"] = totalOrders

	// Get total revenue
	var totalRevenue float64
	err = ems.db.QueryRow(ctx, "SELECT COALESCE(SUM(total_price), 0) FROM marketplace_orders WHERE status = 'completed'").Scan(&totalRevenue)
	if err != nil {
		return nil, fmt.Errorf("failed to get total revenue: %w", err)
	}
	stats["total_revenue"] = totalRevenue

	// Get average rating
	var avgRating float64
	err = ems.db.QueryRow(ctx, "SELECT COALESCE(AVG(rating), 0) FROM marketplace_reviews").Scan(&avgRating)
	if err != nil {
		return nil, fmt.Errorf("failed to get average rating: %w", err)
	}
	stats["average_rating"] = avgRating

	// Get top selling devices
	topDevicesQuery := `
		SELECT cd.name, cd.type, COUNT(mo.id) as sales_count
		FROM certified_devices cd
		LEFT JOIN marketplace_orders mo ON cd.id = mo.device_id AND mo.status = 'completed'
		GROUP BY cd.id, cd.name, cd.type
		ORDER BY sales_count DESC
		LIMIT 5
	`

	rows, err := ems.db.Query(ctx, topDevicesQuery)
	if err != nil {
		return nil, fmt.Errorf("failed to get top devices: %w", err)
	}
	defer rows.Close()

	var topDevices []map[string]interface{}
	for rows.Next() {
		var name, deviceType string
		var salesCount int
		err := rows.Scan(&name, &deviceType, &salesCount)
		if err != nil {
			return nil, fmt.Errorf("failed to scan top device: %w", err)
		}

		topDevices = append(topDevices, map[string]interface{}{
			"name":        name,
			"type":        deviceType,
			"sales_count": salesCount,
		})
	}
	stats["top_devices"] = topDevices

	return stats, nil
}

// Helper methods

func (ems *EnhancedMarketplaceService) updateDeviceRating(ctx context.Context, deviceID string) error {
	// Calculate average rating for device
	var avgRating float64
	err := ems.db.QueryRow(ctx, "SELECT COALESCE(AVG(rating), 0) FROM marketplace_reviews WHERE device_id = $1", deviceID).Scan(&avgRating)
	if err != nil {
		return fmt.Errorf("failed to calculate average rating: %w", err)
	}

	// Update device rating in certified_devices table
	// Note: This assumes we have a rating field in certified_devices
	// If not, we would need to add it or store it separately
	_, err = ems.db.Exec(ctx, "UPDATE certified_devices SET rating = $1 WHERE id = $2", avgRating, deviceID)
	if err != nil {
		return fmt.Errorf("failed to update device rating: %w", err)
	}

	return nil
}

func generateVendorID() string {
	return fmt.Sprintf("vendor_%d", time.Now().UnixNano())
}

func generateReviewID() string {
	return fmt.Sprintf("review_%d", time.Now().UnixNano())
}

func generateAnalyticsID() string {
	return fmt.Sprintf("analytics_%d", time.Now().UnixNano())
}
