// ASCII Visualization - Real-time building sensor data displayed in ASCII interface
package visualization

import (
	"context"
	"fmt"
	"log"
	"math"
	"strings"
	"sync"
	"time"

	"github.com/arxos/arxos/cmd/building-integration/sensors"
	"github.com/gorilla/websocket"
)

// ASCIIConfig holds configuration for ASCII visualization
type ASCIIConfig struct {
	Width        int           `json:"width"`         // Canvas width in characters
	Height       int           `json:"height"`        // Canvas height in characters
	UpdateRate   time.Duration `json:"update_rate"`   // How often to refresh display
	ShowSensors  bool          `json:"show_sensors"`  // Show sensor positions
	ShowValues   bool          `json:"show_values"`   // Show current values
	ShowAlarms   bool          `json:"show_alarms"`   // Highlight alarms
	ColorMode    bool          `json:"color_mode"`    // Use ANSI color codes
	WebSocketURL string        `json:"websocket_url"` // ArxOS WebSocket URL for integration
	FloorPlan    *FloorPlan    `json:"floor_plan"`    // Floor plan layout
}

// FloorPlan represents the building layout for ASCII rendering
type FloorPlan struct {
	Width       float64 `json:"width"`        // Real-world width (meters)
	Height      float64 `json:"height"`       // Real-world height (meters)
	Rooms       []Room  `json:"rooms"`        // Room definitions
	Walls       []Wall  `json:"walls"`        // Wall definitions
	Doors       []Door  `json:"doors"`        // Door definitions
	Windows     []Window `json:"windows"`     // Window definitions
}

// Room represents a room in the floor plan
type Room struct {
	ID       string  `json:"id"`
	Name     string  `json:"name"`
	X        float64 `json:"x"`        // Left edge (meters)
	Y        float64 `json:"y"`        // Top edge (meters)
	Width    float64 `json:"width"`    // Width (meters)
	Height   float64 `json:"height"`   // Height (meters)
	Type     string  `json:"type"`     // "office", "conference", "mechanical", etc.
}

// Wall represents a wall in the floor plan
type Wall struct {
	X1        float64 `json:"x1"`
	Y1        float64 `json:"y1"`
	X2        float64 `json:"x2"`
	Y2        float64 `json:"y2"`
	Thickness float64 `json:"thickness"`
	Type      string  `json:"type"` // "exterior", "interior", "load-bearing"
}

// Door represents a door opening
type Door struct {
	X      float64 `json:"x"`
	Y      float64 `json:"y"`
	Width  float64 `json:"width"`
	Height float64 `json:"height"`
	Open   bool    `json:"open"`
}

// Window represents a window opening
type Window struct {
	X      float64 `json:"x"`
	Y      float64 `json:"y"`
	Width  float64 `json:"width"`
	Height float64 `json:"height"`
}

// ASCIIVisualization manages real-time ASCII display of building sensor data
type ASCIIVisualization struct {
	config      *ASCIIConfig
	buildingID  string
	canvas      [][]rune
	colorCanvas [][]string
	sensorData  map[string]*sensors.SensorReading
	wsConn      *websocket.Conn
	wsConnMutex sync.RWMutex
	wsReconnecting bool
	ctx         context.Context
	cancel      context.CancelFunc
	wg          sync.WaitGroup
	mutex       sync.RWMutex
	
	// Statistics
	objectsRendered int
	frameCount      uint64
	lastFrameTime   time.Time
	fps             float64
}

// ASCIIStats represents rendering statistics
type ASCIIStats struct {
	ObjectsRendered int
	FPS             float64
	SensorCount     int
	AlarmCount      int
	LastUpdate      time.Time
}

// ANSI color codes for colored output
const (
	ColorReset  = "\033[0m"
	ColorRed    = "\033[31m"
	ColorGreen  = "\033[32m"
	ColorYellow = "\033[33m"
	ColorBlue   = "\033[34m"
	ColorPurple = "\033[35m"
	ColorCyan   = "\033[36m"
	ColorWhite  = "\033[37m"
	ColorBold   = "\033[1m"
	ColorDim    = "\033[2m"
)

// ASCII characters for different building elements
var (
	CharWall        = '█'
	CharDoor        = 'D'
	CharWindow      = 'W'
	CharEmpty       = ' '
	CharRoom        = '·'
	CharSensorGood  = 'S'
	CharSensorAlarm = '!'
	CharSensorError = 'X'
)

// NewASCIIVisualization creates a new ASCII visualization
func NewASCIIVisualization(config *ASCIIConfig, buildingID string) (*ASCIIVisualization, error) {
	ctx, cancel := context.WithCancel(context.Background())
	
	viz := &ASCIIVisualization{
		config:      config,
		buildingID:  buildingID,
		sensorData:  make(map[string]*sensors.SensorReading),
		ctx:         ctx,
		cancel:      cancel,
		lastFrameTime: time.Now(),
	}
	
	// Initialize canvas
	viz.initializeCanvas()
	
	// Create default floor plan if none provided
	if config.FloorPlan == nil {
		config.FloorPlan = viz.createDefaultFloorPlan()
	}
	
	return viz, nil
}

// initializeCanvas sets up the ASCII canvas
func (av *ASCIIVisualization) initializeCanvas() {
	av.canvas = make([][]rune, av.config.Height)
	av.colorCanvas = make([][]string, av.config.Height)
	
	for y := 0; y < av.config.Height; y++ {
		av.canvas[y] = make([]rune, av.config.Width)
		av.colorCanvas[y] = make([]string, av.config.Width)
		
		for x := 0; x < av.config.Width; x++ {
			av.canvas[y][x] = CharEmpty
			av.colorCanvas[y][x] = ColorReset
		}
	}
}

// createDefaultFloorPlan creates a simple demo floor plan
func (av *ASCIIVisualization) createDefaultFloorPlan() *FloorPlan {
	return &FloorPlan{
		Width:  50.0, // 50 meters wide
		Height: 30.0, // 30 meters deep
		Rooms: []Room{
			{ID: "r101", Name: "Conference A", X: 5, Y: 5, Width: 8, Height: 6, Type: "conference"},
			{ID: "r102", Name: "Open Office", X: 15, Y: 5, Width: 20, Height: 15, Type: "office"},
			{ID: "r103", Name: "Server Room", X: 5, Y: 15, Width: 6, Height: 8, Type: "mechanical"},
			{ID: "mechanical", Name: "Mechanical", X: 40, Y: 5, Width: 8, Height: 20, Type: "mechanical"},
			{ID: "electrical", Name: "Electrical", X: 2, Y: 25, Width: 4, Height: 4, Type: "electrical"},
		},
		Walls: []Wall{
			// Exterior walls
			{X1: 0, Y1: 0, X2: 50, Y2: 0, Thickness: 0.3, Type: "exterior"},     // North
			{X1: 50, Y1: 0, X2: 50, Y2: 30, Thickness: 0.3, Type: "exterior"},   // East
			{X1: 50, Y1: 30, X2: 0, Y2: 30, Thickness: 0.3, Type: "exterior"},   // South
			{X1: 0, Y1: 30, X2: 0, Y2: 0, Thickness: 0.3, Type: "exterior"},     // West
			// Interior walls
			{X1: 13, Y1: 5, X2: 13, Y2: 11, Thickness: 0.15, Type: "interior"},  // Conference room wall
			{X1: 5, Y1: 11, X2: 13, Y2: 11, Thickness: 0.15, Type: "interior"},  
			{X1: 11, Y1: 15, X2: 11, Y2: 23, Thickness: 0.15, Type: "interior"}, // Server room wall
		},
		Doors: []Door{
			{X: 9, Y: 5, Width: 0.8, Height: 0.2, Open: false},   // Conference room door
			{X: 25, Y: 5, Width: 0.8, Height: 0.2, Open: true},   // Office main entrance
			{X: 8, Y: 15, Width: 0.8, Height: 0.2, Open: false},  // Server room door
		},
		Windows: []Window{
			{X: 8, Y: 0, Width: 2, Height: 0.2},   // Conference room window
			{X: 20, Y: 0, Width: 4, Height: 0.2},  // Office windows
			{X: 30, Y: 0, Width: 4, Height: 0.2},
		},
	}
}

// Start begins the ASCII visualization
func (av *ASCIIVisualization) Start(ctx context.Context) error {
	log.Println("🎨 Starting ASCII visualization...")
	
	// Connect to ArxOS WebSocket if configured
	if av.config.WebSocketURL != "" {
		if err := av.connectWebSocket(); err != nil {
			log.Printf("⚠️  Failed to connect to ArxOS WebSocket: %v", err)
			// Continue without WebSocket - use console output
		}
		
		// Start WebSocket monitoring goroutine
		av.wg.Add(1)
		go av.monitorWebSocketConnection()
	}
	
	// Start rendering loop
	av.wg.Add(1)
	go av.renderLoop()
	
	log.Printf("✅ ASCII visualization started (%dx%d)", av.config.Width, av.config.Height)
	return nil
}

// Stop stops the ASCII visualization
func (av *ASCIIVisualization) Stop() {
	log.Println("🛑 Stopping ASCII visualization...")
	
	av.cancel()
	
	// Close WebSocket connection safely
	av.wsConnMutex.Lock()
	if av.wsConn != nil {
		av.wsConn.Close()
		av.wsConn = nil
	}
	av.wsConnMutex.Unlock()
	
	// Wait for goroutines
	done := make(chan struct{})
	go func() {
		av.wg.Wait()
		close(done)
	}()
	
	select {
	case <-done:
		log.Println("ASCII visualization stopped")
	case <-time.After(3 * time.Second):
		log.Println("Timeout waiting for ASCII visualization to stop")
	}
}

// UpdateSensor updates sensor data for visualization
func (av *ASCIIVisualization) UpdateSensor(reading *sensors.SensorReading) error {
	av.mutex.Lock()
	av.sensorData[reading.SensorID] = reading
	av.mutex.Unlock()
	
	return nil
}

// connectWebSocket connects to ArxOS WebSocket for real-time updates
func (av *ASCIIVisualization) connectWebSocket() error {
	av.wsConnMutex.Lock()
	defer av.wsConnMutex.Unlock()
	
	// Close existing connection if any
	if av.wsConn != nil {
		av.wsConn.Close()
		av.wsConn = nil
	}
	
	conn, _, err := websocket.DefaultDialer.Dial(av.config.WebSocketURL, nil)
	if err != nil {
		return err
	}
	
	av.wsConn = conn
	
	// Send layer context to identify as ASCII visualization client
	layerMsg := map[string]interface{}{
		"type": "layer_context",
		"context": map[string]interface{}{
			"layer":      "LayerASCII",
			"precision":  "high",
			"client_type": "building_integration",
		},
		"timestamp": time.Now().Format(time.RFC3339),
	}
	
	if err := conn.WriteJSON(layerMsg); err != nil {
		conn.Close()
		av.wsConn = nil
		return fmt.Errorf("failed to send layer context: %w", err)
	}
	
	log.Println("📡 Connected to ArxOS WebSocket")
	return nil
}

// monitorWebSocketConnection monitors and reconnects WebSocket if needed
func (av *ASCIIVisualization) monitorWebSocketConnection() {
	defer av.wg.Done()
	
	reconnectDelay := time.Second
	maxReconnectDelay := time.Minute
	
	for {
		select {
		case <-av.ctx.Done():
			return
		case <-time.After(5 * time.Second): // Check every 5 seconds
			av.wsConnMutex.RLock()
			needsReconnect := av.wsConn == nil && av.config.WebSocketURL != "" && !av.wsReconnecting
			av.wsConnMutex.RUnlock()
			
			if needsReconnect {
				av.wsConnMutex.Lock()
				av.wsReconnecting = true
				av.wsConnMutex.Unlock()
				
				log.Printf("🔄 Attempting WebSocket reconnection in %v...", reconnectDelay)
				time.Sleep(reconnectDelay)
				
				if err := av.connectWebSocket(); err != nil {
					log.Printf("⚠️  WebSocket reconnection failed: %v", err)
					// Exponential backoff
					reconnectDelay = time.Duration(math.Min(float64(reconnectDelay*2), float64(maxReconnectDelay)))
				} else {
					log.Println("✅ WebSocket reconnected successfully")
					reconnectDelay = time.Second // Reset delay
				}
				
				av.wsConnMutex.Lock()
				av.wsReconnecting = false
				av.wsConnMutex.Unlock()
			}
		}
	}
}

// renderLoop continuously renders the ASCII visualization
func (av *ASCIIVisualization) renderLoop() {
	defer av.wg.Done()
	
	ticker := time.NewTicker(av.config.UpdateRate)
	defer ticker.Stop()
	
	for {
		select {
		case <-ticker.C:
			av.render()
			av.updateFPS()
			
		case <-av.ctx.Done():
			return
		}
	}
}

// render creates the current ASCII frame
func (av *ASCIIVisualization) render() {
	av.mutex.Lock()
	defer av.mutex.Unlock()
	
	// Clear canvas
	av.clearCanvas()
	
	// Draw floor plan
	av.drawFloorPlan()
	
	// Draw sensors
	if av.config.ShowSensors {
		av.drawSensors()
	}
	
	// Draw values
	if av.config.ShowValues {
		av.drawValues()
	}
	
	// Output to console or WebSocket
	av.outputFrame()
	
	av.frameCount++
}

// clearCanvas resets the canvas
func (av *ASCIIVisualization) clearCanvas() {
	for y := 0; y < av.config.Height; y++ {
		for x := 0; x < av.config.Width; x++ {
			av.canvas[y][x] = CharEmpty
			av.colorCanvas[y][x] = ColorReset
		}
	}
}

// drawFloorPlan renders the building floor plan
func (av *ASCIIVisualization) drawFloorPlan() {
	if av.config.FloorPlan == nil {
		return
	}
	
	plan := av.config.FloorPlan
	
	// Calculate scale factors
	scaleX := float64(av.config.Width-2) / plan.Width   // Leave 1 char border
	scaleY := float64(av.config.Height-4) / plan.Height // Leave space for info
	
	// Draw rooms (filled areas)
	for _, room := range plan.Rooms {
		av.drawRoom(room, scaleX, scaleY)
	}
	
	// Draw walls (higher priority)
	for _, wall := range plan.Walls {
		av.drawWall(wall, scaleX, scaleY)
	}
	
	// Draw doors and windows
	for _, door := range plan.Doors {
		av.drawDoor(door, scaleX, scaleY)
	}
	for _, window := range plan.Windows {
		av.drawWindow(window, scaleX, scaleY)
	}
}

// drawRoom renders a room as a filled area
func (av *ASCIIVisualization) drawRoom(room Room, scaleX, scaleY float64) {
	x1 := int(room.X*scaleX) + 1
	y1 := int(room.Y*scaleY) + 1
	x2 := int((room.X+room.Width)*scaleX) + 1
	y2 := int((room.Y+room.Height)*scaleY) + 1
	
	// Fill room area
	for y := y1; y <= y2 && y < av.config.Height-2; y++ {
		for x := x1; x <= x2 && x < av.config.Width-1; x++ {
			if x >= 0 && y >= 0 {
				av.canvas[y][x] = CharRoom
				
				// Color based on room type
				switch room.Type {
				case "conference":
					av.colorCanvas[y][x] = ColorBlue
				case "office":
					av.colorCanvas[y][x] = ColorGreen
				case "mechanical":
					av.colorCanvas[y][x] = ColorYellow
				case "electrical":
					av.colorCanvas[y][x] = ColorRed
				default:
					av.colorCanvas[y][x] = ColorWhite
				}
			}
		}
	}
	
	// Draw room name if there's space
	nameX := x1 + (x2-x1)/2 - len(room.Name)/2
	nameY := y1 + (y2-y1)/2
	
	if nameY >= 0 && nameY < av.config.Height && nameX >= 0 && nameX+len(room.Name) < av.config.Width {
		for i, char := range room.Name {
			if nameX+i < av.config.Width && nameX+i >= 0 {
				av.canvas[nameY][nameX+i] = char
				av.colorCanvas[nameY][nameX+i] = ColorBold
			}
		}
	}
}

// drawWall renders a wall
func (av *ASCIIVisualization) drawWall(wall Wall, scaleX, scaleY float64) {
	x1 := int(wall.X1*scaleX) + 1
	y1 := int(wall.Y1*scaleY) + 1
	x2 := int(wall.X2*scaleX) + 1
	y2 := int(wall.Y2*scaleY) + 1
	
	// Draw line between points
	av.drawLine(x1, y1, x2, y2, CharWall, ColorWhite)
}

// drawDoor renders a door
func (av *ASCIIVisualization) drawDoor(door Door, scaleX, scaleY float64) {
	x := int(door.X*scaleX) + 1
	y := int(door.Y*scaleY) + 1
	
	if x >= 0 && x < av.config.Width && y >= 0 && y < av.config.Height {
		char := CharDoor
		color := ColorGreen
		if door.Open {
			char = '/'
			color = ColorCyan
		}
		av.canvas[y][x] = char
		av.colorCanvas[y][x] = color
	}
}

// drawWindow renders a window
func (av *ASCIIVisualization) drawWindow(window Window, scaleX, scaleY float64) {
	x := int(window.X*scaleX) + 1
	y := int(window.Y*scaleY) + 1
	
	if x >= 0 && x < av.config.Width && y >= 0 && y < av.config.Height {
		av.canvas[y][x] = CharWindow
		av.colorCanvas[y][x] = ColorCyan
	}
}

// drawSensors renders sensor positions and status
func (av *ASCIIVisualization) drawSensors() {
	if av.config.FloorPlan == nil {
		return
	}
	
	plan := av.config.FloorPlan
	scaleX := float64(av.config.Width-2) / plan.Width
	scaleY := float64(av.config.Height-4) / plan.Height
	
	for _, reading := range av.sensorData {
		x := int(reading.Position.X*scaleX) + 1
		y := int(reading.Position.Y*scaleY) + 1
		
		if x >= 0 && x < av.config.Width && y >= 0 && y < av.config.Height {
			char := CharSensorGood
			color := ColorGreen
			
			// Choose character and color based on sensor state
			switch reading.AlarmState {
			case "critical":
				char = CharSensorAlarm
				color = ColorRed + ColorBold
			case "warning":
				char = CharSensorAlarm
				color = ColorYellow
			case "normal":
				if reading.Quality == "good" {
					char = CharSensorGood
					color = ColorGreen
				} else {
					char = CharSensorError
					color = ColorRed + ColorDim
				}
			default:
				char = CharSensorError
				color = ColorRed
			}
			
			av.canvas[y][x] = char
			av.colorCanvas[y][x] = color
		}
	}
}

// drawValues renders sensor values as text
func (av *ASCIIVisualization) drawValues() {
	if av.config.FloorPlan == nil {
		return
	}
	
	// Draw sensor values in sidebar or bottom area
	infoY := av.config.Height - 3
	x := 1
	
	av.drawText(x, infoY, "SENSORS:", ColorBold)
	infoY++
	
	sensorCount := 0
	alarmCount := 0
	
	for _, reading := range av.sensorData {
		if sensorCount >= 10 { // Limit display to prevent overflow
			break
		}
		
		// Format value based on sensor type
		valueStr := av.formatSensorValue(reading)
		
		// Color based on alarm state
		color := ColorGreen
		switch reading.AlarmState {
		case "critical":
			color = ColorRed + ColorBold
			alarmCount++
		case "warning":
			color = ColorYellow
			alarmCount++
		}
		
		text := fmt.Sprintf("%-12s %s", reading.Name[:min(12, len(reading.Name))], valueStr)
		av.drawText(x, infoY, text, color)
		
		infoY++
		sensorCount++
		
		if infoY >= av.config.Height-1 {
			break
		}
	}
	
	// Draw status info
	statusY := 0
	av.drawText(1, statusY, fmt.Sprintf("Building: %s", av.buildingID), ColorBold)
	statusY++
	av.drawText(1, statusY, fmt.Sprintf("Sensors: %d | Alarms: %d | FPS: %.1f", 
		len(av.sensorData), alarmCount, av.fps), ColorWhite)
	
	av.objectsRendered = len(av.sensorData) + 1 // +1 for floor plan
}

// formatSensorValue formats a sensor value for display
func (av *ASCIIVisualization) formatSensorValue(reading *sensors.SensorReading) string {
	switch reading.Type {
	case sensors.SensorTypeTemperature:
		return fmt.Sprintf("%.1f°C", reading.Value)
	case sensors.SensorTypeHumidity:
		return fmt.Sprintf("%.1f%%RH", reading.Value)
	case sensors.SensorTypeCO2:
		return fmt.Sprintf("%.0fppm", reading.Value)
	case sensors.SensorTypePower:
		return fmt.Sprintf("%.1fkW", reading.Value)
	case sensors.SensorTypeVoltage:
		return fmt.Sprintf("%.1fV", reading.Value)
	case sensors.SensorTypeCurrent:
		return fmt.Sprintf("%.1fA", reading.Value)
	case sensors.SensorTypePressure:
		return fmt.Sprintf("%.0fPa", reading.Value)
	case sensors.SensorTypeFlow:
		return fmt.Sprintf("%.2fL/s", reading.Value)
	default:
		return fmt.Sprintf("%.2f%s", reading.Value, reading.Unit)
	}
}

// drawText renders text at specified position with color
func (av *ASCIIVisualization) drawText(x, y int, text, color string) {
	for i, char := range text {
		if x+i >= 0 && x+i < av.config.Width && y >= 0 && y < av.config.Height {
			av.canvas[y][x+i] = char
			av.colorCanvas[y][x+i] = color
		}
	}
}

// drawLine draws a line between two points using Bresenham's algorithm
func (av *ASCIIVisualization) drawLine(x1, y1, x2, y2 int, char rune, color string) {
	dx := int(math.Abs(float64(x2 - x1)))
	dy := int(math.Abs(float64(y2 - y1)))
	sx := 1
	if x1 >= x2 {
		sx = -1
	}
	sy := 1
	if y1 >= y2 {
		sy = -1
	}
	err := dx - dy
	
	x, y := x1, y1
	
	for {
		if x >= 0 && x < av.config.Width && y >= 0 && y < av.config.Height {
			av.canvas[y][x] = char
			av.colorCanvas[y][x] = color
		}
		
		if x == x2 && y == y2 {
			break
		}
		
		e2 := 2 * err
		if e2 > -dy {
			err -= dy
			x += sx
		}
		if e2 < dx {
			err += dx
			y += sy
		}
	}
}

// outputFrame outputs the current frame to console or WebSocket
func (av *ASCIIVisualization) outputFrame() {
	av.wsConnMutex.RLock()
	hasConnection := av.wsConn != nil
	av.wsConnMutex.RUnlock()
	
	if hasConnection {
		av.outputToWebSocket()
	} else {
		av.outputToConsole()
	}
}

// outputToConsole prints the frame to console
func (av *ASCIIVisualization) outputToConsole() {
	// Clear screen
	fmt.Print("\033[2J\033[H")
	
	var output strings.Builder
	
	for y := 0; y < av.config.Height; y++ {
		for x := 0; x < av.config.Width; x++ {
			if av.config.ColorMode {
				output.WriteString(av.colorCanvas[y][x])
			}
			output.WriteRune(av.canvas[y][x])
			if av.config.ColorMode {
				output.WriteString(ColorReset)
			}
		}
		output.WriteRune('\n')
	}
	
	fmt.Print(output.String())
}

// outputToWebSocket sends frame to ArxOS WebSocket
func (av *ASCIIVisualization) outputToWebSocket() {
	// Convert frame to string
	var frame strings.Builder
	for y := 0; y < av.config.Height; y++ {
		for x := 0; x < av.config.Width; x++ {
			frame.WriteRune(av.canvas[y][x])
		}
		frame.WriteRune('\n')
	}
	
	// Create message for ArxOS
	message := map[string]interface{}{
		"type": "ascii_frame",
		"building_id": av.buildingID,
		"frame": frame.String(),
		"sensors": len(av.sensorData),
		"timestamp": time.Now().Format(time.RFC3339),
		"stats": map[string]interface{}{
			"objects_rendered": av.objectsRendered,
			"fps": av.fps,
			"sensor_count": len(av.sensorData),
		},
	}
	
	// Send to WebSocket with proper mutex protection
	av.wsConnMutex.Lock()
	if av.wsConn != nil {
		err := av.wsConn.WriteJSON(message)
		if err != nil {
			log.Printf("Failed to send ASCII frame to WebSocket: %v", err)
			// Connection lost, close it to trigger reconnection
			av.wsConn.Close()
			av.wsConn = nil
			av.wsConnMutex.Unlock()
			// Fall back to console output
			av.outputToConsole()
			return
		}
	}
	av.wsConnMutex.Unlock()
}

// updateFPS calculates and updates FPS counter
func (av *ASCIIVisualization) updateFPS() {
	now := time.Now()
	delta := now.Sub(av.lastFrameTime).Seconds()
	
	if delta > 0 {
		av.fps = av.fps*0.9 + (1.0/delta)*0.1 // Smooth FPS calculation
	}
	
	av.lastFrameTime = now
}

// GetStats returns current rendering statistics
func (av *ASCIIVisualization) GetStats() ASCIIStats {
	av.mutex.RLock()
	defer av.mutex.RUnlock()
	
	alarmCount := 0
	for _, reading := range av.sensorData {
		if reading.AlarmState != "normal" {
			alarmCount++
		}
	}
	
	return ASCIIStats{
		ObjectsRendered: av.objectsRendered,
		FPS:             av.fps,
		SensorCount:     len(av.sensorData),
		AlarmCount:      alarmCount,
		LastUpdate:      time.Now(),
	}
}

// Helper function for min
func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}