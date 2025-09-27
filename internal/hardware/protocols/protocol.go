package protocols

import (
	"context"
	"fmt"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Protocol represents a communication protocol interface
type Protocol interface {
	// Name returns the protocol name
	Name() string

	// Version returns the protocol version
	Version() string

	// Connect establishes a connection
	Connect(ctx context.Context, config map[string]interface{}) error

	// Disconnect closes the connection
	Disconnect(ctx context.Context) error

	// Send sends a message
	Send(ctx context.Context, message *Message) error

	// Receive receives a message
	Receive(ctx context.Context) (*Message, error)

	// IsConnected returns connection status
	IsConnected() bool

	// GetCapabilities returns protocol capabilities
	GetCapabilities() []string
}

// Message represents a protocol message
type Message struct {
	ID        string                 `json:"id"`
	Type      MessageType            `json:"type"`
	Source    string                 `json:"source"`
	Target    string                 `json:"target"`
	Payload   map[string]interface{} `json:"payload"`
	Timestamp time.Time              `json:"timestamp"`
	Priority  MessagePriority        `json:"priority"`
	Metadata  map[string]interface{} `json:"metadata"`
}

// MessageType represents the type of protocol message
type MessageType string

const (
	MessageTypeRead    MessageType = "read"
	MessageTypeWrite   MessageType = "write"
	MessageTypeCommand MessageType = "command"
	MessageTypeData    MessageType = "data"
	MessageTypeStatus  MessageType = "status"
	MessageTypeError   MessageType = "error"
)

// MessagePriority represents message priority
type MessagePriority string

const (
	MessagePriorityLow      MessagePriority = "low"
	MessagePriorityNormal   MessagePriority = "normal"
	MessagePriorityHigh     MessagePriority = "high"
	MessagePriorityCritical MessagePriority = "critical"
)

// ProtocolManager manages communication protocols
type ProtocolManager struct {
	protocols map[string]Protocol
	metrics   *ProtocolMetrics
}

// ProtocolMetrics tracks protocol performance metrics
type ProtocolMetrics struct {
	MessagesSent     int64 `json:"messages_sent"`
	MessagesReceived int64 `json:"messages_received"`
	Errors           int64 `json:"errors"`
	Connections      int64 `json:"connections"`
	Disconnections   int64 `json:"disconnections"`
}

// NewProtocolManager creates a new protocol manager
func NewProtocolManager() *ProtocolManager {
	return &ProtocolManager{
		protocols: make(map[string]Protocol),
		metrics:   &ProtocolMetrics{},
	}
}

// RegisterProtocol registers a new protocol
func (pm *ProtocolManager) RegisterProtocol(protocol Protocol) error {
	if protocol == nil {
		return fmt.Errorf("protocol cannot be nil")
	}

	name := protocol.Name()
	if name == "" {
		return fmt.Errorf("protocol name cannot be empty")
	}

	pm.protocols[name] = protocol
	logger.Info("Protocol registered: %s v%s", name, protocol.Version())
	return nil
}

// GetProtocol retrieves a protocol by name
func (pm *ProtocolManager) GetProtocol(name string) (Protocol, error) {
	protocol, exists := pm.protocols[name]
	if !exists {
		return nil, fmt.Errorf("protocol %s not found", name)
	}
	return protocol, nil
}

// ListProtocols returns all registered protocols
func (pm *ProtocolManager) ListProtocols() []string {
	var names []string
	for name := range pm.protocols {
		names = append(names, name)
	}
	return names
}

// SendMessage sends a message using the specified protocol
func (pm *ProtocolManager) SendMessage(ctx context.Context, protocolName string, message *Message) error {
	protocol, err := pm.GetProtocol(protocolName)
	if err != nil {
		return err
	}

	if !protocol.IsConnected() {
		return fmt.Errorf("protocol %s is not connected", protocolName)
	}

	if err := protocol.Send(ctx, message); err != nil {
		pm.metrics.Errors++
		return fmt.Errorf("failed to send message: %w", err)
	}

	pm.metrics.MessagesSent++
	logger.Debug("Message sent via %s: %s", protocolName, message.ID)
	return nil
}

// ReceiveMessage receives a message using the specified protocol
func (pm *ProtocolManager) ReceiveMessage(ctx context.Context, protocolName string) (*Message, error) {
	protocol, err := pm.GetProtocol(protocolName)
	if err != nil {
		return nil, err
	}

	if !protocol.IsConnected() {
		return nil, fmt.Errorf("protocol %s is not connected", protocolName)
	}

	message, err := protocol.Receive(ctx)
	if err != nil {
		pm.metrics.Errors++
		return nil, fmt.Errorf("failed to receive message: %w", err)
	}

	pm.metrics.MessagesReceived++
	logger.Debug("Message received via %s: %s", protocolName, message.ID)
	return message, nil
}

// ConnectProtocol connects a protocol
func (pm *ProtocolManager) ConnectProtocol(ctx context.Context, protocolName string, config map[string]interface{}) error {
	protocol, err := pm.GetProtocol(protocolName)
	if err != nil {
		return err
	}

	if err := protocol.Connect(ctx, config); err != nil {
		pm.metrics.Errors++
		return fmt.Errorf("failed to connect protocol %s: %w", protocolName, err)
	}

	pm.metrics.Connections++
	logger.Info("Protocol connected: %s", protocolName)
	return nil
}

// DisconnectProtocol disconnects a protocol
func (pm *ProtocolManager) DisconnectProtocol(ctx context.Context, protocolName string) error {
	protocol, err := pm.GetProtocol(protocolName)
	if err != nil {
		return err
	}

	if err := protocol.Disconnect(ctx); err != nil {
		pm.metrics.Errors++
		return fmt.Errorf("failed to disconnect protocol %s: %w", protocolName, err)
	}

	pm.metrics.Disconnections++
	logger.Info("Protocol disconnected: %s", protocolName)
	return nil
}

// GetMetrics returns protocol metrics
func (pm *ProtocolManager) GetMetrics() *ProtocolMetrics {
	return pm.metrics
}

// CreateMessage creates a new protocol message
func CreateMessage(messageType MessageType, source, target string, payload map[string]interface{}) *Message {
	return &Message{
		ID:        fmt.Sprintf("msg_%d", time.Now().UnixNano()),
		Type:      messageType,
		Source:    source,
		Target:    target,
		Payload:   payload,
		Timestamp: time.Now(),
		Priority:  MessagePriorityNormal,
		Metadata:  make(map[string]interface{}),
	}
}

// CreateCommandMessage creates a command message
func CreateCommandMessage(source, target string, command map[string]interface{}) *Message {
	message := CreateMessage(MessageTypeCommand, source, target, command)
	message.Priority = MessagePriorityHigh
	return message
}

// CreateDataMessage creates a data message
func CreateDataMessage(source, target string, data map[string]interface{}) *Message {
	return CreateMessage(MessageTypeData, source, target, data)
}

// CreateStatusMessage creates a status message
func CreateStatusMessage(source, target string, status map[string]interface{}) *Message {
	return CreateMessage(MessageTypeStatus, source, target, status)
}

// CreateErrorMessage creates an error message
func CreateErrorMessage(source, target string, error map[string]interface{}) *Message {
	message := CreateMessage(MessageTypeError, source, target, error)
	message.Priority = MessagePriorityCritical
	return message
}
