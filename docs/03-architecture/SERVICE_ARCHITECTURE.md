---
title: Arxos Service Architecture
summary: Separation of concerns between Arxos service and Meshtastic firmware, with protocol translation and deployment options.
owner: Lead Architecture
last_updated: 2025-09-04
---
# Arxos Service Architecture

> For protocol and transport specifics, see:
> - Mesh protocol canonical: [../12-protocols/MESH_PROTOCOL.md](../12-protocols/MESH_PROTOCOL.md)
> - Technical mesh architecture: [../technical/mesh_architecture.md](../technical/mesh_architecture.md)

## Overview

Arxos operates as a **software-as-a-service (SaaS)** running on standard Meshtastic hardware. This architecture provides clean separation between the proven Meshtastic mesh networking platform and the Arxos building intelligence system.

## Architecture Principles

### 1. Service Layer Separation
- **Meshtastic Hardware**: Unchanged, proven mesh networking
- **Arxos Service**: Building intelligence software layer
- **Clean Interface**: Standard Meshtastic client protocol

### 2. No Firmware Modification
- **Standard Meshtastic**: Use existing, stable firmware
- **Software Layer**: Arxos runs as a service on top
- **Easy Updates**: Software updates without firmware changes

### 3. Hardware Independence
- **Any Meshtastic Device**: Works with any compatible hardware
- **Vendor Neutral**: Not tied to specific hardware vendors
- **Future Proof**: Easy to support new Meshtastic devices

## Service Architecture

### High-Level Service Stack

```
┌─────────────────────────────────────────────────────────┐
│  User Terminal Interface (Desktop/Mobile)              │
├─────────────────────────────────────────────────────────┤
│  Arxos Service Layer (Rust)                            │
│  ├── Building Intelligence Engine                      │
│  ├── ArxObject Processing                              │
│  ├── Document Parser                                   │
│  ├── Terminal Interface                                │
│  └── Meshtastic Client                                 │
├─────────────────────────────────────────────────────────┤
│  Meshtastic Hardware (Unchanged)                       │
│  ├── Standard Meshtastic Firmware                      │
│  ├── LoRa Mesh Networking                              │
│  └── ESP32 + LoRa Radio                                │
└─────────────────────────────────────────────────────────┘
```

### Service Components

#### 1. Arxos Service Core
```rust
pub struct ArxOSService {
    meshtastic_client: MeshtasticClient,
    building_engine: BuildingIntelligenceEngine,
    terminal_interface: TerminalInterface,
    document_parser: DocumentParser,
    database: Database,
}

impl ArxOSService {
    pub async fn run(&mut self) -> Result<(), Error> {
        // Main service loop
        loop {
            tokio::select! {
                // Handle Meshtastic messages
                mesh_msg = self.meshtastic_client.receive() => {
                    self.handle_mesh_message(mesh_msg?).await?;
                }
                // Handle terminal commands
                terminal_cmd = self.terminal_interface.get_command() => {
                    self.execute_command(terminal_cmd?).await?;
                }
                // Process building intelligence
                building_update = self.building_engine.process() => {
                    self.update_building_intelligence(building_update?).await?;
                }
            }
        }
    }
}
```

#### 2. Meshtastic Client Integration
```rust
pub struct MeshtasticClient {
    connection: MeshtasticConnection,
    protocol_translator: ProtocolTranslator,
    message_queue: MessageQueue,
}

impl MeshtasticClient {
    pub async fn send_arxobject(&self, arxobject: ArxObject) -> Result<(), Error> {
        // Convert ArxObject to Meshtastic message
        let meshtastic_msg = self.protocol_translator.encode_arxobject(arxobject)?;
        
        // Send via standard Meshtastic protocol
        self.connection.send_message(meshtastic_msg).await?;
        Ok(())
    }
    
    pub async fn receive_message(&self) -> Result<Option<ArxObject>, Error> {
        // Receive Meshtastic message
        if let Some(meshtastic_msg) = self.connection.receive_message().await? {
            // Convert to ArxObject
            let arxobject = self.protocol_translator.decode_arxobject(meshtastic_msg)?;
            Ok(Some(arxobject))
        } else {
            Ok(None)
        }
    }
}
```

#### 3. Protocol Translation
```rust
pub struct ProtocolTranslator {
    arxos_encoder: ArxOSEncoder,
    arxos_decoder: ArxOSDecoder,
}

impl ProtocolTranslator {
    pub fn encode_arxobject(&self, arxobject: ArxObject) -> Result<MeshtasticMessage, Error> {
        // Convert 13-byte ArxObject to Meshtastic message format
        let data = self.arxos_encoder.encode(arxobject)?;
        Ok(MeshtasticMessage::new(data))
    }
    
    pub fn decode_arxobject(&self, msg: MeshtasticMessage) -> Result<ArxObject, Error> {
        // Convert Meshtastic message to 13-byte ArxObject
        let data = msg.get_data();
        let arxobject = self.arxos_decoder.decode(data)?;
        Ok(arxobject)
    }
}
```

## Deployment Architecture

### Service Deployment Options

#### Option 1: Standalone Service
```bash
# Run Arxos as standalone service on ESP32
arxos-service --config config.toml --meshtastic-port /dev/ttyUSB0
```

<!-- Docker/containerization removed per project constraints: pure local binaries on devices only. -->

#### Option 3: System Service
```ini
[Unit]
Description=Arxos Building Intelligence Service
After=network.target

[Service]
Type=simple
User=arxos
ExecStart=/usr/local/bin/arxos-service
Restart=always

[Install]
WantedBy=multi-user.target
```

### Configuration Management

#### Service Configuration
```toml
# config.toml
[meshtastic]
port = "/dev/ttyUSB0"
baud_rate = 9600
node_id = 0x0001

[building]
id = "building-001"
name = "Crystal Tower"
location = { lat = 40.7128, lon = -74.0060 }

[database]
path = "/var/lib/arxos/building.db"
max_size = "100MB"

[terminal]
prompt = "arx>"
history_size = 1000
```

## Service Integration

### Meshtastic Integration Points

#### 1. Message Protocol
- **Standard Meshtastic**: Use existing message format
- **ArxObject Payload**: Embed 13-byte ArxObjects in message data
- **Routing**: Leverage Meshtastic's proven routing algorithms

#### 2. Hardware Interface
- **Serial Connection**: Connect to Meshtastic device via serial
- **USB Connection**: Use USB-to-serial for development
- **Bluetooth**: Connect via Bluetooth for mobile devices

#### 3. Network Management
- **Mesh Discovery**: Use Meshtastic's node discovery
- **Route Management**: Leverage Meshtastic's routing tables
- **Connection Management**: Use Meshtastic's connection handling

### Service Lifecycle

#### 1. Service Startup
```rust
impl ArxOSService {
    pub async fn start(&mut self) -> Result<(), Error> {
        // Initialize Meshtastic connection
        self.meshtastic_client.connect().await?;
        
        // Initialize building intelligence engine
        self.building_engine.initialize().await?;
        
        // Start terminal interface
        self.terminal_interface.start().await?;
        
        // Begin main service loop
        self.run().await
    }
}
```

#### 2. Service Shutdown
```rust
impl ArxOSService {
    pub async fn shutdown(&mut self) -> Result<(), Error> {
        // Graceful shutdown
        self.terminal_interface.stop().await?;
        self.building_engine.shutdown().await?;
        self.meshtastic_client.disconnect().await?;
        Ok(())
    }
}
```

## Benefits of Service Architecture

### 1. Development Benefits
- **Faster Development**: Focus on building intelligence, not mesh networking
- **Easy Testing**: Test Arxos logic independently of hardware
- **Standard Tools**: Use normal Rust development tools
- **Version Control**: Easy software versioning and updates

### 2. Deployment Benefits
- **Software Updates**: Update Arxos without touching firmware
- **A/B Testing**: Deploy different Arxos versions
- **Rollback**: Easy to rollback software changes
- **Monitoring**: Standard service monitoring and logging

### 3. Hardware Benefits
- **Proven Hardware**: Use battle-tested Meshtastic devices
- **Vendor Independence**: Not tied to specific hardware vendors
- **Future Hardware**: Easy to support new Meshtastic devices
- **Cost Effective**: Leverage existing Meshtastic ecosystem

### 4. Maintenance Benefits
- **Separation of Concerns**: Clear boundaries between layers
- **Independent Updates**: Update Arxos and Meshtastic independently
- **Easier Debugging**: Isolate issues to specific layers
- **Community Support**: Leverage both Arxos and Meshtastic communities

## Implementation Strategy

### Phase 1: Service Foundation
1. **Create Service Structure**: Basic service framework
2. **Meshtastic Client**: Implement Meshtastic client integration
3. **Protocol Translation**: Convert between ArxOS and Meshtastic formats
4. **Basic Terminal**: Simple terminal interface

### Phase 2: Building Intelligence
1. **ArxObject Processing**: Core ArxObject handling
2. **Building Engine**: Building intelligence algorithms
3. **Document Parser**: Document processing capabilities
4. **Database Integration**: Building data storage

### Phase 3: Advanced Features
1. **Holographic Processing**: Fractal generation and quantum simulation
2. **Mesh Collaboration**: Advanced mesh intelligence features
3. **Performance Optimization**: Service performance tuning
4. **Production Deployment**: Production-ready service deployment

## Conclusion

The Arxos Service Architecture provides a clean, maintainable approach to building intelligence by leveraging the proven Meshtastic platform while adding advanced building intelligence capabilities. This architecture enables rapid development, easy deployment, and future scalability while maintaining the core principles of air-gapped, terminal-only operation.

Key advantages include:
- **Clean Separation**: Clear boundaries between mesh networking and building intelligence
- **Proven Foundation**: Leverage battle-tested Meshtastic platform
- **Easy Development**: Focus on building intelligence, not mesh networking
- **Future Proof**: Easy to extend and maintain
- **Hardware Independence**: Works with any Meshtastic-compatible device
