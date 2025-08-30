# Node Type Catalog

## Every Building Component as a Smart Node

### Electrical Nodes

#### Outlet Controller Node
```yaml
Function: Control and monitor outlets
Hardware:
  - ESP32 + LoRa
  - 20A relay
  - Current sensor (ACS712)
  - Status LED
Cost: $35
BILT Reward: 25 per outlet
Complexity: ⭐⭐ (Easy)
```

#### Breaker Monitor Node
```yaml
Function: Monitor electrical panel
Hardware:
  - ESP32 + LoRa
  - Current transformers (CT)
  - Voltage divider
  - SD card logging
Cost: $65
BILT Reward: 100 per panel
Complexity: ⭐⭐⭐⭐ (Advanced)
```

### Environmental Nodes

#### Climate Sensor Node
```yaml
Function: Temperature, humidity, CO2
Hardware:
  - ESP32 + LoRa
  - BME280 sensor
  - MH-Z19 CO2 sensor
  - OLED display
Cost: $45
BILT Reward: 20 per room
Complexity: ⭐⭐ (Easy)
```

#### Air Quality Node
```yaml
Function: Comprehensive air monitoring
Hardware:
  - ESP32 + LoRa
  - PM2.5/PM10 sensor
  - VOC sensor
  - CO2 sensor
Cost: $85
BILT Reward: 50 per zone
Complexity: ⭐⭐⭐ (Moderate)
```

### Security Nodes

#### Door Monitor Node
```yaml
Function: Door status and access
Hardware:
  - ESP32 + LoRa
  - Reed switch
  - RFID reader (optional)
  - Buzzer
Cost: $30
BILT Reward: 20 per door
Complexity: ⭐⭐ (Easy)
```

### Special Nodes

#### Mobile Scanner Node
```yaml
Function: Portable building mapper
Hardware:
  - ESP32 + LoRa
  - LiDAR sensor
  - IMU for position
  - Battery pack
  - Phone mount
Cost: $125
BILT Reward: 100 per new area
Complexity: ⭐⭐⭐⭐⭐ (Expert)
```

#### Gateway Node
```yaml
Function: Building mesh coordinator
Hardware:
  - ESP32 + LoRa
  - External antenna
  - Ethernet (optional)
  - SD card
  - RTC
Cost: $75
BILT Reward: 200 per building
Complexity: ⭐⭐⭐ (Moderate)
```

---

→ Next: [Assembly Guide](assembly.md)