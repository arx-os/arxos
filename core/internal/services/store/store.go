// Package store implements the ArxOS equipment and hardware marketplace
// that integrates with BILT tokens for purchases and community contributions
package store

import (
	"encoding/json"
	"fmt"
	"math"
	"sync"
	"time"

	"github.com/arxos/arxos/core/internal/services/bilt"
)

// StoreEngine manages the ArxOS hardware and equipment marketplace
type StoreEngine struct {
	mu           sync.RWMutex
	catalog      map[string]*Product
	purchases    []Purchase
	reviews      map[string][]Review
	biltEngine   *bilt.BILTEngine
	userCarts    map[string]*Cart
	orderHistory map[string][]Order
}

// Product represents an item in the marketplace
type Product struct {
	ID           string                 `json:"id"`
	Name         string                 `json:"name"`
	Description  string                 `json:"description"`
	Category     ProductCategory        `json:"category"`
	Type         ProductType            `json:"type"`
	PriceBILT    float64                `json:"price_bilt"`    // Price in BILT tokens
	PriceUSD     float64                `json:"price_usd"`     // USD equivalent
	Stock        int                    `json:"stock"`
	Manufacturer string                 `json:"manufacturer"`
	OpenSource   bool                   `json:"open_source"`
	Specs        map[string]interface{} `json:"specs"`
	Images       []string               `json:"images"`
	Documentation []string              `json:"documentation"`
	Rating       float64                `json:"rating"`
	Reviews      int                    `json:"reviews"`
	CreatedBy    string                 `json:"created_by"`
	CreatedAt    time.Time             `json:"created_at"`
	UpdatedAt    time.Time             `json:"updated_at"`
}

// ProductCategory defines product categories
type ProductCategory string

const (
	CategorySensors     ProductCategory = "sensors"
	CategoryControllers ProductCategory = "controllers"
	CategoryActuators   ProductCategory = "actuators"
	CategoryNetworking  ProductCategory = "networking"
	CategorySafety      ProductCategory = "safety"
	CategoryTools       ProductCategory = "tools"
	CategoryKits        ProductCategory = "kits"
	CategorySoftware    ProductCategory = "software"
)

// ProductType defines specific product types
type ProductType string

const (
	// Sensors
	TypeTemperatureSensor ProductType = "temperature_sensor"
	TypeHumiditySensor    ProductType = "humidity_sensor"
	TypeMotionSensor      ProductType = "motion_sensor"
	TypeLightSensor       ProductType = "light_sensor"
	TypePressureSensor    ProductType = "pressure_sensor"
	TypeFlowSensor        ProductType = "flow_sensor"
	
	// Controllers
	TypeBASController  ProductType = "bas_controller"
	TypePLC           ProductType = "plc"
	TypeArduinoBoard  ProductType = "arduino_board"
	TypeRaspberryPi   ProductType = "raspberry_pi"
	
	// Actuators
	TypeRelay         ProductType = "relay"
	TypeServo         ProductType = "servo"
	TypeValve         ProductType = "valve"
	TypeDamper        ProductType = "damper"
	
	// Networking
	TypeWiFiModule    ProductType = "wifi_module"
	TypeLoRaModule    ProductType = "lora_module"
	TypeZigbeeModule  ProductType = "zigbee_module"
	TypeEthernet      ProductType = "ethernet"
	
	// Safety
	TypeSmokeDetector ProductType = "smoke_detector"
	TypeCODetector    ProductType = "co_detector"
	TypeEmergencyStop ProductType = "emergency_stop"
	
	// Tools
	TypeMultimeter    ProductType = "multimeter"
	TypeOscilloscope  ProductType = "oscilloscope"
	TypeLogicAnalyzer ProductType = "logic_analyzer"
	
	// Kits
	TypeStarterKit    ProductType = "starter_kit"
	TypeTrainingKit   ProductType = "training_kit"
	TypeFieldKit      ProductType = "field_kit"
)

// Purchase represents a completed purchase
type Purchase struct {
	ID           string    `json:"id"`
	UserID       string    `json:"user_id"`
	ProductID    string    `json:"product_id"`
	Quantity     int       `json:"quantity"`
	PriceBILT    float64   `json:"price_bilt"`
	Status       string    `json:"status"`
	Timestamp    time.Time `json:"timestamp"`
	ShippingInfo Shipping  `json:"shipping_info"`
}

// Review represents a product review
type Review struct {
	ID        string    `json:"id"`
	ProductID string    `json:"product_id"`
	UserID    string    `json:"user_id"`
	Rating    int       `json:"rating"` // 1-5 stars
	Comment   string    `json:"comment"`
	Verified  bool      `json:"verified"` // Verified purchase
	Helpful   int       `json:"helpful"`  // Helpful votes
	Timestamp time.Time `json:"timestamp"`
}

// Cart represents a user's shopping cart
type Cart struct {
	UserID    string     `json:"user_id"`
	Items     []CartItem `json:"items"`
	TotalBILT float64    `json:"total_bilt"`
	TotalUSD  float64    `json:"total_usd"`
	UpdatedAt time.Time  `json:"updated_at"`
}

// CartItem represents an item in the cart
type CartItem struct {
	ProductID string  `json:"product_id"`
	Quantity  int     `json:"quantity"`
	PriceBILT float64 `json:"price_bilt"`
	PriceUSD  float64 `json:"price_usd"`
}

// Order represents a completed order
type Order struct {
	ID            string      `json:"id"`
	UserID        string      `json:"user_id"`
	Items         []OrderItem `json:"items"`
	TotalBILT     float64     `json:"total_bilt"`
	TotalUSD      float64     `json:"total_usd"`
	Status        OrderStatus `json:"status"`
	PaymentMethod string      `json:"payment_method"`
	ShippingInfo  Shipping    `json:"shipping_info"`
	CreatedAt     time.Time   `json:"created_at"`
	UpdatedAt     time.Time   `json:"updated_at"`
}

// OrderItem represents an item in an order
type OrderItem struct {
	ProductID   string  `json:"product_id"`
	ProductName string  `json:"product_name"`
	Quantity    int     `json:"quantity"`
	PriceBILT   float64 `json:"price_bilt"`
	PriceUSD    float64 `json:"price_usd"`
}

// OrderStatus represents the status of an order
type OrderStatus string

const (
	OrderPending    OrderStatus = "pending"
	OrderProcessing OrderStatus = "processing"
	OrderShipped    OrderStatus = "shipped"
	OrderDelivered  OrderStatus = "delivered"
	OrderCancelled  OrderStatus = "cancelled"
)

// Shipping represents shipping information
type Shipping struct {
	Address  string    `json:"address"`
	City     string    `json:"city"`
	State    string    `json:"state"`
	ZipCode  string    `json:"zip_code"`
	Country  string    `json:"country"`
	Method   string    `json:"method"`
	Tracking string    `json:"tracking"`
	ETA      time.Time `json:"eta"`
}

// NewStoreEngine creates a new store engine
func NewStoreEngine(biltEngine *bilt.BILTEngine) *StoreEngine {
	store := &StoreEngine{
		catalog:      make(map[string]*Product),
		reviews:      make(map[string][]Review),
		biltEngine:   biltEngine,
		userCarts:    make(map[string]*Cart),
		orderHistory: make(map[string][]Order),
	}
	
	// Initialize with default products
	store.initializeDefaultCatalog()
	
	return store
}

// AddProduct adds a new product to the catalog
func (s *StoreEngine) AddProduct(product *Product) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	if product.ID == "" {
		product.ID = generateProductID()
	}
	
	if product.CreatedAt.IsZero() {
		product.CreatedAt = time.Now()
	}
	product.UpdatedAt = time.Now()
	
	// Validate product
	if err := s.validateProduct(product); err != nil {
		return fmt.Errorf("invalid product: %w", err)
	}
	
	s.catalog[product.ID] = product
	
	return nil
}

// GetProduct retrieves a product by ID
func (s *StoreEngine) GetProduct(productID string) (*Product, error) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	
	product, exists := s.catalog[productID]
	if !exists {
		return nil, fmt.Errorf("product not found: %s", productID)
	}
	
	return product, nil
}

// SearchProducts searches for products matching criteria
func (s *StoreEngine) SearchProducts(category ProductCategory, productType ProductType, openSourceOnly bool) []*Product {
	s.mu.RLock()
	defer s.mu.RUnlock()
	
	var results []*Product
	
	for _, product := range s.catalog {
		// Filter by category
		if category != "" && product.Category != category {
			continue
		}
		
		// Filter by type
		if productType != "" && product.Type != productType {
			continue
		}
		
		// Filter by open source
		if openSourceOnly && !product.OpenSource {
			continue
		}
		
		results = append(results, product)
	}
	
	return results
}

// PurchaseWithBILT purchases a product using BILT tokens
func (s *StoreEngine) PurchaseWithBILT(userID, productID string, quantity int) (*Purchase, error) {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	// Get product
	product, exists := s.catalog[productID]
	if !exists {
		return nil, fmt.Errorf("product not found: %s", productID)
	}
	
	// Check stock
	if product.Stock < quantity {
		return nil, fmt.Errorf("insufficient stock: available=%d, requested=%d", 
			product.Stock, quantity)
	}
	
	// Calculate total cost
	totalCost := product.PriceBILT * float64(quantity)
	
	// Check user balance
	balance, err := s.biltEngine.GetUserBalance(userID)
	if err != nil {
		return nil, fmt.Errorf("failed to get balance: %w", err)
	}
	
	if balance < totalCost {
		return nil, fmt.Errorf("insufficient BILT balance: have=%.2f, need=%.2f", 
			balance, totalCost)
	}
	
	// Process payment (deduct BILT tokens)
	// In production, this would be a proper transaction
	err = s.processBILTPayment(userID, totalCost, fmt.Sprintf("Purchase: %s x%d", product.Name, quantity))
	if err != nil {
		return nil, fmt.Errorf("payment failed: %w", err)
	}
	
	// Update stock
	product.Stock -= quantity
	
	// Create purchase record
	purchase := &Purchase{
		ID:        generatePurchaseID(),
		UserID:    userID,
		ProductID: productID,
		Quantity:  quantity,
		PriceBILT: totalCost,
		Status:    "completed",
		Timestamp: time.Now(),
	}
	
	s.purchases = append(s.purchases, *purchase)
	
	// Reward contributor if open source
	if product.OpenSource && product.CreatedBy != "" && product.CreatedBy != userID {
		contributorReward := totalCost * 0.05 // 5% to contributor
		s.biltEngine.RecordEarning(product.CreatedBy, contributorReward, 
			fmt.Sprintf("Open source contribution sale: %s", product.Name))
	}
	
	return purchase, nil
}

// AddReview adds a product review
func (s *StoreEngine) AddReview(review *Review) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	// Validate review
	if review.Rating < 1 || review.Rating > 5 {
		return fmt.Errorf("rating must be between 1 and 5")
	}
	
	// Check if product exists
	product, exists := s.catalog[review.ProductID]
	if !exists {
		return fmt.Errorf("product not found: %s", review.ProductID)
	}
	
	// Check if user has purchased the product
	review.Verified = s.hasUserPurchased(review.UserID, review.ProductID)
	
	// Add review
	review.ID = generateReviewID()
	review.Timestamp = time.Now()
	
	if _, exists := s.reviews[review.ProductID]; !exists {
		s.reviews[review.ProductID] = []Review{}
	}
	s.reviews[review.ProductID] = append(s.reviews[review.ProductID], *review)
	
	// Update product rating
	s.updateProductRating(product)
	
	// Award BILT tokens for verified reviews
	if review.Verified {
		s.biltEngine.RecordEarning(review.UserID, 0.5, "Product review")
	}
	
	return nil
}

// GetCart retrieves a user's cart
func (s *StoreEngine) GetCart(userID string) *Cart {
	s.mu.RLock()
	defer s.mu.RUnlock()
	
	cart, exists := s.userCarts[userID]
	if !exists {
		return &Cart{
			UserID:    userID,
			Items:     []CartItem{},
			UpdatedAt: time.Now(),
		}
	}
	
	return cart
}

// AddToCart adds an item to the user's cart
func (s *StoreEngine) AddToCart(userID, productID string, quantity int) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	
	// Get product
	product, exists := s.catalog[productID]
	if !exists {
		return fmt.Errorf("product not found: %s", productID)
	}
	
	// Get or create cart
	cart, exists := s.userCarts[userID]
	if !exists {
		cart = &Cart{
			UserID: userID,
			Items:  []CartItem{},
		}
		s.userCarts[userID] = cart
	}
	
	// Check if item already in cart
	found := false
	for i, item := range cart.Items {
		if item.ProductID == productID {
			cart.Items[i].Quantity += quantity
			found = true
			break
		}
	}
	
	if !found {
		cart.Items = append(cart.Items, CartItem{
			ProductID: productID,
			Quantity:  quantity,
			PriceBILT: product.PriceBILT,
			PriceUSD:  product.PriceUSD,
		})
	}
	
	// Update totals
	s.updateCartTotals(cart)
	cart.UpdatedAt = time.Now()
	
	return nil
}

// Helper functions

func (s *StoreEngine) validateProduct(product *Product) error {
	if product.Name == "" {
		return fmt.Errorf("product name required")
	}
	if product.PriceBILT <= 0 {
		return fmt.Errorf("price must be positive")
	}
	if product.Category == "" {
		return fmt.Errorf("category required")
	}
	return nil
}

func (s *StoreEngine) hasUserPurchased(userID, productID string) bool {
	for _, purchase := range s.purchases {
		if purchase.UserID == userID && purchase.ProductID == productID {
			return true
		}
	}
	return false
}

func (s *StoreEngine) updateProductRating(product *Product) {
	reviews := s.reviews[product.ID]
	if len(reviews) == 0 {
		return
	}
	
	total := 0.0
	for _, review := range reviews {
		total += float64(review.Rating)
	}
	
	product.Rating = math.Round(total/float64(len(reviews))*10) / 10
	product.Reviews = len(reviews)
}

func (s *StoreEngine) updateCartTotals(cart *Cart) {
	totalBILT := 0.0
	totalUSD := 0.0
	
	for _, item := range cart.Items {
		totalBILT += item.PriceBILT * float64(item.Quantity)
		totalUSD += item.PriceUSD * float64(item.Quantity)
	}
	
	cart.TotalBILT = totalBILT
	cart.TotalUSD = totalUSD
}

func (s *StoreEngine) processBILTPayment(userID string, amount float64, description string) error {
	// In production, this would be a proper blockchain transaction
	// For now, we simulate by creating a spending transaction
	return s.biltEngine.RecordEarning(userID, -amount, description)
}

func (s *StoreEngine) initializeDefaultCatalog() {
	// Add default products to the catalog
	defaultProducts := []*Product{
		{
			ID:           "temp-sensor-dht22",
			Name:         "DHT22 Temperature & Humidity Sensor",
			Description:  "High accuracy digital temperature and humidity sensor",
			Category:     CategorySensors,
			Type:         TypeTemperatureSensor,
			PriceBILT:    2.5,
			PriceUSD:     12.00,
			Stock:        100,
			Manufacturer: "Community",
			OpenSource:   true,
			Specs: map[string]interface{}{
				"accuracy_temp": "±0.5°C",
				"accuracy_rh":   "±2%",
				"range_temp":    "-40 to 80°C",
				"range_rh":      "0 to 100%",
				"interface":     "OneWire",
			},
		},
		{
			ID:           "bas-controller-arduino",
			Name:         "ArxOS BAS Controller (Arduino Mega)",
			Description:  "Open source building automation controller",
			Category:     CategoryControllers,
			Type:         TypeBASController,
			PriceBILT:    15.0,
			PriceUSD:     75.00,
			Stock:        50,
			Manufacturer: "ArxOS Community",
			OpenSource:   true,
			Specs: map[string]interface{}{
				"processor":     "ATmega2560",
				"io_pins":       54,
				"analog_inputs": 16,
				"memory":        "256KB Flash",
				"protocols":     []string{"Modbus", "BACnet", "MQTT"},
			},
		},
		{
			ID:           "motion-sensor-pir",
			Name:         "PIR Motion Sensor Module",
			Description:  "Passive infrared motion detection sensor",
			Category:     CategorySensors,
			Type:         TypeMotionSensor,
			PriceBILT:    1.5,
			PriceUSD:     7.50,
			Stock:        200,
			Manufacturer: "Community",
			OpenSource:   true,
			Specs: map[string]interface{}{
				"detection_range": "6 meters",
				"detection_angle": "110 degrees",
				"trigger_time":    "0.5-200s adjustable",
				"voltage":         "5-20V DC",
			},
		},
		{
			ID:           "relay-4ch",
			Name:         "4-Channel Relay Module",
			Description:  "Optoisolated 4-channel relay for switching AC/DC loads",
			Category:     CategoryActuators,
			Type:         TypeRelay,
			PriceBILT:    3.0,
			PriceUSD:     15.00,
			Stock:        75,
			Manufacturer: "Community",
			OpenSource:   true,
			Specs: map[string]interface{}{
				"channels":      4,
				"max_current":   "10A per channel",
				"max_voltage":   "250VAC / 30VDC",
				"control":       "5V logic",
				"isolation":     "Optoisolated",
			},
		},
		{
			ID:           "starter-kit",
			Name:         "ArxOS Building Automation Starter Kit",
			Description:  "Complete kit for learning building automation with ArxOS",
			Category:     CategoryKits,
			Type:         TypeStarterKit,
			PriceBILT:    25.0,
			PriceUSD:     125.00,
			Stock:        30,
			Manufacturer: "ArxOS",
			OpenSource:   true,
			Specs: map[string]interface{}{
				"contents": []string{
					"1x Arduino Mega",
					"2x Temperature sensors",
					"2x Motion sensors",
					"1x 4-channel relay",
					"1x WiFi module",
					"Jumper wires",
					"Training materials",
				},
			},
		},
	}
	
	for _, product := range defaultProducts {
		product.CreatedAt = time.Now()
		product.UpdatedAt = time.Now()
		product.Rating = 4.5
		product.Reviews = 0
		s.catalog[product.ID] = product
	}
}

// ID generation helpers

func generateProductID() string {
	return fmt.Sprintf("prod_%d", time.Now().UnixNano())
}

func generatePurchaseID() string {
	return fmt.Sprintf("purchase_%d", time.Now().UnixNano())
}

func generateReviewID() string {
	return fmt.Sprintf("review_%d", time.Now().UnixNano())
}

func generateOrderID() string {
	return fmt.Sprintf("order_%d", time.Now().UnixNano())
}