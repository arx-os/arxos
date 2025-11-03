//
//  ArxOSCoreFFI.swift
//  ArxOSMobile
//
//  C FFI Integration for ArxOS
//

import Foundation

// Import C FFI functions from the bridge
// These will be linked from libarxos when the framework is properly configured
@_silgen_name("arxos_list_rooms")
func arxos_list_rooms(_ buildingName: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_list_equipment")
func arxos_list_equipment(_ buildingName: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_get_room")
func arxos_get_room(_ buildingName: UnsafePointer<CChar>?, _ roomId: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_get_equipment")
func arxos_get_equipment(_ buildingName: UnsafePointer<CChar>?, _ equipmentId: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_parse_ar_scan")
func arxos_parse_ar_scan(_ jsonData: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_extract_equipment")
func arxos_extract_equipment(_ jsonData: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_process_ar_scan_to_pending")
func arxos_process_ar_scan_to_pending(_ jsonData: UnsafePointer<CChar>?, _ buildingName: UnsafePointer<CChar>?, _ confidenceThreshold: Double) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_export_for_ar")
func arxos_export_for_ar(_ buildingName: UnsafePointer<CChar>?, _ format: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_free_string")
func arxos_free_string(_ ptr: UnsafeMutablePointer<CChar>?)

/// Wrapper class for ArxOS C FFI functions
class ArxOSCoreFFI {
    
    /// Call FFI function and parse JSON result
    private func callFFI<T: Decodable>(
        function: (UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>?,
        input: String,
        errorMessage: String
    ) -> Result<T, Error> {
        guard let inputCString = input.cString(using: .utf8) else {
            return .failure(TerminalError.ffiError("Failed to convert input to C string"))
        }
        
        let resultPtr = inputCString.withUnsafeBufferPointer { buffer in
            function(buffer.baseAddress)
        }
        
        guard let resultPtr = resultPtr else {
            return .failure(TerminalError.ffiError("FFI call returned null pointer"))
        }
        
        let resultString = String(cString: resultPtr)
        arxos_free_string(resultPtr)
        
        guard let data = resultString.data(using: .utf8) else {
            return .failure(TerminalError.ffiError("Failed to convert result to data"))
        }
        
        do {
            let decoder = JSONDecoder()
            // Handle JSON responses that may wrap data
            if let wrapper = try? decoder.decode(FFIResponse<T>.self, from: data) {
                if let error = wrapper.error {
                    return .failure(TerminalError.ffiError(error))
                }
                if let data = wrapper.data {
                    return .success(data)
                }
            }
            
            // Try direct decoding
            let decoded = try decoder.decode(T.self, from: data)
            return .success(decoded)
        } catch {
            // Return mock data for now until FFI is fully integrated
            return .failure(TerminalError.ffiError("JSON parsing error: \(error.localizedDescription)"))
        }
    }
    
    /// List all rooms
    func listRooms(buildingName: String, completion: @escaping (Result<[Room], Error>) -> Void) {
        DispatchQueue.global().async {
            // TODO: Uncomment when FFI library is properly linked
            // let result = self.callFFI(function: arxos_list_rooms, input: buildingName, errorMessage: "Failed to list rooms")
            
            // For now, return empty array since FFI library isn't linked yet
            let result: Result<[Room], Error> = .success([])
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    /// Get a specific room
    func getRoom(buildingName: String, roomId: String, completion: @escaping (Result<Room, Error>) -> Void) {
        DispatchQueue.global().async {
            // TODO: Implement when FFI library is linked
            let result: Result<Room, Error> = .failure(TerminalError.ffiError("FFI library not linked"))
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    /// List all equipment
    func listEquipment(buildingName: String, completion: @escaping (Result<[Equipment], Error>) -> Void) {
        DispatchQueue.global().async {
            // TODO: Uncomment when FFI library is properly linked
            // let result = self.callFFI(function: arxos_list_equipment, input: buildingName, errorMessage: "Failed to list equipment")
            
            // For now, return empty array until FFI library is linked
            let result: Result<[Equipment], Error> = .success([])
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    /// Get a specific equipment item
    func getEquipment(buildingName: String, equipmentId: String, completion: @escaping (Result<Equipment, Error>) -> Void) {
        DispatchQueue.global().async {
            // TODO: Implement when FFI library is linked
            let result: Result<Equipment, Error> = .failure(TerminalError.ffiError("FFI library not linked"))
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    /// Parse AR scan data
    func parseARScan(jsonData: String, completion: @escaping (Result<ARScanData, Error>) -> Void) {
        DispatchQueue.global().async {
            // TODO: Implement when FFI library is linked
            let result: Result<ARScanData, Error> = .failure(TerminalError.ffiError("FFI library not linked"))
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    /// Extract equipment from AR scan
    func extractEquipment(jsonData: String, completion: @escaping (Result<[Equipment], Error>) -> Void) {
        DispatchQueue.global().async {
            // TODO: Implement when FFI library is linked
            let result: Result<[Equipment], Error> = .success([])
            DispatchQueue.main.async {
                completion(result)
            }
        }
    }
    
    /// Process AR scan and create pending equipment
    func processARScanToPending(jsonData: String, buildingName: String, confidenceThreshold: Double, completion: @escaping (Result<PendingARScanResult, Error>) -> Void) {
        DispatchQueue.global().async {
            guard let jsonCString = jsonData.cString(using: .utf8),
                  let buildingCString = buildingName.cString(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert input to C string")))
                }
                return
            }
            
            let resultPtr = jsonCString.withUnsafeBufferPointer { jsonBuffer in
                buildingCString.withUnsafeBufferPointer { buildingBuffer in
                    arxos_process_ar_scan_to_pending(jsonBuffer.baseAddress, buildingBuffer.baseAddress, confidenceThreshold)
                }
            }
            
            guard let resultPtr = resultPtr else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("FFI call returned null pointer")))
                }
                return
            }
            
            let resultString = String(cString: resultPtr)
            arxos_free_string(resultPtr)
            
            guard let data = resultString.data(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert result to data")))
                }
                return
            }
            
            do {
                let decoder = JSONDecoder()
                let result = try decoder.decode(PendingARScanResult.self, from: data)
                DispatchQueue.main.async {
                    completion(.success(result))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.parseError("Failed to parse pending scan result: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    /// Export building to AR format
    func exportForAR(buildingName: String, format: String, completion: @escaping (Result<ARExportResult, Error>) -> Void) {
        DispatchQueue.global().async {
            guard let buildingCString = buildingName.cString(using: .utf8),
                  let formatCString = format.cString(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert input to C string")))
                }
                return
            }
            
            let resultPtr = buildingCString.withUnsafeBufferPointer { buildingBuffer in
                formatCString.withUnsafeBufferPointer { formatBuffer in
                    arxos_export_for_ar(buildingBuffer.baseAddress, formatBuffer.baseAddress)
                }
            }
            
            guard let resultPtr = resultPtr else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("FFI call returned null pointer")))
                }
                return
            }
            
            let resultString = String(cString: resultPtr)
            arxos_free_string(resultPtr)
            
            guard let data = resultString.data(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert result to data")))
                }
                return
            }
            
            do {
                let decoder = JSONDecoder()
                let result = try decoder.decode(ARExportResult.self, from: data)
                DispatchQueue.main.async {
                    completion(.success(result))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.parseError("Failed to parse export result: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    /// Configure Git credentials for commits
    func configureGitCredentials(name: String, email: String, completion: @escaping (Result<Void, Error>) -> Void) {
        DispatchQueue.global().async {
            // TODO: Uncomment when FFI function is implemented
            // let result = self.callFFI(function: arxos_set_git_credentials, input: "\(name),\(email)", errorMessage: "Failed to configure Git credentials")
            // DispatchQueue.main.async {
            //     completion(result.map { _ in })
            // }
            
            // For now, simulate success
            print("Configuring Git: \(name) <\(email)>")
            DispatchQueue.main.async {
                completion(.success(()))
            }
        }
    }
}

/// Result from processing AR scan to pending
struct PendingARScanResult: Codable {
    let success: Bool
    let pendingCount: Int
    let pendingIds: [String]
    let building: String
    let confidenceThreshold: Double
    
    enum CodingKeys: String, CodingKey {
        case success
        case pendingCount = "pending_count"
        case pendingIds = "pending_ids"
        case building
        case confidenceThreshold = "confidence_threshold"
    }
}

/// Result from exporting for AR
struct ARExportResult: Codable {
    let success: Bool
    let building: String
    let format: String
    let outputFile: String
    let message: String
    
    enum CodingKeys: String, CodingKey {
        case success
        case building
        case format
        case outputFile = "output_file"
        case message
    }
}

/// Helper struct for parsing FFI responses
private struct FFIResponse<T: Decodable>: Decodable {
    let error: String?
    let data: T?
}

/// Error types
enum TerminalError: LocalizedError {
    case ffiError(String)
    case parseError(String)
    case unknownCommand(String)
    case invalidArguments
    
    var errorDescription: String? {
        switch self {
        case .ffiError(let msg):
            return "FFI error: \(msg)"
        case .parseError(let msg):
            return "Parse error: \(msg)"
        case .unknownCommand(let command):
            return "Unknown command: \(command)"
        case .invalidArguments:
            return "Invalid arguments provided"
        }
    }
}
