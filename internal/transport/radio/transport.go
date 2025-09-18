// Package radio provides packet radio transport for ArxOS
package radio

import (
	"bytes"
	"encoding/binary"
	"errors"
	"fmt"
	"hash/crc32"
	"strings"
	"sync"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// Command types for radio protocol
const (
	CmdGet    byte = 0x01 // Get equipment/building data
	CmdSet    byte = 0x02 // Update equipment status
	CmdList   byte = 0x03 // List equipment in path
	CmdSearch byte = 0x04 // Search by criteria
	CmdDiff   byte = 0x05 // Get changes since timestamp
	CmdBatch  byte = 0x06 // Multiple operations
	CmdPing   byte = 0x07 // Connectivity test
	CmdAck    byte = 0x80 // Acknowledgment
	CmdError  byte = 0xFF // Error response
)

// Status codes for compression
var StatusCodes = map[string]byte{
	"OPERATIONAL": 'O',
	"DEGRADED":    'D',
	"FAILED":      'F',
	"MAINTENANCE": 'M',
	"OFFLINE":     'X',
	"UNKNOWN":     'U',
}

// Path abbreviations for compression
var PathAbbreviations = map[string]string{
	"/floor-":     "/",
	"/room-":      "/",
	"/zone-":      "/",
	"/electrical": "E",
	"/hvac":       "H",
	"/plumbing":   "P",
	"/network":    "N",
	"/security":   "S",
}

// RadioConfig holds configuration for radio transport
type RadioConfig struct {
	Device            string        `json:"device"`
	BaudRate          int           `json:"baud_rate"`
	MaxPayload        int           `json:"max_payload"`
	Compression       string        `json:"compression"`
	AckTimeout        time.Duration `json:"ack_timeout"`
	MaxRetries        int           `json:"max_retries"`
	KeepAliveInterval time.Duration `json:"keepalive_interval"`
}

// RadioTransport implements packet radio transport
type RadioTransport struct {
	config          RadioConfig
	buildingContext string
	sequenceNumber  byte
	pendingAcks     map[byte]time.Time
	mutex           sync.RWMutex
	radioInterface  RadioInterface
}

// RadioInterface defines the hardware interface
type RadioInterface interface {
	Open(device string, baudRate int) error
	Close() error
	Send(data []byte) error
	Receive() ([]byte, error)
	SetTimeout(timeout time.Duration)
}

// Command represents an ArxOS command
type Command struct {
	Method   string
	Path     string
	Building string
	Args     map[string]interface{}
}

// Response represents a command response
type Response struct {
	Status int
	Data   interface{}
	Error  string
}

// NewRadioTransport creates a new radio transport instance
func NewRadioTransport(config RadioConfig) *RadioTransport {
	return &RadioTransport{
		config:      config,
		pendingAcks: make(map[byte]time.Time),
	}
}

// Connect establishes connection to radio hardware
func (r *RadioTransport) Connect() error {
	// Initialize hardware interface based on config
	// This would be implemented based on specific hardware
	logger.Info("Connecting to radio device: %s", r.config.Device)

	// Placeholder for actual hardware initialization
	// r.radioInterface = NewLoRaWANInterface() or similar

	return nil
}

// Send transmits a command over radio
func (r *RadioTransport) Send(cmd Command) (Response, error) {
	// 1. Compress the command
	compressed, err := r.compress(cmd)
	if err != nil {
		return Response{}, fmt.Errorf("compression failed: %w", err)
	}

	// 2. Check payload size
	if len(compressed) > r.config.MaxPayload {
		return r.sendFragmented(compressed)
	}

	// 3. Transmit with retry logic
	response, err := r.transmitWithRetry(compressed)
	if err != nil {
		return Response{}, fmt.Errorf("transmission failed: %w", err)
	}

	// 4. Decompress response
	return r.decompress(response)
}

// compress encodes a command for radio transmission
func (r *RadioTransport) compress(cmd Command) ([]byte, error) {
	var buf bytes.Buffer

	// Write header
	header := byte(0x00) // Version 0
	if r.config.Compression == "high" {
		header |= 0x20 // Set compression bit
	}
	header |= 0x10 // Request acknowledgment
	buf.WriteByte(header)

	// Write command type
	cmdByte := r.commandToByte(cmd.Method)
	buf.WriteByte(cmdByte)

	// Write sequence number
	r.mutex.Lock()
	r.sequenceNumber++
	seq := r.sequenceNumber
	r.mutex.Unlock()
	buf.WriteByte(seq)

	// Compress and write path
	compressedPath := r.compressPath(cmd.Path)
	buf.WriteByte(byte(len(compressedPath)))
	buf.Write(compressedPath)

	// Compress and write arguments
	compressedArgs := r.compressArgs(cmd.Args)
	binary.Write(&buf, binary.BigEndian, uint16(len(compressedArgs)))
	buf.Write(compressedArgs)

	// Calculate and append CRC
	crc := crc32.ChecksumIEEE(buf.Bytes())
	binary.Write(&buf, binary.BigEndian, uint32(crc))

	return buf.Bytes(), nil
}

// compressPath applies path compression rules
func (r *RadioTransport) compressPath(path string) []byte {
	// Apply building context if set
	if r.buildingContext != "" {
		path = strings.TrimPrefix(path, "/building/")
		path = strings.TrimPrefix(path, r.buildingContext)
		path = "B1" + path // Use short building reference
	}

	// Apply abbreviations
	for long, short := range PathAbbreviations {
		path = strings.ReplaceAll(path, long, short)
	}

	return []byte(path)
}

// compressArgs compresses command arguments
func (r *RadioTransport) compressArgs(args map[string]interface{}) []byte {
	if len(args) == 0 {
		return []byte{}
	}

	var buf bytes.Buffer
	for key, value := range args {
		// Simple key-value encoding
		buf.WriteByte(byte(len(key)))
		buf.WriteString(key)

		// Encode value based on type
		switch v := value.(type) {
		case string:
			// Apply status compression if applicable
			if code, ok := StatusCodes[v]; ok {
				buf.WriteByte('S') // Status type
				buf.WriteByte(code)
			} else {
				buf.WriteByte('T') // Text type
				buf.WriteByte(byte(len(v)))
				buf.WriteString(v)
			}
		case int:
			buf.WriteByte('I') // Integer type
			binary.Write(&buf, binary.BigEndian, int32(v))
		default:
			// Skip unsupported types
			logger.Warn("Skipping unsupported argument type: %T", v)
		}
	}

	return buf.Bytes()
}

// decompress decodes a radio response
func (r *RadioTransport) decompress(data []byte) (Response, error) {
	if len(data) < 4 {
		return Response{}, errors.New("response too short")
	}

	// Parse header
	header := data[0]
	if header == CmdError {
		// Error response
		errorMsg := string(data[1:])
		return Response{
			Status: 500,
			Error:  errorMsg,
		}, nil
	}

	// Parse response based on command type
	// This would be expanded based on protocol specification
	return Response{
		Status: 200,
		Data:   string(data[1:]),
	}, nil
}

// transmitWithRetry sends data with retry logic
func (r *RadioTransport) transmitWithRetry(data []byte) ([]byte, error) {
	for attempt := 0; attempt < r.config.MaxRetries; attempt++ {
		if attempt > 0 {
			// Exponential backoff
			delay := time.Duration(1<<uint(attempt-1)) * time.Second
			time.Sleep(delay)
			logger.Debug("Retry attempt %d after %v delay", attempt, delay)
		}

		// Send data
		if r.radioInterface != nil {
			if err := r.radioInterface.Send(data); err != nil {
				logger.Warn("Send failed on attempt %d: %v", attempt, err)
				continue
			}

			// Wait for response
			r.radioInterface.SetTimeout(r.config.AckTimeout)
			response, err := r.radioInterface.Receive()
			if err == nil {
				return response, nil
			}
			logger.Warn("Receive failed on attempt %d: %v", attempt, err)
		} else {
			// Simulation mode
			logger.Debug("Radio simulation: would send %d bytes", len(data))
			return []byte("SIM:OK"), nil
		}
	}

	return nil, fmt.Errorf("max retries (%d) exceeded", r.config.MaxRetries)
}

// sendFragmented handles messages too large for single packet
func (r *RadioTransport) sendFragmented(data []byte) (Response, error) {
	// Calculate number of fragments
	fragmentSize := r.config.MaxPayload - 10 // Reserve space for fragment header
	numFragments := (len(data) + fragmentSize - 1) / fragmentSize

	logger.Info("Sending fragmented message: %d fragments of %d bytes", numFragments, fragmentSize)

	// Send each fragment
	for i := 0; i < numFragments; i++ {
		start := i * fragmentSize
		end := start + fragmentSize
		if end > len(data) {
			end = len(data)
		}

		// Create fragment packet
		fragment := r.createFragment(data[start:end], i, numFragments)

		// Send fragment
		if _, err := r.transmitWithRetry(fragment); err != nil {
			return Response{}, fmt.Errorf("fragment %d failed: %w", i, err)
		}
	}

	// Wait for complete response
	// This would be implemented based on protocol
	return Response{Status: 200}, nil
}

// createFragment creates a fragment packet
func (r *RadioTransport) createFragment(data []byte, index, total int) []byte {
	var buf bytes.Buffer

	// Fragment header
	buf.WriteByte(0x08) // Fragment flag
	buf.WriteByte(byte(index))
	buf.WriteByte(byte(total))

	// Fragment data
	buf.Write(data)

	// CRC for fragment
	crc := crc32.ChecksumIEEE(buf.Bytes())
	binary.Write(&buf, binary.BigEndian, uint32(crc))

	return buf.Bytes()
}

// commandToByte converts command method to protocol byte
func (r *RadioTransport) commandToByte(method string) byte {
	switch strings.ToUpper(method) {
	case "GET":
		return CmdGet
	case "SET", "PUT", "POST":
		return CmdSet
	case "LIST":
		return CmdList
	case "SEARCH":
		return CmdSearch
	case "DIFF":
		return CmdDiff
	case "PING":
		return CmdPing
	default:
		return CmdGet
	}
}

// EstablishContext sets up building context for compression
func (r *RadioTransport) EstablishContext(buildingID string) error {
	r.mutex.Lock()
	defer r.mutex.Unlock()

	r.buildingContext = buildingID
	logger.Info("Established building context: %s", buildingID)

	// Send context establishment message
	// This would be implemented based on protocol
	return nil
}

// Close closes the radio transport
func (r *RadioTransport) Close() error {
	if r.radioInterface != nil {
		return r.radioInterface.Close()
	}
	return nil
}

// Ping tests radio connectivity
func (r *RadioTransport) Ping() error {
	cmd := Command{
		Method: "PING",
		Path:   "/",
	}

	start := time.Now()
	response, err := r.Send(cmd)
	if err != nil {
		return err
	}

	elapsed := time.Since(start)
	logger.Info("Radio ping successful: %v (status: %d)", elapsed, response.Status)
	return nil
}
