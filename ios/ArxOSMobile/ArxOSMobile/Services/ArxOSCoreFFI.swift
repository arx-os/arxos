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
        DispatchQueue.global().async {
            // For now, return empty array since FFI library isn't linked yet
            // When Rust library is linked, call: arxos_list_rooms(buildingName)
            let result: Result<[Room], Error> = .success([])
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    /// Get a specific room
    func getRoom(buildingName: String, roomId: String, completion: @escaping (Result<Room, Error>) -> Void) {
        DispatchQueue.global().async {
            // For now, return error
            let result: Result<Room, Error> = .failure(TerminalError.ffiError("FFI library not linked"))
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    /// List all equipment
    func listEquipment(buildingName: String, completion: @escaping (Result<[Equipment], Error>) -> Void) {
        DispatchQueue.global().async {
            // For now, return empty array - will be replaced with actual FFI call when library is linked
            // When Rust library is linked:
            // let cString = buildingName.cString(using: .utf8)
            // let resultPtr = arxos_list_equipment(cString)
            // let resultString = String(cString: resultPtr)
            // arxos_free_string(resultPtr)
            // Parse JSON and return
            
            let result: Result<[Equipment], Error> = .success([])
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    /// Get a specific equipment item
    func getEquipment(buildingName: String, equipmentId: String, completion: @escaping (Result<Equipment, Error>) -> Void) {
        DispatchQueue.global().async {
            let result: Result<Equipment, Error> = .failure(TerminalError.ffiError("FFI library not linked"))
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    /// Parse AR scan data
    func parseARScan(jsonData: String, completion: @escaping (Result<ARScanData, Error>) -> Void) {
        DispatchQueue.global().async {
            let result: Result<ARScanData, Error> = .failure(TerminalError.ffiError("FFI library not linked"))
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    /// Extract equipment from AR scan
    func extractEquipment(jsonData: String, completion: @escaping (Result<[Equipment], Error>) -> Void) {
        DispatchQueue.global().async {
            let result: Result<[Equipment], Error> = .success([])
            DispatchQueue.main.async {
                completion(result)
            }
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
