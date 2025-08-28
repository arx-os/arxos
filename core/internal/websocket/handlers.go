// Package websocket provides WebSocket handlers with layer awareness
package websocket

import (
	"encoding/json"
	"fmt"
	"math"
	"strings"
	"time"
	
	"github.com/arxos/arxos/core/internal/arxobject"
)

// MessageHandler processes messages based on layer context
type MessageHandler struct {
	server *Server
}

// NewMessageHandler creates a new message handler
func NewMessageHandler(server *Server) *MessageHandler {
	return &MessageHandler{server: server}
}

// HandleObjectUpdate processes object updates with layer awareness
func (h *MessageHandler) HandleObjectUpdate(client *Client, msg *Message) error {
	// Extract object data
	var obj arxobject.ArxObjectUnified
	if err := json.Unmarshal(msg.Payload, &obj); err != nil {
		return fmt.Errorf("failed to unmarshal object: %w", err)
	}
	
	// Apply layer-specific filtering
	filtered := h.filterObjectForLayer(&obj, client.Context)
	
	// Create response based on layer
	response := &Message{
		Type:      "object_update",
		Timestamp: time.Now(),
		Layer:     client.Context.Layer,
		Payload:   nil,
	}
	
	// Adapt response for layer
	switch client.Context.Layer {
	case LayerCLI:
		response.Payload = h.objectToCLI(filtered)
	case LayerASCII:
		response.Payload = h.objectToASCII(filtered)
	case LayerWebGL:
		response.Payload = h.objectToWebGL(filtered)
	case LayerAR:
		response.Payload = h.objectToAR(filtered)
	case LayerVR:
		response.Payload = h.objectToVR(filtered)
	case LayerNeural:
		response.Payload = h.objectToNeural(filtered)
	}
	
	return client.Send(response)
}

// HandleViewportChange processes viewport changes
func (h *MessageHandler) HandleViewportChange(client *Client, msg *Message) error {
	var viewport Bounds
	if err := json.Unmarshal(msg.Payload, &viewport); err != nil {
		return fmt.Errorf("failed to unmarshal viewport: %w", err)
	}
	
	// Update client viewport
	client.Context.Viewport = viewport
	
	// Get objects in new viewport
	objects := h.server.GetObjectsInViewport(viewport, client.Context.Precision)
	
	// Send filtered objects
	response := &Message{
		Type:      "viewport_update",
		Timestamp: time.Now(),
		Layer:     client.Context.Layer,
		Payload:   objects,
	}
	
	return client.Send(response)
}

// HandlePrecisionChange adjusts the precision level
func (h *MessageHandler) HandlePrecisionChange(client *Client, msg *Message) error {
	var precision Precision
	if err := json.Unmarshal(msg.Payload, &precision); err != nil {
		return fmt.Errorf("failed to unmarshal precision: %w", err)
	}
	
	// Validate precision for layer
	maxPrecision := h.getMaxPrecisionForLayer(client.Context.Layer)
	if precision > maxPrecision {
		precision = maxPrecision
	}
	
	client.Context.Precision = precision
	
	// Refresh current view with new precision
	return h.HandleViewportChange(client, &Message{
		Payload: mustMarshal(client.Context.Viewport),
	})
}

// filterObjectForLayer applies layer-specific filtering
func (h *MessageHandler) filterObjectForLayer(obj *arxobject.ArxObjectUnified, ctx *LayerContext) *arxobject.ArxObjectUnified {
	filtered := obj.Clone()
	
	// Apply precision-based simplification
	if ctx.Precision <= PrecisionMeter {
		// Only keep bounding box
		filtered.Geometry.Points = nil
		filtered.Geometry.Vertices = nil
		filtered.Geometry.Faces = nil
	} else if ctx.Precision <= PrecisionCentimeter {
		// Simplify geometry
		filtered.Geometry.Points = h.simplifyPoints(filtered.Geometry.Points, ctx.Precision)
	}
	
	// Apply layer-based property filtering
	switch ctx.Layer {
	case LayerCLI:
		// Keep only essential properties
		essentials := make(arxobject.Properties)
		for k, v := range filtered.Properties {
			if h.isEssentialProperty(k) {
				essentials[k] = v
			}
		}
		filtered.Properties = essentials
		
	case LayerASCII:
		// Convert complex properties to strings
		for k, v := range filtered.Properties {
			filtered.Properties[k] = fmt.Sprintf("%v", v)
		}
	}
	
	// Apply viewport culling
	if !h.isInViewport(filtered, ctx.Viewport) {
		return nil
	}
	
	return filtered
}

// simplifyPoints reduces point cloud density based on precision
func (h *MessageHandler) simplifyPoints(points []arxobject.Point3D, precision Precision) []arxobject.Point3D {
	if len(points) == 0 {
		return points
	}
	
	// Calculate sampling rate based on precision
	sampleRate := int(math.Pow(10, float64(precision)))
	if sampleRate > len(points) {
		return points
	}
	
	// Sample points uniformly
	simplified := make([]arxobject.Point3D, 0, len(points)/sampleRate)
	for i := 0; i < len(points); i += sampleRate {
		simplified = append(simplified, points[i])
	}
	
	return simplified
}

// isEssentialProperty determines if a property is essential for CLI
func (h *MessageHandler) isEssentialProperty(key string) bool {
	essentials := []string{"name", "type", "status", "confidence", "id"}
	for _, e := range essentials {
		if strings.EqualFold(key, e) {
			return true
		}
	}
	return false
}

// isInViewport checks if object is within viewport
func (h *MessageHandler) isInViewport(obj *arxobject.ArxObjectUnified, viewport Bounds) bool {
	bbox := obj.Geometry.BoundingBox
	
	// Check if bounding boxes overlap
	return !(bbox.Max.X < viewport.Min.X || bbox.Min.X > viewport.Max.X ||
		bbox.Max.Y < viewport.Min.Y || bbox.Min.Y > viewport.Max.Y ||
		bbox.Max.Z < viewport.Min.Z || bbox.Min.Z > viewport.Max.Z)
}

// getMaxPrecisionForLayer returns maximum precision for a layer
func (h *MessageHandler) getMaxPrecisionForLayer(layer Layer) Precision {
	switch layer {
	case LayerCLI:
		return PrecisionMeter
	case LayerASCII:
		return PrecisionDecimeter
	case LayerWebGL:
		return PrecisionCentimeter
	case LayerAR:
		return PrecisionMillimeter
	case LayerVR:
		return PrecisionMicrometer
	case LayerNeural:
		return PrecisionNanometer
	default:
		return PrecisionMeter
	}
}

// Layer-specific conversion functions

func (h *MessageHandler) objectToCLI(obj *arxobject.ArxObjectUnified) json.RawMessage {
	if obj == nil {
		return nil
	}
	
	// Create simple text representation
	data := map[string]interface{}{
		"id":         obj.ID,
		"type":       obj.Type,
		"name":       obj.Name,
		"path":       obj.Path.String(),
		"confidence": fmt.Sprintf("%.2f", obj.GetConfidenceScore()),
		"status":     obj.ValidationStatus,
	}
	
	return mustMarshal(data)
}

func (h *MessageHandler) objectToASCII(obj *arxobject.ArxObjectUnified) json.RawMessage {
	if obj == nil {
		return nil
	}
	
	// Create ASCII art representation
	ascii := h.generateASCIIArt(obj)
	
	data := map[string]interface{}{
		"id":         obj.ID,
		"type":       obj.Type,
		"name":       obj.Name,
		"ascii":      ascii,
		"properties": obj.Properties,
	}
	
	return mustMarshal(data)
}

func (h *MessageHandler) objectToWebGL(obj *arxobject.ArxObjectUnified) json.RawMessage {
	if obj == nil {
		return nil
	}
	
	// Full 3D representation
	return mustMarshal(obj)
}

func (h *MessageHandler) objectToAR(obj *arxobject.ArxObjectUnified) json.RawMessage {
	if obj == nil {
		return nil
	}
	
	// AR-optimized with anchoring data
	data := map[string]interface{}{
		"object":      obj,
		"anchors":     h.generateAnchors(obj),
		"occlusion":   h.generateOcclusionMesh(obj),
		"interactions": h.getARInteractions(obj),
	}
	
	return mustMarshal(data)
}

func (h *MessageHandler) objectToVR(obj *arxobject.ArxObjectUnified) json.RawMessage {
	if obj == nil {
		return nil
	}
	
	// VR-optimized with collision and haptics
	data := map[string]interface{}{
		"object":      obj,
		"collision":   h.generateCollisionMesh(obj),
		"haptics":     h.getHapticProperties(obj),
		"teleport":    h.getTeleportPoints(obj),
		"grabbable":   h.isGrabbable(obj),
	}
	
	return mustMarshal(data)
}

func (h *MessageHandler) objectToNeural(obj *arxobject.ArxObjectUnified) json.RawMessage {
	if obj == nil {
		return nil
	}
	
	// Neural interface with thought patterns
	data := map[string]interface{}{
		"object":         obj,
		"thoughtMatrix":  h.generateThoughtMatrix(obj),
		"intentMapping":  h.getIntentMapping(obj),
		"neuralAnchors":  h.getNeuralAnchors(obj),
		"consciousness":  h.getConsciousnessLevel(obj),
	}
	
	return mustMarshal(data)
}

// Helper functions for layer-specific features

func (h *MessageHandler) generateASCIIArt(obj *arxobject.ArxObjectUnified) string {
	switch obj.Type {
	case arxobject.TypeWall:
		return `
╔════════════╗
║            ║
║    WALL    ║
║            ║
╚════════════╝`
	case arxobject.TypeDoor:
		return `
╔════╗╔════╗
║    ╚╝    ║
║   DOOR   ║
║    ╔╗    ║
╚════╝╚════╝`
	case arxobject.TypeWindow:
		return `
╔══╦══╦══╗
║  ║  ║  ║
╠══╬══╬══╣
║  ║  ║  ║
╚══╩══╩══╝`
	default:
		return `[${obj.Type}]`
	}
}

func (h *MessageHandler) generateAnchors(obj *arxobject.ArxObjectUnified) []map[string]interface{} {
	// Generate AR anchor points
	return []map[string]interface{}{
		{
			"type":     "corner",
			"position": obj.Geometry.BoundingBox.Min,
			"strength": 0.9,
		},
		{
			"type":     "center",
			"position": obj.Geometry.Position,
			"strength": 1.0,
		},
	}
}

func (h *MessageHandler) generateOcclusionMesh(obj *arxobject.ArxObjectUnified) interface{} {
	// Simplified occlusion mesh for AR
	return map[string]interface{}{
		"vertices": obj.Geometry.Vertices,
		"faces":    obj.Geometry.Faces,
		"material": "occlusion",
	}
}

func (h *MessageHandler) getARInteractions(obj *arxobject.ArxObjectUnified) []string {
	interactions := []string{"tap", "view"}
	
	if obj.Type == arxobject.TypeDoor {
		interactions = append(interactions, "open", "close")
	}
	
	return interactions
}

func (h *MessageHandler) generateCollisionMesh(obj *arxobject.ArxObjectUnified) interface{} {
	// Generate collision mesh for VR
	return map[string]interface{}{
		"type":        "box",
		"bounds":      obj.Geometry.BoundingBox,
		"isStatic":    true,
		"friction":    0.5,
		"restitution": 0.1,
	}
}

func (h *MessageHandler) getHapticProperties(obj *arxobject.ArxObjectUnified) map[string]interface{} {
	// Material-based haptic feedback
	haptics := map[string]interface{}{
		"texture":    "smooth",
		"hardness":   0.8,
		"temperature": 20.0, // Celsius
	}
	
	switch obj.Material {
	case "wood":
		haptics["texture"] = "grainy"
		haptics["hardness"] = 0.6
	case "metal":
		haptics["texture"] = "smooth"
		haptics["hardness"] = 1.0
		haptics["temperature"] = 18.0
	case "glass":
		haptics["texture"] = "smooth"
		haptics["hardness"] = 0.9
	}
	
	return haptics
}

func (h *MessageHandler) getTeleportPoints(obj *arxobject.ArxObjectUnified) []arxobject.Point3D {
	// Valid teleport destinations
	if obj.Type == arxobject.TypeFloor || obj.Type == arxobject.TypeRoom {
		return []arxobject.Point3D{obj.Geometry.Position}
	}
	return nil
}

func (h *MessageHandler) isGrabbable(obj *arxobject.ArxObjectUnified) bool {
	// Check if object can be grabbed in VR
	grabbableTypes := []arxobject.ArxObjectType{
		arxobject.TypeFurniture,
		arxobject.TypeEquipment,
		arxobject.TypeAppliance,
	}
	
	for _, t := range grabbableTypes {
		if obj.Type == t {
			return true
		}
	}
	return false
}

func (h *MessageHandler) generateThoughtMatrix(obj *arxobject.ArxObjectUnified) [][]float64 {
	// Neural interface thought patterns
	return [][]float64{
		{0.8, 0.2, 0.5},  // Attention vector
		{0.3, 0.9, 0.1},  // Interest vector
		{0.6, 0.4, 0.7},  // Interaction vector
	}
}

func (h *MessageHandler) getIntentMapping(obj *arxobject.ArxObjectUnified) map[string]string {
	// Map thoughts to actions
	return map[string]string{
		"examine":  "view_details",
		"modify":   "edit_properties",
		"navigate": "teleport_to",
		"query":    "get_info",
	}
}

func (h *MessageHandler) getNeuralAnchors(obj *arxobject.ArxObjectUnified) []interface{} {
	// Spatial memory anchors for neural interface
	return []interface{}{
		map[string]interface{}{
			"type":     "spatial",
			"position": obj.Geometry.Position,
			"strength": obj.GetConfidenceScore(),
		},
		map[string]interface{}{
			"type":      "semantic",
			"concept":   string(obj.Type),
			"relations": len(obj.Relationships),
		},
	}
}

func (h *MessageHandler) getConsciousnessLevel(obj *arxobject.ArxObjectUnified) float64 {
	// Object awareness level for neural interface
	// Based on confidence and validation status
	base := obj.GetConfidenceScore()
	
	if obj.ValidationStatus == arxobject.ValidationValidated {
		base *= 1.2
	}
	
	if base > 1.0 {
		base = 1.0
	}
	
	return base
}

// mustMarshal panics if marshaling fails (for internal use only)
func mustMarshal(v interface{}) json.RawMessage {
	data, err := json.Marshal(v)
	if err != nil {
		panic(fmt.Sprintf("failed to marshal: %v", err))
	}
	return data
}