//go:build tinygo
// +build tinygo

package main

import (
	"encoding/json"
	"machine"
	"time"
)

// SensorTemplate represents a basic sensor device template for ESP32
// This template can be compiled with TinyGo for ESP32 microcontrollers

// Device configuration
const (
	DeviceID   = "ESP32_SENSOR_001"
	DeviceType = "sensor"
	Version    = "1.0.0"

	// Pin definitions
	LED_PIN    = machine.GPIO2
	SENSOR_PIN = machine.GPIO34 // ADC pin for sensor reading

	// Network configuration
	WIFI_SSID     = "ArxOS_Network"
	WIFI_PASSWORD = "ArxOS_Password"
	MQTT_BROKER   = "192.168.1.100"
	MQTT_PORT     = 1883

	// Sensor configuration
	READ_INTERVAL      = 30 * time.Second
	HEARTBEAT_INTERVAL = 5 * time.Minute
)

// SensorData represents sensor reading data
type SensorData struct {
	DeviceID    string  `json:"device_id"`
	Timestamp   int64   `json:"timestamp"`
	Temperature float64 `json:"temperature"`
	Humidity    float64 `json:"humidity"`
	Pressure    float64 `json:"pressure"`
	Light       float64 `json:"light"`
	Battery     float64 `json:"battery"`
	Signal      int     `json:"signal"`
}

// DeviceStatus represents device status
type DeviceStatus struct {
	DeviceID string `json:"device_id"`
	Status   string `json:"status"`
	Uptime   int64  `json:"uptime"`
	FreeMem  uint32 `json:"free_memory"`
	LastSeen int64  `json:"last_seen"`
}

// MQTTMessage represents an MQTT message
type MQTTMessage struct {
	Type      string      `json:"type"`
	DeviceID  string      `json:"device_id"`
	Payload   interface{} `json:"payload"`
	Timestamp int64       `json:"timestamp"`
}

// Global variables
var (
	led           machine.Pin
	sensorPin     machine.Pin
	startTime     time.Time
	lastRead      time.Time
	lastHeartbeat time.Time
)

func main() {
	// Initialize device
	initDevice()

	// Main loop
	for {
		// Read sensor data
		if time.Since(lastRead) >= READ_INTERVAL {
			readSensors()
			lastRead = time.Now()
		}

		// Send heartbeat
		if time.Since(lastHeartbeat) >= HEARTBEAT_INTERVAL {
			sendHeartbeat()
			lastHeartbeat = time.Now()
		}

		// Blink LED to indicate activity
		blinkLED()

		// Small delay
		time.Sleep(100 * time.Millisecond)
	}
}

// initDevice initializes the device hardware
func initDevice() {
	// Initialize pins
	led = LED_PIN
	led.Configure(machine.PinConfig{Mode: machine.PinOutput})

	sensorPin = SENSOR_PIN
	sensorPin.Configure(machine.PinConfig{Mode: machine.PinInput})

	// Initialize ADC for sensor readings
	machine.InitADC()

	// Set start time
	startTime = time.Now()
	lastRead = startTime
	lastHeartbeat = startTime

	// Turn on LED to indicate initialization
	led.High()
	time.Sleep(1 * time.Second)
	led.Low()
}

// readSensors reads data from all connected sensors
func readSensors() {
	// Read temperature (simulated - would use actual sensor)
	temperature := readTemperature()

	// Read humidity (simulated - would use actual sensor)
	humidity := readHumidity()

	// Read pressure (simulated - would use actual sensor)
	pressure := readPressure()

	// Read light level (simulated - would use actual sensor)
	light := readLightLevel()

	// Read battery level
	battery := readBatteryLevel()

	// Read WiFi signal strength
	signal := readSignalStrength()

	// Create sensor data
	data := SensorData{
		DeviceID:    DeviceID,
		Timestamp:   time.Now().Unix(),
		Temperature: temperature,
		Humidity:    humidity,
		Pressure:    pressure,
		Light:       light,
		Battery:     battery,
		Signal:      signal,
	}

	// Send sensor data via MQTT
	sendSensorData(data)
}

// readTemperature reads temperature from sensor
func readTemperature() float64 {
	// Simulate temperature reading (20-30°C range)
	// In real implementation, would read from actual temperature sensor
	return 22.5 + float64(time.Now().Unix()%100)/10.0
}

// readHumidity reads humidity from sensor
func readHumidity() float64 {
	// Simulate humidity reading (30-70% range)
	// In real implementation, would read from actual humidity sensor
	return 45.0 + float64(time.Now().Unix()%200)/10.0
}

// readPressure reads atmospheric pressure from sensor
func readPressure() float64 {
	// Simulate pressure reading (950-1050 hPa range)
	// In real implementation, would read from actual pressure sensor
	return 1013.25 + float64(time.Now().Unix()%100)/10.0
}

// readLightLevel reads light level from sensor
func readLightLevel() float64 {
	// Read from ADC pin (0-4095 range for ESP32)
	// Convert to percentage
	adcValue := sensorPin.Get()
	return float64(adcValue) / 40.95 // Convert to percentage
}

// readBatteryLevel reads battery level
func readBatteryLevel() float64 {
	// Simulate battery level (0-100% range)
	// In real implementation, would read from battery monitoring circuit
	return 85.0 + float64(time.Now().Unix()%150)/10.0
}

// readSignalStrength reads WiFi signal strength
func readSignalStrength() int {
	// Simulate signal strength (-100 to 0 dBm range)
	// In real implementation, would read from WiFi module
	return -50 + int(time.Now().Unix()%50)
}

// sendSensorData sends sensor data via MQTT
func sendSensorData(data SensorData) {
	message := MQTTMessage{
		Type:      "sensor_data",
		DeviceID:  DeviceID,
		Payload:   data,
		Timestamp: time.Now().Unix(),
	}

	// Convert to JSON
	jsonData, err := json.Marshal(message)
	if err != nil {
		// Handle error (in real implementation)
		return
	}

	// Send via MQTT (simulated - would use actual MQTT client)
	sendMQTTMessage("arxos/sensors/data", jsonData)
}

// sendHeartbeat sends device heartbeat
func sendHeartbeat() {
	status := DeviceStatus{
		DeviceID: DeviceID,
		Status:   "online",
		Uptime:   int64(time.Since(startTime).Seconds()),
		FreeMem:  getFreeMemory(),
		LastSeen: time.Now().Unix(),
	}

	message := MQTTMessage{
		Type:      "heartbeat",
		DeviceID:  DeviceID,
		Payload:   status,
		Timestamp: time.Now().Unix(),
	}

	// Convert to JSON
	jsonData, err := json.Marshal(message)
	if err != nil {
		return
	}

	// Send via MQTT
	sendMQTTMessage("arxos/devices/heartbeat", jsonData)
}

// sendMQTTMessage sends a message via MQTT
func sendMQTTMessage(topic string, payload []byte) {
	// Simulate MQTT message sending
	// In real implementation, would use MQTT client library
	// For now, just blink LED to indicate message sent
	led.High()
	time.Sleep(50 * time.Millisecond)
	led.Low()
}

// blinkLED blinks the LED to indicate activity
func blinkLED() {
	led.High()
	time.Sleep(10 * time.Millisecond)
	led.Low()
}

// getFreeMemory returns available free memory
func getFreeMemory() uint32 {
	// In real implementation, would use actual memory monitoring
	// For now, return a simulated value
	return 50000 // 50KB free memory
}

// handleCommand handles incoming commands
func handleCommand(command map[string]interface{}) {
	// Parse command type
	cmdType, ok := command["type"].(string)
	if !ok {
		return
	}

	switch cmdType {
	case "led_on":
		led.High()
	case "led_off":
		led.Low()
	case "read_sensors":
		readSensors()
	case "restart":
		// Restart device (simulated)
		time.Sleep(1 * time.Second)
	case "config":
		// Update configuration
		updateConfig(command)
	}
}

// updateConfig updates device configuration
func updateConfig(config map[string]interface{}) {
	// Update configuration parameters
	// In real implementation, would store in EEPROM or flash
	if interval, ok := config["read_interval"].(float64); ok {
		// Update read interval
		_ = interval
	}
}

// initWiFi initializes WiFi connection
func initWiFi() {
	// Initialize WiFi module
	// In real implementation, would use WiFi library
}

// initMQTT initializes MQTT connection
func initMQTT() {
	// Initialize MQTT client
	// In real implementation, would use MQTT library
}
