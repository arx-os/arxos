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
    let lastMaintenance: String
    
    init(id: String, name: String, type: String, status: String, location: String, lastMaintenance: String) {
        self.id = id
        self.name = name
        self.type = type
        self.status = status
        self.location = location
        self.lastMaintenance = lastMaintenance
    }
    
    enum CodingKeys: String, CodingKey {
        case id
        case name
        case type = "equipment_type"
        case status
        case location
        case lastMaintenance = "last_maintenance"
    }
    
    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(String.self, forKey: .id)
        name = try container.decode(String.self, forKey: .name)
        type = try container.decode(String.self, forKey: .type)
        status = try container.decode(String.self, forKey: .status)
        location = try container.decode(String.self, forKey: .location)
        lastMaintenance = try container.decodeIfPresent(String.self, forKey: .lastMaintenance) ?? "Unknown"
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
    let roomName: String
    let floorLevel: Int32
    
    init(detectedEquipment: [DetectedEquipment], roomBoundaries: RoomBoundaries, deviceType: String? = nil, appVersion: String? = nil, scanDurationMs: Int64? = nil, pointCount: Int64? = nil, accuracyEstimate: Double? = nil, lightingConditions: String? = nil, roomName: String = "", floorLevel: Int32 = 0) {
        self.detectedEquipment = detectedEquipment
        self.roomBoundaries = roomBoundaries
        self.deviceType = deviceType
        self.appVersion = appVersion
        self.scanDurationMs = scanDurationMs
        self.pointCount = pointCount
        self.accuracyEstimate = accuracyEstimate
        self.lightingConditions = lightingConditions
        self.roomName = roomName
        self.floorLevel = floorLevel
    }
    
    enum CodingKeys: String, CodingKey {
        case detectedEquipment = "detected_equipment"
        case roomBoundaries = "room_boundaries"
        case deviceType = "device_type"
        case appVersion = "app_version"
        case scanDurationMs = "scan_duration_ms"
        case pointCount = "point_count"
        case accuracyEstimate = "accuracy_estimate"
        case lightingConditions = "lighting_conditions"
        case roomName = "roomName"
        case floorLevel = "floorLevel"
    }
}

/// Detected Equipment from AR Scan
struct DetectedEquipment: Identifiable, Codable {
    let id: UUID
    let name: String
    let type: String
    let position: Position3D
    let confidence: Double?
    let detectionMethod: String?
    let status: String
    let icon: String
    
    init(id: UUID = UUID(), name: String, type: String, position: Position3D, confidence: Double? = nil, detectionMethod: String? = nil, status: String = "Unknown", icon: String = "gear") {
        self.id = id
        self.name = name
        self.type = type
        self.position = position
        self.confidence = confidence
        self.detectionMethod = detectionMethod
        self.status = status
        self.icon = icon
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

