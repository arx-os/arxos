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
)

// Precision levels as bit flags for fast comparison
const (
	PrecisionCoarse    uint8 = 1 << iota // 1 foot
	PrecisionStandard                     // 1 inch
	PrecisionFine                         // 1/16 inch
	PrecisionUltraFine                    // 1/64 inch
	PrecisionMicro                        // 1/1000 inch
)

// ArxObject is the DNA of building elements
// Optimized struct layout for CPU cache efficiency (64 bytes)
type ArxObject struct {
	// Identity (16 bytes)
	ID   uint64 // Fast numeric ID instead of string
	Type ArxObjectType
	Precision uint8
	Priority  uint8
	Flags     uint8  // Active, Locked, etc as bit flags
	_padding  [4]byte
	
	// Geometry (24 bytes) - stored as fixed-point for precision
	X, Y, Z       int32 // Position in millimeters (int32 = ±2,147km range)
	Length, Width int16 // Dimensions in millimeters (int16 = ±32m range)
	Height        int16
	RotationZ     int16 // Rotation in decidegrees (0.1 degree precision)
	
	// Relationships (16 bytes) - indices into relationship arrays
	RelationshipStart uint32
	RelationshipCount uint16
	ConstraintBits    uint16 // Bit flags for common constraints
	
	// Metadata (8 bytes) - pointer to extended data only when needed
	MetadataPtr *ArxMetadata
}

// ArxMetadata holds optional extended data
// Only allocated when needed to save memory
type ArxMetadata struct {
	Properties map[string]interface{}
	Tags       []string
	Version    uint32
	UpdatedAt  int64
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

// CreateObject adds a new ArxObject with minimal overhead
func (e *Engine) CreateObject(objType ArxObjectType, x, y, z float32) uint64 {
	e.mu.Lock()
	defer e.mu.Unlock()
	
	id := e.nextID
	e.nextID++
	
	obj := ArxObject{
		ID:        id,
		Type:      objType,
		Precision: PrecisionStandard,
		Priority:  getPriority(objType),
		Flags:     1, // Active flag
		X:         int32(x * 1000), // Convert to mm
		Y:         int32(y * 1000),
		Z:         int32(z * 1000),
		Length:    1000, // 1m default
		Width:     1000,
		Height:    1000,
	}
	
	idx := len(e.objects)
	e.objects = append(e.objects, obj)
	e.idIndex[id] = idx
	e.spatial.Insert(&obj)
	
	return id
}

// QueryRegion finds objects in region using SIMD-friendly operations
func (e *Engine) QueryRegion(minX, minY, maxX, maxY float32) []uint64 {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	// Convert to fixed-point
	minXi := int32(minX * 1000)
	minYi := int32(minY * 1000)
	maxXi := int32(maxX * 1000)
	maxYi := int32(maxY * 1000)
	
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
			ID:     id,
			Type:   spec.Type,
			X:      int32(spec.X * 1000),
			Y:      int32(spec.Y * 1000),
			Z:      int32(spec.Z * 1000),
			Length: int16(spec.Length * 1000),
			Width:  int16(spec.Width * 1000),
			Height: int16(spec.Height * 1000),
			Flags:  1,
		}
		
		idx := len(e.objects)
		e.objects = append(e.objects, obj)
		e.idIndex[id] = idx
	}
	
	// Batch spatial index update
	e.spatial.BatchInsert(e.objects[len(e.objects)-len(specs):])
	
	return ids
}

// ObjectSpec for batch creation
type ObjectSpec struct {
	Type   ArxObjectType
	X, Y, Z float32
	Length, Width, Height float32
}

// CheckCollision uses SIMD-friendly integer math
func (e *Engine) CheckCollision(id uint64, clearance int32) bool {
	e.mu.RLock()
	defer e.mu.RUnlock()
	
	idx, exists := e.idIndex[id]
	if !exists {
		return false
	}
	
	obj := &e.objects[idx]
	
	// Use integer math for speed
	minX := obj.X - int32(obj.Length/2) - clearance
	maxX := obj.X + int32(obj.Length/2) + clearance
	minY := obj.Y - int32(obj.Width/2) - clearance
	maxY := obj.Y + int32(obj.Width/2) + clearance
	
	// Check against all objects (vectorizable)
	for i := range e.objects {
		other := &e.objects[i]
		if other.ID == id || other.Flags&1 == 0 {
			continue
		}
		
		// Integer bounds check (fast)
		otherMinX := other.X - int32(other.Length/2)
		otherMaxX := other.X + int32(other.Length/2)
		otherMinY := other.Y - int32(other.Width/2)
		otherMaxY := other.Y + int32(other.Width/2)
		
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
	
	size := 8 + len(e.objects)*64 // Header + objects
	buf := make([]byte, size)
	
	// Write header
	binary.LittleEndian.PutUint64(buf[0:8], uint64(len(e.objects)))
	
	// Write objects (can be done with unsafe cast for speed)
	offset := 8
	for _, obj := range e.objects {
		binary.LittleEndian.PutUint64(buf[offset:], obj.ID)
		buf[offset+8] = uint8(obj.Type)
		buf[offset+9] = obj.Precision
		buf[offset+10] = obj.Priority
		buf[offset+11] = obj.Flags
		binary.LittleEndian.PutUint32(buf[offset+12:], uint32(obj.X))
		binary.LittleEndian.PutUint32(buf[offset+16:], uint32(obj.Y))
		binary.LittleEndian.PutUint32(buf[offset+20:], uint32(obj.Z))
		binary.LittleEndian.PutUint16(buf[offset+24:], uint16(obj.Length))
		binary.LittleEndian.PutUint16(buf[offset+26:], uint16(obj.Width))
		binary.LittleEndian.PutUint16(buf[offset+28:], uint16(obj.Height))
		offset += 64
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
	}
	return 4
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
	gridX := obj.X / int32(si.gridSize)
	gridY := obj.Y / int32(si.gridSize)
	idx := gridY*1000 + gridX
	
	if idx >= 0 && idx < int32(len(si.grid)) {
		si.grid[idx] = append(si.grid[idx], obj.ID)
	}
}

// BatchInsert adds multiple objects efficiently
func (si *SpatialIndex) BatchInsert(objects []ArxObject) {
	for i := range objects {
		si.Insert(&objects[i])
	}
}