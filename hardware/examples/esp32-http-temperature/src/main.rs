/*
 * ArxOS ESP32 HTTP Temperature & Humidity Sensor
 * 
 * ⚠️  SECURITY WARNING: EXAMPLE FILE ONLY ⚠️
 * 
 * This is an EXAMPLE file for demonstration purposes only.
 * DO NOT use this code in production without proper security measures.
 * 
 * SECURITY NOTES:
 * - Replace ALL placeholder values below with your actual credentials
 * - Use environment variables or secure configuration management
 * - NEVER commit real credentials to version control
 * - Use encrypted storage for sensitive data
 * 
 * This example demonstrates HTTP POST integration with ArxOS sensor ingestion server.
 * 
 * Hardware Requirements:
 * - ESP32 development board
 * - DHT22 temperature/humidity sensor
 * - 10kΩ pull-up resistor
 * 
 * Prerequisites:
 * - ArxOS server running with HTTP ingestion enabled
 * - Command: arx sensors http --building "Your Building" --host 0.0.0.0 --port 3000
 */

use esp_idf_hal::delay::FreeRtos;
use esp_idf_hal::gpio::{Input, Output, PinDriver};
use esp_idf_hal::peripherals::Peripherals;
use esp_idf_svc::eventloop::EspSystemEventLoop;
use esp_idf_svc::nvs::EspDefaultNvsPartition;
use esp_idf_svc::wifi::{AuthMethod, BlockingWifi, ClientConfiguration, Configuration, EspWifi};
use esp_idf_svc::http::client::{EspHttpClient, EspHttpClientConfiguration};
use serde_json::{json, Value};

// ⚠️  CONFIGURATION - REPLACE WITH YOUR ACTUAL VALUES
// ⚠️  NEVER commit these values to version control!

const WIFI_SSID: &str = "YOUR_WIFI_SSID";
const WIFI_PASSWORD: &str = "YOUR_WIFI_PASSWORD";

// ArxOS HTTP endpoint configuration
const ARXOS_HOST: &str = "192.168.1.100";  // Your ArxOS server IP
const ARXOS_PORT: u16 = 3000;
const ARXOS_ENDPOINT: &str = "http://192.168.1.100:3000/sensors/ingest";

// Sensor pins
const DHT_PIN: u8 = 4;
const LED_PIN: u8 = 2;

// Sensor information
const SENSOR_ID: &str = "esp32_temp_001";
const SENSOR_TYPE: &str = "temperature_humidity";
const ROOM_PATH: &str = "/B1/3/301/HVAC";
const BUILDING_ID: &str = "B1";
const EQUIPMENT_ID: &str = "HVAC-301";

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("ArxOS ESP32 HTTP Temperature & Humidity Sensor");
    println!("================================================");

    // Initialize peripherals
    let peripherals = Peripherals::take().unwrap();
    let sysloop = EspSystemEventLoop::take()?;
    let nvs = EspDefaultNvsPartition::take()?;

    // Initialize WiFi
    let mut wifi = BlockingWifi::wrap(
        EspWifi::new(peripherals.modem, sysloop.clone(), Some(nvs))?,
        sysloop,
    )?;

    wifi.set_configuration(&Configuration::Client(ClientConfiguration {
        ssid: WIFI_SSID.into(),
        password: WIFI_PASSWORD.into(),
        auth_method: AuthMethod::WPA2Personal,
        ..Default::default()
    }))?;

    wifi.start()?;
    wifi.connect()?;
    wifi.wait_netif_up()?;

    println!("WiFi connected successfully!");

    // Initialize GPIO pins
    let mut led = PinDriver::output(peripherals.pins.gpio2)?;

    // Main loop
    loop {
        // Read sensor data (simplified for example)
        let (temperature, humidity) = read_sensor()?;

        println!("Temperature: {:.1}°F, Humidity: {:.1}%", temperature, humidity);

        // Create JSON payload in ArxOS format
        let payload = json!({
            "api_version": "arxos.io/v1",
            "kind": "SensorData",
            "metadata": {
                "sensor_id": SENSOR_ID,
                "sensor_type": SENSOR_TYPE,
                "room_path": ROOM_PATH,
                "timestamp": get_current_timestamp(),
                "source": "http",
                "building_id": BUILDING_ID,
                "equipment_id": EQUIPMENT_ID
            },
            "data": {
                "temperature": temperature,
                "humidity": humidity
            },
            "alerts": [],
            "arxos": {
                "processed": false,
                "validated": false,
                "device_id": format!("esp32_{}", SENSOR_ID)
            }
        });

        // Send HTTP POST to ArxOS
        match post_to_arxos(&payload.to_string()) {
            Ok(_) => {
                println!("✅ Sensor data sent successfully");
                led.set_high()?;
                FreeRtos::delay_ms(100);
                led.set_low()?;
            }
            Err(e) => {
                println!("❌ Failed to send: {}", e);
                // Flash LED rapidly on error
                for _ in 0..5 {
                    led.set_high()?;
                    FreeRtos::delay_ms(50);
                    led.set_low()?;
                    FreeRtos::delay_ms(50);
                }
            }
        }

        // Wait 60 seconds before next reading
        FreeRtos::delay_ms(60000);
    }
}

fn read_sensor() -> Result<(f32, f32), Box<dyn std::error::Error>> {
    // Simplified sensor reading - replace with actual DHT22 implementation
    // This is a placeholder for the example
    let temp = 72.5f32;
    let hum = 45.0f32;
    Ok((temp, hum))
}

fn get_current_timestamp() -> String {
    // Simplified timestamp - in production use chrono or proper time API
    "2024-12-01T10:30:00Z".to_string()
}

fn post_to_arxos(json_body: &str) -> Result<(), Box<dyn std::error::Error>> {
    let client_config = EspHttpClientConfiguration::default();
    let mut client = EspHttpClient::new(&client_config)?;

    // Create HTTP request
    let uri = ARXOS_ENDPOINT;
    let method = esp_idf_svc::http::client::Method::Post;
    let mut request = client.request(method, uri, &[("Content-Type", "application/json")])?;

    // Write JSON body
    request.write_all(json_body.as_bytes())?;
    request.flush()?;

    // Get response
    let status = request.status();
    println!("HTTP Status: {}", status);

    let mut response_buffer = [0u8; 256];
    let bytes_read = request.read(&mut response_buffer)?;

    let response_body = String::from_utf8_lossy(&response_buffer[..bytes_read]);
    println!("Response: {}", response_body);

    // Check status code
    if status >= 200 && status < 300 {
        Ok(())
    } else {
        Err(format!("HTTP error: {}", status).into())
    }
}

