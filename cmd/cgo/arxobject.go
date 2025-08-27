package cgo

// #cgo CFLAGS: -I. -O3
// #cgo LDFLAGS: -lm
// #include <stdlib.h>
// #include "arxobject_bridge.h"
import "C"
import (
	"encoding/json"
	"fmt"
	"runtime"
	"sync"
	"unsafe"
)

// ============================================================================
// Type Mappings
// ============================================================================

// ObjectType represents the type of ArxObject
type ObjectType int

const (
	TypeUnknown   ObjectType = C.ARX_TYPE_UNKNOWN
	TypeBuilding  ObjectType = C.ARX_TYPE_BUILDING
	TypeFloor     ObjectType = C.ARX_TYPE_FLOOR
	TypeRoom      ObjectType = C.ARX_TYPE_ROOM
	TypeWall      ObjectType = C.ARX_TYPE_WALL
	TypeDoor      ObjectType = C.ARX_TYPE_DOOR
	TypeWindow    ObjectType = C.ARX_TYPE_WINDOW
	TypeColumn    ObjectType = C.ARX_TYPE_COLUMN
	TypeBeam      ObjectType = C.ARX_TYPE_BEAM
	TypeSlab      ObjectType = C.ARX_TYPE_SLAB
	TypeRoof      ObjectType = C.ARX_TYPE_ROOF
	TypeStair     ObjectType = C.ARX_TYPE_STAIR
	TypeElevator  ObjectType = C.ARX_TYPE_ELEVATOR
	TypeEquipment ObjectType = C.ARX_TYPE_EQUIPMENT
	TypeFurniture ObjectType = C.ARX_TYPE_FURNITURE
	TypeFixture   ObjectType = C.ARX_TYPE_FIXTURE
	TypePipe      ObjectType = C.ARX_TYPE_PIPE
	TypeDuct      ObjectType = C.ARX_TYPE_DUCT
	TypeCable     ObjectType = C.ARX_TYPE_CABLE
	TypeSensor    ObjectType = C.ARX_TYPE_SENSOR
	TypeSystem    ObjectType = C.ARX_TYPE_SYSTEM
)

// Point3D represents a 3D point
type Point3D struct {
	X float64 `json:"x"`
	Y float64 `json:"y"`
	Z float64 `json:"z"`
}

// BoundingBox represents a 3D bounding box
type BoundingBox struct {
	Min Point3D `json:"min"`
	Max Point3D `json:"max"`
}

// ArxObject represents a building object
type ArxObject struct {
	ID           uint64                 `json:"id"`
	Name         string                 `json:"name"`
	Path         string                 `json:"path"`
	Type         ObjectType             `json:"type"`
	WorldX       int32                  `json:"world_x_mm"`
	WorldY       int32                  `json:"world_y_mm"`
	WorldZ       int32                  `json:"world_z_mm"`
	Width        int32                  `json:"width_mm"`
	Height       int32                  `json:"height_mm"`
	Depth        int32                  `json:"depth_mm"`
	ParentID     uint64                 `json:"parent_id,omitempty"`
	ChildIDs     []uint64               `json:"child_ids,omitempty"`
	Confidence   float32                `json:"confidence"`
	IsValidated  bool                   `json:"is_validated"`
	Properties   map[string]interface{} `json:"properties,omitempty"`
	Metadata     map[string]interface{} `json:"metadata,omitempty"`
}

// PerformanceStats represents system performance metrics
type PerformanceStats struct {
	TotalObjects     uint64  `json:"total_objects"`
	TotalQueries     uint64  `json:"total_queries"`
	AvgQueryTimeMS   float64 `json:"avg_query_time_ms"`
	AvgCreateTimeMS  float64 `json:"avg_create_time_ms"`
	AvgUpdateTimeMS  float64 `json:"avg_update_time_ms"`
	MemoryUsageBytes uint64  `json:"memory_usage_bytes"`
}

// ============================================================================
// Global State
// ============================================================================

var (
	initOnce sync.Once
	initErr  error
	mutex    sync.RWMutex
)

// ============================================================================
// Initialization
// ============================================================================

// Initialize initializes the ArxObject system
func Initialize(config map[string]interface{}) error {
	initOnce.Do(func() {
		configJSON, err := json.Marshal(config)
		if err != nil {
			initErr = fmt.Errorf("failed to marshal config: %w", err)
			return
		}

		cConfig := C.CString(string(configJSON))
		defer C.free(unsafe.Pointer(cConfig))

		result := C.arx_initialize(cConfig)
		defer freeResult(result)

		if !bool(result.success) {
			initErr = fmt.Errorf("initialization failed: %s", C.GoString(result.message))
		}
	})
	return initErr
}

// Cleanup cleans up the ArxObject system
func Cleanup() {
	mutex.Lock()
	defer mutex.Unlock()
	C.arx_cleanup()
}

// ============================================================================
// Object Operations
// ============================================================================

// CreateObject creates a new ArxObject
func CreateObject(name, path string, objType ObjectType, x, y, z int32) (*ArxObject, error) {
	mutex.Lock()
	defer mutex.Unlock()

	cName := C.CString(name)
	defer C.free(unsafe.Pointer(cName))
	
	cPath := C.CString(path)
	defer C.free(unsafe.Pointer(cPath))

	cObj := C.arx_object_create(
		cName,
		cPath,
		C.ArxObjectType(objType),
		C.int32_t(x),
		C.int32_t(y),
		C.int32_t(z),
	)

	if cObj == nil {
		return nil, fmt.Errorf("failed to create object: %s", GetLastError())
	}

	// Convert to Go struct
	obj := cObjectToGo(cObj)
	
	// Set finalizer to ensure C memory is freed
	runtime.SetFinalizer(obj, func(o *ArxObject) {
		// Note: Don't free here as object is stored in C list
	})

	return obj, nil
}

// GetObject retrieves an object by ID
func GetObject(id uint64) (*ArxObject, error) {
	mutex.RLock()
	defer mutex.RUnlock()

	cObj := C.arx_object_get(C.uint64_t(id))
	if cObj == nil {
		return nil, fmt.Errorf("object not found: %d", id)
	}

	return cObjectToGo(cObj), nil
}

// UpdateObject updates an existing object
func UpdateObject(obj *ArxObject) error {
	mutex.Lock()
	defer mutex.Unlock()

	cObj := goObjectToC(obj)
	defer C.arx_object_free(cObj)

	result := C.arx_object_update(cObj)
	defer freeResult(result)

	if !bool(result.success) {
		return fmt.Errorf("update failed: %s", C.GoString(result.message))
	}

	return nil
}

// DeleteObject deletes an object by ID
func DeleteObject(id uint64) error {
	mutex.Lock()
	defer mutex.Unlock()

	result := C.arx_object_delete(C.uint64_t(id))
	defer freeResult(result)

	if !bool(result.success) {
		return fmt.Errorf("delete failed: %s", C.GoString(result.message))
	}

	return nil
}

// ============================================================================
// Query Operations
// ============================================================================

// QueryByPath finds objects matching a path pattern
func QueryByPath(pathPattern string) ([]*ArxObject, error) {
	mutex.RLock()
	defer mutex.RUnlock()

	cPattern := C.CString(pathPattern)
	defer C.free(unsafe.Pointer(cPattern))

	result := C.arx_query_by_path(cPattern)
	defer C.arx_query_result_free(result)

	if result.error_message != nil {
		return nil, fmt.Errorf("query failed: %s", C.GoString(result.error_message))
	}

	return queryResultToGo(result), nil
}

// QueryByType finds objects of a specific type
func QueryByType(objType ObjectType) ([]*ArxObject, error) {
	mutex.RLock()
	defer mutex.RUnlock()

	result := C.arx_query_by_type(C.ArxObjectType(objType))
	defer C.arx_query_result_free(result)

	if result.error_message != nil {
		return nil, fmt.Errorf("query failed: %s", C.GoString(result.error_message))
	}

	return queryResultToGo(result), nil
}

// QueryByConfidence finds objects above a confidence threshold
func QueryByConfidence(minConfidence float32) ([]*ArxObject, error) {
	mutex.RLock()
	defer mutex.RUnlock()

	result := C.arx_query_by_confidence(C.float(minConfidence))
	defer C.arx_query_result_free(result)

	if result.error_message != nil {
		return nil, fmt.Errorf("query failed: %s", C.GoString(result.error_message))
	}

	return queryResultToGo(result), nil
}

// ============================================================================
// Spatial Operations
// ============================================================================

// CalculateDistance calculates distance between two objects
func CalculateDistance(id1, id2 uint64) (float64, error) {
	mutex.RLock()
	defer mutex.RUnlock()

	distance := C.arx_spatial_distance(C.uint64_t(id1), C.uint64_t(id2))
	if distance < 0 {
		return 0, fmt.Errorf("failed to calculate distance")
	}

	return float64(distance), nil
}

// CheckWithinBounds checks if an object is within bounds
func CheckWithinBounds(id uint64, bounds BoundingBox) bool {
	mutex.RLock()
	defer mutex.RUnlock()

	cBounds := C.ArxBoundingBox{
		min: C.ArxPoint3D{
			x: C.double(bounds.Min.X),
			y: C.double(bounds.Min.Y),
			z: C.double(bounds.Min.Z),
		},
		max: C.ArxPoint3D{
			x: C.double(bounds.Max.X),
			y: C.double(bounds.Max.Y),
			z: C.double(bounds.Max.Z),
		},
	}

	return bool(C.arx_spatial_within_bounds(C.uint64_t(id), &cBounds))
}

// ============================================================================
// ASCII Rendering
// ============================================================================

// RenderASCII2D renders objects as 2D ASCII art
func RenderASCII2D(objects []*ArxObject, width, height int) string {
	mutex.RLock()
	defer mutex.RUnlock()

	if len(objects) == 0 {
		return ""
	}

	// Convert objects to C array
	cObjects := make([]*C.ArxObject, len(objects))
	for i, obj := range objects {
		cObjects[i] = goObjectToC(obj)
		defer C.arx_object_free(cObjects[i])
	}

	// Call C function
	cResult := C.arx_ascii_render_2d(
		(**C.ArxObject)(unsafe.Pointer(&cObjects[0])),
		C.size_t(len(objects)),
		C.int(width),
		C.int(height),
	)
	defer C.free(unsafe.Pointer(cResult))

	return C.GoString(cResult)
}

// ============================================================================
// Performance Metrics
// ============================================================================

// GetPerformanceStats returns system performance statistics
func GetPerformanceStats() *PerformanceStats {
	mutex.RLock()
	defer mutex.RUnlock()

	cStats := C.arx_get_performance_stats()
	defer C.arx_performance_stats_free(cStats)

	return &PerformanceStats{
		TotalObjects:     uint64(cStats.total_objects),
		TotalQueries:     uint64(cStats.total_queries),
		AvgQueryTimeMS:   float64(cStats.avg_query_time_ms),
		AvgCreateTimeMS:  float64(cStats.avg_create_time_ms),
		AvgUpdateTimeMS:  float64(cStats.avg_update_time_ms),
		MemoryUsageBytes: uint64(cStats.memory_usage_bytes),
	}
}

// ============================================================================
// Utility Functions
// ============================================================================

// GetLastError returns the last error message from C
func GetLastError() string {
	return C.GoString(C.arx_get_last_error())
}

// SetLogLevel sets the logging level (0=none, 1=error, 2=warn, 3=info, 4=debug)
func SetLogLevel(level int) {
	C.arx_set_log_level(C.int(level))
}

// GetVersion returns the C library version
func GetVersion() string {
	return C.GoString(C.arx_get_version())
}

// ============================================================================
// Helper Functions
// ============================================================================

func cObjectToGo(cObj *C.ArxObject) *ArxObject {
	if cObj == nil {
		return nil
	}

	obj := &ArxObject{
		ID:          uint64(cObj.id),
		Name:        C.GoString(cObj.name),
		Path:        C.GoString(cObj.path),
		Type:        ObjectType(cObj.obj_type),
		WorldX:      int32(cObj.world_x_mm),
		WorldY:      int32(cObj.world_y_mm),
		WorldZ:      int32(cObj.world_z_mm),
		Width:       int32(cObj.width_mm),
		Height:      int32(cObj.height_mm),
		Depth:       int32(cObj.depth_mm),
		ParentID:    uint64(cObj.parent_id),
		Confidence:  float32(cObj.confidence),
		IsValidated: bool(cObj.is_validated),
	}

	// Parse JSON properties if present
	if cObj.properties_json != nil {
		propJSON := C.GoString(cObj.properties_json)
		if propJSON != "" {
			var props map[string]interface{}
			if err := json.Unmarshal([]byte(propJSON), &props); err == nil {
				obj.Properties = props
			}
		}
	}

	// Parse JSON metadata if present
	if cObj.metadata_json != nil {
		metaJSON := C.GoString(cObj.metadata_json)
		if metaJSON != "" {
			var meta map[string]interface{}
			if err := json.Unmarshal([]byte(metaJSON), &meta); err == nil {
				obj.Metadata = meta
			}
		}
	}

	return obj
}

func goObjectToC(obj *ArxObject) *C.ArxObject {
	if obj == nil {
		return nil
	}

	cObj := (*C.ArxObject)(C.calloc(1, C.sizeof_ArxObject))
	
	cObj.id = C.uint64_t(obj.ID)
	cObj.name = C.CString(obj.Name)
	cObj.path = C.CString(obj.Path)
	cObj.obj_type = C.ArxObjectType(obj.Type)
	cObj.world_x_mm = C.int32_t(obj.WorldX)
	cObj.world_y_mm = C.int32_t(obj.WorldY)
	cObj.world_z_mm = C.int32_t(obj.WorldZ)
	cObj.width_mm = C.int32_t(obj.Width)
	cObj.height_mm = C.int32_t(obj.Height)
	cObj.depth_mm = C.int32_t(obj.Depth)
	cObj.parent_id = C.uint64_t(obj.ParentID)
	cObj.confidence = C.float(obj.Confidence)
	cObj.is_validated = C.bool(obj.IsValidated)

	// Convert properties to JSON
	if obj.Properties != nil {
		if propJSON, err := json.Marshal(obj.Properties); err == nil {
			cObj.properties_json = C.CString(string(propJSON))
		}
	}

	// Convert metadata to JSON
	if obj.Metadata != nil {
		if metaJSON, err := json.Marshal(obj.Metadata); err == nil {
			cObj.metadata_json = C.CString(string(metaJSON))
		}
	}

	return cObj
}

func queryResultToGo(result *C.ArxQueryResult) []*ArxObject {
	if result == nil || result.count == 0 {
		return []*ArxObject{}
	}

	objects := make([]*ArxObject, int(result.count))
	
	// Convert C array to Go slice
	cObjects := (*[1 << 30]*C.ArxObject)(unsafe.Pointer(result.objects))[:result.count:result.count]
	
	for i := 0; i < int(result.count); i++ {
		objects[i] = cObjectToGo(cObjects[i])
	}

	return objects
}

func freeResult(result *C.ArxResult) {
	if result != nil {
		C.free(unsafe.Pointer(result.message))
		C.free(unsafe.Pointer(result))
	}
}