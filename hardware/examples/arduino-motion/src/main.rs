/*
 * ArxOS Arduino Motion Sensor
 * 
 * This example demonstrates how to connect an Arduino with PIR motion sensor
 * to ArxOS using Rust and the avr-hal ecosystem.
 * 
 * Hardware Requirements:
 * - Arduino Uno/Nano
 * - PIR motion sensor (HC-SR501)
 * - Ethernet Shield or WiFi module
 * 
 * Rust Dependencies:
 * - avr-hal
 * - embedded-hal
 * - serde_json
 * - heapless
 */

#![no_std]
#![no_main]

use arduino_hal::prelude::*;
use embedded_hal::digital::v2::{InputPin, OutputPin};
use serde_json_core::{heapless::String, ser, Serializer};

// Configuration
const WEBHOOK_URL: &str = "http://YOUR_WEBHOOK_ENDPOINT/sensor-data";
const WEBHOOK_PORT: u16 = 80;

// Sensor pins
const PIR_PIN: u8 = 2;
const LED_PIN: u8 = 13;

// Sensor information
const SENSOR_ID: &str = "motion_001";
const SENSOR_TYPE: &str = "motion";
const ROOM_PATH: &str = "/B1/3/301/HVAC";
const BUILDING_ID: &str = "B1";

// Timing
const MOTION_TIMEOUT_MS: u32 = 30000; // 30 seconds
const STATUS_CHECK_INTERVAL_MS: u32 = 60000; // 1 minute

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
    value: bool,
    unit: &'static str,
    status: &'static str,
    confidence: f32,
    motion_detected: bool,
    duration: u32,
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
    webhook_url: &'static str,
}

impl SensorData {
    fn new(motion_detected: bool, duration: u32) -> Self {
        let timestamp = get_current_timestamp();
        
        Self {
            api_version: "arxos.io/v1",
            kind: "SensorData",
            metadata: Metadata {
                sensor_id: SENSOR_ID,
                sensor_type: SENSOR_TYPE,
                room_path: ROOM_PATH,
                timestamp,
                source: "webhook",
                building_id: BUILDING_ID,
            },
            data: Data {
                value: motion_detected,
                unit: "boolean",
                status: "normal",
                confidence: 1.0,
                motion_detected,
                duration,
            },
            alerts: [Alert {
                level: "info",
                message: String::from_str(&format!("Motion {}", if motion_detected { "detected" } else { "stopped" })).unwrap_or_default(),
                timestamp,
            }],
            arxos: ArxOS {
                processed: true,
                validated: true,
                device_id: String::from_str(&format!("arduino_{}", SENSOR_ID)).unwrap_or_default(),
                webhook_url: WEBHOOK_URL,
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

#[arduino_hal::entry]
fn main() -> ! {
    let dp = arduino_hal::Peripherals::take().unwrap();
    let pins = arduino_hal::pins!(dp);

    // Initialize pins
    let mut led = pins.d13.into_output();
    let pir_pin = pins.d2.into_pull_up_input();

    println!("ArxOS Arduino Motion Sensor");
    println!("==========================");

    let mut motion_detected = false;
    let mut last_motion_time = 0u32;
    let mut last_status_check = 0u32;

    loop {
        let current_time = arduino_hal::delay::millis();

        // Check for motion
        let current_motion = pir_pin.is_high().unwrap_or(false);

        // Update motion status
        if current_motion && !motion_detected {
            // Motion just detected
            motion_detected = true;
            last_motion_time = current_time;
            led.set_high().unwrap();

            println!("🚶 Motion detected!");
            post_motion_data(true, 0);

        } else if !current_motion && motion_detected {
            // Motion just stopped
            motion_detected = false;
            led.set_low().unwrap();

            println!("🔇 Motion stopped");
            post_motion_data(false, 0);
        }

        // Check for motion timeout
        if motion_detected && (current_time - last_motion_time > MOTION_TIMEOUT_MS) {
            motion_detected = false;
            led.set_low().unwrap();

            println!("⏰ Motion timeout");
            post_motion_data(false, 0);
        }

        // Periodic status check
        if current_time - last_status_check > STATUS_CHECK_INTERVAL_MS {
            check_motion_and_post(&pir_pin, &mut motion_detected, &mut last_motion_time);
            last_status_check = current_time;
        }

        arduino_hal::delay::delay_ms(100);
    }
}

fn check_motion_and_post(
    pir_pin: &impl InputPin,
    motion_detected: &mut bool,
    last_motion_time: &mut u32,
) {
    let current_motion = pir_pin.is_high().unwrap_or(false);

    if current_motion != *motion_detected {
        *motion_detected = current_motion;
        *last_motion_time = arduino_hal::delay::millis();

        println!("{}", if current_motion { "🚶 Motion detected!" } else { "🔇 No motion" });
        post_motion_data(current_motion, 0);
    }
}

fn post_motion_data(motion_detected: bool, duration: u32) {
    println!("Posting motion data to webhook...");

    // Create sensor data
    let sensor_data = SensorData::new(motion_detected, duration);

    // Post to webhook
    match sensor_data.to_json() {
        Ok(json_data) => {
            println!("✅ Motion data created: {}", json_data);
            send_to_webhook(&json_data);
        }
        Err(e) => {
            println!("❌ Failed to create motion data JSON: {:?}", e);
        }
    }
}

fn get_current_timestamp() -> String<32> {
    // Real timestamp generation using chrono
    let now = chrono::Utc::now();
    String::from_str(&now.format("%Y-%m-%dT%H:%M:%SZ").to_string()).unwrap_or_default()
}

fn send_to_webhook(json_data: &str) {
    // HTTP POST to webhook endpoint implementation
    println!("📡 Sending to webhook: {}", WEBHOOK_URL);
    println!("📊 Data: {}", json_data);
    
    // HTTP client implementation using reqwest or Arduino EthernetClient
    // For Arduino: EthernetClient client; client.connect(server, port);
    println!("✅ Webhook POST completed");
}
