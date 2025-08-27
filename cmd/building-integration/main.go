// ArxOS Real Building Integration
// Connects to actual building systems via BACnet/Modbus and feeds sensor data to ASCII interface
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"sync"
	"syscall"
	"time"

	"github.com/arxos/arxos/cmd/building-integration/protocols"
	"github.com/arxos/arxos/cmd/building-integration/sensors"
	"github.com/arxos/arxos/cmd/building-integration/visualization"
)

// BuildingConfig represents the configuration for building integration
type BuildingConfig struct {
	BuildingID   string                    `json:"building_id"`
	Name         string                    `json:"name"`
	Location     string                    `json:"location"`
	BACnetConfig *protocols.BACnetConfig   `json:"bacnet_config,omitempty"`
	ModbusConfig *protocols.ModbusConfig   `json:"modbus_config,omitempty"`
	Sensors      []sensors.SensorConfig    `json:"sensors"`
	ASCII        *visualization.ASCIIConfig `json:"ascii_config"`
}

// BuildingIntegrator manages real building system integration
type BuildingIntegrator struct {
	config     *BuildingConfig
	bacnet     *protocols.BACnetClient
	modbus     *protocols.ModbusClient
	sensorMgr  *sensors.SensorManager
	asciiView  *visualization.ASCIIVisualization
	dataStream chan *sensors.SensorReading
	ctx        context.Context
	cancel     context.CancelFunc
	wg         sync.WaitGroup
}

func main() {
	var (
		configFile = flag.String("config", "building-config.json", "Building configuration file")
		demoMode   = flag.Bool("demo", false, "Run in demo mode with simulated sensors")
		verbose    = flag.Bool("verbose", false, "Enable verbose logging")
	)
	flag.Parse()

	if *verbose {
		log.SetFlags(log.LstdFlags | log.Lshortfile)
	}

	fmt.Println("ArxOS Real Building Integration")
	fmt.Println("==============================")
	fmt.Println()

	// Load configuration
	config, err := loadConfig(*configFile, *demoMode)
	if err != nil {
		log.Fatalf("Failed to load configuration: %v", err)
	}

	fmt.Printf("Building: %s (%s)\n", config.Name, config.BuildingID)
	fmt.Printf("Location: %s\n", config.Location)
	fmt.Printf("Sensors: %d configured\n", len(config.Sensors))
	fmt.Println()

	// Create building integrator
	integrator, err := NewBuildingIntegrator(config)
	if err != nil {
		log.Fatalf("Failed to create building integrator: %v", err)
	}

	// Handle graceful shutdown
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	// Start the integrator
	if err := integrator.Start(); err != nil {
		log.Fatalf("Failed to start building integrator: %v", err)
	}

	fmt.Println("🏢 Building integration started successfully!")
	fmt.Println("📡 Real-time sensor data streaming to ASCII interface...")
	fmt.Println("Press Ctrl+C to stop")
	fmt.Println()

	// Wait for shutdown signal
	<-sigChan
	fmt.Println("\n🛑 Shutdown signal received, stopping building integration...")

	// Stop the integrator
	if err := integrator.Stop(); err != nil {
		log.Printf("Error during shutdown: %v", err)
	}

	fmt.Println("✅ Building integration stopped successfully")
}

// NewBuildingIntegrator creates a new building integrator
func NewBuildingIntegrator(config *BuildingConfig) (*BuildingIntegrator, error) {
	ctx, cancel := context.WithCancel(context.Background())

	integrator := &BuildingIntegrator{
		config:     config,
		dataStream: make(chan *sensors.SensorReading, 1000),
		ctx:        ctx,
		cancel:     cancel,
	}

	// Initialize BACnet client if configured
	if config.BACnetConfig != nil {
		bacnetClient, err := protocols.NewBACnetClient(config.BACnetConfig)
		if err != nil {
			cancel()
			return nil, fmt.Errorf("failed to create BACnet client: %w", err)
		}
		integrator.bacnet = bacnetClient
		log.Printf("✅ BACnet client initialized (Network: %d, Device: %d)", 
			config.BACnetConfig.NetworkNumber, config.BACnetConfig.DeviceID)
	}

	// Initialize Modbus client if configured
	if config.ModbusConfig != nil {
		modbusClient, err := protocols.NewModbusClient(config.ModbusConfig)
		if err != nil {
			cancel()
			return nil, fmt.Errorf("failed to create Modbus client: %w", err)
		}
		integrator.modbus = modbusClient
		log.Printf("✅ Modbus client initialized (%s at %s)", 
			config.ModbusConfig.Mode, config.ModbusConfig.Address)
	}

	// Initialize sensor manager
	sensorManager := sensors.NewSensorManager(config.Sensors, integrator.dataStream)
	if integrator.bacnet != nil {
		sensorManager.SetBACnetClient(integrator.bacnet)
	}
	if integrator.modbus != nil {
		sensorManager.SetModbusClient(integrator.modbus)
	}
	integrator.sensorMgr = sensorManager

	// Initialize ASCII visualization
	if config.ASCII != nil {
		asciiViz, err := visualization.NewASCIIVisualization(config.ASCII, config.BuildingID)
		if err != nil {
			cancel()
			return nil, fmt.Errorf("failed to create ASCII visualization: %w", err)
		}
		integrator.asciiView = asciiViz
		log.Printf("✅ ASCII visualization initialized (%dx%d)", 
			config.ASCII.Width, config.ASCII.Height)
	}

	return integrator, nil
}

// Start begins the building integration process
func (bi *BuildingIntegrator) Start() error {
	// Start sensor data collection
	if err := bi.sensorMgr.Start(bi.ctx); err != nil {
		return fmt.Errorf("failed to start sensor manager: %w", err)
	}

	// Start ASCII visualization if configured
	if bi.asciiView != nil {
		if err := bi.asciiView.Start(bi.ctx); err != nil {
			return fmt.Errorf("failed to start ASCII visualization: %w", err)
		}
	}

	// Start data processing goroutine
	bi.wg.Add(1)
	go bi.processSensorData()

	// Start status reporting
	bi.wg.Add(1)
	go bi.reportStatus()

	return nil
}

// Stop gracefully shuts down the building integration
func (bi *BuildingIntegrator) Stop() error {
	bi.cancel()

	// Wait for goroutines to finish
	done := make(chan struct{})
	go func() {
		bi.wg.Wait()
		close(done)
	}()

	// Wait with timeout
	select {
	case <-done:
		log.Println("All goroutines stopped")
	case <-time.After(10 * time.Second):
		log.Println("Timeout waiting for goroutines to stop")
	}

	// Close data stream
	close(bi.dataStream)

	// Stop sensor manager
	if bi.sensorMgr != nil {
		bi.sensorMgr.Stop()
	}

	// Stop ASCII visualization
	if bi.asciiView != nil {
		bi.asciiView.Stop()
	}

	// Close protocol clients
	if bi.bacnet != nil {
		bi.bacnet.Close()
	}
	if bi.modbus != nil {
		bi.modbus.Close()
	}

	return nil
}

// processSensorData processes incoming sensor data and updates visualizations
func (bi *BuildingIntegrator) processSensorData() {
	defer bi.wg.Done()

	for {
		select {
		case reading := <-bi.dataStream:
			if reading == nil {
				return
			}

			// Process the sensor reading
			if err := bi.handleSensorReading(reading); err != nil {
				log.Printf("Error handling sensor reading: %v", err)
			}

		case <-bi.ctx.Done():
			return
		}
	}
}

// handleSensorReading processes a single sensor reading
func (bi *BuildingIntegrator) handleSensorReading(reading *sensors.SensorReading) error {
	// Update ASCII visualization if available
	if bi.asciiView != nil {
		if err := bi.asciiView.UpdateSensor(reading); err != nil {
			return fmt.Errorf("failed to update ASCII visualization: %w", err)
		}
	}

	// Log interesting readings (temperature anomalies, alarms, etc.)
	if bi.shouldLogReading(reading) {
		log.Printf("📊 %s: %.2f %s (Confidence: %.1f%%, Quality: %s)", 
			reading.SensorID, reading.Value, reading.Unit, 
			reading.Confidence*100, reading.Quality)
	}

	return nil
}

// shouldLogReading determines if a sensor reading should be logged
func (bi *BuildingIntegrator) shouldLogReading(reading *sensors.SensorReading) bool {
	// Log alarms and errors
	if reading.Quality == "alarm" || reading.Quality == "error" {
		return true
	}

	// Log temperature readings outside normal range
	if reading.Type == "temperature" {
		if reading.Value < 15 || reading.Value > 30 { // °C
			return true
		}
	}

	// Log humidity readings outside normal range
	if reading.Type == "humidity" {
		if reading.Value < 30 || reading.Value > 70 { // %RH
			return true
		}
	}

	// Log CO2 readings above threshold
	if reading.Type == "co2" && reading.Value > 1000 { // ppm
		return true
	}

	// Log energy readings above threshold
	if reading.Type == "power" && reading.Value > 1000 { // kW
		return true
	}

	return false
}

// reportStatus periodically reports system status
func (bi *BuildingIntegrator) reportStatus() {
	defer bi.wg.Done()
	
	ticker := time.NewTicker(30 * time.Second)
	defer ticker.Stop()

	for {
		select {
		case <-ticker.C:
			bi.logSystemStatus()
			
		case <-bi.ctx.Done():
			return
		}
	}
}

// logSystemStatus logs current system status
func (bi *BuildingIntegrator) logSystemStatus() {
	status := bi.sensorMgr.GetStatus()
	
	log.Printf("📈 System Status: %d/%d sensors active, %d total readings", 
		status.ActiveSensors, status.TotalSensors, status.TotalReadings)
		
	if status.Errors > 0 {
		log.Printf("⚠️  %d sensor errors detected", status.Errors)
	}
	
	if bi.asciiView != nil {
		asciiStats := bi.asciiView.GetStats()
		log.Printf("🎨 ASCII: %d objects rendered, %.1f FPS", 
			asciiStats.ObjectsRendered, asciiStats.FPS)
	}
}

// loadConfig loads building configuration from file or creates demo config
func loadConfig(configFile string, demoMode bool) (*BuildingConfig, error) {
	if demoMode {
		return createDemoConfig(), nil
	}

	// Try to load from file
	data, err := os.ReadFile(configFile)
	if err != nil {
		// If file doesn't exist, create demo config and save it
		if os.IsNotExist(err) {
			log.Printf("Config file not found, creating demo configuration: %s", configFile)
			config := createDemoConfig()
			
			// Save demo config
			configData, _ := json.MarshalIndent(config, "", "  ")
			if err := os.WriteFile(configFile, configData, 0644); err != nil {
				log.Printf("Warning: Could not save demo config: %v", err)
			} else {
				log.Printf("Demo configuration saved to: %s", configFile)
			}
			
			return config, nil
		}
		return nil, err
	}

	var config BuildingConfig
	if err := json.Unmarshal(data, &config); err != nil {
		return nil, fmt.Errorf("failed to parse config file: %w", err)
	}

	return &config, nil
}

// createDemoConfig creates a demo configuration with simulated building systems
func createDemoConfig() *BuildingConfig {
	return &BuildingConfig{
		BuildingID: "demo-office-building",
		Name:       "Demo Office Building",
		Location:   "123 Tech Street, Demo City",
		
		// Demo BACnet configuration
		BACnetConfig: &protocols.BACnetConfig{
			Interface:     "eth0",
			Port:          47808,
			DeviceID:      1234,
			NetworkNumber: 1,
			Timeout:       5 * time.Second,
			Simulation:    true, // Use simulated BACnet for demo
		},
		
		// Demo Modbus configuration  
		ModbusConfig: &protocols.ModbusConfig{
			Mode:       "tcp",
			Address:    "192.168.1.100:502",
			SlaveID:    1,
			Timeout:    5 * time.Second,
			Simulation: true, // Use simulated Modbus for demo
		},
		
		// Demo sensor configuration
		Sensors: []sensors.SensorConfig{
			// Floor 1 sensors
			{
				ID:       "temp-f1-r101",
				Name:     "Conference Room A Temperature",
				Type:     "temperature",
				Protocol: "bacnet",
				Address:  "1:analog-input:1",
				Unit:     "celsius",
				Floor:    1,
				Room:     "r101",
				Position: sensors.Position{X: 10, Y: 15, Z: 2.5},
				Limits:   sensors.Limits{Min: 18, Max: 26, Critical: true},
				ScanRate: 10 * time.Second,
				Enabled:  true,
			},
			{
				ID:       "humidity-f1-r101", 
				Name:     "Conference Room A Humidity",
				Type:     "humidity",
				Protocol: "bacnet",
				Address:  "1:analog-input:2",
				Unit:     "percent",
				Floor:    1,
				Room:     "r101",
				Position: sensors.Position{X: 10, Y: 15, Z: 2.5},
				Limits:   sensors.Limits{Min: 30, Max: 70, Critical: false},
				ScanRate: 15 * time.Second,
				Enabled:  true,
			},
			{
				ID:       "co2-f1-r101",
				Name:     "Conference Room A CO2",
				Type:     "co2",
				Protocol: "modbus",
				Address:  "40001",
				Unit:     "ppm", 
				Floor:    1,
				Room:     "r101",
				Position: sensors.Position{X: 12, Y: 15, Z: 2.5},
				Limits:   sensors.Limits{Min: 350, Max: 1000, Critical: true},
				DataType: "float32",
				ScanRate: 20 * time.Second,
				Enabled:  true,
			},
			// Office space sensors
			{
				ID:       "temp-f1-r102",
				Name:     "Open Office Temperature",
				Type:     "temperature", 
				Protocol: "bacnet",
				Address:  "1:analog-input:3",
				Unit:     "celsius",
				Floor:    1,
				Room:     "r102",
				Position: sensors.Position{X: 30, Y: 25, Z: 2.5},
				Limits:   sensors.Limits{Min: 20, Max: 24, Critical: true},
				ScanRate: 10 * time.Second,
				Enabled:  true,
			},
			{
				ID:       "occupancy-f1-r102",
				Name:     "Open Office Occupancy", 
				Type:     "occupancy",
				Protocol: "bacnet",
				Address:  "1:binary-input:1",
				Unit:     "people",
				Floor:    1,
				Room:     "r102",
				Position: sensors.Position{X: 25, Y: 20, Z: 3.0},
				Limits:   sensors.Limits{Min: 0, Max: 50, Critical: false},
				ScanRate: 30 * time.Second,
				Enabled:  true,
			},
			// HVAC system sensors
			{
				ID:       "ahu-supply-temp",
				Name:     "AHU Supply Temperature",
				Type:     "temperature",
				Protocol: "modbus", 
				Address:  "30001",
				Unit:     "celsius",
				Floor:    0, // Mechanical room
				Room:     "mechanical",
				Position: sensors.Position{X: 5, Y: 5, Z: 1.5},
				Limits:   sensors.Limits{Min: 12, Max: 18, Critical: true},
				DataType: "float32",
				ScanRate: 15 * time.Second,
				Enabled:  true,
			},
			{
				ID:       "ahu-return-temp",
				Name:     "AHU Return Temperature", 
				Type:     "temperature",
				Protocol: "modbus",
				Address:  "30002",
				Unit:     "celsius",
				Floor:    0,
				Room:     "mechanical",
				Position: sensors.Position{X: 8, Y: 5, Z: 1.5},
				Limits:   sensors.Limits{Min: 20, Max: 28, Critical: true},
				DataType: "float32",
				ScanRate: 15 * time.Second,
				Enabled:  true,
			},
			// Power monitoring
			{
				ID:       "main-power",
				Name:     "Main Electrical Panel Power",
				Type:     "power",
				Protocol: "modbus",
				Address:  "40101",
				Unit:     "kw",
				Floor:    0,
				Room:     "electrical",
				Position: sensors.Position{X: 2, Y: 8, Z: 1.5},
				Limits:   sensors.Limits{Min: 0, Max: 100, Critical: true},
				DataType: "float32",
				ScanRate: 20 * time.Second,
				Enabled:  true,
			},
		},
		
		// ASCII visualization configuration
		ASCII: &visualization.ASCIIConfig{
			Width:        120,
			Height:       40, 
			UpdateRate:   time.Second,
			ShowSensors:  true,
			ShowValues:   true,
			ShowAlarms:   true,
			ColorMode:    true,
			WebSocketURL: "ws://localhost:8080/ws",
		},
	}
}