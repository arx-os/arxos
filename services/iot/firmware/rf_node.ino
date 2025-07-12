/*
 * ArxLink RF Node Firmware
 * 
 * Offline-first RF mesh communication for building-to-building connectivity.
 * Features mesh topology formation, sync protocol, and security layer.
 */

#include <RF24.h>
#include <RF24Network.h>
#include <RF24Mesh.h>
#include <SPI.h>
#include <EEPROM.h>
#include <ArduinoJson.h>
#include <Crypto.h>
#include <AES.h>
#include <SHA256.h>

// Hardware configuration
#define CE_PIN 9
#define CS_PIN 10
#define LED_PIN 13
#define BUTTON_PIN 2
#define BATTERY_PIN A0

// Network configuration
#define CHANNEL 76
#define DATA_RATE RF24_250KBPS
#define POWER_LEVEL RF24_PA_HIGH
#define NODE_ID 0  // Will be assigned by mesh

// Security configuration
#define ENCRYPTION_KEY_SIZE 32
#define MAX_PAYLOAD_SIZE 32
#define SYNC_INTERVAL 30000  // 30 seconds
#define HEARTBEAT_INTERVAL 10000  // 10 seconds

// Message types
enum MessageType {
  MSG_SYNC = 1,
  MSG_HEARTBEAT = 2,
  MSG_DATA = 3,
  MSG_ROUTE_UPDATE = 4,
  MSG_SECURITY_CHALLENGE = 5,
  MSG_SECURITY_RESPONSE = 6,
  MSG_TOPOLOGY_UPDATE = 7,
  MSG_ERROR = 8
};

// Node states
enum NodeState {
  STATE_INIT = 0,
  STATE_DISCOVERING = 1,
  STATE_CONNECTING = 2,
  STATE_CONNECTED = 3,
  STATE_SYNCING = 4,
  STATE_ERROR = 5
};

// Message structure
struct Message {
  uint8_t type;
  uint8_t source_id;
  uint8_t dest_id;
  uint8_t sequence;
  uint8_t payload[MAX_PAYLOAD_SIZE];
  uint8_t payload_size;
  uint32_t timestamp;
  uint8_t checksum;
};

// Node information
struct NodeInfo {
  uint8_t id;
  uint8_t parent_id;
  uint8_t children[8];
  uint8_t child_count;
  uint8_t hop_count;
  uint32_t last_seen;
  float battery_level;
  int8_t signal_strength;
  bool is_gateway;
};

// Global variables
RF24 radio(CE_PIN, CS_PIN);
RF24Network network(radio);
RF24Mesh mesh(radio, network);

NodeInfo node_info;
NodeState current_state = STATE_INIT;
uint32_t last_sync_time = 0;
uint32_t last_heartbeat_time = 0;
uint8_t message_sequence = 0;
uint8_t encryption_key[ENCRYPTION_KEY_SIZE];
bool encryption_enabled = false;

// Message buffers
Message tx_message;
Message rx_message;
uint8_t message_buffer[sizeof(Message)];

// Security variables
uint8_t challenge[16];
uint8_t response[16];
bool authenticated = false;
uint32_t session_key = 0;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Serial.println(F("ArxLink RF Node Starting..."));
  
  // Initialize pins
  pinMode(LED_PIN, OUTPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(BATTERY_PIN, INPUT);
  
  // Initialize radio
  if (!radio.begin()) {
    Serial.println(F("Radio hardware not responding!"));
    while (1) {
      digitalWrite(LED_PIN, HIGH);
      delay(100);
      digitalWrite(LED_PIN, LOW);
      delay(100);
    }
  }
  
  // Configure radio
  radio.setChannel(CHANNEL);
  radio.setDataRate(DATA_RATE);
  radio.setPALevel(POWER_LEVEL);
  radio.setPayloadSize(sizeof(Message));
  radio.enableDynamicPayloads();
  radio.enableAckPayload();
  
  // Initialize mesh network
  mesh.setNodeID(NODE_ID);
  mesh.begin();
  
  // Load node configuration from EEPROM
  loadNodeConfig();
  
  // Initialize security
  initializeSecurity();
  
  // Start discovery process
  current_state = STATE_DISCOVERING;
  
  Serial.println(F("ArxLink RF Node Ready"));
  digitalWrite(LED_PIN, HIGH);
  delay(1000);
  digitalWrite(LED_PIN, LOW);
}

void loop() {
  // Update mesh network
  mesh.update();
  
  // Handle different states
  switch (current_state) {
    case STATE_INIT:
      handleInit();
      break;
    case STATE_DISCOVERING:
      handleDiscovering();
      break;
    case STATE_CONNECTING:
      handleConnecting();
      break;
    case STATE_CONNECTED:
      handleConnected();
      break;
    case STATE_SYNCING:
      handleSyncing();
      break;
    case STATE_ERROR:
      handleError();
      break;
  }
  
  // Handle incoming messages
  handleIncomingMessages();
  
  // Update node information
  updateNodeInfo();
  
  // Send periodic messages
  sendPeriodicMessages();
  
  // Check for button press
  checkButtonPress();
  
  delay(100);  // Small delay to prevent overwhelming
}

void handleInit() {
  Serial.println(F("Initializing node..."));
  
  // Initialize node information
  node_info.id = NODE_ID;
  node_info.parent_id = 0;
  node_info.child_count = 0;
  node_info.hop_count = 0;
  node_info.last_seen = millis();
  node_info.battery_level = getBatteryLevel();
  node_info.signal_strength = 0;
  node_info.is_gateway = false;
  
  // Clear children array
  for (int i = 0; i < 8; i++) {
    node_info.children[i] = 0;
  }
  
  current_state = STATE_DISCOVERING;
}

void handleDiscovering() {
  static uint32_t discovery_start = millis();
  static uint32_t last_discovery_broadcast = 0;
  
  // Send discovery broadcast every 5 seconds
  if (millis() - last_discovery_broadcast > 5000) {
    sendDiscoveryBroadcast();
    last_discovery_broadcast = millis();
  }
  
  // Try to connect to mesh network
  if (mesh.checkConnection()) {
    Serial.println(F("Connected to mesh network"));
    current_state = STATE_CONNECTING;
    return;
  }
  
  // Timeout after 60 seconds
  if (millis() - discovery_start > 60000) {
    Serial.println(F("Discovery timeout, retrying..."));
    discovery_start = millis();
  }
  
  // Blink LED to indicate discovery
  if ((millis() / 500) % 2) {
    digitalWrite(LED_PIN, HIGH);
  } else {
    digitalWrite(LED_PIN, LOW);
  }
}

void handleConnecting() {
  Serial.println(F("Connecting to mesh..."));
  
  // Attempt to join mesh network
  if (mesh.renewAddress()) {
    Serial.println(F("Successfully joined mesh network"));
    node_info.id = mesh.getNodeID();
    current_state = STATE_CONNECTED;
    digitalWrite(LED_PIN, HIGH);
  } else {
    Serial.println(F("Failed to join mesh, retrying..."));
    current_state = STATE_DISCOVERING;
  }
}

void handleConnected() {
  // Update connection status
  if (!mesh.checkConnection()) {
    Serial.println(F("Lost mesh connection"));
    current_state = STATE_DISCOVERING;
    return;
  }
  
  // Update node information
  node_info.last_seen = millis();
  node_info.battery_level = getBatteryLevel();
  
  // Send heartbeat
  if (millis() - last_heartbeat_time > HEARTBEAT_INTERVAL) {
    sendHeartbeat();
    last_heartbeat_time = millis();
  }
  
  // Perform sync if needed
  if (millis() - last_sync_time > SYNC_INTERVAL) {
    current_state = STATE_SYNCING;
  }
  
  // Solid LED indicates connected
  digitalWrite(LED_PIN, HIGH);
}

void handleSyncing() {
  Serial.println(F("Performing network sync..."));
  
  // Send sync message
  sendSyncMessage();
  
  // Update topology
  updateTopology();
  
  // Return to connected state
  current_state = STATE_CONNECTED;
  last_sync_time = millis();
}

void handleError() {
  Serial.println(F("Node in error state"));
  
  // Blink LED rapidly to indicate error
  digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  delay(100);
  
  // Try to recover after 10 seconds
  static uint32_t error_start = millis();
  if (millis() - error_start > 10000) {
    current_state = STATE_INIT;
    error_start = millis();
  }
}

void handleIncomingMessages() {
  RF24NetworkHeader header;
  size_t size = network.available();
  
  if (size) {
    network.read(header, &message_buffer, size);
    
    // Parse message
    if (size == sizeof(Message)) {
      memcpy(&rx_message, message_buffer, sizeof(Message));
      
      // Verify checksum
      if (verifyChecksum(&rx_message)) {
        // Handle message based on type
        switch (rx_message.type) {
          case MSG_SYNC:
            handleSyncMessage();
            break;
          case MSG_HEARTBEAT:
            handleHeartbeatMessage();
            break;
          case MSG_DATA:
            handleDataMessage();
            break;
          case MSG_ROUTE_UPDATE:
            handleRouteUpdateMessage();
            break;
          case MSG_SECURITY_CHALLENGE:
            handleSecurityChallenge();
            break;
          case MSG_SECURITY_RESPONSE:
            handleSecurityResponse();
            break;
          case MSG_TOPOLOGY_UPDATE:
            handleTopologyUpdate();
            break;
          case MSG_ERROR:
            handleErrorMessage();
            break;
        }
      } else {
        Serial.println(F("Message checksum verification failed"));
      }
    }
  }
}

void sendDiscoveryBroadcast() {
  // Create discovery message
  tx_message.type = MSG_SYNC;
  tx_message.source_id = node_info.id;
  tx_message.dest_id = 0;  // Broadcast
  tx_message.sequence = message_sequence++;
  tx_message.timestamp = millis();
  
  // Add discovery payload
  StaticJsonDocument<MAX_PAYLOAD_SIZE> doc;
  doc["action"] = "discovery";
  doc["node_id"] = node_info.id;
  doc["battery"] = node_info.battery_level;
  doc["signal"] = node_info.signal_strength;
  
  String payload = "";
  serializeJson(doc, payload);
  
  memcpy(tx_message.payload, payload.c_str(), min(payload.length(), MAX_PAYLOAD_SIZE));
  tx_message.payload_size = min(payload.length(), MAX_PAYLOAD_SIZE);
  
  // Calculate checksum
  tx_message.checksum = calculateChecksum(&tx_message);
  
  // Send message
  RF24NetworkHeader header(00, 'D');
  network.write(header, &tx_message, sizeof(Message));
  
  Serial.println(F("Sent discovery broadcast"));
}

void sendHeartbeat() {
  // Create heartbeat message
  tx_message.type = MSG_HEARTBEAT;
  tx_message.source_id = node_info.id;
  tx_message.dest_id = 0;  // Broadcast
  tx_message.sequence = message_sequence++;
  tx_message.timestamp = millis();
  
  // Add heartbeat payload
  StaticJsonDocument<MAX_PAYLOAD_SIZE> doc;
  doc["battery"] = node_info.battery_level;
  doc["signal"] = node_info.signal_strength;
  doc["children"] = node_info.child_count;
  doc["hop_count"] = node_info.hop_count;
  
  String payload = "";
  serializeJson(doc, payload);
  
  memcpy(tx_message.payload, payload.c_str(), min(payload.length(), MAX_PAYLOAD_SIZE));
  tx_message.payload_size = min(payload.length(), MAX_PAYLOAD_SIZE);
  
  // Calculate checksum
  tx_message.checksum = calculateChecksum(&tx_message);
  
  // Send message
  RF24NetworkHeader header(00, 'H');
  network.write(header, &tx_message, sizeof(Message));
}

void sendSyncMessage() {
  // Create sync message
  tx_message.type = MSG_SYNC;
  tx_message.source_id = node_info.id;
  tx_message.dest_id = 0;  // Broadcast
  tx_message.sequence = message_sequence++;
  tx_message.timestamp = millis();
  
  // Add sync payload
  StaticJsonDocument<MAX_PAYLOAD_SIZE> doc;
  doc["action"] = "sync";
  doc["node_id"] = node_info.id;
  doc["parent_id"] = node_info.parent_id;
  doc["hop_count"] = node_info.hop_count;
  doc["children"] = node_info.child_count;
  
  String payload = "";
  serializeJson(doc, payload);
  
  memcpy(tx_message.payload, payload.c_str(), min(payload.length(), MAX_PAYLOAD_SIZE));
  tx_message.payload_size = min(payload.length(), MAX_PAYLOAD_SIZE);
  
  // Calculate checksum
  tx_message.checksum = calculateChecksum(&tx_message);
  
  // Send message
  RF24NetworkHeader header(00, 'S');
  network.write(header, &tx_message, sizeof(Message));
  
  Serial.println(F("Sent sync message"));
}

void handleSyncMessage() {
  Serial.print(F("Received sync from node "));
  Serial.println(rx_message.source_id);
  
  // Parse payload
  String payload = String((char*)rx_message.payload, rx_message.payload_size);
  StaticJsonDocument<MAX_PAYLOAD_SIZE> doc;
  deserializeJson(doc, payload);
  
  String action = doc["action"];
  
  if (action == "discovery") {
    // Handle discovery response
    uint8_t source_id = doc["node_id"];
    float battery = doc["battery"];
    int8_t signal = doc["signal"];
    
    // Update neighbor information
    updateNeighborInfo(source_id, battery, signal);
  } else if (action == "sync") {
    // Handle sync response
    uint8_t source_id = doc["node_id"];
    uint8_t parent_id = doc["parent_id"];
    uint8_t hop_count = doc["hop_count"];
    uint8_t children = doc["children"];
    
    // Update topology information
    updateTopologyInfo(source_id, parent_id, hop_count, children);
  }
}

void handleHeartbeatMessage() {
  // Update neighbor information
  String payload = String((char*)rx_message.payload, rx_message.payload_size);
  StaticJsonDocument<MAX_PAYLOAD_SIZE> doc;
  deserializeJson(doc, payload);
  
  uint8_t source_id = rx_message.source_id;
  float battery = doc["battery"];
  int8_t signal = doc["signal"];
  
  updateNeighborInfo(source_id, battery, signal);
}

void handleDataMessage() {
  Serial.print(F("Received data from node "));
  Serial.println(rx_message.source_id);
  
  // Process data message
  String payload = String((char*)rx_message.payload, rx_message.payload_size);
  
  // Forward if not destination
  if (rx_message.dest_id != node_info.id && rx_message.dest_id != 0) {
    forwardMessage(&rx_message);
  } else {
    // Process locally
    processDataMessage(payload);
  }
}

void handleRouteUpdateMessage() {
  Serial.println(F("Received route update"));
  
  // Update routing table
  String payload = String((char*)rx_message.payload, rx_message.payload_size);
  updateRoutingTable(payload);
}

void handleSecurityChallenge() {
  Serial.println(F("Received security challenge"));
  
  // Generate response
  generateSecurityResponse();
  
  // Send response
  tx_message.type = MSG_SECURITY_RESPONSE;
  tx_message.source_id = node_info.id;
  tx_message.dest_id = rx_message.source_id;
  tx_message.sequence = message_sequence++;
  tx_message.timestamp = millis();
  
  memcpy(tx_message.payload, response, 16);
  tx_message.payload_size = 16;
  
  tx_message.checksum = calculateChecksum(&tx_message);
  
  RF24NetworkHeader header(rx_message.source_id, 'R');
  network.write(header, &tx_message, sizeof(Message));
}

void handleSecurityResponse() {
  Serial.println(F("Received security response"));
  
  // Verify response
  if (verifySecurityResponse()) {
    authenticated = true;
    Serial.println(F("Authentication successful"));
  } else {
    Serial.println(F("Authentication failed"));
  }
}

void handleTopologyUpdate() {
  Serial.println(F("Received topology update"));
  
  // Update local topology information
  String payload = String((char*)rx_message.payload, rx_message.payload_size);
  updateTopologyFromPayload(payload);
}

void handleErrorMessage() {
  Serial.println(F("Received error message"));
  
  // Handle error message
  String payload = String((char*)rx_message.payload, rx_message.payload_size);
  StaticJsonDocument<MAX_PAYLOAD_SIZE> doc;
  deserializeJson(doc, payload);
  
  String error = doc["error"];
  Serial.print(F("Error: "));
  Serial.println(error);
}

void sendPeriodicMessages() {
  // Send periodic messages based on state
  if (current_state == STATE_CONNECTED) {
    // Send heartbeat periodically
    if (millis() - last_heartbeat_time > HEARTBEAT_INTERVAL) {
      sendHeartbeat();
      last_heartbeat_time = millis();
    }
  }
}

void updateNodeInfo() {
  // Update battery level
  node_info.battery_level = getBatteryLevel();
  
  // Update signal strength
  node_info.signal_strength = radio.getPALevel();
  
  // Update last seen
  node_info.last_seen = millis();
}

void updateNeighborInfo(uint8_t node_id, float battery, int8_t signal) {
  // Update neighbor information in local storage
  // This would typically be stored in EEPROM or memory
  Serial.print(F("Updated neighbor "));
  Serial.print(node_id);
  Serial.print(F(" battery: "));
  Serial.print(battery);
  Serial.print(F(" signal: "));
  Serial.println(signal);
}

void updateTopologyInfo(uint8_t node_id, uint8_t parent_id, uint8_t hop_count, uint8_t children) {
  // Update topology information
  Serial.print(F("Updated topology for node "));
  Serial.print(node_id);
  Serial.print(F(" parent: "));
  Serial.print(parent_id);
  Serial.print(F(" hops: "));
  Serial.print(hop_count);
  Serial.print(F(" children: "));
  Serial.println(children);
}

void updateTopology() {
  // Update local topology information
  // This would involve querying neighbors and updating routing tables
  
  // Send topology update to neighbors
  tx_message.type = MSG_TOPOLOGY_UPDATE;
  tx_message.source_id = node_info.id;
  tx_message.dest_id = 0;  // Broadcast
  tx_message.sequence = message_sequence++;
  tx_message.timestamp = millis();
  
  // Create topology payload
  StaticJsonDocument<MAX_PAYLOAD_SIZE> doc;
  doc["node_id"] = node_info.id;
  doc["parent_id"] = node_info.parent_id;
  doc["hop_count"] = node_info.hop_count;
  doc["children"] = node_info.child_count;
  
  String payload = "";
  serializeJson(doc, payload);
  
  memcpy(tx_message.payload, payload.c_str(), min(payload.length(), MAX_PAYLOAD_SIZE));
  tx_message.payload_size = min(payload.length(), MAX_PAYLOAD_SIZE);
  
  tx_message.checksum = calculateChecksum(&tx_message);
  
  RF24NetworkHeader header(00, 'T');
  network.write(header, &tx_message, sizeof(Message));
}

void updateTopologyFromPayload(String payload) {
  // Parse topology update payload
  StaticJsonDocument<MAX_PAYLOAD_SIZE> doc;
  deserializeJson(doc, payload);
  
  uint8_t node_id = doc["node_id"];
  uint8_t parent_id = doc["parent_id"];
  uint8_t hop_count = doc["hop_count"];
  uint8_t children = doc["children"];
  
  // Update local topology
  updateTopologyInfo(node_id, parent_id, hop_count, children);
}

void forwardMessage(Message* msg) {
  // Forward message to next hop
  RF24NetworkHeader header(msg->dest_id, 'F');
  network.write(header, msg, sizeof(Message));
  
  Serial.print(F("Forwarded message to node "));
  Serial.println(msg->dest_id);
}

void processDataMessage(String payload) {
  // Process data message locally
  Serial.print(F("Processing data: "));
  Serial.println(payload);
  
  // Parse JSON payload
  StaticJsonDocument<MAX_PAYLOAD_SIZE> doc;
  deserializeJson(doc, payload);
  
  // Handle different data types
  if (doc.containsKey("sensor_data")) {
    handleSensorData(doc["sensor_data"]);
  } else if (doc.containsKey("command")) {
    handleCommand(doc["command"]);
  } else if (doc.containsKey("status")) {
    handleStatusUpdate(doc["status"]);
  }
}

void handleSensorData(JsonObject sensor_data) {
  // Handle sensor data
  Serial.println(F("Processing sensor data"));
  
  // Extract sensor values
  float temperature = sensor_data["temperature"] | 0.0;
  float humidity = sensor_data["humidity"] | 0.0;
  float pressure = sensor_data["pressure"] | 0.0;
  
  Serial.print(F("Temperature: "));
  Serial.println(temperature);
  Serial.print(F("Humidity: "));
  Serial.println(humidity);
  Serial.print(F("Pressure: "));
  Serial.println(pressure);
}

void handleCommand(JsonObject command) {
  // Handle command
  Serial.println(F("Processing command"));
  
  String cmd = command["type"];
  
  if (cmd == "led_on") {
    digitalWrite(LED_PIN, HIGH);
    Serial.println(F("LED turned on"));
  } else if (cmd == "led_off") {
    digitalWrite(LED_PIN, LOW);
    Serial.println(F("LED turned off"));
  } else if (cmd == "reboot") {
    Serial.println(F("Rebooting..."));
    delay(1000);
    asm volatile ("jmp 0");
  }
}

void handleStatusUpdate(JsonObject status) {
  // Handle status update
  Serial.println(F("Processing status update"));
  
  // Update local status
  if (status.containsKey("battery")) {
    node_info.battery_level = status["battery"];
  }
  
  if (status.containsKey("signal")) {
    node_info.signal_strength = status["signal"];
  }
}

void updateRoutingTable(String payload) {
  // Update routing table
  Serial.println(F("Updating routing table"));
  
  StaticJsonDocument<MAX_PAYLOAD_SIZE> doc;
  deserializeJson(doc, payload);
  
  // Process routing information
  // This would update the local routing table
}

void checkButtonPress() {
  static bool last_button_state = HIGH;
  static uint32_t last_button_time = 0;
  
  bool button_state = digitalRead(BUTTON_PIN);
  
  if (button_state != last_button_state) {
    if (button_state == LOW) {  // Button pressed
      uint32_t current_time = millis();
      if (current_time - last_button_time > 50) {  // Debounce
        handleButtonPress();
        last_button_time = current_time;
      }
    }
    last_button_state = button_state;
  }
}

void handleButtonPress() {
  Serial.println(F("Button pressed"));
  
  // Toggle LED
  digitalWrite(LED_PIN, !digitalRead(LED_PIN));
  
  // Send status update
  tx_message.type = MSG_DATA;
  tx_message.source_id = node_info.id;
  tx_message.dest_id = 0;  // Broadcast
  tx_message.sequence = message_sequence++;
  tx_message.timestamp = millis();
  
  // Create status payload
  StaticJsonDocument<MAX_PAYLOAD_SIZE> doc;
  doc["status"] = "button_pressed";
  doc["node_id"] = node_info.id;
  doc["battery"] = node_info.battery_level;
  doc["timestamp"] = millis();
  
  String payload = "";
  serializeJson(doc, payload);
  
  memcpy(tx_message.payload, payload.c_str(), min(payload.length(), MAX_PAYLOAD_SIZE));
  tx_message.payload_size = min(payload.length(), MAX_PAYLOAD_SIZE);
  
  tx_message.checksum = calculateChecksum(&tx_message);
  
  RF24NetworkHeader header(00, 'B');
  network.write(header, &tx_message, sizeof(Message));
}

float getBatteryLevel() {
  // Read battery voltage
  int raw_value = analogRead(BATTERY_PIN);
  float voltage = (raw_value * 5.0) / 1024.0;
  
  // Convert to battery percentage (assuming 3.3V battery)
  float percentage = (voltage / 3.3) * 100.0;
  percentage = constrain(percentage, 0.0, 100.0);
  
  return percentage;
}

void loadNodeConfig() {
  // Load node configuration from EEPROM
  Serial.println(F("Loading node configuration..."));
  
  // Read encryption key
  for (int i = 0; i < ENCRYPTION_KEY_SIZE; i++) {
    encryption_key[i] = EEPROM.read(i);
  }
  
  // Read node ID
  node_info.id = EEPROM.read(ENCRYPTION_KEY_SIZE);
  
  Serial.print(F("Node ID: "));
  Serial.println(node_info.id);
}

void saveNodeConfig() {
  // Save node configuration to EEPROM
  Serial.println(F("Saving node configuration..."));
  
  // Save encryption key
  for (int i = 0; i < ENCRYPTION_KEY_SIZE; i++) {
    EEPROM.write(i, encryption_key[i]);
  }
  
  // Save node ID
  EEPROM.write(ENCRYPTION_KEY_SIZE, node_info.id);
}

void initializeSecurity() {
  Serial.println(F("Initializing security..."));
  
  // Generate random challenge
  for (int i = 0; i < 16; i++) {
    challenge[i] = random(256);
  }
  
  // Initialize session key
  session_key = random(0xFFFFFFFF);
  
  Serial.println(F("Security initialized"));
}

void generateSecurityResponse() {
  // Generate security response based on challenge
  // This is a simplified implementation
  for (int i = 0; i < 16; i++) {
    response[i] = challenge[i] ^ encryption_key[i % ENCRYPTION_KEY_SIZE];
  }
}

bool verifySecurityResponse() {
  // Verify security response
  // This is a simplified implementation
  for (int i = 0; i < 16; i++) {
    if (response[i] != (challenge[i] ^ encryption_key[i % ENCRYPTION_KEY_SIZE])) {
      return false;
    }
  }
  return true;
}

uint8_t calculateChecksum(Message* msg) {
  // Calculate simple checksum
  uint8_t checksum = 0;
  uint8_t* data = (uint8_t*)msg;
  
  for (int i = 0; i < sizeof(Message) - 1; i++) {
    checksum ^= data[i];
  }
  
  return checksum;
}

bool verifyChecksum(Message* msg) {
  uint8_t calculated = calculateChecksum(msg);
  return calculated == msg->checksum;
}

void encryptMessage(Message* msg) {
  if (!encryption_enabled) return;
  
  // Simple XOR encryption
  for (int i = 0; i < msg->payload_size; i++) {
    msg->payload[i] ^= encryption_key[i % ENCRYPTION_KEY_SIZE];
  }
}

void decryptMessage(Message* msg) {
  if (!encryption_enabled) return;
  
  // Simple XOR decryption
  for (int i = 0; i < msg->payload_size; i++) {
    msg->payload[i] ^= encryption_key[i % ENCRYPTION_KEY_SIZE];
  }
} 