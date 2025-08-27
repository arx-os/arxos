// Sensor Manager - Real-time sensor data collection and management for ArxOS building integration
package sensors

import (
	"context"
	"fmt"
	"log"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/arxos/arxos/cmd/building-integration/protocols"
)

// SensorType represents different types of building sensors
type SensorType string

const (
	SensorTypeTemperature SensorType = "temperature"
	SensorTypeHumidity    SensorType = "humidity"
	SensorTypeCO2         SensorType = "co2"
	SensorTypePressure    SensorType = "pressure"
	SensorTypeOccupancy   SensorType = "occupancy"
	SensorTypePower       SensorType = "power"
	SensorTypeVoltage     SensorType = "voltage"
	SensorTypeCurrent     SensorType = "current"
	SensorTypeFlow        SensorType = "flow"
	SensorTypeLight       SensorType = "light"
	SensorTypeMotion      SensorType = "motion"
	SensorTypeDoor        SensorType = "door"
	SensorTypeWindow      SensorType = "window"
)

// Protocol represents the communication protocol used by a sensor
type Protocol string

const (
	ProtocolBACnet Protocol = "bacnet"
	ProtocolModbus Protocol = "modbus"
	ProtocolHTTP   Protocol = "http"
	ProtocolMQTT   Protocol = "mqtt"
)

// SensorConfig holds configuration for a single sensor
type SensorConfig struct {
	ID          string    `json:"id"`           // Unique sensor identifier
	Name        string    `json:"name"`         // Human-readable name
	Type        SensorType `json:"type"`        // Sensor type (temperature, humidity, etc.)
	Protocol    Protocol  `json:"protocol"`     // Communication protocol
	Address     string    `json:"address"`      // Protocol-specific address
	Unit        string    `json:"unit"`         // Measurement unit
	Floor       int       `json:"floor"`        // Floor number
	Room        string    `json:"room"`         // Room identifier
	Position    Position  `json:"position"`     // 3D position
	Limits      Limits    `json:"limits"`       // Acceptable value limits
	ScanRate    time.Duration `json:"scan_rate"` // How often to read sensor
	DataType    string    `json:"data_type"`    // Data type for Modbus
	Enabled     bool      `json:"enabled"`      // Whether sensor is enabled
}

// Position represents 3D coordinates of a sensor
type Position struct {
	X float64 `json:"x"` // X coordinate (meters)
	Y float64 `json:"y"` // Y coordinate (meters) 
	Z float64 `json:"z"` // Z coordinate (meters)
}

// Limits defines acceptable sensor value ranges
type Limits struct {
	Min      float64 `json:"min"`      // Minimum acceptable value
	Max      float64 `json:"max"`      // Maximum acceptable value
	Critical bool    `json:"critical"` // Whether violations are critical alarms
}

// SensorReading represents a sensor measurement
type SensorReading struct {
	SensorID    string      `json:"sensor_id"`
	Name        string      `json:"name"`
	Type        SensorType  `json:"type"`
	Value       float64     `json:"value"`
	Unit        string      `json:"unit"`
	Quality     string      `json:"quality"`     // "good", "bad", "uncertain", "alarm"
	Confidence  float64     `json:"confidence"`  // 0.0 to 1.0
	Timestamp   time.Time   `json:"timestamp"`
	Position    Position    `json:"position"`
	Floor       int         `json:"floor"`
	Room        string      `json:"room"`
	RawValue    interface{} `json:"raw_value,omitempty"`
	Protocol    Protocol    `json:"protocol"`
	Address     string      `json:"address"`
	AlarmState  string      `json:"alarm_state"` // "normal", "warning", "critical"
}

// SensorStatus represents the operational status of a sensor
type SensorStatus struct {
	SensorID       string        `json:"sensor_id"`
	LastReading    time.Time     `json:"last_reading"`
	ReadingCount   uint64        `json:"reading_count"`
	ErrorCount     uint64        `json:"error_count"`
	LastError      string        `json:"last_error,omitempty"`
	CommQuality    float64       `json:"comm_quality"`    // 0.0 to 1.0
	IsOnline       bool          `json:"is_online"`
	ResponseTime   time.Duration `json:"response_time"`
	NextScan       time.Time     `json:"next_scan"`
}

// SystemStatus represents overall sensor system status
type SystemStatus struct {
	TotalSensors   int     `json:"total_sensors"`
	ActiveSensors  int     `json:"active_sensors"`
	ErrorSensors   int     `json:"error_sensors"`
	TotalReadings  uint64  `json:"total_readings"`
	Errors         uint64  `json:"errors"`
	AvgConfidence  float64 `json:"avg_confidence"`
	Alarms         int     `json:"alarms"`
	Uptime         time.Duration `json:"uptime"`
}

// SensorManager coordinates sensor data collection from multiple protocols
type SensorManager struct {
	sensors       map[string]*SensorConfig
	sensorStatus  map[string]*SensorStatus
	bacnetClient  *protocols.BACnetClient
	modbusClient  *protocols.ModbusClient
	dataStream    chan<- *SensorReading
	ctx           context.Context
	cancel        context.CancelFunc
	wg            sync.WaitGroup
	mutex         sync.RWMutex
	
	// Statistics
	startTime     time.Time
	totalReadings uint64
	totalErrors   uint64
}

// NewSensorManager creates a new sensor manager
func NewSensorManager(configs []SensorConfig, dataStream chan<- *SensorReading) *SensorManager {
	ctx, cancel := context.WithCancel(context.Background())
	
	sm := &SensorManager{
		sensors:      make(map[string]*SensorConfig),
		sensorStatus: make(map[string]*SensorStatus),
		dataStream:   dataStream,
		ctx:          ctx,
		cancel:       cancel,
		startTime:    time.Now(),
	}
	
	// Initialize sensor configurations
	for i, config := range configs {
		// Set default scan rate if not specified
		if config.ScanRate == 0 {
			config.ScanRate = 10 * time.Second
		}
		
		// Enable by default if not specified
		if !config.Enabled {
			config.Enabled = true
		}
		
		sm.sensors[config.ID] = &configs[i]
		sm.sensorStatus[config.ID] = &SensorStatus{
			SensorID:     config.ID,
			CommQuality:  1.0,
			IsOnline:     false,
		}
	}
	
	log.Printf("🔧 Sensor manager initialized with %d sensors", len(sm.sensors))
	return sm
}

// SetBACnetClient sets the BACnet client for BACnet sensors
func (sm *SensorManager) SetBACnetClient(client *protocols.BACnetClient) {
	sm.bacnetClient = client
	log.Println("📡 BACnet client attached to sensor manager")
}

// SetModbusClient sets the Modbus client for Modbus sensors  
func (sm *SensorManager) SetModbusClient(client *protocols.ModbusClient) {
	sm.modbusClient = client
	log.Println("📡 Modbus client attached to sensor manager")
}

// Start begins sensor data collection
func (sm *SensorManager) Start(ctx context.Context) error {
	log.Println("🚀 Starting sensor data collection...")
	
	// Start sensor polling goroutines
	for _, sensor := range sm.sensors {
		if !sensor.Enabled {
			continue
		}
		
		sm.wg.Add(1)
		go sm.pollSensor(sensor)
	}
	
	// Start status monitoring
	sm.wg.Add(1)
	go sm.monitorStatus()
	
	log.Printf("✅ Started polling %d sensors", len(sm.sensors))
	return nil
}

// Stop gracefully stops sensor data collection
func (sm *SensorManager) Stop() {
	log.Println("🛑 Stopping sensor data collection...")
	
	sm.cancel()
	
	// Wait for goroutines to finish
	done := make(chan struct{})
	go func() {
		sm.wg.Wait()
		close(done)
	}()
	
	select {
	case <-done:
		log.Println("All sensor goroutines stopped")
	case <-time.After(5 * time.Second):
		log.Println("Timeout waiting for sensor goroutines to stop")
	}
	
	log.Println("✅ Sensor manager stopped")
}

// pollSensor continuously polls a single sensor
func (sm *SensorManager) pollSensor(config *SensorConfig) {
	defer sm.wg.Done()
	
	log.Printf("📊 Starting polling for sensor: %s (%s)", config.Name, config.ID)
	
	ticker := time.NewTicker(config.ScanRate)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			sm.readSensor(config)
			
		case <-sm.ctx.Done():
			log.Printf("📊 Stopped polling sensor: %s", config.ID)
			return
		}
	}
}

// readSensor reads a value from a specific sensor
func (sm *SensorManager) readSensor(config *SensorConfig) {
	startTime := time.Now()
	
	reading, err := sm.performSensorRead(config)
	responseTime := time.Since(startTime)
	
	// Update sensor status
	sm.updateSensorStatus(config.ID, reading, err, responseTime)
	
	if err != nil {
		log.Printf("❌ Error reading sensor %s: %v", config.ID, err)
		sm.totalErrors++
		return
	}
	
	if reading == nil {
		log.Printf("⚠️  No reading from sensor %s", config.ID)
		return
	}
	
	// Validate reading against limits
	sm.validateReading(reading, config)
	
	// Send to data stream
	select {
	case sm.dataStream <- reading:
		sm.totalReadings++
	case <-sm.ctx.Done():
		return
	default:
		log.Printf("⚠️  Data stream buffer full, dropping reading from %s", config.ID)
	}
}

// performSensorRead executes the actual sensor read based on protocol
func (sm *SensorManager) performSensorRead(config *SensorConfig) (*SensorReading, error) {
	switch config.Protocol {
	case ProtocolBACnet:
		return sm.readBACnetSensor(config)
	case ProtocolModbus:
		return sm.readModbusSensor(config)
	default:
		return nil, fmt.Errorf("unsupported protocol: %s", config.Protocol)
	}
}

// readBACnetSensor reads a sensor via BACnet
func (sm *SensorManager) readBACnetSensor(config *SensorConfig) (*SensorReading, error) {
	if sm.bacnetClient == nil {
		return nil, fmt.Errorf("BACnet client not available")
	}
	
	value, err := sm.bacnetClient.ReadProperty(config.Address)
	if err != nil {
		return nil, fmt.Errorf("BACnet read failed: %w", err)
	}
	
	// Convert to float64
	floatValue, ok := sm.convertToFloat(value.Value)
	if !ok {
		return nil, fmt.Errorf("could not convert BACnet value to float: %v", value.Value)
	}
	
	reading := &SensorReading{
		SensorID:   config.ID,
		Name:       config.Name,
		Type:       config.Type,
		Value:      floatValue,
		Unit:       config.Unit,
		Quality:    value.Quality,
		Confidence: sm.calculateConfidence(value.Quality, value.Reliability),
		Timestamp:  value.Timestamp,
		Position:   config.Position,
		Floor:      config.Floor,
		Room:       config.Room,
		RawValue:   value.Value,
		Protocol:   ProtocolBACnet,
		Address:    config.Address,
		AlarmState: "normal",
	}
	
	return reading, nil
}

// readModbusSensor reads a sensor via Modbus
func (sm *SensorManager) readModbusSensor(config *SensorConfig) (*SensorReading, error) {
	if sm.modbusClient == nil {
		return nil, fmt.Errorf("Modbus client not available")
	}
	
	// Parse Modbus address
	address, function, err := sm.modbusClient.ParseAddress(config.Address)
	if err != nil {
		return nil, fmt.Errorf("invalid Modbus address: %w", err)
	}
	
	// Determine data type
	dataType := protocols.DataTypeUint16
	if config.DataType != "" {
		dataType = protocols.ModbusDataType(config.DataType)
	}
	
	var value *protocols.ModbusValue
	
	switch function {
	case protocols.ReadHoldingRegisters:
		value, err = sm.modbusClient.ReadHoldingRegister(address, dataType)
	case protocols.ReadInputRegisters:
		value, err = sm.modbusClient.ReadInputRegister(address, dataType)
	case protocols.ReadCoils:
		value, err = sm.modbusClient.ReadCoil(address)
	default:
		return nil, fmt.Errorf("unsupported Modbus function: %v", function)
	}
	
	if err != nil {
		return nil, fmt.Errorf("Modbus read failed: %w", err)
	}
	
	// Convert to float64
	floatValue, ok := sm.convertToFloat(value.Value)
	if !ok {
		return nil, fmt.Errorf("could not convert Modbus value to float: %v", value.Value)
	}
	
	reading := &SensorReading{
		SensorID:   config.ID,
		Name:       config.Name,
		Type:       config.Type,
		Value:      floatValue,
		Unit:       config.Unit,
		Quality:    value.Quality,
		Confidence: sm.calculateConfidence(value.Quality, ""),
		Timestamp:  value.Timestamp,
		Position:   config.Position,
		Floor:      config.Floor,
		Room:       config.Room,
		RawValue:   value.Value,
		Protocol:   ProtocolModbus,
		Address:    config.Address,
		AlarmState: "normal",
	}
	
	return reading, nil
}

// convertToFloat converts various numeric types to float64
func (sm *SensorManager) convertToFloat(value interface{}) (float64, bool) {
	switch v := value.(type) {
	case float64:
		return v, true
	case float32:
		return float64(v), true
	case int:
		return float64(v), true
	case int16:
		return float64(v), true
	case int32:
		return float64(v), true
	case int64:
		return float64(v), true
	case uint:
		return float64(v), true
	case uint16:
		return float64(v), true
	case uint32:
		return float64(v), true
	case uint64:
		return float64(v), true
	case bool:
		if v {
			return 1.0, true
		}
		return 0.0, true
	case string:
		if f, err := strconv.ParseFloat(v, 64); err == nil {
			return f, true
		}
		return 0, false
	default:
		return 0, false
	}
}

// calculateConfidence calculates reading confidence based on quality indicators
func (sm *SensorManager) calculateConfidence(quality, reliability string) float64 {
	confidence := 1.0
	
	// Adjust based on quality
	switch strings.ToLower(quality) {
	case "good":
		confidence = 1.0
	case "uncertain":
		confidence = 0.7
	case "bad", "error":
		confidence = 0.3
	case "communication-error":
		confidence = 0.1
	case "alarm":
		confidence = 0.5 // Data may still be valid but alarming
	default:
		confidence = 0.8 // Unknown quality
	}
	
	// Adjust based on reliability (BACnet specific)
	switch strings.ToLower(reliability) {
	case "no-fault-detected":
		// No change
	case "no-sensor", "over-range", "under-range":
		confidence *= 0.5
	case "open-loop", "shorted-loop":
		confidence *= 0.3
	case "unreliable-other":
		confidence *= 0.6
	case "process-error":
		confidence *= 0.4
	case "multi-state-fault":
		confidence *= 0.5
	case "configuration-error":
		confidence *= 0.2
	case "communication-failure":
		confidence *= 0.1
	}
	
	return confidence
}

// validateReading validates a sensor reading against configured limits
func (sm *SensorManager) validateReading(reading *SensorReading, config *SensorConfig) {
	// Check if value is within acceptable limits
	if reading.Value < config.Limits.Min || reading.Value > config.Limits.Max {
		if config.Limits.Critical {
			reading.AlarmState = "critical"
			reading.Quality = "alarm"
		} else {
			reading.AlarmState = "warning"
		}
		
		log.Printf("🚨 Sensor %s out of limits: %.2f %s (limits: %.2f - %.2f)", 
			config.ID, reading.Value, reading.Unit, config.Limits.Min, config.Limits.Max)
	}
	
	// Check for sensor-specific anomalies
	switch config.Type {
	case SensorTypeTemperature:
		// Extreme temperature readings
		if reading.Value < -10 || reading.Value > 50 {
			reading.AlarmState = "warning"
			log.Printf("⚠️  Extreme temperature reading: %s = %.2f°C", config.ID, reading.Value)
		}
		
	case SensorTypeCO2:
		// High CO2 levels
		if reading.Value > 1000 {
			reading.AlarmState = "warning"
			log.Printf("⚠️  High CO2 detected: %s = %.0f ppm", config.ID, reading.Value)
		}
		if reading.Value > 1500 {
			reading.AlarmState = "critical"
		}
		
	case SensorTypePower:
		// Power consumption spikes
		if reading.Value > config.Limits.Max * 0.9 {
			reading.AlarmState = "warning"
			log.Printf("⚠️  High power consumption: %s = %.2f kW", config.ID, reading.Value)
		}
	}
}

// updateSensorStatus updates the status tracking for a sensor
func (sm *SensorManager) updateSensorStatus(sensorID string, reading *SensorReading, err error, responseTime time.Duration) {
	sm.mutex.Lock()
	defer sm.mutex.Unlock()
	
	status, exists := sm.sensorStatus[sensorID]
	if !exists {
		return
	}
	
	status.ResponseTime = responseTime
	status.NextScan = time.Now().Add(sm.sensors[sensorID].ScanRate)
	
	if err != nil {
		status.ErrorCount++
		status.LastError = err.Error()
		status.IsOnline = false
		
		// Degrade communication quality
		status.CommQuality = status.CommQuality * 0.9
		if status.CommQuality < 0.1 {
			status.CommQuality = 0.1
		}
	} else {
		status.ReadingCount++
		status.LastReading = time.Now()
		status.IsOnline = true
		status.LastError = ""
		
		// Improve communication quality
		status.CommQuality = status.CommQuality*0.9 + 0.1
		if status.CommQuality > 1.0 {
			status.CommQuality = 1.0
		}
	}
}

// monitorStatus periodically logs system status
func (sm *SensorManager) monitorStatus() {
	defer sm.wg.Done()
	
	ticker := time.NewTicker(60 * time.Second)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			sm.logSystemStatus()
			
		case <-sm.ctx.Done():
			return
		}
	}
}

// logSystemStatus logs current system status
func (sm *SensorManager) logSystemStatus() {
	status := sm.GetStatus()
	
	log.Printf("📊 Sensor System: %d/%d sensors online, %d readings, %d errors (%.1f%% success)", 
		status.ActiveSensors, status.TotalSensors, status.TotalReadings, status.Errors,
		float64(status.TotalReadings-status.Errors)/float64(status.TotalReadings+1)*100)
		
	if status.Alarms > 0 {
		log.Printf("🚨 %d sensors in alarm state", status.Alarms)
	}
}

// GetStatus returns current system status
func (sm *SensorManager) GetStatus() SystemStatus {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	
	activeSensors := 0
	errorSensors := 0
	alarms := 0
	totalConfidence := 0.0
	
	for _, status := range sm.sensorStatus {
		if status.IsOnline {
			activeSensors++
		}
		if status.ErrorCount > 0 {
			errorSensors++
		}
		totalConfidence += status.CommQuality
	}
	
	avgConfidence := 0.0
	if len(sm.sensorStatus) > 0 {
		avgConfidence = totalConfidence / float64(len(sm.sensorStatus))
	}
	
	return SystemStatus{
		TotalSensors:  len(sm.sensors),
		ActiveSensors: activeSensors,
		ErrorSensors:  errorSensors,
		TotalReadings: sm.totalReadings,
		Errors:        sm.totalErrors,
		AvgConfidence: avgConfidence,
		Alarms:        alarms,
		Uptime:        time.Since(sm.startTime),
	}
}

// GetSensorStatus returns status for a specific sensor
func (sm *SensorManager) GetSensorStatus(sensorID string) (*SensorStatus, bool) {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	
	status, exists := sm.sensorStatus[sensorID]
	if !exists {
		return nil, false
	}
	
	// Return a copy
	statusCopy := *status
	return &statusCopy, true
}

// GetAllSensorStatus returns status for all sensors
func (sm *SensorManager) GetAllSensorStatus() map[string]*SensorStatus {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	
	result := make(map[string]*SensorStatus)
	for id, status := range sm.sensorStatus {
		statusCopy := *status
		result[id] = &statusCopy
	}
	
	return result
}

// GetSensorConfig returns configuration for a specific sensor
func (sm *SensorManager) GetSensorConfig(sensorID string) (*SensorConfig, bool) {
	sm.mutex.RLock()
	defer sm.mutex.RUnlock()
	
	config, exists := sm.sensors[sensorID]
	if !exists {
		return nil, false
	}
	
	// Return a copy
	configCopy := *config
	return &configCopy, true
}