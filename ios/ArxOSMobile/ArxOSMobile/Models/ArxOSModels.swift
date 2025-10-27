import Foundation

/// Room data model
struct Room: Identifiable, Codable {
    let id: String
    let name: String
    let floor: Int
    let wing: String
    let roomType: String
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case floor
        case wing
        case roomType = "room_type"
    }
}

/// Equipment data model
struct Equipment: Identifiable, Codable {
    let id: String
    let name: String
    let type: String
    let status: String
    let location: String
    let lastMaintenance: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case type = "equipment_type"
        case status
        case location
        case lastMaintenance = "last_maintenance"
    }
}

/// AR Scan Data model
struct ARScanData: Codable {
    let detectedEquipment: [DetectedEquipment]
    let roomBoundaries: RoomBoundaries
    let deviceType: String?
    let appVersion: String?
    let scanDurationMs: Int64?
    let pointCount: Int64?
    let accuracyEstimate: Double?
    let lightingConditions: String?
    
    enum CodingKeys: String, CodingKey {
        case detectedEquipment = "detected_equipment"
        case roomBoundaries = "room_boundaries"
        case deviceType = "device_type"
        case appVersion = "app_version"
        case scanDurationMs = "scan_duration_ms"
        case pointCount = "point_count"
        case accuracyEstimate = "accuracy_estimate"
        case lightingConditions = "lighting_conditions"
    }
}

/// Detected Equipment from AR Scan
struct DetectedEquipment: Identifiable, Codable {
    let id: UUID?
    let name: String
    let type: String
    let position: Position3D
    let confidence: Double?
    let detectionMethod: String?
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case type
        case position
        case confidence
        case detectionMethod = "detection_method"
    }
}

/// 3D Position
struct Position3D: Codable {
    let x: Double
    let y: Double
    let z: Double
}

/// Room Boundaries
struct RoomBoundaries: Codable {
    let walls: [Wall]
    let openings: [Opening]
}

/// Wall structure
struct Wall: Codable {
    let startPoint: Position3D
    let endPoint: Position3D
    let height: Double
    let thickness: Double
    
    enum CodingKeys: String, CodingKey {
        case startPoint = "start_point"
        case endPoint = "end_point"
        case height
        case thickness
    }
}

/// Opening (door/window) structure
struct Opening: Codable {
    let position: Position3D
    let width: Double
    let height: Double
    let type: String
}

