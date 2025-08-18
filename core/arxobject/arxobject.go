// Package arxobject provides the core DNA structure for building elements
// Optimized for speed and minimal memory footprint
package arxobject

import (
	"encoding/binary"
	"sync"
	"time"
)

// ArxObjectType represents building system types as uint8 for efficiency
type ArxObjectType uint8

const (
	// Structural System (Priority 1)
	StructuralBeam ArxObjectType = iota
	StructuralColumn
	StructuralWall
	StructuralSlab
	StructuralFoundation
	
	// Life Safety (Priority 2)
	FireSprinkler
	FireAlarm
	EmergencyExit
	SmokeDetector
	
	// MEP Systems (Priority 3)
	ElectricalOutlet
	ElectricalPanel
	ElectricalConduit
	HVACDuct
	HVACUnit
	PlumbingPipe
	PlumbingFixture
	
	// Hardware/IoT Systems (Priority 4)
	NetworkSwitch
	NetworkPort
	PLCController
	IOModule
	Sensor
	Actuator
	
	// Circuit/Manufacturing Level (Priority 5)
	PCBBoard
	ICChip
	Pin
	Trace
	Component
)

// Precision levels as bit flags for fast comparison
const (
	PrecisionCoarse    uint8 = 1 << iota // 1 foot
	PrecisionStandard                     // 1 inch
	PrecisionFine                         // 1/16 inch
	PrecisionUltraFine                    // 1/64 inch
	PrecisionMicro                        // 1/1000 inch
)

// Unit conversion constants for nanometer-based coordinates
const (
	// Base unit is nanometer (1 nm = 10^-9 m)
	Nanometer  int64 = 1
	Micrometer int64 = 1000              // 1 μm = 1000 nm
	Millimeter int64 = 1000000           // 1 mm = 1,000,000 nm
	Centimeter int64 = 10000000          // 1 cm = 10,000,000 nm
	Meter      int64 = 1000000000        // 1 m = 1,000,000,000 nm
	Kilometer  int64 = 1000000000000     // 1 km = 10^12 nm
	
	// Imperial units
	Inch       int64 = 25400000          // 1 in = 25.4 mm = 25,400,000 nm
	Foot       int64 = 304800000         // 1 ft = 304.8 mm = 304,800,000 nm
	Yard       int64 = 914400000         // 1 yd = 914.4 mm
	Mile       int64 = 1609344000000     // 1 mi = 1.609344 km
	
	// PCB/Manufacturing units
	Mil        int64 = 25400             // 1 mil = 0.001 inch = 25.4 μm
	Micron     int64 = 1000              // Common in PCB manufacturing
)

// ArxObject is the DNA of building elements
// Optimized for the full scale range: campus to circuit traces
// Now with confidence scoring for AI-driven intelligence
type ArxObject struct {
	// Identity (16 bytes)
	ID   uint64 // Fast numeric ID instead of string
	Type ArxObjectType
	Precision uint8
	Priority  uint8
	Flags     uint8  // Active, Locked, etc as bit flags
	ScaleLevel uint8 // Scale level for rendering optimization
	_padding  [4]byte
	
	// Geometry (48 bytes) - stored in nanometers for universal precision
	X, Y, Z       int64 // Position in nanometers (int64 = ±9,223,372km range, 1nm precision)
	Length, Width int64 // Dimensions in nanometers (handles mm to nm scale)
	Height        int64
	RotationZ     int32 // Rotation in millidegrees (0.001 degree precision)
	_padding2     [4]byte
	
	// Relationships (16 bytes) - indices into relationship arrays
	RelationshipStart uint32
	RelationshipCount uint16
	ConstraintBits    uint16 // Bit flags for common constraints
	
	// Confidence (40 bytes) - AI confidence scoring
	Confidence ConfidenceScore
	
	// Validation (16 bytes) - validation tracking
	ValidationState uint8 // 0=pending, 1=partial, 2=complete, 3=conflict
	_padding3       [7]byte
	ValidatedAt     int64 // Unix timestamp
	
	// Metadata (8 bytes) - pointer to extended data only when needed
	MetadataPtr *ArxMetadata
}

// ConfidenceScore represents multi-dimensional confidence for AI-driven intelligence
type ConfidenceScore struct {
	Classification float32 // How certain about object type (0-1)
	Position       float32 // Spatial accuracy confidence (0-1)
	Properties     float32 // Data accuracy confidence (0-1)
	Relationships  float32 // Connection validity (0-1)
	Overall        float32 // Weighted average (0-1)
}

// NewConfidenceScore creates a confidence score with automatic overall calculation
func NewConfidenceScore(classification, position, properties, relationships float32) ConfidenceScore {
	cs := ConfidenceScore{
		Classification: clamp32(classification, 0, 1),
		Position:       clamp32(position, 0, 1),
		Properties:     clamp32(properties, 0, 1),
		Relationships:  clamp32(relationships, 0, 1),
	}
	cs.CalculateOverall()
	return cs
}

// CalculateOverall computes weighted average of confidence dimensions
func (cs *ConfidenceScore) CalculateOverall() {
	cs.Overall = cs.Classification*0.35 +
		cs.Position*0.30 +
		cs.Properties*0.20 +
		cs.Relationships*0.15
	cs.Overall = clamp32(cs.Overall, 0, 1)
}

// IsHighConfidence returns true if overall confidence > 0.85
func (cs *ConfidenceScore) IsHighConfidence() bool {
	return cs.Overall > 0.85
}

// IsLowConfidence returns true if overall confidence < 0.6
func (cs *ConfidenceScore) IsLowConfidence() bool {
	return cs.Overall < 0.6
}

// ArxMetadata holds optional extended data
// Only allocated when needed to save memory
type ArxMetadata struct {
	Properties   map[string]interface{}
	Tags         []string
	Version      uint32
	UpdatedAt    int64
	Source       string // pdf, field, inference, etc.
	ValidatedBy  string // Who validated this object
}

// SpatialIndex uses a flat quadtree for cache-efficient queries
type SpatialIndex struct {
	mu       sync.RWMutex
	grid     [][]uint64 // 2D grid of object IDs
	gridSize int        // Grid resolution
	objects  []ArxObject // Flat array for cache locality
}

// Engine provides high-performance ArxObject operations
type Engine struct {
	objects      []ArxObject      // Primary storage - flat array
	spatial      *SpatialIndex    // Spatial indexing
	relationships []Relationship   // Flat relationship array
	idIndex      map[uint64]int   // ID to array index lookup
	nextID       uint64
	mu           sync.RWMutex
}

// Relationship stored separately for memory efficiency
type Relationship struct {
	SourceID uint64
	TargetID uint64
	Type     uint8
}

// NewEngine creates an optimized ArxObject engine
func NewEngine(capacity int) *Engine {
	return &Engine{
		objects:  make([]ArxObject, 0, capacity),
		idIndex:  make(map[uint64]int, capacity),
		spatial:  NewSpatialIndex(1000), // 1m grid cells
	}
}

// CreateObject adds a new ArxObject with minimal overhead and default confidence
// x, y, z are in meters by default for backward compatibility
func (e *Engine) CreateObject(objType ArxObjectType, x, y, z float32) uint64 {
	e.mu.Lock()
	defer e.mu.Unlock()
	
	id := e.nextID
	e.nextID++
	
	obj := ArxObject{
		ID:         id,
		Type:       objType,
		Precision:  PrecisionStandard,
		Priority:   getPriority(objType),
		Flags:      1, // Active flag
		ScaleLevel: getScaleLevel(objType),
		X:          int64(x * float32(Meter)), // Convert meters to nanometers
		Y:          int64(y * float32(Meter)),
		Z:          int64(z * float32(Meter)),
		Length:     Meter, // 1m default in nanometers
		Width:      Meter,
		Height:     Meter,
		// Default confidence for manually created objects
		Confidence: NewConfidenceScore(0.5, 0.7, 0.5, 0.3),
		ValidationState: 0, // Pending
	}
	
	idx := len(e.objects)
	e.objects = append(e.objects, obj)
	e.idIndex[id] = idx
	e.spatial.Insert(&obj)
	
	return id
}

// CreateObjectWithConfidence adds a new ArxObject with specified confidence
func (e *Engine) CreateObjectWithConfidence(objType ArxObjectType, x, y, z float32, confidence ConfidenceScore) uint64 {
	e.mu.Lock()
	defer e.mu.Unlock()
	
	id := e.nextID
	e.nextID++
	
	obj := ArxObject{
		ID:         id,
		Type:       objType,
		Precision:  PrecisionStandard,
		Priority:   getPriority(objType),
		Flags:      1, // Active flag
		ScaleLevel: getScaleLevel(objType),
		X:          int64(x * float32(Meter)),
		Y:          int64(y * float32(Meter)),
		Z:          int64(z * float32(Meter)),
		Length:     Meter,
		Width:      Meter,
		Height:     Meter,
		Confidence: confidence,
		ValidationState: 0, // Pending
	}
	
	idx := len(e.objects)
	e.objects = append(e.objects, obj)
	e.idIndex[id] = idx
	e.spatial.Insert(&obj)
	
	return id
}

// CreateObjectNano adds a new ArxObject with nanometer precision
func (e *Engine) CreateObjectNano(objType ArxObjectType, x, y, z int64) uint64 {
	e.mu.Lock()
	defer e.mu.Unlock()
	
	id := e.nextID
	e.nextID++
	
	obj := ArxObject{
		ID:         id,
		Type:       objType,
		Precision:  PrecisionMicro,
		Priority:   getPriority(objType),
		Flags:      1, // Active flag
		ScaleLevel: getScaleLevel(objType),
		X:          x,
		Y:          y,
		Z:          z,
		Length:     getDefaultSize(objType),
		Width:      getDefaultSize(objType),
		Height:     getDefaultSize(objType),
	}
	
	idx := len(e.objects)
	e.objects = append(e.objects, obj)
	e.idIndex[id] = idx
	e.spatial.Insert(&obj)
	
	return id
}

// QueryRegion finds objects in region using SIMD-friendly operations
// minX, minY, maxX, maxY are in meters for backward compatibility
func (e *Engine) QueryRegion(minX, minY, maxX, maxY float32) []uint64 {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	// Convert meters to nanometers
	minXi := int64(minX * float32(Meter))
	minYi := int64(minY * float32(Meter))
	maxXi := int64(maxX * float32(Meter))
	maxYi := int64(maxY * float32(Meter))
	
	result := make([]uint64, 0, 100)
	
	// Vectorizable loop - compiler can optimize this
	for i := range e.objects {
		obj := &e.objects[i]
		if obj.Flags&1 == 0 { // Skip inactive
			continue
		}
		
		// Branch-free bounds check
		inBounds := (obj.X >= minXi) && (obj.X <= maxXi) &&
		           (obj.Y >= minYi) && (obj.Y <= maxYi)
		
		if inBounds {
			result = append(result, obj.ID)
		}
	}
	
	return result
}

// QueryRegionNano finds objects in region with nanometer precision
func (e *Engine) QueryRegionNano(minX, minY, maxX, maxY int64) []uint64 {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	result := make([]uint64, 0, 100)
	
	for i := range e.objects {
		obj := &e.objects[i]
		if obj.Flags&1 == 0 { // Skip inactive
			continue
		}
		
		// Branch-free bounds check
		inBounds := (obj.X >= minX) && (obj.X <= maxX) &&
		           (obj.Y >= minY) && (obj.Y <= maxY)
		
		if inBounds {
			result = append(result, obj.ID)
		}
	}
	
	return result
}

// GetObject retrieves by ID with O(1) lookup
func (e *Engine) GetObject(id uint64) (*ArxObject, bool) {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	idx, exists := e.idIndex[id]
	if !exists {
		return nil, false
	}
	
	return &e.objects[idx], true
}

// BatchCreate creates multiple objects efficiently
func (e *Engine) BatchCreate(specs []ObjectSpec) []uint64 {
	e.mu.Lock()
	defer e.mu.Unlock()
	
	// Pre-allocate space
	newCount := len(e.objects) + len(specs)
	if cap(e.objects) < newCount {
		newObjects := make([]ArxObject, len(e.objects), newCount*2)
		copy(newObjects, e.objects)
		e.objects = newObjects
	}
	
	ids := make([]uint64, len(specs))
	
	for i, spec := range specs {
		id := e.nextID
		e.nextID++
		ids[i] = id
		
		obj := ArxObject{
			ID:         id,
			Type:       spec.Type,
			ScaleLevel: getScaleLevel(spec.Type),
			X:          int64(spec.X * float32(Meter)),
			Y:          int64(spec.Y * float32(Meter)),
			Z:          int64(spec.Z * float32(Meter)),
			Length:     int64(spec.Length * float32(Meter)),
			Width:      int64(spec.Width * float32(Meter)),
			Height:     int64(spec.Height * float32(Meter)),
			Flags:      1,
		}
		
		idx := len(e.objects)
		e.objects = append(e.objects, obj)
		e.idIndex[id] = idx
	}
	
	// Batch spatial index update
	e.spatial.BatchInsert(e.objects[len(e.objects)-len(specs):])
	
	return ids
}

// ObjectSpec for batch creation (meters for backward compatibility)
type ObjectSpec struct {
	Type   ArxObjectType
	X, Y, Z float32
	Length, Width, Height float32
}

// ObjectSpecNano for batch creation with nanometer precision
type ObjectSpecNano struct {
	Type   ArxObjectType
	X, Y, Z int64
	Length, Width, Height int64
}

// CheckCollision uses SIMD-friendly integer math
// clearance is in millimeters for backward compatibility
func (e *Engine) CheckCollision(id uint64, clearance int32) bool {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	idx, exists := e.idIndex[id]
	if !exists {
		return false
	}
	
	obj := &e.objects[idx]
	clearanceNano := int64(clearance) * Millimeter
	
	// Use integer math for speed
	minX := obj.X - obj.Length/2 - clearanceNano
	maxX := obj.X + obj.Length/2 + clearanceNano
	minY := obj.Y - obj.Width/2 - clearanceNano
	maxY := obj.Y + obj.Width/2 + clearanceNano
	
	// Check against all objects (vectorizable)
	for i := range e.objects {
		other := &e.objects[i]
		if other.ID == id || other.Flags&1 == 0 {
			continue
		}
		
		// Integer bounds check (fast)
		otherMinX := other.X - other.Length/2
		otherMaxX := other.X + other.Length/2
		otherMinY := other.Y - other.Width/2
		otherMaxY := other.Y + other.Width/2
		
		// Branch-free overlap detection
		overlapX := minX < otherMaxX && maxX > otherMinX
		overlapY := minY < otherMaxY && maxY > otherMinY
		
		if overlapX && overlapY {
			return true
		}
	}
	
	return false
}

// Serialize to binary for ultra-fast save/load
func (e *Engine) Serialize() []byte {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	// Updated size for int64 coordinates
	size := 8 + len(e.objects)*96 // Header + objects (96 bytes per object)
	buf := make([]byte, size)
	
	// Write header
	binary.LittleEndian.PutUint64(buf[0:8], uint64(len(e.objects)))
	
	// Write objects
	offset := 8
	for _, obj := range e.objects {
		binary.LittleEndian.PutUint64(buf[offset:], obj.ID)
		buf[offset+8] = uint8(obj.Type)
		buf[offset+9] = obj.Precision
		buf[offset+10] = obj.Priority
		buf[offset+11] = obj.Flags
		buf[offset+12] = obj.ScaleLevel
		// 3 bytes padding
		
		// Write int64 coordinates (24 bytes)
		binary.LittleEndian.PutUint64(buf[offset+16:], uint64(obj.X))
		binary.LittleEndian.PutUint64(buf[offset+24:], uint64(obj.Y))
		binary.LittleEndian.PutUint64(buf[offset+32:], uint64(obj.Z))
		
		// Write int64 dimensions (24 bytes)
		binary.LittleEndian.PutUint64(buf[offset+40:], uint64(obj.Length))
		binary.LittleEndian.PutUint64(buf[offset+48:], uint64(obj.Width))
		binary.LittleEndian.PutUint64(buf[offset+56:], uint64(obj.Height))
		
		// Write rotation (4 bytes)
		binary.LittleEndian.PutUint32(buf[offset+64:], uint32(obj.RotationZ))
		
		// Write relationships (8 bytes)
		binary.LittleEndian.PutUint32(buf[offset+68:], obj.RelationshipStart)
		binary.LittleEndian.PutUint16(buf[offset+72:], obj.RelationshipCount)
		binary.LittleEndian.PutUint16(buf[offset+74:], obj.ConstraintBits)
		
		offset += 96
	}
	
	return buf
}

func getPriority(t ArxObjectType) uint8 {
	if t <= StructuralFoundation {
		return 1
	} else if t <= SmokeDetector {
		return 2
	} else if t <= PlumbingFixture {
		return 3
	} else if t <= Actuator {
		return 4
	} else if t <= Component {
		return 5
	}
	return 6
}

func getScaleLevel(t ArxObjectType) uint8 {
	switch {
	case t <= StructuralFoundation:
		return 3 // Building scale
	case t <= PlumbingFixture:
		return 2 // Floor/Room scale
	case t <= Actuator:
		return 1 // Component scale
	case t <= Component:
		return 0 // Circuit scale
	default:
		return 2
	}
}

func getDefaultSize(t ArxObjectType) int64 {
	switch {
	case t <= StructuralFoundation:
		return Meter // 1m default for structural
	case t <= PlumbingFixture:
		return 100 * Millimeter // 100mm for MEP
	case t <= Actuator:
		return 50 * Millimeter // 50mm for IoT devices
	case t == PCBBoard:
		return 100 * Millimeter // 100mm PCB
	case t == ICChip:
		return 10 * Millimeter // 10mm chip
	case t == Trace:
		return 100 * Micrometer // 100 micron trace
	default:
		return Meter
	}
}

// NewSpatialIndex creates a grid-based spatial index
func NewSpatialIndex(gridSize int) *SpatialIndex {
	return &SpatialIndex{
		gridSize: gridSize,
		grid:     make([][]uint64, 1000), // 1000x1000 grid
	}
}

// Insert adds object to spatial index
func (si *SpatialIndex) Insert(obj *ArxObject) {
	// Convert nanometers to grid cells (gridSize is in millimeters)
	gridX := obj.X / (int64(si.gridSize) * Millimeter)
	gridY := obj.Y / (int64(si.gridSize) * Millimeter)
	idx := gridY*1000 + gridX
	
	if idx >= 0 && idx < int64(len(si.grid)) {
		si.grid[idx] = append(si.grid[idx], obj.ID)
	}
}

// BatchInsert adds multiple objects efficiently
func (si *SpatialIndex) BatchInsert(objects []ArxObject) {
	for i := range objects {
		si.Insert(&objects[i])
	}
}

// Convenience methods for ArxObject unit conversions

// GetPositionMeters returns position in meters
func (a *ArxObject) GetPositionMeters() (x, y, z float64) {
	return float64(a.X) / float64(Meter),
		float64(a.Y) / float64(Meter),
		float64(a.Z) / float64(Meter)
}

// GetPositionMillimeters returns position in millimeters
func (a *ArxObject) GetPositionMillimeters() (x, y, z float64) {
	return float64(a.X) / float64(Millimeter),
		float64(a.Y) / float64(Millimeter),
		float64(a.Z) / float64(Millimeter)
}

// GetPositionMicrometers returns position in micrometers
func (a *ArxObject) GetPositionMicrometers() (x, y, z float64) {
	return float64(a.X) / float64(Micrometer),
		float64(a.Y) / float64(Micrometer),
		float64(a.Z) / float64(Micrometer)
}

// GetDimensionsMeters returns dimensions in meters
func (a *ArxObject) GetDimensionsMeters() (length, width, height float64) {
	return float64(a.Length) / float64(Meter),
		float64(a.Width) / float64(Meter),
		float64(a.Height) / float64(Meter)
}

// GetDimensionsMillimeters returns dimensions in millimeters
func (a *ArxObject) GetDimensionsMillimeters() (length, width, height float64) {
	return float64(a.Length) / float64(Millimeter),
		float64(a.Width) / float64(Millimeter),
		float64(a.Height) / float64(Millimeter)
}

// SetPositionMeters sets position from meters
func (a *ArxObject) SetPositionMeters(x, y, z float64) {
	a.X = int64(x * float64(Meter))
	a.Y = int64(y * float64(Meter))
	a.Z = int64(z * float64(Meter))
}

// SetPositionMillimeters sets position from millimeters
func (a *ArxObject) SetPositionMillimeters(x, y, z float64) {
	a.X = int64(x * float64(Millimeter))
	a.Y = int64(y * float64(Millimeter))
	a.Z = int64(z * float64(Millimeter))
}

// SetPositionMicrometers sets position from micrometers
func (a *ArxObject) SetPositionMicrometers(x, y, z float64) {
	a.X = int64(x * float64(Micrometer))
	a.Y = int64(y * float64(Micrometer))
	a.Z = int64(z * float64(Micrometer))
}

// Validate marks the object as validated and improves confidence
func (a *ArxObject) Validate(validator string, measurementConfidence float32) {
	a.ValidationState = 2 // Complete
	a.ValidatedAt = time.Now().Unix()
	
	// Improve confidence scores
	a.Confidence.Classification = clamp32(a.Confidence.Classification+0.2, 0, 1)
	a.Confidence.Position = clamp32(a.Confidence.Position*0.5+measurementConfidence*0.5, 0, 1)
	a.Confidence.Properties = clamp32(a.Confidence.Properties+0.15, 0, 1)
	
	// Recalculate overall
	a.Confidence.CalculateOverall()
	
	// Update metadata if present
	if a.MetadataPtr != nil {
		a.MetadataPtr.ValidatedBy = validator
		a.MetadataPtr.UpdatedAt = time.Now().Unix()
	}
}

// GetConfidenceLevel returns a string representation of confidence level
func (a *ArxObject) GetConfidenceLevel() string {
	if a.Confidence.IsHighConfidence() {
		return "high"
	} else if a.Confidence.IsLowConfidence() {
		return "low"
	}
	return "medium"
}

// NeedsValidation returns true if object needs field validation
func (a *ArxObject) NeedsValidation() bool {
	return a.ValidationState == 0 || a.Confidence.IsLowConfidence()
}

// clamp32 clamps a float32 value between min and max
func clamp32(value, min, max float32) float32 {
	if value < min {
		return min
	}
	if value > max {
		return max
	}
	return value
}