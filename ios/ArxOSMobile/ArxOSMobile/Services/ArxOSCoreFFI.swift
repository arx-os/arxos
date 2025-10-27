//
//  ArxOSCoreFFI.swift
//  ArxOSMobile
//
//  C FFI Integration for ArxOS
//

import Foundation

/// Wrapper class for ArxOS C FFI functions
class ArxOSCoreFFI {
    
    /// List all rooms
    func listRooms(buildingName: String, completion: @escaping (Result<[Room], Error>) -> Void) {
        // FFI implementation will be activated when Rust library is linked
        DispatchQueue.main.async {
            completion(.failure(TerminalError.ffiError("FFI library not linked")))
        }
    }
    
    /// Get a specific room
    func getRoom(buildingName: String, roomId: String, completion: @escaping (Result<Room, Error>) -> Void) {
        // FFI implementation will be activated when Rust library is linked
        DispatchQueue.main.async {
            completion(.failure(TerminalError.ffiError("FFI library not linked")))
        }
    }
    
    /// List all equipment
    func listEquipment(buildingName: String, completion: @escaping (Result<[Equipment], Error>) -> Void) {
        // FFI implementation will be activated when Rust library is linked
        DispatchQueue.main.async {
            completion(.failure(TerminalError.ffiError("FFI library not linked")))
        }
    }
    
    /// Get a specific equipment item
    func getEquipment(buildingName: String, equipmentId: String, completion: @escaping (Result<Equipment, Error>) -> Void) {
        // FFI implementation will be activated when Rust library is linked
        DispatchQueue.main.async {
            completion(.failure(TerminalError.ffiError("FFI library not linked")))
        }
    }
    
    /// Parse AR scan data
    func parseARScan(jsonData: String, completion: @escaping (Result<ARScanData, Error>) -> Void) {
        // FFI implementation will be activated when Rust library is linked
        DispatchQueue.main.async {
            completion(.failure(TerminalError.ffiError("FFI library not linked")))
        }
    }
    
    /// Extract equipment from AR scan
    func extractEquipment(jsonData: String, completion: @escaping (Result<[Equipment], Error>) -> Void) {
        // FFI implementation will be activated when Rust library is linked
        DispatchQueue.main.async {
            completion(.failure(TerminalError.ffiError("FFI library not linked")))
        }
    }
}

/// Error types
enum TerminalError: LocalizedError {
    case ffiError(String)
    case parseError(String)
    
    var errorDescription: String? {
        switch self {
        case .ffiError(let msg):
            return "FFI error: \(msg)"
        case .parseError(let msg):
            return "Parse error: \(msg)"
        }
    }
}
