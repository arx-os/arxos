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
	
	// Construct BACnet Read Property request
	objectID := BACnetObjectID{
		Type:     objType,
		Instance: uint32(instance),
	}
	
	// Build BACnet request packet
	requestID := c.generateRequestID()
	packet := c.buildReadPropertyRequest(networkNum, objectID, PropPresentValue, requestID)
	
	// Send request and wait for response
	response, err := c.sendRequestAndWait(packet, requestID)
	if err != nil {
		log.Printf("⚠️ BACnet read error: %v", err)
		// Fall back to simulation if available
		if c.config.Simulation {
			return c.getSimulatedValue(address)
		}
		return nil, err
	}
	
	log.Printf("📡 BACnet read success: Network %d, Object %v, Instance %d = %v", 
		networkNum, objType, instance, response.Value.Value)
	
	return response.Value, nil
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
	// Parse BACnet/IP header (BVLC - BACnet Virtual Link Layer)
	if len(data) < 4 {
		log.Printf("⚠️ Invalid BACnet packet: too short (%d bytes)", len(data))
		return
	}
	
	// Check BVLC type (0x81 for BACnet/IP)
	if data[0] != 0x81 {
		log.Printf("⚠️ Invalid BACnet packet: wrong BVLC type (0x%02x)", data[0])
		return
	}
	
	// Parse BVLC function
	bvlcFunction := data[1]
	length := uint16(data[2])<<8 | uint16(data[3])
	
	if uint16(len(data)) < length {
		log.Printf("⚠️ Invalid BACnet packet: length mismatch")
		return
	}
	
	// Handle different BVLC functions
	switch bvlcFunction {
	case 0x0A: // Original-Unicast-NPDU
		c.parseNPDU(data[4:], addr)
	case 0x0B: // Original-Broadcast-NPDU
		c.parseNPDU(data[4:], addr)
	case 0x04: // Forwarded-NPDU
		if len(data) >= 10 {
			c.parseNPDU(data[10:], addr)
		}
	default:
		log.Printf("📥 Received BACnet BVLC function 0x%02x (%d bytes) from %s", 
			bvlcFunction, len(data), addr)
	}
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

// generateRequestID generates a unique request ID for tracking responses
func (c *BACnetClient) generateRequestID() uint8 {
	// Simple incrementing ID (wraps at 255)
	// In production, would need better tracking
	return uint8(time.Now().UnixNano() & 0xFF)
}

// buildReadPropertyRequest builds a BACnet Read Property request packet
func (c *BACnetClient) buildReadPropertyRequest(network uint16, objectID BACnetObjectID, property BACnetProperty, requestID uint8) []byte {
	// Build BACnet/IP packet
	packet := make([]byte, 0, 128)
	
	// BVLC header
	packet = append(packet, 0x81)  // BVLC type
	packet = append(packet, 0x0A)  // Original-Unicast-NPDU
	packet = append(packet, 0x00, 0x00) // Length (filled later)
	
	// NPDU (Network Protocol Data Unit)
	packet = append(packet, 0x01)  // Version
	packet = append(packet, 0x04)  // Control (expecting reply)
	
	// APDU (Application Protocol Data Unit)
	// PDU Type: Confirmed-Request (0x00)
	// Service Choice: Read-Property (0x0C)
	packet = append(packet, 0x00 | (requestID & 0x0F))
	packet = append(packet, 0x04)  // Max segments, max APDU
	packet = append(packet, requestID)  // Invoke ID
	packet = append(packet, 0x0C)  // Service choice: Read Property
	
	// Context Tag 0: Object Identifier
	packet = append(packet, 0x0C)  // Tag
	objectIDBytes := encodeObjectID(objectID)
	packet = append(packet, objectIDBytes...)
	
	// Context Tag 1: Property Identifier
	packet = append(packet, 0x19)  // Tag
	packet = append(packet, byte(property))
	
	// Update length in BVLC header
	length := uint16(len(packet))
	packet[2] = byte(length >> 8)
	packet[3] = byte(length & 0xFF)
	
	return packet
}

// encodeObjectID encodes a BACnet object ID
func encodeObjectID(id BACnetObjectID) []byte {
	// BACnet encodes object ID as 4 bytes:
	// 10 bits for type, 22 bits for instance
	value := (uint32(id.Type) << 22) | (id.Instance & 0x3FFFFF)
	return []byte{
		byte(value >> 24),
		byte(value >> 16),
		byte(value >> 8),
		byte(value),
	}
}

// sendRequestAndWait sends a request and waits for response
func (c *BACnetClient) sendRequestAndWait(packet []byte, requestID uint8) (*BACnetResponse, error) {
	if c.conn == nil {
		return nil, fmt.Errorf("no connection available")
	}
	
	// Create response channel
	responseChan := make(chan *BACnetResponse, 1)
	c.mutex.Lock()
	c.requests[requestID] = responseChan
	c.mutex.Unlock()
	
	// Clean up on exit
	defer func() {
		c.mutex.Lock()
		delete(c.requests, requestID)
		c.mutex.Unlock()
	}()
	
	// Send packet (broadcast for discovery)
	broadcastAddr, _ := net.ResolveUDPAddr("udp", fmt.Sprintf("255.255.255.255:%d", c.config.Port))
	_, err := c.conn.WriteTo(packet, broadcastAddr)
	if err != nil {
		return nil, fmt.Errorf("failed to send request: %w", err)
	}
	
	// Wait for response
	select {
	case response := <-responseChan:
		return response, nil
	case <-time.After(c.config.Timeout):
		return nil, fmt.Errorf("request timeout")
	case <-c.ctx.Done():
		return nil, fmt.Errorf("client shutting down")
	}
}

// parseNPDU parses the Network Protocol Data Unit
func (c *BACnetClient) parseNPDU(data []byte, addr net.Addr) {
	if len(data) < 2 {
		return
	}
	
	version := data[0]
	if version != 0x01 {
		log.Printf("⚠️ Unsupported BACnet version: 0x%02x", version)
		return
	}
	
	control := data[1]
	offset := 2
	
	// Check for DNET, DLEN, DADR
	if control&0x20 != 0 {
		if len(data) < offset+3 {
			return
		}
		dlen := data[offset+2]
		offset += 3 + int(dlen)
	}
	
	// Check for SNET, SLEN, SADR
	if control&0x08 != 0 {
		if len(data) < offset+3 {
			return
		}
		slen := data[offset+2]
		offset += 3 + int(slen)
	}
	
	// Check for hop count
	if control&0x20 != 0 {
		offset++
	}
	
	// Parse APDU
	if offset < len(data) {
		c.parseAPDU(data[offset:], addr)
	}
}

// parseAPDU parses the Application Protocol Data Unit
func (c *BACnetClient) parseAPDU(data []byte, addr net.Addr) {
	if len(data) < 3 {
		return
	}
	
	pduType := (data[0] >> 4) & 0x0F
	
	switch pduType {
	case 0x03: // Complex-ACK-PDU
		invokeID := data[1]
		serviceChoice := data[2]
		
		if serviceChoice == 0x0C { // Read-Property-ACK
			c.parseReadPropertyACK(data[3:], invokeID)
		}
		
	case 0x01: // Unconfirmed-Request-PDU
		serviceChoice := data[1]
		if serviceChoice == 0x08 { // I-Am
			c.parseIAm(data[2:], addr)
		}
	}
}

// parseReadPropertyACK parses a Read Property acknowledgment
func (c *BACnetClient) parseReadPropertyACK(data []byte, invokeID uint8) {
	// Simplified parsing - extract present value
	// In production, would need full ASN.1 decoding
	
	var value interface{}
	if len(data) >= 4 {
		// Assume real (float) value for now
		value = float64(data[len(data)-4])
	}
	
	response := &BACnetResponse{
		Value: &BACnetValue{
			Value:       value,
			Quality:     "good",
			Timestamp:   time.Now(),
			Reliability: "no-fault-detected",
		},
	}
	
	// Send to waiting request
	c.mutex.RLock()
	if ch, ok := c.requests[invokeID]; ok {
		select {
		case ch <- response:
		default:
		}
	}
	c.mutex.RUnlock()
}

// parseIAm parses an I-Am response (device discovery)
func (c *BACnetClient) parseIAm(data []byte, addr net.Addr) {
	// Extract device ID from I-Am response
	// Simplified parsing
	if len(data) < 4 {
		return
	}
	
	deviceID := uint32(data[3])
	
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if _, exists := c.devices[deviceID]; !exists {
		c.devices[deviceID] = &BACnetDevice{
			DeviceID:  deviceID,
			Name:      fmt.Sprintf("Device_%d", deviceID),
			Address: &BACnetAddress{
				IPAddress: addr.(*net.UDPAddr).IP,
				Port:      addr.(*net.UDPAddr).Port,
			},
			Objects:   make(map[BACnetObjectID]*BACnetObject),
			LastSeen:  time.Now(),
			Reachable: true,
		}
		log.Printf("✅ Discovered BACnet device: %d at %s", deviceID, addr)
	}
}

// getSimulatedValue returns a simulated value for demo mode
func (c *BACnetClient) getSimulatedValue(address string) (*BACnetValue, error) {
	c.simMutex.RLock()
	defer c.simMutex.RUnlock()
	
	if point, ok := c.simData[address]; ok {
		return &BACnetValue{
			Value:       point.CurrentValue,
			Quality:     "good",
			Timestamp:   point.LastUpdate,
			Reliability: "no-fault-detected",
		}, nil
	}
	
	// Return default value if not found
	return &BACnetValue{
		Value:       float64(20 + rand.Intn(10)),
		Quality:     "good",
		Timestamp:   time.Now(),
		Reliability: "no-fault-detected",
	}, nil
}