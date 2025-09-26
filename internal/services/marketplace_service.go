package services

import (
	"context"
	"encoding/json"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common"
	"github.com/arx-os/arxos/internal/database"
	"github.com/arx-os/arxos/internal/hardware"
)

// MarketplaceService implements the hardware marketplace for certified devices
type MarketplaceService struct {
	db *database.PostGISDB
}

// NewMarketplaceService creates a new MarketplaceService
func NewMarketplaceService(db *database.PostGISDB) *MarketplaceService {
	return &MarketplaceService{db: db}
}

// ListCertifiedDevices lists all certified devices available in the marketplace
func (ms *MarketplaceService) ListCertifiedDevices(ctx context.Context) ([]*hardware.CertifiedDevice, error) {
	query := `
		SELECT id, name, type, price, certification, description, features, specifications, availability, created_at
		FROM certified_devices
		WHERE availability = 'available'
		ORDER BY created_at DESC
	`

	rows, err := ms.db.Query(ctx, query)
	if err != nil {
		return nil, fmt.Errorf("failed to list certified devices: %w", err)
	}
	defer rows.Close()

	var devices []*hardware.CertifiedDevice
	for rows.Next() {
		var device hardware.CertifiedDevice
		var featuresJSON, specsJSON []byte
		err := rows.Scan(
			&device.ID,
			&device.Name,
			&device.Type,
			&device.Price,
			&device.Certification,
			&device.Description,
			&featuresJSON,
			&specsJSON,
			&device.Availability,
			&device.CreatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan certified device: %w", err)
		}

		// Parse JSON fields
		if err := json.Unmarshal(featuresJSON, &device.Features); err != nil {
			device.Features = []string{}
		}
		if err := json.Unmarshal(specsJSON, &device.Specifications); err != nil {
			device.Specifications = make(map[string]interface{})
		}

		devices = append(devices, &device)
	}

	return devices, nil
}

// GetCertifiedDevice retrieves a specific certified device
func (ms *MarketplaceService) GetCertifiedDevice(ctx context.Context, deviceID string) (*hardware.CertifiedDevice, error) {
	query := `
		SELECT id, name, type, price, certification, description, features, specifications, availability, created_at
		FROM certified_devices
		WHERE id = $1
	`

	var device hardware.CertifiedDevice
	var featuresJSON, specsJSON []byte
	err := ms.db.QueryRow(ctx, query, deviceID).Scan(
		&device.ID,
		&device.Name,
		&device.Type,
		&device.Price,
		&device.Certification,
		&device.Description,
		&featuresJSON,
		&specsJSON,
		&device.Availability,
		&device.CreatedAt,
	)

	if err != nil {
		if err.Error() == "no rows in result set" {
			return nil, fmt.Errorf("certified device not found")
		}
		return nil, fmt.Errorf("failed to get certified device: %w", err)
	}

	// Parse JSON fields
	if err := json.Unmarshal(featuresJSON, &device.Features); err != nil {
		device.Features = []string{}
	}
	if err := json.Unmarshal(specsJSON, &device.Specifications); err != nil {
		device.Specifications = make(map[string]interface{})
	}

	return &device, nil
}

// PurchaseDevice purchases a certified device
func (ms *MarketplaceService) PurchaseDevice(ctx context.Context, req hardware.PurchaseDeviceRequest) (*hardware.PurchaseResult, error) {
	// Validate request
	if req.DeviceID == "" {
		return nil, fmt.Errorf("device ID is required")
	}
	if req.Quantity <= 0 {
		return nil, fmt.Errorf("quantity must be greater than 0")
	}

	// Get certified device
	device, err := ms.GetCertifiedDevice(ctx, req.DeviceID)
	if err != nil {
		return nil, fmt.Errorf("failed to get certified device: %w", err)
	}

	// Check availability
	if device.Availability != "available" {
		return nil, fmt.Errorf("device is not available for purchase")
	}

	// Calculate total price
	totalPrice := device.Price * float64(req.Quantity)

	// Create order
	order := &hardware.Order{
		ID:         generateOrderID(),
		UserID:     common.GetUserIDFromContextSafe(ctx), // Get from context
		DeviceID:   req.DeviceID,
		Quantity:   req.Quantity,
		Status:     "pending",
		TotalPrice: totalPrice,
		Shipping:   req.Shipping,
		Payment:    req.Payment,
		CreatedAt:  time.Now(),
		UpdatedAt:  time.Now(),
	}

	// Insert order
	query := `
		INSERT INTO marketplace_orders (id, user_id, device_id, quantity, status, total_price, shipping_info, payment_info, created_at, updated_at)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
		RETURNING id, user_id, device_id, quantity, status, total_price, shipping_info, payment_info, created_at, updated_at`

	var createdOrder hardware.Order
	var shippingJSON, paymentJSON []byte
	err = ms.db.QueryRow(ctx, query,
		order.ID,
		order.UserID,
		order.DeviceID,
		order.Quantity,
		order.Status,
		order.TotalPrice,
		order.Shipping,
		order.Payment,
	).Scan(
		&createdOrder.ID,
		&createdOrder.UserID,
		&createdOrder.DeviceID,
		&createdOrder.Quantity,
		&createdOrder.Status,
		&createdOrder.TotalPrice,
		&shippingJSON,
		&paymentJSON,
		&createdOrder.CreatedAt,
		&createdOrder.UpdatedAt,
	)

	if err != nil {
		return nil, fmt.Errorf("failed to create order: %w", err)
	}

	// Parse JSON fields
	if err := json.Unmarshal(shippingJSON, &createdOrder.Shipping); err != nil {
		createdOrder.Shipping = hardware.ShippingInfo{}
	}
	if err := json.Unmarshal(paymentJSON, &createdOrder.Payment); err != nil {
		createdOrder.Payment = hardware.PaymentInfo{}
	}

	// Create purchase result
	result := &hardware.PurchaseResult{
		ID:           createdOrder.ID,
		Status:       createdOrder.Status,
		DeviceID:     createdOrder.DeviceID,
		OrderNumber:  fmt.Sprintf("ORD-%s", createdOrder.ID),
		TrackingInfo: "Processing...",
		TotalPrice:   createdOrder.TotalPrice,
		PurchasedAt:  createdOrder.CreatedAt,
	}

	return result, nil
}

// ListOrders lists orders for a user
func (ms *MarketplaceService) ListOrders(ctx context.Context, userID string) ([]*hardware.Order, error) {
	query := `
		SELECT id, user_id, device_id, quantity, status, total_price, shipping_info, payment_info, created_at, updated_at
		FROM marketplace_orders
		WHERE user_id = $1
		ORDER BY created_at DESC
	`

	rows, err := ms.db.Query(ctx, query, userID)
	if err != nil {
		return nil, fmt.Errorf("failed to list orders: %w", err)
	}
	defer rows.Close()

	var orders []*hardware.Order
	for rows.Next() {
		var order hardware.Order
		var shippingJSON, paymentJSON []byte
		err := rows.Scan(
			&order.ID,
			&order.UserID,
			&order.DeviceID,
			&order.Quantity,
			&order.Status,
			&order.TotalPrice,
			&shippingJSON,
			&paymentJSON,
			&order.CreatedAt,
			&order.UpdatedAt,
		)
		if err != nil {
			return nil, fmt.Errorf("failed to scan order: %w", err)
		}

		// Parse JSON fields
		if err := json.Unmarshal(shippingJSON, &order.Shipping); err != nil {
			order.Shipping = hardware.ShippingInfo{}
		}
		if err := json.Unmarshal(paymentJSON, &order.Payment); err != nil {
			order.Payment = hardware.PaymentInfo{}
		}

		orders = append(orders, &order)
	}

	return orders, nil
}

// GetOrder retrieves a specific order
func (ms *MarketplaceService) GetOrder(ctx context.Context, orderID string) (*hardware.Order, error) {
	query := `
		SELECT id, user_id, device_id, quantity, status, total_price, shipping_info, payment_info, created_at, updated_at
		FROM marketplace_orders
		WHERE id = $1
	`

	var order hardware.Order
	var shippingJSON, paymentJSON []byte
	err := ms.db.QueryRow(ctx, query, orderID).Scan(
		&order.ID,
		&order.UserID,
		&order.DeviceID,
		&order.Quantity,
		&order.Status,
		&order.TotalPrice,
		&shippingJSON,
		&paymentJSON,
		&order.CreatedAt,
		&order.UpdatedAt,
	)

	if err != nil {
		if err.Error() == "no rows in result set" {
			return nil, fmt.Errorf("order not found")
		}
		return nil, fmt.Errorf("failed to get order: %w", err)
	}

	// Parse JSON fields
	if err := json.Unmarshal(shippingJSON, &order.Shipping); err != nil {
		order.Shipping = hardware.ShippingInfo{}
	}
	if err := json.Unmarshal(paymentJSON, &order.Payment); err != nil {
		order.Payment = hardware.PaymentInfo{}
	}

	return &order, nil
}

// CancelOrder cancels an order
func (ms *MarketplaceService) CancelOrder(ctx context.Context, orderID string) error {
	// Get order to validate it exists and can be cancelled
	order, err := ms.GetOrder(ctx, orderID)
	if err != nil {
		return fmt.Errorf("order not found: %w", err)
	}

	// Check if order can be cancelled
	if order.Status == "shipped" || order.Status == "delivered" {
		return fmt.Errorf("order cannot be cancelled: status is %s", order.Status)
	}

	// Update order status
	query := `
		UPDATE marketplace_orders 
		SET status = 'cancelled', updated_at = NOW()
		WHERE id = $1
	`

	_, err = ms.db.Exec(ctx, query, orderID)
	if err != nil {
		return fmt.Errorf("failed to cancel order: %w", err)
	}

	return nil
}

// Helper functions

func generateOrderID() string {
	return fmt.Sprintf("ord_%d", time.Now().UnixNano())
}
