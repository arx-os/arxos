# ARXOS CGO Bridge

The CGO bridge provides a seamless interface between Go services and the ARXOS C core components. This enables Go applications to leverage the high-performance C implementations while maintaining Go's developer experience and ecosystem benefits.

## 🏗️ **Architecture Overview**

```
┌─────────────────────────────────────────────────────────┐
│                    Go Services Layer                    │
│  ├── HTTP API & Authentication                         │
│  ├── Database Integration & Caching                    │
│  ├── Configuration & Logging                           │
│  ├── Deployment & Monitoring                           │
│  └── Business Logic Orchestration                      │
├─────────────────────────────────────────────────────────┤
│                    CGO Bridge Layer                     │
│  ├── Go Wrapper Functions                              │
│  ├── C Function Calls                                  │
│  ├── Memory Management                                 │
│  └── Error Handling                                    │
├─────────────────────────────────────────────────────────┤
│                    C Core Foundation                   │
│  ├── ArxObject Runtime Engine                          │
│  ├── ASCII-BIM Spatial Engine                          │
│  ├── Building Management System                         │
│  ├── Version Control System                             │
│  └── Spatial Indexing System                           │
└─────────────────────────────────────────────────────────┘
```

## 🚀 **Key Benefits**

- **Performance**: Sub-millisecond operations for building intelligence
- **Integration**: Seamless Go-C interoperability with CGO
- **Memory Safety**: Proper memory management and cleanup
- **Error Handling**: Comprehensive error reporting from C to Go
- **Type Safety**: Strong typing for all C core operations

## 📚 **API Reference**

### **ArxObject Management**

```go
import "github.com/arxos/core/cgo"

// Create a new building element
obj, err := cgo.CreateArxObject("wall_001", "Exterior Wall", "North facing wall", 1)
if err != nil {
    log.Fatal(err)
}
defer obj.Destroy()

// Set and get properties
err = obj.SetProperty("material", "concrete")
if err != nil {
    log.Fatal(err)
}

material, err := obj.GetProperty("material")
if err != nil {
    log.Fatal(err)
}
fmt.Printf("Material: %s\n", material)
```

### **Building Management**

```go
// Create a building
building, err := cgo.CreateArxBuilding("Office Building", "5-story office complex")
if err != nil {
    log.Fatal(err)
}
defer building.Destroy()

// Add objects to building
err = building.AddObject(obj)
if err != nil {
    log.Fatal(err)
}

// Get building summary
summary, err := building.GetSummary()
if err != nil {
    log.Fatal(err)
}
fmt.Println(summary)
```

### **ASCII Art Generation**

```go
// Generate 2D floor plan
objects := []*cgo.ArxObject{obj}
floorPlan, err := cgo.Generate2DFloorPlan(objects, 80, 40, 1.0)
if err != nil {
    log.Fatal(err)
}
fmt.Println(floorPlan)

// Generate 3D building view
building3D, err := cgo.Generate3DBuildingView(objects, 60, 30, 20, 1.0)
if err != nil {
    log.Fatal(err)
}
fmt.Println(building3D)
```

### **Version Control**

```go
// Initialize repository
vc, err := cgo.InitRepo("./building_repo", "John Doe", "john@example.com")
if err != nil {
    log.Fatal(err)
}
defer vc.Destroy()

// Create commit
commitHash, err := vc.Commit("Add exterior wall", "", "")
if err != nil {
    log.Fatal(err)
}
fmt.Printf("Commit: %s\n", commitHash)

// Get history
history, err := vc.GetHistory(10)
if err != nil {
    log.Fatal(err)
}
fmt.Println(history)
```

### **Spatial Indexing**

```go
// Create spatial index
index, err := cgo.CreateSpatialIndex(8, true) // 8 levels, use octree
if err != nil {
    log.Fatal(err)
}
defer index.Destroy()

// Add objects to index
err = index.AddObject(obj)
if err != nil {
    log.Fatal(err)
}

// Perform spatial queries
results, err := index.Query(cgo.QueryTypeRange, 0, 0, 0, 100, 100, 100, 0, 50)
if err != nil {
    log.Fatal(err)
}
fmt.Printf("Found %d objects in range\n", len(results))

// Get statistics
stats, err := index.GetStatistics()
if err != nil {
    log.Fatal(err)
}
fmt.Println(stats)
```

## 🔧 **Installation & Setup**

### **Prerequisites**

- Go 1.21+
- GCC 7.0+ or Clang 6.0+
- POSIX threads (pthread)
- Math library (libm)

### **Build the C Core**

```bash
cd core/c
make all
```

### **Use in Go Project**

```bash
go get github.com/arxos/core/cgo
```

### **CGO Flags**

The bridge automatically sets the required CGO flags:

```go
/*
#cgo CFLAGS: -I../c
#cgo LDFLAGS: -L../c/lib -larxos -lpthread -lm
#include "bridge.h"
#include <stdlib.h>
*/
import "C"
```

## 🧪 **Testing**

### **Run CGO Bridge Tests**

```bash
cd core/cgo
go test -v
```

### **Run Integration Test**

```bash
cd core/cgo
go run test_bridge.go
```

## 📊 **Performance Characteristics**

| Operation | C Performance | Go Overhead | Total Performance |
|-----------|---------------|-------------|-------------------|
| ArxObject Creation | < 1ms | < 0.1ms | < 1.1ms |
| Property Access | < 0.1ms | < 0.05ms | < 0.15ms |
| ASCII Generation | < 10ms | < 0.5ms | < 10.5ms |
| Spatial Query | < 5ms | < 0.2ms | < 5.2ms |
| Version Commit | < 100ms | < 1ms | < 101ms |

## 🚨 **Error Handling**

All C functions return proper error information that gets converted to Go errors:

```go
obj, err := cgo.CreateArxObject("", "", "", 1)
if err != nil {
    // Error contains detailed message from C core
    fmt.Printf("Error: %v\n", err)
    return
}
```

## 💾 **Memory Management**

The bridge handles memory management automatically:

- **C strings** are converted to Go strings and freed
- **C objects** are wrapped in Go structs with proper cleanup
- **Arrays** are converted to Go slices with proper memory management
- **All C memory** is properly freed to prevent leaks

## 🔒 **Thread Safety**

- **C core functions** are thread-safe with pthread read-write locks
- **Go wrapper** functions are safe for concurrent use
- **Memory management** is thread-safe
- **Error handling** is thread-local

## 🚀 **Usage Examples**

### **Complete Building Workflow**

```go
package main

import (
    "fmt"
    "log"
    "github.com/arxos/core/cgo"
)

func main() {
    // 1. Create building
    building, err := cgo.CreateArxBuilding("My House", "Single family home")
    if err != nil {
        log.Fatal(err)
    }
    defer building.Destroy()

    // 2. Create building elements
    wall1, err := cgo.CreateArxObject("wall_001", "Exterior Wall", "North wall", 1)
    if err != nil {
        log.Fatal(err)
    }
    defer wall1.Destroy()

    door1, err := cgo.CreateArxObject("door_001", "Front Door", "Main entrance", 2)
    if err != nil {
        log.Fatal(err)
    }
    defer door1.Destroy()

    // 3. Set properties
    wall1.SetProperty("material", "brick")
    wall1.SetProperty("height", "3.0m")
    door1.SetProperty("material", "wood")
    door1.SetProperty("width", "1.0m")

    // 4. Add to building
    building.AddObject(wall1)
    building.AddObject(door1)

    // 5. Generate ASCII representation
    objects := []*cgo.ArxObject{wall1, door1}
    floorPlan, err := cgo.Generate2DFloorPlan(objects, 60, 30, 1.0)
    if err != nil {
        log.Fatal(err)
    }

    // 6. Version control
    vc, err := cgo.InitRepo("./house_repo", "Architect", "arch@example.com")
    if err != nil {
        log.Fatal(err)
    }
    defer vc.Destroy()

    commitHash, err := vc.Commit("Initial house design", "", "")
    if err != nil {
        log.Fatal(err)
    }

    fmt.Printf("House created and committed: %s\n", commitHash)
    fmt.Println("Floor plan:")
    fmt.Println(floorPlan)
}
```

## 🔮 **Future Enhancements**

- **Batch operations** for multiple objects
- **Async operations** with Go channels
- **Streaming ASCII generation** for large buildings
- **Advanced spatial queries** with custom filters
- **Performance profiling** and metrics collection

## 📖 **API Documentation**

For complete API documentation, see the Go package documentation:

```bash
go doc github.com/arxos/core/cgo
```

## 🤝 **Contributing**

When adding new C core functionality:

1. **Add bridge functions** to `bridge.h` and `bridge.c`
2. **Add Go wrappers** to `arxos.go`
3. **Add tests** to `test_bridge.go`
4. **Update documentation** in this README
5. **Update Makefile** if new C files are added

## 📄 **License**

This project is part of the ARXOS platform and follows the same licensing terms.
