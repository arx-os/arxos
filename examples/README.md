# Arxos Examples

## Learn by Building

This directory contains example code and projects to get you started with Arxos.

### Examples

#### 1. Basic Node (`basic_node/`)
Simple ESP32 node that joins the mesh and sends heartbeats.

#### 2. Outlet Controller (`outlet_controller/`)
Control and monitor an electrical outlet, earning BILT tokens.

#### 3. Temperature Sensor (`temp_sensor/`)
Read temperature/humidity and report to mesh network.

#### 4. Terminal Client (`terminal_client/`)
Connect to mesh network from a PC and view building data.

#### 5. Mobile Scanner (`mobile_scanner/`)
Use phone + Bluetooth LE to scan and map buildings.

### Quick Start

```bash
# Run the terminal example
cd examples/terminal_client
cargo run

# Flash ESP32 example
cd examples/basic_node
pio run -t upload
```

### Learning Path

1. **Start Here** → `basic_node/` - Understand mesh basics
2. **Add Sensors** → `temp_sensor/` - Read real data
3. **Control Things** → `outlet_controller/` - Actuate devices
4. **Visualize** → `terminal_client/` - See your building
5. **Go Mobile** → `mobile_scanner/` - Map new areas

### BILT Rewards

Complete these examples to earn BILT:
- Basic Node: 50 BILT
- First Sensor: 100 BILT
- First Control: 150 BILT
- Terminal View: 200 BILT
- Mobile Scan: 500 BILT

### Community Examples

Share your examples! Best examples each month earn bonus BILT.

---

*"Learning by doing, earning while learning"* 🎓