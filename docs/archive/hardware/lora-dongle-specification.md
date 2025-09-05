# LoRa USB-C Dongle Hardware Specification
**Version:** 1.0  
**Date:** August 31, 2025  
**Target Cost:** $25-35

## Overview

The Arxos LoRa dongle provides mobile devices with direct access to building mesh networks without internet connectivity. This specification defines the hardware, firmware, and manufacturing requirements for a USB-C dongle that works with iOS and Android devices.

## Hardware Architecture

### Block Diagram

```
┌──────────────────────────────────────────────────────────┐
│                    USB-C CONNECTOR                        │
│                         Type-C                            │
└────────────────────┬───────────────┬─────────────────────┘
                     │               │
              ┌──────▼──────┐ ┌──────▼──────┐
              │   Power     │ │    USB      │
              │ Management  │ │   2.0 FS    │
              │   3.3V LDO  │ │  Interface  │
              └──────┬──────┘ └──────┬──────┘
                     │               │
         ┌───────────▼───────────────▼───────────┐
         │        SAMD21G18A MCU                 │
         │   - 48MHz ARM Cortex-M0+              │
         │   - 256KB Flash / 32KB RAM            │
         │   - USB Device Controller              │
         │   - SPI/I2C/UART interfaces           │
         └──────┬────────────┬──────────┬────────┘
                │            │          │
         ┌──────▼──────┐     │   ┌──────▼──────┐
         │  Status LED │     │   │  TCXO       │
         │   RGB/WS2812│     │   │  32MHz      │
         └─────────────┘     │   └─────────────┘
                             │
                    ┌────────▼────────┐
                    │  SX1262 LoRa    │
                    │   Transceiver   │
                    │  +22dBm TX      │
                    │  -148dBm RX     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  RF Front End   │
                    │  - Balun        │
                    │  - SAW Filter   │
                    │  - RF Switch    │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Chip Antenna   │
                    │  2dBi Ceramic   │
                    └─────────────────┘
```

### Component Selection

#### Microcontroller: SAMD21G18A
- **Core**: ARM Cortex-M0+ @ 48MHz
- **Memory**: 256KB Flash, 32KB SRAM
- **USB**: Native USB 2.0 Full Speed
- **Interfaces**: SERCOM (SPI for SX1262)
- **Power**: 3.3V, 4mA active, 2μA standby
- **Package**: QFN48 (7x7mm)
- **Cost**: $2.50

#### LoRa Transceiver: SX1262
- **Frequency**: 150-960 MHz (software selectable)
- **TX Power**: +22dBm max
- **RX Sensitivity**: -148dBm @ SF12 BW=125kHz
- **Current**: TX: 118mA @ +22dBm, RX: 5mA
- **Interface**: SPI up to 16MHz
- **Package**: QFN24 (4x4mm)
- **Cost**: $4.50

#### Power Management: AP2112K-3.3
- **Input**: 5V from USB-C
- **Output**: 3.3V @ 600mA
- **Dropout**: 250mV typical
- **Protection**: Over-current, thermal
- **Package**: SOT23-5
- **Cost**: $0.30

#### Antenna: Johanson 0915AT43A0026
- **Frequency**: 915MHz (US version)
- **Gain**: 2dBi
- **Type**: Ceramic chip antenna
- **Size**: 10x3x1.2mm
- **Cost**: $1.50

### PCB Design

```
Top Layer (Component Side):
┌─────────────────────────────────────┐
│  USB-C   ┌─────┐  ┌──────┐         │ 25mm
│   ═══    │SAMD │  │SX1262│  ┌───┐  │
│          │ 21  │  │      │  │ANT│  │
│  ●LED    └─────┘  └──────┘  └───┘  │
└─────────────────────────────────────┘
                  15mm

Bottom Layer (Ground Plane):
┌─────────────────────────────────────┐
│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
│░░░░░░░░ Ground Fill ░░░░░░░░░░░░░░░│
│░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
└─────────────────────────────────────┘

Stack-up (4-layer):
1. Top - Signal/Components
2. Ground Plane
3. Power Plane (3.3V)
4. Bottom - Signal/Ground
```

#### Design Rules
- **Trace Width**: 0.2mm minimum
- **Via Size**: 0.3mm drill, 0.5mm pad
- **Clearance**: 0.15mm
- **RF Trace**: 50Ω impedance controlled
- **Crystal**: Keep-out zone 5mm radius

### Enclosure Design

```
Material: Aluminum 6061-T6 (RF shielding)
Finish: Black anodized
Dimensions: 28 x 17 x 9mm (with USB-C plug)

┌─────────────────────────────┐
│  ╔═══════════════════════╗  │
│  ║   ARXOS MESH          ║  │ Top View
│  ║   ● LED               ║  │
│  ╚═══════════════════════╝  │
└─────────────────────────────┘

├─────────────────────────────┤
│▓▓▓│                         │ Side View
│USB│      Aluminum Body      │ 9mm
│▓▓▓│                         │
└─────────────────────────────┘
```

## Firmware Architecture

### Memory Map

```
Flash Memory Layout (256KB):
0x00000000 ┌─────────────────┐
           │   Bootloader    │ 8KB
0x00002000 ├─────────────────┤
           │   Application   │ 200KB
0x00034000 ├─────────────────┤
           │   Config Data   │ 16KB
0x00038000 ├─────────────────┤
           │   Crypto Keys   │ 8KB
0x0003A000 ├─────────────────┤
           │   Reserved      │ 24KB
0x00040000 └─────────────────┘

SRAM Layout (32KB):
0x20000000 ┌─────────────────┐
           │   Stack         │ 4KB
0x20001000 ├─────────────────┤
           │   Heap          │ 8KB
0x20003000 ├─────────────────┤
           │   LoRa Buffers  │ 8KB
0x20005000 ├─────────────────┤
           │   USB Buffers   │ 4KB
0x20006000 ├─────────────────┤
           │   Runtime Data  │ 8KB
0x20008000 └─────────────────┘
```

### USB Descriptors

```c
// USB Device Descriptor
const USB_DeviceDescriptor device_descriptor = {
    .bLength = 18,
    .bDescriptorType = USB_DESC_DEVICE,
    .bcdUSB = 0x0200,          // USB 2.0
    .bDeviceClass = 0x02,      // CDC Class
    .bDeviceSubClass = 0x00,
    .bDeviceProtocol = 0x00,
    .bMaxPacketSize = 64,
    .idVendor = 0x16C0,        // Arxos VID
    .idProduct = 0x05E1,       // LoRa Dongle PID
    .bcdDevice = 0x0100,       // Version 1.0
    .iManufacturer = 1,        // "Arxos"
    .iProduct = 2,             // "LoRa Mesh Dongle"
    .iSerialNumber = 3,        // Unique serial
    .bNumConfigurations = 1
};

// CDC ACM Configuration for Serial Port Emulation
const USB_ConfigDescriptor config_descriptor = {
    .bLength = 9,
    .bDescriptorType = USB_DESC_CONFIGURATION,
    .wTotalLength = 67,
    .bNumInterfaces = 2,       // CDC requires 2 interfaces
    .bConfigurationValue = 1,
    .iConfiguration = 0,
    .bmAttributes = 0x80,      // Bus powered
    .bMaxPower = 50            // 100mA
};
```

### LoRa Configuration

```c
// Regional frequency plans
typedef struct {
    uint32_t frequency;
    uint8_t max_power;
    uint8_t channels[8];
} RegionalParams;

const RegionalParams regions[] = {
    // US915
    {
        .frequency = 915000000,
        .max_power = 20,  // dBm
        .channels = {902.3, 902.5, 902.7, 902.9, 903.1, 903.3, 903.5, 903.7}
    },
    // EU868
    {
        .frequency = 868000000,
        .max_power = 14,  // dBm
        .channels = {868.1, 868.3, 868.5, 0, 0, 0, 0, 0}
    },
    // AS923
    {
        .frequency = 923000000,
        .max_power = 16,  // dBm
        .channels = {923.2, 923.4, 0, 0, 0, 0, 0, 0}
    }
};

// Adaptive Data Rate settings
const LoRaSettings adr_table[] = {
    // DR, SF, BW, Max Payload
    {0, 12, 125, 51},   // Longest range
    {1, 11, 125, 51},
    {2, 10, 125, 51},
    {3, 9,  125, 115},
    {4, 8,  125, 222},
    {5, 7,  125, 222},  // Fastest
};
```

## Manufacturing Requirements

### PCB Fabrication

```yaml
PCB Specification:
  layers: 4
  thickness: 1.6mm
  material: FR-4
  copper_weight: 1oz
  surface_finish: ENIG
  solder_mask: Black
  silkscreen: White
  min_trace: 0.15mm
  min_via: 0.3mm
  impedance_control: 50Ω ±10%
```

### Assembly Process

```
1. SMT Assembly
   - Solder paste: SAC305 lead-free
   - Stencil thickness: 0.12mm
   - Placement accuracy: ±0.05mm
   - Reflow profile: JEDEC J-STD-020

2. Testing Sequence
   - In-circuit test (ICT)
   - Boundary scan (JTAG)
   - Functional test
   - RF calibration
   - Final QC

3. Programming
   - Flash bootloader via SWD
   - Program application firmware
   - Write unique serial number
   - Calibrate RF parameters
```

### Bill of Materials

| Component | Part Number | Qty | Unit Cost | Extended |
|-----------|------------|-----|-----------|----------|
| MCU | ATSAMD21G18A-AU | 1 | $2.50 | $2.50 |
| LoRa | SX1262IMLT-T | 1 | $4.50 | $4.50 |
| LDO | AP2112K-3.3TRG1 | 1 | $0.30 | $0.30 |
| USB-C | TYPE-C-31-M-12 | 1 | $0.50 | $0.50 |
| TCXO | DSC1001CI5-032.0000 | 1 | $1.20 | $1.20 |
| Antenna | 0915AT43A0026 | 1 | $1.50 | $1.50 |
| LED | WS2812B-MINI | 1 | $0.15 | $0.15 |
| Capacitors | Various | 15 | $0.02 | $0.30 |
| Resistors | Various | 10 | $0.01 | $0.10 |
| Inductors | Various | 3 | $0.10 | $0.30 |
| RF Switch | BGS12AL7-4 | 1 | $0.40 | $0.40 |
| Balun | 0896BM15A0001 | 1 | $0.35 | $0.35 |
| PCB | 4-layer | 1 | $2.00 | $2.00 |
| Assembly | - | 1 | $3.00 | $3.00 |
| Enclosure | Aluminum CNC | 1 | $4.00 | $4.00 |
| **Total** | | | | **$21.10** |

*Note: Pricing based on 1000-unit quantities*

## Certification Requirements

### FCC Part 15 (USA)
- Intentional radiator certification
- Maximum conducted power: +20dBm
- Spurious emissions: <-36dBm
- Test standard: FCC Part 15.247

### CE RED (Europe)
- Radio Equipment Directive 2014/53/EU
- EN 300 220 (Short Range Devices)
- EN 301 489 (EMC)
- EN 60950 (Safety)

### IC RSS-247 (Canada)
- Industry Canada certification
- Similar to FCC requirements
- French labeling required

## Quality Assurance

### Manufacturing Tests

```python
# Production test script
def test_dongle(serial_port):
    tests = []
    
    # USB enumeration test
    tests.append(test_usb_enumeration())
    
    # Firmware version check
    tests.append(test_firmware_version("1.0.0"))
    
    # LoRa TX power calibration
    tests.append(calibrate_tx_power(target=20))  # dBm
    
    # LoRa RX sensitivity test
    tests.append(test_rx_sensitivity(limit=-140))  # dBm
    
    # Frequency accuracy
    tests.append(test_frequency_accuracy(tolerance=10))  # ppm
    
    # Current consumption
    tests.append(test_current_draw(idle=5, tx=120))  # mA
    
    # LED functionality
    tests.append(test_rgb_led())
    
    # Environmental stress
    tests.append(test_temperature_range(-20, 70))  # °C
    
    return all(tests)
```

### Reliability Standards

- MTBF: >50,000 hours
- Operating temperature: -20°C to +70°C
- Storage temperature: -40°C to +85°C
- Humidity: 5% to 95% non-condensing
- ESD protection: ±8kV contact, ±15kV air
- Drop test: 1.5m onto concrete
- Insertion cycles: >10,000

## Firmware Update Process

### OTA Update via USB

```
1. Device enters DFU mode (hold button on insert)
2. Host sends new firmware image
3. Bootloader validates signature
4. Flash new application
5. Reboot with new firmware

Security:
- Ed25519 signature verification
- Anti-rollback version check
- Encrypted firmware option
- Secure bootloader
```

## Conclusion

This LoRa USB-C dongle design provides a compact, cost-effective solution for air-gapped building access. At approximately $21 in materials (volume pricing) plus $4-9 in assembly and testing, the target retail price of $35 is achievable while maintaining quality and performance standards.

The combination of SAMD21 MCU and SX1262 transceiver provides excellent range and battery life while remaining compatible with both iOS and Android devices through standard USB CDC drivers.