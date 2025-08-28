// Package websocket provides viewport-based optimization
package websocket

import (
	"math"
	"sort"
	"sync"
	
	"github.com/arxos/arxos/core/internal/arxobject"
)

// ViewportManager handles viewport-based object culling and LOD
type ViewportManager struct {
	mu          sync.RWMutex
	octree      *Octree
	viewports   map[string]*ClientViewport  // Client ID -> Viewport
	objectCache map[string]*CachedObject    // Object ID -> Cached data
}

// ClientViewport tracks a client's viewport state
type ClientViewport struct {
	ClientID     string
	Bounds       Bounds
	Layer        Layer
	Precision    Precision
	Zoom         float64
	CameraPos    arxobject.Point3D
	CameraDir    Vector3
	FOV          float64  // Field of view in degrees
	LastUpdate   int64    // Unix timestamp
	VisibleObjects []string // IDs of visible objects
}

// CachedObject stores pre-computed LOD versions
type CachedObject struct {
	Object      *arxobject.ArxObjectUnified
	LODs        map[Precision]*arxobject.ArxObjectUnified
	LastAccess  int64
	UpdateCount int
}

// Vector3 represents a 3D vector
type Vector3 struct {
	X, Y, Z float64
}

// NewViewportManager creates a new viewport manager
func NewViewportManager() *ViewportManager {
	return &ViewportManager{
		octree:      NewOctree(DefaultWorldBounds()),
		viewports:   make(map[string]*ClientViewport),
		objectCache: make(map[string]*CachedObject),
	}
}

// DefaultWorldBounds returns default world boundaries
func DefaultWorldBounds() Bounds {
	const worldSize = 1000000000 // 1km in millimeters
	return Bounds{
		Min: arxobject.Point3D{X: -worldSize, Y: -worldSize, Z: -worldSize},
		Max: arxobject.Point3D{X: worldSize, Y: worldSize, Z: worldSize},
	}
}

// RegisterClient registers a new client viewport
func (vm *ViewportManager) RegisterClient(clientID string, viewport *ClientViewport) {
	vm.mu.Lock()
	defer vm.mu.Unlock()
	
	viewport.ClientID = clientID
	vm.viewports[clientID] = viewport
}

// UnregisterClient removes a client viewport
func (vm *ViewportManager) UnregisterClient(clientID string) {
	vm.mu.Lock()
	defer vm.mu.Unlock()
	
	delete(vm.viewports, clientID)
}

// UpdateViewport updates a client's viewport
func (vm *ViewportManager) UpdateViewport(clientID string, bounds Bounds, zoom float64, cameraPos arxobject.Point3D) {
	vm.mu.Lock()
	defer vm.mu.Unlock()
	
	if viewport, exists := vm.viewports[clientID]; exists {
		viewport.Bounds = bounds
		viewport.Zoom = zoom
		viewport.CameraPos = cameraPos
		viewport.LastUpdate = getCurrentTimestamp()
		
		// Update visible objects
		viewport.VisibleObjects = vm.findVisibleObjects(viewport)
	}
}

// GetVisibleObjects returns objects visible in a viewport
func (vm *ViewportManager) GetVisibleObjects(clientID string) []*arxobject.ArxObjectUnified {
	vm.mu.RLock()
	defer vm.mu.RUnlock()
	
	viewport, exists := vm.viewports[clientID]
	if !exists {
		return nil
	}
	
	// Query octree for objects in viewport
	candidates := vm.octree.Query(viewport.Bounds)
	
	// Apply frustum culling
	visible := vm.frustumCull(candidates, viewport)
	
	// Apply LOD selection
	withLOD := vm.selectLOD(visible, viewport)
	
	// Apply occlusion culling (simplified)
	final := vm.occlusionCull(withLOD, viewport)
	
	return final
}

// AddObject adds an object to the spatial index
func (vm *ViewportManager) AddObject(obj *arxobject.ArxObjectUnified) {
	vm.mu.Lock()
	defer vm.mu.Unlock()
	
	// Add to octree
	vm.octree.Insert(obj)
	
	// Create cache entry
	vm.objectCache[obj.ID] = &CachedObject{
		Object:     obj,
		LODs:       make(map[Precision]*arxobject.ArxObjectUnified),
		LastAccess: getCurrentTimestamp(),
	}
}

// RemoveObject removes an object from the spatial index
func (vm *ViewportManager) RemoveObject(objectID string) {
	vm.mu.Lock()
	defer vm.mu.Unlock()
	
	if cached, exists := vm.objectCache[objectID]; exists {
		vm.octree.Remove(cached.Object)
		delete(vm.objectCache, objectID)
	}
}

// UpdateObject updates an object's position
func (vm *ViewportManager) UpdateObject(obj *arxobject.ArxObjectUnified) {
	vm.mu.Lock()
	defer vm.mu.Unlock()
	
	// Remove old position
	if cached, exists := vm.objectCache[obj.ID]; exists {
		vm.octree.Remove(cached.Object)
	}
	
	// Insert at new position
	vm.octree.Insert(obj)
	
	// Update cache
	if cached, exists := vm.objectCache[obj.ID]; exists {
		cached.Object = obj
		cached.UpdateCount++
		cached.LastAccess = getCurrentTimestamp()
		// Clear LOD cache on update
		cached.LODs = make(map[Precision]*arxobject.ArxObjectUnified)
	}
}

// findVisibleObjects finds objects visible in viewport
func (vm *ViewportManager) findVisibleObjects(viewport *ClientViewport) []string {
	candidates := vm.octree.Query(viewport.Bounds)
	
	visible := []string{}
	for _, obj := range candidates {
		if vm.isInViewport(obj, viewport.Bounds) {
			visible = append(visible, obj.ID)
		}
	}
	
	return visible
}

// isInViewport checks if object is in viewport
func (vm *ViewportManager) isInViewport(obj *arxobject.ArxObjectUnified, viewport Bounds) bool {
	bbox := obj.Geometry.BoundingBox
	
	// Check AABB intersection
	return !(bbox.Max.X < viewport.Min.X || bbox.Min.X > viewport.Max.X ||
		bbox.Max.Y < viewport.Min.Y || bbox.Min.Y > viewport.Max.Y ||
		bbox.Max.Z < viewport.Min.Z || bbox.Min.Z > viewport.Max.Z)
}

// frustumCull performs view frustum culling
func (vm *ViewportManager) frustumCull(objects []*arxobject.ArxObjectUnified, viewport *ClientViewport) []*arxobject.ArxObjectUnified {
	if viewport.FOV <= 0 {
		// No frustum culling if FOV not set
		return objects
	}
	
	culled := []*arxobject.ArxObjectUnified{}
	frustum := vm.buildFrustum(viewport)
	
	for _, obj := range objects {
		if vm.isInFrustum(obj, frustum) {
			culled = append(culled, obj)
		}
	}
	
	return culled
}

// Frustum represents a view frustum
type Frustum struct {
	Planes [6]Plane // near, far, left, right, top, bottom
}

// Plane represents a 3D plane
type Plane struct {
	Normal   Vector3
	Distance float64
}

// buildFrustum creates a view frustum from viewport
func (vm *ViewportManager) buildFrustum(viewport *ClientViewport) Frustum {
	// Simplified frustum for now
	aspect := 16.0 / 9.0  // Assume 16:9 aspect
	near := 100.0         // 10cm near plane
	far := 1000000.0      // 1km far plane
	
	halfFOV := (viewport.FOV * math.Pi / 180.0) / 2.0
	nearHeight := 2.0 * math.Tan(halfFOV) * near
	nearWidth := nearHeight * aspect
	
	// Camera coordinate system
	forward := viewport.CameraDir
	right := vm.cross(forward, Vector3{0, 0, 1})
	up := vm.cross(right, forward)
	
	// Frustum planes
	frustum := Frustum{}
	
	// Near plane
	frustum.Planes[0] = Plane{
		Normal:   forward,
		Distance: near,
	}
	
	// Far plane
	frustum.Planes[1] = Plane{
		Normal:   Vector3{-forward.X, -forward.Y, -forward.Z},
		Distance: far,
	}
	
	// Left plane
	leftNormal := vm.normalize(vm.cross(up, vm.add(
		vm.scale(forward, near),
		vm.scale(right, -nearWidth/2),
	)))
	frustum.Planes[2] = Plane{Normal: leftNormal, Distance: 0}
	
	// Right plane
	rightNormal := vm.normalize(vm.cross(vm.add(
		vm.scale(forward, near),
		vm.scale(right, nearWidth/2),
	), up))
	frustum.Planes[3] = Plane{Normal: rightNormal, Distance: 0}
	
	// Top plane
	topNormal := vm.normalize(vm.cross(right, vm.add(
		vm.scale(forward, near),
		vm.scale(up, nearHeight/2),
	)))
	frustum.Planes[4] = Plane{Normal: topNormal, Distance: 0}
	
	// Bottom plane
	bottomNormal := vm.normalize(vm.cross(vm.add(
		vm.scale(forward, near),
		vm.scale(up, -nearHeight/2),
	), right))
	frustum.Planes[5] = Plane{Normal: bottomNormal, Distance: 0}
	
	return frustum
}

// isInFrustum checks if object is in frustum
func (vm *ViewportManager) isInFrustum(obj *arxobject.ArxObjectUnified, frustum Frustum) bool {
	// Test bounding box against frustum planes
	bbox := obj.Geometry.BoundingBox
	
	for _, plane := range frustum.Planes {
		// Find the vertex farthest in the direction of the plane normal
		p := arxobject.Point3D{}
		
		if plane.Normal.X >= 0 {
			p.X = bbox.Max.X
		} else {
			p.X = bbox.Min.X
		}
		
		if plane.Normal.Y >= 0 {
			p.Y = bbox.Max.Y
		} else {
			p.Y = bbox.Min.Y
		}
		
		if plane.Normal.Z >= 0 {
			p.Z = bbox.Max.Z
		} else {
			p.Z = bbox.Min.Z
		}
		
		// Check if point is behind plane
		dist := plane.Normal.X*float64(p.X) +
			plane.Normal.Y*float64(p.Y) +
			plane.Normal.Z*float64(p.Z) - plane.Distance
			
		if dist < 0 {
			return false // Object is outside frustum
		}
	}
	
	return true
}

// selectLOD selects appropriate LOD for objects
func (vm *ViewportManager) selectLOD(objects []*arxobject.ArxObjectUnified, viewport *ClientViewport) []*arxobject.ArxObjectUnified {
	result := make([]*arxobject.ArxObjectUnified, len(objects))
	
	for i, obj := range objects {
		// Calculate distance from camera
		distance := vm.distanceToCamera(obj, viewport.CameraPos)
		
		// Select LOD based on distance and layer
		lod := vm.getLODForDistance(distance, viewport.Layer, viewport.Precision)
		
		// Get or create LOD version
		result[i] = vm.getOrCreateLOD(obj, lod)
	}
	
	return result
}

// distanceToCamera calculates distance from object to camera
func (vm *ViewportManager) distanceToCamera(obj *arxobject.ArxObjectUnified, cameraPos arxobject.Point3D) float64 {
	dx := float64(obj.Geometry.Position.X - cameraPos.X)
	dy := float64(obj.Geometry.Position.Y - cameraPos.Y)
	dz := float64(obj.Geometry.Position.Z - cameraPos.Z)
	
	return math.Sqrt(dx*dx + dy*dy + dz*dz)
}

// getLODForDistance determines LOD level based on distance
func (vm *ViewportManager) getLODForDistance(distance float64, layer Layer, basePrecision Precision) Precision {
	// Convert distance to meters
	distMeters := distance / 1000.0
	
	// LOD thresholds in meters
	thresholds := []float64{
		1.0,     // < 1m: maximum precision
		5.0,     // 1-5m: high precision
		10.0,    // 5-10m: medium precision
		50.0,    // 10-50m: low precision
		100.0,   // 50-100m: very low precision
		500.0,   // 100-500m: minimal precision
	}
	
	// Find appropriate precision reduction
	reduction := 0
	for _, threshold := range thresholds {
		if distMeters < threshold {
			break
		}
		reduction++
	}
	
	// Apply reduction to base precision
	targetPrecision := int(basePrecision) - reduction
	if targetPrecision < 0 {
		targetPrecision = 0
	}
	
	// Cap by layer maximum
	maxForLayer := vm.getMaxPrecisionForLayer(layer)
	if Precision(targetPrecision) > maxForLayer {
		targetPrecision = int(maxForLayer)
	}
	
	return Precision(targetPrecision)
}

// getMaxPrecisionForLayer returns max precision for layer
func (vm *ViewportManager) getMaxPrecisionForLayer(layer Layer) Precision {
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

// getOrCreateLOD gets or creates an LOD version
func (vm *ViewportManager) getOrCreateLOD(obj *arxobject.ArxObjectUnified, precision Precision) *arxobject.ArxObjectUnified {
	cached, exists := vm.objectCache[obj.ID]
	if !exists {
		// No cache, return filtered version
		filter := NewDataFilter()
		return filter.FilterObject(obj, precision)
	}
	
	// Check if LOD exists
	if lod, exists := cached.LODs[precision]; exists {
		cached.LastAccess = getCurrentTimestamp()
		return lod
	}
	
	// Create new LOD
	filter := NewDataFilter()
	lod := filter.FilterObject(obj, precision)
	cached.LODs[precision] = lod
	cached.LastAccess = getCurrentTimestamp()
	
	return lod
}

// occlusionCull performs occlusion culling
func (vm *ViewportManager) occlusionCull(objects []*arxobject.ArxObjectUnified, viewport *ClientViewport) []*arxobject.ArxObjectUnified {
	// Sort by distance from camera
	sorted := make([]*arxobject.ArxObjectUnified, len(objects))
	copy(sorted, objects)
	
	sort.Slice(sorted, func(i, j int) bool {
		dist_i := vm.distanceToCamera(sorted[i], viewport.CameraPos)
		dist_j := vm.distanceToCamera(sorted[j], viewport.CameraPos)
		return dist_i < dist_j
	})
	
	// Simple occlusion: limit far objects when many are visible
	maxVisible := vm.getMaxVisibleForLayer(viewport.Layer)
	if len(sorted) > maxVisible {
		sorted = sorted[:maxVisible]
	}
	
	// TODO: Implement proper occlusion culling with depth buffer
	
	return sorted
}

// getMaxVisibleForLayer returns max visible objects for layer
func (vm *ViewportManager) getMaxVisibleForLayer(layer Layer) int {
	caps := GetLayerCapabilities(layer)
	return caps.MaxDataPoints
}

// CleanupCache removes old cached LODs
func (vm *ViewportManager) CleanupCache(maxAge int64) {
	vm.mu.Lock()
	defer vm.mu.Unlock()
	
	now := getCurrentTimestamp()
	
	for id, cached := range vm.objectCache {
		if now-cached.LastAccess > maxAge {
			delete(vm.objectCache, id)
		}
	}
}

// GetStats returns viewport statistics
func (vm *ViewportManager) GetStats() map[string]interface{} {
	vm.mu.RLock()
	defer vm.mu.RUnlock()
	
	totalLODs := 0
	for _, cached := range vm.objectCache {
		totalLODs += len(cached.LODs)
	}
	
	return map[string]interface{}{
		"active_viewports": len(vm.viewports),
		"cached_objects":   len(vm.objectCache),
		"cached_lods":      totalLODs,
		"octree_nodes":     vm.octree.NodeCount(),
	}
}

// Vector math helpers

func (vm *ViewportManager) cross(a, b Vector3) Vector3 {
	return Vector3{
		X: a.Y*b.Z - a.Z*b.Y,
		Y: a.Z*b.X - a.X*b.Z,
		Z: a.X*b.Y - a.Y*b.X,
	}
}

func (vm *ViewportManager) normalize(v Vector3) Vector3 {
	length := math.Sqrt(v.X*v.X + v.Y*v.Y + v.Z*v.Z)
	if length == 0 {
		return v
	}
	return Vector3{
		X: v.X / length,
		Y: v.Y / length,
		Z: v.Z / length,
	}
}

func (vm *ViewportManager) add(a, b Vector3) Vector3 {
	return Vector3{
		X: a.X + b.X,
		Y: a.Y + b.Y,
		Z: a.Z + b.Z,
	}
}

func (vm *ViewportManager) scale(v Vector3, s float64) Vector3 {
	return Vector3{
		X: v.X * s,
		Y: v.Y * s,
		Z: v.Z * s,
	}
}

// getCurrentTimestamp returns current Unix timestamp in milliseconds
func getCurrentTimestamp() int64 {
	return time.Now().UnixMilli()
}