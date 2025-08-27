// Modbus protocol implementation for ArxOS building integration
package protocols

import (
	"context"
	"encoding/binary"
	"fmt"
	"log"
	"math"
	"math/rand"
	"net"
	"strconv"
	"sync"
	"time"
)

// ModbusConfig holds Modbus client configuration
type ModbusConfig struct {
	Mode       string        `json:"mode"`        // "tcp", "rtu", "ascii"
	Address    string        `json:"address"`     // TCP: "host:port", RTU: "/dev/ttyUSB0"
	SlaveID    uint8         `json:"slave_id"`    // Modbus slave/unit ID
	BaudRate   int           `json:"baud_rate"`   // For RTU/ASCII serial
	Parity     string        `json:"parity"`      // "none", "even", "odd"
	StopBits   int           `json:"stop_bits"`   // 1 or 2
	DataBits   int           `json:"data_bits"`   // 7 or 8
	Timeout    time.Duration `json:"timeout"`     // Request timeout
	Simulation bool          `json:"simulation"`  // Use simulation mode
}

// ModbusFunctionCode represents Modbus function codes
type ModbusFunctionCode uint8

const (
	ReadCoils            ModbusFunctionCode = 0x01
	ReadDiscreteInputs   ModbusFunctionCode = 0x02
	ReadHoldingRegisters ModbusFunctionCode = 0x03
	ReadInputRegisters   ModbusFunctionCode = 0x04
	WriteSingleCoil      ModbusFunctionCode = 0x05
	WriteSingleRegister  ModbusFunctionCode = 0x06
	WriteMultipleCoils   ModbusFunctionCode = 0x0F
	WriteMultipleRegisters ModbusFunctionCode = 0x10
)

// ModbusDataType represents different data interpretations
type ModbusDataType string

const (
	DataTypeInt16    ModbusDataType = "int16"
	DataTypeUint16   ModbusDataType = "uint16"
	DataTypeInt32    ModbusDataType = "int32"
	DataTypeUint32   ModbusDataType = "uint32"
	DataTypeFloat32  ModbusDataType = "float32"
	DataTypeBool     ModbusDataType = "bool"
)

// ModbusRequest represents a Modbus request
type ModbusRequest struct {
	SlaveID      uint8
	Function     ModbusFunctionCode
	StartAddress uint16
	Quantity     uint16
	Data         []byte
}

// ModbusResponse represents a Modbus response
type ModbusResponse struct {
	SlaveID       uint8
	Function      ModbusFunctionCode
	Data          []byte
	ExceptionCode uint8
	Error         error
}

// ModbusValue represents a value read from Modbus
type ModbusValue struct {
	Value     interface{}
	DataType  ModbusDataType
	Address   uint16
	Quality   string
	Timestamp time.Time
	RawData   []byte
}

// ModbusClient handles Modbus communication
type ModbusClient struct {
	config     *ModbusConfig
	conn       net.Conn
	mutex      sync.Mutex
	ctx        context.Context
	cancel     context.CancelFunc
	wg         sync.WaitGroup
	
	// Transaction handling
	transactionID uint16
	
	// Simulation mode data
	simRegisters map[uint16]*SimulatedRegister
	simCoils     map[uint16]*SimulatedCoil
	simMutex     sync.RWMutex
}

// SimulatedRegister represents a simulated Modbus register
type SimulatedRegister struct {
	Address      uint16
	Value        uint16
	FloatValue   float32
	DataType     ModbusDataType
	BaseValue    float64
	Noise        float64
	Trend        float64
	LastUpdate   time.Time
}

// SimulatedCoil represents a simulated Modbus coil
type SimulatedCoil struct {
	Address    uint16
	Value      bool
	LastUpdate time.Time
}

// NewModbusClient creates a new Modbus client
func NewModbusClient(config *ModbusConfig) (*ModbusClient, error) {
	ctx, cancel := context.WithCancel(context.Background())
	
	client := &ModbusClient{
		config:       config,
		ctx:          ctx,
		cancel:       cancel,
		simRegisters: make(map[uint16]*SimulatedRegister),
		simCoils:     make(map[uint16]*SimulatedCoil),
	}

	if config.Simulation {
		log.Println("🔧 Modbus client running in simulation mode")
		client.initializeSimulation()
		return client, nil
	}

	// Initialize real Modbus connection
	if err := client.connect(); err != nil {
		cancel()
		return nil, err
	}

	return client, nil
}

// connect establishes the Modbus connection
func (c *ModbusClient) connect() error {
	switch c.config.Mode {
	case "tcp":
		return c.connectTCP()
	case "rtu":
		return c.connectRTU()
	case "ascii":
		return c.connectASCII()
	default:
		return fmt.Errorf("unsupported Modbus mode: %s", c.config.Mode)
	}
}

// connectTCP establishes a Modbus TCP connection
func (c *ModbusClient) connectTCP() error {
	conn, err := net.DialTimeout("tcp", c.config.Address, c.config.Timeout)
	if err != nil {
		return fmt.Errorf("failed to connect to Modbus TCP: %w", err)
	}
	
	c.conn = conn
	log.Printf("🌐 Modbus TCP client connected to %s", c.config.Address)
	return nil
}

// connectRTU establishes a Modbus RTU serial connection
func (c *ModbusClient) connectRTU() error {
	// TODO: Implement RTU serial connection
	return fmt.Errorf("Modbus RTU not yet implemented")
}

// connectASCII establishes a Modbus ASCII serial connection
func (c *ModbusClient) connectASCII() error {
	// TODO: Implement ASCII serial connection
	return fmt.Errorf("Modbus ASCII not yet implemented")
}

// initializeSimulation sets up simulated Modbus registers and coils
func (c *ModbusClient) initializeSimulation() {
	// Initialize simulated registers for various building systems
	simRegisters := map[uint16]*SimulatedRegister{
		// HVAC system registers (30001-30010)
		30001: {Address: 30001, DataType: DataTypeFloat32, BaseValue: 15.5, Noise: 0.5, Trend: 0.01}, // Supply temp
		30002: {Address: 30002, DataType: DataTypeFloat32, BaseValue: 24.0, Noise: 0.3, Trend: -0.005}, // Return temp
		30003: {Address: 30003, DataType: DataTypeUint16, BaseValue: 850, Noise: 50, Trend: 2}, // Supply pressure
		30004: {Address: 30004, DataType: DataTypeUint16, BaseValue: 750, Noise: 30, Trend: -1}, // Return pressure
		
		// Environmental sensors (40001-40020) 
		40001: {Address: 40001, DataType: DataTypeFloat32, BaseValue: 650.0, Noise: 50.0, Trend: 2.0}, // CO2 ppm (conference room)
		40002: {Address: 40002, DataType: DataTypeFloat32, BaseValue: 450.0, Noise: 30.0, Trend: 1.0}, // CO2 ppm (open office)
		40003: {Address: 40003, DataType: DataTypeFloat32, BaseValue: 68.5, Noise: 3.0, Trend: 0.1}, // Light level
		40004: {Address: 40004, DataType: DataTypeFloat32, BaseValue: 239.8, Noise: 2.0, Trend: 0.03}, // Voltage L3
		40005: {Address: 40005, DataType: DataTypeFloat32, BaseValue: 195.4, Noise: 10.0, Trend: 0.2}, // Current L1
		
		// Power monitoring registers (40101-40120)
		40101: {Address: 40101, DataType: DataTypeFloat32, BaseValue: 45.7, Noise: 5.0, Trend: 0.1}, // Main power (kW)
		40102: {Address: 40102, DataType: DataTypeFloat32, BaseValue: 240.5, Noise: 2.0, Trend: 0.05}, // Voltage L1
		40103: {Address: 40103, DataType: DataTypeFloat32, BaseValue: 241.2, Noise: 2.0, Trend: -0.02}, // Voltage L2
		
		// Water system registers (40201-40220)
		40201: {Address: 40201, DataType: DataTypeFloat32, BaseValue: 3.2, Noise: 0.2, Trend: 0.01}, // Water flow rate
		40202: {Address: 40202, DataType: DataTypeUint16, BaseValue: 85, Noise: 5, Trend: 0.5}, // Water pressure
		40203: {Address: 40203, DataType: DataTypeFloat32, BaseValue: 18.5, Noise: 0.5, Trend: 0.02}, // Water temperature
	}

	// Initialize simulated coils for digital I/O
	simCoils := map[uint16]*SimulatedCoil{
		// HVAC control coils (00001-00020)
		1:  {Address: 1, Value: true},   // AHU enable
		2:  {Address: 2, Value: false},  // Heating enable
		3:  {Address: 3, Value: true},   // Cooling enable
		4:  {Address: 4, Value: false},  // Fan high speed
		5:  {Address: 5, Value: true},   // Economizer enable
		
		// Lighting control coils (00101-00120)
		101: {Address: 101, Value: true},  // Office lights
		102: {Address: 102, Value: true},  // Conference room lights
		103: {Address: 103, Value: false}, // Emergency lights
		104: {Address: 104, Value: true},  // Exterior lights
		
		// Security system coils (00201-00220)
		201: {Address: 201, Value: false}, // Alarm active
		202: {Address: 202, Value: true},  // Security system armed
		203: {Address: 203, Value: false}, // Motion detected
		204: {Address: 204, Value: true},  // Door locked
	}

	c.simMutex.Lock()
	c.simRegisters = simRegisters
	c.simCoils = simCoils
	c.simMutex.Unlock()
	
	// Initialize current values
	for _, reg := range simRegisters {
		reg.Value = uint16(reg.BaseValue)
		reg.FloatValue = float32(reg.BaseValue)
		reg.LastUpdate = time.Now()
	}
	
	// Start simulation update loop
	c.wg.Add(1)
	go c.simulationLoop()
}

// ReadHoldingRegister reads a single holding register
func (c *ModbusClient) ReadHoldingRegister(address uint16, dataType ModbusDataType) (*ModbusValue, error) {
	return c.ReadHoldingRegisters(address, 1, dataType)
}

// ReadHoldingRegisters reads multiple holding registers
func (c *ModbusClient) ReadHoldingRegisters(startAddress uint16, quantity uint16, dataType ModbusDataType) (*ModbusValue, error) {
	if c.config.Simulation {
		return c.readSimulatedHoldingRegisters(startAddress, quantity, dataType)
	}
	
	return c.readRealHoldingRegisters(startAddress, quantity, dataType)
}

// ReadInputRegister reads a single input register  
func (c *ModbusClient) ReadInputRegister(address uint16, dataType ModbusDataType) (*ModbusValue, error) {
	return c.ReadInputRegisters(address, 1, dataType)
}

// ReadInputRegisters reads multiple input registers
func (c *ModbusClient) ReadInputRegisters(startAddress uint16, quantity uint16, dataType ModbusDataType) (*ModbusValue, error) {
	if c.config.Simulation {
		return c.readSimulatedInputRegisters(startAddress, quantity, dataType)
	}
	
	return c.readRealInputRegisters(startAddress, quantity, dataType)
}

// ReadCoil reads a single coil
func (c *ModbusClient) ReadCoil(address uint16) (*ModbusValue, error) {
	return c.ReadCoils(address, 1)
}

// ReadCoils reads multiple coils
func (c *ModbusClient) ReadCoils(startAddress uint16, quantity uint16) (*ModbusValue, error) {
	if c.config.Simulation {
		return c.readSimulatedCoils(startAddress, quantity)
	}
	
	return c.readRealCoils(startAddress, quantity)
}

// ParseAddress parses a Modbus address string (e.g., "40001", "30001", "00001")
func (c *ModbusClient) ParseAddress(address string) (uint16, ModbusFunctionCode, error) {
	addr, err := strconv.ParseUint(address, 10, 16)
	if err != nil {
		return 0, 0, fmt.Errorf("invalid address format: %s", address)
	}
	
	modbusAddr := uint16(addr)
	var function ModbusFunctionCode
	
	// Determine function based on address range
	switch {
	case modbusAddr >= 1 && modbusAddr <= 9999: // Coils (0x)
		function = ReadCoils
		modbusAddr = modbusAddr - 1 // Modbus addresses are 0-based
	case modbusAddr >= 10001 && modbusAddr <= 19999: // Discrete Inputs (1x)
		function = ReadDiscreteInputs  
		modbusAddr = modbusAddr - 10001
	case modbusAddr >= 30001 && modbusAddr <= 39999: // Input Registers (3x)
		function = ReadInputRegisters
		modbusAddr = modbusAddr - 30001
	case modbusAddr >= 40001 && modbusAddr <= 49999: // Holding Registers (4x)
		function = ReadHoldingRegisters
		modbusAddr = modbusAddr - 40001
	default:
		return 0, 0, fmt.Errorf("address out of valid Modbus range: %d", addr)
	}
	
	return modbusAddr, function, nil
}

// readSimulatedHoldingRegisters reads from simulated holding registers
func (c *ModbusClient) readSimulatedHoldingRegisters(startAddress uint16, quantity uint16, dataType ModbusDataType) (*ModbusValue, error) {
	// Convert from 0-based to 40000-based addressing for simulation lookup
	simAddress := startAddress + 40001
	
	c.simMutex.RLock()
	reg, exists := c.simRegisters[simAddress]
	c.simMutex.RUnlock()
	
	if !exists {
		// Create a default register if it doesn't exist
		value := &ModbusValue{
			Value:     uint16(0),
			DataType:  dataType,
			Address:   startAddress,
			Quality:   "good",
			Timestamp: time.Now(),
		}
		return value, nil
	}
	
	// Convert value based on data type
	var convertedValue interface{}
	switch dataType {
	case DataTypeUint16:
		convertedValue = reg.Value
	case DataTypeInt16:
		convertedValue = int16(reg.Value)
	case DataTypeFloat32:
		convertedValue = reg.FloatValue
	case DataTypeUint32, DataTypeInt32:
		// For 32-bit values, we'd need to read 2 registers
		convertedValue = uint32(reg.Value)
	default:
		convertedValue = reg.Value
	}
	
	// Simulate occasional communication errors
	quality := "good"
	if rand.Float64() < 0.01 { // 1% error rate
		quality = "communication-error"
	}
	
	value := &ModbusValue{
		Value:     convertedValue,
		DataType:  dataType,
		Address:   startAddress,
		Quality:   quality,
		Timestamp: time.Now(),
	}
	
	return value, nil
}

// readSimulatedInputRegisters reads from simulated input registers
func (c *ModbusClient) readSimulatedInputRegisters(startAddress uint16, quantity uint16, dataType ModbusDataType) (*ModbusValue, error) {
	// Convert from 0-based to 30000-based addressing
	simAddress := startAddress + 30001
	
	c.simMutex.RLock()
	reg, exists := c.simRegisters[simAddress]
	c.simMutex.RUnlock()
	
	if !exists {
		value := &ModbusValue{
			Value:     uint16(0),
			DataType:  dataType,
			Address:   startAddress,
			Quality:   "good",
			Timestamp: time.Now(),
		}
		return value, nil
	}
	
	var convertedValue interface{}
	switch dataType {
	case DataTypeUint16:
		convertedValue = reg.Value
	case DataTypeFloat32:
		convertedValue = reg.FloatValue
	default:
		convertedValue = reg.Value
	}
	
	return &ModbusValue{
		Value:     convertedValue,
		DataType:  dataType,
		Address:   startAddress,
		Quality:   "good",
		Timestamp: time.Now(),
	}, nil
}

// readSimulatedCoils reads from simulated coils
func (c *ModbusClient) readSimulatedCoils(startAddress uint16, quantity uint16) (*ModbusValue, error) {
	// Convert from 0-based to 1-based addressing
	simAddress := startAddress + 1
	
	c.simMutex.RLock()
	coil, exists := c.simCoils[simAddress]
	c.simMutex.RUnlock()
	
	if !exists {
		return &ModbusValue{
			Value:     false,
			DataType:  DataTypeBool,
			Address:   startAddress,
			Quality:   "good",
			Timestamp: time.Now(),
		}, nil
	}
	
	return &ModbusValue{
		Value:     coil.Value,
		DataType:  DataTypeBool,
		Address:   startAddress,
		Quality:   "good",
		Timestamp: time.Now(),
	}, nil
}

// readRealHoldingRegisters reads from actual Modbus device
func (c *ModbusClient) readRealHoldingRegisters(startAddress uint16, quantity uint16, dataType ModbusDataType) (*ModbusValue, error) {
	request := &ModbusRequest{
		SlaveID:      c.config.SlaveID,
		Function:     ReadHoldingRegisters,
		StartAddress: startAddress,
		Quantity:     quantity,
	}
	
	response, err := c.sendRequest(request)
	if err != nil {
		return nil, err
	}
	
	// Parse response data based on data type
	value, err := c.parseRegisterData(response.Data, dataType, startAddress)
	if err != nil {
		return nil, err
	}
	
	return value, nil
}

// readRealInputRegisters reads from actual Modbus device
func (c *ModbusClient) readRealInputRegisters(startAddress uint16, quantity uint16, dataType ModbusDataType) (*ModbusValue, error) {
	request := &ModbusRequest{
		SlaveID:      c.config.SlaveID,
		Function:     ReadInputRegisters,
		StartAddress: startAddress,
		Quantity:     quantity,
	}
	
	response, err := c.sendRequest(request)
	if err != nil {
		return nil, err
	}
	
	value, err := c.parseRegisterData(response.Data, dataType, startAddress)
	if err != nil {
		return nil, err
	}
	
	return value, nil
}

// readRealCoils reads from actual Modbus device
func (c *ModbusClient) readRealCoils(startAddress uint16, quantity uint16) (*ModbusValue, error) {
	request := &ModbusRequest{
		SlaveID:      c.config.SlaveID,
		Function:     ReadCoils,
		StartAddress: startAddress,
		Quantity:     quantity,
	}
	
	response, err := c.sendRequest(request)
	if err != nil {
		return nil, err
	}
	
	// Parse coil data (first bit of first byte for single coil)
	value := false
	if len(response.Data) > 0 {
		value = (response.Data[0] & 0x01) == 0x01
	}
	
	return &ModbusValue{
		Value:     value,
		DataType:  DataTypeBool,
		Address:   startAddress,
		Quality:   "good",
		Timestamp: time.Now(),
		RawData:   response.Data,
	}, nil
}

// sendRequest sends a Modbus request and waits for response
func (c *ModbusClient) sendRequest(request *ModbusRequest) (*ModbusResponse, error) {
	c.mutex.Lock()
	defer c.mutex.Unlock()
	
	if c.conn == nil {
		return nil, fmt.Errorf("Modbus connection not established")
	}
	
	// Build Modbus TCP ADU (Application Data Unit)
	adu := c.buildTCPADU(request)
	
	// Send request
	c.conn.SetWriteDeadline(time.Now().Add(c.config.Timeout))
	_, err := c.conn.Write(adu)
	if err != nil {
		return nil, fmt.Errorf("failed to send Modbus request: %w", err)
	}
	
	// Read response
	c.conn.SetReadDeadline(time.Now().Add(c.config.Timeout))
	buffer := make([]byte, 256)
	n, err := c.conn.Read(buffer)
	if err != nil {
		return nil, fmt.Errorf("failed to read Modbus response: %w", err)
	}
	
	// Parse response
	response, err := c.parseTCPADU(buffer[:n])
	if err != nil {
		return nil, fmt.Errorf("failed to parse Modbus response: %w", err)
	}
	
	return response, nil
}

// buildTCPADU builds a Modbus TCP Application Data Unit
func (c *ModbusClient) buildTCPADU(request *ModbusRequest) []byte {
	c.transactionID++
	
	// MBAP Header (7 bytes) + PDU
	var adu []byte
	
	// Transaction ID (2 bytes)
	adu = append(adu, byte(c.transactionID>>8), byte(c.transactionID))
	
	// Protocol ID (2 bytes) - always 0 for Modbus/TCP
	adu = append(adu, 0x00, 0x00)
	
	// Length field (2 bytes) - will be filled after PDU is built
	lengthPos := len(adu)
	adu = append(adu, 0x00, 0x00)
	
	// Unit ID (1 byte)
	adu = append(adu, request.SlaveID)
	
	// PDU (Protocol Data Unit)
	pdu := c.buildPDU(request)
	adu = append(adu, pdu...)
	
	// Fill length field (Unit ID + PDU length)
	length := uint16(1 + len(pdu))
	adu[lengthPos] = byte(length >> 8)
	adu[lengthPos+1] = byte(length)
	
	return adu
}

// buildPDU builds a Modbus Protocol Data Unit
func (c *ModbusClient) buildPDU(request *ModbusRequest) []byte {
	var pdu []byte
	
	// Function code
	pdu = append(pdu, byte(request.Function))
	
	switch request.Function {
	case ReadCoils, ReadDiscreteInputs, ReadHoldingRegisters, ReadInputRegisters:
		// Starting address (2 bytes)
		pdu = append(pdu, byte(request.StartAddress>>8), byte(request.StartAddress))
		// Quantity (2 bytes)
		pdu = append(pdu, byte(request.Quantity>>8), byte(request.Quantity))
		
	case WriteSingleCoil:
		// Address (2 bytes)
		pdu = append(pdu, byte(request.StartAddress>>8), byte(request.StartAddress))
		// Value (2 bytes) - 0xFF00 for ON, 0x0000 for OFF
		if len(request.Data) > 0 && request.Data[0] != 0 {
			pdu = append(pdu, 0xFF, 0x00)
		} else {
			pdu = append(pdu, 0x00, 0x00)
		}
		
	case WriteSingleRegister:
		// Address (2 bytes)
		pdu = append(pdu, byte(request.StartAddress>>8), byte(request.StartAddress))
		// Value (2 bytes)
		if len(request.Data) >= 2 {
			pdu = append(pdu, request.Data[0], request.Data[1])
		} else {
			pdu = append(pdu, 0x00, 0x00)
		}
	}
	
	return pdu
}

// parseTCPADU parses a Modbus TCP response
func (c *ModbusClient) parseTCPADU(adu []byte) (*ModbusResponse, error) {
	if len(adu) < 8 {
		return nil, fmt.Errorf("invalid Modbus TCP ADU length: %d", len(adu))
	}
	
	// Skip MBAP header (6 bytes) and extract Unit ID + PDU
	unitID := adu[6]
	pdu := adu[7:]
	
	return c.parsePDU(pdu, unitID)
}

// parsePDU parses a Modbus Protocol Data Unit
func (c *ModbusClient) parsePDU(pdu []byte, slaveID uint8) (*ModbusResponse, error) {
	if len(pdu) < 1 {
		return nil, fmt.Errorf("empty PDU")
	}
	
	response := &ModbusResponse{
		SlaveID:  slaveID,
		Function: ModbusFunctionCode(pdu[0]),
	}
	
	// Check for exception response
	if pdu[0]&0x80 == 0x80 {
		if len(pdu) < 2 {
			return nil, fmt.Errorf("invalid exception response")
		}
		response.ExceptionCode = pdu[1]
		response.Error = fmt.Errorf("Modbus exception code: %d", pdu[1])
		return response, nil
	}
	
	// Parse normal response based on function code
	switch ModbusFunctionCode(pdu[0]) {
	case ReadCoils, ReadDiscreteInputs:
		if len(pdu) < 2 {
			return nil, fmt.Errorf("invalid read coils response")
		}
		byteCount := pdu[1]
		if len(pdu) < int(2+byteCount) {
			return nil, fmt.Errorf("insufficient data in response")
		}
		response.Data = pdu[2 : 2+byteCount]
		
	case ReadHoldingRegisters, ReadInputRegisters:
		if len(pdu) < 2 {
			return nil, fmt.Errorf("invalid read registers response")
		}
		byteCount := pdu[1]
		if len(pdu) < int(2+byteCount) {
			return nil, fmt.Errorf("insufficient data in response")
		}
		response.Data = pdu[2 : 2+byteCount]
	}
	
	return response, nil
}

// parseRegisterData parses register data based on data type
func (c *ModbusClient) parseRegisterData(data []byte, dataType ModbusDataType, address uint16) (*ModbusValue, error) {
	if len(data) < 2 {
		return nil, fmt.Errorf("insufficient register data")
	}
	
	var value interface{}
	
	switch dataType {
	case DataTypeUint16:
		value = binary.BigEndian.Uint16(data[:2])
		
	case DataTypeInt16:
		value = int16(binary.BigEndian.Uint16(data[:2]))
		
	case DataTypeUint32:
		if len(data) < 4 {
			return nil, fmt.Errorf("insufficient data for uint32")
		}
		value = binary.BigEndian.Uint32(data[:4])
		
	case DataTypeInt32:
		if len(data) < 4 {
			return nil, fmt.Errorf("insufficient data for int32")
		}
		value = int32(binary.BigEndian.Uint32(data[:4]))
		
	case DataTypeFloat32:
		if len(data) < 4 {
			return nil, fmt.Errorf("insufficient data for float32")
		}
		bits := binary.BigEndian.Uint32(data[:4])
		value = math.Float32frombits(bits)
		
	default:
		value = binary.BigEndian.Uint16(data[:2])
	}
	
	return &ModbusValue{
		Value:     value,
		DataType:  dataType,
		Address:   address,
		Quality:   "good",
		Timestamp: time.Now(),
		RawData:   data,
	}, nil
}

// simulationLoop updates simulated register and coil values
func (c *ModbusClient) simulationLoop() {
	defer c.wg.Done()
	
	ticker := time.NewTicker(3 * time.Second)
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

// updateSimulatedValues updates all simulated register values
func (c *ModbusClient) updateSimulatedValues() {
	c.simMutex.Lock()
	defer c.simMutex.Unlock()
	
	now := time.Now()
	
	// Update registers
	for _, reg := range c.simRegisters {
		// Add random noise
		noise := (rand.Float64() - 0.5) * reg.Noise
		
		// Add trend over time
		timeDelta := now.Sub(reg.LastUpdate).Seconds()
		trend := reg.Trend * timeDelta
		
		// Calculate new value
		newValue := reg.BaseValue + noise + trend
		
		// Apply realistic bounds based on register type
		switch reg.Address {
		case 30001, 30002, 40203: // Temperature sensors
			newValue = math.Max(10, math.Min(35, newValue))
		case 40001, 40002: // CO2 sensors (now at 40001, 40002)
			newValue = math.Max(350, math.Min(2000, newValue))
		case 40101: // Power consumption (now at 40101)
			newValue = math.Max(20, math.Min(80, newValue))
		case 40102, 40103, 40004: // Voltages
			newValue = math.Max(230, math.Min(250, newValue))
		case 40201: // Water flow rate
			newValue = math.Max(0.5, math.Min(10.0, newValue))
		}
		
		reg.BaseValue = newValue
		reg.Value = uint16(newValue)
		reg.FloatValue = float32(newValue)
		reg.LastUpdate = now
	}
	
	// Occasionally flip some coil states
	if rand.Float64() < 0.1 { // 10% chance per update
		for _, coil := range c.simCoils {
			if rand.Float64() < 0.2 { // 20% chance for each coil
				coil.Value = !coil.Value
				coil.LastUpdate = now
			}
		}
	}
}

// GetStatus returns Modbus client status
func (c *ModbusClient) GetStatus() map[string]interface{} {
	status := map[string]interface{}{
		"mode":           c.config.Mode,
		"simulation":     c.config.Simulation,
		"slave_id":       c.config.SlaveID,
		"connection":     c.conn != nil,
	}
	
	if c.config.Simulation {
		c.simMutex.RLock()
		status["simulated_registers"] = len(c.simRegisters)
		status["simulated_coils"] = len(c.simCoils)
		c.simMutex.RUnlock()
	}
	
	return status
}

// Close shuts down the Modbus client
func (c *ModbusClient) Close() error {
	c.cancel()
	
	// Wait for goroutines to finish
	done := make(chan struct{})
	go func() {
		c.wg.Wait()
		close(done)
	}()
	
	select {
	case <-done:
		log.Println("Modbus client goroutines stopped")
	case <-time.After(5 * time.Second):
		log.Println("Timeout waiting for Modbus goroutines to stop")
	}
	
	// Close connection
	if c.conn != nil {
		c.conn.Close()
	}
	
	log.Println("🔌 Modbus client closed")
	return nil
}