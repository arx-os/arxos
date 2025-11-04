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

@_silgen_name("arxos_get_room")
func arxos_get_room(_ buildingName: UnsafePointer<CChar>?, _ roomId: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_list_equipment")
func arxos_list_equipment(_ buildingName: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>?

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

@_silgen_name("arxos_load_ar_model")
func arxos_load_ar_model(_ buildingName: UnsafePointer<CChar>?, _ format: UnsafePointer<CChar>?, _ outputPath: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_save_ar_scan")
func arxos_save_ar_scan(_ jsonData: UnsafePointer<CChar>?, _ buildingName: UnsafePointer<CChar>?, _ confidenceThreshold: Double) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_list_pending_equipment")
func arxos_list_pending_equipment(_ buildingName: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_confirm_pending_equipment")
func arxos_confirm_pending_equipment(_ buildingName: UnsafePointer<CChar>?, _ pendingId: UnsafePointer<CChar>?, _ commitToGit: Int32) -> UnsafeMutablePointer<CChar>?

@_silgen_name("arxos_reject_pending_equipment")
func arxos_reject_pending_equipment(_ buildingName: UnsafePointer<CChar>?, _ pendingId: UnsafePointer<CChar>?) -> UnsafeMutablePointer<CChar>?

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
            return .failure(TerminalError.ffiError("JSON parsing error: \(error.localizedDescription)"))
        }
    }
    
    /// List all rooms
    func listRooms(buildingName: String, completion: @escaping (Result<[Room], Error>) -> Void) {
        DispatchQueue.global().async {
            guard let buildingCString = buildingName.cString(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert building name to C string")))
                }
                return
            }
            
            let resultPtr = buildingCString.withUnsafeBufferPointer { buffer in
                arxos_list_rooms(buffer.baseAddress)
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
                let roomInfos = try decoder.decode([RoomInfo].self, from: data)
                // Convert RoomInfo to Room
                let rooms = roomInfos.map { roomInfo in
                    Room(
                        id: roomInfo.id,
                        name: roomInfo.name,
                        floor: Int(roomInfo.position.z), // Use Z coordinate as floor level
                        wing: roomInfo.properties["wing"] ?? "",
                        roomType: roomInfo.roomType
                    )
                }
                DispatchQueue.main.async {
                    completion(.success(rooms))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.parseError("Failed to parse rooms: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    /// Get a specific room
    func getRoom(buildingName: String, roomId: String, completion: @escaping (Result<Room, Error>) -> Void) {
        DispatchQueue.global().async {
            guard let buildingCString = buildingName.cString(using: .utf8),
                  let roomIdCString = roomId.cString(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert input to C string")))
                }
                return
            }
            
            let resultPtr = buildingCString.withUnsafeBufferPointer { buildingBuffer in
                roomIdCString.withUnsafeBufferPointer { roomIdBuffer in
                    arxos_get_room(buildingBuffer.baseAddress, roomIdBuffer.baseAddress)
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
                let roomInfo = try decoder.decode(RoomInfo.self, from: data)
                // Convert RoomInfo to Room
                let room = Room(
                    id: roomInfo.id,
                    name: roomInfo.name,
                    floor: Int(roomInfo.position.z), // Use Z coordinate as floor level
                    wing: roomInfo.properties["wing"] ?? "",
                    roomType: roomInfo.roomType
                )
                DispatchQueue.main.async {
                    completion(.success(room))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.parseError("Failed to parse room: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    /// List all equipment
    func listEquipment(buildingName: String, completion: @escaping (Result<[Equipment], Error>) -> Void) {
        DispatchQueue.global().async {
            guard let buildingCString = buildingName.cString(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert building name to C string")))
                }
                return
            }
            
            let resultPtr = buildingCString.withUnsafeBufferPointer { buffer in
                arxos_list_equipment(buffer.baseAddress)
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
                let equipmentInfos = try decoder.decode([EquipmentInfo].self, from: data)
                // Convert EquipmentInfo to Equipment
                let equipment = equipmentInfos.map { eqInfo in
                    Equipment(
                        id: eqInfo.id,
                        name: eqInfo.name,
                        type: eqInfo.equipmentType,
                        status: eqInfo.status,
                        location: String(format: "X:%.1f Y:%.1f Z:%.1f", eqInfo.position.x, eqInfo.position.y, eqInfo.position.z),
                        lastMaintenance: eqInfo.properties["last_maintenance"] ?? "Unknown"
                    )
                }
                DispatchQueue.main.async {
                    completion(.success(equipment))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.parseError("Failed to parse equipment: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    /// Get a specific equipment item
    func getEquipment(buildingName: String, equipmentId: String, completion: @escaping (Result<Equipment, Error>) -> Void) {
        DispatchQueue.global().async {
            guard let buildingCString = buildingName.cString(using: .utf8),
                  let equipmentIdCString = equipmentId.cString(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert input to C string")))
                }
                return
            }
            
            let resultPtr = buildingCString.withUnsafeBufferPointer { buildingBuffer in
                equipmentIdCString.withUnsafeBufferPointer { equipmentIdBuffer in
                    arxos_get_equipment(buildingBuffer.baseAddress, equipmentIdBuffer.baseAddress)
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
                let eqInfo = try decoder.decode(EquipmentInfo.self, from: data)
                // Convert EquipmentInfo to Equipment
                let equipment = Equipment(
                    id: eqInfo.id,
                    name: eqInfo.name,
                    type: eqInfo.equipmentType,
                    status: eqInfo.status,
                    location: String(format: "X:%.1f Y:%.1f Z:%.1f", eqInfo.position.x, eqInfo.position.y, eqInfo.position.z),
                    lastMaintenance: eqInfo.properties["last_maintenance"] ?? "Unknown"
                )
                DispatchQueue.main.async {
                    completion(.success(equipment))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.parseError("Failed to parse equipment: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    /// Parse AR scan data
    func parseARScan(jsonData: String, completion: @escaping (Result<ARScanData, Error>) -> Void) {
        DispatchQueue.global().async {
            guard let jsonCString = jsonData.cString(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert JSON data to C string")))
                }
                return
            }
            
            let resultPtr = jsonCString.withUnsafeBufferPointer { buffer in
                arxos_parse_ar_scan(buffer.baseAddress)
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
                let scanData = try decoder.decode(ARScanData.self, from: data)
                DispatchQueue.main.async {
                    completion(.success(scanData))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.parseError("Failed to parse AR scan data: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    /// Extract equipment from AR scan
    func extractEquipment(jsonData: String, completion: @escaping (Result<[Equipment], Error>) -> Void) {
        DispatchQueue.global().async {
            guard let jsonCString = jsonData.cString(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert JSON data to C string")))
                }
                return
            }
            
            let resultPtr = jsonCString.withUnsafeBufferPointer { buffer in
                arxos_extract_equipment(buffer.baseAddress)
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
                let equipmentInfos = try decoder.decode([EquipmentInfo].self, from: data)
                // Convert EquipmentInfo to Equipment
                let equipment = equipmentInfos.map { eqInfo in
                    Equipment(
                        id: eqInfo.id,
                        name: eqInfo.name,
                        type: eqInfo.equipmentType,
                        status: eqInfo.status,
                        location: String(format: "X:%.1f Y:%.1f Z:%.1f", eqInfo.position.x, eqInfo.position.y, eqInfo.position.z),
                        lastMaintenance: eqInfo.properties["last_maintenance"] ?? "Unknown"
                    )
                }
                DispatchQueue.main.async {
                    completion(.success(equipment))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.parseError("Failed to parse extracted equipment: \(error.localizedDescription)")))
                }
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
    
    /// Load/export building model for AR viewing
    /// 
    /// Exports a building to AR-compatible format (USDZ or glTF) and returns the file path.
    /// If outputPath is nil, a temporary file will be created.
    ///
    /// - Parameters:
    ///   - buildingName: Name of building to export
    ///   - format: Export format: "usdz" or "gltf" (case-insensitive)
    ///   - outputPath: Optional path where model should be saved (nil for temp file)
    ///   - completion: Completion handler with ARModelLoadResult or Error
    func loadARModel(
        buildingName: String,
        format: String,
        outputPath: String? = nil,
        completion: @escaping (Result<ARModelLoadResult, Error>) -> Void
    ) {
        DispatchQueue.global().async {
            guard let buildingCString = buildingName.cString(using: .utf8),
                  let formatCString = format.cString(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert input to C string")))
                }
                return
            }
            
            let outputCString = outputPath?.cString(using: .utf8)
            
            let resultPtr = buildingCString.withUnsafeBufferPointer { buildingBuffer in
                formatCString.withUnsafeBufferPointer { formatBuffer in
                    if let outputCString = outputCString {
                        return outputCString.withUnsafeBufferPointer { outputBuffer in
                            arxos_load_ar_model(buildingBuffer.baseAddress, formatBuffer.baseAddress, outputBuffer.baseAddress)
                        }
                    } else {
                        return arxos_load_ar_model(buildingBuffer.baseAddress, formatBuffer.baseAddress, nil)
                    }
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
                let result = try decoder.decode(ARModelLoadResult.self, from: data)
                DispatchQueue.main.async {
                    completion(.success(result))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.parseError("Failed to parse model load result: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    /// Save AR scan data and process to pending equipment
    ///
    /// Accepts AR scan data from mobile devices, saves it to a file for debugging/audit,
    /// and processes it to create pending equipment items that can be reviewed and confirmed.
    ///
    /// - Parameters:
    ///   - scanData: AR scan data to save and process
    ///   - buildingName: Name of building for context
    ///   - confidenceThreshold: Minimum confidence score (0.0-1.0) to create pending items
    ///   - completion: Completion handler with ARScanSaveResult or Error
    func saveARScan(
        scanData: ARScanData,
        buildingName: String,
        confidenceThreshold: Double = 0.7,
        completion: @escaping (Result<ARScanSaveResult, Error>) -> Void
    ) {
        DispatchQueue.global().async {
            // Convert ARScanData to JSON
            guard let jsonData = try? JSONEncoder().encode(scanData),
                  let jsonString = String(data: jsonData, encoding: .utf8),
                  let jsonCString = jsonString.cString(using: .utf8),
                  let buildingCString = buildingName.cString(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert scan data to C string")))
                }
                return
            }
            
            let resultPtr = jsonCString.withUnsafeBufferPointer { jsonBuffer in
                buildingCString.withUnsafeBufferPointer { buildingBuffer in
                    arxos_save_ar_scan(jsonBuffer.baseAddress, buildingBuffer.baseAddress, confidenceThreshold)
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
                let result = try decoder.decode(ARScanSaveResult.self, from: data)
                DispatchQueue.main.async {
                    completion(.success(result))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.parseError("Failed to parse scan save result: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    /// List pending equipment for a building
    ///
    /// - Parameters:
    ///   - buildingName: Name of building
    ///   - completion: Completion handler with PendingEquipmentListResult or Error
    func listPendingEquipment(
        buildingName: String,
        completion: @escaping (Result<PendingEquipmentListResult, Error>) -> Void
    ) {
        DispatchQueue.global().async {
            guard let buildingCString = buildingName.cString(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert building name to C string")))
                }
                return
            }
            
            let resultPtr = buildingCString.withUnsafeBufferPointer { buffer in
                arxos_list_pending_equipment(buffer.baseAddress)
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
                let result = try decoder.decode(PendingEquipmentListResult.self, from: data)
                DispatchQueue.main.async {
                    completion(.success(result))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.parseError("Failed to parse pending equipment list: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    /// Confirm pending equipment and add to building data
    ///
    /// - Parameters:
    ///   - buildingName: Name of building
    ///   - pendingId: ID of pending equipment to confirm
    ///   - commitToGit: Whether to commit changes to Git
    ///   - completion: Completion handler with PendingEquipmentConfirmResult or Error
    func confirmPendingEquipment(
        buildingName: String,
        pendingId: String,
        commitToGit: Bool = true,
        completion: @escaping (Result<PendingEquipmentConfirmResult, Error>) -> Void
    ) {
        DispatchQueue.global().async {
            guard let buildingCString = buildingName.cString(using: .utf8),
                  let pendingIdCString = pendingId.cString(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert input to C string")))
                }
                return
            }
            
            let resultPtr = buildingCString.withUnsafeBufferPointer { buildingBuffer in
                pendingIdCString.withUnsafeBufferPointer { pendingBuffer in
                    arxos_confirm_pending_equipment(buildingBuffer.baseAddress, pendingBuffer.baseAddress, commitToGit ? 1 : 0)
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
                let result = try decoder.decode(PendingEquipmentConfirmResult.self, from: data)
                DispatchQueue.main.async {
                    completion(.success(result))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.parseError("Failed to parse confirmation result: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    /// Reject pending equipment
    ///
    /// - Parameters:
    ///   - buildingName: Name of building
    ///   - pendingId: ID of pending equipment to reject
    ///   - completion: Completion handler with PendingEquipmentRejectResult or Error
    func rejectPendingEquipment(
        buildingName: String,
        pendingId: String,
        completion: @escaping (Result<PendingEquipmentRejectResult, Error>) -> Void
    ) {
        DispatchQueue.global().async {
            guard let buildingCString = buildingName.cString(using: .utf8),
                  let pendingIdCString = pendingId.cString(using: .utf8) else {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.ffiError("Failed to convert input to C string")))
                }
                return
            }
            
            let resultPtr = buildingCString.withUnsafeBufferPointer { buildingBuffer in
                pendingIdCString.withUnsafeBufferPointer { pendingBuffer in
                    arxos_reject_pending_equipment(buildingBuffer.baseAddress, pendingBuffer.baseAddress)
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
                let result = try decoder.decode(PendingEquipmentRejectResult.self, from: data)
                DispatchQueue.main.async {
                    completion(.success(result))
                }
            } catch {
                DispatchQueue.main.async {
                    completion(.failure(TerminalError.parseError("Failed to parse rejection result: \(error.localizedDescription)")))
                }
            }
        }
    }
    
    /// Configure Git credentials for commits
    ///
    /// Note: This function currently stores credentials locally in the app.
    /// The Rust backend does not have a dedicated FFI function for this yet.
    /// Git credentials are configured via the Git config system when commits are made.
    func configureGitCredentials(name: String, email: String, completion: @escaping (Result<Void, Error>) -> Void) {
        DispatchQueue.global().async {
            // Store credentials locally for use in Git operations
            // The Rust backend will use these when creating commits via PersistenceManager
            UserDefaults.standard.set(name, forKey: "git_author_name")
            UserDefaults.standard.set(email, forKey: "git_author_email")
            
            print("Git credentials configured: \(name) <\(email)>")
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

/// Result from loading AR model
struct ARModelLoadResult: Codable {
    let success: Bool
    let building: String
    let format: String
    let filePath: String
    let fileSize: UInt64
    let message: String
    
    enum CodingKeys: String, CodingKey {
        case success
        case building
        case format
        case filePath = "file_path"
        case fileSize = "file_size"
        case message
    }
}

/// Result from saving AR scan
struct ARScanSaveResult: Codable {
    let success: Bool
    let building: String
    let pendingCount: Int
    let pendingIds: [String]
    let confidenceThreshold: Double
    let scanTimestamp: String
    let scanFile: String?
    let message: String
    
    enum CodingKeys: String, CodingKey {
        case success
        case building
        case pendingCount = "pending_count"
        case pendingIds = "pending_ids"
        case confidenceThreshold = "confidence_threshold"
        case scanTimestamp = "scan_timestamp"
        case scanFile = "scan_file"
        case message
    }
}

/// Result from listing pending equipment
struct PendingEquipmentListResult: Codable {
    let success: Bool
    let building: String
    let pendingCount: Int
    let pendingItems: [PendingEquipmentItem]
    
    enum CodingKeys: String, CodingKey {
        case success
        case building
        case pendingCount = "pending_count"
        case pendingItems = "pending_items"
    }
}

/// Pending equipment item
struct PendingEquipmentItem: Identifiable, Codable {
    let id: String
    let name: String
    let equipmentType: String
    let position: Position3D
    let confidence: Double
    let detectionMethod: String
    let detectedAt: String
    let floorLevel: Int32
    let roomName: String?
    let status: String
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case equipmentType = "equipment_type"
        case position
        case confidence
        case detectionMethod = "detection_method"
        case detectedAt = "detected_at"
        case floorLevel = "floor_level"
        case roomName = "room_name"
        case status
    }
}

/// Result from confirming pending equipment
struct PendingEquipmentConfirmResult: Codable {
    let success: Bool
    let building: String
    let pendingId: String
    let equipmentId: String
    let committed: Bool
    let commitId: String?
    let message: String
    
    enum CodingKeys: String, CodingKey {
        case success
        case building
        case pendingId = "pending_id"
        case equipmentId = "equipment_id"
        case committed
        case commitId = "commit_id"
        case message
    }
}

/// Result from rejecting pending equipment
struct PendingEquipmentRejectResult: Codable {
    let success: Bool
    let building: String
    let pendingId: String
    let message: String
    
    enum CodingKeys: String, CodingKey {
        case success
        case building
        case pendingId = "pending_id"
        case message
    }
}

/// RoomInfo from Rust FFI (matches Rust RoomInfo struct)
struct RoomInfo: Codable {
    let id: String
    let name: String
    let roomType: String
    let position: Position
    let properties: [String: String]
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case roomType = "room_type"
        case position
        case properties
    }
}

/// EquipmentInfo from Rust FFI (matches Rust EquipmentInfo struct)
struct EquipmentInfo: Codable {
    let id: String
    let name: String
    let equipmentType: String
    let status: String
    let position: Position
    let properties: [String: String]
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case equipmentType = "equipment_type"
        case status
        case position
        case properties
    }
}

/// Position from Rust FFI (matches Rust Position struct)
struct Position: Codable {
    let x: Double
    let y: Double
    let z: Double
    let coordinateSystem: String
    
    enum CodingKeys: String, CodingKey {
        case x
        case y
        case z
        case coordinateSystem = "coordinate_system"
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
