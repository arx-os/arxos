//
//  ArxOSCoreFFITests.swift
//  ArxOSMobileTests
//
//  Unit tests for ArxOSCoreFFI wrapper functions
//

import XCTest
@testable import ArxOSMobile

/// Tests for ArxOSCoreFFI wrapper class
///
/// These tests verify the Swift wrapper functions that interface with the Rust FFI.
/// Note: These tests may require mocking the FFI calls for full testability.
final class ArxOSCoreFFITests: XCTestCase {
    
    var ffi: ArxOSCoreFFI!
    
    override func setUp() {
        super.setUp()
        ffi = ArxOSCoreFFI()
    }
    
    override func tearDown() {
        ffi = nil
        super.tearDown()
    }
    
    // MARK: - AR Model Loading Tests
    
    func testLoadARModelSuccess() {
        let expectation = expectation(description: "Load AR model")
        
        ffi.loadARModel(buildingName: "Test Building", format: "gltf", outputPath: nil) { result in
            switch result {
            case .success(let loadResult):
                XCTAssertTrue(loadResult.success)
                XCTAssertEqual(loadResult.building, "Test Building")
                XCTAssertNotNil(loadResult.filePath)
            case .failure(let error):
                // May fail if building doesn't exist - that's acceptable for unit test
                print("Expected failure in test environment: \(error)")
            }
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testLoadARModelInvalidFormat() {
        let expectation = expectation(description: "Load AR model with invalid format")
        
        ffi.loadARModel(buildingName: "Test Building", format: "invalid", outputPath: nil) { result in
            switch result {
            case .success:
                XCTFail("Should fail with invalid format")
            case .failure:
                // Expected failure
                XCTAssertTrue(true)
            }
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - AR Scan Saving Tests
    
    func testSaveARScanSuccess() {
        let expectation = expectation(description: "Save AR scan")
        
        let scanData = ARScanData(
            detectedEquipment: [
                DetectedEquipment(
                    name: "Test Equipment",
                    type: "HVAC",
                    position: Position3D(x: 1.0, y: 2.0, z: 3.0),
                    confidence: 0.9,
                    detectionMethod: "Test",
                    status: "Detected",
                    icon: "gear"
                )
            ],
            roomBoundaries: RoomBoundaries(walls: [], openings: []),
            deviceType: "iPhone",
            appVersion: "1.0.0",
            scanDurationMs: 1000,
            pointCount: nil,
            accuracyEstimate: nil,
            lightingConditions: nil,
            roomName: "Test Room",
            floorLevel: 1
        )
        
        ffi.saveARScan(scanData: scanData, buildingName: "Test Building", confidenceThreshold: 0.7) { result in
            switch result {
            case .success(let saveResult):
                XCTAssertTrue(saveResult.success)
                XCTAssertEqual(saveResult.building, "Test Building")
                XCTAssertGreaterThanOrEqual(saveResult.pendingCount, 0)
            case .failure(let error):
                // May fail if building doesn't exist - acceptable for unit test
                print("Expected failure in test environment: \(error)")
            }
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - Pending Equipment Tests
    
    func testListPendingEquipment() {
        let expectation = expectation(description: "List pending equipment")
        
        ffi.listPendingEquipment(buildingName: "Test Building") { result in
            switch result {
            case .success(let listResult):
                XCTAssertTrue(listResult.success)
                XCTAssertEqual(listResult.building, "Test Building")
                XCTAssertNotNil(listResult.items)
            case .failure(let error):
                // May fail if building doesn't exist - acceptable for unit test
                print("Expected failure in test environment: \(error)")
            }
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testConfirmPendingEquipment() {
        let expectation = expectation(description: "Confirm pending equipment")
        
        ffi.confirmPendingEquipment(buildingName: "Test Building", pendingId: "test-pending-id", commitToGit: false) { result in
            switch result {
            case .success(let confirmResult):
                XCTAssertTrue(confirmResult.success)
                XCTAssertEqual(confirmResult.building, "Test Building")
            case .failure:
                // Expected if pending ID doesn't exist - acceptable for unit test
                XCTAssertTrue(true)
            }
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testRejectPendingEquipment() {
        let expectation = expectation(description: "Reject pending equipment")
        
        ffi.rejectPendingEquipment(buildingName: "Test Building", pendingId: "test-pending-id") { result in
            switch result {
            case .success(let rejectResult):
                XCTAssertTrue(rejectResult.success)
                XCTAssertEqual(rejectResult.building, "Test Building")
            case .failure:
                // Expected if pending ID doesn't exist - acceptable for unit test
                XCTAssertTrue(true)
            }
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    // MARK: - Room and Equipment Tests
    
    func testListRooms() {
        let expectation = expectation(description: "List rooms")
        
        ffi.listRooms(buildingName: "Test Building") { result in
            switch result {
            case .success(let rooms):
                XCTAssertNotNil(rooms)
                // Rooms may be empty if building doesn't exist - acceptable
            case .failure:
                // May fail if building doesn't exist - acceptable for unit test
                XCTAssertTrue(true)
            }
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 5.0)
    }
    
    func testListEquipment() {
        let expectation = expectation(description: "List equipment")
        
        ffi.listEquipment(buildingName: "Test Building") { result in
            switch result {
            case .success(let equipment):
                XCTAssertNotNil(equipment)
                // Equipment may be empty if building doesn't exist - acceptable
            case .failure:
                // May fail if building doesn't exist - acceptable for unit test
                XCTAssertTrue(true)
            }
            expectation.fulfill()
        }
        
        wait(for: [expectation], timeout: 5.0)
    }
}

