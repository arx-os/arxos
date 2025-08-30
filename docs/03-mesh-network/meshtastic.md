# Meshtastic Integration Guide

## Building on Battle-Tested Mesh Infrastructure

### What is Meshtastic?

Meshtastic is an open-source, off-grid, decentralized mesh network built for ESP32 boards with LoRa radios. It's perfect for Arxos because:

- **Proven**: Thousands of nodes worldwide
- **Encrypted**: AES-256 by default
- **Efficient**: Optimized for low bandwidth
- **Extensible**: Plugin architecture
- **Active**: Vibrant developer community

### Arxos as a Meshtastic Plugin

```python
# Arxos extends Meshtastic with:
class ArxosPlugin(MeshtasticPlugin):
    def __init__(self):
        self.name = "Arxos Building OS"
        self.port_num = 256  # Custom port for ArxObjects
        self.want_response = True
    
    def process_packet(self, packet):
        # Decode 13-byte ArxObject
        arxobj = ArxObject.from_bytes(packet.decoded.payload)
        
        # Update building cache
        building_cache.update(arxobj)
        
        # Award BILT tokens
        if arxobj.is_discovery():
            award_bilt(packet.from_id, 50)
        
        # Update terminal display
        terminal.refresh(arxobj)
```

### Hardware Requirements

```yaml
Supported Boards:
- TTGO T-Beam ($35)
  - ESP32 + LoRa + GPS + Battery
  - Perfect for mobile players
  
- Heltec LoRa32 V3 ($25)
  - ESP32-S3 + LoRa + OLED
  - Great for fixed nodes
  
- RAK WisBlock ($45)
  - Modular system
  - Professional grade
  
- DIY ESP32 + SX1262 ($20)
  - Maximum flexibility
  - Custom PCB possible
```

### Flashing Meshtastic

```bash
# Web installer (easiest)
Visit: https://flasher.meshtastic.org
Click: "Flash ESP32"
Select: Your board type
Connect: USB cable
Flash: Automatic!

# CLI installer
pip install meshtastic-flasher
meshtastic-flasher --port /dev/ttyUSB0 --board heltec-v3

# Arduino IDE (for customization)
1. Install ESP32 board support
2. Clone Meshtastic firmware
3. Add Arxos plugin
4. Compile and upload
```

### Channel Configuration

```python
# Configure Arxos channels
import meshtastic
import meshtastic.serial_interface

interface = meshtastic.serial_interface.SerialInterface()

# Channel 0: Building Operations
interface.sendText(
    "meshtastic --ch-index 0 "
    "--ch-name 'Building Ops' "
    "--ch-psk random "
    "--ch-uplink false"
)

# Channel 1: Player Chat  
interface.sendText(
    "meshtastic --ch-index 1 "
    "--ch-name 'Player Chat' "
    "--ch-psk random"
)

# Channel 2: Emergency
interface.sendText(
    "meshtastic --ch-index 2 "
    "--ch-name 'Emergency' "
    "--ch-psk KNOWN_EMERGENCY_KEY"
)
```

### Region Configuration

```yaml
United States:
  frequency: 902-928 MHz
  power: 100 mW (20 dBm)
  channels: 13
  
Europe:
  frequency: 863-870 MHz
  power: 25 mW (14 dBm)
  duty_cycle: 1%
  
Asia:
  frequency: 920-925 MHz
  power: 25 mW (14 dBm)
  channels: varies

Australia:
  frequency: 915-928 MHz
  power: 25 mW (14 dBm)
  channels: 51
```

### Meshtastic Settings for Arxos

```python
# Optimal settings for building automation
config = {
    "lora": {
        "region": "US",
        "modem_preset": "MEDIUM_FAST",  # Good balance
        "hop_limit": 3,  # City-wide reach
        "tx_power": 20,  # Maximum legal
        "channel_num": 20,  # Avoid interference
    },
    "device": {
        "role": "ROUTER",  # Fixed nodes
        # "role": "CLIENT",  # Mobile players
        "serial_enabled": True,  # Terminal access
        "debug_log_enabled": False,  # Save bandwidth
    },
    "position": {
        "position_broadcast_secs": 0,  # Disable GPS
        "gps_update_interval": 0,  # Save battery
    },
    "power": {
        "wait_bluetooth_secs": 0,  # No Bluetooth
        "mesh_sds_timeout_secs": 0,  # Always on
        "sds_secs": 0,  # No sleep
    },
}
```

### ArxObject over Meshtastic

```python
# Send ArxObject through Meshtastic
def send_arxobject(arxobj, interface):
    # Pack into 13 bytes
    payload = arxobj.to_bytes()
    
    # Send on Arxos port
    interface.sendData(
        payload,
        portNum=256,  # Arxos port
        channelIndex=0,  # Building ops channel
        wantResponse=True,
    )

# Receive ArxObject
def on_receive(packet, interface):
    if packet.decoded.portnum == 256:  # Arxos port
        arxobj = ArxObject.from_bytes(packet.decoded.payload)
        print(f"Received: {arxobj}")
        
        # Update game state
        update_building_model(arxobj)
        award_discovery_bilt(packet.from_id, arxobj)
```

### Mesh Commands

```bash
# List nodes in mesh
meshtastic --nodes

# Send ArxObject (hex encoded)
meshtastic --senddata 0F17101472086604B00F140150 --port 256

# Monitor packets
meshtastic --debug --listen

# Get mesh statistics
meshtastic --info
```

### Performance Tuning

#### For Dense Buildings (Many Nodes)
```python
config = {
    "lora": {
        "modem_preset": "SHORT_FAST",  # Lower range, higher speed
        "hop_limit": 1,  # Single building
        "tx_power": 10,  # Reduce interference
    }
}
```

#### For Sparse Rural (Few Nodes)
```python
config = {
    "lora": {
        "modem_preset": "LONG_SLOW",  # Maximum range
        "hop_limit": 7,  # Regional coverage
        "tx_power": 20,  # Maximum power
    }
}
```

### Troubleshooting

| Problem | Solution |
|---------|----------||
| No nodes found | Check antenna, increase hop_limit |
| Slow delivery | Use SHORT_FAST preset |
| Poor range | Use LONG_SLOW, external antenna |
| Packet loss | Reduce tx rate, check interference |
| Battery drain | Increase sleep time, reduce tx_power |

### Meshtastic API Usage

```python
# Python API for building integration
import meshtastic
import meshtastic.serial_interface
from arxos import ArxObject

class ArxosMesh:
    def __init__(self, port="/dev/ttyUSB0"):
        self.interface = meshtastic.serial_interface.SerialInterface(port)
        self.interface.on_receive = self.on_packet
        
    def on_packet(self, packet, interface):
        """Handle incoming packets"""
        if packet.decoded.portnum == 256:
            arxobj = ArxObject.from_bytes(packet.decoded.payload)
            self.process_arxobject(arxobj)
    
    def send_arxobject(self, arxobj):
        """Send ArxObject to mesh"""
        self.interface.sendData(
            arxobj.to_bytes(),
            portNum=256,
            wantResponse=True
        )
    
    def process_arxobject(self, arxobj):
        """Game logic for received objects"""
        print(f"Object {arxobj.id:04X} at ({arxobj.x}, {arxobj.y})")
        # Update building model
        # Award BILT tokens
        # Refresh terminal display
```

### Integration with Terminal

```bash
# Terminal shows mesh status
$ arxos mesh status

Mesh Network Status
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Nodes Online: 12
Packets/Hour: 847
Delivery Rate: 98.3%
Average Hops: 2.1

Nearby Buildings:
  Office Complex [!YOU] - 247 objects
  Shopping Mall [3 hops] - 892 objects
  School [2 hops] - 421 objects
  
Channel Usage:
  Ch0 (Ops): 45% utilized
  Ch1 (Chat): 12% utilized  
  Ch2 (Emergency): 0% utilized
  
Your Node:
  ID: !abc123ef
  Battery: 100% (USB powered)
  Uptime: 47 hours
  BILT Earned: 1,247
```

### Advanced Features

#### Store and Forward
```python
# Enable S&F for offline nodes
config["store_forward"] = {
    "enabled": True,
    "heartbeat": 900,  # 15 minutes
    "records": 100,
    "history_return_max": 25,
}
```

#### Range Testing
```bash
# Built-in range test mode
meshtastic --set range_test_enabled true

# Monitor signal quality
meshtastic --info | grep -i snr
```

#### Firmware Customization
```c
// Add Arxos to Meshtastic firmware
#define ARXOS_PORT_NUM 256

void handleArxosPacket(MeshPacket *p) {
    ArxObject obj;
    memcpy(&obj, p->decoded.payload.bytes, 13);
    
    // Process ArxObject
    updateBuildingCache(&obj);
    
    // Award BILT tokens
    if (isDiscovery(&obj)) {
        awardBilt(p->from, 50);
    }
}
```

---

→ Next: [Routing Algorithms](routing.md)