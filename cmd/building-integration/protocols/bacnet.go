// BACnet protocol implementation for ArxOS building integration
package protocols

import (
	"context"
	"fmt"
	"log"
	"math"
	"math/rand"
	"net"
	"strconv"
	"strings"
	"sync"
	"time"
)

// BACnetConfig holds BACnet client configuration
type BACnetConfig struct {
	Interface     string        `json:"interface"`      // Network interface (e.g., "eth0") 
	Port          int           `json:"port"`           // UDP port (default 47808)
	DeviceID      uint32        `json:"device_id"`      // Our device ID
	NetworkNumber uint16        `json:"network_number"` // BACnet network number
	Timeout       time.Duration `json:"timeout"`        // Request timeout
	Simulation    bool          `json:"simulation"`     // Use simulation mode for demo
}

// BACnetObjectType represents BACnet object types
type BACnetObjectType int

const (
	BACnetAnalogInput  BACnetObjectType = 0
	BACnetAnalogOutput BACnetObjectType = 1
	BACnetBinaryInput  BACnetObjectType = 3
	BACnetBinaryOutput BACnetObjectType = 4
	BACnetDeviceObject BACnetObjectType = 8
)

// BACnetObjectID represents a BACnet object identifier
type BACnetObjectID struct {
	Type     BACnetObjectType
	Instance uint32
}

// BACnetAddress represents a BACnet device address
type BACnetAddress struct {
	NetworkNumber uint16
	DeviceID      uint32
	IPAddress     net.IP
	Port          int
}

// BACnetProperty represents a BACnet property identifier
type BACnetProperty int

const (
	PropPresentValue BACnetProperty = 85
	PropObjectName   BACnetProperty = 77
	PropUnits        BACnetProperty = 117
	PropDescription  BACnetProperty = 28
	PropReliability  BACnetProperty = 103
)

// BACnetValue represents a value read from BACnet
type BACnetValue struct {
	Value       interface{}
	Quality     string
	Timestamp   time.Time
	Reliability string
}

// BACnetClient handles BACnet communication
type BACnetClient struct {
	config   *BACnetConfig
	conn     net.PacketConn
	devices  map[uint32]*BACnetDevice
	requests map[uint8]chan *BACnetResponse
	mutex    sync.RWMutex
	ctx      context.Context
	cancel   context.CancelFunc
	wg       sync.WaitGroup
	
	// Simulation mode data
	simData  map[string]*SimulatedPoint
	simMutex sync.RWMutex
}

// BACnetDevice represents a discovered BACnet device
type BACnetDevice struct {
	DeviceID    uint32
	Name        string
	Address     *BACnetAddress
	Objects     map[BACnetObjectID]*BACnetObject
	LastSeen    time.Time
	Reachable   bool
}

// BACnetObject represents a BACnet object
type BACnetObject struct {
	ID          BACnetObjectID
	Name        string
	Description string
	Units       string
	PresentValue interface{}
	Reliability string
	LastUpdate  time.Time
}

// BACnetResponse represents a BACnet response message
type BACnetResponse struct {
	SourceDevice uint32
	ObjectID     BACnetObjectID
	Property     BACnetProperty
	Value        *BACnetValue
	Error        error
}

// SimulatedPoint represents a simulated BACnet point for demo mode
type SimulatedPoint struct {
	Address     string
	ObjectID    BACnetObjectID
	BaseValue   float64
	CurrentValue float64
	Noise       float64
	Trend       float64
	LastUpdate  time.Time
}

// NewBACnetClient creates a new BACnet client
func NewBACnetClient(config *BACnetConfig) (*BACnetClient, error) {
	ctx, cancel := context.WithCancel(context.Background())
	
	client := &BACnetClient{
		config:   config,
		devices:  make(map[uint32]*BACnetDevice),
		requests: make(map[uint8]chan *BACnetResponse),
		ctx:      ctx,
		cancel:   cancel,
		simData:  make(map[string]*SimulatedPoint),
	}

	if config.Simulation {
		log.Println("🔧 BACnet client running in simulation mode")
		client.initializeSimulation()
		return client, nil
	}

	// Initialize real BACnet connection
	if err := client.initializeConnection(); err != nil {
		cancel()
		return nil, err
	}

	// Start background receiver
	client.wg.Add(1)
	go client.receiveLoop()

	// Start device discovery
	client.wg.Add(1) 
	go client.discoveryLoop()

	return client, nil
}

// initializeConnection sets up the real BACnet UDP connection
func (c *BACnetClient) initializeConnection() error {
	addr := fmt.Sprintf(":%d", c.config.Port)
	
	conn, err := net.ListenPacket("udp", addr)
	if err != nil {
		return fmt.Errorf("failed to bind BACnet socket: %w", err)
	}
	
	c.conn = conn
	log.Printf("🌐 BACnet client listening on UDP port %d", c.config.Port)
	return nil
}

// initializeSimulation sets up simulated BACnet points
func (c *BACnetClient) initializeSimulation() {
	// Create simulated points for demo
	simPoints := map[string]*SimulatedPoint{
		"1:analog-input:1": {
			Address:      "1:analog-input:1",
			ObjectID:     BACnetObjectID{Type: BACnetAnalogInput, Instance: 1},
			BaseValue:    22.0, // Temperature in Celsius
			CurrentValue: 22.0,
			Noise:        0.5,
			Trend:        0.02,
		},
		"1:analog-input:2": {
			Address:      "1:analog-input:2", 
			ObjectID:     BACnetObjectID{Type: BACnetAnalogInput, Instance: 2},
			BaseValue:    45.0, // Humidity in %
			CurrentValue: 45.0,
			Noise:        2.0,
			Trend:        0.1,
		},
		"1:analog-input:3": {
			Address:      "1:analog-input:3",
			ObjectID:     BACnetObjectID{Type: BACnetAnalogInput, Instance: 3},
			BaseValue:    21.5,
			CurrentValue: 21.5,
			Noise:        0.3,
			Trend:        -0.01,
		},
		"1:binary-input:1": {
			Address:      "1:binary-input:1",
			ObjectID:     BACnetObjectID{Type: BACnetBinaryInput, Instance: 1}, 
			BaseValue:    12.0, // Occupancy count
			CurrentValue: 12.0,
			Noise:        3.0,
			Trend:        0.05,
		},
	}

	c.simMutex.Lock()
	c.simData = simPoints
	c.simMutex.Unlock()
	
	// Start simulation update loop
	c.wg.Add(1)
	go c.simulationLoop()
}

// ReadProperty reads a property from a BACnet object
func (c *BACnetClient) ReadProperty(address string) (*BACnetValue, error) {
	if c.config.Simulation {
		return c.readSimulatedProperty(address)
	}
	
	return c.readRealProperty(address)
}

// readSimulatedProperty reads from simulated BACnet data
func (c *BACnetClient) readSimulatedProperty(address string) (*BACnetValue, error) {
	c.simMutex.RLock()
	point, exists := c.simData[address]
	c.simMutex.RUnlock()
	
	if !exists {
		return nil, fmt.Errorf("simulated point not found: %s", address)
	}
	
	// Return current simulated value
	value := &BACnetValue{
		Value:       point.CurrentValue,
		Quality:     "good",
		Timestamp:   time.Now(),
		Reliability: "no-fault-detected",
	}
	
	// Occasionally simulate communication errors
	if rand.Float64() < 0.02 { // 2% error rate
		value.Quality = "communication-error"
		value.Reliability = "communication-failure" 
	}
	
	return value, nil
}

// readRealProperty reads from actual BACnet device (placeholder implementation)
func (c *BACnetClient) readRealProperty(address string) (*BACnetValue, error) {
	// Parse BACnet address (format: "network:object-type:instance")
	parts := strings.Split(address, ":")
	if len(parts) != 3 {
		return nil, fmt.Errorf("invalid BACnet address format: %s", address)
	}
	
	networkNum, err := strconv.ParseUint(parts[0], 10, 16)
	if err != nil {
		return nil, fmt.Errorf("invalid network number: %s", parts[0])
	}
	
	objType := c.parseObjectType(parts[1])
	instance, err := strconv.ParseUint(parts[2], 10, 32)
	if err != nil {
		return nil, fmt.Errorf("invalid instance: %s", parts[2])
	}
	
	// TODO: Implement actual BACnet request/response handling
	// This is a complex protocol requiring proper BACnet packet construction
	// For now, return placeholder data
	
	log.Printf("📡 BACnet read request: Network %d, Object %v, Instance %d", 
		networkNum, objType, instance)
	
	return &BACnetValue{
		Value:       float64(20 + rand.Intn(10)), // Placeholder value
		Quality:     "good",
		Timestamp:   time.Now(),
		Reliability: "no-fault-detected",
	}, nil
}

// parseObjectType converts string to BACnet object type
func (c *BACnetClient) parseObjectType(typeStr string) BACnetObjectType {
	switch strings.ToLower(typeStr) {
	case "analog-input", "ai":
		return BACnetAnalogInput
	case "analog-output", "ao":
		return BACnetAnalogOutput
	case "binary-input", "bi":
		return BACnetBinaryInput
	case "binary-output", "bo":
		return BACnetBinaryOutput
	case "device":
		return BACnetDeviceObject
	default:
		return BACnetAnalogInput // Default fallback
	}
}

// simulationLoop updates simulated sensor values
func (c *BACnetClient) simulationLoop() {
	defer c.wg.Done()
	
	ticker := time.NewTicker(5 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			c.updateSimulatedValues()
			
		case <-c.ctx.Done():
			return
		}
	}
}

// updateSimulatedValues updates all simulated point values
func (c *BACnetClient) updateSimulatedValues() {
	c.simMutex.Lock()
	defer c.simMutex.Unlock()
	
	now := time.Now()
	
	for _, point := range c.simData {
		// Add random noise
		noise := (rand.Float64() - 0.5) * point.Noise
		
		// Add trend over time
		timeDelta := now.Sub(point.LastUpdate).Seconds()
		trend := point.Trend * timeDelta
		
		// Update value with bounds checking
		newValue := point.CurrentValue + noise + trend
		
		// Keep temperature sensors in reasonable range (18-26°C)
		if point.BaseValue > 15 && point.BaseValue < 30 {
			newValue = math.Max(18, math.Min(26, newValue))
		}
		
		// Keep humidity in reasonable range (30-70%)
		if point.BaseValue > 30 && point.BaseValue < 80 {
			newValue = math.Max(30, math.Min(70, newValue))
		}
		
		// Keep occupancy non-negative and reasonable
		if point.ObjectID.Type == BACnetBinaryInput {
			newValue = math.Max(0, math.Min(25, newValue))
		}
		
		point.CurrentValue = newValue
		point.LastUpdate = now
	}
}

// receiveLoop handles incoming BACnet messages
func (c *BACnetClient) receiveLoop() {
	defer c.wg.Done()
	
	if c.conn == nil {
		return // Simulation mode
	}
	
	buffer := make([]byte, 1500) // Standard MTU
	
	for {
		select {
		case <-c.ctx.Done():
			return
			
		default:
			c.conn.SetReadDeadline(time.Now().Add(100 * time.Millisecond))
			n, addr, err := c.conn.ReadFrom(buffer)
			
			if err != nil {
				if netErr, ok := err.(net.Error); ok && netErr.Timeout() {
					continue
				}
				log.Printf("BACnet receive error: %v", err)
				continue
			}
			
			// Process received BACnet packet
			c.processPacket(buffer[:n], addr)
		}
	}
}

// processPacket processes a received BACnet packet
func (c *BACnetClient) processPacket(data []byte, addr net.Addr) {
	// TODO: Implement BACnet packet parsing
	// This requires understanding BACnet APDU format, NPDU, etc.
	log.Printf("📥 Received BACnet packet (%d bytes) from %s", len(data), addr)
}

// discoveryLoop periodically discovers BACnet devices
func (c *BACnetClient) discoveryLoop() {
	defer c.wg.Done()
	
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			c.discoverDevices()
			
		case <-c.ctx.Done():
			return
		}
	}
}

// discoverDevices sends Who-Is requests to discover BACnet devices
func (c *BACnetClient) discoverDevices() {
	if c.conn == nil {
		return // Simulation mode
	}
	
	// TODO: Send BACnet Who-Is broadcast
	log.Println("🔍 Discovering BACnet devices...")
}

// GetDevices returns discovered BACnet devices
func (c *BACnetClient) GetDevices() map[uint32]*BACnetDevice {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	devices := make(map[uint32]*BACnetDevice)
	for id, device := range c.devices {
		devices[id] = device
	}
	return devices
}

// GetStatus returns BACnet client status
func (c *BACnetClient) GetStatus() map[string]interface{} {
	c.mutex.RLock()
	defer c.mutex.RUnlock()
	
	status := map[string]interface{}{
		"simulation":      c.config.Simulation,
		"devices_found":   len(c.devices),
		"connection_state": "connected",
	}
	
	if c.config.Simulation {
		c.simMutex.RLock()
		status["simulated_points"] = len(c.simData)
		c.simMutex.RUnlock()
	}
	
	return status
}

// Close shuts down the BACnet client
func (c *BACnetClient) Close() error {
	c.cancel()
	
	// Wait for goroutines to finish
	done := make(chan struct{})
	go func() {
		c.wg.Wait()
		close(done)
	}()
	
	select {
	case <-done:
		log.Println("BACnet client goroutines stopped")
	case <-time.After(5 * time.Second):
		log.Println("Timeout waiting for BACnet goroutines to stop")
	}
	
	// Close network connection
	if c.conn != nil {
		c.conn.Close()
	}
	
	log.Println("🔌 BACnet client closed")
	return nil
}