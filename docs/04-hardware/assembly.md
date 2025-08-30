# DIY Assembly Guide

## Build Your First Node in 30 Minutes

### Tools Needed
- Soldering iron (optional)
- Wire strippers
- Screwdriver
- Multimeter (helpful)

### Step 1: Prepare Components
```
☐ ESP32 board
☐ LoRa module
☐ Antenna
☐ Jumper wires
☐ Power supply
☐ Breadboard (for testing)
```

### Step 2: Connect LoRa to ESP32
```
LoRa → ESP32
━━━━━━━━━━━━━
VCC  → 3.3V
GND  → GND
SCK  → GPIO 5
MISO → GPIO 19
MOSI → GPIO 27
CS   → GPIO 18
RST  → GPIO 14
IRQ  → GPIO 26
```

### Step 3: Add Sensors/Relays
```
Relay Module:
VCC → 5V
GND → GND
IN  → GPIO 32

Temperature Sensor:
VCC → 3.3V
GND → GND
SDA → GPIO 21
SCL → GPIO 22
```

### Step 4: Flash Firmware
1. Download Arduino IDE
2. Install ESP32 board support
3. Open ArxOS sketch
4. Select your board
5. Click Upload

### Step 5: Test & Deploy
```bash
# Serial monitor shows:
ArxOS Node Starting...
Joining mesh network...
Node ID: 0x4A7B
BILT Wallet: Ready
Status: ONLINE

# You're earning BILT!
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Won't upload | Check USB cable, install drivers |
| No mesh connection | Check antenna, move near window |
| Relay won't switch | Check 5V power, GPIO connection |

### Enclosure Options

#### 3D Printed
- Download STL files
- PLA or PETG material
- Snap-fit design
- Cost: $2

#### Commercial
- IP65 junction box
- Cable glands
- DIN rail mount
- Cost: $10

### Pro Tips

1. **Test on breadboard first**
2. **Use quality jumper wires**
3. **Add status LEDs**
4. **Label everything**
5. **Document your build**

### Share Your Build

Post your build on Discord:
- Photos of your node
- Unique features
- Lessons learned
- BILT earned

Top builds featured monthly!

---

→ Next: [Terminal Interface](../05-terminal/)