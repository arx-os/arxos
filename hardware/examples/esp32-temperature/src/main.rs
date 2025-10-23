/*
 * ArxOS ESP32 Temperature & Humidity Sensor
 * 
 * This example demonstrates how to connect an ESP32 with DHT22 sensor
 * to ArxOS using Rust and the esp-rs ecosystem.
 * 
 * Hardware Requirements:
 * - ESP32 development board
 * - DHT22 temperature/humidity sensor
 * - 10kΩ pull-up resistor
 * 
 * Rust Dependencies:
 * - esp-idf-hal
 * - esp-idf-svc
 * - serde_json
 * - reqwest
 * - tokio
 * - dht-sensor
 * - chrono
 */

use esp_idf_hal::delay::FreeRtos;
use esp_idf_hal::gpio::{Input, Output, PinDriver};
use esp_idf_hal::peripherals::Peripherals;
use esp_idf_svc::eventloop::EspSystemEventLoop;
use esp_idf_svc::nvs::EspDefaultNvsPartition;
use esp_idf_svc::wifi::{AuthMethod, BlockingWifi, ClientConfiguration, Configuration, EspWifi};
use esp_idf_svc::http::client::{EspHttpClient, EspHttpClientConfiguration};
use serde_json::{json, Value};
use chrono::{DateTime, Utc};
use base64::{Engine as _, engine::general_purpose};
use dht_sensor::*;

// Configuration
const WIFI_SSID: &str = "YOUR_WIFI_SSID";
const WIFI_PASSWORD: &str = "YOUR_WIFI_PASSWORD";
const GITHUB_TOKEN: &str = "YOUR_GITHUB_TOKEN";
const GITHUB_OWNER: &str = "YOUR_GITHUB_USERNAME";
const GITHUB_REPO: &str = "YOUR_BUILDING_REPO";

// Sensor pins
const DHT_PIN: u8 = 4;
const LED_PIN: u8 = 2;

// Sensor information
const SENSOR_ID: &str = "temp_hum_001";
const SENSOR_TYPE: &str = "temperature_humidity";
const ROOM_PATH: &str = "/B1/3/301/HVAC";
const BUILDING_ID: &str = "B1";

struct SensorData {
    temperature: f32,
    humidity: f32,
    timestamp: DateTime<Utc>,
}

impl SensorData {
    fn new(temperature: f32, humidity: f32) -> Self {
        Self {
            temperature,
            humidity,
            timestamp: Utc::now(),
        }
    }

    fn to_yaml(&self) -> String {
        let status = if self.temperature >= 60.0 && self.temperature <= 85.0 {
            "normal"
        } else {
            "warning"
        };

        format!(
            r#"apiVersion: arxos.io/v1
kind: SensorData
metadata:
  sensor_id: {}
  sensor_type: {}
  room_path: {}
  timestamp: {}
  source: github-api
  building_id: {}

data:
  temperature:
    value: {:.1}
    unit: fahrenheit
    status: {}
    confidence: 0.95
  humidity:
    value: {:.1}
    unit: percent
    status: normal
    confidence: 0.92

alerts:
  - level: info
    message: "Temperature within normal range"
    timestamp: {}

_arxos:
  processed: true
  validated: true
  device_id: esp32_{}
"#,
            SENSOR_ID,
            SENSOR_TYPE,
            ROOM_PATH,
            self.timestamp.to_rfc3339(),
            BUILDING_ID,
            self.temperature,
            status,
            self.humidity,
            self.timestamp.to_rfc3339(),
            SENSOR_ID
        )
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("ArxOS ESP32 Temperature & Humidity Sensor");
    println!("==========================================");

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
    let dht_pin = PinDriver::input(peripherals.pins.gpio4)?;

    // Main loop
    loop {
        // Read sensor data using DHT22
        let (temperature, humidity) = read_dht22_sensor(&dht_pin)?;

        println!("Temperature: {:.1}°F", temperature);
        println!("Humidity: {:.1}%", humidity);

        // Create sensor data
        let sensor_data = SensorData::new(temperature, humidity);
        let yaml_data = sensor_data.to_yaml();

        // Post to GitHub
        if let Err(e) = post_to_github(&yaml_data) {
            println!("Failed to post to GitHub: {}", e);
        } else {
            println!("✅ Sensor data posted successfully");
        }

        // Blink LED to indicate activity
        led.set_high()?;
        FreeRtos::delay_ms(100);
        led.set_low()?;

        // Wait 5 minutes before next reading
        FreeRtos::delay_ms(300000);
    }
}

fn read_dht22_sensor(pin: &PinDriver<Input>) -> Result<(f32, f32), Box<dyn std::error::Error>> {
    // DHT22 sensor reading implementation
    // This would use the dht-sensor crate for actual hardware reading
    let mut buffer = [0u8; 5];
    
    // Start signal
    let mut output_pin = pin.into_output()?;
    output_pin.set_low()?;
    FreeRtos::delay_ms(18);
    output_pin.set_high()?;
    FreeRtos::delay_us(40);
    
    // Switch to input and read data
    let input_pin = output_pin.into_input()?;
    
    // Wait for response
    if !wait_for_signal(&input_pin, true, 80)? {
        return Err("DHT22 not responding".into());
    }
    
    if !wait_for_signal(&input_pin, false, 80)? {
        return Err("DHT22 response timeout".into());
    }
    
    // Read 40 bits of data
    for i in 0..40 {
        if !wait_for_signal(&input_pin, true, 50)? {
            return Err("Data bit timeout".into());
        }
        
        let high_time = measure_signal_time(&input_pin, false)?;
        buffer[i / 8] |= if high_time > 40 { 1 } else { 0 } << (7 - (i % 8));
    }
    
    // Verify checksum
    let checksum = buffer[0].wrapping_add(buffer[1]).wrapping_add(buffer[2]).wrapping_add(buffer[3]);
    if checksum != buffer[4] {
        return Err("DHT22 checksum error".into());
    }
    
    // Convert to temperature and humidity
    let humidity = ((buffer[0] as u16) << 8 | buffer[1] as u16) as f32 / 10.0;
    let temperature_raw = ((buffer[2] as u16) << 8 | buffer[3] as u16) as f32 / 10.0;
    let temperature = if buffer[2] & 0x80 != 0 {
        -temperature_raw
    } else {
        temperature_raw
    };
    
    // Convert Celsius to Fahrenheit
    let temperature_f = temperature * 9.0 / 5.0 + 32.0;
    
    Ok((temperature_f, humidity))
}

fn wait_for_signal(pin: &PinDriver<Input>, expected: bool, timeout_us: u32) -> Result<bool, Box<dyn std::error::Error>> {
    let start = esp_idf_hal::delay::FreeRtos::get_tick_count();
    let timeout_ticks = timeout_us / 1000; // Convert to milliseconds
    
    while (esp_idf_hal::delay::FreeRtos::get_tick_count() - start) < timeout_ticks {
        if pin.is_high()? == expected {
            return Ok(true);
        }
        FreeRtos::delay_us(1);
    }
    
    Ok(false)
}

fn measure_signal_time(pin: &PinDriver<Input>, expected: bool) -> Result<u32, Box<dyn std::error::Error>> {
    let start = esp_idf_hal::delay::FreeRtos::get_tick_count();
    
    while pin.is_high()? == expected {
        FreeRtos::delay_us(1);
    }
    
    Ok(esp_idf_hal::delay::FreeRtos::get_tick_count() - start)
}

fn post_to_github(yaml_data: &str) -> Result<(), Box<dyn std::error::Error>> {
    let client = EspHttpClient::new(&EspHttpClientConfiguration::default())?;

    let timestamp = Utc::now().format("%Y%m%d_%H%M%S").to_string();
    let filename = format!("sensor-data/temperature_humidity_{}.yaml", timestamp);

    let url = format!(
        "https://api.github.com/repos/{}/{}/contents/{}",
        GITHUB_OWNER, GITHUB_REPO, filename
    );

    let payload = json!({
        "message": format!("feat: sensor data from {} - {}", SENSOR_ID, timestamp),
        "content": general_purpose::STANDARD.encode(yaml_data),
        "branch": "main"
    });

    let mut request = client.post(&url)?;
    request.insert_header("Authorization", &format!("token {}", GITHUB_TOKEN))?;
    request.insert_header("Content-Type", "application/json")?;
    request.insert_header("User-Agent", "ArxOS-ESP32-Rust/1.0")?;

    let response = request.submit()?;
    
    if response.status() == 200 || response.status() == 201 {
        println!("✅ Successfully posted to GitHub");
        Ok(())
    } else {
        Err(format!("GitHub API error: {}", response.status()).into())
    }
}
