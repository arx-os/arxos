/**
 * Arxos ESP32 Node Firmware
 * 
 * Turns an ESP32 into a building intelligence node
 * communicating via LoRa mesh network
 */

#include <Arduino.h>
#include <SPI.h>
#include <LoRa.h>

// Pin definitions for LoRa module
#define LORA_SCK 5
#define LORA_MISO 19
#define LORA_MOSI 27
#define LORA_CS 18
#define LORA_RST 14
#define LORA_IRQ 26

// ArxObject structure - 13 bytes
struct ArxObject {
    uint16_t id;
    uint8_t object_type;
    uint16_t x;
    uint16_t y; 
    uint16_t z;
    uint8_t properties[4];
} __attribute__((packed));

// Object types
const uint8_t TYPE_OUTLET = 0x10;
const uint8_t TYPE_SENSOR = 0x30;
const uint8_t TYPE_MESHTASTIC_NODE = 0x72;

// This node's identity
ArxObject thisNode = {
    .id = 0x0001,
    .object_type = TYPE_MESHTASTIC_NODE,
    .x = 0,
    .y = 0,
    .z = 0,
    .properties = {0, 0, 100, 0} // battery%, signal, etc
};

void setup() {
    Serial.begin(115200);
    Serial.println("Arxos Node Starting...");
    
    // Setup LoRa
    LoRa.setPins(LORA_CS, LORA_RST, LORA_IRQ);
    
    if (!LoRa.begin(915E6)) { // 915 MHz for US
        Serial.println("LoRa init failed!");
        while (1);
    }
    
    Serial.println("LoRa init succeeded!");
    Serial.print("Node ID: 0x");
    Serial.println(thisNode.id, HEX);
    Serial.println("Ready to join mesh network!");
}

void loop() {
    // Check for incoming packets
    int packetSize = LoRa.parsePacket();
    if (packetSize == sizeof(ArxObject)) {
        ArxObject received;
        LoRa.readBytes((uint8_t*)&received, sizeof(ArxObject));
        
        Serial.print("Received object 0x");
        Serial.print(received.id, HEX);
        Serial.print(" type 0x");
        Serial.println(received.object_type, HEX);
    }
    
    // Send heartbeat every 10 seconds
    static unsigned long lastSend = 0;
    if (millis() - lastSend > 10000) {
        lastSend = millis();
        
        // Update battery level (mock)
        thisNode.properties[0] = random(80, 100);
        
        // Send packet
        LoRa.beginPacket();
        LoRa.write((uint8_t*)&thisNode, sizeof(ArxObject));
        LoRa.endPacket();
        
        Serial.println("Heartbeat sent");
    }
}