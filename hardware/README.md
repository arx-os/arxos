# ArxOS Hardware Platform

The ArxOS Hardware Platform provides a comprehensive ecosystem for managing IoT devices, edge computing, and building automation systems. It includes device templates, protocol translation, certification programs, and gateway management.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ArxOS Hardware Platform                  │
├─────────────────────────────────────────────────────────────┤
│  Platform Manager  │  Device Manager  │  Protocol Manager   │
├─────────────────────────────────────────────────────────────┤
│  Certification     │  Gateway Manager │  Template Library   │
├─────────────────────────────────────────────────────────────┤
│  ESP32 Templates   │  RP2040 Templates│  Gateway Templates  │
├─────────────────────────────────────────────────────────────┤
│  MQTT Protocol     │  Modbus Protocol │  BACnet Protocol    │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Directory Structure

```
hardware/
├── templates/                 # Device templates for TinyGo
│   ├── esp32/                # ESP32 microcontroller templates
│   │   └── sensor_template.go
│   ├── rp2040/               # RP2040 microcontroller templates
│   │   └── actuator_template.go
│   └── gateway/              # Gateway device templates
│       └── gateway_template.go
└── README.md                 # This file

internal/hardware/
├── platform/                 # Core platform management
│   └── platform.go
├── devices/                  # Device management
│   └── device.go
├── protocols/                # Protocol implementations
│   ├── protocol.go
│   ├── mqtt.go
│   └── modbus.go
└── certification/            # Device certification system
    └── certification.go
```

## 🚀 Features

### **Device Management**
- **Device Registration**: Register and manage IoT devices
- **Status Monitoring**: Real-time device status tracking
- **Command Execution**: Send commands to devices
- **Message Processing**: Handle device messages and telemetry

### **Protocol Translation**
- **MQTT Support**: Full MQTT 3.1.1 implementation
- **Modbus Support**: Modbus RTU and TCP protocols
- **BACnet Support**: Building automation protocol (planned)
- **Custom Protocols**: Extensible protocol framework

### **Device Templates**
- **ESP32 Templates**: Sensor and actuator templates for ESP32
- **RP2040 Templates**: Actuator templates for RP2040
- **Gateway Templates**: Protocol translation gateways
- **TinyGo Compatible**: All templates compile with TinyGo

### **Certification System**
- **Test Framework**: Comprehensive device testing
- **Standards Compliance**: Multiple certification standards
- **Performance Metrics**: Device performance tracking
- **Quality Assurance**: Automated quality checks

## 🔧 Getting Started

### **1. Platform Initialization**

```go
package main

import (
    "context"
    "github.com/arx-os/arxos/internal/hardware/platform"
    "github.com/arx-os/arxos/internal/hardware/devices"
    "github.com/arx-os/arxos/internal/hardware/protocols"
)

func main() {
    // Create platform manager
    platform := platform.NewPlatform()
    
    // Register protocols
    mqttProtocol := protocols.NewMQTTProtocol()
    platform.RegisterProtocol(mqttProtocol)
    
    modbusProtocol := protocols.NewModbusProtocol()
    platform.RegisterProtocol(modbusProtocol)
    
    // Create and register device
    device := &devices.Device{
        ID:        "SENSOR_001",
        Name:      "Temperature Sensor",
        Type:      devices.DeviceTypeSensor,
        Platform:  "esp32",
        GatewayID: "GATEWAY_001",
        Location:  "/B1/3/A/301/SENSORS/TEMP-01",
        Status:    devices.DeviceStatusOnline,
        Capabilities: []string{"temperature", "humidity"},
    }
    
    err := platform.RegisterDevice(context.Background(), device)
    if err != nil {
        log.Fatal(err)
    }
}
```

### **2. Device Communication**

```go
// Send command to device
command := map[string]interface{}{
    "type": "read_sensors",
    "interval": 30,
}

err := platform.SendMessage(ctx, "SENSOR_001", command)
if err != nil {
    log.Printf("Failed to send command: %v", err)
}

// Process device message
message := &devices.DeviceMessage{
    ID:        "msg_001",
    DeviceID:  "SENSOR_001",
    Type:      devices.MessageTypeData,
    Payload: map[string]interface{}{
        "temperature": 22.5,
        "humidity":    45.0,
    },
    Timestamp: time.Now(),
    Priority:  devices.MessagePriorityNormal,
}

err = platform.ProcessMessage(ctx, message)
if err != nil {
    log.Printf("Failed to process message: %v", err)
}
```

### **3. Protocol Configuration**

```go
// MQTT Configuration
mqttConfig := map[string]interface{}{
    "broker":     "192.168.1.100",
    "port":       1883,
    "client_id":  "arxos_gateway",
    "username":   "mqtt_user",
    "password":   "mqtt_pass",
    "qos":        1,
    "retain":     false,
}

err := platform.ConnectProtocol(ctx, "mqtt", mqttConfig)
if err != nil {
    log.Printf("Failed to connect MQTT: %v", err)
}

// Modbus Configuration
modbusConfig := map[string]interface{}{
    "type":      "tcp",
    "address":   "192.168.1.200",
    "port":      502,
    "timeout":   5,
}

err = platform.ConnectProtocol(ctx, "modbus", modbusConfig)
if err != nil {
    log.Printf("Failed to connect Modbus: %v", err)
}
```

## 📱 Device Templates

### **ESP32 Sensor Template**

The ESP32 sensor template provides a foundation for building sensor devices:

```go
// Key features:
- Temperature, humidity, pressure, light sensors
- WiFi connectivity
- MQTT communication
- Battery monitoring
- Heartbeat mechanism
- LED status indicators
```

**Compilation:**
```bash
tinygo build -target=esp32 -o sensor.bin hardware/templates/esp32/sensor_template.go
```

### **RP2040 Actuator Template**

The RP2040 actuator template provides a foundation for building actuator devices:

```go
// Key features:
- Relay control
- PWM output
- Button input
- Status LEDs
- WiFi connectivity
- MQTT communication
```

**Compilation:**
```bash
tinygo build -target=rp2040 -o actuator.uf2 hardware/templates/rp2040/actuator_template.go
```

### **Gateway Template**

The gateway template provides protocol translation capabilities:

```go
// Key features:
- Multiple protocol support (UART, SPI, I2C)
- Device discovery and management
- MQTT gateway functionality
- Status monitoring
- Command routing
```

## 🧪 Device Certification

### **Certification Process**

1. **Test Registration**: Register certification tests
2. **Device Testing**: Run tests on devices
3. **Result Analysis**: Analyze test results
4. **Certification**: Issue certification if passed

```go
// Register certification test
test := &certification.CertificationTest{
    ID:          "safety_basic",
    Name:        "Basic Safety Test",
    Description: "Basic electrical and fire safety compliance test",
    Category:    certification.TestCategorySafety,
    Standard:    "IEC 61010-1",
    Version:     "1.0",
}

err := certManager.RegisterTest(test)
if err != nil {
    log.Printf("Failed to register test: %v", err)
}

// Run test on device
result, err := certManager.RunTest(ctx, "DEVICE_001", "safety_basic")
if err != nil {
    log.Printf("Test failed: %v", err)
}

if result.Status == certification.TestStatusPassed {
    log.Printf("Device certified! Score: %.2f", result.Score)
}
```

### **Available Test Categories**

- **Safety**: Electrical and fire safety compliance
- **Performance**: Performance and throughput testing
- **Compatibility**: Protocol and hardware compatibility
- **Security**: Security and encryption testing
- **Reliability**: Uptime and error rate testing
- **Interoperability**: Standards compliance testing

## 📊 Monitoring and Metrics

### **Platform Metrics**

```go
metrics := platform.GetMetrics()
log.Printf("Total Devices: %d", metrics.TotalDevices)
log.Printf("Online Devices: %d", metrics.OnlineDevices)
log.Printf("Total Gateways: %d", metrics.TotalGateways)
log.Printf("Online Gateways: %d", metrics.OnlineGateways)
log.Printf("Messages Sent: %d", metrics.MessagesSent)
log.Printf("Messages Received: %d", metrics.MessagesReceived)
log.Printf("Errors: %d", metrics.Errors)
```

### **Device Metrics**

```go
deviceMetrics := deviceManager.GetMetrics()
log.Printf("Total Devices: %d", deviceMetrics.TotalDevices)
log.Printf("Online Devices: %d", deviceMetrics.OnlineDevices)
log.Printf("Offline Devices: %d", deviceMetrics.OfflineDevices)
log.Printf("Error Devices: %d", deviceMetrics.ErrorDevices)
log.Printf("Messages Received: %d", deviceMetrics.MessagesReceived)
log.Printf("Messages Sent: %d", deviceMetrics.MessagesSent)
log.Printf("Errors: %d", deviceMetrics.Errors)
```

## 🔌 Protocol Support

### **MQTT Protocol**

- **Version**: MQTT 3.1.1
- **Features**: Publish/Subscribe, QoS, Retain, Clean Session
- **Security**: Username/Password authentication
- **Topics**: Hierarchical topic structure

### **Modbus Protocol**

- **Types**: RTU and TCP
- **Functions**: Read/Write registers, Read/Write coils
- **Features**: Multiple slave support, error handling
- **Security**: IP-based access control

### **BACnet Protocol** (Planned)

- **Standard**: ANSI/ASHRAE 135-2016
- **Features**: Object discovery, property access
- **Security**: BACnet security profiles
- **Integration**: Building automation systems

## 🛠️ Development

### **Adding New Device Templates**

1. Create template file in appropriate directory
2. Implement required interfaces
3. Add TinyGo build tags
4. Test compilation with TinyGo
5. Update documentation

### **Adding New Protocols**

1. Implement `Protocol` interface
2. Add protocol-specific configuration
3. Register with protocol manager
4. Add unit tests
5. Update documentation

### **Adding New Certification Tests**

1. Create test implementation
2. Define test configuration
3. Register with certification manager
4. Add test validation
5. Update documentation

## 📚 Examples

### **Complete Device Management Example**

```go
package main

import (
    "context"
    "log"
    "time"
    
    "github.com/arx-os/arxos/internal/hardware/platform"
    "github.com/arx-os/arxos/internal/hardware/devices"
    "github.com/arx-os/arxos/internal/hardware/protocols"
)

func main() {
    // Initialize platform
    platform := platform.NewPlatform()
    
    // Register MQTT protocol
    mqtt := protocols.NewMQTTProtocol()
    platform.RegisterProtocol(mqtt)
    
    // Connect MQTT
    mqttConfig := map[string]interface{}{
        "broker": "localhost",
        "port":   1883,
    }
    
    ctx := context.Background()
    err := platform.ConnectProtocol(ctx, "mqtt", mqttConfig)
    if err != nil {
        log.Fatal(err)
    }
    
    // Create device
    device := &devices.Device{
        ID:        "TEMP_SENSOR_001",
        Name:      "Temperature Sensor",
        Type:      devices.DeviceTypeSensor,
        Platform:  "esp32",
        GatewayID: "GATEWAY_001",
        Location:  "/B1/3/A/301/SENSORS/TEMP-01",
        Status:    devices.DeviceStatusOnline,
        Capabilities: []string{"temperature", "humidity"},
    }
    
    // Register device
    err = platform.RegisterDevice(ctx, device)
    if err != nil {
        log.Fatal(err)
    }
    
    // Send command
    command := map[string]interface{}{
        "type": "read_sensors",
    }
    
    err = platform.SendMessage(ctx, "TEMP_SENSOR_001", command)
    if err != nil {
        log.Printf("Failed to send command: %v", err)
    }
    
    // Monitor device
    for {
        time.Sleep(30 * time.Second)
        
        device, err := platform.GetDevice("TEMP_SENSOR_001")
        if err != nil {
            log.Printf("Failed to get device: %v", err)
            continue
        }
        
        log.Printf("Device Status: %s", device.Status)
        log.Printf("Last Seen: %s", device.LastSeen)
    }
}
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Join our Discord community
- Check the documentation wiki

---

**ArxOS Hardware Platform** - Building the future of IoT and building automation! 🏗️✨
