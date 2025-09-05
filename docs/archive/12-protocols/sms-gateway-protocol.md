# SMS Gateway Protocol Specification

> Scope: Emergency and universal fallback. For mesh transport details, defer to `MESH_PROTOCOL.md`; for object formats, see `../technical/arxobject_specification.md`.
**Version:** 1.0  
**Date:** August 31, 2025  
**Purpose:** Emergency and Universal Access

## Overview

The SMS Gateway provides universal building access through standard text messaging, ensuring critical information remains accessible during emergencies when internet and power may be unavailable. This system works with any phone capable of SMS, from flip phones to smartphones.

## System Architecture

### Hardware Configuration

```
┌─────────────────────────────────────────────┐
│            Raspberry Pi Zero W               │
│  ┌─────────────────────────────────────┐    │
│  │  Quectel EC25 LTE Modem (Mini PCIe) │    │
│  │  - Global bands support              │    │
│  │  - SMS and voice capable             │    │
│  │  - 12V backup battery                │    │
│  └──────────────┬──────────────────────┘    │
│                 │                            │
│  ┌──────────────▼──────────────────────┐    │
│  │     SMS Gateway Software            │    │
│  │  - Message parser                   │    │
│  │  - Command processor                │    │
│  │  - Response formatter               │    │
│  └──────────────┬──────────────────────┘    │
│                 │                            │
│  ┌──────────────▼──────────────────────┐    │
│  │    LoRa Mesh Interface              │    │
│  │  - Query building network           │    │
│  │  - Cache critical data              │    │
│  └─────────────────────────────────────┘    │
└─────────────────────────────────────────────┘
```

### Network Topology

```
Any Phone (SMS)
     │
     ▼
Cellular Network
     │
┌────▼────────────────────┐
│  Building SMS Gateway    │
│  Phone: +1-555-BLD-1234  │
└────┬────────────────────┘
     │
     ▼
Building Mesh Network
```

## SMS Command Protocol

### Message Format

```
Inbound SMS Structure:
[AUTH] [COMMAND] [PARAMS]

AUTH:    4-digit code or "911" for emergency
COMMAND: Action to perform (4-8 characters)
PARAMS:  Space-separated key:value pairs

Examples:
"1234 STATUS room:127"
"1234 MAP floor:2"
"911 EXITS"
"HELP"
```

### Command Dictionary

#### Public Commands (No Auth Required)

| Command | Description | Response |
|---------|-------------|----------|
| HELP | Show available commands | Command list |
| INFO | Building information | Name, address, emergency # |
| 911 | Emergency menu | Emergency commands |

#### Authenticated Commands

| Command | Parameters | Description | Example |
|---------|------------|-------------|---------|
| STATUS | room:N | Room status | "1234 STATUS room:127" |
| MAP | floor:N | ASCII floor plan | "1234 MAP floor:1" |
| FIND | type:X | Locate equipment | "1234 FIND type:outlet" |
| QUERY | various | ArxQL query | "1234 QUERY floor:2 type:exit" |
| ROUTE | from:X to:Y | Navigation | "1234 ROUTE from:lobby to:127" |
| ALERT | message | Send alert | "1234 ALERT water leak room 205" |

#### Emergency Commands (911 Prefix)

| Command | Description | Response |
|---------|-------------|----------|
| 911 EXITS | All emergency exits | List with distances |
| 911 FIRE | Fire system status | Alarms, sprinklers |
| 911 AED | AED locations | Nearest AED devices |
| 911 EVAC | Evacuation routes | Safest exit paths |
| 911 HAZMAT | Hazmat info | Chemical storage |
| 911 SHELTER | Shelter areas | Safe rooms |
| 911 PEOPLE | Occupancy estimate | People count by area |
| 911 SYSTEMS | Critical systems | Power, water, HVAC |

### Response Format

#### Single SMS Response (≤160 chars)

```
"Rm 127: 2 outlets on B7, 1 light, temp 72F, vacant. Last check: 5min ago [1/1]"
```

#### Multi-Part Response

```
SMS 1: "[1/3] Floor 2 - North Wing
###############
#  201 | 202  #"

SMS 2: "[2/3] # Lab  |Class #
# [O]  | [O]  #
#  [L] | [L]  #"

SMS 3: "[3/3] ###############
Legend: O=Outlet L=Light
Query time: 2.1s"
```

#### ASCII Floor Plan Format

```
Compact Mode (for SMS):
#########
#101|102#
#Lab|Off#
#[O]|[O]#
#########

Legend Mode:
O=Outlet
L=Light  
D=Door
E=Exit
F=Fire
```

## Implementation

### Gateway Software (Python)

```python
# src/gateway/sms_gateway.py

import serial
import re
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
import asyncio
from dataclasses import dataclass

@dataclass
class SMSMessage:
    sender: str
    timestamp: datetime
    body: str
    
@dataclass
class SMSResponse:
    recipient: str
    parts: List[str]  # Split for multi-part messages

class SMSGateway:
    def __init__(self, modem_port: str, mesh_interface):
        self.modem = serial.Serial(modem_port, 115200)
        self.mesh = mesh_interface
        self.auth_codes = {}  # phone -> (code, expiry)
        self.rate_limits = {}  # phone -> last_request_time
        
    async def init_modem(self):
        """Initialize cellular modem for SMS mode"""
        commands = [
            "AT",           # Test connection
            "AT+CMGF=1",    # Text mode
            "AT+CNMI=2,2",  # Auto-display new messages
            "AT+CPMS=\"SM\"", # Use SIM storage
        ]
        
        for cmd in commands:
            self.modem.write(f"{cmd}\r\n".encode())
            await asyncio.sleep(0.5)
            response = self.modem.read_all().decode()
            if "OK" not in response:
                raise Exception(f"Modem init failed at {cmd}")
    
    async def process_message(self, msg: SMSMessage) -> SMSResponse:
        """Process incoming SMS and generate response"""
        
        # Rate limiting
        if self.check_rate_limit(msg.sender):
            return SMSResponse(msg.sender, 
                ["Rate limit exceeded. Wait 1 minute."])
        
        # Parse command
        parts = msg.body.strip().upper().split()
        if not parts:
            return SMSResponse(msg.sender, ["Invalid command. Text HELP"])
        
        # Check for emergency prefix
        if parts[0] == "911":
            return await self.handle_emergency(parts[1:], msg.sender)
        
        # Check for public commands
        if parts[0] in ["HELP", "INFO"]:
            return await self.handle_public(parts[0], msg.sender)
        
        # Authenticated commands
        auth_code = parts[0] if len(parts) > 0 else ""
        if not self.verify_auth(msg.sender, auth_code):
            # Generate new auth code
            new_code = self.generate_auth_code(msg.sender)
            return SMSResponse(msg.sender, 
                [f"Auth required. Your code: {new_code} (valid 5min)"])
        
        # Process authenticated command
        command = parts[1] if len(parts) > 1 else ""
        params = parts[2:] if len(parts) > 2 else []
        
        return await self.handle_command(command, params, msg.sender)
    
    def verify_auth(self, phone: str, code: str) -> bool:
        """Verify authentication code"""
        if phone not in self.auth_codes:
            return False
            
        stored_code, expiry = self.auth_codes[phone]
        if datetime.now() > expiry:
            del self.auth_codes[phone]
            return False
            
        return stored_code == code
    
    def generate_auth_code(self, phone: str) -> str:
        """Generate time-limited auth code"""
        import random
        code = str(random.randint(1000, 9999))
        expiry = datetime.now() + timedelta(minutes=5)
        self.auth_codes[phone] = (code, expiry)
        return code
    
    async def handle_emergency(self, params: List[str], 
                              sender: str) -> SMSResponse:
        """Handle 911 emergency commands"""
        if not params:
            return SMSResponse(sender, [
                "911 Commands: EXITS, FIRE, AED, EVAC, PEOPLE, SYSTEMS"
            ])
        
        command = params[0]
        
        if command == "EXITS":
            exits = await self.mesh.query("type:emergency_exit")
            return self.format_exit_list(exits, sender)
            
        elif command == "FIRE":
            fire_status = await self.mesh.query("type:fire_alarm OR type:sprinkler")
            return self.format_fire_status(fire_status, sender)
            
        elif command == "AED":
            aeds = await self.mesh.query("type:aed")
            return self.format_aed_locations(aeds, sender)
            
        elif command == "EVAC":
            routes = await self.mesh.get_evacuation_routes()
            return self.format_evac_routes(routes, sender)
            
        elif command == "PEOPLE":
            occupancy = await self.mesh.get_occupancy_estimate()
            return self.format_occupancy(occupancy, sender)
            
        elif command == "SYSTEMS":
            systems = await self.mesh.query("category:critical_system")
            return self.format_systems_status(systems, sender)
            
        else:
            return SMSResponse(sender, [f"Unknown 911 command: {command}"])
    
    async def handle_command(self, command: str, params: List[str], 
                           sender: str) -> SMSResponse:
        """Handle authenticated commands"""
        
        if command == "STATUS":
            room = self.extract_param(params, "room")
            if not room:
                return SMSResponse(sender, ["Usage: STATUS room:127"])
            
            status = await self.mesh.get_room_status(room)
            return self.format_room_status(status, sender)
            
        elif command == "MAP":
            floor = self.extract_param(params, "floor")
            if not floor:
                return SMSResponse(sender, ["Usage: MAP floor:1"])
            
            floor_plan = await self.mesh.get_floor_plan(int(floor))
            return self.format_floor_plan(floor_plan, sender)
            
        elif command == "FIND":
            equipment_type = self.extract_param(params, "type")
            if not equipment_type:
                return SMSResponse(sender, ["Usage: FIND type:outlet"])
            
            results = await self.mesh.query(f"type:{equipment_type}")
            return self.format_search_results(results, sender)
            
        elif command == "QUERY":
            # Direct ArxQL query
            query = " ".join(params)
            results = await self.mesh.query(query)
            return self.format_query_results(results, sender)
            
        else:
            return SMSResponse(sender, [f"Unknown command: {command}"])
    
    def format_floor_plan(self, floor_plan: str, sender: str) -> SMSResponse:
        """Format floor plan for SMS - may require multiple messages"""
        # Compress floor plan to fit SMS
        compressed = self.compress_ascii_plan(floor_plan)
        
        # Split into 160-char chunks
        parts = []
        lines = compressed.split('\n')
        current_part = ""
        
        for line in lines:
            if len(current_part) + len(line) + 1 < 140:  # Leave room for [1/N]
                current_part += line + "\n"
            else:
                parts.append(current_part)
                current_part = line + "\n"
        
        if current_part:
            parts.append(current_part)
        
        # Add part numbers
        total = len(parts)
        numbered_parts = [f"[{i+1}/{total}] {part}" 
                         for i, part in enumerate(parts)]
        
        return SMSResponse(sender, numbered_parts)
    
    def compress_ascii_plan(self, plan: str) -> str:
        """Compress ASCII floor plan for SMS"""
        # Remove unnecessary whitespace
        lines = plan.split('\n')
        compressed = []
        
        for line in lines:
            # Remove leading/trailing spaces
            line = line.strip()
            # Replace multiple spaces with single
            line = re.sub(r'\s+', ' ', line)
            # Shorten room names
            line = line.replace('Room', 'Rm')
            line = line.replace('Office', 'Off')
            line = line.replace('Laboratory', 'Lab')
            compressed.append(line)
        
        return '\n'.join(compressed)
    
    def send_sms(self, response: SMSResponse):
        """Send SMS response via modem"""
        for i, part in enumerate(response.parts):
            # AT command to send SMS
            self.modem.write(f'AT+CMGS="{response.recipient}"\r'.encode())
            time.sleep(0.5)
            self.modem.write(f'{part}\x1A'.encode())  # Ctrl+Z to send
            time.sleep(2)  # Wait between parts
```

### Mesh Interface Bridge

```rust
// src/gateway/mesh_bridge.rs

use crate::core::{ArxObject, MeshNetwork};
use std::collections::HashMap;
use std::time::{Duration, Instant};

pub struct SMSMeshBridge {
    mesh: MeshNetwork,
    cache: ResponseCache,
    emergency_cache: EmergencyCache,
}

impl SMSMeshBridge {
    pub fn new(mesh: MeshNetwork) -> Self {
        Self {
            mesh,
            cache: ResponseCache::new(Duration::from_secs(300)), // 5 min cache
            emergency_cache: EmergencyCache::new(),
        }
    }
    
    pub async fn query(&mut self, arxql: &str) -> Result<Vec<ArxObject>, Error> {
        // Check cache first
        if let Some(cached) = self.cache.get(arxql) {
            return Ok(cached);
        }
        
        // Query mesh network
        let results = self.mesh.query(arxql).await?;
        
        // Cache results
        self.cache.insert(arxql.to_string(), results.clone());
        
        Ok(results)
    }
    
    pub async fn get_room_status(&mut self, room: &str) -> RoomStatus {
        let query = format!("room:{}", room);
        let objects = self.query(&query).await.unwrap_or_default();
        
        RoomStatus {
            room_number: room.to_string(),
            outlets: objects.iter()
                .filter(|o| o.object_type == object_types::OUTLET)
                .count(),
            lights: objects.iter()
                .filter(|o| o.object_type == object_types::LIGHT)
                .count(),
            temperature: self.get_temperature(&objects),
            occupancy: self.get_occupancy(&objects),
            last_update: Instant::now(),
        }
    }
    
    pub async fn get_floor_plan(&mut self, floor: i8) -> String {
        // Get all objects on floor
        let query = format!("floor:{}", floor);
        let objects = self.query(&query).await.unwrap_or_default();
        
        // Generate compact ASCII representation
        self.generate_sms_floor_plan(&objects, floor)
    }
    
    fn generate_sms_floor_plan(&self, objects: &[ArxObject], floor: i8) -> String {
        // Ultra-compact floor plan for SMS
        let mut plan = String::new();
        
        // Find room boundaries
        let rooms = self.extract_rooms(objects);
        
        // Generate grid (very compact)
        let grid_size = 20; // 20x10 characters
        let mut grid = vec![vec![' '; grid_size]; 10];
        
        // Place rooms
        for room in rooms {
            // Simplified room placement
            let x = (room.x / 3000) as usize; // Scale to grid
            let y = (room.y / 3000) as usize;
            
            if x < grid_size && y < 10 {
                // Room number or abbreviated name
                let label = room.number.chars().take(3).collect::<String>();
                for (i, ch) in label.chars().enumerate() {
                    if x + i < grid_size {
                        grid[y][x + i] = ch;
                    }
                }
            }
        }
        
        // Convert grid to string
        plan.push_str(&format!("Floor {}\n", floor));
        for row in grid {
            plan.push_str(&row.iter().collect::<String>());
            plan.push('\n');
        }
        
        plan
    }
    
    pub async fn get_evacuation_routes(&mut self) -> Vec<EvacRoute> {
        // This should be pre-calculated and cached
        if let Some(routes) = self.emergency_cache.get_evac_routes() {
            return routes;
        }
        
        // Calculate evacuation routes
        let exits = self.query("type:emergency_exit").await.unwrap_or_default();
        let routes = self.calculate_evac_routes(&exits);
        
        // Cache for emergency use
        self.emergency_cache.store_evac_routes(routes.clone());
        
        routes
    }
}

// Emergency data cache (persists even if power cycles)
struct EmergencyCache {
    exits: Vec<ArxObject>,
    aed_locations: Vec<ArxObject>,
    evac_routes: Vec<EvacRoute>,
    last_update: Instant,
}

impl EmergencyCache {
    fn new() -> Self {
        // Load from persistent storage if available
        Self::load_from_disk().unwrap_or_else(|| Self {
            exits: Vec::new(),
            aed_locations: Vec::new(),
            evac_routes: Vec::new(),
            last_update: Instant::now(),
        })
    }
    
    fn load_from_disk() -> Option<Self> {
        // Read from /var/cache/arxos/emergency.bin
        std::fs::read("/var/cache/arxos/emergency.bin").ok()
            .and_then(|data| bincode::deserialize(&data).ok())
    }
    
    fn save_to_disk(&self) {
        // Persist to disk for power failure recovery
        if let Ok(data) = bincode::serialize(self) {
            let _ = std::fs::write("/var/cache/arxos/emergency.bin", data);
        }
    }
}
```

## Compression Algorithms

### Text Compression for SMS

```python
class SMSCompressor:
    """Compress building data to fit SMS constraints"""
    
    # Common abbreviations
    ABBREVIATIONS = {
        'Room': 'Rm',
        'Floor': 'Fl',
        'Building': 'Bld',
        'Temperature': 'Temp',
        'Emergency': 'Emrg',
        'Electrical': 'Elec',
        'Available': 'Avail',
        'Occupied': 'Occ',
        'Equipment': 'Equip',
        'Outlet': 'Out',
        'Circuit': 'Ckt',
        'North': 'N',
        'South': 'S',
        'East': 'E',
        'West': 'W',
    }
    
    @staticmethod
    def compress(text: str) -> str:
        """Compress text for SMS transmission"""
        compressed = text
        
        # Apply abbreviations
        for full, abbr in SMSCompressor.ABBREVIATIONS.items():
            compressed = compressed.replace(full, abbr)
            compressed = compressed.replace(full.lower(), abbr.lower())
        
        # Remove unnecessary punctuation
        compressed = compressed.replace(', ', ',')
        compressed = compressed.replace(': ', ':')
        
        # Compress whitespace
        compressed = ' '.join(compressed.split())
        
        # Use symbols where possible
        compressed = compressed.replace(' degrees', '°')
        compressed = compressed.replace(' percent', '%')
        compressed = compressed.replace(' and ', '&')
        
        return compressed
    
    @staticmethod
    def compress_floor_plan(plan: str, max_width: int = 20) -> str:
        """Ultra-compress floor plan for SMS"""
        lines = plan.strip().split('\n')
        compressed = []
        
        for line in lines:
            # Truncate long lines
            if len(line) > max_width:
                line = line[:max_width-1] + '>'
            
            # Replace wall characters with simpler ones
            line = line.replace('═', '=')
            line = line.replace('║', '|')
            line = line.replace('╔', '+')
            line = line.replace('╗', '+')
            line = line.replace('╚', '+')
            line = line.replace('╝', '+')
            
            compressed.append(line)
        
        return '\n'.join(compressed)
```

## Security and Authentication

### Time-Based OTP System

```python
import hmac
import hashlib
import time

class TOTP:
    """Time-based One-Time Password for SMS auth"""
    
    def __init__(self, secret: bytes, interval: int = 300):  # 5 minute windows
        self.secret = secret
        self.interval = interval
    
    def generate(self, phone_number: str) -> str:
        """Generate 4-digit code for phone number"""
        # Current time window
        counter = int(time.time()) // self.interval
        
        # Create message from phone + counter
        message = f"{phone_number}{counter}".encode()
        
        # Generate HMAC
        digest = hmac.new(self.secret, message, hashlib.sha256).digest()
        
        # Extract 4 digits
        offset = digest[-1] & 0x0F
        truncated = digest[offset:offset+4]
        code = int.from_bytes(truncated, 'big') % 10000
        
        return f"{code:04d}"
    
    def verify(self, phone_number: str, code: str, window: int = 1) -> bool:
        """Verify code with time window tolerance"""
        current = self.generate(phone_number)
        if current == code:
            return True
        
        # Check previous/next windows for clock skew
        for i in range(1, window + 1):
            counter = int(time.time()) // self.interval
            
            # Check past
            past_counter = counter - i
            past_message = f"{phone_number}{past_counter}".encode()
            past_digest = hmac.new(self.secret, past_message, hashlib.sha256).digest()
            past_offset = past_digest[-1] & 0x0F
            past_code = int.from_bytes(past_digest[past_offset:past_offset+4], 'big') % 10000
            if f"{past_code:04d}" == code:
                return True
            
            # Check future
            future_counter = counter + i
            future_message = f"{phone_number}{future_counter}".encode()
            future_digest = hmac.new(self.secret, future_message, hashlib.sha256).digest()
            future_offset = future_digest[-1] & 0x0F
            future_code = int.from_bytes(future_digest[future_offset:future_offset+4], 'big') % 10000
            if f"{future_code:04d}" == code:
                return True
        
        return False
```

### Rate Limiting

```python
class RateLimiter:
    """Prevent SMS abuse and cost overruns"""
    
    def __init__(self):
        self.limits = {
            'per_minute': 3,
            'per_hour': 20,
            'per_day': 100,
            'emergency_multiplier': 5,  # 5x for 911 commands
        }
        self.requests = defaultdict(list)
    
    def check_limit(self, phone: str, is_emergency: bool = False) -> bool:
        """Check if phone number has exceeded rate limits"""
        now = datetime.now()
        
        # Clean old entries
        self.requests[phone] = [
            req for req in self.requests[phone]
            if now - req < timedelta(days=1)
        ]
        
        # Count recent requests
        minute_ago = now - timedelta(minutes=1)
        hour_ago = now - timedelta(hours=1)
        
        recent_minute = sum(1 for req in self.requests[phone] if req > minute_ago)
        recent_hour = sum(1 for req in self.requests[phone] if req > hour_ago)
        recent_day = len(self.requests[phone])
        
        # Apply multiplier for emergency
        multiplier = self.limits['emergency_multiplier'] if is_emergency else 1
        
        # Check limits
        if recent_minute >= self.limits['per_minute'] * multiplier:
            return False
        if recent_hour >= self.limits['per_hour'] * multiplier:
            return False
        if recent_day >= self.limits['per_day'] * multiplier:
            return False
        
        # Record this request
        self.requests[phone].append(now)
        return True
```

## Deployment Configuration

### Systemd Service

```ini
# /etc/systemd/system/arxos-sms-gateway.service
[Unit]
Description=Arxos SMS Gateway
After=network.target ModemManager.service

[Service]
Type=simple
User=arxos
Group=dialout
ExecStart=/usr/local/bin/arxos-sms-gateway
Restart=always
RestartSec=10

# Security
PrivateTmp=true
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/cache/arxos /var/log/arxos

[Install]
WantedBy=multi-user.target
```

### Modem Configuration

```bash
#!/bin/bash
# Configure Quectel EC25 modem for SMS gateway

# Set up udev rules for consistent device naming
cat > /etc/udev/rules.d/99-arxos-modem.rules << EOF
SUBSYSTEM=="tty", ATTRS{idVendor}=="2c7c", ATTRS{idProduct}=="0125", SYMLINK+="arxos-modem"
EOF

# Configure ModemManager to ignore our modem
cat > /etc/ModemManager/conf.d/arxos-blacklist.conf << EOF
[ModemManager]
filter-policy=strict
[filter]
subsystems=tty
drivers=option,qmi_wwan
EOF

# Set up PPP for data connection (backup internet)
cat > /etc/ppp/peers/arxos-lte << EOF
/dev/arxos-modem
115200
noauth
defaultroute
usepeerdns
persist
nodetach
EOF
```

## Testing Procedures

### SMS Gateway Test Suite

```python
# tests/test_sms_gateway.py

class TestSMSGateway:
    def test_command_parsing(self):
        """Test various command formats"""
        test_cases = [
            ("HELP", ("HELP", None, [])),
            ("1234 STATUS room:127", ("STATUS", "1234", ["room:127"])),
            ("911 EXITS", ("911", None, ["EXITS"])),
            ("1234 QUERY floor:2 type:outlet", 
             ("QUERY", "1234", ["floor:2", "type:outlet"])),
        ]
        
        for input_msg, expected in test_cases:
            result = parse_sms_command(input_msg)
            assert result == expected
    
    def test_response_splitting(self):
        """Test multi-part message splitting"""
        long_response = "A" * 500  # Longer than 160 chars
        
        parts = split_sms_response(long_response)
        
        assert len(parts) == 4  # Should split into 4 parts
        assert all(len(part) <= 160 for part in parts)
        assert parts[0].startswith("[1/4]")
        assert parts[-1].startswith("[4/4]")
    
    def test_compression(self):
        """Test text compression for SMS"""
        original = "Room 127: Temperature 72 degrees, Occupied, Emergency Exit Available"
        compressed = SMSCompressor.compress(original)
        
        assert len(compressed) < len(original)
        assert "Rm 127" in compressed
        assert "72°" in compressed
        assert "Emrg Exit Avail" in compressed
    
    def test_rate_limiting(self):
        """Test rate limit enforcement"""
        limiter = RateLimiter()
        phone = "+1234567890"
        
        # Should allow first few requests
        for _ in range(3):
            assert limiter.check_limit(phone) == True
        
        # Should block after limit
        assert limiter.check_limit(phone) == False
        
        # Emergency should have higher limit
        for _ in range(10):
            assert limiter.check_limit(phone, is_emergency=True) == True
```

### Load Testing

```bash
#!/bin/bash
# SMS load test using Twilio API

# Send burst of messages
for i in {1..100}; do
    curl -X POST https://api.twilio.com/2010-04-01/Accounts/$ACCOUNT_SID/Messages.json \
        --data-urlencode "Body=1234 STATUS room:$i" \
        --data-urlencode "From=+15551234567" \
        --data-urlencode "To=$GATEWAY_NUMBER" \
        -u $ACCOUNT_SID:$AUTH_TOKEN &
    
    sleep 0.5
done

wait

# Check gateway logs for handling
tail -f /var/log/arxos/sms-gateway.log
```

## Cost Analysis

### Monthly Operating Costs

| Item | Cost | Notes |
|------|------|-------|
| SIM Card | $10 | IoT data plan with SMS |
| SMS Fees | $20 | ~2000 messages/month |
| Power | $2 | 5W continuous |
| **Total** | **$32** | Per building |

### Hardware Costs (One-Time)

| Component | Cost |
|-----------|------|
| Raspberry Pi Zero W | $15 |
| Quectel EC25 Modem | $60 |
| USB adapter cable | $10 |
| SIM card holder | $5 |
| 12V battery backup | $30 |
| Enclosure | $15 |
| **Total** | **$135** |

## Emergency Protocols

### Power Failure Operation

```python
class EmergencyMode:
    """Minimal operation during power failure"""
    
    def __init__(self):
        self.battery_level = 100  # Percentage
        self.low_power_mode = False
        
    def enter_battery_mode(self):
        """Switch to battery power"""
        # Reduce query frequency
        self.query_interval = 60  # seconds
        
        # Cache more aggressively
        self.cache_duration = 3600  # 1 hour
        
        # Disable non-emergency queries
        self.emergency_only = True
        
        # Send notification
        self.send_power_failure_alert()
    
    def monitor_battery(self):
        """Monitor battery and adjust operation"""
        if self.battery_level < 20:
            self.low_power_mode = True
            # Only respond to 911 commands
            self.accepted_commands = ["911"]
            
        if self.battery_level < 5:
            # Final emergency broadcast
            self.send_final_status_broadcast()
            self.shutdown_gracefully()
```

## Conclusion

The SMS Gateway provides universal building access through the most widely available communication medium - text messaging. By implementing intelligent compression, caching, and emergency protocols, the system ensures critical building information remains accessible even when all other systems fail. 

The gateway operates completely offline from the internet, maintaining Arxos's air-gapped security model while providing a vital lifeline during emergencies.