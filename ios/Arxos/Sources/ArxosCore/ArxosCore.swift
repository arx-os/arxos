// ArxosCore — thin Swift façade over UniFFI → Rust arxos-core.
//
// Exactly one data path: real UniFFI bindings to the content-addressed store.
// No parallel CAS, no pseudo-CIDs, no fallback implementations.

import Foundation
import Security

// MARK: - Public models

public struct BuildingSummary: Equatable, Sendable {
    public var buildingId: String
    public var name: String?
    public var headRoot: String?
    public var buildingObject: String?
    public var stagedCount: UInt64

    public init(
        buildingId: String,
        name: String? = nil,
        headRoot: String? = nil,
        buildingObject: String? = nil,
        stagedCount: UInt64 = 0
    ) {
        self.buildingId = buildingId
        self.name = name
        self.headRoot = headRoot
        self.buildingObject = buildingObject
        self.stagedCount = stagedCount
    }
}

public struct CapturePutResult: Equatable, Sendable {
    public var cid: String
    public var objectType: String
}

public struct CommitSummary: Equatable, Sendable {
    public var rootCid: String
    public var buildingId: String
    public var objectCount: UInt64
    public var previousRoot: String?
}

public struct AnnotationOverlay: Equatable, Identifiable, Sendable {
    public var id: String { cid }
    public var cid: String
    public var text: String
    public var x: Double
    public var y: Double
    public var z: Double
    public var distanceM: Double
}

public struct RoomPlanSurface: Equatable, Sendable {
    public var id: String
    public var category: String
    public var transform: [Double]
    public var dimensions: [Double]

    public init(id: String, category: String, transform: [Double], dimensions: [Double]) {
        self.id = id
        self.category = category
        self.transform = transform
        self.dimensions = dimensions
    }
}

public struct RoomPlanObject: Equatable, Sendable {
    public var id: String
    public var category: String
    public var transform: [Double]
    public var dimensions: [Double]

    public init(id: String, category: String, transform: [Double], dimensions: [Double]) {
        self.id = id
        self.category = category
        self.transform = transform
        self.dimensions = dimensions
    }
}

public struct IngestSummary: Equatable, Sendable {
    public var spaceCid: String
    public var surfaceCids: [String]
    public var objectCids: [String]

    public init(spaceCid: String, surfaceCids: [String], objectCids: [String]) {
        self.spaceCid = spaceCid
        self.surfaceCids = surfaceCids
        self.objectCids = objectCids
    }
}

public struct SpatialItem: Equatable, Sendable {
    public var cid: String
    public var objectType: String
    public var name: String?
    public var x: Double
    public var y: Double
    public var z: Double
    public var properties: [String: String]

    public init(
        cid: String,
        objectType: String,
        name: String?,
        x: Double,
        y: Double,
        z: Double,
        properties: [String: String]
    ) {
        self.cid = cid
        self.objectType = objectType
        self.name = name
        self.x = x
        self.y = y
        self.z = z
        self.properties = properties
    }
}

public struct MergeResultSummary: Equatable, Sendable {
    public var rootCid: String
    public var objectCount: UInt64
    public var kept: UInt64
    public var dedupedAnnotations: UInt64
    public var spatialIndexRoot: String?
    public var parentA: String
    public var parentB: String

    public init(
        rootCid: String,
        objectCount: UInt64,
        kept: UInt64,
        dedupedAnnotations: UInt64,
        spatialIndexRoot: String?,
        parentA: String,
        parentB: String
    ) {
        self.rootCid = rootCid
        self.objectCount = objectCount
        self.kept = kept
        self.dedupedAnnotations = dedupedAnnotations
        self.spatialIndexRoot = spatialIndexRoot
        self.parentA = parentA
        self.parentB = parentB
    }
}

public struct PullSummary: Equatable, Sendable {
    public var rootCid: String
    public var objectsStored: UInt64
    public var objectsSkipped: UInt64
    public var adoptedRoot: String?

    public init(
        rootCid: String,
        objectsStored: UInt64,
        objectsSkipped: UInt64,
        adoptedRoot: String?
    ) {
        self.rootCid = rootCid
        self.objectsStored = objectsStored
        self.objectsSkipped = objectsSkipped
        self.adoptedRoot = adoptedRoot
    }
}

// MARK: - Façade

/// Public Swift API. Store operations throw `ArxosError` from UniFFI.
public enum ArxosCore {
    public static func version() -> String {
        uniffiVersion()
    }

    public static func hello(name: String) -> String {
        uniffiHello(name: name)
    }

    public static func generateBuildingId() -> String {
        uniffiGenerateBuildingId()
    }

    public static func defaultStorePath() -> String {
        let base = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask).first
            ?? FileManager.default.temporaryDirectory
        let url = base.appendingPathComponent("arxos-store", isDirectory: true)
        try? FileManager.default.createDirectory(at: url, withIntermediateDirectories: true)
        protectStore(at: url)
        return url.path
    }

    /// CAS lives in Application Support (not shared Documents). Exclude from
    /// iCloud/unencrypted backup; complete data protection when the device locks.
    static func protectStore(at url: URL) {
        var mutable = url
        var values = URLResourceValues()
        values.isExcludedFromBackup = true
        try? mutable.setResourceValues(values)
        try? FileManager.default.setAttributes(
            [.protectionKey: FileProtectionType.complete],
            ofItemAtPath: url.path
        )
        let keys = url.appendingPathComponent("keys", isDirectory: true)
        if FileManager.default.fileExists(atPath: keys.path) {
            var keyUrl = keys
            var keyValues = URLResourceValues()
            keyValues.isExcludedFromBackup = true
            try? keyUrl.setResourceValues(keyValues)
            try? FileManager.default.setAttributes(
                [.protectionKey: FileProtectionType.complete],
                ofItemAtPath: keys.path
            )
        }
    }

    static func ensureDeviceSeed(storePath: String) throws {
        let seed = try DeviceSeed.loadOrCreate(migratingFrom: storePath)
        try uniffiSetDeviceSeed(seed: seed)
    }

    public static func initBuilding(storePath: String, name: String?) throws -> BuildingSummary {
        try ensureDeviceSeed(storePath: storePath)
        let s = try uniffiInitBuilding(storePath: storePath, name: name)
        protectStore(at: URL(fileURLWithPath: storePath, isDirectory: true))
        DeviceSeed.deleteDiskSeed(storePath: storePath)
        return BuildingSummary(
            buildingId: s.buildingId,
            name: s.name,
            headRoot: s.headRoot,
            buildingObject: s.buildingObject,
            stagedCount: s.stagedCount
        )
    }

    public static func openBuilding(storePath: String, buildingId: String) throws -> BuildingSummary {
        try ensureDeviceSeed(storePath: storePath)
        let s = try uniffiOpenBuilding(storePath: storePath, buildingId: buildingId)
        return BuildingSummary(
            buildingId: s.buildingId,
            name: s.name,
            headRoot: s.headRoot,
            buildingObject: s.buildingObject,
            stagedCount: s.stagedCount
        )
    }

    public static func listBuildings(storePath: String) throws -> [BuildingSummary] {
        try uniffiListBuildings(storePath: storePath).map {
            BuildingSummary(
                buildingId: $0.buildingId,
                name: $0.name,
                headRoot: $0.headRoot,
                buildingObject: $0.buildingObject,
                stagedCount: $0.stagedCount
            )
        }
    }

    public static func captureSpace(
        storePath: String,
        buildingId: String,
        name: String?,
        x: Double, y: Double, z: Double,
        entityId: String? = nil
    ) throws -> CapturePutResult {
        try ensureDeviceSeed(storePath: storePath)
        let r = try uniffiCaptureSpace(
            storePath: storePath, buildingId: buildingId, name: name, x: x, y: y, z: z,
            entityId: entityId
        )
        return CapturePutResult(cid: r.cid, objectType: r.objectType)
    }

    public static func captureAnnotation(
        storePath: String,
        buildingId: String,
        text: String,
        x: Double, y: Double, z: Double
    ) throws -> CapturePutResult {
        try ensureDeviceSeed(storePath: storePath)
        let r = try uniffiCaptureAnnotation(
            storePath: storePath, buildingId: buildingId, text: text, x: x, y: y, z: z
        )
        return CapturePutResult(cid: r.cid, objectType: r.objectType)
    }

    public static func capturePointCloud(
        storePath: String,
        buildingId: String,
        pointsXYZF32LE: Data,
        x: Double, y: Double, z: Double
    ) throws -> CapturePutResult {
        try ensureDeviceSeed(storePath: storePath)
        let r = try uniffiCapturePointCloud(
            storePath: storePath,
            buildingId: buildingId,
            pointsXyzF32Le: pointsXYZF32LE,
            x: x, y: y, z: z
        )
        return CapturePutResult(cid: r.cid, objectType: r.objectType)
    }

    public static func commitBuilding(
        storePath: String,
        buildingId: String,
        message: String?
    ) throws -> CommitSummary {
        try ensureDeviceSeed(storePath: storePath)
        let r = try uniffiCommitBuilding(
            storePath: storePath, buildingId: buildingId, message: message
        )
        return CommitSummary(
            rootCid: r.rootCid,
            buildingId: r.buildingId,
            objectCount: r.objectCount,
            previousRoot: r.previousRoot
        )
    }

    public static func annotationsNear(
        storePath: String,
        buildingId: String,
        x: Double, y: Double, z: Double,
        radiusM: Double
    ) throws -> [AnnotationOverlay] {
        try uniffiAnnotationsNear(
            storePath: storePath, buildingId: buildingId,
            x: x, y: y, z: z, radiusM: radiusM
        ).map {
            AnnotationOverlay(
                cid: $0.cid, text: $0.text,
                x: $0.x, y: $0.y, z: $0.z, distanceM: $0.distanceM
            )
        }
    }

    public struct BuildingLocator: Equatable, Sendable {
        public var buildingId: String
        public var controllers: [String]
        public var inbox: String?
    }

    public static func parseBuildingLocator(uri: String) throws -> BuildingLocator {
        let r = try uniffiParseBuildingLocator(uri: uri)
        return BuildingLocator(
            buildingId: r.buildingId,
            controllers: r.controllers,
            inbox: r.inbox
        )
    }

    public struct PushSummary: Equatable, Sendable {
        public var buildingId: String
        public var accepted: UInt64
        public var duplicate: UInt64
        public var rejected: UInt64
    }

    /// Push staged Facts to a peer inbox. Never sets remote head.
    /// Requires generated UniFFI bindings (`./ios/scripts/prep.sh` after UDL change).
    public static func pushStaged(
        storePath: String,
        buildingId: String,
        peerTicket: String
    ) throws -> PushSummary {
        try ensureDeviceSeed(storePath: storePath)
        let r = try uniffiPushStaged(
            storePath: storePath, buildingId: buildingId, peerTicket: peerTicket
        )
        return PushSummary(
            buildingId: r.buildingId,
            accepted: r.accepted,
            duplicate: r.duplicate,
            rejected: r.rejected
        )
    }

    public static func ingestRoomPlan(
        storePath: String,
        buildingId: String,
        surfaces: [RoomPlanSurface],
        objects: [RoomPlanObject]
    ) throws -> IngestSummary {
        try ensureDeviceSeed(storePath: storePath)
        let geom = RoomPlanGeometry(
            surfaces: surfaces.map {
                FfiRoomPlanSurface(
                    id: $0.id, category: $0.category,
                    transform: $0.transform, dimensions: $0.dimensions
                )
            },
            objects: objects.map {
                FfiRoomPlanObject(
                    id: $0.id, category: $0.category,
                    transform: $0.transform, dimensions: $0.dimensions
                )
            }
        )
        let r = try uniffiIngestRoomPlan(
            storePath: storePath, buildingId: buildingId, geometry: geom
        )
        return IngestSummary(
            spaceCid: r.spaceCid,
            surfaceCids: r.surfaceCids,
            objectCids: r.objectCids
        )
    }

    public static func querySpatialVolume(
        storePath: String,
        buildingId: String,
        minX: Double, minY: Double, minZ: Double,
        maxX: Double, maxY: Double, maxZ: Double
    ) throws -> [SpatialItem] {
        try uniffiQuerySpatialVolume(
            storePath: storePath, buildingId: buildingId,
            minX: minX, minY: minY, minZ: minZ,
            maxX: maxX, maxY: maxY, maxZ: maxZ
        ).map { item in
            var props = [String: String]()
            for kv in item.properties {
                props[kv.key] = kv.value
            }
            return SpatialItem(
                cid: item.cid,
                objectType: item.objectType,
                name: item.name,
                x: item.poseX,
                y: item.poseY,
                z: item.poseZ,
                properties: props
            )
        }
    }

    public static func mergeBuildingRoot(
        storePath: String,
        buildingId: String,
        otherRootCid: String,
        message: String?
    ) throws -> MergeResultSummary {
        try ensureDeviceSeed(storePath: storePath)
        let r = try uniffiMergeBuildingRoot(
            storePath: storePath, buildingId: buildingId,
            otherRootCid: otherRootCid, message: message
        )
        return MergeResultSummary(
            rootCid: r.rootCid,
            objectCount: r.objectCount,
            kept: r.kept,
            dedupedAnnotations: r.dedupedAnnotations,
            spatialIndexRoot: r.spatialIndexRoot,
            parentA: r.parentA,
            parentB: r.parentB
        )
    }

    public static func pullRemoteRoot(
        storePath: String,
        peerTicket: String,
        rootCid: String,
        buildingId: String?,
        setHead: Bool
    ) throws -> PullSummary {
        let r = try uniffiPullRemoteRoot(
            storePath: storePath, peerTicket: peerTicket,
            rootCid: rootCid, buildingId: buildingId,
            setHead: setHead
        )
        return PullSummary(
            rootCid: r.rootCid,
            objectsStored: r.objectsStored,
            objectsSkipped: r.objectsSkipped,
            adoptedRoot: r.adoptedRoot
        )
    }

    public static func exportUsd(
        storePath: String,
        buildingId: String,
        outputPath: String
    ) throws {
        try uniffiExportUsd(
            storePath: storePath, buildingId: buildingId, outputPath: outputPath
        )
    }

    public static func exportIfc(
        storePath: String,
        buildingId: String,
        outputPath: String
    ) throws {
        try uniffiExportIfc(
            storePath: storePath, buildingId: buildingId, outputPath: outputPath
        )
    }
}

/// Controller seed in the Keychain. Never stored in the CAS folder.
enum DeviceSeed {
    private static let service = "ai.arxos.device-seed"
    private static let account = "controller"

    static func loadOrCreate(migratingFrom storePath: String) throws -> Data {
        if let existing = try load() {
            deleteDiskSeed(storePath: storePath)
            return existing
        }
        let disk = URL(fileURLWithPath: storePath, isDirectory: true)
            .appendingPathComponent("keys", isDirectory: true)
            .appendingPathComponent("device.seed")
        if let fromDisk = try? Data(contentsOf: disk), fromDisk.count == 32 {
            try save(fromDisk)
            deleteDiskSeed(storePath: storePath)
            return fromDisk
        }
        var bytes = [UInt8](repeating: 0, count: 32)
        let status = SecRandomCopyBytes(kSecRandomDefault, bytes.count, &bytes)
        guard status == errSecSuccess else {
            throw NSError(
                domain: NSOSStatusErrorDomain,
                code: Int(status),
                userInfo: [NSLocalizedDescriptionKey: "failed to generate device seed"]
            )
        }
        let data = Data(bytes)
        try save(data)
        return data
    }

    static func load() throws -> Data? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        if status == errSecItemNotFound {
            return nil
        }
        guard status == errSecSuccess, let data = item as? Data else {
            throw NSError(domain: NSOSStatusErrorDomain, code: Int(status))
        }
        return data
    }

    static func save(_ data: Data) throws {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
        SecItemDelete(query as CFDictionary)
        var attrs = query
        attrs[kSecValueData as String] = data
        attrs[kSecAttrAccessible as String] = kSecAttrAccessibleWhenUnlockedThisDeviceOnly
        let status = SecItemAdd(attrs as CFDictionary, nil)
        guard status == errSecSuccess else {
            throw NSError(domain: NSOSStatusErrorDomain, code: Int(status))
        }
    }

    static func deleteDiskSeed(storePath: String) {
        let seed = URL(fileURLWithPath: storePath, isDirectory: true)
            .appendingPathComponent("keys", isDirectory: true)
            .appendingPathComponent("device.seed")
        try? FileManager.default.removeItem(at: seed)
    }
}
