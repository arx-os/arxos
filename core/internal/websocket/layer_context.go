// Package websocket provides layer-aware WebSocket communication for ArxOS
package websocket

import (
	"encoding/json"
	"fmt"
	"math"
	"sync"
	"time"
)

// Layer represents the interface layer (1-6 as per vision.md)
type Layer int

const (
	LayerCLI       Layer = 1 // Pure CLI (text only)
	LayerASCII     Layer = 2 // ASCII graphics
	LayerWebGL     Layer = 3 // 3D WebGL
	LayerAR        Layer = 4 // Augmented Reality
	LayerVR        Layer = 5 // Virtual Reality
	LayerNeural    Layer = 6 // Neural interface (future)
)

// Precision represents the spatial precision level
type Precision int

const (
	PrecisionMeter      Precision = 0 // 1m
	PrecisionDecimeter  Precision = 1 // 100mm
	PrecisionCentimeter Precision = 2 // 10mm
	PrecisionMillimeter Precision = 3 // 1mm
	PrecisionTenthMM    Precision = 4 // 0.1mm
	PrecisionHundrethMM Precision = 5 // 0.01mm
	PrecisionMicrometer Precision = 6 // 0.001mm (1μm)
	PrecisionNanometer  Precision = 9 // 0.000001mm (1nm)
)

// Bounds represents a spatial bounding box
type Bounds struct {
	MinX float64 `json:"min_x"`
	MinY float64 `json:"min_y"`
	MinZ float64 `json:"min_z"`
	MaxX float64 `json:"max_x"`
	MaxY float64 `json:"max_y"`
	MaxZ float64 `json:"max_z"`
}

// LayerContext provides context for layer-aware messaging
type LayerContext struct {
	Layer       Layer     `json:"layer"`        // Interface layer (1-6)
	Precision   Precision `json:"precision"`    // Spatial precision (0-9)
	Viewport    Bounds    `json:"viewport"`     // What's visible
	Zoom        float64   `json:"zoom"`         // Zoom level
	FrameRate   int       `json:"frame_rate"`   // Target FPS for this layer
	Quality     string    `json:"quality"`      // low, medium, high, ultra
	Timestamp   time.Time `json:"timestamp"`
	ClientID    string    `json:"client_id"`
	Capabilities []string `json:"capabilities"` // Client capabilities
}

// Message represents a layer-aware WebSocket message
type Message struct {
	ID        string          `json:"id"`
	Type      MessageType     `json:"type"`
	Context   LayerContext    `json:"context"`
	Payload   json.RawMessage `json:"payload"`
	Priority  Priority        `json:"priority"`
	Timestamp time.Time       `json:"timestamp"`
}

// MessageType defines the type of WebSocket message
type MessageType string

const (
	// Data messages
	MessageTypeData        MessageType = "data"
	MessageTypeUpdate      MessageType = "update"
	MessageTypeDelta       MessageType = "delta"
	MessageTypeSnapshot    MessageType = "snapshot"
	
	// Control messages
	MessageTypeSubscribe   MessageType = "subscribe"
	MessageTypeUnsubscribe MessageType = "unsubscribe"
	MessageTypePing        MessageType = "ping"
	MessageTypePong        MessageType = "pong"
	
	// Layer-specific messages
	MessageTypeLayerChange MessageType = "layer_change"
	MessageTypeViewportChange MessageType = "viewport_change"
	MessageTypePrecisionChange MessageType = "precision_change"
	
	// Error messages
	MessageTypeError       MessageType = "error"
)

// Priority defines message priority
type Priority int

const (
	PriorityLow       Priority = 0
	PriorityNormal    Priority = 1
	PriorityHigh      Priority = 2
	PriorityCritical  Priority = 3
)

// LayerCapabilities defines what each layer can handle
type LayerCapabilities struct {
	MaxDataPoints    int     `json:"max_data_points"`
	MaxUpdateRate    int     `json:"max_update_rate"`    // Updates per second
	MaxPrecision     Precision `json:"max_precision"`
	SupportsBinary   bool    `json:"supports_binary"`
	Supports3D       bool    `json:"supports_3d"`
	SupportsColor    bool    `json:"supports_color"`
	SupportsTextures bool    `json:"supports_textures"`
	MaxBandwidth     int64   `json:"max_bandwidth"`      // Bytes per second
}

// GetLayerCapabilities returns capabilities for each layer
func GetLayerCapabilities(layer Layer) LayerCapabilities {
	switch layer {
	case LayerCLI:
		return LayerCapabilities{
			MaxDataPoints:    100,
			MaxUpdateRate:    1,
			MaxPrecision:     PrecisionMillimeter,
			SupportsBinary:   false,
			Supports3D:       false,
			SupportsColor:    false,
			SupportsTextures: false,
			MaxBandwidth:     1024 * 10, // 10KB/s
		}
		
	case LayerASCII:
		return LayerCapabilities{
			MaxDataPoints:    1000,
			MaxUpdateRate:    10,
			MaxPrecision:     PrecisionMillimeter,
			SupportsBinary:   false,
			Supports3D:       false,
			SupportsColor:    true,
			SupportsTextures: false,
			MaxBandwidth:     1024 * 100, // 100KB/s
		}
		
	case LayerWebGL:
		return LayerCapabilities{
			MaxDataPoints:    100000,
			MaxUpdateRate:    60,
			MaxPrecision:     PrecisionTenthMM,
			SupportsBinary:   true,
			Supports3D:       true,
			SupportsColor:    true,
			SupportsTextures: true,
			MaxBandwidth:     1024 * 1024 * 10, // 10MB/s
		}
		
	case LayerAR:
		return LayerCapabilities{
			MaxDataPoints:    50000,
			MaxUpdateRate:    30,
			MaxPrecision:     PrecisionMillimeter,
			SupportsBinary:   true,
			Supports3D:       true,
			SupportsColor:    true,
			SupportsTextures: true,
			MaxBandwidth:     1024 * 1024 * 5, // 5MB/s
		}
		
	case LayerVR:
		return LayerCapabilities{
			MaxDataPoints:    200000,
			MaxUpdateRate:    90,
			MaxPrecision:     PrecisionTenthMM,
			SupportsBinary:   true,
			Supports3D:       true,
			SupportsColor:    true,
			SupportsTextures: true,
			MaxBandwidth:     1024 * 1024 * 20, // 20MB/s
		}
		
	case LayerNeural:
		return LayerCapabilities{
			MaxDataPoints:    1000000,
			MaxUpdateRate:    1000,
			MaxPrecision:     PrecisionNanometer,
			SupportsBinary:   true,
			Supports3D:       true,
			SupportsColor:    true,
			SupportsTextures: true,
			MaxBandwidth:     1024 * 1024 * 100, // 100MB/s
		}
		
	default:
		return LayerCapabilities{
			MaxDataPoints: 100,
			MaxUpdateRate: 1,
			MaxPrecision:  PrecisionMeter,
		}
	}
}

// NewLayerContext creates a new layer context
func NewLayerContext(layer Layer, precision Precision, viewport Bounds, zoom float64) *LayerContext {
	caps := GetLayerCapabilities(layer)
	
	// Clamp precision to layer maximum
	if precision > caps.MaxPrecision {
		precision = caps.MaxPrecision
	}
	
	return &LayerContext{
		Layer:       layer,
		Precision:   precision,
		Viewport:    viewport,
		Zoom:        zoom,
		FrameRate:   caps.MaxUpdateRate,
		Quality:     "medium",
		Timestamp:   time.Now(),
		ClientID:    generateClientID(),
		Capabilities: getLayerCapabilityNames(layer),
	}
}

// ShouldSendData determines if data should be sent based on context
func (ctx *LayerContext) ShouldSendData(dataPoint DataPoint) bool {
	// Check if data is within viewport
	if !ctx.IsInViewport(dataPoint.X, dataPoint.Y, dataPoint.Z) {
		return false
	}
	
	// Check if precision is sufficient
	if !ctx.IsPrecisionSufficient(dataPoint.RequiredPrecision) {
		return false
	}
	
	// Check zoom level relevance
	if !ctx.IsZoomRelevant(dataPoint.MinZoom, dataPoint.MaxZoom) {
		return false
	}
	
	return true
}

// IsInViewport checks if a point is within the viewport
func (ctx *LayerContext) IsInViewport(x, y, z float64) bool {
	return x >= ctx.Viewport.MinX && x <= ctx.Viewport.MaxX &&
	       y >= ctx.Viewport.MinY && y <= ctx.Viewport.MaxY &&
	       z >= ctx.Viewport.MinZ && z <= ctx.Viewport.MaxZ
}

// IsPrecisionSufficient checks if context precision meets requirements
func (ctx *LayerContext) IsPrecisionSufficient(required Precision) bool {
	return ctx.Precision >= required
}

// IsZoomRelevant checks if current zoom is within relevant range
func (ctx *LayerContext) IsZoomRelevant(minZoom, maxZoom float64) bool {
	if minZoom > 0 && ctx.Zoom < minZoom {
		return false
	}
	if maxZoom > 0 && ctx.Zoom > maxZoom {
		return false
	}
	return true
}

// GetPrecisionMeters returns the precision in meters
func (ctx *LayerContext) GetPrecisionMeters() float64 {
	return GetPrecisionValue(ctx.Precision)
}

// GetPrecisionValue returns the precision value in meters
func GetPrecisionValue(p Precision) float64 {
	switch p {
	case PrecisionMeter:
		return 1.0
	case PrecisionDecimeter:
		return 0.1
	case PrecisionCentimeter:
		return 0.01
	case PrecisionMillimeter:
		return 0.001
	case PrecisionTenthMM:
		return 0.0001
	case PrecisionHundrethMM:
		return 0.00001
	case PrecisionMicrometer:
		return 0.000001
	case PrecisionNanometer:
		return 0.000000001
	default:
		return 1.0
	}
}

// SimplifyForLayer simplifies data based on layer capabilities
func (ctx *LayerContext) SimplifyForLayer(data interface{}) interface{} {
	caps := GetLayerCapabilities(ctx.Layer)
	
	// Apply precision rounding
	if floatData, ok := data.([]float64); ok {
		precision := GetPrecisionValue(ctx.Precision)
		simplified := make([]float64, len(floatData))
		for i, v := range floatData {
			simplified[i] = math.Round(v/precision) * precision
		}
		return simplified
	}
	
	// Reduce data points if needed
	if points, ok := data.([]DataPoint); ok {
		if len(points) > caps.MaxDataPoints {
			// Simple decimation - in production use proper algorithms
			step := len(points) / caps.MaxDataPoints
			simplified := []DataPoint{}
			for i := 0; i < len(points); i += step {
				simplified = append(simplified, points[i])
			}
			return simplified
		}
	}
	
	return data
}

// DataPoint represents a spatial data point
type DataPoint struct {
	X, Y, Z           float64
	Value             interface{}
	RequiredPrecision Precision
	MinZoom           float64
	MaxZoom           float64
}

// LayerManager manages layer contexts for multiple clients
type LayerManager struct {
	mu       sync.RWMutex
	contexts map[string]*LayerContext // ClientID -> Context
	stats    map[Layer]*LayerStats
}

// LayerStats tracks statistics per layer
type LayerStats struct {
	ActiveClients   int
	MessagesSent    int64
	BytesSent       int64
	AverageFPS      float64
	LastUpdate      time.Time
}

// NewLayerManager creates a new layer manager
func NewLayerManager() *LayerManager {
	lm := &LayerManager{
		contexts: make(map[string]*LayerContext),
		stats:    make(map[Layer]*LayerStats),
	}
	
	// Initialize stats for each layer
	for layer := LayerCLI; layer <= LayerNeural; layer++ {
		lm.stats[layer] = &LayerStats{
			LastUpdate: time.Now(),
		}
	}
	
	return lm
}

// RegisterClient registers a new client with layer context
func (lm *LayerManager) RegisterClient(ctx *LayerContext) {
	lm.mu.Lock()
	defer lm.mu.Unlock()
	
	lm.contexts[ctx.ClientID] = ctx
	lm.stats[ctx.Layer].ActiveClients++
}

// UnregisterClient removes a client
func (lm *LayerManager) UnregisterClient(clientID string) {
	lm.mu.Lock()
	defer lm.mu.Unlock()
	
	if ctx, exists := lm.contexts[clientID]; exists {
		lm.stats[ctx.Layer].ActiveClients--
		delete(lm.contexts, clientID)
	}
}

// UpdateContext updates a client's layer context
func (lm *LayerManager) UpdateContext(clientID string, newCtx *LayerContext) {
	lm.mu.Lock()
	defer lm.mu.Unlock()
	
	if oldCtx, exists := lm.contexts[clientID]; exists {
		// Update stats if layer changed
		if oldCtx.Layer != newCtx.Layer {
			lm.stats[oldCtx.Layer].ActiveClients--
			lm.stats[newCtx.Layer].ActiveClients++
		}
	}
	
	newCtx.ClientID = clientID
	lm.contexts[clientID] = newCtx
}

// GetContext retrieves a client's context
func (lm *LayerManager) GetContext(clientID string) (*LayerContext, bool) {
	lm.mu.RLock()
	defer lm.mu.RUnlock()
	
	ctx, exists := lm.contexts[clientID]
	return ctx, exists
}

// GetLayerClients returns all clients for a specific layer
func (lm *LayerManager) GetLayerClients(layer Layer) []string {
	lm.mu.RLock()
	defer lm.mu.RUnlock()
	
	clients := []string{}
	for clientID, ctx := range lm.contexts {
		if ctx.Layer == layer {
			clients = append(clients, clientID)
		}
	}
	return clients
}

// BroadcastToLayer sends a message to all clients in a layer
func (lm *LayerManager) BroadcastToLayer(layer Layer, msg *Message) {
	clients := lm.GetLayerClients(layer)
	
	for _, clientID := range clients {
		if ctx, exists := lm.GetContext(clientID); exists {
			// Adapt message for client's specific context
			adaptedMsg := adaptMessageForContext(msg, ctx)
			// In production, send via actual WebSocket connection
			_ = adaptedMsg
		}
	}
	
	// Update stats
	lm.mu.Lock()
	lm.stats[layer].MessagesSent++
	lm.stats[layer].LastUpdate = time.Now()
	lm.mu.Unlock()
}

// GetStats returns statistics for all layers
func (lm *LayerManager) GetStats() map[Layer]*LayerStats {
	lm.mu.RLock()
	defer lm.mu.RUnlock()
	
	// Return a copy to avoid race conditions
	statsCopy := make(map[Layer]*LayerStats)
	for layer, stats := range lm.stats {
		statsCopy[layer] = &LayerStats{
			ActiveClients: stats.ActiveClients,
			MessagesSent:  stats.MessagesSent,
			BytesSent:     stats.BytesSent,
			AverageFPS:    stats.AverageFPS,
			LastUpdate:    stats.LastUpdate,
		}
	}
	return statsCopy
}

// Helper functions

func getLayerCapabilityNames(layer Layer) []string {
	caps := GetLayerCapabilities(layer)
	capabilities := []string{}
	
	if caps.SupportsBinary {
		capabilities = append(capabilities, "binary")
	}
	if caps.Supports3D {
		capabilities = append(capabilities, "3d")
	}
	if caps.SupportsColor {
		capabilities = append(capabilities, "color")
	}
	if caps.SupportsTextures {
		capabilities = append(capabilities, "textures")
	}
	
	return capabilities
}

func adaptMessageForContext(msg *Message, ctx *LayerContext) *Message {
	adapted := *msg
	adapted.Context = *ctx
	
	// Simplify payload based on layer capabilities
	var payload interface{}
	if err := json.Unmarshal(msg.Payload, &payload); err == nil {
		simplified := ctx.SimplifyForLayer(payload)
		if simplifiedJSON, err := json.Marshal(simplified); err == nil {
			adapted.Payload = simplifiedJSON
		}
	}
	
	return &adapted
}

func generateClientID() string {
	return fmt.Sprintf("client_%d", time.Now().UnixNano())
}

// String representations

func (l Layer) String() string {
	switch l {
	case LayerCLI:
		return "CLI"
	case LayerASCII:
		return "ASCII"
	case LayerWebGL:
		return "WebGL"
	case LayerAR:
		return "AR"
	case LayerVR:
		return "VR"
	case LayerNeural:
		return "Neural"
	default:
		return fmt.Sprintf("Layer%d", l)
	}
}

func (p Precision) String() string {
	switch p {
	case PrecisionMeter:
		return "1m"
	case PrecisionDecimeter:
		return "100mm"
	case PrecisionCentimeter:
		return "10mm"
	case PrecisionMillimeter:
		return "1mm"
	case PrecisionTenthMM:
		return "0.1mm"
	case PrecisionHundrethMM:
		return "0.01mm"
	case PrecisionMicrometer:
		return "1μm"
	case PrecisionNanometer:
		return "1nm"
	default:
		return fmt.Sprintf("Precision%d", p)
	}
}