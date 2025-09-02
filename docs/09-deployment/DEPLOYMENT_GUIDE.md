# ArxOS Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying ArxOS building intelligence networks. The deployment maintains complete air-gap security while providing powerful building intelligence capabilities.

## Deployment Principles

### Air-Gap Compliance
- **No Internet:** System never connects to internet
- **Local Mesh Only:** All communication via LoRa/Bluetooth
- **Physical Isolation:** Complete separation from internet infrastructure
- **Encrypted Communication:** All mesh traffic encrypted

### Terminal-Only Interface
- **CLI Primary:** Terminal interface for all users
- **ASCII Visualization:** Building data as ASCII art
- **Mobile Terminal:** Terminal + LiDAR on mobile devices
- **No Web UI:** No web interfaces or SSH

## Hardware Requirements

### Mesh Nodes (ESP32)
- **ESP32-S3:** Main processing unit
- **LoRa Radio:** SX1262 or SX1276
- **Antenna:** 915MHz (US) or 868MHz (EU)
- **Power:** Solar panel + battery
- **Storage:** 4MB flash memory
- **Cost:** $25-85 per node

### User Devices
- **Desktop/Laptop:** USB LoRa dongle
- **Mobile:** iPhone with LiDAR (iPhone 12 Pro+)
- **Bluetooth:** Standard Bluetooth 5.0+

### Network Infrastructure
- **Mesh Nodes:** 1 per room/area
- **Gateway Node:** 1 per building
- **District Gateway:** 1 per district
- **No Internet:** No internet connectivity required

## Deployment Architecture

### Building-Level Deployment
```
┌─────────────────────────────────────────────────────────────────┐
│                    BUILDING INTELLIGENCE NETWORK               │
├─────────────────────────────────────────────────────────────────┤
│  Gateway Node (ESP32) - Building coordinator                   │
│  ├── LoRa Mesh (915MHz) - Building-to-building communication   │
│  ├── Bluetooth - Local device connections                      │
│  ├── Database - Local building intelligence storage            │
│  └── Terminal Interface - Command-line access                  │
├─────────────────────────────────────────────────────────────────┤
│  Room-Level Nodes (ESP32) - Local intelligence                 │
│  ├── Outlet Nodes - Electrical monitoring/control              │
│  ├── Sensor Nodes - Environmental monitoring                   │
│  ├── Door Nodes - Access control and monitoring                │
│  └── Panel Nodes - Electrical panel monitoring                 │
├─────────────────────────────────────────────────────────────────┤
│  User Devices - Field interaction                              │
│  ├── Desktop/Laptop - Terminal interface                       │
│  ├── Mobile Devices - Terminal + LiDAR scanning                │
│  └── LoRa Dongles - Direct mesh connection                     │
└─────────────────────────────────────────────────────────────────┘
```

### District-Level Deployment
```
┌─────────────────────────────────────────────────────────────────┐
│                    SCHOOL DISTRICT NETWORK                     │
├─────────────────────────────────────────────────────────────────┤
│  District Gateway - Inter-building coordination                │
│  ├── High-power LoRa - District-wide communication             │
│  ├── Building Gateways - Individual building networks          │
│  └── District Database - Cross-building intelligence           │
├─────────────────────────────────────────────────────────────────┤
│  Building Networks - Individual building intelligence           │
│  ├── Building A - Complete building network                    │
│  ├── Building B - Complete building network                    │
│  └── Building C - Complete building network                    │
└─────────────────────────────────────────────────────────────────┘
```

## Step-by-Step Deployment

### Phase 1: Planning and Preparation

#### 1.1 Site Assessment
```bash
# Survey building layout
arxos survey building --floor-plan
arxos survey building --electrical-systems
arxos survey building --hvac-systems
arxos survey building --network-coverage
```

#### 1.2 Node Placement Planning
- **Room Coverage:** 1 node per room/area
- **Signal Strength:** Ensure LoRa coverage
- **Power Access:** Solar panel placement
- **Security:** Secure mounting locations

#### 1.3 Hardware Procurement
- **ESP32 Nodes:** Calculate required quantity
- **LoRa Radios:** SX1262 or SX1276
- **Antennas:** 915MHz (US) or 868MHz (EU)
- **Solar Panels:** 5W panels with batteries
- **USB Dongles:** For user devices

### Phase 2: Hardware Installation

#### 2.1 Gateway Node Installation
```bash
# Install gateway node
arxos install gateway --building-id 0x0001
arxos configure gateway --frequency 915.0
arxos configure gateway --power 14
arxos start gateway
```

#### 2.2 Room Node Installation
```bash
# Install room nodes
arxos install node --room 205 --node-id 0x0002
arxos install node --room 206 --node-id 0x0003
arxos install node --room 207 --node-id 0x0004
```

#### 2.3 Network Formation
```bash
# Form mesh network
arxos mesh discover
arxos mesh connect
arxos mesh status
```

### Phase 3: Software Configuration

#### 3.1 Firmware Installation
```bash
# Flash ESP32 firmware
arxos flash firmware --node-id 0x0001
arxos flash firmware --node-id 0x0002
arxos flash firmware --node-id 0x0003
```

#### 3.2 Network Configuration
```bash
# Configure mesh network
arxos config mesh --frequency 915.0
arxos config mesh --power 14
arxos config mesh --encryption-key <key>
arxos config mesh --timeout 30
```

#### 3.3 Database Setup
```bash
# Initialize building database
arxos db init --building-id 0x0001
arxos db schema --electrical
arxos db schema --hvac
arxos db schema --plumbing
```

### Phase 4: User Device Setup

#### 4.1 Desktop Terminal Setup
```bash
# Install ArxOS terminal
cargo install arxos-terminal

# Connect to mesh network
arxos connect /dev/ttyUSB0
arxos status
```

#### 4.2 Mobile App Setup
```bash
# Install mobile app
# Download from App Store
# Connect via Bluetooth
arxos connect bluetooth://meshtastic-001
```

#### 4.3 USB Dongle Setup
```bash
# Install USB LoRa dongle
arxos install dongle --device /dev/ttyUSB0
arxos configure dongle --frequency 915.0
arxos test dongle
```

### Phase 5: Testing and Validation

#### 5.1 Network Testing
```bash
# Test mesh connectivity
arxos test mesh --ping-all
arxos test mesh --routing
arxos test mesh --performance
```

#### 5.2 Query Testing
```bash
# Test building queries
arxos query "outlets room:205"
arxos query "equipment type:hvac"
arxos query "emergency exits"
```

#### 5.3 LiDAR Testing
```bash
# Test LiDAR scanning
arxos scan start
arxos scan room:205
arxos scan stop
```

## Configuration Management

### Network Configuration
```bash
# Mesh network settings
arxos config mesh frequency 915.0
arxos config mesh power 14
arxos config mesh encryption-key <key>
arxos config mesh timeout 30
arxos config mesh retry-count 3
```

### Node Configuration
```bash
# Individual node settings
arxos config node --id 0x0001 --role gateway
arxos config node --id 0x0002 --role room
arxos config node --id 0x0003 --role sensor
```

### Security Configuration
```bash
# Security settings
arxos config security --encryption aes-256
arxos config security --key-rotation 30
arxos config security --audit-logging on
```

## Monitoring and Maintenance

### Network Monitoring
```bash
# Monitor mesh network
arxos monitor mesh --status
arxos monitor mesh --performance
arxos monitor mesh --errors
```

### Node Health
```bash
# Check node health
arxos health node --id 0x0001
arxos health node --all
arxos health battery --all
```

### Database Maintenance
```bash
# Database maintenance
arxos db backup --building-id 0x0001
arxos db optimize --building-id 0x0001
arxos db cleanup --building-id 0x0001
```

## Troubleshooting

### Common Issues

#### Connection Problems
```bash
# Check USB dongle connection
arxos diagnose usb --device /dev/ttyUSB0
arxos diagnose bluetooth --device meshtastic-001
```

#### Mesh Network Issues
```bash
# Diagnose mesh network
arxos diagnose mesh --connectivity
arxos diagnose mesh --routing
arxos diagnose mesh --performance
```

#### Node Problems
```bash
# Diagnose node issues
arxos diagnose node --id 0x0001
arxos diagnose node --power
arxos diagnose node --signal
```

### Error Recovery
```bash
# Reset network
arxos reset mesh --force
arxos reset node --id 0x0001
arxos reset database --building-id 0x0001
```

## Security Considerations

### Physical Security
- **Node Placement:** Secure mounting locations
- **Access Control:** Physical access restrictions
- **Tamper Detection:** Monitor for tampering
- **Backup Systems:** Redundant nodes

### Network Security
- **Encryption:** AES-256 encryption
- **Authentication:** Node ID verification
- **Access Control:** Authorized users only
- **Audit Logging:** Complete activity logs

### Data Security
- **Local Storage:** No cloud storage
- **Encryption:** All data encrypted
- **Access Control:** User permissions
- **Backup:** Local backup only

## Performance Optimization

### Network Optimization
```bash
# Optimize mesh network
arxos optimize mesh --frequency 915.0
arxos optimize mesh --power 14
arxos optimize mesh --routing
```

### Database Optimization
```bash
# Optimize database
arxos optimize db --indexes
arxos optimize db --queries
arxos optimize db --storage
```

### Power Optimization
```bash
# Optimize power usage
arxos optimize power --sleep-mode
arxos optimize power --transmission
arxos optimize power --processing
```

## Scaling and Expansion

### Multi-Building Deployment
```bash
# Deploy to multiple buildings
arxos deploy building --id 0x0001
arxos deploy building --id 0x0002
arxos deploy building --id 0x0003
```

### District-Wide Deployment
```bash
# Deploy district gateway
arxos deploy district --gateway 0x1000
arxos deploy district --buildings 0x0001,0x0002,0x0003
```

### Network Expansion
```bash
# Add new nodes
arxos add node --room 208 --node-id 0x0005
arxos add node --room 209 --node-id 0x0006
arxos mesh update
```

## Conclusion

ArxOS deployment provides a robust, secure, and scalable building intelligence network. The air-gapped architecture ensures complete security while the terminal-only interface provides powerful building intelligence capabilities.

The deployment process is straightforward and can be scaled from single buildings to entire districts while maintaining complete air-gap compliance.
