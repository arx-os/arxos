# Bluetooth Mesh Bridge Implementation
**Version:** 1.0  
**Date:** August 31, 2025  
**Component:** ESP32 BLE to LoRa Bridge

## Overview

The Bluetooth Mesh Bridge enables mobile devices to access the Arxos building network using their built-in Bluetooth capabilities. Every ESP32 node in the building can act as a bridge, providing redundant access points throughout the facility.

## Architecture

### Network Topology

```
Mobile Devices (Multiple)
     │ │ │
     ▼ ▼ ▼
   BLE 5.0
     │ │ │
┌────┴─┴─┴────────────────────────────────────┐
│          ESP32 Node (Bridge Mode)           │
│  ┌────────────┐      ┌──────────────────┐  │
│  │  BLE Stack │◄────►│  Bridge Logic    │  │
│  │  (Client)  │      │  (Translation)   │  │
│  └────────────┘      └────────┬─────────┘  │
│                              │              │
│  ┌────────────┐      ┌───────▼──────────┐  │
│  │ LoRa Radio │◄────►│  Mesh Protocol   │  │
│  │  (SX1262)  │      │  (ArxObjects)    │  │
│  └────────────┘      └──────────────────┘  │
└──────────────────────────────────────────────┘
                       │
                       ▼
              Building Mesh Network
```

### ESP32 Resource Allocation

```
ESP32-S3 Resources:
┌─────────────────────────────────┐
│ Core 0 (Protocol Core)          │
│ - BLE Stack                     │
│ - Connection management         │
│ - Security/Encryption           │
│ - 40% CPU typical               │
├─────────────────────────────────┤
│ Core 1 (Application Core)       │
│ - Bridge translation            │
│ - LoRa packet handling          │
│ - Command processing            │
│ - 30% CPU typical               │
├─────────────────────────────────┤
│ Memory (8MB PSRAM)              │
│ - BLE buffers: 256KB            │
│ - Bridge cache: 512KB           │
│ - LoRa queues: 128KB            │
│ - Free: 7.1MB                   │
└─────────────────────────────────┘
```

## BLE Service Definition

### GATT Services and Characteristics

```yaml
# Primary Service: Arxos Mesh Bridge
Service UUID: 6E400001-B5A3-F393-E0A9-E50E24DCCA9E

Characteristics:
  - TX Characteristic (Mobile → Building)
    UUID: 6E400002-B5A3-F393-E0A9-E50E24DCCA9E
    Properties: WRITE, WRITE_WITHOUT_RESPONSE
    Max Length: 512 bytes
    Purpose: Send commands to building
    
  - RX Characteristic (Building → Mobile)
    UUID: 6E400003-B5A3-F393-E0A9-E50E24DCCA9E
    Properties: NOTIFY
    Max Length: 512 bytes
    Purpose: Receive responses from building
    
  - Status Characteristic
    UUID: 6E400004-B5A3-F393-E0A9-E50E24DCCA9E
    Properties: READ, NOTIFY
    Length: 16 bytes
    Purpose: Connection status and metrics
    
  - Control Characteristic
    UUID: 6E400005-B5A3-F393-E0A9-E50E24DCCA9E
    Properties: WRITE
    Length: 8 bytes
    Purpose: Connection control and config
```

### Advertisement Data

```c
// BLE Advertisement packet structure
typedef struct {
    uint8_t flags;           // 0x06 = General + BR/EDR not supported
    uint8_t length_type;     // 0x09 = Complete local name
    char name[14];           // "Arxos-XXXX" where XXXX is node ID
    uint8_t service_uuid[16]; // 128-bit service UUID
    uint8_t tx_power;        // Transmit power level
    uint8_t mesh_status;     // Custom data: mesh connectivity
} __attribute__((packed)) AdvPacket;

// Advertisement interval: 100ms (fast) or 1000ms (slow)
// TX Power: +4dBm for ~100m range
// Scannable: Yes (for extended info)
```

## Implementation Code

### ESP32 Firmware (Rust)

```rust
// src/firmware/esp32/ble_bridge.rs

use esp_idf_hal::prelude::*;
use esp_idf_svc::bt::{BleGatts, BleGap, BleAdvertising};
use esp_idf_hal::delay::FreeRtos;
use heapless::Vec;
use heapless::spsc::{Queue, Producer, Consumer};

const MAX_CONNECTIONS: usize = 4;
const BUFFER_SIZE: usize = 4096;

struct Connection {
    conn_id: u16,
    remote_addr: [u8; 6],
    rx_buffer: Vec<u8, BUFFER_SIZE>,
    tx_buffer: Vec<u8, BUFFER_SIZE>,
    authenticated: bool,
    last_activity: u32,
}

struct BLEBridge {
    connections: [Option<Connection>; MAX_CONNECTIONS],
    lora_tx: Producer<'static, ArxObject, 16>,
    lora_rx: Consumer<'static, ArxObject, 16>,
    gatts: BleGatts,
    gap: BleGap,
}

impl BLEBridge {
    fn init() -> Result<Self, EspError> {
        // Initialize BLE
        let gatts = BleGatts::new()?;
        let gap = BleGap::new()?;
        let advertising = BleAdvertising::new()?;
        
        esp_bluedroid_init();
        esp_bluedroid_enable();
        
        // Register GATT server
        esp_ble_gatts_register_callback(gatts_event_handler);
        esp_ble_gatts_app_register(0);
        
        // Set up advertising
        setup_advertising();
        
        // Create queues for LoRa communication
        lora_tx_queue = xQueueCreate(10, sizeof(MeshPacket));
        lora_rx_queue = xQueueCreate(10, sizeof(MeshPacket));
    }
    
    void setup_advertising() {
        esp_ble_adv_params_t adv_params = {
            .adv_int_min = 0x50,  // 100ms
            .adv_int_max = 0x50,
            .adv_type = ADV_TYPE_IND,
            .own_addr_type = BLE_ADDR_TYPE_PUBLIC,
            .channel_map = ADV_CHNL_ALL,
            .adv_filter_policy = ADV_FILTER_ALLOW_SCAN_ANY_CON_ANY,
        };
        
        // Advertising data
        uint8_t adv_data[] = {
            0x02, 0x01, 0x06,  // Flags
            0x11, 0x09, 'A', 'r', 'x', 'o', 's', '-',  // Name
            '0', '0', '0', '1',  // Node ID
            0x03, 0x03, 0x00, 0x18  // Service UUID (short)
        };
        
        esp_ble_gap_config_adv_data_raw(adv_data, sizeof(adv_data));
        esp_ble_gap_start_advertising(&adv_params);
    }
    
    // Handle ArxQL query from mobile device
    void process_query(uint16_t conn_id, const uint8_t* data, size_t len) {
        // Parse ArxQL command
        ArxQLCommand cmd;
        if (!parse_arxql(data, len, &cmd)) {
            send_error(conn_id, "Invalid ArxQL syntax");
            return;
        }
        
        // Check if query can be handled locally
        if (is_local_query(cmd)) {
            handle_local_query(conn_id, cmd);
        } else {
            // Forward to mesh network
            forward_to_mesh(conn_id, cmd);
        }
    }
    
    // Bridge ArxObjects between BLE and LoRa
    void bridge_task(void* param) {
        MeshPacket packet;
        
        while (true) {
            // Check for incoming LoRa packets
            if (xQueueReceive(lora_rx_queue, &packet, 0) == pdTRUE) {
                // Find connection waiting for this response
                uint16_t conn_id = find_waiting_connection(packet.request_id);
                if (conn_id != INVALID_CONN_ID) {
                    // Convert to BLE format and send
                    uint8_t ble_data[512];
                    size_t ble_len = mesh_to_ble(packet, ble_data);
                    send_notification(conn_id, ble_data, ble_len);
                }
            }
            
            // Process outgoing BLE data
            for (int i = 0; i < MAX_CONNECTIONS; i++) {
                if (connections[i].tx_len > 0) {
                    // Convert to mesh packet
                    MeshPacket mesh_pkt;
                    ble_to_mesh(connections[i].tx_buffer, 
                               connections[i].tx_len, &mesh_pkt);
                    
                    // Send to LoRa
                    xQueueSend(lora_tx_queue, &mesh_pkt, 0);
                    connections[i].tx_len = 0;
                }
            }
            
            vTaskDelay(pdMS_TO_TICKS(10));
        }
    }
};
```

### Mobile App Integration (Rust)

```rust
// src/mobile/bluetooth_bridge.rs

use btleplug::api::{Central, Peripheral, WriteType};
use btleplug::platform::{Adapter, Manager};
use uuid::Uuid;
use tokio::sync::mpsc;

const SERVICE_UUID: Uuid = Uuid::from_u128(0x6E400001_B5A3_F393_E0A9_E50E24DCCA9E);
const TX_CHAR_UUID: Uuid = Uuid::from_u128(0x6E400002_B5A3_F393_E0A9_E50E24DCCA9E);
const RX_CHAR_UUID: Uuid = Uuid::from_u128(0x6E400003_B5A3_F393_E0A9_E50E24DCCA9E);

pub struct BluetoothBridge {
    adapter: Adapter,
    device: Option<Box<dyn Peripheral>>,
    rx_channel: mpsc::Receiver<Vec<u8>>,
    tx_channel: mpsc::Sender<Vec<u8>>,
}

impl BluetoothBridge {
    pub async fn new() -> Result<Self, Error> {
        let manager = Manager::new().await?;
        let adapters = manager.adapters().await?;
        let adapter = adapters.into_iter().nth(0)
            .ok_or(Error::NoAdapter)?;
        
        let (tx, rx) = mpsc::channel(100);
        
        Ok(Self {
            adapter,
            device: None,
            rx_channel: rx,
            tx_channel: tx,
        })
    }
    
    pub async fn scan_for_nodes(&self) -> Result<Vec<ArxosNode>, Error> {
        self.adapter.start_scan().await?;
        tokio::time::sleep(Duration::from_secs(5)).await;
        
        let peripherals = self.adapter.peripherals().await?;
        let mut nodes = Vec::new();
        
        for peripheral in peripherals {
            if let Ok(Some(properties)) = peripheral.properties().await {
                if properties.local_name.as_ref()
                    .map(|n| n.starts_with("Arxos-"))
                    .unwrap_or(false) 
                {
                    nodes.push(ArxosNode {
                        name: properties.local_name.unwrap(),
                        address: properties.address,
                        rssi: properties.rssi,
                    });
                }
            }
        }
        
        self.adapter.stop_scan().await?;
        Ok(nodes)
    }
    
    pub async fn connect(&mut self, node: &ArxosNode) -> Result<(), Error> {
        let peripherals = self.adapter.peripherals().await?;
        
        for peripheral in peripherals {
            if let Ok(Some(properties)) = peripheral.properties().await {
                if properties.address == node.address {
                    peripheral.connect().await?;
                    peripheral.discover_services().await?;
                    
                    // Subscribe to notifications
                    let chars = peripheral.characteristics();
                    let rx_char = chars.iter()
                        .find(|c| c.uuid == RX_CHAR_UUID)
                        .ok_or(Error::CharacteristicNotFound)?;
                    
                    peripheral.subscribe(rx_char).await?;
                    
                    // Start notification handler
                    let tx = self.tx_channel.clone();
                    let peripheral_clone = peripheral.clone();
                    tokio::spawn(async move {
                        let mut notification_stream = 
                            peripheral_clone.notifications().await.unwrap();
                        
                        while let Some(data) = notification_stream.next().await {
                            tx.send(data.value).await.ok();
                        }
                    });
                    
                    self.device = Some(Box::new(peripheral));
                    return Ok(());
                }
            }
        }
        
        Err(Error::NodeNotFound)
    }
    
    pub async fn send_command(&self, arxql: &str) -> Result<(), Error> {
        if let Some(device) = &self.device {
            let chars = device.characteristics();
            let tx_char = chars.iter()
                .find(|c| c.uuid == TX_CHAR_UUID)
                .ok_or(Error::CharacteristicNotFound)?;
            
            // Fragment if necessary (BLE MTU is typically 244 bytes)
            let data = arxql.as_bytes();
            for chunk in data.chunks(244) {
                device.write(tx_char, chunk, WriteType::WithResponse).await?;
            }
            
            Ok(())
        } else {
            Err(Error::NotConnected)
        }
    }
    
    pub async fn receive_response(&mut self) -> Result<Vec<u8>, Error> {
        self.rx_channel.recv().await
            .ok_or(Error::ChannelClosed)
    }
}

// High-level API
pub struct ArxosBLE {
    bridge: BluetoothBridge,
    cache: HashMap<String, CachedResponse>,
}

impl ArxosBLE {
    pub async fn query(&mut self, arxql: &str) -> Result<QueryResponse, Error> {
        // Check cache first
        if let Some(cached) = self.cache.get(arxql) {
            if cached.timestamp.elapsed() < Duration::from_secs(30) {
                return Ok(cached.response.clone());
            }
        }
        
        // Send query
        self.bridge.send_command(arxql).await?;
        
        // Wait for response with timeout
        let response = tokio::time::timeout(
            Duration::from_secs(5),
            self.bridge.receive_response()
        ).await??;
        
        // Parse response
        let parsed = parse_arxos_response(&response)?;
        
        // Cache result
        self.cache.insert(arxql.to_string(), CachedResponse {
            response: parsed.clone(),
            timestamp: Instant::now(),
        });
        
        Ok(parsed)
    }
}
```

## Protocol Translation

### ArxQL to BLE Packet Format

```
ArxQL Command: "QUERY floor:2 type:outlet status:available"

BLE Packet Structure:
┌────────┬────────┬────────┬────────────────────────┐
│ Header │ Length │  Cmd   │       Payload          │
│ (1B)   │  (2B)  │  (1B)  │      (Variable)        │
├────────┼────────┼────────┼────────────────────────┤
│  0xAA  │ 0x002C │  0x01  │ "floor:2 type:outlet.."│
└────────┴────────┴────────┴────────────────────────┘

Header: 0xAA = Start of packet
Length: Total packet length including header
Cmd:    0x01 = Query, 0x02 = Control, 0x03 = Status
```

### ArxObject to BLE Format

```
ArxObject (13 bytes) → BLE Notification (20 bytes)

Original ArxObject:
[ID:2][Type:1][X:2][Y:2][Z:2][Props:4] = 13 bytes

BLE Format:
[Header:1][Count:1][Timestamp:4][ArxObject:13][CRC:1] = 20 bytes

Multiple objects are sent as:
[Header][Count:N][Timestamp][Obj1][Obj2]...[ObjN][CRC]
```

## Performance Optimization

### Connection Parameters

```c
// Optimal BLE connection parameters for low latency
typedef struct {
    uint16_t min_interval;  // 7.5ms (6 * 1.25ms)
    uint16_t max_interval;  // 15ms (12 * 1.25ms)
    uint16_t latency;       // 0 (no slave latency)
    uint16_t timeout;       // 2000ms (200 * 10ms)
} ConnectionParams;

// Different profiles for different use cases
const ConnectionParams profiles[] = {
    // Interactive (terminal commands)
    {.min_interval = 6, .max_interval = 12, .latency = 0, .timeout = 200},
    
    // Bulk transfer (floor plans)
    {.min_interval = 40, .max_interval = 80, .latency = 4, .timeout = 600},
    
    // Power saving (monitoring)
    {.min_interval = 320, .max_interval = 640, .latency = 10, .timeout = 1000},
};
```

### Data Compression

```rust
// Compress ArxQL responses for BLE transmission
fn compress_response(objects: &[ArxObject]) -> Vec<u8> {
    let mut compressed = Vec::new();
    
    // Use delta encoding for coordinates
    let mut prev_x = 0u16;
    let mut prev_y = 0u16;
    let mut prev_z = 0u16;
    
    for obj in objects {
        // Store deltas instead of absolute values
        let dx = (obj.x as i16 - prev_x as i16) as u8;
        let dy = (obj.y as i16 - prev_y as i16) as u8;
        let dz = (obj.z as i16 - prev_z as i16) as u8;
        
        compressed.push(obj.object_type);
        compressed.push(dx);
        compressed.push(dy);
        compressed.push(dz);
        
        prev_x = obj.x;
        prev_y = obj.y;
        prev_z = obj.z;
    }
    
    compressed
}
```

## Security Implementation

### Pairing and Bonding

```c
// BLE security configuration
static void configure_security() {
    // Set security parameters
    esp_ble_auth_req_t auth_req = ESP_LE_AUTH_REQ_SC_MITM_BOND;
    esp_ble_io_cap_t iocap = ESP_IO_CAP_NONE;  // No input/output
    
    uint8_t key_size = 16;
    uint8_t init_key = ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK;
    uint8_t rsp_key = ESP_BLE_ENC_KEY_MASK | ESP_BLE_ID_KEY_MASK;
    
    esp_ble_gap_set_security_param(ESP_BLE_SM_AUTHEN_REQ_MODE, 
                                   &auth_req, sizeof(auth_req));
    esp_ble_gap_set_security_param(ESP_BLE_SM_IOCAP_MODE, 
                                   &iocap, sizeof(iocap));
    esp_ble_gap_set_security_param(ESP_BLE_SM_MAX_KEY_SIZE, 
                                   &key_size, sizeof(key_size));
    esp_ble_gap_set_security_param(ESP_BLE_SM_SET_INIT_KEY, 
                                   &init_key, sizeof(init_key));
    esp_ble_gap_set_security_param(ESP_BLE_SM_SET_RSP_KEY, 
                                   &rsp_key, sizeof(rsp_key));
}
```

### Access Control

```rust
// Building-specific access tokens
struct AccessToken {
    building_id: Uuid,
    user_id: String,
    permissions: Permissions,
    expires: Instant,
    signature: [u8; 64],  // Ed25519 signature
}

impl AccessToken {
    fn validate(&self, building_key: &PublicKey) -> bool {
        // Check expiration
        if Instant::now() > self.expires {
            return false;
        }
        
        // Verify signature
        let message = format!("{}{}{:?}{:?}", 
            self.building_id, self.user_id, 
            self.permissions, self.expires);
        
        verify_signature(building_key, message.as_bytes(), &self.signature)
    }
}
```

## Monitoring and Diagnostics

### Connection Metrics

```c
typedef struct {
    uint32_t packets_sent;
    uint32_t packets_received;
    uint32_t bytes_sent;
    uint32_t bytes_received;
    uint16_t rssi;
    uint16_t connection_interval;
    uint8_t phy;  // 1M, 2M, or Coded PHY
    uint32_t errors;
    uint32_t retransmissions;
} ConnectionMetrics;

// Report metrics via status characteristic
void report_metrics(uint16_t conn_id) {
    ConnectionMetrics metrics;
    get_connection_metrics(conn_id, &metrics);
    
    uint8_t report[16];
    pack_metrics(&metrics, report);
    
    send_notification(conn_id, STATUS_CHAR_UUID, report, sizeof(report));
}
```

## Testing Procedures

### Range Testing

```bash
#!/bin/bash
# BLE range test script

# Test at various distances
for distance in 10 20 50 100; do
    echo "Testing at ${distance}m..."
    
    # Position device at distance
    read -p "Position device at ${distance}m and press enter"
    
    # Run throughput test
    ./ble_test --mode throughput --duration 60 > "ble_${distance}m.log"
    
    # Run latency test
    ./ble_test --mode latency --count 1000 >> "ble_${distance}m.log"
    
    # Measure RSSI
    ./ble_test --mode rssi --samples 100 >> "ble_${distance}m.log"
done
```

### Interference Testing

```python
# Test BLE performance with WiFi interference
def test_coexistence():
    # Start WiFi traffic generator on 2.4GHz
    start_wifi_traffic(channel=6, bandwidth=40)
    
    # Test BLE on overlapping channels
    results = []
    for ble_channel in [37, 38, 39]:  # BLE advertising channels
        metrics = test_ble_performance(channel=ble_channel)
        results.append(metrics)
    
    # Test with adaptive frequency hopping
    afh_metrics = test_ble_performance(afh_enabled=True)
    
    return {
        'static_channels': results,
        'adaptive_hopping': afh_metrics
    }
```

## Conclusion

The Bluetooth Mesh Bridge leverages existing ESP32 hardware to provide zero-configuration access to the Arxos building network. By implementing BLE 5.0 with proper connection parameters and security, mobile devices can reliably communicate with buildings from up to 100 meters away without requiring any special hardware.

The bridge maintains the air-gapped security model by never routing traffic to the internet, while providing familiar Bluetooth connectivity that works with every modern smartphone.