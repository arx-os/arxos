package radio

import (
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"strings"
	"time"

	"github.com/arx-os/arxos/internal/common/logger"
)

// LoRaWANInterface implements RadioInterface for LoRaWAN devices
type LoRaWANInterface struct {
	port       io.ReadWriteCloser
	buffer     []byte
	timeout    time.Duration
	deviceEUI  string
	appEUI     string
	appKey     string
	joinStatus bool
}

// NewLoRaWANInterface creates a new LoRaWAN interface
func NewLoRaWANInterface() *LoRaWANInterface {
	return &LoRaWANInterface{
		buffer:  make([]byte, 1024),
		timeout: 30 * time.Second,
	}
}

// Open initializes the LoRaWAN device
func (l *LoRaWANInterface) Open(device string, baudRate int) error {
	logger.Info("Opening LoRaWAN device: %s at %d baud", device, baudRate)

	// In production, this would open a serial port
	// For now, we'll simulate the connection
	// port, err := serial.OpenPort(&serial.Config{
	//     Name: device,
	//     Baud: baudRate,
	// })
	// if err != nil {
	//     return fmt.Errorf("failed to open port: %w", err)
	// }
	// l.port = port

	// Initialize LoRaWAN module
	if err := l.initialize(); err != nil {
		return fmt.Errorf("failed to initialize LoRaWAN: %w", err)
	}

	// Join network
	if err := l.joinNetwork(); err != nil {
		return fmt.Errorf("failed to join LoRaWAN network: %w", err)
	}

	return nil
}

// initialize sends initialization AT commands to the LoRaWAN module
func (l *LoRaWANInterface) initialize() error {
	commands := []string{
		"AT",              // Test command
		"AT+RESET",        // Reset module
		"AT+MODE=1",       // Set to LoRaWAN mode
		"AT+CLASS=A",      // Set device class
		"AT+REGION=US915", // Set region
	}

	for _, cmd := range commands {
		if err := l.sendATCommand(cmd); err != nil {
			return fmt.Errorf("command %s failed: %w", cmd, err)
		}
		time.Sleep(100 * time.Millisecond)
	}

	return nil
}

// joinNetwork performs OTAA join procedure
func (l *LoRaWANInterface) joinNetwork() error {
	logger.Info("Joining LoRaWAN network via OTAA")

	// Set device credentials
	if l.deviceEUI != "" {
		if err := l.sendATCommand(fmt.Sprintf("AT+DEVEUI=%s", l.deviceEUI)); err != nil {
			return err
		}
	}

	if l.appEUI != "" {
		if err := l.sendATCommand(fmt.Sprintf("AT+APPEUI=%s", l.appEUI)); err != nil {
			return err
		}
	}

	if l.appKey != "" {
		if err := l.sendATCommand(fmt.Sprintf("AT+APPKEY=%s", l.appKey)); err != nil {
			return err
		}
	}

	// Initiate join
	if err := l.sendATCommand("AT+JOIN"); err != nil {
		return err
	}

	// Wait for join confirmation (with timeout)
	joinTimeout := time.After(60 * time.Second)
	ticker := time.NewTicker(2 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-joinTimeout:
			return errors.New("LoRaWAN join timeout")
		case <-ticker.C:
			response, err := l.readResponse()
			if err == nil && strings.Contains(response, "JOINED") {
				l.joinStatus = true
				logger.Info("Successfully joined LoRaWAN network")
				return nil
			}
		}
	}
}

// Send transmits data over LoRaWAN
func (l *LoRaWANInterface) Send(data []byte) error {
	if !l.joinStatus {
		return errors.New("not joined to LoRaWAN network")
	}

	// Convert data to hex for AT command
	hexData := hex.EncodeToString(data)

	// Send data (port 1, confirmed message)
	cmd := fmt.Sprintf("AT+SEND=1,1,%s", hexData)
	if err := l.sendATCommand(cmd); err != nil {
		return fmt.Errorf("send failed: %w", err)
	}

	// Wait for send confirmation
	response, err := l.readResponse()
	if err != nil {
		return err
	}

	if !strings.Contains(response, "SENT") {
		return fmt.Errorf("send not confirmed: %s", response)
	}

	logger.Debug("LoRaWAN sent %d bytes", len(data))
	return nil
}

// Receive reads data from LoRaWAN
func (l *LoRaWANInterface) Receive() ([]byte, error) {
	// In LoRaWAN Class A, we can only receive after sending
	// This checks for any downlink data

	response, err := l.readResponseWithTimeout(l.timeout)
	if err != nil {
		return nil, err
	}

	// Parse received data
	// Format: +RECV=<port>,<len>,<data>
	if strings.HasPrefix(response, "+RECV=") {
		parts := strings.Split(response[6:], ",")
		if len(parts) >= 3 {
			hexData := parts[2]
			data, err := hex.DecodeString(hexData)
			if err != nil {
				return nil, fmt.Errorf("failed to decode received data: %w", err)
			}
			logger.Debug("LoRaWAN received %d bytes", len(data))
			return data, nil
		}
	}

	return nil, errors.New("no data received")
}

// SetTimeout sets the receive timeout
func (l *LoRaWANInterface) SetTimeout(timeout time.Duration) {
	l.timeout = timeout
}

// Close closes the LoRaWAN interface
func (l *LoRaWANInterface) Close() error {
	// Leave network
	l.sendATCommand("AT+LEAVE")

	if l.port != nil {
		return l.port.Close()
	}
	return nil
}

// sendATCommand sends an AT command to the module
func (l *LoRaWANInterface) sendATCommand(cmd string) error {
	logger.Debug("LoRaWAN AT: %s", cmd)

	if l.port != nil {
		// Send command with CR+LF
		_, err := l.port.Write([]byte(cmd + "\r\n"))
		return err
	}

	// Simulation mode
	return nil
}

// readResponse reads a response from the module
func (l *LoRaWANInterface) readResponse() (string, error) {
	return l.readResponseWithTimeout(5 * time.Second)
}

// readResponseWithTimeout reads a response with timeout
func (l *LoRaWANInterface) readResponseWithTimeout(timeout time.Duration) (string, error) {
	if l.port == nil {
		// Simulation mode
		return "OK", nil
	}

	// Set read deadline
	// if deadliner, ok := l.port.(interface{ SetReadDeadline(time.Time) error }); ok {
	//     deadliner.SetReadDeadline(time.Now().Add(timeout))
	// }

	// Read response
	n, err := l.port.Read(l.buffer)
	if err != nil {
		return "", err
	}

	response := string(l.buffer[:n])
	logger.Debug("LoRaWAN response: %s", strings.TrimSpace(response))
	return response, nil
}

// SetCredentials sets LoRaWAN credentials
func (l *LoRaWANInterface) SetCredentials(deviceEUI, appEUI, appKey string) {
	l.deviceEUI = deviceEUI
	l.appEUI = appEUI
	l.appKey = appKey
}

// GetStatus returns current LoRaWAN status
func (l *LoRaWANInterface) GetStatus() (map[string]interface{}, error) {
	status := map[string]interface{}{
		"joined":     l.joinStatus,
		"device_eui": l.deviceEUI,
		"app_eui":    l.appEUI,
	}

	// Get additional status from module
	if l.port != nil {
		// Get RSSI
		if err := l.sendATCommand("AT+RSSI?"); err == nil {
			if response, err := l.readResponse(); err == nil {
				status["rssi"] = response
			}
		}

		// Get SNR
		if err := l.sendATCommand("AT+SNR?"); err == nil {
			if response, err := l.readResponse(); err == nil {
				status["snr"] = response
			}
		}
	}

	return status, nil
}
