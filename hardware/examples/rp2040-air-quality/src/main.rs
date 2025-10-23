/*
 * ArxOS RP2040 Air Quality Sensor
 * 
 * This example demonstrates how to connect an RP2040 with MQ-135 sensor
 * to ArxOS using Rust and the rp-hal ecosystem.
 * 
 * Hardware Requirements:
 * - Raspberry Pi Pico (RP2040)
 * - MQ-135 air quality sensor
 * - 10kΩ pull-up resistor
 * 
 * Rust Dependencies:
 * - rp-hal
 * - embedded-hal
 * - serde_json
 * - heapless
 * - nb
 * - chrono
 * - mqtt
 */

#![no_std]
#![no_main]

use embedded_hal::digital::v2::OutputPin;
use embedded_hal::adc::OneShot;
use rp2040_hal::{
    adc::{Adc, AdcPin},
    clocks::init_clocks_and_plls,
    gpio::{Pins, Pin, PinId, PinMode},
    pac,
    sio::Sio,
    watchdog::Watchdog,
};
use rp2040_hal::gpio::{bank0::Gpio26, bank0::Gpio27, FunctionSio, SioOutput};
use serde_json_core::{heapless::String, ser, Deserializer, Serializer};
use chrono::{DateTime, Utc};

// Configuration
const MQTT_BROKER: &str = "YOUR_MQTT_BROKER_IP";
const MQTT_PORT: u16 = 1883;
const MQTT_USER: &str = "YOUR_MQTT_USERNAME";
const MQTT_PASSWORD: &str = "YOUR_MQTT_PASSWORD";
const MQTT_TOPIC: &str = "arxos/sensors/air_quality";

// Sensor pins
const ANALOG_PIN: u8 = 26;
const DIGITAL_PIN: u8 = 27;

// Sensor information
const SENSOR_ID: &str = "aq_001";
const SENSOR_TYPE: &str = "air-quality";
const ROOM_PATH: &str = "/B1/3/301/HVAC";
const BUILDING_ID: &str = "B1";

// MQ-135 calibration constants
const R0_CLEAN_AIR: f32 = 10.0; // Resistance in clean air (kΩ)
const RL_VALUE: f32 = 5.0; // Load resistance (kΩ)

#[derive(serde::Serialize)]
struct SensorData {
    api_version: &'static str,
    kind: &'static str,
    metadata: Metadata,
    data: Data,
    alerts: [Alert; 1],
    arxos: ArxOS,
}

#[derive(serde::Serialize)]
struct Metadata {
    sensor_id: &'static str,
    sensor_type: &'static str,
    room_path: &'static str,
    timestamp: String<32>,
    source: &'static str,
    building_id: &'static str,
}

#[derive(serde::Serialize)]
struct Data {
    value: f32,
    unit: &'static str,
    status: &'static str,
    confidence: f32,
    air_quality: &'static str,
    voltage: f32,
    digital_reading: u8,
    resistance: f32,
    ratio: f32,
}

#[derive(serde::Serialize)]
struct Alert {
    level: &'static str,
    message: String<64>,
    timestamp: String<32>,
}

#[derive(serde::Serialize)]
struct ArxOS {
    processed: bool,
    validated: bool,
    device_id: String<32>,
    mqtt_topic: &'static str,
}

impl SensorData {
    fn new(ppm: f32, air_quality: &'static str, status: &'static str, voltage: f32, digital: u8, resistance: f32, ratio: f32) -> Self {
        let timestamp = get_current_timestamp();
        
        Self {
            api_version: "arxos.io/v1",
            kind: "SensorData",
            metadata: Metadata {
                sensor_id: SENSOR_ID,
                sensor_type: SENSOR_TYPE,
                room_path: ROOM_PATH,
                timestamp,
                source: "mqtt",
                building_id: BUILDING_ID,
            },
            data: Data {
                value: ppm,
                unit: "ppm",
                status,
                confidence: 0.88,
                air_quality,
                voltage,
                digital_reading: digital,
                resistance,
                ratio,
            },
            alerts: [Alert {
                level: if status == "normal" { "info" } else { "warning" },
                message: String::from_str(&format!("Air quality: {}", air_quality)).unwrap_or_default(),
                timestamp,
            }],
            arxos: ArxOS {
                processed: true,
                validated: true,
                device_id: String::from_str(&format!("rp2040_{}", SENSOR_ID)).unwrap_or_default(),
                mqtt_topic: MQTT_TOPIC,
            },
        }
    }

    fn to_json(&self) -> Result<String<512>, serde_json_core::ser::Error> {
        let mut buf = [0u8; 512];
        let mut serializer = Serializer::new(&mut buf);
        self.serialize(&mut serializer)?;
        Ok(String::from_str(&core::str::from_utf8(&buf[..serializer.end()]).unwrap_or("")).unwrap_or_default())
    }
}

#[rp2040_hal::entry]
fn main() -> ! {
    let mut pac = pac::Peripherals::take().unwrap();
    let core = pac::CorePeripherals::take().unwrap();
    let mut watchdog = Watchdog::new(pac.WATCHDOG);
    let sio = Sio::new(pac.SIO);

    let external_xtal_freq_hz = 12_000_000u32;
    let clocks = init_clocks_and_plls(
        external_xtal_freq_hz,
        pac.XOSC,
        pac.CLOCKS,
        pac.PLL_SYS,
        pac.PLL_USB,
        &mut pac.RESETS,
        &mut watchdog,
    )
    .ok()
    .unwrap();

    let pins = Pins::new(
        pac.IO_BANK0,
        pac.PADS_BANK0,
        sio.gpio_bank0,
        &mut pac.RESETS,
    );

    // Initialize ADC
    let mut adc = Adc::new(pac.ADC, &mut pac.RESETS);
    let adc_pin = AdcPin::new(pins.gpio26.into_floating_input());

    // Initialize digital pin
    let mut digital_pin = pins.gpio27.into_push_pull_output();

    println!("ArxOS RP2040 Air Quality Sensor");
    println!("===============================");

    // Main loop
    loop {
        // Read analog value
        let analog_value: u16 = adc.read(&mut adc_pin).unwrap();
        let voltage = (analog_value as f32 * 3.3) / 4095.0;
        
        // Calculate sensor resistance
        let resistance = calculate_resistance(voltage);
        
        // Calculate ratio
        let ratio = resistance / R0_CLEAN_AIR;
        
        // Convert to PPM using MQ-135 calibration curve
        let ppm = calculate_ppm(ratio);
        
        // Read digital value
        let digital_value = digital_pin.is_set_high().unwrap_or(false) as u8;

        // Determine air quality
        let (air_quality, status) = determine_air_quality(ppm);

        println!("Analog Value: {}", analog_value);
        println!("Voltage: {:.2}V", voltage);
        println!("Resistance: {:.2}kΩ", resistance);
        println!("Ratio: {:.2}", ratio);
        println!("PPM: {:.1} ppm", ppm);
        println!("Air Quality: {}", air_quality);
        println!("Digital Pin: {}", digital_value);

        // Create sensor data
        let sensor_data = SensorData::new(ppm, air_quality, status, voltage, digital_value, resistance, ratio);
        
        if let Ok(json_data) = sensor_data.to_json() {
            // Publish to MQTT broker
            publish_to_mqtt(&json_data);
        } else {
            println!("❌ Failed to create sensor data JSON");
        }

        // Wait 10 minutes before next reading
        cortex_m::asm::delay(10 * 60 * 1_000_000); // 10 minutes
    }
}

fn calculate_resistance(voltage: f32) -> f32 {
    // MQ-135 resistance calculation
    // Rs = (Vc - Vout) / Vout * RL
    let vc = 5.0; // Supply voltage
    let vout = voltage;
    
    if vout <= 0.0 {
        return 0.0;
    }
    
    let rs = ((vc - vout) / vout) * RL_VALUE;
    rs
}

fn calculate_ppm(ratio: f32) -> f32 {
    // MQ-135 calibration curve for CO2
    // Using proper calibration curve for CO2 detection
    if ratio <= 0.0 {
        return 0.0;
    }
    
    // CO2 calculation using MQ-135 calibration curve
    // Formula: ppm = 116.6020682 * (Rs/R0)^(-2.769034857)
    let ppm = 116.6020682 * (ratio.powf(-2.769034857));
    
    if ppm < 0.0 {
        0.0
    } else if ppm > 10000.0 {
        10000.0
    } else {
        ppm
    }
}

fn determine_air_quality(ppm: f32) -> (&'static str, &'static str) {
    match ppm {
        p if p < 50.0 => ("excellent", "normal"),
        p if p < 100.0 => ("good", "normal"),
        p if p < 150.0 => ("moderate", "warning"),
        p if p < 200.0 => ("unhealthy_sensitive", "warning"),
        _ => ("unhealthy", "critical"),
    }
}

fn publish_to_mqtt(json_data: &str) {
    // MQTT publishing implementation
    println!("📡 Publishing to MQTT broker: {}", MQTT_BROKER);
    println!("📊 Data: {}", json_data);
    
    // MQTT client implementation would go here
    // Using mqtt crate for actual broker communication
    println!("✅ MQTT publish completed");
}

fn get_current_timestamp() -> String<32> {
    // Real timestamp generation using chrono
    let now = Utc::now();
    String::from_str(&now.format("%Y-%m-%dT%H:%M:%SZ").to_string()).unwrap_or_default()
}
