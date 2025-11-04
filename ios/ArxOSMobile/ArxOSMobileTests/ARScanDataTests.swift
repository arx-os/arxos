//
//  ARScanDataTests.swift
//  ArxOSMobileTests
//
//  Unit tests for AR scan data models
//

import XCTest
@testable import ArxOSMobile

/// Tests for ARScanData model serialization
final class ARScanDataTests: XCTestCase {
    
    func testARScanDataEncoding() {
        let scanData = ARScanData(
            detectedEquipment: [
                DetectedEquipment(
                    name: "VAV-301",
                    type: "HVAC",
                    position: Position3D(x: 10.0, y: 20.0, z: 3.0),
                    confidence: 0.9,
                    detectionMethod: "ARKit",
                    status: "Detected",
                    icon: "gear"
                )
            ],
            roomBoundaries: RoomBoundaries(walls: [], openings: []),
            deviceType: "iPhone 15 Pro",
            appVersion: "1.0.0",
            scanDurationMs: 5000,
            pointCount: 1000,
            accuracyEstimate: 0.95,
            lightingConditions: "Good",
            roomName: "Room 301",
            floorLevel: 3
        )
        
        // Test encoding to JSON
        let encoder = JSONEncoder()
        encoder.outputFormatting = .prettyPrinted
        
        do {
            let jsonData = try encoder.encode(scanData)
            XCTAssertNotNil(jsonData)
            
            // Verify JSON structure
            let json = try JSONSerialization.jsonObject(with: jsonData) as? [String: Any]
            XCTAssertNotNil(json)
            XCTAssertEqual(json?["roomName"] as? String, "Room 301")
            XCTAssertEqual(json?["floorLevel"] as? Int32, 3)
            
            // Verify detectedEquipment array
            if let equipment = json?["detectedEquipment"] as? [[String: Any]] {
                XCTAssertEqual(equipment.count, 1)
                XCTAssertEqual(equipment[0]["name"] as? String, "VAV-301")
                XCTAssertEqual(equipment[0]["type"] as? String, "HVAC")
            } else {
                XCTFail("detectedEquipment should be an array")
            }
        } catch {
            XCTFail("Failed to encode ARScanData: \(error)")
        }
    }
    
    func testDetectedEquipmentEncoding() {
        let equipment = DetectedEquipment(
            name: "Test Equipment",
            type: "Electrical",
            position: Position3D(x: 1.0, y: 2.0, z: 3.0),
            confidence: 0.8,
            detectionMethod: "Tap-to-Place",
            status: "Placed",
            icon: "bolt"
        )
        
        let encoder = JSONEncoder()
        
        do {
            let jsonData = try encoder.encode(equipment)
            let json = try JSONSerialization.jsonObject(with: jsonData) as? [String: Any]
            
            // Verify only expected fields are encoded (excludes SwiftUI-specific fields)
            XCTAssertEqual(json?["name"] as? String, "Test Equipment")
            XCTAssertEqual(json?["type"] as? String, "Electrical")
            XCTAssertNotNil(json?["confidence"] as? Double)
            XCTAssertEqual(json?["detectionMethod"] as? String, "Tap-to-Place")
            
            // Verify SwiftUI-specific fields are NOT in JSON
            XCTAssertNil(json?["id"])
            XCTAssertNil(json?["status"])
            XCTAssertNil(json?["icon"])
        } catch {
            XCTFail("Failed to encode DetectedEquipment: \(error)")
        }
    }
    
    func testDetectedEquipmentDefaultConfidence() {
        // Test that nil confidence defaults to 0.7 in encoding
        let equipment = DetectedEquipment(
            name: "Test",
            type: "Unknown",
            position: Position3D(x: 0, y: 0, z: 0),
            confidence: nil,
            detectionMethod: nil,
            status: "Unknown",
            icon: "gear"
        )
        
        let encoder = JSONEncoder()
        
        do {
            let jsonData = try encoder.encode(equipment)
            let json = try JSONSerialization.jsonObject(with: jsonData) as? [String: Any]
            
            // Should have default confidence value
            if let confidence = json?["confidence"] as? Double {
                XCTAssertEqual(confidence, 0.7, accuracy: 0.01)
            } else {
                XCTFail("confidence should be encoded with default value")
            }
        } catch {
            XCTFail("Failed to encode DetectedEquipment: \(error)")
        }
    }
}

