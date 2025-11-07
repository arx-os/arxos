# ArxOS Hardware Examples

**Open source sensor implementations for ArxOS building management**

## ESP32 Temperature/Humidity Sensor

### Hardware Requirements
- ESP32 development board
- DHT22 temperature/humidity sensor
- Breadboard and jumper wires
- 4.7kΩ pull-up resistor

### Circuit Diagram
```
ESP32          DHT22
GPIO 4    →    Data
3.3V      →    VCC
GND       →    GND
GPIO 4    →    4.7kΩ → 3.3V (pull-up)
```

### Arduino Code
```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <DHT.h>

#define DHT_PIN 4
#define DHT_TYPE DHT22

DHT dht(DHT_PIN, DHT_TYPE);

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* githubToken = "YOUR_GITHUB_TOKEN";
const char* repoOwner = "your-org";
const char* repoName = "building";

void setup() {
  Serial.begin(115200);
  dht.begin();
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  Serial.println("WiFi connected!");
}

void loop() {
  float temperature = dht.readTemperature(true); // Fahrenheit
  float humidity = dht.readHumidity();
  
  if (!isnan(temperature) && !isnan(humidity)) {
    sendToArxOS(temperature, humidity);
  }
  
  delay(60000); // Send data every minute
}

void sendToArxOS(float temp, float humidity) {
  HTTPClient http;
  
  // Create sensor data JSON
  JsonDocument doc;
  doc["equipment_id"] = "VAV-301";
  doc["sensor_id"] = "esp32_001";
  doc["sensor_type"] = "temperature_humidity";
  doc["temperature"] = temp;
  doc["humidity"] = humidity;
  doc["timestamp"] = getTimestamp();
  doc["location"] = "/B1/3/301/HVAC/VAV-301";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  // Send to GitHub API
  String url = "https://api.github.com/repos/" + String(repoOwner) + "/" + String(repoName) + "/contents/sensor-data/VAV-301/temperature-humidity.json";
  
  http.begin(url);

  String authHeader = String("token ");
  authHeader += githubToken;

  http.addHeader("Authorization", authHeader.c_str());
  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.PUT(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Data sent successfully: " + String(httpResponseCode));
  } else {
    Serial.println("Error sending data: " + String(httpResponseCode));
  }
  
  http.end();
}

String getTimestamp() {
  // Get current timestamp in ISO format
  time_t now = time(nullptr);
  struct tm* timeinfo = localtime(&now);
  
  char buffer[32];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", timeinfo);
  return String(buffer);
}
```

## RP2040 Air Quality Sensor

### Hardware Requirements
- Raspberry Pi Pico (RP2040)
- SGP30 air quality sensor
- Breadboard and jumper wires
- I2C level shifter (if needed)

### Circuit Diagram
```
RP2040          SGP30
GPIO 0 (SDA) →  SDA
GPIO 1 (SCL) →  SCL
3.3V         →  VCC
GND          →  GND
```

### Arduino Code
```cpp
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include <SGP30.h>

SGP30 sgp;

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* webhookUrl = "https://your-webhook.com/sensor-data";

void setup() {
  Serial.begin(115200);
  Wire.begin();
  
  if (!sgp.begin()) {
    Serial.println("SGP30 sensor not found!");
    while (1);
  }
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  Serial.println("WiFi connected!");
}

void loop() {
  sgp.measureAirQuality();
  
  uint16_t co2 = sgp.getCO2();
  uint16_t tvoc = sgp.getTVOC();
  
  sendToArxOS(co2, tvoc);
  delay(300000); // Send data every 5 minutes
}

void sendToArxOS(uint16_t co2, uint16_t tvoc) {
  HTTPClient http;
  
  // Create sensor data JSON
  JsonDocument doc;
  doc["equipment_id"] = "AHU-01";
  doc["sensor_id"] = "rp2040_001";
  doc["sensor_type"] = "air_quality";
  doc["co2"] = co2;
  doc["tvoc"] = tvoc;
  doc["timestamp"] = getTimestamp();
  doc["location"] = "/B1/ROOF/MER-NORTH/HVAC/AHU-01";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  // Send to webhook
  http.begin(webhookUrl);
  http.addHeader("Content-Type", "application/json");
  
  int httpResponseCode = http.POST(jsonString);
  
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.println("Data sent successfully: " + String(httpResponseCode));
  } else {
    Serial.println("Error sending data: " + String(httpResponseCode));
  }
  
  http.end();
}

String getTimestamp() {
  time_t now = time(nullptr);
  struct tm* timeinfo = localtime(&now);
  
  char buffer[32];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", timeinfo);
  return String(buffer);
}
```

## Arduino Motion Sensor

### Hardware Requirements
- Arduino Uno/Nano
- PIR motion sensor
- Ethernet shield or WiFi module
- Breadboard and jumper wires

### Circuit Diagram
```
Arduino         PIR Sensor
5V          →   VCC
GND         →   GND
Digital 2   →   OUT
```

### Arduino Code
```cpp
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";
const char* mqttServer = "your-mqtt-broker.com";
const int mqttPort = 1883;

WiFiClient wifiClient;
PubSubClient mqttClient(wifiClient);

const int pirPin = 2;
bool motionDetected = false;
unsigned long lastMotionTime = 0;

void setup() {
  Serial.begin(115200);
  pinMode(pirPin, INPUT);
  
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  
  mqttClient.setServer(mqttServer, mqttPort);
  mqttClient.setCallback(onMessage);
  
  Serial.println("WiFi connected!");
}

void loop() {
  if (!mqttClient.connected()) {
    reconnect();
  }
  mqttClient.loop();
  
  int pirState = digitalRead(pirPin);
  
  if (pirState == HIGH && !motionDetected) {
    motionDetected = true;
    lastMotionTime = millis();
    sendMotionData(true);
  } else if (pirState == LOW && motionDetected) {
    motionDetected = false;
    sendMotionData(false);
  }
  
  delay(100);
}

void sendMotionData(bool motion) {
  JsonDocument doc;
  doc["equipment_id"] = "ROOM-301";
  doc["sensor_id"] = "arduino_001";
  doc["sensor_type"] = "motion";
  doc["motion_detected"] = motion;
  doc["timestamp"] = getTimestamp();
  doc["location"] = "/B1/3/301/ROOM/ROOM-301";
  
  String jsonString;
  serializeJson(doc, jsonString);
  
  String topic = "arxos/sensors/ROOM-301/motion";
  mqttClient.publish(topic.c_str(), jsonString.c_str());
  
  Serial.println("Motion data sent: " + String(motion));
}

void onMessage(char* topic, byte* payload, unsigned int length) {
  // Handle incoming MQTT messages
  String message = "";
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println("Message received: " + message);
}

void reconnect() {
  while (!mqttClient.connected()) {
    Serial.println("Attempting MQTT connection...");
    
    if (mqttClient.connect("arduino_sensor")) {
      Serial.println("MQTT connected!");
      mqttClient.subscribe("arxos/sensors/ROOM-301/commands");
    } else {
      Serial.println("MQTT connection failed, retrying in 5 seconds");
      delay(5000);
    }
  }
}

String getTimestamp() {
  time_t now = time(nullptr);
  struct tm* timeinfo = localtime(&now);
  
  char buffer[32];
  strftime(buffer, sizeof(buffer), "%Y-%m-%dT%H:%M:%SZ", timeinfo);
  return String(buffer);
}
```

## Integration Methods

### GitHub API Integration
```cpp
// Direct GitHub API call
String url = "https://api.github.com/repos/your-org/building/contents/sensor-data/equipment-id/sensor-type.json";
http.begin(url);
String authHeader = String("token ");
authHeader += githubToken;
http.addHeader("Authorization", authHeader.c_str());
http.addHeader("Content-Type", "application/json");
http.PUT(jsonData);
```

### Webhook Integration
```cpp
// Send to webhook endpoint
http.begin("https://your-webhook.com/sensor-data");
http.addHeader("Content-Type", "application/json");
http.POST(jsonData);
```

### MQTT Integration
```cpp
// Publish to MQTT broker
mqttClient.publish("arxos/sensors/equipment-id/sensor-type", jsonData.c_str());
```

## Sensor Data Format

All sensors should output data in this format:

```json
{
  "equipment_id": "VAV-301",
  "sensor_id": "esp32_001",
  "sensor_type": "temperature_humidity",
  "temperature": 72.5,
  "humidity": 45.2,
  "timestamp": "2024-12-01T10:30:00Z",
  "location": "/B1/3/301/HVAC/VAV-301"
}
```

## Troubleshooting

### Common Issues
1. **WiFi Connection**: Check SSID and password
2. **Sensor Reading**: Verify wiring and sensor power
3. **Data Format**: Ensure JSON is valid
4. **API Limits**: Check GitHub API rate limits
5. **MQTT Connection**: Verify broker settings

### Debug Tips
1. Use Serial.println() for debugging
2. Check HTTP response codes
3. Validate JSON format
4. Test with small data sets first
5. Monitor network connectivity

---

**ArxOS Hardware Examples** - Open source sensor implementations
