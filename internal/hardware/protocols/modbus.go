package protocols

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// ModbusProtocol implements Modbus RTU/TCP communication protocol
type ModbusProtocol struct {
	name         string
	version      string
	connected    bool
	client       ModbusClient
	config       map[string]interface{}
	capabilities []string
}

// ModbusClient represents a Modbus client interface
type ModbusClient interface {
	Connect() error
	Disconnect() error
	ReadHoldingRegisters(slaveID byte, address uint16, quantity uint16) ([]byte, error)
	WriteHoldingRegister(slaveID byte, address uint16, value uint16) error
	ReadInputRegisters(slaveID byte, address uint16, quantity uint16) ([]byte, error)
	ReadCoils(slaveID byte, address uint16, quantity uint16) ([]byte, error)
	WriteCoil(slaveID byte, address uint16, value bool) error
	IsConnected() bool
}

// ModbusConfig represents Modbus configuration
type ModbusConfig struct {
	Type     string `json:"type"`      // "rtu" or "tcp"
	Address  string `json:"address"`   // Serial port or TCP address
	BaudRate int    `json:"baud_rate"` // For RTU
	DataBits int    `json:"data_bits"` // For RTU
	StopBits int    `json:"stop_bits"` // For RTU
	Parity   string `json:"parity"`    // For RTU
	Port     int    `json:"port"`      // For TCP
	Timeout  int    `json:"timeout"`   // Connection timeout in seconds
}

// NewModbusProtocol creates a new Modbus protocol instance
func NewModbusProtocol() *ModbusProtocol {
	return &ModbusProtocol{
		name:      "modbus",
		version:   "1.0",
		connected: false,
		capabilities: []string{
			"read_holding_registers",
			"write_holding_register",
			"read_input_registers",
			"read_coils",
			"write_coil",
			"rtu",
			"tcp",
		},
	}
}

// Name returns the protocol name
func (m *ModbusProtocol) Name() string {
	return m.name
}

// Version returns the protocol version
func (m *ModbusProtocol) Version() string {
	return m.version
}

// Connect establishes a Modbus connection
func (m *ModbusProtocol) Connect(ctx context.Context, config map[string]interface{}) error {
	m.config = config

	// Parse Modbus configuration
	modbusConfig, err := m.parseConfig(config)
	if err != nil {
		return fmt.Errorf("failed to parse Modbus config: %w", err)
	}

	// Create Modbus client based on type
	if modbusConfig.Type == "tcp" {
		m.client = NewMockModbusTCPClient(modbusConfig)
	} else {
		m.client = NewMockModbusRTUClient(modbusConfig)
	}

	// Connect
	if err := m.client.Connect(); err != nil {
		return fmt.Errorf("failed to connect Modbus client: %w", err)
	}

	m.connected = true
	logger.Info("Modbus %s protocol connected to %s", modbusConfig.Type, modbusConfig.Address)
	return nil
}

// Disconnect closes the Modbus connection
func (m *ModbusProtocol) Disconnect(ctx context.Context) error {
	if m.client != nil {
		if err := m.client.Disconnect(); err != nil {
			return fmt.Errorf("failed to disconnect Modbus client: %w", err)
		}
	}

	m.connected = false
	logger.Info("Modbus protocol disconnected")
	return nil
}

// Send sends a message via Modbus
func (m *ModbusProtocol) Send(ctx context.Context, message *Message) error {
	if !m.connected {
		return fmt.Errorf("Modbus protocol is not connected")
	}

	// Parse Modbus command from message payload
	command, err := m.parseCommand(message.Payload)
	if err != nil {
		return fmt.Errorf("failed to parse Modbus command: %w", err)
	}

	// Execute Modbus command
	var result []byte
	switch command.Function {
	case "read_holding_registers":
		result, err = m.client.ReadHoldingRegisters(command.SlaveID, command.Address, command.Quantity)
	case "write_holding_register":
		err = m.client.WriteHoldingRegister(command.SlaveID, command.Address, command.Value)
	case "read_input_registers":
		result, err = m.client.ReadInputRegisters(command.SlaveID, command.Address, command.Quantity)
	case "read_coils":
		result, err = m.client.ReadCoils(command.SlaveID, command.Address, command.Quantity)
	case "write_coil":
		err = m.client.WriteCoil(command.SlaveID, command.Address, command.BoolValue)
	default:
		return fmt.Errorf("unsupported Modbus function: %s", command.Function)
	}

	if err != nil {
		return fmt.Errorf("Modbus command failed: %w", err)
	}

	// Store result in message metadata
	if result != nil {
		message.Metadata["result"] = result
	}

	logger.Debug("Modbus command executed: %s", command.Function)
	return nil
}

// Receive receives a message via Modbus
func (m *ModbusProtocol) Receive(ctx context.Context) (*Message, error) {
	// Modbus is typically a request-response protocol
	// This would be implemented based on specific use case
	return nil, fmt.Errorf("receive not implemented for Modbus")
}

// IsConnected returns connection status
func (m *ModbusProtocol) IsConnected() bool {
	return m.connected && m.client != nil && m.client.IsConnected()
}

// GetCapabilities returns Modbus capabilities
func (m *ModbusProtocol) GetCapabilities() []string {
	return m.capabilities
}

// ModbusCommand represents a Modbus command
type ModbusCommand struct {
	Function  string `json:"function"`
	SlaveID   byte   `json:"slave_id"`
	Address   uint16 `json:"address"`
	Quantity  uint16 `json:"quantity"`
	Value     uint16 `json:"value"`
	BoolValue bool   `json:"bool_value"`
}

// parseConfig parses Modbus configuration
func (m *ModbusProtocol) parseConfig(config map[string]interface{}) (*ModbusConfig, error) {
	modbusConfig := &ModbusConfig{
		Type:     "tcp",
		Address:  "localhost",
		BaudRate: 9600,
		DataBits: 8,
		StopBits: 1,
		Parity:   "none",
		Port:     502,
		Timeout:  5,
	}

	if t, ok := config["type"].(string); ok {
		modbusConfig.Type = t
	}

	if addr, ok := config["address"].(string); ok {
		modbusConfig.Address = addr
	}

	if baudRate, ok := config["baud_rate"].(float64); ok {
		modbusConfig.BaudRate = int(baudRate)
	}

	if dataBits, ok := config["data_bits"].(float64); ok {
		modbusConfig.DataBits = int(dataBits)
	}

	if stopBits, ok := config["stop_bits"].(float64); ok {
		modbusConfig.StopBits = int(stopBits)
	}

	if parity, ok := config["parity"].(string); ok {
		modbusConfig.Parity = parity
	}

	if port, ok := config["port"].(float64); ok {
		modbusConfig.Port = int(port)
	}

	if timeout, ok := config["timeout"].(float64); ok {
		modbusConfig.Timeout = int(timeout)
	}

	return modbusConfig, nil
}

// parseCommand parses a Modbus command from message payload
func (m *ModbusProtocol) parseCommand(payload map[string]interface{}) (*ModbusCommand, error) {
	command := &ModbusCommand{}

	if function, ok := payload["function"].(string); ok {
		command.Function = function
	} else {
		return nil, fmt.Errorf("function is required")
	}

	if slaveID, ok := payload["slave_id"].(float64); ok {
		command.SlaveID = byte(slaveID)
	} else {
		return nil, fmt.Errorf("slave_id is required")
	}

	if address, ok := payload["address"].(float64); ok {
		command.Address = uint16(address)
	} else {
		return nil, fmt.Errorf("address is required")
	}

	if quantity, ok := payload["quantity"].(float64); ok {
		command.Quantity = uint16(quantity)
	}

	if value, ok := payload["value"].(float64); ok {
		command.Value = uint16(value)
	}

	if boolValue, ok := payload["bool_value"].(bool); ok {
		command.BoolValue = boolValue
	}

	return command, nil
}

// MockModbusClient is a mock Modbus client for testing
type MockModbusClient struct {
	config    *ModbusConfig
	connected bool
}

// NewMockModbusTCPClient creates a new mock Modbus TCP client
func NewMockModbusTCPClient(config *ModbusConfig) ModbusClient {
	return &MockModbusClient{
		config:    config,
		connected: false,
	}
}

// NewMockModbusRTUClient creates a new mock Modbus RTU client
func NewMockModbusRTUClient(config *ModbusConfig) ModbusClient {
	return &MockModbusClient{
		config:    config,
		connected: false,
	}
}

// Connect simulates Modbus connection
func (m *MockModbusClient) Connect() error {
	time.Sleep(50 * time.Millisecond)
	m.connected = true
	logger.Debug("Mock Modbus client connected to %s", m.config.Address)
	return nil
}

// Disconnect simulates Modbus disconnection
func (m *MockModbusClient) Disconnect() error {
	m.connected = false
	logger.Debug("Mock Modbus client disconnected")
	return nil
}

// ReadHoldingRegisters simulates reading holding registers
func (m *MockModbusClient) ReadHoldingRegisters(slaveID byte, address uint16, quantity uint16) ([]byte, error) {
	if !m.connected {
		return nil, fmt.Errorf("Modbus client is not connected")
	}

	// Return mock data
	result := make([]byte, quantity*2)
	for i := uint16(0); i < quantity; i++ {
		result[i*2] = byte((address + i) >> 8)
		result[i*2+1] = byte((address + i) & 0xFF)
	}

	logger.Debug("Mock Modbus read holding registers: slave=%d, addr=%d, qty=%d", slaveID, address, quantity)
	return result, nil
}

// WriteHoldingRegister simulates writing a holding register
func (m *MockModbusClient) WriteHoldingRegister(slaveID byte, address uint16, value uint16) error {
	if !m.connected {
		return fmt.Errorf("Modbus client is not connected")
	}

	logger.Debug("Mock Modbus write holding register: slave=%d, addr=%d, value=%d", slaveID, address, value)
	return nil
}

// ReadInputRegisters simulates reading input registers
func (m *MockModbusClient) ReadInputRegisters(slaveID byte, address uint16, quantity uint16) ([]byte, error) {
	if !m.connected {
		return nil, fmt.Errorf("Modbus client is not connected")
	}

	// Return mock data
	result := make([]byte, quantity*2)
	for i := uint16(0); i < quantity; i++ {
		result[i*2] = byte((address + i) >> 8)
		result[i*2+1] = byte((address + i) & 0xFF)
	}

	logger.Debug("Mock Modbus read input registers: slave=%d, addr=%d, qty=%d", slaveID, address, quantity)
	return result, nil
}

// ReadCoils simulates reading coils
func (m *MockModbusClient) ReadCoils(slaveID byte, address uint16, quantity uint16) ([]byte, error) {
	if !m.connected {
		return nil, fmt.Errorf("Modbus client is not connected")
	}

	// Return mock data
	bytes := (quantity + 7) / 8
	result := make([]byte, bytes)
	for i := uint16(0); i < quantity; i++ {
		if (address+i)%2 == 0 {
			result[i/8] |= 1 << (i % 8)
		}
	}

	logger.Debug("Mock Modbus read coils: slave=%d, addr=%d, qty=%d", slaveID, address, quantity)
	return result, nil
}

// WriteCoil simulates writing a coil
func (m *MockModbusClient) WriteCoil(slaveID byte, address uint16, value bool) error {
	if !m.connected {
		return fmt.Errorf("Modbus client is not connected")
	}

	logger.Debug("Mock Modbus write coil: slave=%d, addr=%d, value=%t", slaveID, address, value)
	return nil
}

// IsConnected returns connection status
func (m *MockModbusClient) IsConnected() bool {
	return m.connected
}
